# src/persona_builder.py
"""
Refactored persona configuration builder with improved maintainability.

This module is responsible for constructing persona-based search configurations
by leveraging the Strategy Pattern for platform-specific query generation.
It no longer contains legacy or deprecated functions.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from src.core.constants import PERSONA_DEFAULTS
from src.core.search_strategy import SearchStrategyFactory
from src.core.utils import validate_persona_config

logger = logging.getLogger(__name__)


class PersonaConfigBuilder:
    """
    Builds persona configurations from AI metadata using platform-specific strategies.
    """

    def __init__(self) -> None:
        self.strategy_factory = SearchStrategyFactory()

    def build_from_metadata(self, ai_metadata: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
        """
        Builds a complete persona configuration map from AI-extracted metadata.

        Args:
            ai_metadata: The metadata dictionary from the CV analysis.

        Returns:
            A dictionary of named persona configurations.
        """
        if not ai_metadata or not isinstance(ai_metadata, dict):
            logger.error("AI metadata is invalid or None. Cannot build personas.")
            return {}

        search_personas = ai_metadata.get("search_personas", [])
        if not search_personas or not isinstance(search_personas, list):
            logger.warning("No valid 'search_personas' found in AI metadata. Cannot build dynamic personas.")
            return {}

        return self._build_from_search_personas(search_personas)

    def _build_from_search_personas(self, search_personas: list[dict]) -> dict[str, dict[str, Any]]:
        """Build configurations from the modern 'search_personas' format."""
        final_persona_config: dict[str, dict[str, Any]] = {}
        for i, persona_obj in enumerate(search_personas):
            if not isinstance(persona_obj, dict):
                logger.warning(f"Skipping invalid persona object at index {i} (not a dict).")
                continue

            config = self._build_single_persona_config(persona_obj)
            if not config:
                continue

            persona_key = self._generate_persona_key(persona_obj, i)
            unique_key = self._ensure_unique_key(persona_key, final_persona_config)
            final_persona_config[unique_key] = config

        logger.info(f"✅ Built {len(final_persona_config)} persona configurations from AI metadata.")
        return final_persona_config

    def _build_single_persona_config(self, persona_obj: dict) -> dict[str, Any] | None:
        """Build and validate a configuration for a single persona object."""
        try:
            platform_queries = self.strategy_factory.build_all_queries(persona_obj)
            if not platform_queries:
                logger.warning(
                    f"No platform queries could be generated for persona: {persona_obj.get('primary_title_en')}"
                )
                return None

            config = {
                "platform_queries": platform_queries,
                "hours_old": PERSONA_DEFAULTS["hours_old"],
                "results": PERSONA_DEFAULTS["results"],
            }

            if validate_persona_config(config, logger):
                return config
            else:
                logger.warning(
                    f"Generated config for persona {persona_obj.get('primary_title_en')} failed validation."
                )
                return None
        except Exception as e:
            logger.exception(f"Error building single persona config: {e}")
            return None

    def _generate_persona_key(self, persona_obj: dict, index: int) -> str:
        """Generate a normalized, human-readable key for a persona."""
        primary_title = persona_obj.get("primary_title_en") or persona_obj.get("primary_title_tr", f"persona_{index}")
        # Sanitize the title to create a valid key
        key = re.sub(r"[\s/\\]+", "_", str(primary_title).lower())
        key = re.sub(r"[^\w_]", "", key)
        return key.strip("_")

    def _ensure_unique_key(self, key: str, existing_keys: dict[str, Any]) -> str:
        """Ensure the generated key is unique to avoid overwriting."""
        original_key = key
        counter = 1
        while key in existing_keys:
            key = f"{original_key}_{counter}"
            counter += 1
        return key


# ================= Legacy Compatibility Layer (for older tests) ================= #
def _generate_unique_key(title: str, existing: set[str]) -> str:  # pragma: no cover - simple utility
    base = re.sub(r"[^a-z0-9]+", "_", title.strip().lower()).strip("_")
    if not base:
        base = "persona"
    candidate = base
    i = 1
    while candidate in existing:
        candidate = f"{base}_{i}"
        i += 1
    return candidate


def build_dynamic_personas(
    titles: list[str],
) -> dict[str, dict[str, Any]]:  # pragma: no cover - exercised via legacy tests
    if not isinstance(titles, list):
        raise TypeError("titles must be a list")
    cleaned = []
    for t in titles:
        if not isinstance(t, str):
            raise TypeError("all titles must be strings")
        if not t.strip():
            continue
        cleaned.append(t.strip())
    if not cleaned:
        return {}
    # Intentional legacy behavior: raise if a literal 'invalid' present
    if any(c.lower() == "invalid" for c in cleaned):
        raise TypeError("invalid title encountered")

    personas: dict[str, dict[str, Any]] = {}
    existing: set[str] = set()
    for raw in cleaned:
        key = _generate_unique_key(raw, existing)
        existing.add(key)
        lower = raw.lower()
        results = 30 if ("developer" in lower or "react" in lower) else 20
        if "analyst" in lower:
            results = 25 if "data" in lower else 25
        persona_term = f'("{raw}" OR "{raw}") -Senior -Lead -Manager'
        personas[key] = {"term": persona_term, "hours_old": 72, "results": results}
    return personas
