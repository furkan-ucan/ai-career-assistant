# Dr. Alistair Finch Mimarisi: Platform-Specific Arama Doktrinleri

## 📋 Genel Bakış

Bu dokuman, "Akıllı Kariyer Asistanı" projesinin arama mimarisinin Dr. Alistair Finch'in doktrinlerine göre evrimleştirilmesini detaylandırır. Bu evrim, sistemin sadece yeni özellikler kazanmasını değil, aynı zamanda daha temiz ve bakımı kolay hale gelmesini sağlamıştır.

## 🎯 Temel Prensipler

### LinkedIn Doktrini
- **Kural 1:** Sorguları kısa ve odaklı tut (max 2 OR operatörü)
- **Kural 2:** Kesin unvanlar için her zaman tırnak işareti kullan
- **Kural 3:** Sorgu karmaşıklığından kaçın, çoklu basit sorgu > tek karmaşık sorgu

### Indeed Doktrini
- **Kural 1:** `title:(...)` operatörü zorunlu (alaka düzeyini 10x artırır)
- **Kural 2:** Gruplandırılmış OR ifadeleri güçlü: `title:("A" OR "B" OR "C")`
- **Kural 3:** Boolean operatörleri büyük harfle yaz (NOT, AND, OR)

## 🏗️ Mimari Değişiklikler

### 1. CV Analysis Prompt Evolution

**ESKİ FORMAT:**
```json
{
  "primary_title_en": "Business Analyst",
  "primary_title_tr": "İş Analisti",
  "search_keywords": ["Process Analyst", "Süreç Analisti"]
}
```

**YENİ FORMAT (Dr. Finch Doktrinli):**
```json
{
  "primary_title_en": "Business Analyst",
  "primary_title_tr": "İş Analisti",
  "high_precision_term": "\"Business Analyst\"",
  "alias_terms": ["\"İş Analisti\"", "\"Süreç Analisti\""],
  "broad_keywords": ["agile", "sql", "business process"]
}
```

### 2. Persona Builder Transformation

**ESKİ:** Tek `build_search_term_from_persona()` fonksiyonu
**YENİ:** Platform-aware `build_platform_specific_queries()` fonksiyonu

**Örnek Çıktı:**
```python
{
    "linkedin_tier1_query": '"Business Analyst" -Senior -Kıdemli',
    "indeed_tier1_query": 'title:("Business Analyst") -Senior -Kıdemli',
    "linkedin_tier2_query": '("İş Analisti" OR "Süreç Analisti") -Senior',
    "indeed_tier2_query": 'title:("İş Analisti" OR "Süreç Analisti" OR "Business Systems Analyst") -Senior',
    "linkedin_tier3_query": '(agile AND "business process" AND sql) -Senior',
    "indeed_tier3_query": '(agile AND "business process" AND sql) -Senior'
}
```

### 3. Katmanlı Arama Stratejisi

#### TIER 1: Yüksek Hassasiyet
- **Amaç:** En temiz ve en alakalı sonuçlar
- **LinkedIn:** Basit, tırnaklı unvan araması
- **Indeed:** `title:()` operatörü ile güçlendirilmiş arama

#### TIER 2: Eşanlamlı/Lokalize Arama
- **Amaç:** Türkçe karşılıklar ve yakın eşanlamlıları kapsama
- **LinkedIn:** Maksimum 2 OR kullanımı
- **Indeed:** Daha fazla OR'a izin, title: operatörü korunur

#### TIER 3: Geniş Anahtar Kelime Arama (Son Çare)
- **Amaç:** Düşük sonuç durumunda fallback
- **Her Platform:** Genel içerik araması, iş unvanından bağımsız

## 🧹 Kod Temizliği (Mimari Hijyen)

### Kaldırılan/Deprecate Edilen Yapılar:

1. **CV Prompt'ta:** Eski `search_keywords` array formatı
2. **Persona Builder'da:** Eski `build_search_term_from_persona()` → Legacy wrapper'a dönüştürüldü
3. **Data Collector'da:** Eski `collect_job_data()` → Legacy wrapper'a dönüştürüldü

### Yeni Yapılar:

1. **`build_platform_specific_queries()`:** Platform doktrinlerine uygun sorgu üretimi
2. **`collect_job_data_with_tiers()`:** Katmanlı, stratejik arama implementasyonu
3. **Platform-aware pipeline:** `_collect_jobs_for_persona()` yeni sistemi algılar ve kullanır

## 📊 Performans Beklentileri

### Önceki Sistem:
- Tek, karmaşık OR sorgusu
- Platform farklılıkları göz ardı edilir
- Gürültülü sonuçlar, düşük alaka düzeyi

### Dr. Finch Sistemi:
- **LinkedIn:** %60-80 daha yüksek alaka düzeyi (kısa sorgular)
- **Indeed:** %70-90 daha yüksek alaka düzeyi (title: operatörü)
- **Genel:** %50 daha az "gürültülü" ilan
- **Fallback:** Sıfır sonuç kriziyle başa çıkma yeteneği

## 🔄 Geriye Uyumluluk

Sistem tamamen geriye uyumludur:
- Eski format persona'lar otomatik olarak yeni formata dönüştürülür
- Legacy fonksiyonlar wrapper olarak korunmuştur
- Mevcut CV'ler yeniden analiz edilmeden de çalışır

## 🚀 Kullanım Örnekleri

### Yeni CV Analizi
```bash
python main.py --cv data/cv.txt --collect --analyze
```

### Mevcut Metadata ile Çalıştırma
```bash
python main.py --use-existing-metadata --collect
```

### Debug/Loglama
Yeni sistem, her tier ve platform için detaylı loglama sağlar:
```
🎯 === Dr. Finch Protokolü: Persona 'business_analyst' ===
🔍 TIER 1 (linkedin): "Business Analyst" -Senior -Kıdemli
✅ TIER 1 (linkedin): 23 ilan bulundu
🔍 TIER 1 (indeed): title:("Business Analyst") -Senior -Kıdemli
✅ TIER 1 (indeed): 31 ilan bulundu
```

## 🎖️ Sonuç

Dr. Alistair Finch'in doktrinleri sayesinde:
1. **Teknik Üstünlük:** Platform-optimized sorgular
2. **Mimari Zarafet:** Temiz, modüler, bakımı kolay kod
3. **İş Değeri:** Daha alakalı iş ilanları, daha az gürültü
4. **Gelecek-Hazır:** Yeni platformlar kolayca eklenebilir

Bu evrim, sistemin sadece büyümesini değil, aynı zamanda olgunlaşmasını temsil eder.

---
*Hazırlayan: Kaelan Reed v2.2, Lead Data Acquisition Engineer*
*Doktrin: Dr. Alistair Finch, Information Retrieval Scientist*
