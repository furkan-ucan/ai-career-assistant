# META
# Name: Comprehensive Code Audit
# Description: Bir modülün kod kalitesini, performansını ve güvenliğini derinlemesine analiz eder ve birleştirilmiş bir rapor oluşturur.
# Category: Analysis
# Duration: ~10 minutes
# Input: Path to the module/directory
# Output: A comprehensive audit report in Markdown format.

# WORKFLOW OVERVIEW
# Bu iş akışı, mevcut bir kod tabanının sağlığını 360 derece değerlendirir ve teknik bulguları iş etkisine dönüştüren bir rapor sunar.

# WORKFLOW STEPS

## Step 1: Code Quality Review
# Prompt: prompts/code_analysis/review_code_quality.prompt.md
# Input: {{module_path}}
# Output: quality_report
# Purpose: Kodu SOLID, clean code ve diğer en iyi pratikler açısından değerlendirmek.

---

## Step 2: Performance Analysis
# Prompt: prompts/code_generation/optimize_performance.prompt.md
# Input: {{module_path}}
# Output: performance_report
# Purpose: Potansiyel performans darboğazlarını, bellek sızıntılarını ve verimsiz algoritmaları tespit etmek.

---

## Step 3: Security Audit
# Prompt: prompts/security/audit_security.prompt.md
# Input: {{module_path}}
# Output: security_report
# Purpose: OWASP Top 10 gibi standartlara göre güvenlik zafiyetlerini taramak.

---

## Step 4: Consolidated Business Report
# Prompt: prompts/system/generate_performance_report.prompt.md
# Input: {{quality_report}} + {{performance_report}} + {{security_report}}
# Output: final_audit_report
# Purpose: Tüm teknik bulguları birleştirip, yöneticilerin anlayabileceği, iş etkisine ve ROI'ye odaklanan tek bir rapor oluşturmak.
