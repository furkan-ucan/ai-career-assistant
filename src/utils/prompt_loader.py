from __future__ import annotations

from pathlib import Path


def load_prompt(file_path: str | Path) -> str:
    """Return the prompt text from the given file."""
    path = Path(file_path)
    return path.read_text(encoding="utf-8")
