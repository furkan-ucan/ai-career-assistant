# src/config.py
"""Modern configuration management with Pydantic validation for Akilli Kariyer Asistani.
This module handles loading configuration from a YAML file, applying environment variable overrides,
validates all settings using Pydantic models, and caches the configuration for efficient access.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .config_models import AppConfig
from .exceptions import ConfigError

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config.yaml")
_config_cache: AppConfig | None = None


def _get_cached_config() -> AppConfig | None:
    """Get cached validated configuration if available."""
    return _config_cache


def _set_cached_config(config_data: AppConfig) -> AppConfig:
    """Cache validated configuration data and return it."""
    global _config_cache
    _config_cache = config_data
    return _config_cache


def get_config() -> AppConfig:
    """
    Loads configuration from config.yaml, validates with Pydantic models,
    applies environment overrides, and caches the result.

    Returns:
        Validated AppConfig instance with all settings properly typed

    Raises:
        ConfigError: If configuration is invalid or required fields missing
    """
    # Check cache first
    cached_config = _get_cached_config()
    if cached_config is not None:
        return cached_config

    # Load, validate and process configuration
    raw_config_data = _load_yaml_config()
    _apply_env_overrides(raw_config_data)
    _add_api_keys(raw_config_data)

    # Validate with Pydantic
    try:
        validated_config = AppConfig(**raw_config_data)
    except Exception as exc:
        raise ConfigError(f"Configuration validation failed: {exc}") from exc

    # Cache and return
    return _set_cached_config(validated_config)


def _load_yaml_config() -> dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)
            return yaml_content if yaml_content is not None else {}
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {CONFIG_PATH}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse config file: {exc}") from exc


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
    config_data["gemini_api_key"] = os.getenv("GEMINI_API_KEY")
    config_data["github_token"] = os.getenv("GITHUB_TOKEN")

    # AI settings from environment
    config_data["gemini_model"] = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    config_data["embedding_model"] = os.getenv("EMBEDDING_MODEL", "text-embedding-004")

    # Validate required keys after Pydantic validation
    if config_data["gemini_api_key"] is None:
        raise ConfigError("Missing required environment variable: GEMINI_API_KEY")
    if config_data["github_token"] is None:
        raise ConfigError("Missing required environment variable: GITHUB_TOKEN")


def load_settings() -> AppConfig:
    """Legacy function, now a wrapper for get_config for backward compatibility."""
    return get_config()


def clear_cache() -> None:
    """Clear the configuration cache. Useful for testing or reloading configuration."""
    global _config_cache
    _config_cache = None
