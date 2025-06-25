import hashlib

from src.cv_analyzer import CVAnalyzer


def test_cache_key_generation():
    analyzer = CVAnalyzer()
    text = "example cv"
    key = analyzer._get_cache_key(text)
    # Cache key now includes prompt version for invalidation
    expected = f"v1.1_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"
    assert key == expected


def test_normalize_skills_blacklist():
    analyzer = CVAnalyzer()
    skills: list[str] = ["Python", "MS Office", "react-js", "python", "msoffice"]
    normalized = analyzer._normalize_skills(skills)
    assert "python" in normalized
    assert "react-js" in normalized
    # MS Office should be blacklisted when normalized to "msoffice"
    assert "msoffice" not in normalized
    assert normalized.count("python") == 1


def test_fail_safe(monkeypatch):
    analyzer = CVAnalyzer()

    def fake_call(_):
        return None

    monkeypatch.setattr(analyzer, "_call_gemini_api", fake_call)
    result = analyzer.extract_metadata_from_cv("cv text")
    assert result == {"key_skills": [], "target_job_titles": [], "skill_importance": []}


def test_strip_markdown_fences():
    analyzer = CVAnalyzer()

    # Test markdown removal
    content_with_fences = '```json\n{"test": "data"}\n```'
    cleaned = analyzer._strip_markdown_fences(content_with_fences)
    assert cleaned == '{"test": "data"}'

    # Test without fences
    content_without_fences = '{"test": "data"}'
    cleaned = analyzer._strip_markdown_fences(content_without_fences)
    assert cleaned == '{"test": "data"}'


def test_clean_job_titles():
    analyzer = CVAnalyzer()

    titles = ["business analyst (junior)", "data_scientist", "full-stack developer"]
    cleaned = analyzer._clean_job_titles(titles)

    assert "Business Analyst" in cleaned
    assert "Data Scientist" in cleaned
    assert "Full-Stack Developer" in cleaned


def test_categorize_skills_by_importance():
    analyzer = CVAnalyzer()

    skills = ["python", "sql", "excel"]
    importance = [0.9, 0.8, 0.5]

    categorized = analyzer._categorize_skills_by_importance(skills, importance)

    assert "python" in categorized["core"]
    assert "sql" in categorized["secondary"]
    assert "excel" in categorized["familiar"]


def test_validate_skill_metadata_mismatch(monkeypatch):
    """Test handling of mismatched skill/importance arrays."""
    analyzer = CVAnalyzer()

    # Mock successful API call with mismatched arrays
    def mock_api_call(cv_text: str):
        return {
            "key_skills": ["python", "sql", "react"],
            "target_job_titles": ["Developer", "Analyst"],
            "skill_importance": [0.9, 0.8],  # Missing one importance score
        }

    monkeypatch.setattr(analyzer, "_call_gemini_api", mock_api_call)
    result = analyzer.extract_metadata_from_cv("test cv")

    # Should pad missing importance scores
    skills = result["key_skills"]
    importance = result["skill_importance"]
    assert isinstance(skills, list) and isinstance(importance, list)
    assert len(skills) == len(importance)
    # Check that the third skill has the default padded importance
    assert len(importance) == 3 and abs(importance[2] - 0.8) < 0.01
