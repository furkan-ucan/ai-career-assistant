from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_dataframe_csv(df: pd.DataFrame, output_dir: Path, prefix: str) -> Path:
    """Save DataFrame to a timestamped CSV file."""
    if df is None or df.empty:
        raise ValueError("DataFrame cannot be None or empty")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_dir / f"{prefix}_{timestamp}.csv"
        df.to_csv(file_path, index=False, encoding="utf-8")
        return file_path
    except PermissionError as exc:
        raise OSError(f"Failed to save CSV to {output_dir}: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Unexpected error saving DataFrame: {exc}") from exc
