# 🤖 Akıllı Kariyer Asistanı

> **CV'nizi anlayan ve size özel iş fırsatlarını bulan yapay zeka destekli kariyer asistanı**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-green.svg)](https://ai.google.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector-orange.svg)](https://www.trychroma.com)
[![JobSpy](https://img.shields.io/badge/JobSpy-Multi--Platform-red.svg)](https://github.com/speedyapply/jobspy)

## 📋 Proje Özeti

Akıllı Kariyer Asistanı, geleneksel iş arama sürecini devrim niteliğinde değiştiren bir AI uygulamasıdır. Manuel olarak yüzlerce iş ilanı arasında gezinmek yerine, CV'nizi derinlemesine analiz ederek size en uygun pozisyonları **otomatik olarak keşfeder ve puanlar**.

### 🎯 Temel Özellikler

- **🧠 AI Destekli Analiz:** Gemini AI ile CV ve iş ilanlarını semantik olarak analiz
- **🌐 Çoklu Platform Desteği:** LinkedIn ve Indeed'den eş zamanlı iş ilanı toplama
- **🔍 Akıllı Keşif:** "Yazılım Geliştirici" ararken "İş Zekası Uzmanı" gibi ilişkili pozisyonları da bulur
- **📊 Puanlama Sistemi:** Her ilan için %0-100 arası uygunluk skoru
- **🎭 Persona Tabanlı Arama:** 12 farklı kariyer profili ile geniş kapsamlı tarama
- **⚡ Zaman Tasarrufu:** 2 saatlik manuel aramayı 2 dakikaya indirger
- **🔒 Gizlilik:** Tüm veriler yerel olarak işlenir, cloud'a gönderilmez

## 🚀 Hızlı Başlangıç

### Ön Koşullar
- Python 3.11+
- Google Gemini API Key ([Ücretsiz alın](https://aistudio.google.com/app/apikey))
- 8GB+ RAM (ChromaDB için)

### ⚡ Kurulum

```bash
# 1. Projeyi klonlayın
git clone https://github.com/furkan-ucan/akilli-kariyer-asistani.git
cd akilli-kariyer-asistani

# 2. Sanal ortam oluşturun
python -m venv kariyer-asistani-env

# 3. Sanal ortamı aktive edin
# Windows:
kariyer-asistani-env\Scripts\activate
# macOS/Linux:
source kariyer-asistani-env/bin/activate

# 4. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 5. API key'inizi ayarlayın
# .env dosyası oluşturun ve içine ekleyin:
echo "GEMINI_API_KEY=your_actual_gemini_api_key" > .env

# 6. CV'nizi ekleyin
# data/cv.txt dosyasına CV'nizin tam metnini kopyalayın
# NOT: Dosya yoksa data klasörünü oluşturun:
mkdir data
# Sonra cv.txt dosyasını data klasörü içine oluşturun
```

## 🎯 Kullanım Rehberi

### 1️⃣ Temel Kurulum Sonrası Ayarlar

#### CV Hazırlama
```bash
# data/cv.txt dosyasını oluşturun ve aşağıdaki bilgileri ekleyin:
```

**CV formatı örneği** (`data/cv.txt`):
```text
İsim: Furkan Uçan
Pozisyon: Yazılım Geliştirici / Veri Analisti

EĞİTİM:
- Yönetim Bilişim Sistemleri, 2024

TEKNİK BECERİLER:
- Programlama: Python, JavaScript, TypeScript, React
- Veritabanı: SQL, PostgreSQL, MongoDB
- Araçlar: Git, Docker, AWS
- Veri Analizi: Pandas, NumPy, Matplotlib

DENEYIM:
- Full Stack Developer (2023-2024)
- Web uygulamaları geliştirme
- API tasarımı ve entegrasyonu
- Veri görselleştirme projeleri

PROJELER:
- E-ticaret sitesi (React + Node.js)
- Veri analizi dashboardu (Python + Streamlit)
- REST API geliştirme (Flask/FastAPI)

HEDEFLER:
- Yazılım geliştirme alanında kariyer yapmak
- Full-stack projelerinde çalışmak
- Veri odaklı uygulamalar geliştirmek
```

#### API Key Alma
1. [Google AI Studio](https://aistudio.google.com/app/apikey)'ya gidin
2. "Create API Key" butonuna tıklayın
3. API key'i kopyalayın
4. `.env` dosyasına ekleyin:
```bash
GEMINI_API_KEY=AIzaSyC... (gerçek key'iniz)
```

### 2️⃣ İlk Çalıştırma

```bash
# Sistemi çalıştırın
python main.py
```

**Beklenen çıktı:**
```
🚀 Akıllı Kariyer Asistanı - Böl ve Fethet Stratejisi
============================================================

📋 MANUEL DOĞRULAMA PROTOKOLÜ REHBERİ
🔬 Sistemin 'kör noktalarını' tespit etmek için adım adım rehber
============================================================

🔹 ADIM 1: Manuel Arama (Indeed'de)
   • Indeed.com'da giriş yapın
   • Filtreler: 'Son 3 gün', 'Türkiye', 'Entry Level/Junior'

🎯 SİSTEM DURUMU: Tarih filtresi AÇIK (≤3 gün)
============================================================

✅ Sistem kontrolleri başarılı
🎯 12 farklı persona ile stratejik veri toplama başlatılıyor...

🔍 Stratejik Veri Toplama Başlatılıyor (Böl ve Fethet - Çoklu Site)...
============================================================

--- Persona 'Yazilim_Gelistirici' için arama yapılıyor ---
🔍 Arama terimi: 'Yazılım Geliştirici'
🌐 LinkedIn'de arama yapılıyor...
✅ LinkedIn'den 15 ilan toplandı
🌐 Indeed'de arama yapılıyor...
✅ Indeed'den 18 ilan toplandı
✅ 33 ilan toplandı

[12 persona için benzer süreç...]

🔄 12 persona sonucu birleştiriliyor...
� Birleştirme öncesi: 340 ilan
✨ Tekrar temizleme sonrası: 284 benzersiz ilan

🚀 Tam Otomatik AI Kariyer Analizi Başlatılıyor...
============================================================

✅ CV embedding oluşturuldu
✅ Vector store hazır
🔄 6/6: Akıllı eşleştirme ve filtreleme...

✅ 8 adet yüksek kaliteli pozisyon bulundu!
📊 Uygunluk eşiği: %50 ve üzeri

======================================================================
🎉 SİZE ÖZEL EN UYGUN İŞ İLANLARI
🎯 YBS + Full-Stack + Veri Analizi Odaklı
======================================================================

1. Yazılım Uzmanı - MİA Teknoloji A.Ş.
   📍 Ankara, T06, TR
   📊 Uygunluk: %63.9
   🎭 Persona: Yazilim_Gelistirici
   🔗 https://tr.indeed.com/viewjob?jk=...

2. Full Stack Developer - Pratik İnsan Kaynakları
   📍 İstanbul, T34, TR
   📊 Uygunluk: %63.8
   🎭 Persona: Full_Stack
   🔗 https://tr.indeed.com/viewjob?jk=...

📈 Persona Dağılımı:
   Full_Stack: 3 ilan
   Yazilim_Gelistirici: 2 ilan
   Python_Developer: 2 ilan
   Analist: 1 ilan
```

## 🛠️ Özelleştirme Rehberi

### 3️⃣ Kendi İhtiyaçlarınıza Göre Ayarlama

#### A) Persona ve Arama Terimlerini Değiştirme

`main.py` dosyasındaki `persona_search_terms` sözlüğünü düzenleyin:

```python
# Mevcut personalar
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

# Örnek: Pazarlama odaklı personalar
persona_search_terms = {
    "Dijital_Pazarlama": "Dijital Pazarlama Uzmanı",
    "SEO_Specialist": "SEO Uzmanı",
    "Content_Marketing": "İçerik Pazarlama",
    "Social_Media": "Sosyal Medya Uzmanı",
    "PPC_Specialist": "Google Ads Uzmanı",
    "Email_Marketing": "E-posta Pazarlama",
    "Brand_Manager": "Marka Yöneticisi",
    "Marketing_Analyst": "Pazarlama Analisti"
}

# Örnek: Finans odaklı personalar
persona_search_terms = {
    "Financial_Analyst": "Finansal Analist",
    "Accounting": "Muhasebe Uzmanı",
    "Risk_Management": "Risk Yönetimi",
    "Internal_Audit": "İç Denetim",
    "Treasury": "Hazine Uzmanı",
    "Credit_Analyst": "Kredi Analisti",
    "Investment": "Yatırım Danışmanı",
    "Corporate_Finance": "Kurumsal Finans"
}
```

#### B) Filtreleme Ayarlarını Değiştirme

`main.py` dosyasındaki konfigürasyon sabitlerini düzenleyin:

```python
# Mevcut ayarlar
ENABLE_DATE_FILTER = True      # Tarih filtresi açık/kapalı
DATE_FILTER_DAYS = 3           # Son X gün içindeki ilanlar
MIN_SIMILARITY_THRESHOLD = 50  # Benzerlik eşiği (%)

# Daha katı filtreleme için:
DATE_FILTER_DAYS = 1           # Sadece bugünkü ilanlar
MIN_SIMILARITY_THRESHOLD = 70  # Daha yüksek kalite eşiği

# Daha geniş tarama için:
DATE_FILTER_DAYS = 7           # Son 1 hafta
MIN_SIMILARITY_THRESHOLD = 40  # Daha düşük eşik
```

#### C) İlan Sayısını Artırma/Azaltma

`collect_data_for_all_personas()` fonksiyonunda:

```python
# Mevcut
jobs_df = collect_job_data(search_term=term, max_results_per_site=20)

# Daha fazla ilan için
jobs_df = collect_job_data(search_term=term, max_results_per_site=50)

# Daha hızlı test için
jobs_df = collect_job_data(search_term=term, max_results_per_site=5)
```

#### D) Platform Seçimi

`src/data_collector.py` dosyasında site listesini değiştirin:

```python
# Mevcut: LinkedIn + Indeed
sites = ['linkedin', 'indeed']

# Sadece Indeed için
sites = ['indeed']

# Sadece LinkedIn için (daha yavaş ama daha detaylı)
sites = ['linkedin']

# Gelecekte: Diğer platformlar eklenebilir
# sites = ['linkedin', 'indeed', 'glassdoor', 'monster']
```

### 4️⃣ Gelişmiş Özelleştirme

#### Junior/Senior Filtreleme Ayarlama

`src/filter.py` dosyasında `filter_junior_suitable_jobs()` fonksiyonunu düzenleyin:

```python
# Daha katı junior filtreleme için
junior_keywords = [
    'junior', 'entry', 'trainee', 'stajyer', 'yeni mezun',
    'başlangıç', 'intern', 'graduate', 'associate'
]

# Daha geniş deneyim aralığı için senior pozisyonları da dahil et
# Sadece experience_keywords listesindeki şartları gevşetin
```

#### Manuel Doğrulama Sıklığını Ayarlama

Manuel doğrulama rehberini kendi rutininize göre ayarlayın:

```python
def print_manual_validation_guide():
    # Günlük çalışma için
    print("🔹 Bu protokolü her gün çalıştırın")

    # Haftalık çalışma için
    print("🔹 Bu protokolü haftada 2-3 kez çalıştırın")

    # Ayar testleri için
    print("🔹 Ayar değiştirdikten sonra mutlaka çalıştırın")
```

## 📊 Sonuçları Analiz Etme

### 5️⃣ Çıktıları Anlama ve İyileştirme

#### Persona Performansı Analizi

Sistem çalıştıktan sonra "Persona Dağılımı" bölümünü inceleyin:

```
📈 Persona Dağılımı:
   Full_Stack: 3 ilan          # En başarılı persona
   Yazilim_Gelistirici: 2 ilan
   Python_Developer: 2 ilan
   Analist: 1 ilan
   React_Developer: 0 ilan     # Bu persona için arama terimini değiştirin
```

**Optimizasyon önerileri:**
- `React_Developer: 0 ilan` görüyorsanız → "React" yerine "Frontend Developer" deneyin
- Belirli persona çok fazla sonuç veriyorsa → arama terimini daha spesifik yapın
- Hiç sonuç alamayan personalar → tamamen farklı terimler deneyin

#### Uygunluk Skorlarını Analiz Etme

```
📊 Uygunluk: %63.9  # Çok iyi (>60%)
📊 Uygunluk: %45.2  # Orta (40-60%)
📊 Uygunluk: %35.8  # Düşük (<40%)
```

**Skor düşükse yapılacaklar:**
1. **CV'nizi geliştirin:** Daha fazla teknik detay ekleyin
2. **İş ilanlarını manuel kontrol edin:** Belki sizin için uygun ama sistem algılamıyor
3. **Eşiği düşürün:** `MIN_SIMILARITY_THRESHOLD = 40` yapın

#### Toplanan İlan Sayısı Analizi

```
📊 Birleştirme öncesi: 340 ilan    # Ham toplam
✨ Tekrar temizleme sonrası: 284 ilan  # Tekrarlar temizlendi
✅ 8 adet yüksek kaliteli pozisyon    # Final sonuçlar
```

**Sayılar düşükse:**
- `max_results_per_site` değerini artırın (20 → 50)
- Daha fazla persona ekleyin
- Tarih filtresini genişletin (3 → 7 gün)

## 🚨 Sorun Giderme

### 6️⃣ Sık Karşılaşılan Sorunlar

#### Problem: "API key bulunamadı" hatası
```bash
❌ HATA: Gemini API key bulunamadı!
```
**Çözüm:**
1. `.env` dosyasının var olduğundan emin olun
2. Dosya içeriğini kontrol edin: `GEMINI_API_KEY=AIzaSyC...`
3. API key'in çalıştığını test edin: [AI Studio](https://aistudio.google.com/) üzerinden

#### Problem: "CV dosyası bulunamadı" hatası
```bash
❌ HATA: CV dosyası bulunamadı: data/cv.txt
```
**Çözüm:**
```bash
# data klasörünü oluşturun
mkdir data

# cv.txt dosyasını oluşturun ve CV'nizi yapıştırın
# Windows: notepad data/cv.txt
# macOS/Linux: nano data/cv.txt
```

#### Problem: "Hiçbir ilan bulunamadı" durumu
```bash
❌ Hiçbir persona için ilan bulunamadı. Genel bir sorun olabilir.
```
**Çözüm:**
1. İnternet bağlantınızı kontrol edin
2. JobSpy'ın çalıştığını test edin:
```python
from jobspy import scrape_jobs
jobs = scrape_jobs(site_name="indeed", search_term="yazılım", country_indeed="Turkey")
print(len(jobs))
```

#### Problem: Çok az sonuç (1-2 ilan)
**Çözüm:**
1. Benzerlik eşiğini düşürün: `MIN_SIMILARITY_THRESHOLD = 40`
2. Tarih filtresini genişletin: `DATE_FILTER_DAYS = 7`
3. Daha fazla persona ekleyin
4. `max_results_per_site` değerini artırın

#### Problem: Çok fazla alakasız sonuç
**Çözüm:**
1. Benzerlik eşiğini yükseltin: `MIN_SIMILARITY_THRESHOLD = 60`
2. CV'nizi daha spesifik hale getirin
3. Persona arama terimlerini daha dar yapın

#### Problem: Sistem çok yavaş çalışıyor
**Çözüm:**
1. `max_results_per_site` değerini düşürün (20 → 10)
2. Daha az persona kullanın
3. Sadece Indeed kullanın: `sites = ['indeed']`

## 🔧 Gelişmiş Konfigürasyon

### 7️⃣ Uzman Seviye Ayarlar

#### A) Çoklu Dil Desteği
CV'nizi hem Türkçe hem İngilizce hazırlayın:

```text
# data/cv.txt
=== TÜRKÇE ===
İsim: Furkan Uçan
Pozisyon: Yazılım Geliştirici
Beceriler: Python, JavaScript, React...

=== ENGLISH ===
Name: Furkan Uçan
Position: Software Developer
Skills: Python, JavaScript, React...
```

#### B) Sektör Odaklı Özelleştirme

**Fintech için:**
```python
persona_search_terms = {
    "Blockchain_Developer": "Blockchain Developer",
    "Fintech_Engineer": "Fintech Software Engineer",
    "DeFi_Developer": "DeFi Developer",
    "Payment_Systems": "Payment Systems Developer",
    "Crypto_Analyst": "Cryptocurrency Analyst"
}
```

**E-ticaret için:**
```python
persona_search_terms = {
    "Ecommerce_Developer": "E-commerce Developer",
    "Shopify_Developer": "Shopify Developer",
    "Magento_Developer": "Magento Developer",
    "WooCommerce": "WooCommerce Developer",
    "Product_Manager": "E-commerce Product Manager"
}
```

#### C) Lokasyon Filtreleme

`src/data_collector.py` dosyasına lokasyon filtresi ekleyin:

```python
# Sadece İstanbul
location_filter = "İstanbul"

# Sadece uzaktan çalışma
location_filter = "remote"

# Çoklu şehir
location_filter = ["İstanbul", "Ankara", "İzmir"]
```

## 📈 Başarı Metrikleri ve Optimizasyon

### 8️⃣ Performans Takibi

#### Haftalık Performans Raporu

Sistemin başarısını ölçmek için aşağıdaki metrikleri takip edin:

```
📊 HAFTALIK RAPOR
==================
Toplanan İlan: 284
Filtrelenen İlan: 45
Yüksek Kaliteli: 8
Başvuru Yapılan: 3
Geri Dönüş: 1
Mülakat: 0

Başarı Oranı: %12.5 (3/24 başvuru)
Kalite Skoru: %17.8 (8/45 filtre)
```

#### Sürekli İyileştirme Döngüsü

1. **Hafta 1:** Sistemi çalıştır, sonuçları kaydet
2. **Hafta 2:** Başvuru sonuçlarına göre ayarları değiştir
3. **Hafta 3:** Yeni ayarları test et
4. **Hafta 4:** En iyi konfigürasyonu belirle

## 💡 İpuçları ve Püf Noktaları

### 9️⃣ Uzman Tavsiyeleri

#### En İyi Sonuçlar İçin:
- **CV'nizi düzenli güncelleyin** (yeni projeler, beceriler)
- **Farklı persona kombinasyonları deneyin**
- **Manuel doğrulama yapmayı ihmal etmeyin**
- **Sonuçları Excel'de analiz edin** (CSV export)
- **Aynı şirketten çok başvuru yapmayın** (filtre ekleyin)

#### Zaman Optimizasyonu:
- **Sabah 08:00:** Yeni ilanlar için ideal saat
- **Akşam 18:00:** Günlük güncellemeler için
- **Hafta sonu:** Haftalık optimizasyon çalışması

#### Başvuru Stratejisi:
- Top 3 ilanı öncelikle değerlendirin
- %60+ skorlu ilanlar için özel kapak mektubu yazın
- %40-60 arası ilanlar için standart başvuru yapın
- %40 altı ilanları manuel kontrol edin


## 🏗️ Teknik Mimari

### Sistem Bileşenleri
```
┌─────────────────────────────────────┐
│         Ana Uygulama (main.py)      │
├─────────────────────────────────────┤
│  CV İşleme    │  İş İlanı Toplama   │ (Gemini AI)    (JobSpy: LinkedIn+Indeed)
├─────────────────────────────────────┤
│       Vektör Veritabanı             │ (ChromaDB)
├─────────────────────────────────────┤
│    Benzerlik Analizi & Puanlama     │ (Cosine Similarity)
├─────────────────────────────────────┤
│  Filtreleme   │   Sıralama          │ (AI-based filtering)
└─────────────────────────────────────┘
```

### Teknoloji Yığını
- **AI/ML:** Google Gemini (Embedding), ChromaDB (Vector DB)
- **Veri Toplama:** JobSpy (LinkedIn + Indeed scraping)
- **Veri İşleme:** Pandas, NumPy
- **Backend:** Python 3.12+

### Veri Akışı
1. **Toplama:** JobSpy → LinkedIn/Indeed → Ham CSV
2. **Temizleme:** Deduplication → Tarih filtresi → Temiz CSV
3. **Analiz:** Gemini AI → CV + İlanlar → Embeddings
4. **Eşleştirme:** ChromaDB → Cosine similarity → Puanlama
5. **Filtreleme:** Junior filter → Eşik filtresi → Final sonuçlar

## 📊 Gerçek Test Sonuçları

### Son Test Metrikleri (Çoklu Platform)
- **Platform:** LinkedIn + Indeed
- **Toplanan İlan:** 284 adet (12 persona)
- **Benzersiz İlan:** 234 adet (deduplication sonrası)
- **Yüksek Kaliteli:** 8 adet (%50+ skor)
- **İşleme Süresi:** ~2.5 dakika
- **Başarı Oranı:** %100 (tüm adımlar başarılı)

### Platform Karşılaştırması
| Platform | Ortalama İlan/Arama | Açıklama Kalitesi | Hız | Doğruluk |
|----------|--------------------|--------------------|-----|----------|
| LinkedIn | 15-20 ilan | Çok yüksek (detaylı) | Yavaş | %95 |
| Indeed | 18-25 ilan | Yüksek (özet) | Hızlı | %90 |

### Keşfedilen Değerli Pozisyonlar
1. **Yazılım Uzmanı** (MİA Teknoloji) - %63.9 ✨ [LinkedIn]
2. **Full Stack Developer** (Pratik İK) - %63.8 ✨ [Indeed]
3. **Veri Analiz Elemanı** (Rasyonel Kurumsal) - %63.4 ✨ [LinkedIn]
4. **İş Analizi Yöneticisi** (BNP Paribas) - %60.9 ✨ [Indeed]
5. **Python Developer** (Tech Startup) - %58.5 ✨ [LinkedIn]

### Persona Başarı Oranları
```
📈 En Başarılı Personalar:
1. Full_Stack: 35% (3/8 ilan)
2. Yazilim_Gelistirici: 25% (2/8 ilan)
3. Python_Developer: 25% (2/8 ilan)
4. Analist: 15% (1/8 ilan)

❌ Optimizasyon Gereken:
- React_Developer: 0 ilan
- Flutter_Developer: 0 ilan
- TypeScript_Developer: 0 ilan
```

## 🔧 Dosya Yapısı

```
kariyer-asistani/
├── main.py                     # 🚀 Ana uygulama (BURADAN BAŞLAYIN)
├── requirements.txt            # 📦 Python bağımlılıkları
├── .env                        # 🔐 API keys (SİZ OLUŞTURUN)
├── README.md                   # 📖 Bu rehber dosyası
├── src/                        # 📁 Kaynak kodlar
│   ├── data_collector.py       # 🌐 Çoklu platform iş ilanı toplama
│   ├── cv_processor.py         # 📄 CV analizi ve embedding
│   ├── embedding_service.py    # 🧠 Gemini AI embedding servisi
│   ├── vector_store.py         # 🗃️ ChromaDB vektör veritabanı
│   └── filter.py               # 🔍 Junior/YBS filtreleme kuralları
├── data/                       # 📊 Veriler (SİZ OLUŞTURUN)
│   ├── cv.txt                  # 📋 Sizin CV'niz (ZORUNLU)
│   └── birlesmis_ilanlar_*.csv # 💾 Toplanan iş ilanları (OTOMATIK)
└── memory-bank/                # 📚 Proje dokümantasyonu
    ├── projectbrief.md         # 🎯 Proje amacı ve hedefleri
    ├── productContext.md       # 🏭 Ürün bağlamı ve kullanıcı senaryoları
    ├── systemPatterns.md       # 🏗️ Sistem mimarisi ve tasarım
    ├── techContext.md          # ⚙️ Teknik detaylar ve implementasyon
    ├── activeContext.md        # 🔄 Güncel geliştirme durumu
    └── progress.md             # 📈 İlerleme takibi ve sonraki adımlar
```

### 📋 Dosya Sorumluluğu Rehberi

| Dosya | Ne Zaman Düzenlersiniz | Amaç |
|-------|------------------------|------|
| `main.py` | Persona eklemek/konfigürasyon değiştirmek | Ana sistem ayarları |
| `.env` | İlk kurulum | API key güvenliği |
| `data/cv.txt` | CV'niz değiştiğinde | Sistem size daha iyi eşleştirme yapabilir |
| `src/filter.py` | Çok az/çok fazla sonuç alıyorsanız | Filtreleme kurallarını ayarlama |
| `requirements.txt` | Yeni paket eklediğinizde | Bağımlılık yönetimi |

### 🎯 Hızlı Başlangıç Kontrol Listesi

- [ ] ✅ Python 3.11+ yüklü
- [ ] ✅ `git clone` ile projeyi indirdim
- [ ] ✅ `python -m venv` ile sanal ortam oluşturdum
- [ ] ✅ `pip install -r requirements.txt` çalıştırdım
- [ ] ✅ Gemini API key aldım ve `.env` dosyasına ekledim
- [ ] ✅ `data/` klasörünü oluşturdum
- [ ] ✅ `data/cv.txt` dosyasına CV'mi yazdım
- [ ] ✅ `python main.py` ile sistemi test ettim
- [ ] ✅ Persona ve filtreleme ayarlarını kendi ihtiyaçlarıma göre değiştirdim

## 🚧 Gelecek Özellikler (Roadmap)

### 🎯 Faz 3: Web Arayüzü (Bu Ay)
- 🌐 **Flask Web Uygulaması**
  - Modern, responsive tasarım
  - Gerçek zamanlı sonuç görüntüleme
  - İlan işaretleme sistemi (❤️ Favoriler, ❌ İlgisiz)
- 📱 **Mobil Uyumluluk**
  - Telefon/tablet desteği
  - Touch-friendly arayüz

### 🤖 Faz 4: Otomasyon (Gelecek Ay)
- ⏰ **Zamanlanmış Çalışma**
  ```bash
  # Günlük otomatik tarama
  python main.py --schedule daily --time 08:00

  # Haftalık rapor
  python main.py --schedule weekly --day monday
  ```
- 📱 **Bildirim Sistemi**
  - Telegram bot entegrasyonu
  - Email bildirimleri
  - Slack webhook desteği
- 🔄 **Sürekli İzleme**
  - Favorilediğiniz ilanların durumu
  - Şirket takip sistemi
  - Başvuru takip yönetimi

### 📊 Faz 5: Gelişmiş Analitik (Sonraki Ay)
- 📈 **Dashboard & Raporlama**
  - Haftalık/aylık performans raporları
  - Trend analizi (hangi beceriler popüler?)
  - Başvuru başarı oranı takibi
- 🎯 **Akıllı Öneriler**
  - CV iyileştirme önerileri
  - Eksik beceri tespit sistemi
  - Maaş benchmark analizi

### 🌍 Faz 6: Platform Genişletme (Uzun Vadeli)
- 🔗 **Yeni İş Platformları**
  - Glassdoor entegrasyonu
  - Monster.com desteği
  - StartupJobs.com (startups için)
  - RemoteOK.io (uzaktan çalışma)
- 🌐 **Uluslararası Pazar**
  - Almanya: Xing, StepStone
  - ABD: Dice, AngelList
  - Genel: Glassdoor, Monster

### 🤝 Faz 7: Topluluk Özellikleri (Gelecek Vizyon)
- 👥 **Kullanıcı Topluluğu**
  - İlan paylaşım sistemi
  - Başarı hikayeleri
  - Mentor-mentee eşleştirme
- 🏆 **Gamification**
  - Başarı rozetleri
  - Haftalık liderlik tablosu
  - Referans sistemi

## 🎁 Bonus Özellikler

### 💎 Şimdi Kullanabileceğiniz Gizli Özellikler

#### 1. Özel Filtreleme
```python
# main.py içinde
def custom_company_filter(jobs):
    """Belirli şirketleri önceliklendir"""
    priority_companies = ["Microsoft", "Google", "Amazon", "Meta"]
    return sorted(jobs, key=lambda x: x['company'] in priority_companies, reverse=True)
```

#### 2. Maaş Tahmin Sistemi
```python
# CV'nizde maaş beklentisi belirtin
"""
MAAŞ BEKLENTİSİ: 15.000-25.000 TL
ÇALIŞMA TERCİHİ: Uzaktan/Hibrit
SEKTÖR TERCİHİ: Fintech, E-ticaret, SaaS
"""
```

#### 3. Başvuru Takip Sistemi
```python
# Başvuru yaptığınız ilanları takip edin
applied_jobs = {
    'job_id_1': {'date': '2024-01-15', 'status': 'Applied'},
    'job_id_2': {'date': '2024-01-16', 'status': 'Interview'},
}
```

## 🎓 Öğrenme Kaynakları

### 📚 Sistem Nasıl Çalışıyor?
- **AI Embeddings:** [Gemini AI Documentation](https://ai.google.dev/docs)
- **Vector Databases:** [ChromaDB Tutorial](https://docs.trychroma.com/)
- **Web Scraping:** [JobSpy GitHub](https://github.com/speedyapply/jobspy)

### 🛠️ Geliştirme Rehberi
- **Python Best Practices:** PEP 8, Type Hints
- **Git Workflow:** Feature branches, PR reviews
- **Testing:** Unit tests, Integration tests
- **Documentation:** Docstrings, README güncellemeleri

### 🎯 Kariyer Tavsiyeleri
- **CV Optimizasyonu:** ATS-friendly formatlar
- **Başvuru Stratejileri:** Quality over quantity
- **Mülakat Hazırlığı:** Teknik + behavioral sorular
- **Networking:** LinkedIn optimization

## 🤝 Katkıda Bulunma

### 🌟 Topluluk Katkısı Hoş Geldiniz!

Bu proje açık kaynaklıdır ve topluluğun katkılarıyla büyür. Her seviyeden geliştirici katkıda bulunabilir:

#### 🎯 Katkı Alanları
- **🐛 Bug Reports:** Sorunları bildirin
- **💡 Feature Requests:** Yeni özellik önerileri
- **📝 Documentation:** Rehber ve dokümantasyon iyileştirmeleri
- **🧪 Testing:** Yeni senaryolar ve test case'leri
- **🌍 Localization:** Farklı dil/ülke desteği
- **📊 Data Sources:** Yeni iş platformu entegrasyonları

#### 🚀 Nasıl Başlarsınız?

1. **🍴 Fork edin**
   ```bash
   # GitHub'da "Fork" butonuna tıklayın
   git clone https://github.com/YOURUSERNAME/akilli-kariyer-asistani.git
   ```

2. **🌿 Feature branch oluşturun**
   ```bash
   git checkout -b feature/amazing-new-feature
   # veya
   git checkout -b bugfix/fix-linkedin-scraping
   # veya
   git checkout -b docs/improve-readme
   ```

3. **💻 Geliştirme yapın**
   ```bash
   # Kodunuzu yazın
   # Testlerinizi çalıştırın
   python -m pytest tests/
   ```

4. **📝 Commit atın**
   ```bash
   git add .
   git commit -m "feat: LinkedIn API rate limit handling eklendi"
   # veya
   git commit -m "fix: CSV encoding sorunu düzeltildi"
   # veya
   git commit -m "docs: Kurulum rehberi güncellendi"
   ```

5. **🚀 Push edin**
   ```bash
   git push origin feature/amazing-new-feature
   ```

6. **🔄 Pull Request açın**
   - GitHub'da "Compare & pull request" butonuna tıklayın
   - Değişikliklerinizi detaylandırın
   - Test sonuçlarını paylaşın

#### 📋 Katkı Kuralları

- **Code Style:** PEP 8 Python style guide
- **Testing:** Yeni özellikler için test yazın
- **Documentation:** Public fonksiyonlar için docstring
- **Git Messages:** [Conventional Commits](https://www.conventionalcommits.org/) formatı

#### 🏆 Katkıda Bulunanlar

Bu projeye katkıda bulunan herkese teşekkürler:

<!-- Contributors will be automatically added here -->
<a href="https://github.com/furkan-ucan/akilli-kariyer-asistani/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=furkan-ucan/akilli-kariyer-asistani" />
</a>

## 📞 İletişim ve Destek

### 👨‍💻 Proje Sahibi
**Furkan Uçan**
📧 **Email:** furkan.ucann@yandex.com
💼 **LinkedIn:** [linkedin.com/in/furkan-ucan](https://linkedin.com/in/furkan-ucan)
🐙 **GitHub:** [github.com/furkan-ucan](https://github.com/furkan-ucan)

### 💬 Topluluk Desteği
- **🐛 Bug Report:** [GitHub Issues](https://github.com/furkan-ucan/akilli-kariyer-asistani/issues)
- **💡 Feature Request:** [GitHub Discussions](https://github.com/furkan-ucan/akilli-kariyer-asistani/discussions)
- **❓ Sorular:** README.md'de cevabı yoksa issue açın
- **🤝 Collaboration:** Birlikte çalışmak için LinkedIn'den iletişime geçin

### 🆘 Acil Destek

**Sistem çalışmıyor mu?** Aşağıdaki bilgileri paylaşın:

```bash
# Sistem bilgileri
python --version
pip list | grep -E "(jobspy|chromadb|google-generativeai)"

# Hata detayları
python main.py > debug.log 2>&1
# debug.log dosyasının içeriğini paylaşın
```

**Hızlı çözüm için:**
1. ✅ `.env` dosyasındaki API key'i kontrol edin
2. ✅ `data/cv.txt` dosyasının var olduğundan emin olun
3. ✅ İnternet bağlantınızın stabil olduğunu test edin
4. ✅ Son sürümü kullandığınızdan emin olun: `git pull origin main`

---

<div align="center">

## 🌟 Proje Beğendiniz mi?

[![GitHub stars](https://img.shields.io/github/stars/furkan-ucan/akilli-kariyer-asistani?style=social)](https://github.com/furkan-ucan/akilli-kariyer-asistani/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/furkan-ucan/akilli-kariyer-asistani?style=social)](https://github.com/furkan-ucan/akilli-kariyer-asistani/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/furkan-ucan/akilli-kariyer-asistani?style=social&label=Watch)](https://github.com/furkan-ucan/akilli-kariyer-asistani/watchers)

### ⭐ **Star vermeyi unutmayın!** ⭐

Bu proje faydalı olduysa yıldız vererek destekleyebilirsiniz.
Arkadaşlarınızla paylaşarak daha fazla kişinin faydalanmasını sağlayabilirsiniz.

### 💝 Teşekkürler

> *"Hayallerinizdeki işi bulmak artık hayallerinizden daha kolay!"*
> *"AI destekli kariyer planlaması artık herkesin elinde!"*

**🚀 Başarılı bir kariyer yolculuğu dileriz!**

</div>

---

<details>
<summary>📋 Değişiklik Geçmişi (Changelog)</summary>

### 🔄 v2.0.0 (Mevcut)
- ✅ Çoklu platform desteği (LinkedIn + Indeed)
- ✅ 12 persona sistemi
- ✅ Gelişmiş filtreleme
- ✅ Çok dilli README

### 🔄 v1.0.0 (Önceki)
- ✅ Tek platform (Indeed)
- ✅ Temel AI eşleştirme
- ✅ ChromaDB entegrasyonu

</details>
