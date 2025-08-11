# src/reranking_cache.py
"""
AI Reranking Cache System - Prevents redundant API calls for job analysis
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RerankingCache:
    """Caches AI reranking results to prevent redundant API calls."""

    def __init__(self, cache_dir: str | Path = "data/reranking_cache", max_age_days: int = 30):
        """Initialize the reranking cache."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_days = max_age_days

    def _get_job_cache_key(self, job: dict[str, Any]) -> str:
        """Generate a unique cache key for a job based on its core content."""
        # Use title, company, and first 500 chars of description for key
        title = str(job.get("title", "")).strip().lower()
        company = str(job.get("company", "")).strip().lower()
        description = str(job.get("description", ""))[:500].strip().lower()

        # Create a stable hash
        content = f"{title}|{company}|{description}"
        hash_obj = hashlib.sha256(content.encode("utf-8"))
        return f"rerank_{hash_obj.hexdigest()[:16]}.json"

    def _is_cache_valid(self, cache_data: dict[str, Any]) -> bool:
        """Check if cached data is still valid (not too old)."""
        try:
            cached_at = datetime.fromisoformat(cache_data.get("cached_at", ""))
            age = datetime.now(UTC) - cached_at
            return age <= timedelta(days=self.max_age_days)
        except (ValueError, TypeError):
            return False

    def get_cached_reranking(self, job: dict[str, Any]) -> dict[str, Any] | None:
        """Retrieve cached reranking result for a job if available and valid."""
        cache_key = self._get_job_cache_key(job)
        cache_file = self.cache_dir / cache_key

        if not cache_file.exists():
            return None

        try:
            with cache_file.open("r", encoding="utf-8") as f:
                cache_data = json.load(f)

            if self._is_cache_valid(cache_data):
                logger.debug(f"Cache hit for job: {job.get('title', 'Unknown')}")
                rerank_result = cache_data.get("rerank_result", {})
                return rerank_result if isinstance(rerank_result, dict) else None
            else:
                logger.debug(f"Cache expired for job: {job.get('title', 'Unknown')}")
                # Optionally remove expired cache
                cache_file.unlink(missing_ok=True)
                return None

        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to read cache for job {job.get('title', 'Unknown')}: {e}")
            return None

    def save_reranking_result(self, job: dict[str, Any], rerank_result: dict[str, Any]) -> None:
        """Save reranking result to cache."""
        cache_key = self._get_job_cache_key(job)
        cache_file = self.cache_dir / cache_key

        cache_data = {
            "job_title": job.get("title", ""),
            "job_company": job.get("company", ""),
            "cached_at": datetime.now(UTC).isoformat(),
            "rerank_result": rerank_result,
        }

        try:
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cached reranking for job: {job.get('title', 'Unknown')}")
        except (OSError, TypeError) as e:
            logger.error(f"Failed to save reranking cache for job {job.get('title', 'Unknown')}: {e}")

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache files and return count of removed files."""
        removed_count = 0

        if not self.cache_dir.exists():
            return 0

        try:
            for cache_file in self.cache_dir.glob("rerank_*.json"):
                try:
                    with cache_file.open("r", encoding="utf-8") as f:
                        cache_data = json.load(f)

                    if not self._is_cache_valid(cache_data):
                        cache_file.unlink()
                        removed_count += 1

                except (OSError, json.JSONDecodeError):
                    # Remove corrupted cache files
                    cache_file.unlink(missing_ok=True)
                    removed_count += 1

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired/corrupted reranking cache files")

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

        return removed_count

    def get_cache_stats(self) -> dict[str, int]:
        """Get statistics about the reranking cache."""
        if not self.cache_dir.exists():
            return {"total_files": 0, "valid_files": 0, "expired_files": 0}

        total_files = 0
        valid_files = 0
        expired_files = 0

        try:
            for cache_file in self.cache_dir.glob("rerank_*.json"):
                total_files += 1
                try:
                    with cache_file.open("r", encoding="utf-8") as f:
                        cache_data = json.load(f)

                    if self._is_cache_valid(cache_data):
                        valid_files += 1
                    else:
                        expired_files += 1

                except (OSError, json.JSONDecodeError):
                    expired_files += 1

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")

        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "expired_files": expired_files,
        }
