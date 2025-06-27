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


def _validate_input(target_job_titles: list[str]) -> None:
    """Validate input parameters for build_dynamic_personas."""
    if not isinstance(target_job_titles, list):
        raise TypeError("target_job_titles must be a list")

    for title in target_job_titles:
        if not isinstance(title, str):
            raise TypeError(f"All job titles must be strings, got {type(title)}")


def _generate_unique_key(title: str, existing_keys: set[str]) -> str:
    """Generate a unique, normalized key for a persona from a job title."""
    # Normalize key to prevent collisions
    key = re.sub(r"[^\w\s]", "", title.strip().lower())  # Remove special chars first
    key = re.sub(r"\s+", "_", key)  # Then replace spaces with underscores

    # Handle potential key collisions
    original_key = key
    counter = 1
    while key in existing_keys:
        key = f"{original_key}_{counter}"
        counter += 1
    return key


def _build_search_term(title: str) -> str:
    """Build a search term from a job title, escaping quotes and adding exclusions."""
    # Escape quotes in title for safe query construction
    safe_title = title.replace('"', '\\"')
    return f'("{safe_title}" OR "{safe_title}") -Senior -Lead'


def _determine_result_count(title: str) -> int:
    """Determine the number of results based on role keywords in the job title."""
    role_lower = title.lower()
    for role, count in ROLE_RESULTS.items():
        if role in role_lower:
            return count
    return DEFAULT_RESULTS


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
    _validate_input(target_job_titles)

    personas: dict[str, dict[str, object]] = {}
    existing_keys: set[str] = set()

    for title in target_job_titles or []:
        # Skip empty or whitespace-only titles
        if not title.strip():
            continue

        key = _generate_unique_key(title, existing_keys)
        term = _build_search_term(title)
        results = _determine_result_count(title)

        personas[key] = {"term": term, "hours_old": DEFAULT_HOURS_OLD, "results": results}
        existing_keys.add(key)

    return personas
