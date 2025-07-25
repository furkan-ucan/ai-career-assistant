from __future__ import annotations

from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)


def load_prompt(file_path: str | Path) -> str:
    """Return the prompt text from the given file."""
    path = Path(file_path)
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, IsADirectoryError, UnicodeDecodeError):
        logger.exception("Error reading prompt file: %s", path)
        raise
