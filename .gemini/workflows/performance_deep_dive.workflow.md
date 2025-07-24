# META
# Name: Performance Deep Dive
# Description: Bir uygulamanın performansını logları ve kodu analiz ederek derinlemesine inceler, darboğazları bulur ve optimizasyon önerileri sunar.
# Category: Analysis
# Duration: ~8 minutes
# Input: Path to the module/directory and optional path to log files.
# Output: A detailed performance report with optimization suggestions.

# WORKFLOW STEPS

## Step 1: Log Analysis (Optional)
# Prompt: prompts/system/analyze_logs.prompt.md
# Input: {{log_files_path}}
# Output: log_analysis_report
# Purpose: Gerçek dünya kullanım verilerinden yavaş sorguları, sık hataları ve performans anormalliklerini tespit etmek.

---

## Step 2: Code Performance Analysis
# Prompt: prompts/code_generation/optimize_performance.prompt.md
# Input: {{module_path}}
# Output: code_performance_report
# Purpose: Koddaki verimsiz algoritmaları, I/O darboğazlarını ve bellek kullanımı sorunlarını bulmak.

---

## Step 3: Generate Business-Focused Report
# Prompt: prompts/system/generate_performance_report.prompt.md
# Input: {{log_analysis_report}} + {{code_performance_report}}
# Output: final_performance_report
# Purpose: Teknik bulguları, kullanıcı deneyimi ve maliyet gibi iş metriklerine etkileriyle birlikte raporlamak.
