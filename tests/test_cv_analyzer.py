from pathlib import Path

from src.cv_analyzer import CVAnalyzer


def test_normalization_and_blacklist(tmp_path):
    analyzer = CVAnalyzer(cache_dir=tmp_path)
    skills = analyzer.normalize_skills(["Python", "MS Office", "react-js", "python"])
    assert "python" in skills
    assert "reactjs" in skills
    assert "msoffice" not in skills


def test_cache_write_and_read(tmp_path):
    analyzer = CVAnalyzer(cache_dir=tmp_path)
    text = "Python developer with SQL"
    data = {"key_skills": ["python", "sql"], "target_job_titles": ["Developer"]}
    analyzer.cache_metadata(text, data)
    loaded = analyzer.load_cached_metadata(text)
    assert loaded is not None
    assert loaded["metadata"] == data
    # ensure timestamp is present
    assert "generated_at" in loaded
