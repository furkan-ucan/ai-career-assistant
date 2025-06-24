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
    escaped = escaped.replace(r"\ ", r"(?:\s|-)").replace(r"\-", r"(?:\s|-)")
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def _compile_patterns_from_config(items: List[str]) -> List[re.Pattern]:
    """Compile a list of keywords (comma separated allowed) into regex patterns."""
    patterns = []
    for item in items or []:
        for part in str(item).split(","):
            part = part.strip()
            if part:
                patterns.append(_create_regex_pattern(part))
    return patterns


def _compile_weighted_patterns(items: Dict[str, int]) -> List[Tuple[re.Pattern, int]]:
    """Compile mapping of comma-separated keywords to weighted regex patterns."""
    patterns = []
    for key, weight in (items or {}).items():
        for part in str(key).split(","):
            part = part.strip()
            if part:
                patterns.append((_create_regex_pattern(part), int(weight)))
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
        desc_weights_cfg = scoring_cfg.get("description_weights", {})
        exp_penalty_cfg = scoring_cfg.get("experience_penalties", {"5": -40, "4": -20})
        cv_cfg = scoring_cfg.get("cv_skill_keywords", {})

        self.title_patterns = {
            "negative": _compile_patterns_from_config(title_cfg.get("negative", [])),
            "positive": _compile_patterns_from_config(title_cfg.get("positive", [])),
        }
        self.description_weights = {
            "negative": _compile_weighted_patterns(
                desc_weights_cfg.get("negative", {})
            ),
            "positive": _compile_weighted_patterns(
                desc_weights_cfg.get("positive", {})
            ),
        }
        self.experience_penalties = {int(k): int(v) for k, v in exp_penalty_cfg.items()}
        self.cv_skill_patterns = _compile_patterns_from_config(cv_cfg)
        # Supported variations: "3 yıl", "4 sene", "2 yr", "5 yrs", "1 year", "7 years", "10+ years"
        self.experience_pattern = re.compile(
            r"(\d+)\+?\s*(y[ıi]l|sene|yrs?|years?)",
            re.IGNORECASE,
        )

    def score_title(self, title: str) -> int:
        if not title:  # Handle None, empty string, etc.
            return 0
        score = 0
        for pattern in self.title_patterns.get("negative", []):
            if pattern.search(title):
                score += self.weights["negative"]
        for pattern in self.title_patterns.get("positive", []):
            if pattern.search(title):
                score += self.weights["positive"]
                logger.debug("Title score %s for '%s'", score, title)
        return score

    def score_description(self, description: str) -> int:
        """Score job description based on weighted keyword matches."""
        if not description:  # Handle None, empty string, etc.
            return 0
        text = description[:3000]
        score = 0
        for pattern, weight in self.description_weights.get("positive", []):
            if pattern.search(text):
                score += weight
        for pattern, weight in self.description_weights.get("negative", []):
            if pattern.search(text):
                score += weight
        logger.debug("Description score %s", score)
        return score

    def score_experience(self, text: str) -> int:
        """Detect experience years and apply configured penalties."""
        if not text:  # Handle None, empty string, etc.
            return 0
        matches = self.experience_pattern.findall(text.lower())
        if not matches:
            logger.debug("No experience information found")
            return 0
        years = max(int(m[0]) for m in matches)
        for threshold, penalty in sorted(
            self.experience_penalties.items(), reverse=True
        ):
            if years >= threshold:
                logger.debug("Experience %s years -> %s", years, penalty)
                return penalty
        logger.debug("Experience %s years -> 0", years)
        return 0

    def score_job(self, job_data: Dict[str, str]) -> Tuple[int, Dict[str, int]]:
        title = job_data.get("title", "")
        desc = job_data.get("description", "")
        title_score = self.score_title(title)
        desc_score = self.score_description(desc)
        exp_score = self.score_experience(desc)
        total = title_score + desc_score + exp_score
        details = {
            "title": title_score,
            "description": desc_score,
            "experience": exp_score,
            "total": total,
        }
        logger.debug("Job '%s' scored %s", title, details)
        return total, details

    def should_include(self, score: float) -> bool:
        include = score >= self.threshold
        logger.debug("Include decision %s for score %s", include, score)
        return bool(include)
