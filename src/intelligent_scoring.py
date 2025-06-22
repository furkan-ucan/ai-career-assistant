"""Intelligent scoring system for job filtering."""

from __future__ import annotations

# Standard Library
import logging
import re
from typing import Dict, List, Tuple


def _create_regex_pattern(keyword: str) -> re.Pattern:
    """Return compiled regex pattern with word boundaries.

    Spaces or hyphens in the keyword are treated interchangeably.
    """
    escaped = re.escape(keyword.strip())
    escaped = escaped.replace(r"\ ", r"(?:\s|-)" ).replace(r"\-", r"(?:\s|-)")
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def _compile_patterns_from_config(items: List[str]) -> List[re.Pattern]:
    """Compile a list of keywords (comma separated allowed) into regex patterns."""
    patterns = []
    for item in items or []:
        for part in str(item).split(','):
            part = part.strip()
            if part:
                patterns.append(_create_regex_pattern(part))
    return patterns

logger = logging.getLogger(__name__)


class IntelligentScoringSystem:
    """Weighted scoring and regex-based experience detection."""

    def __init__(self, config: Dict):
        scoring_cfg = config.get("scoring_system", {})

        weight_cfg = scoring_cfg.get("weights", {})
        self.weights = {
            "negative": weight_cfg.get("negative", -30),
            "positive": weight_cfg.get("positive", 30),
        }
        self.threshold = scoring_cfg.get("threshold", 0)

        title_cfg = scoring_cfg.get("title_keywords", {})
        desc_cfg = scoring_cfg.get("description_keywords", {})
        exp_cfg = scoring_cfg.get("experience_keywords", {})
        cv_cfg = scoring_cfg.get("cv_skill_keywords", {})

        self.title_patterns = {
            "negative": _compile_patterns_from_config(title_cfg.get("negative", [])),
            "positive": _compile_patterns_from_config(title_cfg.get("positive", [])),
        }
        self.description_patterns = {
            "negative": _compile_patterns_from_config(desc_cfg.get("negative", [])),
            "positive": _compile_patterns_from_config(desc_cfg.get("positive", [])),
        }
        self.experience_patterns = _compile_patterns_from_config(exp_cfg)
        self.cv_skill_patterns = _compile_patterns_from_config(cv_cfg)

        # Supported variations: "3 yıl", "4 sene", "2 yr", "5 yrs", "1 year", "7 years"
        self.experience_pattern = re.compile(
            r"(\d+)\s*(y[ıi]l|sene|yrs?|years?)",
            re.IGNORECASE,
        )

    def score_title(self, title: str) -> int:
        score = 0
        for pattern in self.title_patterns.get("negative", []):
            if pattern.search(title):
                score += self.weights["negative"]
        for pattern in self.title_patterns.get("positive", []):
            if pattern.search(title):
                score += self.weights["positive"]
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
