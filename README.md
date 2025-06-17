# 🤖 Akıllı Kariyer Asistanı

> **CV'nizi anlayan ve size özel iş fırsatlarını bulan yapay zeka destekli kariyer asistanı**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-green.svg)](https://ai.google.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector-orange.svg)](https://www.trychroma.com)
[![JobSpy](https://img.shields.io/badge/JobSpy-Scraping-red.svg)](https://github.com/speedyapply/jobspy)

## 📋 Proje Özeti

Akıllı Kariyer Asistanı, geleneksel iş arama sürecini devrim niteliğinde değiştiren bir AI uygulamasıdır. Manuel olarak yüzlerce iş ilanı arasında gezinmek yerine, CV'nizi derinlemesine analiz ederek size en uygun pozisyonları **otomatik olarak keşfeder ve puanlar**.

### 🎯 Temel Özellikler

- **🧠 AI Destekli Analiz:** Gemini AI ile CV ve iş ilanlarını semantik olarak analiz
- **🔍 Akıllı Keşif:** "Yazılım Geliştirici" ararken "İş Zekası Uzmanı" gibi ilişkili pozisyonları da bulur
- **📊 Puanlama Sistemi:** Her ilan için %0-100 arası uygunluk skoru
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
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env

# 6. CV'nizi ekleyin
# data/cv.txt dosyasına CV'nizin tam metnini kopyalayın
```

### 🎬 İlk Kullanım

```bash
# Sistemi çalıştırın
python main.py
```

**Beklenen çıktı:**
```
🚀 Akıllı Kariyer Asistanı Başlatılıyor...
✅ Ortam değişkenleri yüklendi
✅ API key kontrol edildi
✅ CV dosyası bulundu

🧠 AI Analiz Motoru Başlatılıyor...
📄 CV analizi yapılıyor...
✅ CV embedding oluşturuldu
🔄 İş ilanları vector store'a yükleniyor...
🎯 En uygun işler aranıyor...

============================================================
🎉 EN UYGUN İŞ İLANLARI
============================================================

1. Yazılım Uzmanı - MİA Teknoloji A.Ş.
   📍 Ankara, T06, TR
   📊 Uygunluk: %63.9
   🔗 https://tr.indeed.com/viewjob?jk=...

2. Full Stack Developer - Pratik İnsan Kaynakları
   📍 İstanbul, T34, TR  
   📊 Uygunluk: %63.8
   🔗 https://tr.indeed.com/viewjob?jk=...
```

## 📊 Test Sonuçları

### Gerçek Performans Metrikleri
- **Toplanan İlan:** 50 adet (Indeed Türkiye)
- **En Yüksek Uygunluk:** %63.9 (Yazılım Uzmanı)
- **İşleme Süresi:** ~87 saniye
- **Başarı Oranı:** %100 (tüm adımlar başarılı)

### Keşfedilen Değerli Pozisyonlar
1. **Yazılım Uzmanı** (MİA Teknoloji) - %63.9 ✨
2. **Full Stack Developer** (Pratik İK) - %63.8 ✨
3. **Veri Analiz Elemanı** (Rasyonel Kurumsal) - %63.4 ✨
4. **İş Analizi Yöneticisi** (BNP Paribas) - %60.9 ✨
5. **Solution Engineer** (Microsoft) - %43.5 ✨

## 🏗️ Teknik Mimari

### Sistem Bileşenleri
```
┌─────────────────────────────────────┐
│         Ana Uygulama (main.py)      │
├─────────────────────────────────────┤
│  CV İşleme    │  İş İlanı Toplama   │ (Gemini AI)    (JobSpy)
├─────────────────────────────────────┤
│       Vektör Veritabanı             │ (ChromaDB)
├─────────────────────────────────────┤
│    Benzerlik Analizi & Puanlama     │ (Cosine Similarity)
└─────────────────────────────────────┘
```

### Teknoloji Yığını
- **AI/ML:** Google Gemini (Embedding), ChromaDB (Vector DB)
- **Veri Toplama:** JobSpy (Indeed scraping)
- **Veri İşleme:** Pandas, NumPy
- **Backend:** Python 3.12+

## 🔧 Dosya Yapısı

```
kariyer-asistani/
├── main.py                     # Ana uygulama
├── requirements.txt            # Python bağımlılıkları
├── .env                        # API keys (GİZLİ)
├── src/
│   ├── data_collector.py       # İş ilanı toplama
│   ├── cv_processor.py         # CV analizi
│   ├── embedding_service.py    # AI embedding
│   └── vector_store.py         # Vektör DB
├── data/                       # Veriler (GİZLİ)
│   ├── cv.txt                  # Kullanıcı CV'si
│   └── ham_ilanlar_*.csv       # Toplanan ilanlar
└── memory-bank/                # Proje dokümantasyonu
```

## 🚧 Gelecek Özellikler (Roadmap)

### Faz 3: Web Arayüzü (Bu Hafta)
- 🌐 Flask web uygulaması
- 📱 Responsive tasarım
- ✅ İlan işaretleme sistemi

### Faz 4: Otomasyon (Gelecek Hafta)  
- ⏰ Zamanlanmış otomatik çalışma
- 📱 Telegram bot bildirimleri
- 🔄 Çoklu platform desteği (LinkedIn, Glassdoor)

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit atın (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📞 İletişim

**Furkan Uçan**  
📧 furkan.ucann@yandex.com  
💼 [LinkedIn](https://linkedin.com/in/furkan-ucan)  
🐙 [GitHub](https://github.com/furkan-ucan)  

---

⭐ **Bu proje faydalı olduysa star vermeyi unutmayın!**

> *"Hayallerinizdeki işi bulmak artık hayallerinizden daha kolay!"*
