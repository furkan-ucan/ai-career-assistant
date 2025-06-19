"""
Akıllı Kariyer Asistanı - Ana Uygulama (BÖL VE FETHET STRATEJİSİ)
Bu dosya, tüm sistem bileşenlerini koordine eder ve uygulamanın giriş noktasıdır.
"""

import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Environment variables yükle
load_dotenv()

# Modülleri import et
from src.data_collector import collect_job_data
from src.cv_processor import CVProcessor
from src.embedding_service import EmbeddingService
from src.vector_store import VectorStore
from src.filter import filter_junior_suitable_jobs

# --- YENİ KONFİGÜRASYON SABİTLERİ (JobSpy Optimize) ---
MIN_SIMILARITY_THRESHOLD = 60  # Benzerlik eşiği (%) - JobSpy ile daha kaliteli veri
HEDEFLENEN_SITELER = ["linkedin", "indeed"]  # Hangi sitelerde arama yapılacak
DEFAULT_HOURS_OLD = 72  # Varsayılan olarak son 3 günlük ilanlar (JobSpy native)
DEFAULT_RESULTS_PER_PERSONA_SITE = 25  # Her persona ve site için kaç sonuç çekilecek

def collect_data_for_all_personas():
    """
    JobSpy Gelişmiş Özellikler ile Tüm Personalar için Optimize Edilmiş Veri Toplama
    Indeed'in gelişmiş arama operatörlerini ve JobSpy'ın 'hours_old' parametresini kullanır.
    """
    print("\n🔍 JobSpy Gelişmiş Özellikler ile Stratejik Veri Toplama Başlatılıyor...")
    print("=" * 70)

    # Persona bazlı, Indeed'e göre optimize edilmiş ve negatif filtreli arama terimleri
    persona_search_config = {
        "Software_Engineer": {
            "term": "(\"Software Engineer\" OR \"Yazılım Mühendisi\") -Senior -Lead -Principal -Manager -Direktör",
            "hours_old": DEFAULT_HOURS_OLD, "results": DEFAULT_RESULTS_PER_PERSONA_SITE
        },
        "Full_Stack": {
            "term": "(\"Full Stack Developer\" OR \"Full Stack Engineer\") -Senior -Lead -Principal -Manager",
            "hours_old": DEFAULT_HOURS_OLD, "results": DEFAULT_RESULTS_PER_PERSONA_SITE
        },
        "Frontend_Developer": {
            "term": "(\"Frontend Developer\" OR \"Front End Developer\" OR React OR Vue OR Angular) -Senior -Lead",
            "hours_old": DEFAULT_HOURS_OLD, "results": DEFAULT_RESULTS_PER_PERSONA_SITE
        },
        "Backend_Developer": {
            "term": "(\"Backend Developer\" OR \"Back End Developer\" OR Python OR Java OR Node) -Senior -Lead",
            "hours_old": DEFAULT_HOURS_OLD, "results": DEFAULT_RESULTS_PER_PERSONA_SITE
        },
        "Junior_Developer": {
            "term": "\"Junior Developer\" OR \"Junior Software\" OR \"Graduate Developer\" -Senior -Lead",
            "hours_old": DEFAULT_HOURS_OLD, "results": 30  # Junior için daha fazla sonuç
        },
        "Entry_Level_Developer": {
            "term": "\"Entry Level\" OR \"Entry-Level\" OR \"Stajyer\" OR \"Trainee\" -Senior -Manager",
            "hours_old": DEFAULT_HOURS_OLD, "results": 30
        },
        "Business_Analyst": {
            "term": "(\"Business Analyst\" OR \"İş Analisti\") (ERP OR SAP OR Process OR Süreç) -Senior -Lead -Manager",
            "hours_old": DEFAULT_HOURS_OLD, "results": DEFAULT_RESULTS_PER_PERSONA_SITE
        },
        "Data_Analyst": {
            "term": "(\"Data Analyst\" OR \"Veri Analisti\") (SQL OR Python OR PowerBI OR Tableau) -Senior -Lead",
            "hours_old": DEFAULT_HOURS_OLD, "results": DEFAULT_RESULTS_PER_PERSONA_SITE
        },
        "ERP_Consultant": {
            "term": "(\"ERP Consultant\" OR \"ERP Danışmanı\" OR \"SAP Consultant\" OR \"Microsoft Dynamics\") -Senior -Lead -Manager",
            "hours_old": DEFAULT_HOURS_OLD, "results": DEFAULT_RESULTS_PER_PERSONA_SITE
        },
        "Process_Analyst": {
            "term": "(\"Process Analyst\" OR \"Süreç Analisti\" OR \"Business Process\" OR \"İş Süreçleri\") -Senior -Lead",
            "hours_old": DEFAULT_HOURS_OLD, "results": DEFAULT_RESULTS_PER_PERSONA_SITE
        },
        "IT_Analyst": {
            "term": "(\"IT Analyst\" OR \"BT Analisti\" OR \"System Analyst\" OR \"Sistem Analisti\") -Senior -Lead",
            "hours_old": DEFAULT_HOURS_OLD, "results": DEFAULT_RESULTS_PER_PERSONA_SITE
        },
        "Junior_General_Tech": {
            "term": "Junior (Developer OR Analyst OR Engineer OR Specialist OR Uzman OR Danışman) -Senior -Lead",
            "hours_old": 48, "results": 40  # Son 2 gün, daha fazla sonuç
        }
    }

    all_collected_jobs_list = []

    for persona_name, config in persona_search_config.items():
        print(f"\n--- Persona '{persona_name}' için JobSpy Gelişmiş Arama ---")
        print(f"🎯 Optimize edilmiş terim: '{config['term']}'")
        print(f"⏰ Tarih filtresi: Son {config['hours_old']} saat")

        try:
            # JobSpy'ın gelişmiş özelliklerini kullanarak veri toplama
            jobs_df_for_persona = collect_job_data(
                search_term=config["term"],
                site_names=HEDEFLENEN_SITELER,  # LinkedIn + Indeed
                location="Turkey",
                max_results_per_site=config["results"],
                hours_old=config["hours_old"]
            )

            if jobs_df_for_persona is not None and not jobs_df_for_persona.empty:
                # Persona bilgisini ve arama terimini ekle (analiz için faydalı)
                jobs_df_for_persona['persona_source'] = persona_name
                jobs_df_for_persona['search_term_used'] = config["term"]
                all_collected_jobs_list.append(jobs_df_for_persona)
                print(f"✨ Persona '{persona_name}' için {len(jobs_df_for_persona)} ilan bulundu.")
            else:
                print(f"ℹ️ Persona '{persona_name}' için hiçbir siteden ilan bulunamadı.")

        except Exception as e:
            print(f"❌ Persona '{persona_name}' için hata: {str(e)}")
            continue

    if not all_collected_jobs_list:
        print("❌ Hiçbir persona ve site kombinasyonundan ilan bulunamadı.")
        return None

    # Tüm personaların sonuçlarını birleştir
    final_df = pd.concat(all_collected_jobs_list, ignore_index=True)
    print(f"\n📊 Birleştirme öncesi (tüm personalar): {len(final_df)} ilan")

    # Son genel deduplication (persona'lar arası tekrarlar için)
    if 'description' in final_df.columns and not final_df.empty:
         final_df['description_short'] = final_df['description'].astype(str).str[:100]
         final_df.drop_duplicates(subset=['title', 'company', 'location', 'description_short'], inplace=True, keep='first')
         final_df.drop(columns=['description_short'], inplace=True)
    elif not final_df.empty:
         final_df.drop_duplicates(subset=['title', 'company', 'location'], inplace=True, keep='first')

    print(f"✨✨✨ TOPLAM: {len(final_df)} adet BENZERSİZ ilan (JobSpy optimize edilmiş)! ✨✨✨")    # Optimize edilmiş CSV kaydetme
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_csv_path = os.path.join(output_dir, f"jobspy_optimize_ilanlar_{timestamp}.csv")
    final_df.to_csv(final_csv_path, index=False, encoding='utf-8')
    print(f"📁 JobSpy optimize edilmiş veriler: {final_csv_path}")

    return final_csv_path

def analyze_and_find_best_jobs():
    """Tam otomatik analiz: Stratejik veri toplama + AI analizi + Sonuçlar"""
    print("\n🚀 Tam Otomatik AI Kariyer Analizi Başlatılıyor...")
    print("=" * 60)

    # 1. Veri toplama
    print("\n🔄 1/6: JobSpy Gelişmiş Özellikler ile veri toplama...")
    csv_path = collect_data_for_all_personas()
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
            job_embeddings.append(None)    # Vector store'a ekle
    success = vector_store.add_jobs(jobs_df, job_embeddings)
    if not success:
        print("❌ Vector store yükleme başarısız!")
        return    # 5. Benzer işleri bul ve filtrele
    print("\n🔄 6/6: Akıllı eşleştirme ve filtreleme...")
    similar_jobs = vector_store.search_similar_jobs(cv_embedding, top_k=50)
    
    if similar_jobs:
        print("🔍 Sonuçlar YBS/junior pozisyonlar için akıllı filtreleme...")
        filtered_jobs = filter_junior_suitable_jobs(similar_jobs, debug=False)

        if filtered_jobs:
            # Uygunluk puanı eşiği ekleme
            high_quality_jobs = [job for job in filtered_jobs if job['similarity_score'] >= MIN_SIMILARITY_THRESHOLD]

            if high_quality_jobs:
                print(f"✅ {len(high_quality_jobs)} adet yüksek kaliteli pozisyon bulundu!")
                print(f"📊 Uygunluk eşiği: %{MIN_SIMILARITY_THRESHOLD} ve üzeri")

                print("\n" + "="*70)
                print("🎉 SİZE ÖZEL EN UYGUN İŞ İLANLARI (JobSpy Optimize)")
                print("🎯 YBS + Full-Stack + Veri Analizi Odaklı")
                print("="*70)

                for i, job in enumerate(high_quality_jobs[:15], 1):  # Top 15 göster
                    print(f"\n{i}. {job['title']} - {job['company']}")
                    print(f"   📍 {job['location']}")
                    print(f"   📊 Uygunluk: %{job['similarity_score']:.1f}")
                    print(f"   💼 Site: {job.get('source_site', 'N/A')}")  # Hangi siteden geldiği
                    print(f"   👤 Persona: {job.get('persona_source', job.get('persona', 'N/A'))}")  # Hangi persona aramasıyla geldiği
                    print(f"   🔗 {job['url']}")
                    print("-" * 50)

                print(f"\n🎯 Analiz tamamlandı! {len(high_quality_jobs)} yüksek kaliteli pozisyon listelendi.")

                # Persona dağılımı analizi
                if high_quality_jobs and ('persona_source' in high_quality_jobs[0] or 'persona' in high_quality_jobs[0]):
                    persona_counts = {}
                    for job in high_quality_jobs:
                        persona = job.get('persona_source', job.get('persona', 'Unknown'))
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
    """JobSpy Gelişmiş Özellikler için Manuel Doğrulama Protokolü"""
    print("\n" + "="*80)
    print("📋 JOBSPY GELİŞMİŞ ÖZELLİKLER - MANUEL DOĞRULAMA PROTOKOLÜ")
    print("="*80)
    print("🎯 SİSTEM DURUMU: JobSpy Native (hours_old=72, cosine similarity)")
    print("🚀 Optimize Özellikler: Çoklu site, gelişmiş operatörler, 12 persona")
    print("📊 Beklenen Performans: 100-300 benzersiz ilan, %80+ uygunluk oranı")
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
    print("🎯 12 farklı JobSpy optimize edilmiş persona ile veri toplama başlatılıyor...\n")

    # Tam otomatik analiz çalıştır
    analyze_and_find_best_jobs()


# Test fonksiyonları için
if __name__ == "__main__":
    main()
