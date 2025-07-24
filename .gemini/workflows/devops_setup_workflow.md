# META
# Name: DevOps Starter Kit
# Description: Proje için GitHub Actions tabanlı bir CI/CD pipeline'ı ve ilgili otomasyon script'lerini oluşturur.
# Category: DevOps
# Duration: ~6 minutes
# Input: Project type (e.g., Python, Node.js)
# Output: CI/CD configuration files and helper scripts.

# WORKFLOW OVERVIEW
# Bu iş akışı, bir proje için test, build ve deploy süreçlerini otomatize eden temel DevOps altyapısını kurar.

# WORKFLOW STEPS

## Step 1: CI Pipeline Generation
# Prompt: prompts/system/create_ci_pipeline.prompt.md
# Input: {{project_type}}
# Output: ci_yaml
# Purpose: GitHub Actions için projenin diline ve yapısına uygun bir `main.yml` dosyası oluşturmak.

---

## Step 2: Test Runner Script
# Prompt: prompts/system/create_shell_script.prompt.md
# Input: "Create a script to install dependencies and run all tests with coverage."
# Output: test_script
# Purpose: CI pipeline'ında kullanılacak `scripts/run-tests.sh` script'ini oluşturmak.

---

## Step 3: Deployment Script
# Prompt: prompts/system/create_shell_script.prompt.md
# Input: "Create a script to build the project and deploy it to a staging environment."
# Output: deploy_script
# Purpose: CI pipeline'ında kullanılacak `scripts/deploy.sh` script'ini oluşturmak.

---

## Step 4: Pipeline Documentation
# Prompt: prompts/documentation/create_documentation.prompt.md
# Input: {{ci_yaml}} + "Document the CI/CD pipeline, explaining each step, triggers, and secrets."
# Output: pipeline_docs
# Purpose: `docs/CI_CD_GUIDE.md` dosyasını oluşturarak pipeline'ın nasıl çalıştığını ve nasıl yönetileceğini açıklamak.
