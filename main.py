"""
Akıllı Kariyer Asistanı - Ana Uygulama (BÖL VE FETHET STRATEJİSİ)
Bu dosya, tüm sistem bileşenlerini koordine eder ve uygulamanın giriş noktasıdır.
"""

# Standard Library
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Third Party
import pandas as pd
import yaml  # type: ignore
from dotenv import load_dotenv
from tqdm import tqdm

from src.cv_analyzer import CVAnalyzer

# Local
from src.cv_processor import CVProcessor
from src.data_collector import collect_job_data
from src.embedding_service import EmbeddingService
from src.filter import score_jobs
from src.intelligent_scoring import IntelligentScoringSystem
from src.persona_builder import build_dynamic_personas
from src.vector_store import VectorStore

# Environment variables yükle
load_dotenv()


# Gelişmiş loglama konfigürasyonu
def setup_logging():
    """
    Gelişmiş logging kurulumu - dosya ve konsol çıktısı ile.

    Returns:
        logging.Logger: Yapılandırılmış logger nesnesi
    """
    # Log directory oluştur
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Log formatı
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler (terminal çıktısı)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler (dosya çıktısı)
    # Standard Library
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(log_dir / f"kariyer_asistani_{timestamp}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Error file handler (sadece hatalar)
    error_handler = logging.FileHandler(log_dir / f"errors_{timestamp}.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Handler'ları ekle
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    return root_logger


# Logging sistemini başlat
logger = setup_logging()


def load_config():
    """
    config.yaml dosyasını yükler ve parse eder.

    Returns:
        dict: Yüklenmiş konfigürasyon verisi

    Raises:
        FileNotFoundError: Config dosyası bulunamazsa
        yaml.YAMLError: YAML parse hatası olursa
    """
    config_path = Path("config.yaml")
    try:
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)
        logger.info("✅ config.yaml başarıyla yüklendi")
        return config
    except FileNotFoundError:
        logger.error(f"❌ config.yaml dosyası bulunamadı: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"❌ config.yaml dosyası parse edilemedi: {e}")
        raise


# Konfigürasyonu yükle
config = load_config()
scoring_system: Optional[IntelligentScoringSystem] = None

# Embedding ayarları
embedding_settings = config.get("embedding_settings", {})

# Job settings from config
job_settings = config["job_search_settings"]
MIN_SIMILARITY_THRESHOLD = job_settings["min_similarity_threshold"]
TARGET_SITES = job_settings["target_sites"]
DEFAULT_HOURS_OLD = job_settings["default_hours_old"]
DEFAULT_RESULTS_PER_PERSONA_SITE = job_settings["default_results_per_site"]

# Persona konfigürasyonları
persona_search_config = config["persona_search_configs"]


def collect_data_for_all_personas(selected_personas=None, results_per_site=None, persona_configs=None):
    """
    Tüm persona'lar için iş ilanlarını toplar ve CSV yolunu döner.

    Args:
        selected_personas: Seçili persona listesi (None ise tümü)
        results_per_site: Site başına sonuç sayısı (None ise config'den)

    Returns:
        str: Toplanan verilerin CSV dosya yolu
    """
    logger.info("🔍 JobSpy Gelişmiş Özellikler ile Stratejik Veri Toplama Başlatılıyor...")
    logger.info("=" * 70)

    all_collected_jobs_list = []

    cfg = persona_configs or persona_search_config
    personas = cfg.items()
    if selected_personas:
        personas = [(p, cfg[p]) for p in selected_personas if p in cfg]

    for persona_name, persona_cfg in tqdm(personas, desc="Persona Aramaları"):
        logger.info(f"\n--- Persona '{persona_name}' için JobSpy Gelişmiş Arama ---")
        logger.info(f"🎯 Optimize edilmiş terim: '{persona_cfg['term']}'")
        logger.info(f"⏰ Tarih filtresi: Son {persona_cfg['hours_old']} saat")

        try:
            # JobSpy'ın gelişmiş özelliklerini kullanarak veri toplama
            max_results = results_per_site if results_per_site is not None else persona_cfg["results"]
            jobs_df_for_persona = collect_job_data(
                search_term=persona_cfg["term"],
                site_names=TARGET_SITES,  # LinkedIn + Indeed
                location="Turkey",
                max_results_per_site=max_results,
                hours_old=persona_cfg["hours_old"],
            )
            if jobs_df_for_persona is not None and not jobs_df_for_persona.empty:
                # Persona bilgisini ve arama terimini ekle (analiz için faydalı)
                jobs_df_for_persona["persona_source"] = persona_name
                jobs_df_for_persona["search_term_used"] = persona_cfg["term"]
                all_collected_jobs_list.append(jobs_df_for_persona)
                logger.info(f"✨ Persona '{persona_name}' için {len(jobs_df_for_persona)} ilan bulundu.")
            else:
                logger.info(f"ℹ️ Persona '{persona_name}' için hiçbir siteden ilan bulunamadı.")

        except Exception as e:
            logger.error(f"❌ Persona '{persona_name}' için hata: {str(e)}", exc_info=True)
            continue

    non_empty = [df for df in all_collected_jobs_list if df is not None and not df.empty]
    if not non_empty:
        logger.error("❌ Hiçbir persona ve site kombinasyonundan ilan bulunamadı.")
        return None
    final_df = pd.concat(non_empty, ignore_index=True)
    logger.info(f"\n📊 Birleştirme öncesi (tüm personalar): {len(final_df)} ilan")

    # Son genel deduplication (persona'lar arası tekrarlar için)
    if "description" in final_df.columns and not final_df.empty:
        final_df["description_short"] = final_df["description"].astype(str).str[:100]
        final_df.drop_duplicates(
            subset=["title", "company", "location", "description_short"],
            inplace=True,
            keep="first",
        )
        final_df.drop(columns=["description_short"], inplace=True)
    elif not final_df.empty:
        final_df.drop_duplicates(subset=["title", "company", "location"], inplace=True, keep="first")

    logger.info(f"✨✨✨ TOPLAM: {len(final_df)} adet BENZERSİZ ilan (JobSpy optimize edilmiş)! ✨✨✨")

    # Optimize edilmiş CSV kaydetme (pathlib ile)
    output_dir = Path(config["paths"]["data_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_csv_path = output_dir / f"jobspy_optimize_ilanlar_{timestamp}.csv"
    final_df.to_csv(final_csv_path, index=False, encoding="utf-8")
    logger.info(f"📁 JobSpy optimize edilmiş veriler: {final_csv_path}")

    return str(final_csv_path)


def analyze_and_find_best_jobs(selected_personas=None, results_per_site=None, similarity_threshold=None):
    """Run full pipeline and print best jobs."""
    logger.info("\n🚀 Tam Otomatik AI Kariyer Analizi Başlatılıyor...")
    logger.info("=" * 60)

    threshold = similarity_threshold if similarity_threshold is not None else MIN_SIMILARITY_THRESHOLD

    cv_text = Path(config["paths"]["cv_file"]).read_text(encoding="utf-8")
    analyzer = CVAnalyzer()
    ai_metadata = analyzer.extract_metadata_from_cv(cv_text)

    personas_cfg = persona_search_config
    if ai_metadata.get("target_job_titles"):
        personas_cfg = build_dynamic_personas(ai_metadata["target_job_titles"])
    else:
        logger.warning("AI metadata missing - using static personas")

    if ai_metadata.get("key_skills"):
        weight = config["scoring_system"].get("dynamic_skill_weight", 10)
        for skill in ai_metadata["key_skills"]:
            config["scoring_system"]["description_weights"]["positive"][skill] = weight

    global scoring_system
    scoring_system = IntelligentScoringSystem(config)

    # 1. Veri toplama
    logger.info("\n🔄 1/6: JobSpy Gelişmiş Özellikler ile veri toplama...")
    csv_path = collect_data_for_all_personas(selected_personas, results_per_site, personas_cfg)
    if not csv_path:
        logger.error("❌ Veri toplama başarısız - analiz durduruluyor!")
        return

    # 2. CV'yi işle
    cv_processor = _setup_cv_processor()
    if not cv_processor:
        return

    if not cv_processor.create_cv_embedding():
        logger.error("❌ CV embedding oluşturma başarısız!")
        return

    cv_embedding = cv_processor.cv_embedding
    logger.info("✅ CV embedding oluşturuldu")

    # 3. Vector store'u başlat
    vector_store = _setup_vector_store()
    if not vector_store:
        return

    # 4. İş ilanlarını vector store'a yükle
    logger.info("🔄 4/6: İş ilanları vector store'a yükleniyor...")  # CSV'yi pathlib ile oku
    jobs_df = _load_and_validate_csv(csv_path)
    if jobs_df is None:
        return

    job_embeddings = _process_job_embeddings(jobs_df, vector_store)
    success = vector_store.add_jobs(jobs_df, job_embeddings)
    if not success:
        logger.error("❌ Vector store yükleme başarısız!")
        return

    # 5. Benzer işleri bul ve filtrele
    if cv_embedding is None:
        logger.error("❌ CV embedding oluşturulamadı, arama yapılamıyor")
        return

    similar_jobs = _search_and_score_jobs(cv_embedding, vector_store, threshold)
    _display_results(similar_jobs, threshold)


def _load_and_validate_csv(csv_path: str) -> Optional[pd.DataFrame]:
    """CSV dosyasını yükle ve doğrula"""
    try:
        csv_path_obj = Path(csv_path)
        jobs_df = pd.read_csv(csv_path_obj)
        logger.info(f"📊 {len(jobs_df)} iş ilanı yüklendi")
        return jobs_df
    except FileNotFoundError:
        logger.error(f"❌ CSV dosyası bulunamadı: {csv_path}")
        return None
    except pd.errors.EmptyDataError:
        logger.error("❌ CSV dosyası boş!")
        return None
    except Exception as e:
        logger.error(f"❌ CSV okuma hatası: {e}")
        return None


def _setup_cv_processor() -> Optional[CVProcessor]:
    """CV processor'ı kurulum yap"""
    logger.info("\n📄 2/6: CV analizi...")
    cv_processor = CVProcessor(embedding_settings=embedding_settings)

    if not cv_processor.load_cv():
        logger.error("❌ CV yükleme başarısız!")
        return None

    if not cv_processor.create_cv_embedding():
        logger.error("❌ CV embedding oluşturma başarısız!")
        return None

    logger.info("✅ CV embedding oluşturuldu")
    return cv_processor


def _setup_vector_store() -> Optional[VectorStore]:
    """Vector store'u kurulum yap"""
    logger.info("\n🗃️ 3/6: Vector store hazırlığı...")
    vector_store = VectorStore(
        persist_directory=config["paths"]["chromadb_dir"],
        collection_name=config["vector_store_settings"]["collection_name"],
    )

    if not vector_store.create_collection():
        logger.error("❌ Vector store koleksiyon oluşturma başarısız!")
        return None

    return vector_store


def _process_job_embeddings(jobs_df: pd.DataFrame, vector_store: VectorStore) -> List[Optional[List[float]]]:
    """İş ilanları için embeddings oluştur"""
    embedding_service = EmbeddingService(**embedding_settings)
    logger.info("🔄 5/6: İş ilanları için AI embeddings oluşturuluyor...")

    job_embeddings: List[Optional[List[float]]] = []
    for _, job in tqdm(jobs_df.iterrows(), total=len(jobs_df), desc="İlan Embeddings"):
        job_dict = job.to_dict()

        if vector_store.job_exists(job_dict):
            job_embeddings.append(None)
            continue

        if pd.notna(job.get("description", "")):
            try:
                embedding = embedding_service.create_embedding(str(job["description"]))
                job_embeddings.append(embedding)
            except Exception as e:
                logger.warning(f"⚠️ Embedding oluşturma hatası: {e}")
                job_embeddings.append(None)
        else:
            job_embeddings.append(None)

    return job_embeddings


def _search_and_score_jobs(cv_embedding: List[float], vector_store: VectorStore, threshold: float) -> List[dict]:
    """Benzer işleri bul ve puanla"""
    logger.info("\n🔄 6/6: Akıllı eşleştirme ve filtreleme...")

    top_k = config["vector_store_settings"]["top_k_results"]
    search_results = vector_store.search_jobs(cv_embedding, n_results=top_k)

    similar_jobs = [
        dict(metadata, similarity_score=(1 - dist) * 100)
        for metadata, dist in zip(search_results.get("metadatas", []), search_results.get("distances", []))
    ]

    if not similar_jobs:
        return []

    logger.info("🔍 Sonuçlar akıllı puanlama ile değerlendiriliyor...")
    scored_jobs = score_jobs(similar_jobs, scoring_system, debug=False)
    return [job for job in scored_jobs if job["similarity_score"] >= threshold]


def _display_results(similar_jobs: List[dict], threshold: float) -> None:
    """Sonuçları görüntüle"""
    if similar_jobs:
        logger.info(f"✅ {len(similar_jobs)} adet yüksek kaliteli pozisyon bulundu!")
        logger.info(f"📊 Uygunluk eşiği: %{threshold} ve üzeri")
        logger.info("\n" + "=" * 70)
        logger.info("🎉 SİZE ÖZEL EN UYGUN İŞ İLANLARI (JobSpy Optimize)")
        logger.info("🎯 YBS + Full-Stack + Veri Analizi Odaklı")
        logger.info("=" * 70)

        for i, job in enumerate(similar_jobs[:15], 1):  # Top 15 göster
            logger.info(
                f"\n{i}. {job.get('title', 'Başlık belirtilmemiş')} - {job.get('company', 'Şirket belirtilmemiş')}"
            )
            logger.info(f"   📍 {job.get('location', 'Lokasyon belirtilmemiş')}")
            # match_score veya similarity_score'u güvenli şekilde al
            score = job.get("match_score", job.get("similarity_score", 0))
            logger.info(f"   📊 Uygunluk: %{score:.1f}")
            logger.info(f"   💼 Site: {job.get('source_site', job.get('site', 'Site belirtilmemiş'))}")
            logger.info(f"   👤 Persona: {job.get('persona_source', job.get('persona', 'Persona belirtilmemiş'))}")
            logger.info(f"   🔗 {job.get('url', job.get('job_url', 'URL bulunamadı'))}")
            logger.info("-" * 50)

        logger.info(f"\n🎯 Analiz tamamlandı! {len(similar_jobs)} yüksek kaliteli pozisyon listelendi.")

        if similar_jobs and ("persona_source" in similar_jobs[0] or "persona" in similar_jobs[0]):
            persona_counts: Dict[str, int] = {}
            for job in similar_jobs:
                persona = job.get("persona_source", job.get("persona", "Unknown"))
                persona_counts[persona] = persona_counts.get(persona, 0) + 1

            logger.info("\n📈 Persona Dağılımı:")
            for persona, count in sorted(persona_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   {persona}: {count} ilan")

    else:
        logger.warning(f"⚠️  0 ilan bulundu veya uygunluk eşiği (%{threshold}) altında.")
        logger.info("💡 Eşiği düşürmeyi veya persona terimlerini genişletmeyi düşünebilirsiniz.")


def print_manual_validation_guide():
    """JobSpy Gelişmiş Özellikler için Manuel Doğrulama Protokolü"""
    logger.info("\n" + "=" * 80)
    logger.info("📋 JOBSPY GELİŞMİŞ ÖZELLİKLER - MANUEL DOĞRULAMA PROTOKOLÜ")
    logger.info("=" * 80)
    logger.info("🎯 SİSTEM DURUMU: JobSpy Native (hours_old=72, cosine similarity)")
    logger.info("🚀 Optimize Özellikler: Çoklu site, gelişmiş operatörler, 12 persona")
    logger.info("📊 Beklenen Performans: 100-300 benzersiz ilan, %80+ uygunluk oranı")
    logger.info("=" * 80)


def main(selected_personas=None, results_per_site=None, similarity_threshold=None):
    """Tek komutla tam otomatik AI kariyer analizi."""
    logger.info("🚀 Akıllı Kariyer Asistanı - Böl ve Fethet Stratejisi")
    logger.info("=" * 60)

    # Manuel doğrulama rehberini göster
    print_manual_validation_guide()  # Ön kontroller
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.error("❌ HATA: Gemini API key bulunamadı!")
        logger.info("📝 Lütfen .env dosyasında GEMINI_API_KEY değerini ayarlayın.")
        return

    # pathlib kullanarak CV dosyası kontrol
    cv_path = Path(config["paths"]["cv_file"])
    try:
        if not cv_path.exists():
            logger.error(f"❌ HATA: CV dosyası bulunamadı: {cv_path}")
            logger.info("📝 Lütfen CV'nizi data/cv.txt dosyasına ekleyin.")
            return

        # CV dosyasının okunabilir olduğunu kontrol et
        if cv_path.stat().st_size == 0:
            logger.error(f"❌ HATA: CV dosyası boş: {cv_path}")
            return

    except OSError as e:
        logger.error(f"❌ HATA: CV dosyası erişim hatası: {e}")
        return

    logger.info("✅ Sistem kontrolleri başarılı")
    logger.info("🎯 12 farklı JobSpy optimize edilmiş persona ile veri toplama başlatılıyor...\n")

    # Tam otomatik analiz çalıştır
    analyze_and_find_best_jobs(selected_personas, results_per_site, similarity_threshold)


# Test fonksiyonları için
if __name__ == "__main__":
    # Local
    from src.cli import parse_args

    args = parse_args()
    main(
        selected_personas=args.persona,
        results_per_site=args.results,
        similarity_threshold=args.threshold,
    )
