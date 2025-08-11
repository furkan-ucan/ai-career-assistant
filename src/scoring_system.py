# src/scoring_system.py
"""Dynamic, AI-driven scoring system.

This module creates a scoring system dynamically based on the skills and
importance levels extracted from the user's CV by the CVAnalyzer.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=512)  # Increased cache size for more dynamic keywords
def _create_regex_pattern(keyword: str) -> re.Pattern:
    """Return a compiled, cached regex pattern with word boundaries."""
    if not keyword or len(keyword) < 2:
        return re.compile("a^")  # Regex that never matches
    escaped = re.escape(keyword.strip()).replace(r"\ ", r"(?:\s|-)").replace(r"\-", r"(?:\s|-)")
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


class ScoringSystem:
    """A scoring system built dynamically from AI-extracted CV metadata."""

    def __init__(self, config: dict[str, Any], ai_metadata: dict[str, Any]):
        """
        Initialize the scoring system with dynamic skills from AI metadata.

        Args:
            config: The main application configuration.
            ai_metadata: The metadata extracted from the user's CV.
        """
        scoring_cfg = config.get("scoring_system", {})
        self.threshold = scoring_cfg.get("threshold", 60.0)
        self.weights = {
            "similarity_score": scoring_cfg.get("similarity_weight", 0.6),
            "dynamic_keyword_score": scoring_cfg.get("dynamic_keyword_weight", 0.4),
            "base_keyword_weight": scoring_cfg.get("dynamic_skill_base_weight", 25),
        }

        # --- Build Dynamic Scoring Rules from AI Metadata ---
        self.dynamic_keyword_weights: list[tuple[re.Pattern, int]] = []
        key_skills = ai_metadata.get("key_skills", [])
        skill_importance = ai_metadata.get("skill_importance", [])

        if len(key_skills) != len(skill_importance):
            logger.warning("Mismatch between key_skills and skill_importance lengths. Using default importance.")
            skill_importance = [0.8] * len(key_skills)

        for skill, importance in zip(key_skills, skill_importance, strict=False):
            weight = int(self.weights["base_keyword_weight"] * float(importance))
            self.dynamic_keyword_weights.append((_create_regex_pattern(skill), weight))

        logger.info(f"✅ ScoringSystem initialized with {len(self.dynamic_keyword_weights)} dynamic skills from CV.")

    def score_job(self, job_data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """Calculate a blended score based on dynamic keywords and similarity."""
        title = job_data.get("title", "")
        description = job_data.get("description", "")
        similarity_score = float(job_data.get("similarity_score", 0.0))

        # 1. Calculate Dynamic Keyword Score
        keyword_score = 0
        matched_skills = []
        for pattern, weight in self.dynamic_keyword_weights:
            if pattern.search(title) or pattern.search(description):
                keyword_score += weight
                # Extract the original keyword from the pattern for clean logging
                clean_pattern = pattern.pattern.replace("\\b", "").replace("(?:\\s|-)", " ")
                matched_skills.append(clean_pattern)

        # Normalize keyword score to a 0-100 scale
        total_possible_weight = sum(w for _, w in self.dynamic_keyword_weights)
        normalized_keyword_score = (keyword_score / total_possible_weight) * 100 if total_possible_weight > 0 else 0

        # 2. Blended Score Calculation
        final_score = (normalized_keyword_score * self.weights["dynamic_keyword_score"]) + (
            similarity_score * self.weights["similarity_score"]
        )

        details: dict[str, Any] = {
            "matched_skills": matched_skills,
            "keyword_score_raw": keyword_score,
            "keyword_score_normalized": round(normalized_keyword_score, 2),
            "similarity_score": round(similarity_score, 2),
            "final_blended_score": round(final_score, 2),
        }
        return final_score, details

    def should_include(self, score: float) -> bool:
        """Determine if a job should be included based on its final score."""
        return bool(float(score) >= self.threshold)


def score_and_filter_jobs(jobs_list: list[dict], scoring_system: ScoringSystem) -> list[dict]:
    """Apply the dynamic scoring system to a list of jobs and return filtered results."""
    if not jobs_list:
        return []

    scored_jobs = []
    for job in jobs_list:
        total_score, details = scoring_system.score_job(job)
        if scoring_system.should_include(total_score):
            job["score"] = total_score
            job["score_details"] = details
            scored_jobs.append(job)
        else:
            logger.debug(f"Job filtered out (score={total_score:.2f}): {job.get('title')}")

    scored_jobs.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return scored_jobs
