from datetime import datetime

from src import logger_config


def test_setup_logging_creates_files(monkeypatch, tmp_path):
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)

    class DummyDateTime:
        @classmethod
        def now(cls):
            return fixed_time

    monkeypatch.setattr(logger_config, "datetime", DummyDateTime)

    def _path(path=""):
        return tmp_path / path

    monkeypatch.setattr(logger_config, "Path", _path)

    logger = logger_config.setup_logging()
    log_dir = tmp_path / "logs"
    log_files = list(log_dir.iterdir())
    assert any("kariyer_asistani" in f.name for f in log_files)
    assert any("errors" in f.name for f in log_files)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
