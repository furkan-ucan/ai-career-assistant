"""Simplified IntelligentScoringSystem for legacy tests relying on pattern scoring."""

from __future__ import annotations

import re
from typing import Any


class IntelligentScoringSystem:
    def __init__(self, config: dict[str, Any]):  # config.yaml aware
        scoring_cfg = config.get("scoring_system", {})
        self.threshold = scoring_cfg.get("threshold", -20)
        weights = scoring_cfg.get("weights", {})
        self.positive_w = weights.get("positive", 30)
        self.negative_w = weights.get("negative", -30)
        self.experience_penalties = {int(k): v for k, v in scoring_cfg.get("experience_penalties", {}).items()}

        title_cfg = scoring_cfg.get("title_keywords", {})
        self.neg_title_pattern = self._compile_group(title_cfg.get("negative", []))
        self.pos_title_pattern = self._compile_group(title_cfg.get("positive", []))

        desc_cfg = scoring_cfg.get("description_weights", {})
        self.desc_positive_patterns = self._compile_weighted(desc_cfg.get("positive", {}))
        self.desc_negative_patterns = self._compile_weighted(desc_cfg.get("negative", {}))

    def _compile_group(self, words):
        if not words:
            return re.compile(r"a^")
        escaped = [re.escape(w) for w in words]
        return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)

    def _compile_weighted(self, mapping: dict[str, int]):
        compiled = []
        for group, weight in mapping.items():
            parts = [re.escape(p.strip()) for p in group.split(",") if p.strip()]
            if not parts:
                continue
            compiled.append((re.compile(r"\b(" + "|".join(parts) + r")\b", re.IGNORECASE), int(weight)))
        return compiled

    def score_job(self, job: dict[str, Any]) -> tuple[int, dict[str, int]]:
        title = (job.get("title") or "").lower()
        desc = (job.get("description") or "")[:3000].lower()
        total = 0
        details = {"title": 0, "description": 0, "experience": 0}

        if self.pos_title_pattern.search(title):
            details["title"] += self.positive_w
        if self.neg_title_pattern.search(title):
            details["title"] += self.negative_w

        for pat, w in self.desc_positive_patterns:
            if pat.search(desc):
                details["description"] += int(w)
        for pat, w in self.desc_negative_patterns:
            if pat.search(desc):
                details["description"] += int(w)

        years = [int(y) for y in re.findall(r"(\d{1,2})\s*(yıl|yil|year|years|sene|yr|yrs)", desc)]
        if years:
            max_years = max(years)
            penalty_keys = sorted(self.experience_penalties.keys())
            applied = 0
            for k in penalty_keys:
                if max_years >= k:
                    applied = self.experience_penalties[k]
            details["experience"] = applied

        total = details["title"] + details["description"] + details["experience"]
        return total, details

    def should_include(self, score: int | float) -> bool:
        return bool(score >= self.threshold)
