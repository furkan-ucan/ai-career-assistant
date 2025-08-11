#!/usr/bin/env python3
"""Final duplicate cleanup script"""

import logging

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_final_duplicates():
    """Fix the remaining duplicate in the CSV file"""
    try:
        # Load the CSV
        df = pd.read_csv("data/job_ilanlari.csv")
        logger.info(f"Loaded {len(df)} rows")

        # Check for duplicates
        initial_count = len(df)
        unique_ids = df["id"].nunique()
        logger.info(f"Initial: {initial_count} rows, {unique_ids} unique IDs")

        # Remove duplicates by ID (keep first occurrence)
        df_clean = df.drop_duplicates(subset=["id"], keep="first")

        # Also check URL duplicates
        if "job_url" in df_clean.columns:
            df_clean = df_clean.drop_duplicates(subset=["job_url"], keep="first")

        final_count = len(df_clean)
        final_unique = df_clean["id"].nunique()

        logger.info(f"Final: {final_count} rows, {final_unique} unique IDs")
        logger.info(f"Removed {initial_count - final_count} duplicates")

        # Save the cleaned data
        df_clean.to_csv("data/job_ilanlari.csv", index=False)
        logger.info("✅ Cleaned data saved to data/job_ilanlari.csv")

        return True

    except Exception as e:
        logger.error(f"Error fixing duplicates: {e}")
        return False


if __name__ == "__main__":
    fix_final_duplicates()
