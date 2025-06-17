"""
Akıllı Kariyer Asistanı - Ana Uygulama
Bu dosya, tüm sistem bileşenlerini koordine eder ve uygulamanın giriş noktasıdır.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Environment variables yükle
load_dotenv()

# Modülleri import et
from src.data_collector import collect_job_data
from src.cv_processor import CVProcessor
from src.embedding_service import EmbeddingService
from src.vector_store import VectorStore

def filter_junior_suitable_jobs(jobs_list, debug=False):
    """
    Junior/Entry-level pozisyonlar için uygun olmayan ilanları filtreler
    YBS öğrencisinin kariyer hedefleri (ERP, Proje Yönetimi, İş Analizi) göz önünde bulundurularak optimizasyon
    """
    # Başlık blacklist - SADECE kesinlikle senior olanları hedefler
    title_blacklist = [
        'senior', 'sr.', 'sr ', 'lead', 'principal', 'manager', 
        'direktör', 'müdür', 'chief', 'head', 'supervisor', 
        'team lead', 'tech lead', 'kıdemli', 'başkan',
        'architect', 'baş ', 'lider', 'leader'
        # 'uzman', 'consultant', 'sorumlu' ÇIKARILDI - YBS için gerekli!
    ]
    
    # Deneyim blacklist - Sadece çok net ve yüksek yıl ifadeleri
    experience_blacklist = [
        '5+ yıl', '5 yıl', '5+ years', '5 years', '6+ yıl', '7+ yıl', 
        '8+ yıl', '10+ yıl', 'en az 5 yıl', 'minimum 5 years',
        'minimum 6', 'en az 6', 'minimum 7', 'en az 7'
        # 3-4 yıl ifadeleri ÇIKARILDI - entry-level için makul
    ]
    
    # Sorumluluk blacklist - Sadece doğrudan personel yönetimi içerenler
    # "Proje Yönetimi" VE "ERP" ifadeleri ÇIKARILDI!
    responsibility_blacklist = [
        'takım yönetimi', 'team management', 'personel yönetimi',
        'bütçe yönetimi', 'budget responsibility', 'işe alım', 'hiring',
        'direct reports', 'performans değerlendirme', 'team building'
        # 'proje yönetimi', 'project management' ÇIKARILDI - YBS için kritik!
    ]
    
    filtered_jobs = []
    filter_stats = {'title': 0, 'experience': 0, 'responsibility': 0, 'passed': 0}
    
    for job in jobs_list:
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        
        # 1. Başlık kontrolü
        title_rejected = any(word in title for word in title_blacklist)
        
        # 2. Deneyim kontrolü
        experience_rejected = any(exp in description for exp in experience_blacklist)
        
        # 3. Sorumluluk kontrolü
        responsibility_rejected = any(resp in description for resp in responsibility_blacklist)
        
        # Filtreleme kararı
        if title_rejected:
            filter_stats['title'] += 1
            if debug:
                print(f"🔥 Filtrelendi (başlık): {job.get('title', 'N/A')}")
        elif experience_rejected:
            filter_stats['experience'] += 1
            if debug:
                print(f"🔥 Filtrelendi (deneyim): {job.get('title', 'N/A')}")
        elif responsibility_rejected:
            filter_stats['responsibility'] += 1
            if debug:
                print(f"🔥 Filtrelendi (sorumluluk): {job.get('title', 'N/A')}")
        else:
            # Geçti - listeye ekle
            filtered_jobs.append(job)
            filter_stats['passed'] += 1
            if debug:
                print(f"✅ Geçti: {job.get('title', 'N/A')}")
    
    # Filtreleme istatistikleri
    total_processed = len(jobs_list)
    print(f"\n� Filtreleme İstatistikleri:")
    print(f"   Toplam işlenen: {total_processed}")
    print(f"   🔥 Başlık filtresi: {filter_stats['title']}")
    print(f"   🔥 Deneyim filtresi: {filter_stats['experience']}")
    print(f"   🔥 Sorumluluk filtresi: {filter_stats['responsibility']}")
    print(f"   ✅ Geçen: {filter_stats['passed']}")
    print(f"   📈 Başarı oranı: %{(filter_stats['passed']/total_processed)*100:.1f}")
    
    return filtered_jobs

def collect_fresh_data():
    """YBS hedeflerine göre güncellenmiş akıllı veri toplama"""
    print("\n🔍 Akıllı Veri Toplama Başlatılıyor...")
    print("=" * 60)
    
    # YBS ve ERP odaklı güncellenmiş arama terimi
    arama_terimi = (
        # Yazılım Geliştirme (Ana yetkinlikler)
        "(\"Full Stack Developer\" OR \"React Developer\" OR \"NestJS Developer\" OR "
        "\"TypeScript Developer\" OR \"Flutter Developer\" OR \"Python Developer\" OR \"Yazılım Geliştirici\") OR "
        
        # Analist ve Veri (Güçlü taraflar)
        "(\"Veri Analisti\" OR \"Data Analyst\" OR \"İş Analisti\" OR \"Business Analyst\" OR "
        "\"Sistem Analisti\" OR \"İş Zekası Uzmanı\" OR \"Business Intelligence\" OR \"Process Analyst\") OR "
        
        # YBS ve ERP (Hedef alan - EN ÖNEMLİ!)
        "(\"ERP Specialist\" OR \"ERP Consultant\" OR \"ERP Danışmanı\" OR \"Süreç Geliştirme\" OR "
        "\"Process Improvement\" OR \"SAP Consultant\" OR \"Microsoft Dynamics\" OR \"İş Süreçleri Uzmanı\" OR "
        "\"Yönetim Bilişim Sistemleri\" OR \"Management Information Systems\" OR \"Business Systems Analyst\")"
        
        # Ön filtreleme - Açık senior roller
        ") NOT (Senior OR Lead OR Principal OR Director OR Direktör OR \"Team Lead\")"
    )
      print(f"🎯 Arama Stratejisi: YBS + ERP + Veri Analizi + Full-Stack")
    print(f"📍 Lokasyon: Türkiye")
    print(f"📊 Hedef: 75 ilan (geniş analiz için)")
    
    try:
        # Güncellenmiş veri toplama çağrısı
        csv_path = collect_job_data(
            search_term=arama_terimi,
            location="Turkey", 
            max_results=75
        )
        
        if csv_path:
            print(f"✅ Veri toplama başarılı: {csv_path}")
            return csv_path
        else:
            print("❌ Veri toplama başarısız!")
            return None
            
    except Exception as e:
        print(f"❌ Veri toplama hatası: {str(e)}")
        return None

def analyze_and_find_best_jobs():
    """Tam otomatik analiz: Veri toplama + AI analizi + Sonuçlar"""
    print("\n🚀 Tam Otomatik AI Kariyer Analizi Başlatılıyor...")
    print("=" * 60)
    
    # 1. Önce fresh data toplayalım
    print("🔄 1/6: Fresh veri toplama...")
    csv_path = collect_fresh_data()
    if not csv_path:
        print("❌ Veri toplama başarısız - analiz durduruluyor!")
        return
    
    # 2. CV'yi işle
    print("\n� 2/6: CV analizi...")
    cv_processor = CVProcessor()
    if not cv_processor.load_cv():
        print("❌ CV yükleme başarısız!")
        return

    if not cv_processor.create_cv_embedding():
        print("❌ CV embedding oluşturma başarısız!")
        return

    cv_embedding = cv_processor.cv_embedding
    print("✅ CV embedding oluşturuldu")
    
    # 3. Vector store'u başlat
    print("\n� 3/6: Vector store hazırlığı...")
    vector_store = VectorStore()

    # 4. İş ilanlarını vector store'a yükle
    print("🔄 4/6: İş ilanları vector store'a yükleniyor...")    # CSV'yi oku
    jobs_df = pd.read_csv(csv_path)
    print(f"📊 {len(jobs_df)} iş ilanı yüklendi")

    # Koleksiyon oluştur
    if not vector_store.create_collection():
        print("❌ Vector store koleksiyon oluşturma başarısız!")
        return

    # İş ilanları için embeddings oluştur
    embedding_service = EmbeddingService()

    print("🔄 5/6: İş ilanları için AI embeddings oluşturuluyor...")
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
    
    # 5. Benzer işleri bul ve filtrele
    print("\n🔄 6/6: Akıllı eşleştirme ve filtreleme...")
    similar_jobs = vector_store.search_similar_jobs(cv_embedding, top_k=25)  # Daha fazla al
    
    if similar_jobs:
        # YBS odaklı detaylı filtreleme
        print("🔍 Sonuçlar YBS/junior pozisyonlar için akıllı filtreleme...")
        filtered_jobs = filter_junior_suitable_jobs(similar_jobs, debug=False)
        
        if filtered_jobs:
            print(f"✅ {len(filtered_jobs)} adet uygun pozisyon bulundu!")
            
            print("\n" + "="*70)
            print("🎉 SİZE ÖZEL EN UYGUN İŞ İLANLARI")
            print("🎯 YBS + Full-Stack + Veri Analizi Odaklı")
            print("="*70)

            for i, job in enumerate(filtered_jobs[:15], 1):  # Top 15 göster
                print(f"\n{i}. {job['title']} - {job['company']}")
                print(f"   📍 {job['location']}")
                print(f"   📊 Uygunluk: %{job['similarity_score']:.1f}")
                print(f"   🔗 {job['url']}")
                print("-" * 50)

            print(f"\n🎯 Analiz tamamlandı! {len(filtered_jobs)} uygun pozisyon listelendi.")
        else:
            print("❌ Filtreleme sonrası uygun pozisyon bulunamadı! Kriterleri gözden geçirin.")
    else:
        print("❌ Benzer iş bulunamadı!")

def main():
    """Tek komutla tam otomatik AI kariyer analizi"""
    print("🚀 Akıllı Kariyer Asistanı - Tam Otomatik Mod")
    print("=" * 60)

    # Ön kontroller
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ HATA: Gemini API key bulunamadı!")
        print("📝 Lütfen .env dosyasında GEMINI_API_KEY değerini ayarlayın.")
        return

    cv_path = "data/cv.txt"
    if not os.path.exists(cv_path):
        print(f"❌ HATA: CV dosyası bulunamadı: {cv_path}")
        print("📝 Lütfen CV'nizi data/cv.txt dosyasına ekleyin.")
        return

    print("✅ Sistem kontrolleri başarılı")
    print("🎯 YBS hedeflerine göre tam otomatik analiz başlatılıyor...\n")
    
    # Tam otomatik analiz çalıştır
    analyze_and_find_best_jobs()


# Test fonksiyonları için
if __name__ == "__main__":
    main()
