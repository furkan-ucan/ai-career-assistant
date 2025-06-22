"""Intelligent scoring system for job filtering."""

from __future__ import annotations

# Standard Library
import logging
import re
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class IntelligentScoringSystem:
    """Weighted scoring and regex-based experience detection."""

    def __init__(self, config: Dict):
        scoring_cfg = config.get("scoring_system", {})
        self.weights = scoring_cfg.get("title_weights", {})
        self.threshold = scoring_cfg.get("threshold", 0)
        # compile patterns once
        # Supported variations: "3 yıl", "4 sene", "2 yr", "5 yrs", "1 year", "7 years"
        self.experience_pattern = re.compile(
            r"(\d+)\s*(y[ıi]l|sene|yrs?|years?)",
            re.IGNORECASE,
        )

    def score_title(self, title: str) -> int:
        score = 0
        lowered = title.lower()
        for word, weight in self.weights.get("negative", {}).items():
            if word in lowered:
                score += weight
        for word, weight in self.weights.get("positive", {}).items():
            if word in lowered:
                score += weight
        return score

    def score_experience(self, text: str) -> int:
        # Detect experience year count and penalize >4 years
        matches = self.experience_pattern.findall(text.lower())
        for match in matches:
            years = int(match[0])
            if years >= 5:
                return -40
            if years >= 4:
                return -20
        return 0

    def score_job(self, job_data: Dict[str, str]) -> Tuple[int, Dict[str, int]]:
        title = job_data.get("title", "")
        desc = job_data.get("description", "")
        title_score = self.score_title(title)
        exp_score = self.score_experience(desc)
        total = title_score + exp_score
        details = {"title": title_score, "experience": exp_score, "total": total}
        return total, details

    def should_include(self, score: int) -> bool:
        return score >= self.threshold
