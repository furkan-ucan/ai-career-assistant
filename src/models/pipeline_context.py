from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from ..intelligent_scoring import IntelligentScoringSystem


@dataclass
class PipelineContext:
    """Data carrier for the job analysis pipeline."""

    config: dict[str, Any]
    cli_args: Any
    cv_text: str | None = None
    cv_embedding: list[float] | None = None
    ai_metadata: dict[str, Any] = field(default_factory=dict)
    personas_config: dict[str, Any] = field(default_factory=dict)
    threshold: float = 60.0
    rerank_flag: bool = True
    raw_jobs_df: pd.DataFrame | None = None
    vector_store_path: str | None = None
    initial_matches: list[dict[str, Any]] = field(default_factory=list)
    scored_jobs: list[dict[str, Any]] = field(default_factory=list)
    final_results: list[dict[str, Any]] = field(default_factory=list)
    scoring_system: IntelligentScoringSystem | None = None
    hours_old: int | None = None
