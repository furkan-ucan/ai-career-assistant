"""
Akıllı Kariyer Asistanı - Ana Uygulama (BÖL VE FETHET STRATEJİSİ)
Bu dosya, tüm sistem bileşenlerini koordine eder ve uygulamanın giriş noktasıdır.
"""

# Standard Library
import os
from pathlib import Path
from datetime import datetime

# Third Party
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

from src.config import load_settings
from src.cv_analyzer import CVAnalyzer
from src.cv_processor import CVProcessor
from src.data_collector import collect_job_data
from src.embedding_service import EmbeddingService
from src.filter import score_jobs
from src.intelligent_scoring import IntelligentScoringSystem
from src.logger_config import setup_logging
from src.persona_builder import build_dynamic_personas
from src.utils.file_helpers import save_dataframe_csv
from src.vector_store import VectorStore

# Environment variables yükle
load_dotenv()


logger = setup_logging()


# Konfigürasyonu yükle
config = load_settings()


def load_config() -> dict:
    """Backward compatibility wrapper for tests."""
    return config
scoring_system: IntelligentScoringSystem | None = None

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


def _collect_jobs_for_persona(
    persona_name: str, persona_cfg: dict, results_per_site: int | None
) -> pd.DataFrame | None:
    """
    Tek persona için iş ilanları toplar.

    Args:
        persona_name: Persona adı
        persona_cfg: Persona konfigürasyonu
        results_per_site: Site başına sonuç sayısı

    Returns:
        DataFrame | None: Toplanan iş ilanları veya None
    """
    logger.info(f"\n--- Persona '{persona_name}' için JobSpy Gelişmiş Arama ---")
    logger.info(f"🎯 Optimize edilmiş terim: '{persona_cfg['term']}'")
    logger.info(f"⏰ Tarih filtresi: Son {persona_cfg['hours_old']} saat")

    try:
        max_results = results_per_site if results_per_site is not None else persona_cfg["results"]
        jobs_df_for_persona = collect_job_data(
            search_term=persona_cfg["term"],
            site_names=TARGET_SITES,  # LinkedIn + Indeed
            location="Turkey",
            max_results_per_site=max_results,
            hours_old=persona_cfg["hours_old"],
        )
        # Type safety: collect_job_data fonksiyonundan dönen değeri kontrol et
        if jobs_df_for_persona is not None and not jobs_df_for_persona.empty:
            # Persona bilgisini ve arama terimini ekle (analiz için faydalı)
            jobs_df_for_persona["persona_source"] = persona_name
            jobs_df_for_persona["search_term_used"] = persona_cfg["term"]
            logger.info(f"✨ Persona '{persona_name}' için {len(jobs_df_for_persona)} ilan bulundu.")
            return jobs_df_for_persona  # type: ignore[no-any-return]
        else:
            logger.info(f"ℹ️ Persona '{persona_name}' için hiçbir siteden ilan bulunamadı.")
            return None

    except Exception as e:
        logger.error(f"❌ Persona '{persona_name}' için hata: {str(e)}", exc_info=True)
        return None


def _deduplicate_and_save_jobs(all_jobs_list: list[pd.DataFrame]) -> str | None:
    """
    İş ilanlarını birleştirir, duplikatları temizler ve CSV olarak kaydeder.

    Args:
        all_jobs_list: İş ilanları DataFrame listesi

    Returns:
        str | None: CSV dosya yolu veya None
    """
    non_empty = [df for df in all_jobs_list if df is not None and not df.empty]
    if not non_empty:
        logger.error("❌ Hiçbir persona ve site kombinasyonundan ilan bulunamadı.")
        return None

    final_df = pd.concat(non_empty, ignore_index=True)
    logger.info(f"\n📊 Birleştirme öncesi (tüm personalar): {len(final_df)} ilan")

    # Son genel deduplication (persona'lar arası tekrarlar için)
    if not final_df.empty:
        subset_cols = ["title", "company"]
        if "location" in final_df.columns:
            subset_cols.append("location")
        if "description" in final_df.columns:
            final_df["description_short"] = final_df["description"].astype(str).str[:100]
            subset_cols.append("description_short")

        final_df.drop_duplicates(subset=subset_cols, inplace=True, keep="first")
        if "description_short" in final_df.columns:
            final_df.drop(columns=["description_short"], inplace=True)

    logger.info(f"✨✨✨ TOPLAM: {len(final_df)} adet BENZERSİZ ilan (JobSpy optimize edilmiş)! ✨✨✨")

    output_dir = Path(config["paths"]["data_dir"])
    csv_path = save_dataframe_csv(final_df, output_dir, "jobspy_optimize_ilanlar")
    logger.info(f"📁 JobSpy optimize edilmiş veriler: {csv_path}")

    return str(csv_path)


def collect_data_for_all_personas(selected_personas=None, results_per_site=None, persona_configs=None):
    """
    Tüm persona'lar için iş ilanlarını toplar ve CSV yolunu döner.

    Args:
        selected_personas: Seçili persona listesi (None ise tümü)
        results_per_site: Site başına sonuç sayısı (None ise config'den)
        persona_configs: Persona konfigürasyonları (None ise default)

    Returns:
        str | None: Toplanan verilerin CSV dosya yolu
    """
    logger.info("🔍 JobSpy Gelişmiş Özellikler ile Stratejik Veri Toplama Başlatılıyor...")
    logger.info("=" * 70)

    all_collected_jobs_list = []
    cfg = persona_configs or persona_search_config
    personas = cfg.items()
    if selected_personas:
        personas = [(p, cfg[p]) for p in selected_personas if p in cfg]

    # Her persona için veri toplama
    for persona_name, persona_cfg in tqdm(personas, desc="Persona Aramaları"):
        jobs_df = _collect_jobs_for_persona(persona_name, persona_cfg, results_per_site)
        if jobs_df is not None:
            all_collected_jobs_list.append(jobs_df)

    # Verileri birleştir ve kaydet
    return _deduplicate_and_save_jobs(all_collected_jobs_list)


def analyze_and_find_best_jobs(selected_personas=None, results_per_site=None, similarity_threshold=None):
    """Run full pipeline and print best jobs."""
    logger.info("\n🚀 Tam Otomatik AI Kariyer Analizi Başlatılıyor...")
    logger.info("=" * 60)

    threshold = similarity_threshold if similarity_threshold is not None else MIN_SIMILARITY_THRESHOLD

    # Setup AI metadata and configurations
    ai_metadata, personas_cfg = _setup_ai_metadata_and_personas()
    if not _configure_scoring_system(ai_metadata):
        return

    # Execute the main pipeline
    _execute_full_pipeline(selected_personas, results_per_site, personas_cfg, threshold)


def _setup_ai_metadata_and_personas() -> tuple[dict, dict]:
    """Setup AI metadata and personas configuration."""
    cv_text = Path(config["paths"]["cv_file"]).read_text(encoding="utf-8")
    analyzer = CVAnalyzer()
    ai_metadata = analyzer.extract_metadata_from_cv(cv_text)

    personas_cfg = persona_search_config
    if ai_metadata.get("target_job_titles"):
        # Type safety: ai_metadata["target_job_titles"] var mı ve list[str] mi kontrol et
        target_titles = ai_metadata["target_job_titles"]
        if isinstance(target_titles, list) and all(isinstance(title, str) for title in target_titles):
            personas_cfg = build_dynamic_personas(target_titles)
        else:
            logger.warning("AI metadata target_job_titles geçersiz format - static personas kullanılıyor")
    else:
        logger.warning("AI metadata missing - using static personas")

    return ai_metadata, personas_cfg


def _validate_skill_metadata(key_skills: object, skill_importance: object) -> bool:
    """Validate skill metadata structure and types."""
    return (
        isinstance(key_skills, list)
        and isinstance(skill_importance, list)
        and len(key_skills) == len(skill_importance)
        and all(isinstance(skill, str) for skill in key_skills)
        and all(isinstance(score, int | float) for score in skill_importance)
    )


def _apply_skill_weights(skill: str, importance: float, base_weight: int) -> None:
    """Apply weight multiplier based on skill importance."""
    if importance >= 0.85:
        # Core skills - highest weight
        weight = int(base_weight * 1.5)
        config["scoring_system"]["description_weights"]["positive"][skill] = weight
        logger.debug(f"  🔥 Core skill: {skill} (importance: {importance:.2f}) → weight: {weight}")
    elif importance >= 0.7:
        # Secondary skills - standard weight
        config["scoring_system"]["description_weights"]["positive"][skill] = base_weight
        logger.debug(f"  ⭐ Secondary skill: {skill} (importance: {importance:.2f}) → weight: {base_weight}")
    else:
        # Familiar skills - reduced weight
        weight = int(base_weight * 0.6)
        config["scoring_system"]["description_weights"]["positive"][skill] = weight
        logger.debug(f"  💡 Familiar skill: {skill} (importance: {importance:.2f}) → weight: {weight}")


def _configure_scoring_system(ai_metadata: dict) -> bool:
    """Configure the scoring system with AI metadata and skill importance."""
    global scoring_system

    try:
        if not (ai_metadata.get("key_skills") and ai_metadata.get("skill_importance")):
            logger.info("No AI skill data available - using static scoring")
            scoring_system = IntelligentScoringSystem(config)
            return True

        key_skills = ai_metadata["key_skills"]
        skill_importance = ai_metadata["skill_importance"]

        if not _validate_skill_metadata(key_skills, skill_importance):
            logger.warning("AI metadata skills format invalid - using static scoring")
            scoring_system = IntelligentScoringSystem(config)
            return True

        base_weight = config["scoring_system"].get("dynamic_skill_weight", 10)
        logger.info(f"🎯 Configuring enhanced scoring with {len(key_skills)} AI-detected skills")

        # Apply weight multipliers based on importance
        for skill, importance in zip(key_skills, skill_importance, strict=False):
            _apply_skill_weights(skill, importance, base_weight)

        logger.info("✅ Enhanced AI-driven scoring system configured")
        scoring_system = IntelligentScoringSystem(config)
        return True

    except Exception as e:
        logger.error(f"❌ Scoring system configuration failed: {e}")
        return False


def _execute_full_pipeline(selected_personas, results_per_site, personas_cfg, threshold):
    """Execute the full analysis pipeline."""
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
    _process_and_load_jobs(csv_path, vector_store)

    # 5. Benzer işleri bul ve filtrele
    if cv_embedding is None:
        logger.error("❌ CV embedding oluşturulamadı, arama yapılamıyor")
        return

    similar_jobs = _search_and_score_jobs(cv_embedding, vector_store, threshold)
    _display_results(similar_jobs, threshold)


def _process_and_load_jobs(csv_path: str, vector_store: VectorStore):
    """Process and load jobs into vector store."""
    logger.info("🔄 4/6: İş ilanları vector store'a yükleniyor...")
    jobs_df = _load_and_validate_csv(csv_path)
    if jobs_df is None:
        return

    job_embeddings = _process_job_embeddings(jobs_df, vector_store)
    success = vector_store.add_jobs(jobs_df, job_embeddings)
    if not success:
        logger.error("❌ Vector store yükleme başarısız!")


def _load_and_validate_csv(csv_path: str) -> pd.DataFrame | None:
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


def _setup_cv_processor() -> CVProcessor | None:
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


def _setup_vector_store() -> VectorStore | None:
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


def _process_job_embeddings(jobs_df: pd.DataFrame, vector_store: VectorStore) -> list[list[float] | None]:
    """İş ilanları için embeddings oluştur"""
    embedding_service = EmbeddingService(**embedding_settings)
    logger.info("🔄 5/6: İş ilanları için AI embeddings oluşturuluyor...")

    job_embeddings: list[list[float] | None] = []
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


def _search_and_score_jobs(cv_embedding: list[float], vector_store: VectorStore, threshold: float) -> list[dict]:
    """Benzer işleri bul ve puanla"""
    logger.info("\n🔄 6/6: Akıllı eşleştirme ve filtreleme...")

    top_k = config["vector_store_settings"]["top_k_results"]
    search_results = vector_store.search_jobs(cv_embedding, n_results=top_k)

    similar_jobs = [
        dict(metadata, similarity_score=(1 - dist) * 100)
        for metadata, dist in zip(
            search_results.get("metadatas", []), search_results.get("distances", []), strict=False
        )
    ]

    if not similar_jobs:
        return []

    logger.info("🔍 Sonuçlar akıllı puanlama ile değerlendiriliyor...")
    scored_jobs = score_jobs(similar_jobs, scoring_system, debug=False)
    return [job for job in scored_jobs if job["similarity_score"] >= threshold]


def _display_results(similar_jobs: list[dict], threshold: float) -> None:
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
            persona_counts: dict[str, int] = {}
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
