from __future__ import annotations

from pathlib import Path


def load_prompt(file_path: str | Path) -> str:
    """Return the prompt text from the given file."""
    path = Path(file_path)
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        logger.error("Prompt file not found: %s", path, exc_info=True)
        raise
