# src/core/utils.py
"""
Core utility functions to eliminate code duplication and improve maintainability.
Following DRY principle and centralizing common operations.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def get_app_directories() -> dict[str, Path]:
    """
    Get application directories, supporting both development and installed package environments.

    Returns:
        Dictionary with keys: data_dir, logs_dir, config_dir, prompts_dir
    """
    # Check if we're in a development environment (presence of pyproject.toml)
    # Try to find project root by looking for pyproject.toml
    current_path = Path(__file__).resolve()
    for parent in [current_path] + list(current_path.parents):
        if (parent / "pyproject.toml").exists():
            # Development environment - use project structure
            return {
                "data_dir": parent / "data",
                "logs_dir": parent / "logs",
                "config_dir": parent / "config",
                "prompts_dir": parent / "prompts",
            }

    # Installed package environment - use user directories or environment variables
    base_dir = Path(os.getenv("KARIYER_ASISTANI_HOME", Path.home() / ".kariyer-asistani"))
    return {
        "data_dir": Path(os.getenv("KARIYER_ASISTANI_DATA_DIR", base_dir / "data")),
        "logs_dir": Path(os.getenv("KARIYER_ASISTANI_LOGS_DIR", base_dir / "logs")),
        "config_dir": Path(os.getenv("KARIYER_ASISTANI_CONFIG_DIR", base_dir / "config")),
        "prompts_dir": Path(os.getenv("KARIYER_ASISTANI_PROMPTS_DIR", base_dir / "prompts")),
    }


def safe_dataframe_concat(dataframes: list[pd.DataFrame], ignore_index: bool = True) -> pd.DataFrame:
    """
    Performant and safe DataFrame concatenation.

    Args:
        dataframes: List of DataFrames to concatenate
        ignore_index: Whether to ignore index during concatenation

    Returns:
        Concatenated DataFrame
    """
    if not dataframes:
        return pd.DataFrame()

    valid_dfs = [df for df in dataframes if df is not None and not df.empty]
    if not valid_dfs:
        return pd.DataFrame()

    return valid_dfs[0].copy() if len(valid_dfs) == 1 else pd.concat(valid_dfs, ignore_index=ignore_index)


def deduplicate_dataframe(df: pd.DataFrame, dedup_columns: list[str], logger: Any) -> pd.DataFrame:
    """
    Deduplicate a DataFrame based on specified columns and log the result.

    Args:
        df: DataFrame to deduplicate
        dedup_columns: Columns to use for deduplication
        logger: Logger instance for info messages

    Returns:
        Deduplicated DataFrame
    """
    if df.empty or not dedup_columns:
        return df
    initial_count = len(df)
    result = df.drop_duplicates(subset=dedup_columns, inplace=False, keep="first")
    removed_count = initial_count - len(result)
    if removed_count > 0:
        logger.info(f"🗑️ Deduplication: {removed_count} duplicate rows removed")
    return result


def setup_enhanced_logging(logger_name: str, level: str = "INFO") -> logging.Logger:
    """
    Centralized logging setup to eliminate duplication across modules.

    Args:
        logger_name: Name of the logger
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)

    valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
    chosen_level = level.upper()
    if chosen_level not in valid_levels:
        logger.warning(f"Invalid log level '{level}' provided. Defaulting to INFO.")
        chosen_level = "INFO"

    if not logger.handlers:  # Avoid duplicate handlers
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, chosen_level))

    return logger


def handle_scraping_error(
    error: Exception, context: str, logger: logging.Logger, raise_on_critical: bool = False
) -> bool:
    """
    Standardized error handling for scraping operations.

    Args:
        error: The exception that occurred
        context: Context information (e.g., "LinkedIn scraping")
        logger: Logger instance
        raise_on_critical: Whether to re-raise critical errors

    Returns:
        True if error was handled gracefully, False if critical
    """
    error_msg = f"❌ {context} error: {str(error)}"

    if isinstance(error, (ConnectionError, TimeoutError)):
        logger.warning(f"{error_msg} (Network issue - continuing)")
        return True
    elif isinstance(error, (ValueError, KeyError)):
        logger.error(f"{error_msg} (Data issue - continuing)")
        return True
    else:
        logger.error(f"{error_msg} (Critical error)", exc_info=True)
        if raise_on_critical:
            logger.exception(error_msg)
            return False
        return False


def _validate_required_fields(persona_cfg: dict[str, Any], logger: logging.Logger) -> bool:
    """
    Validate that all required fields are present in persona configuration.

    Args:
        persona_cfg: Persona configuration dictionary
        logger: Logger instance for warnings

    Returns:
        True if all required fields present, False otherwise
    """
    required_fields = ["hours_old", "results"]

    for field in required_fields:
        if field not in persona_cfg:
            logger.warning(f"⚠️ Missing required field in persona config: {field}")
            return False

    return True


def _validate_query_terms(persona_cfg: dict[str, Any], logger: logging.Logger) -> bool:
    """
    Validate that persona configuration has either platform_queries or legacy term.

    Args:
        persona_cfg: Persona configuration dictionary
        logger: Logger instance for warnings

    Returns:
        True if valid query terms present, False otherwise
    """
    has_platform_queries = "platform_queries" in persona_cfg
    has_legacy_term = "term" in persona_cfg

    if not (has_platform_queries or has_legacy_term):
        logger.warning("⚠️ Persona config missing both 'platform_queries' and 'term'")
        return False

    return True


def validate_persona_config(persona_cfg: dict[str, Any], logger: logging.Logger | None = None) -> bool:
    """
    Validate persona configuration structure.

    Args:
        persona_cfg: Persona configuration dictionary
        logger: Optional logger instance (falls back to module logger)

    Returns:
        True if valid, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Validate required fields
    if not _validate_required_fields(persona_cfg, logger):
        return False

    # Return query term validation sonucu direkt
    return _validate_query_terms(persona_cfg, logger)


def clean_search_term(term: str) -> str:
    """
    Clean and validate search terms.

    Args:
        term: Raw search term

    Returns:
        Cleaned search term
    """
    if not term or not isinstance(term, str):
        return ""

    # Remove excessive whitespace
    cleaned = " ".join(term.split())

    # Basic validation
    if len(cleaned.strip()) < 2:
        logging.warning(f"⚠️ Search term too short: '{cleaned}'")
        return ""

    return cleaned


def add_metadata_to_dataframe(df: pd.DataFrame, metadata: dict[str, Any]) -> pd.DataFrame:
    """
    Add consistent metadata columns to job DataFrames.

    Args:
        df: DataFrame to add metadata to
        metadata: Dictionary of metadata to add

    Returns:
        DataFrame with added metadata columns
    """
    if df.empty:
        return df

    result = df.copy()

    # Add timestamp if not exists
    if "collected_at" not in result.columns:
        result["collected_at"] = datetime.now()

    # Add metadata columns
    for key, value in metadata.items():
        result[key] = value

    return result
