from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .exceptions import ConfigError

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config.yaml")
_config_cache: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    """
    Loads configuration from config.yaml, overrides with environment variables,
    and caches the result. This is the central function for all configuration access.

    Override Priority (highest to lowest):
    1. Environment variables (.env file)
    2. config.yaml defaults

    Returns:
        Complete configuration dictionary with all settings merged
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    try:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)
            # Ensure we always have a dict, never None
            config_data: dict[str, Any] = yaml_content if yaml_content is not None else {}
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {CONFIG_PATH}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse config file: {exc}") from exc

    # Environment variable overrides with proper type conversion
    _apply_env_overrides(config_data)

    # Add API keys and sensitive data from environment
    _add_api_keys(config_data)

    _config_cache = config_data
    return _config_cache


def _apply_env_overrides(config_data: dict[str, Any]) -> None:
    """Apply environment variable overrides to config data."""
    # Vector store settings overrides
    if "CHROMA_COLLECTION_NAME" in os.environ:
        config_data.setdefault("vector_store_settings", {})["collection_name"] = os.getenv("CHROMA_COLLECTION_NAME")

    if "CHROMA_DB_PATH" in os.environ:
        config_data.setdefault("paths", {})["chromadb_dir"] = os.getenv("CHROMA_DB_PATH")

    # Apply numeric settings with default fallbacks
    _apply_numeric_setting(config_data, "job_search_settings", "default_hours_old", "DEFAULT_HOURS_OLD", 72)
    _apply_numeric_setting(
        config_data, "job_search_settings", "min_similarity_threshold", "MIN_SIMILARITY_THRESHOLD", 60
    )
    _apply_numeric_setting(
        config_data, "job_search_settings", "default_results_per_site", "DEFAULT_RESULTS_PER_SITE", 25
    )
    _apply_numeric_setting(config_data, "embedding_settings", "batch_size", "EMBEDDING_BATCH_SIZE", 10)
    _apply_numeric_setting(config_data, "embedding_settings", "retry_count", "EMBEDDING_RETRY_COUNT", 3)
    _apply_float_setting(config_data, "embedding_settings", "rate_limit_delay", "EMBEDDING_RATE_LIMIT_DELAY", 0.1)


def _apply_numeric_setting(config_data: dict[str, Any], section: str, key: str, env_var: str, default: int) -> None:
    """Apply numeric environment variable override with proper type conversion."""
    if env_var in os.environ:
        try:
            config_data.setdefault(section, {})[key] = int(os.getenv(env_var, str(default)))
        except ValueError:
            logger.warning(
                "Invalid numeric value for %s: %s, using default %s",
                env_var,
                os.getenv(env_var),
                default,
            )


def _apply_float_setting(config_data: dict[str, Any], section: str, key: str, env_var: str, default: float) -> None:
    """Apply float environment variable override with proper type conversion."""
    if env_var in os.environ:
        try:
            config_data.setdefault(section, {})[key] = float(os.getenv(env_var, str(default)))
        except ValueError:
            logger.warning(
                "Invalid float value for %s: %s, using default %s",
                env_var,
                os.getenv(env_var),
                default,
            )


def _add_api_keys(config_data: dict[str, Any]) -> None:
    """Add API keys and sensitive data from environment variables."""
    config_data["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
    config_data["GITHUB_TOKEN"] = os.getenv("GITHUB_TOKEN")

    # AI settings from environment
    config_data["GEMINI_MODEL"] = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    config_data["EMBEDDING_MODEL"] = os.getenv("EMBEDDING_MODEL", "text-embedding-004")


def load_settings() -> dict[str, Any]:
    """Legacy function, now a wrapper for get_config for backward compatibility."""
    return get_config()


def clear_cache() -> None:
    """Clear the configuration cache. Useful for testing or reloading configuration."""
    global _config_cache
    _config_cache = None
