from __future__ import annotations

import re
from typing import Final

"""Utilities for building persona configs dynamically."""

ROLE_RESULTS: Final[dict[str, int]] = {
    "developer": 30,
    "analyst": 25,
}

DEFAULT_RESULTS: Final[int] = 20
DEFAULT_HOURS_OLD: Final[int] = 72


def build_dynamic_personas(target_job_titles: list[str]) -> dict[str, dict[str, object]]:
    """
    Generate persona configuration dictionaries from a list of job titles, assigning dynamic result counts based on role keywords.

    For each job title, creates a unique key and a search term, and determines the number of results using predefined role mappings or a default value.

    Parameters:
        target_job_titles (list[str]): List of job title strings to generate persona configurations for.

    Returns:
        dict[str, dict[str, object]]: Dictionary mapping persona keys to their configuration dictionaries, each containing "term", "hours_old", and "results".

    Raises:
        TypeError: If target_job_titles is not a list or contains non-string elements.
    """
    if not isinstance(target_job_titles, list):
        raise TypeError("target_job_titles must be a list")

    personas: dict[str, dict[str, object]] = {}
    for title in target_job_titles or []:
        if not isinstance(title, str):
            raise TypeError(f"All job titles must be strings, got {type(title)}")

        # Skip empty or whitespace-only titles
        if not title.strip():
            continue

        # Normalize key to prevent collisions
        key = re.sub(r"[^\w\s]", "", title.strip().lower())  # Remove special chars first
        key = re.sub(r"\s+", "_", key)  # Then replace spaces with underscores

        # Handle potential key collisions
        original_key = key
        counter = 1
        while key in personas:
            key = f"{original_key}_{counter}"
            counter += 1

        # Escape quotes in title for safe query construction
        safe_title = title.replace('"', '\\"')
        term = f'("{safe_title}" OR "{safe_title}") -Senior -Lead'
        role_lower = title.lower()
        results = DEFAULT_RESULTS
        for role, count in ROLE_RESULTS.items():
            if role in role_lower:
                results = count
                break

        personas[key] = {"term": term, "hours_old": DEFAULT_HOURS_OLD, "results": results}

    return personas
