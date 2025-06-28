from unittest.mock import patch

from src.cv_analyzer import CVAnalyzer


def test_fail_safe(monkeypatch):
    """Test that when API fails, we get empty metadata"""
    analyzer = CVAnalyzer()

    def fake_call(cv_text: str):
        return None

    def mock_load_cached(cv_text: str):
        return None  # Cache'i devre dışı bırak

    monkeypatch.setattr(analyzer, "_call_gemini_api", fake_call)
    monkeypatch.setattr(analyzer, "_load_cached_metadata", mock_load_cached)
    result = analyzer.extract_metadata_from_cv("cv text")
    assert result == {"key_skills": [], "target_job_titles": [], "skill_importance": [], "cv_summary": ""}


def test_cv_summary_present(monkeypatch):
    """Test that CV summary is present in successful API response"""
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


def test_cache_key_generation():
    """Test cache functionality through public API"""
    analyzer = CVAnalyzer()
    cv_text = "Sample CV content"

    with patch("src.cv_analyzer.genai.GenerativeModel") as mock_model:
        mock_model.return_value.generate_content.return_value.text = (
            '{"key_skills": ["python"], "target_job_titles": ["dev"], "skill_importance": [0.9], "cv_summary": "test"}'
        )

        # First call should hit API
        result1 = analyzer.extract_metadata_from_cv(cv_text)
        # Second call should use cache (verify by checking API call count)
        result2 = analyzer.extract_metadata_from_cv(cv_text)

        assert result1 == result2
        assert mock_model.return_value.generate_content.call_count == 1


def test_normalize_skills_integration():
    """Test skill normalization through public API"""
    analyzer = CVAnalyzer()

    with patch("src.cv_analyzer.genai.GenerativeModel") as mock_model:
        mock_model.return_value.generate_content.return_value.text = """
        {
            "key_skills": ["Python", "MS Office", "EXCEL", "javascript"],
            "target_job_titles": ["Developer"],
            "skill_importance": [0.9, 0.8, 0.7, 0.6],
            "cv_summary": "Developer with skills"
        }
        """

        result = analyzer.extract_metadata_from_cv("test cv")
        skills = result["key_skills"]

        # Ensure skills is a list before assertions
        assert isinstance(skills, list)

        # Verify normalization: blacklisted skills removed, case normalized
        assert "python" in skills
        assert "javascript" in skills
        assert "ms office" not in skills

        assert "excel" not in skills  # Can't test private method directly, just ensure analyzer works
