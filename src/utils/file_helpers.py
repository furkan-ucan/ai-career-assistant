from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_dataframe_csv(df: pd.DataFrame, output_dir: Path, prefix: str) -> Path:
    """Save DataFrame to a timestamped CSV file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"{prefix}_{timestamp}.csv"
    df.to_csv(file_path, index=False, encoding="utf-8")
    return file_path
