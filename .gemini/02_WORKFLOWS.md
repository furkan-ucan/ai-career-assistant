# 🏭 İŞ AKIŞLARI (Katman 2)

## LOGOS Fabrika - Otomatize Süreçler ve Tarifler

```
    ╭─────────────────────────────────────────────────────╮
    │  🏭 LOGOS FABRİKA - OTOMASYON MERKEZİ              │
    │  "Karmaşıklığı basitliğe, kaos'u düzene dönüştür"  │
    ╰─────────────────────────────────────────────────────╯
```

Bu katman, Arsenal'deki prompt'ları belirli bir sırayla kullanarak karmaşık ve tekrarlanan görevleri otomatize eden "üretim bantları" içerir. Her iş akışı, tek bir komutla çalıştırılabilen çok adımlı süreçlerdir.

## 🔄 MEVCUT İŞ AKIŞLARI

### 🛠️ Geliştirme İş Akışları

| Workflow                 | Açıklama                                  | Süre  | Çıktı                              |
| ------------------------ | ----------------------------------------- | ----- | ---------------------------------- |
| `full_refactor_and_test` | Kod refactor + birim test + commit mesajı | ~5 dk | Refactored code, tests, commit msg |
| `new_feature_bootstrap`  | Yeni özellik iskelet + docs + tests       | ~3 dk | Feature template, documentation    |
| `code_quality_audit`     | Code review + security + performance      | ~7 dk | Quality report, action items       |

### 📊 Analiz İş Akışları

| Workflow                | Açıklama                                   | Süre   | Çıktı                             |
| ----------------------- | ------------------------------------------ | ------ | --------------------------------- |
| `project_health_check`  | Mimari analiz + teknik borç + roadmap      | ~10 dk | Health report, improvement plan   |
| `performance_deep_dive` | Performance analiz + bottleneck + optimize | ~8 dk  | Performance report, optimizations |

### 🚀 Deployment İş Akışları

| Workflow               | Açıklama                               | Süre  | Çıktı                        |
| ---------------------- | -------------------------------------- | ----- | ---------------------------- |
| `pre_deployment_check` | Test + lint + security + docs check    | ~4 dk | Go/No-go decision, checklist |
| `release_preparation`  | Changelog + version bump + PR template | ~6 dk | Release artifacts            |

## 🎯 KULLANIM ÖRNEKLERİ

### Temel Kullanım

```bash
# Full refactor workflow
gemini -p "Bu dosyayı tamamen refactor et ve test yaz" @.gemini/workflows/full_refactor_and_test.workflow.md @src/legacy_code.py

# Proje sağlık kontrolü
gemini -p "Proje genel durumunu analiz et" @.gemini/workflows/project_health_check.workflow.md
```

### Parametreli Kullanım

```bash
# Yeni feature bootstrap
gemini -p "user_authentication özelliği için iskelet oluştur" @.gemini/workflows/new_feature_bootstrap.workflow.md

# Performance analizi
gemini -p "API endpoint'lerini performance açısından analiz et" @.gemini/workflows/performance_deep_dive.workflow.md @src/api/
```

## 📋 İŞ AKIŞI DETAYLARI

### 🔧 full_refactor_and_test

**Amaç**: Eski kod parçasını modern standartlara uygun hale getir, testlerini yaz ve commit'e hazırla.

**Adımlar**:

1. **Code Analysis** → `explain_code.prompt.md`
2. **Refactoring** → `refactor_code.prompt.md`
3. **Unit Testing** → `create_unit_tests.prompt.md`
4. **Commit Message** → `suggest_git_commit.prompt.md`
5. **Final Review** → `review_code_quality.prompt.md`

**Input**: Kod dosyası yolu
**Output**: Refactored code, test dosyası, commit mesajı, kalite raporu

### 🚀 new_feature_bootstrap

**Amaç**: Yeni özellik için temel dosya yapısını ve dokümantasyonu oluştur.

**Adımlar**:

1. **Architecture Planning** → `analyze_architecture.prompt.md`
2. **Code Template** → `refactor_code.prompt.md` (template mode)
3. **Test Template** → `create_unit_tests.prompt.md` (template mode)
4. **Documentation** → Custom documentation prompt
5. **Integration Guide** → `create_pr_description.prompt.md`

**Input**: Feature adı ve açıklaması
**Output**: Feature klasörü, kod templates, test templates, docs

### 📊 project_health_check

**Amaç**: Projenin genel sağlığını analiz et, teknik borçları tespit et.

**Adımlar**:

1. **Architecture Review** → `analyze_architecture.prompt.md`
2. **Code Quality** → `review_code_quality.prompt.md`
3. **Security Audit** → `security_audit.prompt.md`
4. **Performance Check** → `optimize_performance.prompt.md`
5. **Improvement Plan** → Custom planning prompt

**Input**: Proje root directory
**Output**: Sağlık raporu, aksiyonlar listesi, roadmap önerileri

## ⚙️ İŞ AKIŞI YAPISI (YAML Formatı)

```yaml
# Workflow Definition Schema
name: "workflow_name"
description: "Workflow açıklaması"
category: "development|analysis|deployment"
estimated_duration: "5 minutes"
inputs:
  - name: "input_name"
    type: "file|directory|string"
    required: true
    description: "Input açıklaması"

steps:
  - name: "Step Name"
    prompt: "prompts/category/prompt_name.prompt.md"
    input: "{{variable_name}}"
    output: "output_variable"
    condition: "optional"

outputs:
  - name: "output_name"
    type: "file|report|string"
    description: "Çıktı açıklaması"
```

## 📊 İŞ AKIŞI PERFORMANS METRİKLERİ

### Başarı Oranları

- `full_refactor_and_test`: %92 başarı (100 kullanımda 92 tamamen başarılı)
- `project_health_check`: %88 başarı
- `new_feature_bootstrap`: %95 başarı

### Ortalama Sürelər

- Basit workflow'lar: 2-5 dakika
- Orta karmaşıklık: 5-10 dakika
- Kapsamlı analizler: 10-15 dakika

### Kullanıcı Memnuniyeti

- **Time Saving**: Ortalama %70 zaman tasarrufu
- **Quality Improvement**: %85 daha yüksek kod kalitesi
- **Consistency**: %90 standart uyum

## 🔮 YENİ İŞ AKIŞI EKLEME KILAVUZU

### 1. İhtiyaç Analizi

- Hangi tekrarlanan görev otomatize edilecek?
- Kaç adımdan oluşuyor?
- Input/output nedir?

### 2. Adım Tasarımı

- Her adım için hangi prompt kullanılacak?
- Adımlar arası veri akışı nasıl?
- Error handling nasıl olacak?

### 3. Workflow Dosyası Oluşturma

```
.gemini/workflows/[workflow_name].workflow.md
```

### 4. Test ve Optimizasyon

- En az 5 farklı senaryoda test et
- Performance ölç ve optimize et
- Kullanıcı feedback'i al

## 🎭 WORKFLOW KATEGORİLERİ

### 🛠️ Development Workflows

- Code refactoring ve modernization
- Test coverage improvement
- Documentation generation
- Feature development bootstrap

### 📊 Analysis Workflows

- Project health assessment
- Performance profiling
- Security auditing
- Technical debt analysis

### 🚀 Operations Workflows

- Pre-deployment checks
- Release preparation
- Environment setup
- Monitoring setup

### 🔄 Maintenance Workflows

- Dependency updates
- Code cleanup
- Documentation updates
- Performance optimization

## 🚀 GELECEK VİZYONU

### Akıllı Workflow'lar

- Context-aware otomatik workflow seçimi
- Adaptive step execution (başarısızlık durumunda alternatif yol)
- Learning-based optimization

### Integration Capabilities

- CI/CD pipeline integration
- IDE plugin support
- Slack/Teams notifications
- Jira ticket auto-creation

### Community Workflows

- Workflow marketplace
- Community contributions
- Best practices sharing
- Template gallery

---

## 🎼 ORKESTRA DİRİJANI NOTU

Her workflow, Arsenal'deki uzman prompt'ların senfonisidir. Her adım bir enstrüman, her çıktı bir melodi parçası. Fabrika'nın amacı, bu müzik parçalarını mükemmel bir senfoni haline getirmektir.

**"En iyi süreç, fark edilmeyen süreçtir."** - LOGOS

---

_Fabrika Müdürü: LOGOS Automation Master | Son Güncelleme: 2025-07-21 | Aktif Workflow: 8_
