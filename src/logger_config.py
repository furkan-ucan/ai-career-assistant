from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path


def _setup_console_only_logging() -> logging.Logger:
    """Fallback to console-only logging if file handlers fail."""
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    return root_logger


def _create_log_directory(log_dir: Path) -> Path | None:
    """Create the log directory, handling PermissionError."""
    try:
        log_dir.mkdir(exist_ok=True)
        return log_dir
    except PermissionError as exc:
        logging.getLogger(__name__).error("Could not create log directory: %s", exc)
        return None


def _create_console_handler(formatter: logging.Formatter) -> logging.StreamHandler:
    """Create and configure a console handler."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    return console_handler


def _create_file_handler(
    log_dir: Path, timestamp: str, level: int, filename_prefix: str, formatter: logging.Formatter
) -> logging.FileHandler | None:
    """Create and configure a file handler, handling PermissionError."""
    try:
        file_handler = logging.FileHandler(log_dir / f"{filename_prefix}_{timestamp}.log", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        return file_handler
    except PermissionError as exc:
        logging.getLogger(__name__).warning("Could not create file handler '%s': %s", filename_prefix, exc)
        return None


def setup_logging() -> logging.Logger:
    """Configure root logging with file and console handlers."""
    log_dir = Path("logs")
    if not _create_log_directory(log_dir):
        return _setup_console_only_logging()

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    console_handler = _create_console_handler(formatter)
    root_logger.addHandler(console_handler)

    file_handler = _create_file_handler(log_dir, timestamp, logging.DEBUG, "kariyer_asistani", formatter)
    if file_handler:
        root_logger.addHandler(file_handler)

    error_handler = _create_file_handler(log_dir, timestamp, logging.ERROR, "errors", formatter)
    if error_handler:
        root_logger.addHandler(error_handler)

    if not file_handler and not error_handler:
        root_logger.addHandler(console_handler)
        root_logger.warning("No file handlers could be created, logging to console only.")

    return root_logger
