# src/models/pipeline_context.py
"""Dataclass to hold the state and services for the job analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pandas as pd

# Use forward-referencing with TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from src.cv_analyzer import CVAnalyzer
    from src.embedding_service import EmbeddingService

    # REMOVED: Manual scoring system for pure AI approach
    from src.vector_store import VectorStore


@dataclass
class PipelineContext:
    """A data carrier for the entire job analysis pipeline."""

    # --- Configuration & Arguments ---
    config: dict[str, Any]
    cli_args: Any

    # --- Core Data ---
    cv_text: str | None = None
    cv_embedding: list[float] | None = None
    ai_metadata: dict[str, Any] = field(default_factory=dict)
    personas_config: dict[str, Any] = field(default_factory=dict)

    # --- Pipeline Stages Data ---
    raw_jobs_df: pd.DataFrame | None = None
    scored_jobs: list[dict[str, Any]] = field(default_factory=list)
    final_results: list[dict[str, Any]] | None = None

    # --- Services (Injected) ---
    embedding_service: EmbeddingService | None = None
    cv_analyzer: CVAnalyzer | None = None
    vector_store: VectorStore | None = None
    # REMOVED: scoring_system for pure AI approach

    # --- Control Flags & Parameters ---
    threshold: float = 60.0
    rerank_flag: bool = True
    hours_old: int | None = None
