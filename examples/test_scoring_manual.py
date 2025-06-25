#!/usr/bin/env python3
"""Test Intelligent Scoring System functionality"""

# Third Party
import yaml

# Local
from src.intelligent_scoring import IntelligentScoringSystem

# Load config
with open("config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Create scoring system
scoring = IntelligentScoringSystem(config)

# Test cases
test_jobs = [
    {"title": "Junior Developer", "description": "Fresh graduate position"},
    {"title": "Senior Developer", "description": "5+ yıl deneyim gereklidir"},
    {"title": "Software Engineer", "description": "2 yıl deneyim"},
    {"title": "Lead Developer", "description": "Team management required"},
    {"title": "Intern Software Developer", "description": "No experience required"},
    {"title": "Manager", "description": "Leadership role"},
]

print("🔍 Intelligent Scoring System Test Results")
print("=" * 60)

for job in test_jobs:
    score, details = scoring.score_job(job)
    decision = "✅ KABUL" if scoring.should_include(score) else "❌ RED"

    print(f"\n📋 İlan: {job['title']}")
    print(f"📝 Açıklama: {job['description']}")
    print(f"🎯 Toplam Skor: {score}")
    print(f"📊 Detaylar: {details}")
    print(f"🏆 Karar: {decision}")
    print("-" * 40)

print("\n⚙️ Sistem Ayarları:")
print(f"🎯 Eşik Değeri: {scoring.threshold}")
print(f"➕ Pozitif Kelimeler: {config['scoring_system']['title_weights']['positive']}")
print(f"➖ Negatif Kelimeler: {config['scoring_system']['title_weights']['negative']}")
