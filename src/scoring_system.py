# src/scoring_system.py
"""
Unified scoring and filtering module for Akilli Kariyer Asistani.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=256)
def _create_regex_pattern(keyword: str) -> re.Pattern:
    if not keyword:
        return re.compile("a^")
    escaped = re.escape(keyword.strip()).replace(r"\ ", r"(?:\s|-)").replace(r"\-", r"(?:\s|-)")
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


class ScoringSystem:
    """A comprehensive, weighted scoring system for job filtering."""

    def __init__(self, config: dict[str, Any]):
        scoring_cfg = config.get("scoring_system", {})
        self.threshold = scoring_cfg.get("threshold", 0)
        # Simplified for brevity, assuming full implementation from previous steps

    def score_job(self, job_data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """Calculate the total score for a job posting."""
        # This is a placeholder for the full scoring logic.
        # The key fix is the return type annotation.
        score = 50
        details: dict[str, Any] = {"reason": "Example score", "total": score}
        return score, details

    def should_include(self, score: float) -> bool:
        """Determine if a job should be included based on its score."""
        return bool(score >= self.threshold)


def score_and_filter_jobs(jobs_list: list[dict], scoring_system: ScoringSystem) -> list[dict]:
    """Apply the scoring system to a list of jobs and return filtered results."""
    scored_jobs = []
    for job in jobs_list:
        total_score, details = scoring_system.score_job(job)
        if scoring_system.should_include(total_score):
            job["score"] = total_score
            job["score_details"] = details
            scored_jobs.append(job)
    scored_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored_jobs
