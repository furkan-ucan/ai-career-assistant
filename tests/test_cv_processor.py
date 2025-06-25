"""Test for CV Processor module."""

# Standard Library
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Local
from src.cv_processor import CVProcessor


def test_cv_processor_initialization():
    """Test CVProcessor initialization."""
    processor = CVProcessor()
    assert processor.cv_path == Path("data") / "cv.txt"
    assert processor.cv_text is None
    assert processor.cv_embedding is None


def test_cv_processor_custom_path():
    """Test CVProcessor with custom CV path."""
    custom_path = "custom/cv.txt"
    processor = CVProcessor(cv_path=custom_path)
    assert processor.cv_path == Path(custom_path)


def test_cv_processor_custom_embedding_settings():
    """Test CVProcessor with custom embedding settings."""
    settings = {"model": "custom-model"}

    with patch("src.cv_processor.EmbeddingService") as mock_embedding:
        CVProcessor(embedding_settings=settings)
        mock_embedding.assert_called_once_with(**settings)


def test_load_cv_file_exists():
    """Test loading CV when file exists."""
    mock_content = "Test CV content\nPython developer"

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=mock_content)),
    ):
        processor = CVProcessor()
        result = processor.load_cv()
        assert result is True
        assert processor.cv_text == mock_content


def test_load_cv_file_not_exists():
    """Test loading CV when file doesn't exist."""
    with patch("pathlib.Path.exists", return_value=False):
        processor = CVProcessor()
        result = processor.load_cv()
        assert result is False


def test_load_cv_read_error():
    """Test handling of file read errors."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", side_effect=FileNotFoundError),
    ):
        processor = CVProcessor()
        result = processor.load_cv()
        assert result is False


def test_create_cv_embedding():
    """Test CV embedding creation."""
    processor = CVProcessor()
    processor.cv_text = "Test CV content"

    mock_embedding = [0.1, 0.2, 0.3]
    processor.embedding_service = MagicMock()
    processor.embedding_service.create_embedding.return_value = mock_embedding

    result = processor.create_cv_embedding()
    assert result is True
    assert processor.cv_embedding == mock_embedding


def test_get_cv_text():
    """Test getting CV text."""
    processor = CVProcessor()
    processor.cv_text = "Test CV content"
    assert processor.get_cv_text() == "Test CV content"


def test_get_cv_embedding():
    """Test getting CV embedding."""
    processor = CVProcessor()
    test_embedding = [0.1, 0.2, 0.3]
    processor.cv_embedding = test_embedding
    assert processor.get_cv_embedding() == test_embedding


def test_get_cv_summary():
    """Test getting CV summary."""
    processor = CVProcessor()
    processor.cv_text = "Test content"
    processor.cv_embedding = [0.1, 0.2]

    summary = processor.get_cv_summary()
    assert summary["character_count"] == 12
    assert summary["word_count"] == 2
    assert summary["has_embedding"] is True
    assert summary["embedding_dimensions"] == 2
