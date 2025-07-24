# META
# Name: Project Health Check
# Description: Projenin genel mimarisini, kod kalitesini, güvenliğini ve performansını analiz ederek kapsamlı bir sağlık raporu ve iyileştirme yol haritası oluşturur.
# Category: Analysis
# Duration: ~10 minutes
# Input: Project root directory
# Output: Health report, action items, and suggested roadmap.

# WORKFLOW STEPS

## Step 1: Architecture Review
# Prompt: prompts/code_analysis/analyze_architecture.prompt.md
# Input: {{module_path}}
# Output: architecture_report
# Purpose: Sistemin genel yapısını, bileşenlerini ve ilişkilerini anlamak.

---

## Step 2: Code Quality Review
# Prompt: prompts/code_analysis/review_code_quality.prompt.md
# Input: {{module_path}}
# Output: quality_report
# Purpose: Kodu SOLID, clean code ve en iyi pratikler açısından değerlendirmek.

---

## Step 3: Security Audit
# Prompt: prompts/security/audit_security.prompt.md
# Input: {{module_path}}
# Output: security_report
# Purpose: Güvenlik zafiyetlerini taramak.

---

## Step 4: Performance Analysis
# Prompt: prompts/code_generation/optimize_performance.prompt.md
# Input: {{module_path}}
# Output: performance_report
# Purpose: Potansiyel performans darboğazlarını tespit etmek.

---

## Step 5: Generate Improvement Plan
# Prompt: prompts/project_management/plan_project.prompt.md
# Input: {{architecture_report}} + {{quality_report}} + {{security_report}} + {{performance_report}}
# Output: final_report_with_roadmap
# Purpose: Tüm analizleri birleştirip, önceliklendirilmiş aksiyonlar içeren bir iyileştirme planı ve yol haritası oluşturmak.
