import hashlib
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def generate_job_id(row):
    """Generate a unique job ID based on multiple fields."""
    key_fields = [
        str(row.get("title", "")).strip().lower(),
        str(row.get("company", "")).strip().lower(),
        str(row.get("location", "")).strip().lower(),
        str(row.get("description", ""))[:100].strip().lower(),  # First 100 chars
    ]
    combined = "|".join(key_fields)
    # Not for security, only stable deterministic short ID -> use SHA256 and truncate
    digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]
    return digest


def save_dataframe_csv(df: pd.DataFrame, output_dir: Path, prefix: str) -> Path:
    """
    Save a pandas DataFrame to a single CSV file with advanced deduplication.

    Uses multiple deduplication strategies to prevent data bloat and maintain
    a clean, unique dataset of job listings.

    Args:
        df (pd.DataFrame): DataFrame to be saved. Must not be None or empty.
        output_dir (Path): Directory where the CSV file will be saved. Created if it doesn't exist.
        prefix (str): Prefix for the output file name (e.g., 'job_ilanlari').

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
        file_path = output_dir / f"{prefix}.csv"

        # Add composite job ID for better deduplication
        df = df.copy()
        df["composite_id"] = df.apply(generate_job_id, axis=1)

        # If file exists, load existing data and merge with new data
        if file_path.exists():
            try:
                existing_df = pd.read_csv(file_path, encoding="utf-8")

                # Add composite ID to existing data if not present
                if "composite_id" not in existing_df.columns:
                    existing_df["composite_id"] = existing_df.apply(generate_job_id, axis=1)

                # Multi-stage deduplication
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                initial_count = len(combined_df)

                # Stage 1: URL deduplication (highest priority)
                url_column = "job_url" if "job_url" in combined_df.columns else "url"
                if url_column in combined_df.columns:
                    combined_df = combined_df.drop_duplicates(subset=[url_column], keep="first")
                    stage1_removed = initial_count - len(combined_df)
                else:
                    stage1_removed = 0

                # Stage 2: ID deduplication (for legacy data)
                id_column = "id" if "id" in combined_df.columns else None
                if id_column:
                    id_initial = len(combined_df)
                    combined_df = combined_df.drop_duplicates(subset=[id_column], keep="first")
                    id_removed = id_initial - len(combined_df)
                else:
                    id_removed = 0

                # Stage 3: Composite ID deduplication (content-based)
                combined_df = combined_df.drop_duplicates(subset=["composite_id"], keep="first")
                stage2_removed = (initial_count - stage1_removed - id_removed) - len(combined_df)

                # Stage 4: Title+Company fallback
                if "title" in combined_df.columns and "company" in combined_df.columns:
                    pre_stage3 = len(combined_df)
                    combined_df = combined_df.drop_duplicates(subset=["title", "company"], keep="first")
                    stage3_removed = pre_stage3 - len(combined_df)
                else:
                    stage3_removed = 0

                unique_jobs = len(combined_df)

                logger.info("📊 Advanced deduplication complete:")
                logger.info(f"   • Initial: {initial_count} jobs")
                logger.info(f"   • URL duplicates removed: {stage1_removed}")
                if id_removed > 0:
                    logger.info(f"   • ID duplicates removed: {id_removed}")
                logger.info(f"   • Content duplicates removed: {stage2_removed}")
                logger.info(f"   • Title+Company duplicates removed: {stage3_removed}")
                logger.info(f"   • Final unique jobs: {unique_jobs}")

                # Remove temporary composite_id column before saving
                if "composite_id" in combined_df.columns:
                    combined_df = combined_df.drop("composite_id", axis=1)

                combined_df.to_csv(file_path, index=False, encoding="utf-8")

            except Exception as e:
                logger.warning(f"⚠️ Could not merge with existing file: {e}. Creating new file.")
                # Remove composite_id and save new file
                df = df.drop("composite_id", axis=1)
                df.to_csv(file_path, index=False, encoding="utf-8")
        else:
            # Create new file - remove composite_id
            df = df.drop("composite_id", axis=1)
            df.to_csv(file_path, index=False, encoding="utf-8")
            logger.info(f"📁 Created new job database with {len(df)} jobs")

        return file_path

    except PermissionError as exc:
        logger.exception("Permission denied while saving CSV to %s", output_dir)
        raise OSError(f"Failed to save CSV to {output_dir}: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error while saving DataFrame to %s", output_dir)
        raise RuntimeError(f"Unexpected error saving DataFrame: {exc}") from exc
