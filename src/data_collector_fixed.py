"""
Veri Toplama Modülü - JobSpy Gelişmiş Özellikler ile Optimize Edilmiş
JobSpy'ın advanced features (hours_old, gelişmiş search queries, site-specific params) kullanarak
birden fazla platformdan CV'ye uygun iş ilanlarını toplar.
"""

# Standard Library
import logging
from datetime import datetime
from pathlib import Path

# Third Party
import pandas as pd
from jobspy import scrape_jobs

logger = logging.getLogger(__name__)

# --- VARSAYILAN AYARLAR ---
VARSAYILAN_LOKASYON = "Turkey"
VARSAYILAN_MAX_SONUC_PER_SITE = 50  # Her site için ayrı limit
HEDEFLENEN_SITELER = ["indeed", "linkedin"]  # ÇOK ÖNEMLİ: LinkedIn öncelikli!


def collect_job_data(
    search_term,
    location=VARSAYILAN_LOKASYON,
    max_results_per_site=VARSAYILAN_MAX_SONUC_PER_SITE,
    site_names=HEDEFLENEN_SITELER,
    hours_old=72,  # JobSpy native tarih filtresi (varsayılan: 3 gün)
):
    """
    JobSpy'ın gelişmiş özelliklerini kullanarak optimize edilmiş iş ilanı toplama.

    Args:
        search_term: Arama terimi - Indeed için gelişmiş operatörler desteklenir
        location: Arama lokasyonu (varsayılan: Turkey)
        max_results_per_site: Her site için maksimum sonuç sayısı
        site_names: Hedeflenen siteler listesi
        hours_old: Son X saat içindeki ilanlar (JobSpy native filtre)

    Returns:
        pandas.DataFrame: Birleştirilmiş iş ilanları veya None (hata durumunda)
    """
    logger.info("\n🔍 JobSpy Gelişmiş Arama Başlatılıyor...")
    logger.info(f"📍 Lokasyon: {location}")
    logger.info(f"🎯 Hedef: {max_results_per_site} ilan/site")
    logger.info(f"⏰ Tarih filtresi: Son {hours_old} saat (JobSpy native)")
    logger.info(f"🔍 Arama terimi: '{search_term}'")
    logger.info("⏳ Bu işlem birkaç dakika sürebilir...")

    all_jobs_list = []

    for site in site_names:
        logger.info(f"\n--- Site '{site}' için arama yapılıyor ---")
        try:
            # JobSpy'ın gelişmiş parametreleri
            scrape_params = {
                "site_name": site,
                "search_term": search_term,
                "location": location,
                "results_wanted": max_results_per_site,
                "hours_old": hours_old,  # Native tarih filtresi
            }

            # Site-specific optimizations
            if site == "indeed":
                scrape_params["country_indeed"] = "Turkey"
                logger.info("   🎯 Indeed: Türkiye özel ayarları aktif")
            elif site == "linkedin":
                scrape_params["linkedin_fetch_description"] = True  # Detaylı LinkedIn verisi
                logger.info("   💼 LinkedIn: Detaylı açıklama ve direkt URL çekiliyor...")

            # JobSpy ile veri çek
            jobs_from_site = scrape_jobs(**scrape_params)

            if jobs_from_site is not None and not jobs_from_site.empty:
                logger.info(f"✅ '{site}' sitesinden {len(jobs_from_site)} ilan toplandı.")
                jobs_from_site["source_site"] = site  # Hangi siteden geldiğini işaretle
                all_jobs_list.append(jobs_from_site)
            else:
                logger.info(f"ℹ️ '{site}' sitesinden bu arama terimi için ilan bulunamadı.")

        except Exception as e:
            logger.error(f"❌ '{site}' sitesinden veri toplarken hata: {str(e)}", exc_info=True)
            continue  # Bir sitede hata olursa diğerlerine devam et

    # Tüm siteler tarandıktan sonra kontrol et
    if not all_jobs_list:
        logger.error("❌ Hiçbir siteden ilan bulunamadı!")
        return None

    # Tüm sitelerden gelen DataFrame'leri birleştir
    combined_df = pd.concat(all_jobs_list, ignore_index=True)

    # Zaman damgası ekle
    combined_df["collected_at"] = datetime.now()

    # Gelişmiş deduplication (farklı sitelerden aynı ilan gelebilir)
    logger.info("\n🔄 Deduplication başlatılıyor...")
    initial_count = len(combined_df)

    if "description" in combined_df.columns:
        # Açıklama varsa daha hassas deduplication
        combined_df["description_short"] = combined_df["description"].str[:100]
        combined_df.drop_duplicates(
            subset=["title", "company", "location", "description_short"],
            inplace=True,
            keep="first"
        )
        combined_df.drop(columns=["description_short"], inplace=True)
    else:
        # Temel deduplication
        combined_df.drop_duplicates(
            subset=["title", "company", "location"],
            inplace=True,
            keep="first"
        )

    final_count = len(combined_df)
    removed_count = initial_count - final_count
    logger.info("✨ Deduplication tamamlandı:")
    logger.info(f"   📊 Başlangıç: {initial_count} ilan")
    logger.info(f"   🗑️ Çıkarılan tekrar: {removed_count} ilan")
    logger.info(f"   ✅ Final: {final_count} benzersiz ilan")

    return combined_df


# CSV kaydetme fonksiyonu (isteğe bağlı)
def save_jobs_to_csv(jobs_df, filename_prefix="jobspy_ilanlar"):
    """
    İş ilanlarını CSV dosyasına kaydeder
    """
    if jobs_df is None or jobs_df.empty:
        logger.error("❌ Kaydedilecek veri yok!")
        return None

    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"{filename_prefix}_{timestamp}.csv"

    jobs_df.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info(f"📁 Dosya kaydedildi: {csv_path}")

    return csv_path


if __name__ == "__main__":
    # Test için basit bir çalıştırma
    logger.info("🧪 JobSpy Gelişmiş Özellikler Test Ediliyor...")

    test_df = collect_job_data(
        search_term="Software Engineer",
        max_results_per_site=10,
        hours_old=72
    )

    if test_df is not None:
        logger.info(f"\n✅ Test sonucu: {len(test_df)} ilan bulundu.")
        logger.info(f"📊 Site dağılımı: {test_df['source_site'].value_counts().to_dict()}")
        save_jobs_to_csv(test_df, "test_advanced_jobspy")
