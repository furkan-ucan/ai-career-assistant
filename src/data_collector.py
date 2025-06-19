"""
Veri Toplama Modülü - JobSpy Gelişmiş Özellikler ile Optimize Edilmiş
JobSpy'ın advanced features (hours_old, gelişmiş search queries, site-specific params) kullanarak
birden fazla platformdan CV'ye uygun iş ilanlarını toplar.
"""

from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
import os

# --- VARSAYILAN AYARLAR ---
VARSAYILAN_LOKASYON = "Turkey"
VARSAYILAN_MAX_SONUC_PER_SITE = 50  # Her site için ayrı limit
HEDEFLENEN_SITELER = ["indeed", "linkedin"]  # ÇOK ÖNEMLİ: LinkedIn öncelikli!

def collect_job_data(
    search_term,
    location=VARSAYILAN_LOKASYON,
    max_results_per_site=VARSAYILAN_MAX_SONUC_PER_SITE,
    site_names=HEDEFLENEN_SITELER,
    hours_old=72  # JobSpy native tarih filtresi (varsayılan: 3 gün)
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
    print(f"\n🔍 JobSpy Gelişmiş Arama Başlatılıyor...")
    print(f"📍 Lokasyon: {location}")
    print(f"🎯 Hedef: {max_results_per_site} ilan/site")
    print(f"⏰ Tarih filtresi: Son {hours_old} saat (JobSpy native)")
    print(f"🔍 Arama terimi: '{search_term}'")
    print("⏳ Bu işlem birkaç dakika sürebilir...")

    all_jobs_list = []

    for site in site_names:
        print(f"\n--- Site '{site}' için arama yapılıyor ---")
        try:
            # JobSpy'ın gelişmiş parametreleri
            scrape_params = {
                'site_name': site,
                'search_term': search_term,
                'location': location,
                'results_wanted': max_results_per_site,
                'hours_old': hours_old  # Native tarih filtresi
            }

            # Site-specific optimizations
            if site == "indeed":
                scrape_params['country_indeed'] = "Turkey"
                print("   🎯 Indeed: Türkiye özel ayarları aktif")

            elif site == "linkedin":
                scrape_params['linkedin_fetch_description'] = True  # Detaylı LinkedIn verisi
                print("   💼 LinkedIn: Detaylı açıklama ve direkt URL çekiliyor...")

            # JobSpy ile veri çek
            jobs_from_site = scrape_jobs(**scrape_params)

            if jobs_from_site is not None and not jobs_from_site.empty:
                print(f"✅ '{site}' sitesinden {len(jobs_from_site)} ilan toplandı.")
                jobs_from_site['source_site'] = site  # Hangi siteden geldiğini işaretle
                all_jobs_list.append(jobs_from_site)
            else:
                print(f"ℹ️ '{site}' sitesinden bu arama terimi için ilan bulunamadı.")

        except Exception as e:
            print(f"❌ '{site}' sitesinden veri toplarken hata: {str(e)}")
            continue  # Bir sitede hata olursa diğerlerine devam et

    if not all_jobs_list:
        print("❌ Hiçbir siteden ilan bulunamadı!")
        return None

    # Tüm sitelerden gelen DataFrame'leri birleştir
    combined_df = pd.concat(all_jobs_list, ignore_index=True)

    # Zaman damgası ekle
    combined_df['collected_at'] = datetime.now()

    # Gelişmiş deduplication (farklı sitelerden aynı ilan gelebilir)
    print(f"\n🔄 Deduplication başlatılıyor...")
    initial_count = len(combined_df)

    if 'description' in combined_df.columns:
        # Açıklama varsa daha hassas deduplication
        combined_df['description_short'] = combined_df['description'].str[:100]
        combined_df.drop_duplicates(
            subset=['title', 'company', 'location', 'description_short'],
            inplace=True,
            keep='first'
        )
        combined_df.drop(columns=['description_short'], inplace=True)
    else:
        # Temel deduplication
        combined_df.drop_duplicates(
            subset=['title', 'company', 'location'],
            inplace=True,
            keep='first'
        )

    final_count = len(combined_df)
    removed_count = initial_count - final_count

    print(f"✨ Deduplication tamamlandı:")
    print(f"   📊 Başlangıç: {initial_count} ilan")
    print(f"   🗑️ Çıkarılan tekrar: {removed_count} ilan")
    print(f"   ✅ Final: {final_count} benzersiz ilan")

    return combined_df

# CSV kaydetme fonksiyonu (isteğe bağlı)
def save_jobs_to_csv(jobs_df, filename_prefix="jobspy_ilanlar"):
    """
    İş ilanlarını CSV dosyasına kaydeder
    """
    if jobs_df is None or jobs_df.empty:
        print("❌ Kaydedilecek veri yok!")
        return None

    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.csv")

    jobs_df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"📁 Dosya kaydedildi: {csv_path}")

    return csv_path

if __name__ == "__main__":
    # Test için basit bir çalıştırma
    print("🧪 JobSpy Gelişmiş Özellikler Test Ediliyor...")

    test_df = collect_job_data(
        search_term="Software Engineer",
        max_results_per_site=10,
        hours_old=72
    )

    if test_df is not None:
        print(f"\n✅ Test sonucu: {len(test_df)} ilan bulundu.")
        print(f"📊 Site dağılımı: {test_df['source_site'].value_counts().to_dict()}")
        save_jobs_to_csv(test_df, "test_advanced_jobspy")
    else:
        print("❌ Test başarısız!")
