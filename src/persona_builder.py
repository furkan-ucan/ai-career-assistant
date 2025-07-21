# src/persona_builder.py
"""
Refactored persona configuration builder with improved maintainability.

Following Single Responsibility Principle and utilizing the new Strategy Pattern
for platform-specific query generation.
"""

from __future__ import annotations

import re
from typing import Any

from .core.constants import PERSONA_DEFAULTS
from .core.search_strategy import SearchStrategyFactory
from .core.utils import setup_enhanced_logging, validate_persona_config

logger = setup_enhanced_logging(__name__)


class PersonaConfigBuilder:
    """
    Builds persona configurations with proper separation of concerns.

    Handles both new Dr. Finch format and legacy format personas.
    """

    def __init__(self):
        self.strategy_factory = SearchStrategyFactory()

    def build_from_metadata(self, ai_metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """
        Build persona configuration from AI metadata.

        Args:
            ai_metadata: Metadata from CV analysis

        Returns:
            Dictionary of persona configurations
        """
        search_personas = ai_metadata.get("search_personas", [])

        if search_personas:
            return self._build_from_search_personas(search_personas)
        else:
            return self._build_from_legacy_titles(ai_metadata)

    def _build_from_search_personas(self, search_personas: list[dict]) -> dict[str, dict[str, Any]]:
        """Build configurations from Dr. Finch format search personas."""
        persona_config: dict[str, dict[str, Any]] = {}

        for i, persona_obj in enumerate(search_personas):
            if not isinstance(persona_obj, dict):
                logger.warning(f"Skipping invalid persona at index {i}")
                continue

            persona_key = self._generate_persona_key(persona_obj, i)
            persona_key = self._ensure_unique_key(persona_key, persona_config)

            config = self._build_single_persona_config(persona_obj)
            if config:
                persona_config[persona_key] = config

        logger.info(f"✅ Built {len(persona_config)} persona configurations")
        return persona_config

    def _build_single_persona_config(self, persona_obj: dict) -> dict[str, Any] | None:
        """Build configuration for a single persona."""
        try:
            # Generate platform-specific queries using Strategy Pattern
            platform_queries = self.strategy_factory.build_all_queries(persona_obj)

            if not platform_queries:
                logger.warning("No platform queries generated for persona")
                return None

            config = {
                "platform_queries": platform_queries,
                "hours_old": PERSONA_DEFAULTS["hours_old"],
                "results": PERSONA_DEFAULTS["results"],
                # Legacy compatibility
                "term": platform_queries.get("linkedin_tier1_query", ""),
            }

            if validate_persona_config(config):
                return config

        except Exception as e:
            logger.error(f"Error building persona config: {e}")

        return None

    def _build_from_legacy_titles(self, ai_metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Fallback: Build from legacy target_job_titles format."""
        target_titles = ai_metadata.get("target_job_titles", [])
        if not target_titles:
            logger.warning("No target_job_titles found in metadata")
            return {}

        logger.info("Building personas from legacy target_job_titles format")
        return self._build_legacy_personas(target_titles)

    def _build_legacy_personas(self, target_job_titles: list[str]) -> dict[str, dict[str, Any]]:
        """Build persona configs from simple job title list."""
        if not isinstance(target_job_titles, list):
            raise TypeError("target_job_titles must be a list")

        personas: dict[str, dict[str, Any]] = {}
        existing_keys: set[str] = set()

        for title in target_job_titles:
            if not isinstance(title, str) or not title.strip():
                continue

            key = self._generate_unique_key(title, existing_keys)
            term = self._build_legacy_search_term(title)
            results = self._determine_result_count(title)

            personas[key] = {"term": term, "hours_old": PERSONA_DEFAULTS["hours_old"], "results": results}
            existing_keys.add(key)

        return personas

    def _generate_persona_key(self, persona_obj: dict, index: int) -> str:
        """Generate a normalized key for persona."""
        primary_title = persona_obj.get("primary_title_en") or persona_obj.get("primary_title_tr", "")

        if primary_title:
            key = re.sub(r"[^\w\s]", "", str(primary_title).lower())
            key = re.sub(r"\s+", "_", key)
            return key
        else:
            return f"persona_{index}"

    def _ensure_unique_key(self, persona_key: str, existing_config: dict[str, Any]) -> str:
        """Ensure key uniqueness to prevent collisions."""
        original_key = persona_key
        counter = 1
        while persona_key in existing_config:
            persona_key = f"{original_key}_{counter}"
            counter += 1
        return persona_key

    def _generate_unique_key(self, title: str, existing_keys: set) -> str:
        """Generate unique key from job title."""
        key = re.sub(r"[^\w\s]", "", title.strip().lower())
        key = re.sub(r"\s+", "_", key)

        original_key = key
        counter = 1
        while key in existing_keys:
            key = f"{original_key}_{counter}"
            counter += 1
        return key

    def _build_legacy_search_term(self, title: str) -> str:
        """Build search term for legacy format."""
        if '"' in title:
            return f"{title} -Senior -Lead"

        safe_title = title.replace('"', '"')
        return f'("{safe_title}") -Senior -Lead'

    def _determine_result_count(self, title: str) -> int:
        """Determine result count based on job title keywords."""
        role_lower = title.lower()
        role_results = {"developer": 30, "analyst": 25}
        for role, count in role_results.items():
            if role in role_lower:
                return count
        return PERSONA_DEFAULTS["results"]


# Convenience functions for backward compatibility
def build_dynamic_personas_from_metadata(ai_metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Legacy wrapper for PersonaConfigBuilder."""
    builder = PersonaConfigBuilder()
    return builder.build_from_metadata(ai_metadata)


def build_dynamic_personas(target_job_titles: list[str]) -> dict[str, dict[str, Any]]:
    """Legacy function for building from job titles list."""
    builder = PersonaConfigBuilder()
    return builder._build_legacy_personas(target_job_titles)


def build_platform_specific_queries(persona_obj: dict[str, Any]) -> dict[str, str]:
    """
    Generate platform-specific queries using Strategy Pattern.

    This is the main entry point for the new Dr. Finch architecture.
    """
    factory = SearchStrategyFactory()
    return factory.build_all_queries(persona_obj)


def build_search_term_from_persona(persona_obj: dict[str, Any]) -> str:
    """
    LEGACY FUNCTION - Maintained for backward compatibility.

    For new development, use build_platform_specific_queries() directly.
    """
    logger.warning("Using legacy build_search_term_from_persona - consider upgrading")

    platform_queries = build_platform_specific_queries(persona_obj)
    return platform_queries.get("linkedin_tier1_query", "")


# Legacy/deprecated functions maintained for backward compatibility
def _build_personas_from_search_personas(search_personas: list[dict]) -> dict[str, dict[str, Any]]:
    """DEPRECATED: Use PersonaConfigBuilder instead."""
    logger.warning("_build_personas_from_search_personas is deprecated")
    builder = PersonaConfigBuilder()
    return builder._build_from_search_personas(search_personas)


def _build_personas_from_target_titles(ai_metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """DEPRECATED: Use PersonaConfigBuilder instead."""
    logger.warning("_build_personas_from_target_titles is deprecated")
    builder = PersonaConfigBuilder()
    return builder._build_from_legacy_titles(ai_metadata)


def _generate_persona_key(persona_obj: dict, index: int) -> str:
    """DEPRECATED: Use PersonaConfigBuilder instead."""
    builder = PersonaConfigBuilder()
    return builder._generate_persona_key(persona_obj, index)


def _ensure_unique_key(persona_key: str, existing_config: dict[str, Any]) -> str:
    """DEPRECATED: Use PersonaConfigBuilder instead."""
    builder = PersonaConfigBuilder()
    return builder._ensure_unique_key(persona_key, existing_config)


def _validate_input(target_job_titles: list[str]) -> None:
    """Validate input parameters for build_dynamic_personas."""
    if not isinstance(target_job_titles, list):
        raise TypeError("target_job_titles must be a list")

    for title in target_job_titles:
        if not isinstance(title, str):
            raise TypeError(f"All job titles must be strings, got {type(title)}")


def _generate_unique_key(title: str, existing_keys: set[str]) -> str:
    """DEPRECATED: Use PersonaConfigBuilder instead."""
    builder = PersonaConfigBuilder()
    return builder._generate_unique_key(title, existing_keys)


def _build_search_term(title: str) -> str:
    """DEPRECATED: Use PersonaConfigBuilder instead."""
    builder = PersonaConfigBuilder()
    return builder._build_legacy_search_term(title)


def _determine_result_count(title: str) -> int:
    """DEPRECATED: Use PersonaConfigBuilder instead."""
    builder = PersonaConfigBuilder()
    return builder._determine_result_count(title)
