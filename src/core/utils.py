# src/core/utils.py
"""
Core utility functions to eliminate code duplication and improve maintainability.
Following DRY principle and centralizing common operations.
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd


def safe_dataframe_concat(
    dataframes: list[pd.DataFrame], ignore_index: bool = True, dedup_columns: list[str] | None = None
) -> pd.DataFrame:
    """
    Performant and safe DataFrame concatenation with optional deduplication.

    Eliminates the anti-pattern of multiple pd.concat calls.

    Args:
        dataframes: List of DataFrames to concatenate
        ignore_index: Whether to ignore index during concatenation
        dedup_columns: Columns to use for deduplication

    Returns:
        Concatenated and optionally deduplicated DataFrame
    """
    if not dataframes:
        return pd.DataFrame()

    # Filter out None and empty DataFrames
    valid_dfs = [df for df in dataframes if df is not None and not df.empty]

    if not valid_dfs:
        return pd.DataFrame()

    # Single operation with ternary operator for performance
    result: pd.DataFrame = (
        valid_dfs[0].copy() if len(valid_dfs) == 1 else pd.concat(valid_dfs, ignore_index=ignore_index)
    )

    # Optional deduplication
    if dedup_columns and not result.empty:
        initial_count = len(result)
        result.drop_duplicates(subset=dedup_columns, inplace=True, keep="first")
        removed_count = initial_count - len(result)
        if removed_count > 0:
            logging.info(f"🗑️ Deduplication: {removed_count} duplicate rows removed")

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

    if not logger.handlers:  # Avoid duplicate handlers
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper()))

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
            try:
                raise RuntimeError(error_msg)
            except RuntimeError:
                logger.exception("Critical error raised")
                return False
        return False


def validate_persona_config(persona_cfg: dict[str, Any]) -> bool:
    """
    Validate persona configuration structure.

    Args:
        persona_cfg: Persona configuration dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["hours_old", "results"]

    # Check for required fields
    for field in required_fields:
        if field not in persona_cfg:
            logging.warning(f"⚠️ Missing required field in persona config: {field}")
            return False

    # Validate platform_queries or legacy term
    has_platform_queries = "platform_queries" in persona_cfg
    has_legacy_term = "term" in persona_cfg

    if not (has_platform_queries or has_legacy_term):
        logging.warning("⚠️ Persona config missing both 'platform_queries' and 'term'")
        return False

    return True


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
