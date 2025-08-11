#!/usr/bin/env python3
"""
Data cleanup script to consolidate old CSV files into single master file.
This removes file bloat and maintains a clean data directory.
"""

import logging
import shutil
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_data_directory():
    """Consolidate all job CSV files into a single master file."""
    data_dir = Path("data")

    if not data_dir.exists():
        logger.error("Data directory not found!")
        return

    # Find all job CSV files
    job_csv_files = list(data_dir.glob("job_ilanlari_*.csv"))
    jobspy_csv_files = list(data_dir.glob("jobspy_optimize_*.csv"))

    all_csv_files = job_csv_files + jobspy_csv_files

    if not all_csv_files:
        logger.info("No CSV files found to cleanup.")
        return

    logger.info(f"Found {len(all_csv_files)} CSV files to consolidate")

    # Consolidate all data
    all_dataframes = []
    total_jobs = 0

    for csv_file in all_csv_files:
        try:
            df = pd.read_csv(csv_file, encoding="utf-8")
            all_dataframes.append(df)
            total_jobs += len(df)
            logger.info(f"Loaded {len(df)} jobs from {csv_file.name}")
        except Exception as e:
            logger.warning(f"Could not read {csv_file}: {e}")

    if not all_dataframes:
        logger.warning("No valid CSV files found!")
        return

    # Combine all dataframes
    combined_df = pd.concat(all_dataframes, ignore_index=True)

    # Remove duplicates based on URL if available
    if "url" in combined_df.columns:
        initial_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=["url"], keep="last")
        duplicates_removed = initial_count - len(combined_df)
        logger.info(f"Removed {duplicates_removed} duplicate jobs")

    # Save to master file
    master_file = data_dir / "job_ilanlari.csv"
    combined_df.to_csv(master_file, index=False, encoding="utf-8")
    logger.info(f"✅ Saved {len(combined_df)} unique jobs to {master_file}")

    # Create backup directory and move old files
    backup_dir = data_dir / "csv_backups"
    backup_dir.mkdir(exist_ok=True)

    moved_count = 0
    for csv_file in all_csv_files:
        try:
            backup_path = backup_dir / csv_file.name
            shutil.move(str(csv_file), str(backup_path))
            moved_count += 1
        except Exception as e:
            logger.warning(f"Could not move {csv_file}: {e}")

    logger.info(f"📁 Moved {moved_count} old CSV files to backup directory")
    logger.info(f"🎯 Cleanup complete! From {total_jobs} total jobs → {len(combined_df)} unique jobs")
    logger.info(f"💾 Space saved: Removed {len(all_csv_files)} separate files")


if __name__ == "__main__":
    cleanup_data_directory()
