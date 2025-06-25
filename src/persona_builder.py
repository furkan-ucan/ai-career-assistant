from __future__ import annotations

"""Utilities for building persona configs dynamically."""

ROLE_RESULTS = {
    "developer": 30,
    "analyst": 25,
}

DEFAULT_RESULTS = 20


def build_dynamic_personas(target_job_titles: list[str]) -> dict[str, dict[str, object]]:
    """
    Generate persona configuration dictionaries from a list of job titles, assigning dynamic result counts based on role keywords.
    
    For each job title, creates a unique key and a search term, and determines the number of results using predefined role mappings or a default value.
    
    Parameters:
        target_job_titles (list[str]): List of job title strings to generate persona configurations for.
    
    Returns:
        dict[str, dict[str, object]]: Dictionary mapping persona keys to their configuration dictionaries, each containing "term", "hours_old", and "results".
    """
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
