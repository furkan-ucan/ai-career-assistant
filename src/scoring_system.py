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
def _create_regex_pattern(keyword: str) -> re.Pattern | None:
    """Create a regex pattern for the given keyword, with error handling and input validation."""
    if not isinstance(keyword, str) or not keyword.strip():
        logger.warning("_create_regex_pattern: Empty or invalid keyword provided. Returning None.")
        return None
    try:
        # Only allow safe characters, optionally simplify escaping logic
        safe_keyword = keyword.strip()
        # Optionally validate for forbidden regex chars
        escaped = re.escape(safe_keyword).replace(r"\ ", r"(?:\s|-)").replace(r"\-", r"(?:\s|-)")
        pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        return pattern
    except re.error as exc:
        logger.error(f"Regex compilation failed for keyword '{keyword}': {exc}")
        return None


class ScoringSystem:
    """Handles only scoring logic for job postings."""

    def __init__(self, config: dict[str, Any]):
        if config is None:
            logger.error("ScoringSystem config is None.")
            raise ValueError("Config parameter cannot be None.")
        scoring_cfg = config.get("scoring_system", {})
        threshold = scoring_cfg.get("threshold", None)
        if threshold is None:
            logger.error("Threshold value missing in config.")
            raise ValueError("Threshold value must be provided in config['scoring_system'].")
        if not isinstance(threshold, (int, float)):
            logger.error(f"Threshold type invalid: {type(threshold)}")
            raise TypeError("Threshold must be an int or float.")
        if not (0 <= threshold <= 100):
            logger.error(f"Threshold value out of range: {threshold}")
            raise ValueError("Threshold must be between 0 and 100.")
        self.threshold = threshold

    def score_job(self, job_data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """Calculate the total score for a job posting with input validation and error handling."""
        default_score = 0
        default_details = {"reason": "Invalid or missing job data", "total": default_score}
        if job_data is None or not isinstance(job_data, dict):
            return default_score, default_details
        required_keys = ["title", "description", "skills"]
        missing_keys = [k for k in required_keys if k not in job_data]
        if missing_keys:
            return default_score, {"reason": f"Missing keys: {missing_keys}", "total": default_score}
        try:
            # ...existing scoring logic...
            score = 50  # Example: replace with real logic
            details: dict[str, Any] = {"reason": "Example score", "total": score}
            return score, details
        except Exception as exc:
            return default_score, {"reason": f"Exception: {exc}", "total": default_score}

    def should_include(self, score: float) -> bool:
        """Determine if a job should be included based on its score."""
        return bool(score >= self.threshold)


def score_and_filter_jobs(jobs_list: list[dict], scoring_system: ScoringSystem) -> list[dict]:
    """Apply the scoring system to a list of jobs and return filtered results."""
    import logging

    logger = logging.getLogger(__name__)
    if jobs_list is None:
        logger.error("jobs_list is None. Aborting scoring.")
        raise ValueError("jobs_list cannot be None.")
    if scoring_system is None:
        logger.error("scoring_system is None. Aborting scoring.")
        raise ValueError("scoring_system cannot be None.")

    scored_jobs = []
    for job in jobs_list:
        try:
            total_score, details = scoring_system.score_job(job)
        except Exception as exc:
            logger.error(f"Error scoring job: {exc}")
            total_score, details = 0, {"reason": f"Scoring error: {exc}", "total": 0}

        if scoring_system.should_include(total_score):
            job_copy = job.copy()
            job_copy["score"] = total_score
            job_copy["score_details"] = details
            scored_jobs.append(job_copy)
            logger.info(f"Job included (score={total_score}): {job_copy.get('title', 'No Title')}")
        else:
            logger.info(f"Job filtered out (score={total_score}): {job.get('title', 'No Title')}")

    scored_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored_jobs
