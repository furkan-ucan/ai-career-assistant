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

from .core.constants import PERSONA_DEFAULTS
from .core.search_strategy import SearchStrategyFactory
from .core.utils import validate_persona_config

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
