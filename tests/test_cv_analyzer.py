import hashlib
from typing import List

from src.cv_analyzer import CVAnalyzer


def test_cache_key_generation():
    analyzer = CVAnalyzer()
    text = "example cv"
    key = analyzer._get_cache_key(text)
    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    assert key == expected


def test_normalize_skills_blacklist():
    analyzer = CVAnalyzer()
    skills: List[str] = ["Python", "MS Office", "react-js", "python"]
    normalized = analyzer._normalize_skills(skills)
    assert "python" in normalized
    assert "reactjs" in normalized
    assert "msoffice" not in normalized
    assert normalized.count("python") == 1


def test_fail_safe(monkeypatch):
    analyzer = CVAnalyzer()

    def fake_call(_):
        return None

    monkeypatch.setattr(analyzer, "_call_gemini_api", fake_call)
    result = analyzer.extract_metadata_from_cv("cv text")
    assert result == {"key_skills": [], "target_job_titles": []}
