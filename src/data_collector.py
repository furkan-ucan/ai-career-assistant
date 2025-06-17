"""
Veri Toplama Modülü - Akıllı Arama
JobSpy kullanarak CV'ye uygun geniş spektrumda iş ilanlarını toplar.
"""

from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
import os

# --- ESKİ KARMAŞIK ARAMA (GEÇİCİ OLARAK DEVRE DIŞI) ---
# ARAMA_TERIMI = (
#     # Yazılım Geliştirme Hedefleri
#     "(\"Full Stack Developer\" OR \"React Developer\" OR \"NestJS Developer\" OR "
#     "\"TypeScript Developer\" OR \"Flutter Developer\" OR \"Python Developer\" OR "
#     "\"Yazılım Geliştirici\" OR \"Software Developer\" OR \"Frontend Developer\" OR \"Backend Developer\") OR "
#
#     # Analist ve Veri Hedefleri
#     "(\"Veri Analisti\" OR \"Data Analyst\" OR \"İş Analisti\" OR \"Business Analyst\" OR "
#     "\"Sistem Analisti\" OR \"İş Zekası Uzmanı\" OR \"Business Intelligence\" OR "
#     "\"Süreç Analisti\" OR \"Process Analyst\") OR "
#
#     # YBS ve ERP Hedefleri (EN ÖNEMLİ EKLEME!)
#     "(\"ERP Danışmanı\" OR \"ERP Specialist\" OR \"ERP Consultant\" OR \"Süreç Geliştirme Uzmanı\" OR "
#     "\"Yönetim Bilişim Sistemleri\" OR \"Process Improvement\" OR \"SAP Consultant\" OR "
#     "\"Microsoft Dynamics\" OR \"Proje Yönetimi\" OR \"Project Coordinator\" OR "
#     "\"Coğrafi Bilgi Sistemleri\" OR \"GIS Specialist\" OR \"Operasyon Uzmanı\")"
#
#     # Ön Filtreleme - Sadece kesinlikle senior olanlar
#     " NOT (Senior OR Lead OR Principal OR Direktör OR Kıdemli OR \"Team Lead\")"
# )

# --- YENİ BASİT TEST ARAMASI ---
ARAMA_TERIMI = "İş Analisti"  # Sadece bu basit terimi test edelim

# --- VARSAYILAN AYARLAR ---
VARSAYILAN_LOKASYON = "Turkey"
VARSAYILAN_MAX_SONUC = 100  # Daha geniş havuz için artırıldı

def collect_job_data(search_term=ARAMA_TERIMI, location=VARSAYILAN_LOKASYON, max_results=VARSAYILAN_MAX_SONUC):
    """
    CV'ye uygun geniş spektrumda iş ilanlarını toplar ve CSV'ye kaydeder

    Args:
        search_term: Akıllı arama sorgusu (varsayılan: CV'ye optimized)
        location: Arama lokasyonu (varsayılan: Turkey)
        max_results: Maksimum sonuç sayısı (varsayılan: 100)

    Returns:
        str: Kaydedilen CSV dosyasının yolu veya None (hata durumunda)
    """
    print(f"🔍 Akıllı İş Arama Başlatılıyor...")
    print(f"📍 Lokasyon: {location}")
    print(f"🎯 Hedef: {max_results} ilan")
    print("⏳ Bu işlem birkaç dakika sürebilir (geniş spektrum arama)...")

    try:
        # Çoklu platform ile daha kapsamlı arama
        jobs = scrape_jobs(
            site_name="indeed",  # Stabil platform
            search_term=search_term,
            location=location,
            results_wanted=max_results,
            country_indeed="Turkey"
        )

        if jobs is None or jobs.empty:
            print("❌ Hiç ilan bulunamadı!")
            print("💡 İpucu: Arama terimlerini kontrol edin veya lokasyonu değiştirin.")
            return None

        # Zaman damgası ekle
        jobs['collected_at'] = datetime.now()

        # Çıktı dizinini hazırla
        output_dir = "data"
        os.makedirs(output_dir, exist_ok=True)

        # Dosya adı oluştur
        output_file = os.path.join(output_dir, f"ham_ilanlar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        # CSV'ye kaydet
        jobs.to_csv(output_file, index=False, encoding='utf-8')

        print(f"✅ {len(jobs)} ilan toplandı!")
        print(f"📁 Dosya kaydedildi: {output_file}")
        print("🎯 Akıllı arama spektrumu:")
        print("   - Full Stack, React, NestJS, TypeScript")
        print("   - Veri Analisti, İş Analisti, ERP")
        print("   - Flutter, Python, GIS, Data Science")

        return output_file

    except Exception as e:
        print(f"❌ Veri toplama hatası: {str(e)}")
        print("🔧 Çözüm önerileri:")
        print("   - İnternet bağlantınızı kontrol edin")
        print("   - Birkaç dakika bekleyip tekrar deneyin")
        print("   - max_results sayısını azaltın")
        return None

if __name__ == "__main__":
    # Test çalıştırması
    collect_job_data()
