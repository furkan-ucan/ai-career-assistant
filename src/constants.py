# src/constants.py
"""
DEPRECATED: This file is being phased out in favor of src/core/constants.py

Legacy constants for backward compatibility.
New code should import from src.core.constants instead.
"""

from __future__ import annotations

from pathlib import Path

# Re-export core constants for backward compatibility

# Legacy constants that remain here
COSINE_METRIC = "cosine"
DEFAULT_COLLECTION_NAME = "job_embeddings"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
