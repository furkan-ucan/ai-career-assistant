# ⚔️ PROMPT KÜTÜPHANESİ (Katman 1)

## LOGOS Arsenal - Uzman Prompt Koleksiyonu

```
    ╭─────────────────────────────────────────────────────╮
    │  🎯 LOGOS ARSENAL - UZMAN PROMPT KÜTÜPHANESİ       │
    │  "Doğru araç, doğru iş için doğru zamanda"         │
    ╰─────────────────────────────────────────────────────╯
```

Bu katman, Anayasa'ya uygun olarak çalışan, her biri belirli bir göreve adanmış uzman prompt'ları içerir. Her prompt, kendi alanında mükemmel sonuçlar üretecek şekilde özenle tasarlanmıştır.

## 🎭 KATEGORİLER VE UZMANLAR

### 🔬 KOD ANALİZİ

| Prompt                 | Uzman Persona                 | Açıklama                                                |
| ---------------------- | ----------------------------- | ------------------------------------------------------- |
| `explain_code`         | Marcus Chen (Senior Engineer) | Kod parçasının amacını ve karmaşık bölümlerini açıklar  |
| `analyze_architecture` | Elena Rodriguez (Tech Lead)   | Sistem mimarisini ve bileşen ilişkilerini analiz eder   |
| `review_code_quality`  | Maria Santos (Code Reviewer)  | SOLID prensipleri ve clean code açısından değerlendirir |

### 🏗️ KOD ÜRETİMİ VE REFACTORING

| Prompt                     | Uzman Persona                    | Açıklama                                                  |
| -------------------------- | -------------------------------- | --------------------------------------------------------- |
| `refactor_code`            | Anya Sharma (Clean Code Expert)  | DRY ve SOLID prensiplerine göre kodu yeniden yapılandırır |
| `create_unit_tests`        | Viktor Petrov (QA Engineer)      | Kapsamlı birim testleri oluşturur                         |
| `optimize_performance`     | Sarah Kim (Performance Engineer) | Performans bottleneck'lerini tespit eder ve optimize eder |
| `design_api`               | Robert Chen (Backend Architect)  | RESTful API tasarımı ve OpenAPI dokumentasyonu oluşturur  |
| `create_integration_tests` | Jennifer Wu (QA Automation)      | End-to-end test senaryoları oluşturur                     |

### 📊 GIT VE PROJE YÖNETİMİ

| Prompt                    | Uzman Persona                  | Açıklama                                                  |
| ------------------------- | ------------------------------ | --------------------------------------------------------- |
| `suggest_git_commit`      | Conventional Commits Expert    | Conventional Commits standardına uygun mesaj önerir       |
| `create_pr_description`   | Robert Chen (Tech Lead)        | Profesyonel Pull Request açıklaması oluşturur             |
| `analyze_git_history`     | Elena Rodriguez (DevOps)       | Git geçmişini analiz eder ve iyileştirme önerir           |
| `plan_project`            | David Chen (Project Manager)   | Detaylı proje planlaması yapar                            |
| `setup_project_structure` | Isabella Chen (Technical Lead) | Proje iskeletleri ve başlangıç yapılandırmaları oluşturur |

### 🛡️ GÜVENLİK VE KALİTE

| Prompt           | Uzman Persona                     | Açıklama                         |
| ---------------- | --------------------------------- | -------------------------------- |
| `audit_security` | Alex Thompson (Security Expert)   | Kapsamlı güvenlik denetimi yapar |
| `security_audit` | Alex Thompson (Security Engineer) | Güvenlik açıklarını tespit eder  |

### 📋 SİSTEM VE OTOMASYON

| Prompt                         | Uzman Persona                          | Açıklama                                 |
| ------------------------------ | -------------------------------------- | ---------------------------------------- |
| `create_shell_script`          | Ahmed Hassan (DevOps Engineer)         | Bash script'leri oluşturur               |
| `create_ci_pipeline`           | Ahmed Hassan (DevOps Architect)        | CI/CD pipeline yapılandırması oluşturur  |
| `analyze_logs`                 | David Park (Site Reliability Engineer) | Log analizi ve sistem troubleshooting    |
| `generate_performance_report`  | Sarah Kim (Performance Analyst)        | İş değeri odaklı performans raporları    |
| `create_optimal_settings_json` | Dr. Alistair Finch (Config Expert)     | Optimal VS Code yapılandırması oluşturur |

### 📚 DOKÜMANTASYON VE İLETİŞİM

| Prompt                 | Uzman Persona                | Açıklama                                      |
| ---------------------- | ---------------------------- | --------------------------------------------- |
| `create_documentation` | Lisa Park (Technical Writer) | Kapsamlı teknik dokümantasyon oluşturur       |
| `document_code`        | Lisa Park (Technical Writer) | JSDoc/DocString formatında kod dokümantasyonu |

### 🧠 SİSTEM VE META-MÜHENDİSLİK

| Prompt                       | Uzman Persona                      | Açıklama                                    |
| ---------------------------- | ---------------------------------- | ------------------------------------------- |
| `review_system_architecture` | LOGOS (Meta-Architect)             | Sistem mimarisini kendi kendine analiz eder |
| `review_my_prompt`           | Dr. Lena Petrov (DevEx Architect)  | Prompt'ları analiz edip optimize eder       |
| `optimize_gemini_setup`      | Dr. Alistair Finch (Config Expert) | Optimal Gemini CLI yapılandırması oluşturur |

## 🎯 KULLANIM ÖRNEKLERİ

### Temel Kullanım

```bash
# Kod açıklama
gemini -p "Bu kodu açıkla" @.gemini/prompts/code_analysis/explain_code.prompt.md @src/main.py

# Refactoring
gemini -p "Bu kodu refactor et" @.gemini/prompts/code_generation/refactor_code.prompt.md @src/legacy.py

# Commit mesajı
git diff --cached | gemini -p "Commit mesajı öner" @.gemini/prompts/git/suggest_git_commit.prompt.md
```

### Gelişmiş Kullanım

```bash
# Birden fazla dosya analizi
gemini -p "Mimariyi analiz et" @.gemini/prompts/code_analysis/analyze_architecture.prompt.md @src/ @tests/

# Güvenlik taraması
gemini -p "Güvenlik açığı tara" @.gemini/prompts/security/security_audit.prompt.md @src/api/
```

## 📁 PROMPT DOSYA YAPISI

Her prompt aşağıdaki standardize formatı takip eder:

```markdown
# META

# Name: prompt_name

# Description: Kısa açıklama

# Category: Kategori adı

# Expert: Uzman persona adı

# ROLE

[Uzman persona tanımı ve deneyim seviyesi]

# TASK

[Adım adım görev tanımı]

# INPUT

---

{{input}}
```

## 🔗 PROMPT LİSTESİ (Alfabetik)

### A-C

- `analyze_architecture` → Sistem mimarisi analizi
- `analyze_git_history` → Git geçmişi analizi
- `analyze_logs` → Log dosyalarından sistem sorunlarını tespit etme
- `audit_security` → Kapsamlı güvenlik denetimi
- `create_ci_pipeline` → GitHub Actions/GitLab CI pipeline oluşturma
- `create_documentation` → Teknik dokümantasyon oluşturma
- `create_integration_tests` → Entegrasyon testleri
- `create_optimal_settings_json` → Optimal VS Code settings.json oluşturma
- `create_pr_description` → Pull Request açıklaması
- `create_shell_script` → Bash script oluşturma
- `create_unit_tests` → Birim testleri

### D-G

- `design_api` → RESTful API tasarımı ve OpenAPI dokumentasyonu
- `document_code` → JSDoc/DocString formatında kod dokümantasyonu
- `explain_code` → Kod açıklama
- `generate_performance_report` → Performans analizi ve iş etkisi raporu

### H-P

- `optimize_gemini_setup` → Gemini CLI optimizasyonu
- `optimize_performance` → Performans optimizasyonu
- `plan_project` → Proje planlama ve yönetimi

### R-Z

- `refactor_code` → Kod refactoring
- `review_code_quality` → Kod kalite analizi
- `review_my_prompt` → Prompt optimizasyonu ve analiz
- `review_system_architecture` → Sistem mimarisi değerlendirmesi
- `security_audit` → Güvenlik denetimi
- `setup_project_structure` → Proje iskelet yapısı oluşturma
- `suggest_git_commit` → Git commit mesajı

## 🎨 YENİ PROMPT EKLEME KILAVUZU

### 1. Kategori Belirleme

Yeni prompt hangi kategoriye ait? Yoksa yeni kategori mi gerekli?

### 2. Uzman Persona Tasarlama

- İsim ve uzmanlık alanı
- Deneyim seviyesi (Junior, Senior, Principal)
- Kişilik özellikleri ve yaklaşım tarzı

### 3. Dosya Oluşturma

```
.gemini/prompts/[kategori]/[prompt_name].prompt.md
```

### 4. Test ve Doğrulama

- En az 3 farklı senaryoda test et
- Anayasa ile uyumluluğunu kontrol et
- Kütüphane indexini güncelle

## 🔄 KALİTE KONTROL

### Prompt Kalite Kriterleri

- ✅ **Netlik**: Görev tanımı açık ve anlaşılır
- ✅ **Spesifik**: Belirsizlik yok, somut adımlar mevcut
- ✅ **Tutarlılık**: Anayasa ile uyumlu
- ✅ **Test Edilebilirlik**: Çıktı ölçülebilir ve doğrulanabilir

### Performans Metrikleri

- **Doğruluk**: Prompt beklenen sonucu üretiyor mu?
- **Tutarlılık**: Aynı input için benzer output üretiyor mu?
- **Verimlilik**: İstenenden fazla token harcamıyor mu?

---

## 🚀 GELECEK ROADMap

### Kısa Vadeli (1-2 ay)

- [ ] Docker ve DevOps kategorisi ekle
- [ ] Database ve SQL prompts
- [ ] API design ve documentation prompts

### Orta Vadeli (3-6 ay)

- [ ] AI/ML specific prompts (model training, evaluation)
- [ ] Multi-language support (Python, TypeScript, Go)
- [ ] Automated prompt testing pipeline

### Uzun Vadeli (6+ ay)

- [ ] Adaptive prompts (kullanıcı tercihlerine göre)
- [ ] Community contributions framework
- [ ] Prompt performance analytics

---

**"Bir araç ne kadar keskinse, o kadar az güçle daha fazla iş yapar."** - LOGOS

---

_Küratör: LOGOS Arsenal Master | Son Güncelleme: 2025-07-23 | Toplam Prompt: 22_
