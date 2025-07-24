# META
# Name: New Module Bootstrap
# Description: Yeni bir özellik modülü için klasör yapısı, API tasarımı, başlangıç kodu, testler ve dokümantasyon oluşturur.
# Category: Development
# Duration: ~8 minutes
# Input: Feature description (string)
# Output: A new module directory with complete boilerplate

# WORKFLOW OVERVIEW
# Bu iş akışı, yeni bir özellik için gereken tüm başlangıç dosyalarını ve yapılandırmasını oluşturarak geliştirme sürecini hızlandırır.

# WORKFLOW STEPS

## Step 1: Feature Planning
# Prompt: prompts/project_management/plan_project.prompt.md
# Input: {{feature_description}}
# Output: feature_plan
# Purpose: Özelliğin kapsamını, kullanıcı hikayelerini ve görevlerini belirlemek.

---

## Step 2: Directory Scaffolding
# Prompt: prompts/project_management/setup_project_structure.prompt.md
# Input: {{feature_plan}}
# Output: directory_structure
# Purpose: Özellik için gerekli klasör ve boş dosya yapısını oluşturmak.

---

## Step 3: API Design
# Prompt: prompts/code_generation/design_api.prompt.md
# Input: {{feature_plan}}
# Output: api_spec
# Purpose: Modülün dış dünyaya açılacak API'ını tasarlamak ve OpenAPI spek'i oluşturmak.

---

## Step 4: Template Code Generation
# Prompt: prompts/code_generation/refactor_code.prompt.md
# Input: {{api_spec}}
# Output: initial_code
# Purpose: API spek'ine uygun olarak başlangıç kodunu (controller, service vb.) oluşturmak.

---

## Step 5: Unit Test Generation
# Prompt: prompts/code_generation/create_unit_tests.prompt.md
# Input: {{initial_code}}
# Output: test_code
# Purpose: Oluşturulan başlangıç kodu için birim testleri iskeleti hazırlamak.

---

## Step 6: Code Documentation
# Prompt: prompts/documentation/document_code.prompt.md
# Input: {{initial_code}}
# Output: documented_code
# Purpose: Koddaki fonksiyon ve sınıflar için docstring'ler eklemek.

---

## Step 7: Module README
# Prompt: prompts/documentation/create_documentation.prompt.md
# Input: {{feature_plan}} + {{api_spec}}
# Output: module_readme
# Purpose: Modülün nasıl kullanılacağını açıklayan bir README.md dosyası oluşturmak.
