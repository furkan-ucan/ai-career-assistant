"""
Akıllı Kariyer Asistanı - Ana Uygulama
Bu dosya, tüm sistem bileşenlerini koordine eder ve uygulamanın giriş noktasıdır.
"""

import os
import sys
from dotenv import load_dotenv

# Environment variables yükle
load_dotenv()

# Modülleri import et
from src.data_collector import collect_job_data
from src.cv_processor import CVProcessor
from src.embedding_service import EmbeddingService
from src.vector_store import VectorStore

def collect_data():
    """Veri toplama testi"""
    print("\n🔍 Veri Toplama Başlatılıyor...")
    print("-" * 40)

    # Python pozisyonları için arama yap
    jobs_df = collect_job_data(
        search_term="python developer",
        location="Turkey",
        max_results=30
    )

    if jobs_df is not None and len(jobs_df) > 0:
        print(f"✅ {len(jobs_df)} adet iş ilanı toplandı!")
        print("📄 Veriler data/ham_ilanlar.csv dosyasına kaydedildi")
        return True
    else:
        print("❌ Veri toplama başarısız!")
        return False

def analyze_and_find_best_jobs():
    """Ana analiz motoru - CV ile iş ilanlarını karşılaştır"""
    print("\n🧠 AI Analiz Motoru Başlatılıyor...")
    print("-" * 40)
      # 1. CV'yi işle
    print("📄 CV analizi yapılıyor...")
    cv_processor = CVProcessor()
    if not cv_processor.load_cv():
        print("❌ CV yükleme başarısız!")
        return

    if not cv_processor.create_cv_embedding():
        print("❌ CV embedding oluşturma başarısız!")
        return

    cv_embedding = cv_processor.cv_embedding
    print("✅ CV embedding oluşturuldu")
      # 2. İş ilanlarını kontrol et
    import glob
    csv_files = glob.glob("data/ham_ilanlar_*.csv")
    if not csv_files:
        print("❌ İş ilanı verisi bulunamadı! Önce veri toplama işlemini çalıştırın.")
        return

    # En son oluşturulan CSV dosyasını kullan
    csv_path = sorted(csv_files)[-1]
    print(f"📊 Kullanılacak veri dosyası: {csv_path}")
      # 3. Vector store'u başlat
    vector_store = VectorStore()

    # 4. İş ilanlarını vector store'a yükle
    print("🔄 İş ilanları vector store'a yükleniyor...")

    # CSV'yi oku
    import pandas as pd
    jobs_df = pd.read_csv(csv_path)
    print(f"📊 {len(jobs_df)} iş ilanı yüklendi")

    # Koleksiyon oluştur
    if not vector_store.create_collection():
        print("❌ Vector store koleksiyon oluşturma başarısız!")
        return

    # İş ilanları için embeddings oluştur
    from src.embedding_service import EmbeddingService
    embedding_service = EmbeddingService()

    print("🔄 İş ilanları için embeddings oluşturuluyor...")
    job_embeddings = []
    for _, job in jobs_df.iterrows():
        if pd.notna(job.get('description', '')):
            embedding = embedding_service.create_embedding(str(job['description']))
            job_embeddings.append(embedding)
        else:
            job_embeddings.append(None)

    # Vector store'a ekle
    success = vector_store.add_jobs(jobs_df, job_embeddings)
    if not success:
        print("❌ Vector store yükleme başarısız!")
        return

    print("✅ Vector store hazır")
      # 5. Benzer işleri bul
    print("🎯 En uygun işler aranıyor...")
    similar_jobs = vector_store.search_similar_jobs(cv_embedding, top_k=15)

    if similar_jobs:
        print("\n" + "="*60)
        print("🎉 EN UYGUN İŞ İLANLARI")
        print("="*60)

        for i, job in enumerate(similar_jobs, 1):
            print(f"\n{i}. {job['title']} - {job['company']}")
            print(f"   📍 {job['location']}")
            print(f"   📊 Uygunluk: %{job['similarity_score']:.1f}")
            print(f"   🔗 {job['url']}")
            print("-" * 50)

        print("\n🎯 Analiz tamamlandı! En uygun pozisyonlar listelendi.")
    else:
        print("❌ Benzer iş bulunamadı!")

def main():
    """Ana uygulama fonksiyonu"""
    print("🚀 Akıllı Kariyer Asistanı Başlatılıyor...")
    print("=" * 50)

    # API key kontrolü
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ HATA: Gemini API key bulunamadı!")
        print("📝 Lütfen .env dosyasında GEMINI_API_KEY değerini ayarlayın.")
        return

    print("✅ Ortam değişkenleri yüklendi")
    print("✅ API key kontrol edildi")

    # CV dosyası kontrolü
    cv_path = "data/cv.txt"
    if not os.path.exists(cv_path):
        print(f"❌ HATA: CV dosyası bulunamadı: {cv_path}")
        print("📝 Lütfen CV'nizi data/cv.txt dosyasına ekleyin.")
        return

    print("✅ CV dosyası bulundu")
    print("\n🎯 Sistem hazır! Test seçenekleri:")
    print("1. Sadece veri toplama: collect_data()")
    print("2. Tam analiz: analyze_and_find_best_jobs()")

# Test fonksiyonları için
if __name__ == "__main__":
    # İlk çalıştırmada sadece sistem kontrolü
    main()

    # Test seçenekleri
    print("\n" + "="*50)
    print("🧠 Ana analiz motoru çalışıyor...")
    analyze_and_find_best_jobs()
