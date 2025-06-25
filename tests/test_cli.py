"""Test for CLI module."""

# Standard Library
from unittest.mock import mock_open, patch

# Third Party
# Local
from src.cli import build_parser, load_persona_choices, parse_args


def test_load_persona_choices():
    """Test loading persona choices from config."""
    mock_yaml_data = {"persona_search_configs": {"dev": {}, "analyst": {}}}

    with patch("builtins.open", mock_open()), patch("yaml.safe_load") as mock_yaml:
        mock_yaml.return_value = mock_yaml_data
        choices = load_persona_choices()
        assert "dev" in choices
        assert "analyst" in choices


def test_load_persona_choices_empty_on_error():
    """Test that empty list is returned on file error."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        choices = load_persona_choices()
        assert choices == []


def test_build_parser():
    """Test argument parser building."""
    personas = ["dev", "analyst"]
    parser = build_parser(personas)

    # Test parser structure
    assert parser.prog is not None
    assert parser.description is not None

    # Test with valid arguments
    args = parser.parse_args(["-p", "dev", "-r", "50", "-t", "80"])
    assert args.persona == ["dev"]
    assert args.results == 50
    assert args.threshold == 80


def test_build_parser_multiple_personas():
    """Test parser with multiple personas."""
    personas = ["dev", "analyst", "manager"]
    parser = build_parser(personas)

    args = parser.parse_args(["-p", "dev", "-p", "analyst"])
    assert args.persona == ["dev", "analyst"]


@patch("src.cli.load_persona_choices")
def test_parse_args(mock_load_personas):
    """Test parse_args function."""
    mock_load_personas.return_value = ["dev", "analyst"]

    with patch("sys.argv", ["cli.py", "-p", "dev"]):
        args = parse_args()
        assert args.persona == ["dev"]
