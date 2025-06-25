from __future__ import annotations

"""Utilities for building persona configs dynamically."""

ROLE_RESULTS = {
    "developer": 30,
    "analyst": 25,
}

DEFAULT_RESULTS = 20


def build_dynamic_personas(target_job_titles: list[str]) -> dict[str, dict[str, object]]:
    """Convert job titles into persona search configs with dynamic results."""
    personas: dict[str, dict[str, object]] = {}
    for title in target_job_titles or []:
        key = title.strip().replace(" ", "_")
        term = f'("{title}" OR "{title}") -Senior -Lead'
        role_lower = title.lower()
        results = DEFAULT_RESULTS
        for role, count in ROLE_RESULTS.items():
            if role in role_lower:
                results = count
                break
        personas[key] = {"term": term, "hours_old": 72, "results": results}
    return personas
