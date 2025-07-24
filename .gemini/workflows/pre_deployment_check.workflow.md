# META
# Name: Pre-Deployment Check
# Description: Deploy öncesi test, lint, güvenlik ve dokümantasyon kontrollerini içeren bir kontrol listesi çalıştırır.
# Category: DevOps & Operations
# Duration: ~4 minutes
# Input: Path to the code to be deployed.
# Output: A go/no-go decision checklist.

# WORKFLOW STEPS

## Step 1: Run All Tests
# Prompt: prompts/system/create_shell_script.prompt.md
# Input: "Create a script that runs all unit and integration tests with coverage reporting. The script should exit with a non-zero code if any test fails or if coverage is below 80%."
# Output: test_runner_script
# Purpose: Projenin test suit'ini çalıştırmak.

---

## Step 2: Code Quality & Linting Check
# Prompt: prompts/code_analysis/review_code_quality.prompt.md
# Input: {{module_path}}
# Output: quality_report
# Purpose: Kodun kalite standartlarına ve linting kurallarına uygunluğunu kontrol etmek.

---

## Step 3: Security Scan
# Prompt: prompts/security/audit_security.prompt.md
# Input: {{module_path}}
# Output: security_report
# Purpose: Son dakika güvenlik zafiyetlerini kontrol etmek.

---

## Step 4: Documentation Check
# Prompt: prompts/documentation/document_code.prompt.md
# Input: {{module_path}} + "Check for any public functions or classes missing documentation."
# Output: documentation_report
# Purpose: Public API'ların dokümante edildiğinden emin olmak.
