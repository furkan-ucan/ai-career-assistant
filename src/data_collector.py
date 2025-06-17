"""
Veri Toplama Modülü
JobSpy kullanarak iş ilanlarını toplar ve CSV dosyasına kaydeder.
"""

from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
import os

def collect_job_data(search_term="python", location="Turkey", max_results=50):
    """
    İş ilanlarını toplar ve CSV'ye kaydeder

    Args:
        search_term: Arama terimi
        location: Lokasyon
        max_results: Maksimum sonuç sayısı
    """
    print(f"🔍 İş ilanları aranıyor: '{search_term}' - {location}")

    try:
        # İş ilanlarını çek
        jobs = scrape_jobs(
            site_name="indeed",
            search_term=search_term,
            location=location,
            results_wanted=max_results,
            country_indeed="Turkey"
        )

        if jobs.empty:
            print("❌ Hiç ilan bulunamadı!")
            return None

        # Timestamp ekle
        jobs['collected_at'] = datetime.now()

        # CSV'ye kaydet
        output_file = f"data/ham_ilanlar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        jobs.to_csv(output_file, index=False, encoding='utf-8')

        print(f"✅ {len(jobs)} ilan toplandı ve kaydedildi: {output_file}")
        return jobs

    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        return None

if __name__ == "__main__":
    # Test çalıştırması
    collect_job_data()
