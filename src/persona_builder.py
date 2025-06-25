from __future__ import annotations

"""Utilities for building persona configs dynamically."""


def build_dynamic_personas(target_job_titles: list[str]) -> dict[str, dict[str, object]]:
    """Convert job titles into persona search configs."""
    personas: dict[str, dict[str, object]] = {}
    for title in target_job_titles or []:
        key = title.strip().replace(" ", "_")
        term = f'("{title}" OR "{title}") -Senior -Lead'
        personas[key] = {"term": term, "hours_old": 72, "results": 25}
    return personas
