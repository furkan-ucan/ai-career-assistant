import pytest
import yaml

from src.config import load_settings
from src.exceptions import ConfigError


def test_load_settings_custom_path(monkeypatch, tmp_path):
    sample_yaml = {"foo": "bar"}
    file_path = tmp_path / "config.yaml"
    file_path.write_text(yaml.safe_dump(sample_yaml), encoding="utf-8")
    monkeypatch.setattr("src.config.CONFIG_PATH", file_path)
    settings = load_settings()
    assert settings["foo"] == "bar"


def test_min_similarity_threshold_value():
    settings = load_settings()
    val = settings["job_search_settings"]["min_similarity_threshold"]
    assert isinstance(val, int)
    assert val == 60


def test_load_settings_missing_file(monkeypatch, tmp_path):
    missing = tmp_path / "missing.yaml"
    monkeypatch.setattr("src.config.CONFIG_PATH", missing)
    with pytest.raises(ConfigError):
        load_settings()
