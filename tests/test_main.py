"""Tests for main.py functionality."""

# Standard Library
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Test modüllerini import etmek için sys.path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_setup_logging():
    """Test logging setup function."""
    from main import setup_logging

    logger = setup_logging()
    assert logger is not None
    assert logger.level <= 20  # INFO or DEBUG level


def test_validate_skill_metadata():
    """Test skill metadata validation."""
    from main import _validate_skill_metadata

    # Valid metadata
    skills = ["python", "sql"]
    importance = [0.9, 0.8]
    assert _validate_skill_metadata(skills, importance) is True

    # Invalid - wrong types
    assert _validate_skill_metadata("not_list", importance) is False
    assert _validate_skill_metadata(skills, "not_list") is False

    # Invalid - length mismatch
    assert _validate_skill_metadata(skills, [0.9]) is False

    # Invalid - wrong element types
    assert _validate_skill_metadata([1, 2], importance) is False
    assert _validate_skill_metadata(skills, ["high", "low"]) is False


@patch("main.CVAnalyzer")
def test_setup_ai_metadata_and_personas(mock_analyzer_class):
    """Test AI metadata and personas setup."""
    from main import _setup_ai_metadata_and_personas, config

    # Mock analyzer
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer
    mock_analyzer.extract_metadata_from_cv.return_value = {
        "target_job_titles": ["Business Analyst", "Data Analyst"],
        "key_skills": ["python", "sql"],
    }

    # Mock config
    with (
        patch.dict(config, {"paths": {"cv_file": "test_cv.txt"}}),
        patch("pathlib.Path.read_text", return_value="test cv content"),
    ):
        ai_metadata, personas_cfg = _setup_ai_metadata_and_personas()

    assert "target_job_titles" in ai_metadata
    assert "Business_Analyst" in personas_cfg
    assert "Data_Analyst" in personas_cfg


def test_apply_skill_weights():
    """Test skill weight application."""
    from main import _apply_skill_weights, config

    # Initialize empty config
    if "scoring_system" not in config:
        config["scoring_system"] = {"description_weights": {"positive": {}}}

    # Test core skill (importance >= 0.85)
    _apply_skill_weights("python", 0.9, 10)
    assert config["scoring_system"]["description_weights"]["positive"]["python"] == 15

    # Test secondary skill (importance >= 0.7)
    _apply_skill_weights("sql", 0.8, 10)
    assert config["scoring_system"]["description_weights"]["positive"]["sql"] == 10

    # Test familiar skill (importance < 0.7)
    _apply_skill_weights("excel", 0.5, 10)
    assert config["scoring_system"]["description_weights"]["positive"]["excel"] == 6


@patch("main.IntelligentScoringSystem")
def test_configure_scoring_system_with_ai_metadata(mock_scoring_class):
    """Test scoring system configuration with AI metadata."""
    from main import _configure_scoring_system, config

    # Setup config
    config["scoring_system"] = {"dynamic_skill_weight": 10, "description_weights": {"positive": {}}}

    ai_metadata = {"key_skills": ["python", "sql"], "skill_importance": [0.9, 0.8]}

    result = _configure_scoring_system(ai_metadata)
    assert result is True
    mock_scoring_class.assert_called_once_with(config)


@patch("main.IntelligentScoringSystem")
def test_configure_scoring_system_without_ai_metadata(mock_scoring_class):
    """Test scoring system configuration without AI metadata."""
    from main import _configure_scoring_system

    ai_metadata = {}

    result = _configure_scoring_system(ai_metadata)
    assert result is True
    mock_scoring_class.assert_called_once()


@patch("main.IntelligentScoringSystem")
def test_configure_scoring_system_invalid_metadata(mock_scoring_class):
    """Test scoring system configuration with invalid AI metadata."""
    from main import _configure_scoring_system, config

    # Setup config
    config["scoring_system"] = {"dynamic_skill_weight": 10, "description_weights": {"positive": {}}}

    # Invalid metadata - mismatched arrays
    ai_metadata = {
        "key_skills": ["python", "sql"],
        "skill_importance": [0.9],  # Length mismatch
    }

    result = _configure_scoring_system(ai_metadata)
    assert result is True  # Should fallback to static scoring
    mock_scoring_class.assert_called_once_with(config)


def test_load_config():
    """Test configuration loading."""
    from main import load_config

    # Should load without errors
    config = load_config()
    assert isinstance(config, dict)
    assert "scoring_system" in config
    assert "paths" in config


def test_datetime_timestamp():
    """Test datetime timestamp functionality."""
    from main import datetime

    # Test that datetime import works
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    assert len(timestamp) == 15  # YYYYMMDD_HHMMSS format
    assert "_" in timestamp


@patch("main.collect_job_data")
def test_collect_data_for_all_personas_mock(mock_collect):
    """Test data collection for all personas with proper mocking."""
    # Import pandas for DataFrame creation
    import pandas as pd

    from main import collect_data_for_all_personas

    # Mock successful collection with DataFrame
    mock_df = pd.DataFrame({"title": ["Developer"], "company": ["Test Corp"]})
    mock_collect.return_value = mock_df

    personas = ["Business_Analyst"]
    personas_cfg = {"Business_Analyst": {"term": "Business Analyst", "hours_old": 72, "results": 25}}

    # This should return a CSV path if successful
    result = collect_data_for_all_personas(personas, 25, personas_cfg)

    # Result should be None or a valid CSV path
    if result is not None:
        assert result.endswith(".csv")
