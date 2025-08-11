"""Legacy filter utilities required by tests (simplified)."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

NEGATIVE_EXPERIENCE_PATTERN = re.compile(
    r"(\b(5|6|7|8|9|1[0-9])\+?\s*(yıl|yil|year|years|sene|yr|yrs)\b)", re.IGNORECASE
)
SENIOR_TITLE_PATTERN = re.compile(r"\b(senior|lead|manager|architect|director|principal)\b", re.IGNORECASE)
JUNIOR_TITLE_PATTERN = re.compile(r"\b(junior|entry|trainee|intern|stajyer)\b", re.IGNORECASE)


def filter_junior_suitable_jobs(jobs: Iterable[dict[str, Any]]):
    result: list[dict[str, Any]] = []
    for job in jobs:
        title = (job.get("title") or "").lower()
        desc = (job.get("description") or "").lower()
        if SENIOR_TITLE_PATTERN.search(title):
            continue
        if NEGATIVE_EXPERIENCE_PATTERN.search(desc):
            continue
        result.append(job)
    return result


def compare_filters(jobs: list[dict[str, Any]], scoring_system: Any):  # minimal contract
    junior_set = {j.get("title") for j in filter_junior_suitable_jobs(jobs)}
    included = []
    for j in jobs:
        score, details = scoring_system.score_job(j)  # type: ignore[attr-defined]
        if scoring_system.should_include(score):  # type: ignore[attr-defined]
            included.append(j.get("title"))
    return {"intersection": [t for t in included if t in junior_set]}


def score_jobs(jobs: list[dict[str, Any]], scoring_system: Any):  # perf-oriented
    scored = []
    for j in jobs:
        total, details = scoring_system.score_job(j)  # type: ignore[attr-defined]
        if scoring_system.should_include(total):  # type: ignore[attr-defined]
            j["score_details"] = details
            scored.append(j)
    return scored
