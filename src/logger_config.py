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


def setup_logging() -> logging.Logger:
    """Configure root logging with file and console handlers."""
    log_dir = Path("logs")
    try:
        log_dir.mkdir(exist_ok=True)
    except PermissionError as exc:
        # Fallback to console-only logging if directory creation fails
        print(f"Warning: Could not create log directory: {exc}")
        return _setup_console_only_logging()

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        file_handler = logging.FileHandler(log_dir / f"kariyer_asistani_{timestamp}.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        error_handler = logging.FileHandler(log_dir / f"errors_{timestamp}.log", encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
    except PermissionError as exc:
        # Fallback to console-only logging if file handlers fail
        root_logger.addHandler(console_handler)
        root_logger.warning("Could not create file handlers, using console only: %s", exc)

    return root_logger
