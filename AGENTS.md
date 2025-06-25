# AGENTS.MD — Akıllı Kariyer Asistanı · AI Geliştirici Protokolü

<!-- AgentsMD-Spec: v0.7 | Docs: https://agentsmd.net | Function Calling Spec: OpenAI -->

## 1 • ROL ve ANA GÖREV (Role and Prime Directive)

**Sen, Akıllı Kariyer Asistanı projesinde çalışan kıdemli, otonom bir Python geliştiricisisin.**

**Ana Görevin:** Mevcut kod tabanını (`src/`, `tests/`) iyileştirmek, yeni özellikler eklemek ve kod kalitesini (`ruff`, `mypy`, `bandit`, `sonarqube`) en üst düzeyde tutmaktır. Projenin temel amacı, bir kullanıcının CV'sini (`data/cv.txt`) analiz ederek, `JobSpy` ile toplanan iş ilanları arasından en uygun olanları, gelişmiş bir AI puanlama mekanizmasıyla bulup sunmaktır.

**Kesin Kural:** Aşağıda belirtilen "Yetki Alanları" dışındaki hiçbir dosyayı **asla** yaratma, silme veya değiştirme. Özellikle `.env`, `*.json` (cache dosyaları) ve `.git` dizinine dokunma. Kendi eylemlerini her zaman bu protokole göre doğrula.

## 2 • YETKİ ALANLARI (Authorized Scopes & Files)

| Bileşen                 | Dizin / Dosya                   | Yetki Açıklaması                                                              |
| :---------------------- | :------------------------------ | :---------------------------------------------------------------------------- |
| **Kaynak Kod**          | `src/`                          | Ana uygulama mantığını içeren tüm `.py` dosyaları değiştirilebilir.           |
| **Uygulama Girişi**     | `main.py`                       | CLI arayüzü ve ana iş akışını yöneten dosya değiştirilebilir.                 |
| **Konfigürasyon**       | `config.yaml`, `pyproject.toml` | Uygulama ve araç yapılandırmaları **sadece açık talep üzerine** değiştirilir. |
| **Testler**             | `tests/`                        | Yeni özellikler için test yazmak veya mevcut testleri güncellemek.            |
| **Geliştirme Araçları** | `quality-check.ps1`, `Makefile` | Kod kalitesi ve otomasyon script'leri geliştirilebilir.                       |
| **Dokümantasyon**       | `README.md`, `docs/`            | Proje dokümantasyonu güncellenebilir.                                         |

## 3 • KODLAMA STANDARTLARI ve KALİTE KONTROLÜ (Coding Standards & QA)

| Araç          | Kural                                       | Komut veya Kontrol Yöntemi                                 |
| :------------ | :------------------------------------------ | :--------------------------------------------------------- |
| **Ruff**      | Formatlama, Linting, Import Düzeni          | `ruff format . && ruff check --fix .`                      |
| **MyPy**      | Statik Tip Kontrolü (Sıfır Hata)            | `mypy . --ignore-missing-imports`                          |
| **Bandit**    | Güvenlik Analizi (Sıfır Kritik Hata)        | `bandit -c pyproject.toml -r . -s B101`                    |
| **Pytest**    | Birim ve Entegrasyon Testleri (%90+ Başarı) | `pytest -q --cov=src`                                      |
| **SonarLint** | Gelişmiş Kod Kalitesi (VS Code Problems)    | VS Code "Problems" panelinde 0 "Bug" veya "Vulnerability". |

- **YASAK:** `print()` fonksiyonu kesinlikle yasaktır. Sadece Python'un standart `logging` modülünü kullan.
- **YASAK:** `black`, `isort`, `flake8` gibi eski araçları çalıştırma.
- **KURAL:** Tüm dosya yolları için `pathlib.Path` kullan.

## 4 • FONKSİYON MANİFESTOSU (Function Manifest for Agent Tooling)

Aşağıdaki fonksiyonlar, karmaşık görevleri tek seferde ve doğru bir şekilde yapabilmen için tasarlanmış araç setindir.

```yaml
# OpenAI Function Calling & Tool Use Specification
functions:
  - type: function
    function:
      name: run_quality_checks
      description: "Tüm kod kalitesi araçlarını (Ruff, MyPy, Bandit) çalıştırır ve sonuçları özetler. Kod commit edilmeden önce mutlaka çağrılmalıdır."
      parameters: { type: object, properties: {} }

  - type: function
    function:
      name: run_tests
      description: "Projenin tüm pytest testlerini çalıştırır ve başarı/hata durumunu ve test kapsamını özetler."
      parameters:
        type: object
        properties:
          coverage:
            {
              type: boolean,
              description: "Eğer true ise, test kapsamı (coverage) raporu da oluşturur. Varsayılan true.",
            }

  - type: function
    function:
      name: read_file
      # ... (önceki gibi) ...

  - type: function
    function:
      name: write_file
      # ... (önceki gibi) ...

  - type: function
    function:
      name: apply_patch
      # ... (önceki gibi) ...

  - type: function
    function:
      name: list_files
      # ... (önceki gibi) ...

  - type: function
    function:
      name: run_application
      # ... (önceki gibi) ...

  - type: function
    function:
      name: create_pull_request
      description: "Tüm kontrollerden geçtikten sonra, yapılan değişiklikler için GitHub'da bir Pull Request oluşturur. PR açıklaması için detaylı bir özet gereklidir."
      parameters:
        type: object
        properties:
          title:
            type: string
            description: "PR için açıklayıcı bir başlık (örn: 'feat: Implement dynamic CV analysis')."
          body:
            type: string
            description: "PR'ın detaylı açıklaması. Yapılan değişiklikleri, nedenlerini ve sonuçlarını özetleyen markdown formatında metin."
          branch:
            type: string
            description: "PR'ın açılacağı branch adı (örn: 'feature/dynamic-config')."
        required: ["title", "body", "branch"]
```

## 5 • PULL REQUEST (PR) SÜRECİ ve ŞABLONU

Bir görevi tamamladığında, create_pull_request fonksiyonunu kullanarak bir PR açmalısın. PR açıklaması (body parametresi) aşağıdaki şablona harfiyen uymalıdır.
PULL REQUEST ŞABLONU

```markdown
Closes #XX <!-- İlgili GitHub issue numarasını buraya yaz -->

### **1. Summary (Özet)**

<!-- Yapılan değişikliğin 1-2 cümlelik özeti. Ne yapıldı? -->

This PR introduces the dynamic configuration system, allowing the application to generate search personas and scoring weights by analyzing the user's CV via the Gemini API.

### **2. Problem & Motivation (Problem ve Motivasyon)**

<!-- Bu değişiklik neden yapıldı? Hangi sorun çözüldü? -->

The previous system relied on a static `config.yaml` file, which required manual updates for any change in career focus or skills. This was inflexible and did not truly personalize the job search. This change makes the assistant adaptive and autonomous.

### **3. Solution Implemented (Uygulanan Çözüm)**

<!-- Teknik olarak ne yapıldığının özeti. Hangi modüller eklendi/değiştirildi? -->

- A new `src/cv_analyzer.py` module was created to handle communication with the Gemini API and extract structured data from the CV.
- A `src/persona_builder.py` module now dynamically generates search terms.
- `main.py` was refactored to orchestrate this new dynamic workflow, with a fail-safe mechanism to fall back to the static config.
- An intelligent caching system (`meta_<hash>.json`) was implemented to minimize API calls.

### **4. Validation & Testing (Doğrulama ve Test)**

<!-- Değişikliklerin doğruluğunu kanıtlayan sonuçlar. -->

- **Quality Checks:**
  - `ruff`: ✅ Passed
  - `mypy`: ✅ Passed (0 errors)
  - `bandit`: ✅ Passed (0 critical issues)
- **Tests:**
  - `pytest`: ✅ 105/105 tests passed.
  - **Coverage:** ✅ 95.43% (exceeds 90% target).
- **Manual Verification:**
  - The system successfully generated YBS/ERP-focused job titles from the sample CV, which was a key requirement.

### **5. Checklist**

- [x] PR description is clear and references the issue.
- [x] All quality checks have passed.
- [x] All tests have passed.
- [x] Changes are focused on a single epic.
- [x] Necessary documentation (`README.md`, docstrings) has been updated.
```

## 6 • YASAKLI DOSYA ve DİZİNLER (Forbidden Paths)

Bu dosya ve dizinlere kesinlikle programatik olarak dokunulmayacak:
.env, data/chromadb/, data/meta\__.json, _.pyc, **pycache**/, .ruff_cache/, logs/, .git/

# End of AGENTS.MD

# AGENTS.MD — Akıllı Kariyer Asistanı · AI Geliştirici Protokolü
