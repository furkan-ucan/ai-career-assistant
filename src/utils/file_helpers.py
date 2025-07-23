from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def save_dataframe_csv(df: pd.DataFrame, output_dir: Path, prefix: str) -> Path:
    """
    Save a pandas DataFrame to a timestamped CSV file in the specified output directory.

    Args:
        df (pd.DataFrame): DataFrame to be saved. Must not be None or empty.
        output_dir (Path): Directory where the CSV file will be saved. Created if it doesn't exist.
        prefix (str): Prefix for the output file name (e.g., 'results').

    Returns:
        Path: Path to the saved CSV file.

    Raises:
        ValueError: If df is None or empty.
        OSError: If there is a permission error while saving the file.
        RuntimeError: For any other unexpected errors during save operation.
    """
    if df is None or df.empty:
        raise ValueError("DataFrame cannot be None or empty")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_dir / f"{prefix}_{timestamp}.csv"
        df.to_csv(file_path, index=False, encoding="utf-8")
        return file_path
    except PermissionError as exc:
        logger.exception("Permission denied while saving CSV to %s", output_dir)
        raise OSError(f"Failed to save CSV to {output_dir}: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error while saving DataFrame to %s", output_dir)
        raise RuntimeError(f"Unexpected error saving DataFrame: {exc}") from exc
