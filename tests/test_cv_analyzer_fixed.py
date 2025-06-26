import hashlib

from src.config import get_config
from src.cv_analyzer import CVAnalyzer


def test_cache_key_generation():
    analyzer = CVAnalyzer()
    cv_text = "Sample CV content"
    key = analyzer._get_cache_key(cv_text)
    config = get_config()
    prompt_version = config.get("cv_analyzer_settings", {}).get("prompt_version", "v1")
    content_hash = hashlib.sha256(cv_text.encode("utf-8")).hexdigest()[:16]
    expected = f"{prompt_version}_{content_hash}"
    assert key == expected


def test_normalize_skills_blacklist():
    analyzer = CVAnalyzer()
    skills = ["python", "java", "office", "word", "excel", "powerpoint", "outlook", "ms office"]
    normalized = analyzer._normalize_skills(skills)
    # office related skills should be filtered out
    assert "python" in normalized
    assert "java" in normalized
    assert "office" not in normalized
    assert "word" not in normalized
    assert "excel" not in normalized


def test_fail_safe(monkeypatch):
    analyzer = CVAnalyzer()

    def fake_call(cv_text: str):
        return None

    def mock_load_cached(cv_text: str):
        return None  # Cache'i devre dışı bırak

    monkeypatch.setattr(analyzer, "_call_gemini_api", fake_call)
    monkeypatch.setattr(analyzer, "_load_cached_metadata", mock_load_cached)
    result = analyzer.extract_metadata_from_cv("cv text")
    assert result == {"key_skills": [], "target_job_titles": [], "skill_importance": [], "cv_summary": ""}


def test_strip_markdown_fences():
    analyzer = CVAnalyzer()

    # Test markdown removal
    content_with_fences = """```json
    {"key": "value"}
    ```"""
    result = analyzer._strip_markdown_fences(content_with_fences)
    assert result == '{"key": "value"}'

    # Test content without fences (should remain unchanged)
    plain_content = '{"key": "value"}'
    result = analyzer._strip_markdown_fences(plain_content)
    assert result == '{"key": "value"}'


def test_clean_job_titles():
    analyzer = CVAnalyzer()
    titles = ["Software Engineer", "SENIOR DEVELOPER", "junior analyst", "  Data Scientist  "]
    cleaned = analyzer._clean_job_titles(titles)
    expected = ["Software Engineer", "Senior Developer", "Junior Analyst", "Data Scientist"]
    assert cleaned == expected


def test_categorize_skills_by_importance():
    analyzer = CVAnalyzer()
    skills = ["python", "java", "sql"]
    importance = [0.9, 0.7, 0.8]

    categorized_skills = analyzer._categorize_skills_by_importance(skills, importance)

    assert "python" in categorized_skills["core"]  # 0.9 > 0.8
    assert "sql" in categorized_skills["secondary"]  # 0.8 == 0.8
    assert "java" in categorized_skills["secondary"]  # 0.7 >= 0.7


def test_cv_summary_present(monkeypatch):
    analyzer = CVAnalyzer()

    def mock_api_call(cv_text: str):
        return {
            "key_skills": ["python"],
            "target_job_titles": ["Dev"],
            "skill_importance": [0.9],
            "cv_summary": "Skilled developer",
        }

    def mock_load_cached(cv_text: str):
        return None  # Cache'i devre dışı bırak

    monkeypatch.setattr(analyzer, "_call_gemini_api", mock_api_call)
    monkeypatch.setattr(analyzer, "_load_cached_metadata", mock_load_cached)
    result = analyzer.extract_metadata_from_cv("test cv")
    assert "cv_summary" in result
    assert isinstance(result["cv_summary"], str) and len(result["cv_summary"]) > 0
