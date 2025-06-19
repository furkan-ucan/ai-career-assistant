"""
Akıllı Kariyer Asistanı - Ana Uygulama (BÖL VE FETHET STRATEJİSİ)
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
from src.filter import filter_junior_suitable_jobs, filter_jobs_by_date

# Konfigürasyon sabitleri
ENABLE_DATE_FILTER = True  # Manuel doğrulama için True yapın
DATE_FILTER_DAYS = 3       # Son X gün içindeki ilanlar
MIN_SIMILARITY_THRESHOLD = 50  # Benzerlik eşiği (%) - Daha fazla sonuç için düşürüldü

def collect_data_for_all_personas():
    """
    Tüm personalar için ayrı ayrı veri toplar ve sonuçları birleştirir.
    BÖL VE FETHET stratejisi: Karmaşık bir sorgu yerine basit sorgular
    """
    print("\n🔍 Stratejik Veri Toplama Başlatılıyor (Böl ve Fethet - Çoklu Site)...")
    print("=" * 60)

    # Her bir persona için basit ve etkili arama terimleri
    persona_search_terms = {
        "Yazilim_Gelistirici": "Yazılım Geliştirici",
        "Full_Stack": "Full Stack Developer",
        "React_Developer": "React Developer",
        "Python_Developer": "Python Developer",
        "Analist": "İş Analisti",
        "Veri_Analisti": "Veri Analisti",
        "Business_Analyst": "Business Analyst",
        "ERP_Danismani": "ERP Danışmanı",
        "ERP_Specialist": "ERP Specialist",
        "Proses_Gelistirme": "Süreç Geliştirme",
        "Flutter_Developer": "Flutter Developer",
        "TypeScript_Developer": "TypeScript"
    }

    all_jobs_list = []
    total_collected = 0

    for persona, term in persona_search_terms.items():
        print(f"\n--- Persona '{persona}' için arama yapılıyor ---")
        print(f"🔍 Arama terimi: '{term}'")

        try:
            # Her persona için çoklu site araması (DataFrame döndürür)
            jobs_df = collect_job_data(search_term=term, max_results_per_site=20)

            if jobs_df is not None and not jobs_df.empty:
                print(f"✅ {len(jobs_df)} ilan toplandı")                # Persona bilgisini ekle
                jobs_df['persona'] = persona
                jobs_df['search_term'] = term
                all_jobs_list.append(jobs_df)
                total_collected += len(jobs_df)
            else:
                print(f"❌ '{term}' için ilan bulunamadı")

        except Exception as e:
            print(f"❌ '{term}' için hata: {str(e)}")
            continue

    if not all_jobs_list:
        print("❌ Hiçbir persona için ilan bulunamadı. Genel bir sorun olabilir.")
        return None

    # Tüm DataFrame'leri birleştir
    print(f"\n🔄 {len(all_jobs_list)} persona sonucu birleştiriliyor...")
    final_df = pd.concat(all_jobs_list, ignore_index=True)

    print(f"📊 Birleştirme öncesi: {len(final_df)} ilan")    # Tekrarlanan ilanları kaldır (şirket + başlık + lokasyon bazında)
    final_df.drop_duplicates(subset=['company', 'title', 'location'], inplace=True)

    print(f"✨ Tekrar temizleme sonrası: {len(final_df)} benzersiz ilan")

    # NOT: Tarih filtresi burada değil, AI analizi sırasında date_posted field'ı üzerinden yapılacak
    # Çünkü JobSpy'ın date_posted formatı: "1 day ago", "3 days ago" şeklinde

    # Birleştirilmiş veriyi tek bir dosyaya kaydet
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_csv_path = os.path.join(output_dir, f"birlesmis_ilanlar_{timestamp}.csv")
    final_df.to_csv(final_csv_path, index=False, encoding='utf-8')

    print(f"📁 Tüm veriler şuraya kaydedildi: {final_csv_path}")
    print(f"🎯 Toplam başarı: {len(final_df)} benzersiz ilan!")

    return final_csv_path

def analyze_and_find_best_jobs():
    """Tam otomatik analiz: Stratejik veri toplama + AI analizi + Sonuçlar"""
    print("\n🚀 Tam Otomatik AI Kariyer Analizi Başlatılıyor...")
    print("=" * 60)

    # 1. BÖL VE FETHET ile fresh data toplayalım
    print("🔄 1/6: Stratejik veri toplama...")
    csv_path = collect_data_for_all_personas()  # YENİ FONKSİYONU ÇAĞIRIYORUZ
    if not csv_path:
        print("❌ Veri toplama başarısız - analiz durduruluyor!")
        return

    # 2. CV'yi işle
    print("\n📄 2/6: CV analizi...")
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
    print("\n🗃️ 3/6: Vector store hazırlığı...")
    vector_store = VectorStore()

    # 4. İş ilanlarını vector store'a yükle
    print("🔄 4/6: İş ilanları vector store'a yükleniyor...")

    # CSV'yi oku
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

    print("✅ Vector store hazır")    # 5. Benzer işleri bul ve filtrele
    print("\n🔄 6/6: Akıllı eşleştirme ve filtreleme...")
    similar_jobs = vector_store.search_similar_jobs(cv_embedding, top_k=30)  # Daha fazla al

    if similar_jobs:
        # ADIM 1: Tarih filtresi (manuel doğrulama ile aynı zaman penceresi)
        if ENABLE_DATE_FILTER:
            print(f"📅 Tarih filtresi uygulanıyor (son {DATE_FILTER_DAYS} gün)...")
            similar_jobs = filter_jobs_by_date(similar_jobs, max_days=DATE_FILTER_DAYS, debug=False)
            print(f"📊 Tarih filtresi sonrası: {len(similar_jobs)} ilan")
          # ADIM 2: YBS odaklı detaylı filtreleme
        print("🔍 Sonuçlar YBS/junior pozisyonlar için akıllı filtreleme...")
        filtered_jobs = filter_junior_suitable_jobs(similar_jobs, debug=False)

        if filtered_jobs:
            # ADIM 3: Uygunluk puanı eşiği ekleme (Strateji 3)
            high_quality_jobs = [job for job in filtered_jobs if job['similarity_score'] >= MIN_SIMILARITY_THRESHOLD]

            if high_quality_jobs:
                print(f"✅ {len(high_quality_jobs)} adet yüksek kaliteli pozisyon bulundu!")
                print(f"📊 Uygunluk eşiği: %{MIN_SIMILARITY_THRESHOLD} ve üzeri")

                print("\n" + "="*70)
                print("🎉 SİZE ÖZEL EN UYGUN İŞ İLANLARI")
                print("🎯 YBS + Full-Stack + Veri Analizi Odaklı")
                print("="*70)

                for i, job in enumerate(high_quality_jobs[:15], 1):  # Top 15 göster
                    print(f"\n{i}. {job['title']} - {job['company']}")
                    print(f"   📍 {job['location']}")
                    print(f"   📊 Uygunluk: %{job['similarity_score']:.1f}")
                    if 'persona' in job:
                        print(f"   🎭 Persona: {job['persona']}")
                    print(f"   🔗 {job['url']}")
                    print("-" * 50)

                print(f"\n🎯 Analiz tamamlandı! {len(high_quality_jobs)} yüksek kaliteli pozisyon listelendi.")

                # Persona dağılımı analizi
                if high_quality_jobs and 'persona' in high_quality_jobs[0]:
                    persona_counts = {}
                    for job in high_quality_jobs:
                        persona = job.get('persona', 'Unknown')
                        persona_counts[persona] = persona_counts.get(persona, 0) + 1

                    print(f"\n📈 Persona Dağılımı:")
                    for persona, count in sorted(persona_counts.items(), key=lambda x: x[1], reverse=True):
                        print(f"   {persona}: {count} ilan")

            else:
                print(f"⚠️  Filtreleme sonrası {len(filtered_jobs)} ilan bulundu ama uygunluk eşiği (%{MIN_SIMILARITY_THRESHOLD}) altında.")
                print("💡 Eşiği düşürmeyi veya persona terimlerini genişletmeyi düşünebilirsiniz.")

        else:
            print("❌ Filtreleme sonrası uygun pozisyon bulunamadı! Kriterleri gözden geçirin.")
    else:
        print("❌ Benzer iş bulunamadı!")

def print_manual_validation_guide():
    """Manuel doğrulama protokolü rehberini yazdırır"""
    print("\n" + "="*80)
    print("📋 MANUEL DOĞRULAMA PROTOKOLÜ REHBERİ")
    print("🔬 Sistemin 'kör noktalarını' tespit etmek için adım adım rehber")
    print("="*80)

    print(f"""
🔹 ADIM 1: Manuel Arama (Indeed'de)
   • Indeed.com'da giriş yapın
   • Filtreler: 'Son {DATE_FILTER_DAYS} gün', 'Türkiye', 'Entry Level/Junior'
   • Arama terimleri (sırayla deneyin):
     - "Yazılım Geliştirici"
     - "Full Stack Developer"
     - "İş Analisti"
     - "ERP Danışmanı"
   • 2-3 tane "mükemmel uyum" ilan tespit edin ve kaydedin

🔹 ADIM 2: Sistem Çalıştırma
   • Bu scripti çalıştırın (ENABLE_DATE_FILTER=True olduğundan emin olun)
   • Sistem otomatik olarak son {DATE_FILTER_DAYS} günlük ilanları filtreleyecek
   • Sonuçlar görüntülendiğinde manuel bulduğunuz ilanları kontrol edin

🔹 ADIM 3: Karşılaştırma Analizi
   • Manuel bulduğunuz "mükemmel uyum" ilanlar sistem sonuçlarında var mı?
   • VARSA: ✅ Sistem çalışıyor, kör nokta yok
   • YOKSA: ❌ KÖR NOKTA TESPİT EDİLDİ!

🔹 ADIM 4: Kör Nokta Düzeltme (eğer varsa)
   • Kaçırılan ilanların arama terimlerini analiz edin
   • persona_search_terms listesine yeni terimler ekleyin
   • Filtreleme kriterlerini gözden geçirin
   • Tekrar test edin

🔹 ADIM 5: Sürekli İyileştirme
   • Bu protokolü haftalık çalıştırın
   • Yeni iş trendlerini yakalayın
   • Sistem performansını takip edin

💡 NOT: Bu protokol bilimsel doğrulamanın temelini oluşturur!
""")

    print("="*80)
    print(f"🎯 SİSTEM DURUMU: Tarih filtresi {'AÇIK' if ENABLE_DATE_FILTER else 'KAPALI'} (≤{DATE_FILTER_DAYS} gün)")
    print("="*80)

def main():
    """Tek komutla tam otomatik AI kariyer analizi"""
    print("🚀 Akıllı Kariyer Asistanı - Böl ve Fethet Stratejisi")
    print("=" * 60)

    # Manuel doğrulama rehberini göster
    print_manual_validation_guide()

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
    print("🎯 12 farklı persona ile stratejik veri toplama başlatılıyor...\n")

    # Tam otomatik analiz çalıştır
    analyze_and_find_best_jobs()


# Test fonksiyonları için
if __name__ == "__main__":
    main()
