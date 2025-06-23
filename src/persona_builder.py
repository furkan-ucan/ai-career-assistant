"""Dynamic persona builder.

Convert job titles provided by AI into JobSpy-compatible search configurations."""

from __future__ import annotations

# Standard Library
import re
from typing import Dict, List

NEGATIVE_FILTERS = "-Senior -Lead -Manager -Director -Principal"


def build_dynamic_personas(
    job_titles: List[str], hours_old: int = 72, results: int = 25
) -> Dict[str, Dict[str, str | int]]:
    """Build search configs from job titles."""
    personas: Dict[str, Dict[str, str | int]] = {}
    for title in job_titles or []:
        cleaned = re.sub(r"\W+", "_", title).strip("_")
        term = f'("{title}") {NEGATIVE_FILTERS}'
        personas[cleaned] = {"term": term, "hours_old": hours_old, "results": results}
    return personas
