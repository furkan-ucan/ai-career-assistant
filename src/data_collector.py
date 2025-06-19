"""
Veri Toplama Modülü - Çoklu Site Desteği ile Akıllı Arama
JobSpy kullanarak birden fazla platformdan CV'ye uygun iş ilanlarını toplar.
"""

from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
import os

# --- VARSAYILAN AYARLAR ---
VARSAYILAN_LOKASYON = "Turkey"
VARSAYILAN_MAX_SONUC_PER_SITE = 50  # Her site için ayrı limit
HEDEFLENEN_SITELER = ["indeed", "linkedin"]  # ÇOK ÖNEMLİ: Önce Indeed (daha stabil), sonra LinkedIn

def collect_job_data(
    search_term,
    location=VARSAYILAN_LOKASYON,
    max_results_per_site=VARSAYILAN_MAX_SONUC_PER_SITE,
    site_names=HEDEFLENEN_SITELER
):
    """
    Belirtilen sitelerden ve parametrelerle iş ilanlarını toplar.

    Args:
        search_term: Arama terimi (zorunlu)
        location: Arama lokasyonu (varsayılan: Turkey)
        max_results_per_site: Her site için maksimum sonuç sayısı
        site_names: Hedeflenen siteler listesi

    Returns:
        pandas.DataFrame: Birleştirilmiş iş ilanları veya None (hata durumunda)
    """
    print(f"\n🔍 Akıllı İş Arama Başlatılıyor...")
    print(f"📍 Lokasyon: {location}")
    print(f"🎯 Hedef: {max_results_per_site} ilan")
    print("⏳ Bu işlem birkaç dakika sürebilir (geniş spektrum arama)...")

    print("🎯 Akıllı arama spektrumu:")
    print("   - Full Stack, React, NestJS, TypeScript")
    print("   - Veri Analisti, İş Analisti, ERP")
    print("   - Flutter, Python, GIS, Data Science")

    all_jobs_list = []

    for site in site_names:
        print(f"\n--- Site '{site}' için arama yapılıyor ---")
        try:
            # Site-specific parameters
            scrape_params = {
                'site_name': site,
                'search_term': search_term,
                'location': location,
                'results_wanted': max_results_per_site,
                'hours_old': 72  # Son 3 gün için (JobSpy native date filter)
            }

            # Site-specific optimizations
            if site == "indeed":
                scrape_params['country_indeed'] = "Turkey"
            elif site == "linkedin":
                scrape_params['linkedin_fetch_description'] = True  # Daha detaylı LinkedIn verisi
                print("   💼 LinkedIn: Detaylı açıklama ve direkt URL çekiliyor...")

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

    # Tekrarlanan ilanları temizle (farklı sitelerden aynı ilan gelebilir)
    if 'description' in combined_df.columns:
        combined_df['description_short'] = combined_df['description'].str[:100]
        combined_df.drop_duplicates(subset=['title', 'company', 'location', 'description_short'], inplace=True, keep='first')
        combined_df.drop(columns=['description_short'], inplace=True)
    else:
        combined_df.drop_duplicates(subset=['title', 'company', 'location'], inplace=True, keep='first')

    print(f"\n✨ Toplamda {len(combined_df)} adet benzersiz ilan (tüm sitelerden) bulundu.")

    return combined_df  # DataFrame döndür

# CSV kaydetme fonksiyonu (isteğe bağlı)
def save_jobs_to_csv(jobs_df, filename_prefix="ham_ilanlar"):
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

# Eski main.py uyumluluğu için wrapper fonksiyon
def collect_job_data_legacy(search_term, location=VARSAYILAN_LOKASYON, max_results=20):
    """
    Eski main.py uyumluluğu için wrapper. DataFrame yerine CSV path döndürür.
    """
    jobs_df = collect_job_data(
        search_term=search_term,
        location=location,
        max_results_per_site=max_results,
        site_names=["indeed"]  # Eski davranış için sadece Indeed
    )

    if jobs_df is not None:
        return save_jobs_to_csv(jobs_df)
    else:
        return None

if __name__ == "__main__":
    # Test için basit bir çalıştırma
    test_df = collect_job_data(search_term="Python Developer", max_results_per_site=10)
    if test_df is not None:
        print(f"\nTest sonucu: {len(test_df)} ilan bulundu.")
        print(f"Siteler: {test_df['source_site'].value_counts().to_dict()}")
        save_jobs_to_csv(test_df, "test_multi_site")
