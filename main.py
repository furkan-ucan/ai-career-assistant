"""
Akıllı Kariyer Asistanı - Ana Uygulama (BÖL VE FETHET STRATEJİSİ)
Bu dosya, tüm sistem bileşenlerini koordine eder ve uygulamanın giriş noktasıdır.
"""

# Standard Library
import logging
import os
from datetime import datetime
from pathlib import Path

# Third Party
import pandas as pd
import yaml
from dotenv import load_dotenv
from tqdm import tqdm

# Local
from src.cv_processor import CVProcessor
from src.data_collector import collect_job_data
from src.embedding_service import EmbeddingService
from src.filter import filter_junior_suitable_jobs
from src.vector_store import VectorStore

# Environment variables yükle
load_dotenv()

# Loglama konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config():
    """config.yaml dosyasını yükle"""
    config_path = Path("config.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as file:
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

# Konfigürasyondan ayarları al
job_settings = config["job_search_settings"]
filter_settings = config["filter_settings"]  # Filtre ayarlarını yükle
MIN_SIMILARITY_THRESHOLD = job_settings["min_similarity_threshold"]
HEDEFLENEN_SITELER = job_settings["target_sites"]
DEFAULT_HOURS_OLD = job_settings["default_hours_old"]
DEFAULT_RESULTS_PER_PERSONA_SITE = job_settings["default_results_per_site"]

# Persona konfigürasyonları
persona_search_config = config["persona_search_configs"]


def collect_data_for_all_personas():
    """
    JobSpy Gelişmiş Özellikler ile Tüm Personalar için Optimize Edilmiş Veri Toplama
    Config.yaml'dan persona ayarları alınır.
    """
    logger.info("🔍 JobSpy Gelişmiş Özellikler ile Stratejik Veri Toplama Başlatılıyor...")
    logger.info("=" * 70)

    all_collected_jobs_list = []

    for persona_name, persona_config in tqdm(persona_search_config.items(), desc="Persona Aramaları"):
        logger.info(f"\n--- Persona '{persona_name}' için JobSpy Gelişmiş Arama ---")
        logger.info(f"🎯 Optimize edilmiş terim: '{persona_config['term']}'")
        logger.info(f"⏰ Tarih filtresi: Son {persona_config['hours_old']} saat")

        try:
            # JobSpy'ın gelişmiş özelliklerini kullanarak veri toplama
            jobs_df_for_persona = collect_job_data(
                search_term=persona_config["term"],
                site_names=HEDEFLENEN_SITELER,  # LinkedIn + Indeed
                location="Turkey",
                max_results_per_site=persona_config["results"],
                hours_old=persona_config["hours_old"],
            )
            if jobs_df_for_persona is not None and not jobs_df_for_persona.empty:
                # Persona bilgisini ve arama terimini ekle (analiz için faydalı)
                jobs_df_for_persona["persona_source"] = persona_name
                jobs_df_for_persona["search_term_used"] = persona_config["term"]
                all_collected_jobs_list.append(jobs_df_for_persona)
                logger.info(f"✨ Persona '{persona_name}' için {len(jobs_df_for_persona)} ilan bulundu.")
            else:
                logger.info(f"ℹ️ Persona '{persona_name}' için hiçbir siteden ilan bulunamadı.")

        except Exception as e:
            logger.error(f"❌ Persona '{persona_name}' için hata: {str(e)}", exc_info=True)
            continue

    if not all_collected_jobs_list:
        logger.error("❌ Hiçbir persona ve site kombinasyonundan ilan bulunamadı.")
        return None    # Boş DataFrame'leri filtrele (FutureWarning'i önlemek için)
    non_empty_jobs_list = [df for df in all_collected_jobs_list if not df.empty]

    if not non_empty_jobs_list:
        logger.error("❌ Tüm DataFrame'ler boş!")
        return None

    # Tüm personaların sonuçlarını birleştir (FutureWarning'i önlemek için sort=False)
    final_df = pd.concat(non_empty_jobs_list, ignore_index=True, sort=False)
    logger.info(f"\n📊 Birleştirme öncesi (tüm personalar): {len(final_df)} ilan")

    # Son genel deduplication (persona'lar arası tekrarlar için)
    if "description" in final_df.columns and not final_df.empty:
        final_df["description_short"] = final_df["description"].astype(str).str[:100]
        final_df.drop_duplicates(
            subset=["title", "company", "location", "description_short"], inplace=True, keep="first"
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


def analyze_and_find_best_jobs():
    """Tam otomatik analiz: Stratejik veri toplama + AI analizi + Sonuçlar"""
    logger.info("\n🚀 Tam Otomatik AI Kariyer Analizi Başlatılıyor...")
    logger.info("=" * 60)

    # 1. Veri toplama
    logger.info("\n🔄 1/6: JobSpy Gelişmiş Özellikler ile veri toplama...")
    csv_path = collect_data_for_all_personas()
    if not csv_path:
        logger.error("❌ Veri toplama başarısız - analiz durduruluyor!")
        return

    # 2. CV'yi işle
    logger.info("\n📄 2/6: CV analizi...")
    cv_processor = CVProcessor()
    if not cv_processor.load_cv():
        logger.error("❌ CV yükleme başarısız!")
        return

    if not cv_processor.create_cv_embedding():
        logger.error("❌ CV embedding oluşturma başarısız!")
        return

    cv_embedding = cv_processor.cv_embedding
    logger.info("✅ CV embedding oluşturuldu")

    # 3. Vector store'u başlat
    logger.info("\n🗃️ 3/6: Vector store hazırlığı...")
    vector_store = VectorStore()

    # 4. İş ilanlarını vector store'a yükle
    logger.info("🔄 4/6: İş ilanları vector store'a yükleniyor...")  # CSV'yi pathlib ile oku
    try:
        csv_path_obj = Path(csv_path)
        jobs_df = pd.read_csv(csv_path_obj)
        logger.info(f"📊 {len(jobs_df)} iş ilanı yüklendi")
    except FileNotFoundError:
        logger.error(f"❌ CSV dosyası bulunamadı: {csv_path}")
        return
    except pd.errors.EmptyDataError:
        logger.error("❌ CSV dosyası boş!")
        return
    except Exception as e:
        logger.error(f"❌ CSV okuma hatası: {e}")
        return

    # Koleksiyon oluştur
    if not vector_store.create_collection():
        logger.error("❌ Vector store koleksiyon oluşturma başarısız!")
        return

    # İş ilanları için embeddings oluştur (tqdm ile)
    embedding_service = EmbeddingService()

    logger.info("🔄 5/6: İş ilanları için AI embeddings oluşturuluyor...")
    job_embeddings = []

    for _, job in tqdm(jobs_df.iterrows(), total=len(jobs_df), desc="İlan Embeddings"):
        if pd.notna(job.get("description", "")):
            try:
                embedding = embedding_service.create_embedding(str(job["description"]))
                job_embeddings.append(embedding)
            except Exception as e:
                logger.warning(f"⚠️ Embedding oluşturma hatası: {e}")
                job_embeddings.append(None)
        else:
            job_embeddings.append(None)  # Vector store'a ekle (deduplication ile)
    success = vector_store.add_jobs(jobs_df, job_embeddings)
    if not success:
        logger.error("❌ Vector store yükleme başarısız!")
        return  # 5. Benzer işleri bul ve filtrele
    logger.info("\n🔄 6/6: Akıllı eşleştirme ve filtreleme...")
    search_results = vector_store.search_jobs(cv_embedding, n_results=50)    # Search results'ı filter fonksiyonunun beklediği formata dönüştür
    similar_jobs = []
    if search_results and search_results.get("metadatas"):
        metadatas = search_results["metadatas"][0]  # ChromaDB nested list format
        distances = search_results.get("distances", [[]])[0]  # ChromaDB nested list format

        for i, metadata in enumerate(metadatas):
            # Similarity score'u distance'tan çevir (cosine distance -> similarity)
            similarity_score = (1 - distances[i]) * 100 if i < len(distances) else 0
            job_entry = metadata.copy()
            job_entry["similarity_score"] = similarity_score
            similar_jobs.append(job_entry)

    if similar_jobs:
        logger.info("🔍 Sonuçlar YBS/junior pozisyonlar için akıllı filtreleme...")
        filtered_jobs = filter_junior_suitable_jobs(similar_jobs, filter_config=filter_settings, debug=False)

        if filtered_jobs:  # Uygunluk puanı eşiği ekleme
            high_quality_jobs = [job for job in filtered_jobs if job["similarity_score"] >= MIN_SIMILARITY_THRESHOLD]

            if high_quality_jobs:
                logger.info(f"✅ {len(high_quality_jobs)} adet yüksek kaliteli pozisyon bulundu!")
                logger.info(f"📊 Uygunluk eşiği: %{MIN_SIMILARITY_THRESHOLD} ve üzeri")

                logger.info("\n" + "=" * 70)
                logger.info("🎉 SİZE ÖZEL EN UYGUN İŞ İLANLARI (JobSpy Optimize)")
                logger.info("🎯 YBS + Full-Stack + Veri Analizi Odaklı")
                logger.info("=" * 70)

                for i, job in enumerate(high_quality_jobs[:15], 1):  # Top 15 göster
                    logger.info(f"\n{i}. {job['title']} - {job['company']}")
                    logger.info(f"   📍 {job['location']}")
                    logger.info(f"   📊 Uygunluk: %{job['similarity_score']:.1f}")
                    logger.info(f"   💼 Site: {job.get('source_site', 'N/A')}")  # Hangi siteden geldiği
                    logger.info(
                        f"   👤 Persona: {job.get('persona_source', job.get('persona', 'N/A'))}"
                    )  # Hangi persona aramasıyla geldiği
                    logger.info(f"   🔗 {job.get('job_url', job.get('url', 'URL bulunamadı'))}")
                    logger.info("-" * 50)

                logger.info(f"\n🎯 Analiz tamamlandı! {len(high_quality_jobs)} yüksek kaliteli pozisyon listelendi.")

                # Persona dağılımı analizi
                if high_quality_jobs and (
                    "persona_source" in high_quality_jobs[0] or "persona" in high_quality_jobs[0]
                ):
                    persona_counts = {}
                    for job in high_quality_jobs:
                        persona = job.get("persona_source", job.get("persona", "Unknown"))
                        persona_counts[persona] = persona_counts.get(persona, 0) + 1

                    logger.info("\n📈 Persona Dağılımı:")
                    for persona, count in sorted(persona_counts.items(), key=lambda x: x[1], reverse=True):
                        logger.info(f"   {persona}: {count} ilan")

            else:
                logger.warning(
                    f"⚠️  Filtreleme sonrası {len(filtered_jobs)} ilan bulundu ama "
                    f"uygunluk eşiği (%{MIN_SIMILARITY_THRESHOLD}) altında."
                )
                logger.info("💡 Eşiği düşürmeyi veya persona terimlerini genişletmeyi düşünebilirsiniz.")

        else:
            logger.warning("❌ Filtreleme sonrası uygun pozisyon bulunamadı! Kriterleri gözden geçirin.")
    else:
        logger.warning("❌ Benzer iş bulunamadı!")


def print_manual_validation_guide():
    """JobSpy Gelişmiş Özellikler için Manuel Doğrulama Protokolü"""
    logger.info("\n" + "=" * 80)
    logger.info("📋 JOBSPY GELİŞMİŞ ÖZELLİKLER - MANUEL DOĞRULAMA PROTOKOLÜ")
    logger.info("=" * 80)
    logger.info("🎯 SİSTEM DURUMU: JobSpy Native (hours_old=72, cosine similarity)")
    logger.info("🚀 Optimize Özellikler: Çoklu site, gelişmiş operatörler, 12 persona")
    logger.info("📊 Beklenen Performans: 100-300 benzersiz ilan, %80+ uygunluk oranı")
    logger.info("=" * 80)


def main():
    """Tek komutla tam otomatik AI kariyer analizi"""
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

    except (OSError, IOError) as e:
        logger.error(f"❌ HATA: CV dosyası erişim hatası: {e}")
        return

    logger.info("✅ Sistem kontrolleri başarılı")
    logger.info("🎯 12 farklı JobSpy optimize edilmiş persona ile veri toplama başlatılıyor...\n")

    # Tam otomatik analiz çalıştır
    analyze_and_find_best_jobs()


# Test fonksiyonları için
if __name__ == "__main__":
    main()
