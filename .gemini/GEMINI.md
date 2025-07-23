# 🏛️ LOGOS SYSTEM ARCHITECTURE v1.0

## Akıllı Kariyer Asistanı - Birleşik Sistem Mimarisi

```
    ╭─────────────────────────────────────────────────────╮
    │  🎯 LOGOS: Birleşik GEMINI.md Sistem Mimarisi      │
    │  Bir sistem, üç felsefe, sonsuz olasılık           │
    ╰─────────────────────────────────────────────────────╯
```

Bu dosya, Akıllı Kariyer Asistanı projesi için tasarlanmış modüler, ölçeklenebilir ve evrimleşebilen bir yapay zeka işbirliği sistemidir. Üç farklı felsefeyi (Anayasa, Arsenal, Fabrika) tek bir çatı altında birleştiren **LOGOS** mimarisi.

## 📚 TEMEL MODÜLLER

### 🏛️ ANAYASA (Katman 0 - Temel)

**Değişmez yasalar ve proje kimliği**
@./00_CONSTITUTION.md

### ⚔️ ARSENAL (Katman 1 - Araç Kutusu)

**Uzman prompt'lar ve araçlar**
@./01_PROMPT_LIBRARY.md

### 🏭 FABRIKA (Katman 2 - İş Akışları)

**Otomatize edilmiş süreçler ve tarifler**
@./02_WORKFLOWS.md

### 🧠 META (Katman 3 - Öz-Farkındalık)

**Sistem kendini analiz etme ve iyileştirme protokolleri**
@./99_META.md

---

## 🚀 HIZLI BAŞLANGIÇ

```bash
# Proje durumu analizi için
gemini -p "Proje genel durumunu analiz et" @.gemini/GEMINI.md

# Kod analizi için
gemini -p "Bu kodu açıkla" @.gemini/prompts/code_analysis/explain_code.prompt.md @src/main.py

# Otomatik refactor ve test için
gemini -p "Full refactor ve test akışını çalıştır" @.gemini/workflows/full_refactor_and_test.workflow.md
```

## 🎯 SISTEM İLKELERİ

- **Modülerlik**: Her bileşen bağımsız çalışabilir
- **Ölçeklenebilirlik**: Yeni prompt'lar ve akışlar kolayca eklenebilir
- **Evrimleşme**: Sistem kendini analiz edip iyileştirebilir
- **Tutarlılık**: Tüm katmanlar aynı felsefe etrafında birleşir
- **Şeffaflık**: Her işlem izlenebilir ve doğrulanabilir

---

_Tasarım: LOGOS Meta-Mimarı | Versiyon: 1.0 | Tarih: 2025-07-21_
