# Standard Library
import os
import sys
import time

# Third Party
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Local
from src.filter import compare_filters, score_jobs, filter_junior_suitable_jobs
from src.intelligent_scoring import IntelligentScoringSystem


def load_scoring_system():
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return IntelligentScoringSystem(cfg)


def test_title_weighting_positive_negative():
    scoring = load_scoring_system()
    job = {"title": "Junior Developer", "description": ""}
    _, details = scoring.score_job(job)
    assert details["title"] > 0

    job = {"title": "Senior Developer", "description": ""}
    _, details = scoring.score_job(job)
    assert details["title"] < 0


def test_experience_regex_detection():
    scoring = load_scoring_system()
    job = {"title": "Developer", "description": "En az 5 yıl deneyim gereklidir"}
    _, details = scoring.score_job(job)
    assert details["experience"] < 0


def test_should_include_threshold():
    scoring = load_scoring_system()
    job = {"title": "Intern Developer", "description": "0 yıl deneyim"}
    total, _ = scoring.score_job(job)
    assert scoring.should_include(total)


def test_compare_filters_basic():
    jobs = [
        {"title": "Senior Developer", "description": "5 yıl deneyim"},
        {"title": "Junior Developer", "description": "0 yıl deneyim"},
    ]
    scoring = load_scoring_system()
    result = compare_filters(jobs, scoring)
    assert "Junior Developer" in result["intersection"]
    assert "Senior Developer" not in result["intersection"]


def test_scoring_performance():
    scoring = load_scoring_system()
    jobs = [{"title": "Junior Developer", "description": ""} for _ in range(1000)]
    start = time.time()
    score_jobs(jobs, scoring)
    assert (time.time() - start) < 1.0


def test_filter_empty_list():
    assert filter_junior_suitable_jobs([]) == []
