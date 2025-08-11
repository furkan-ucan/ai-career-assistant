# src/embedding_cache.py
"""
Embedding Cache System - Prevents redundant embedding API calls
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Caches embeddings to prevent redundant API calls."""

    def __init__(self, cache_dir: str | Path = "data/embedding_cache", max_age_days: int = 90):
        """Initialize the embedding cache."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_days = max_age_days

    def _get_text_cache_key(self, text: str, embedding_type: str = "general") -> str:
        """Generate a unique cache key for text content."""
        # Normalize text: strip whitespace and convert to lowercase
        normalized_text = text.strip().lower()

        # Create hash
        text_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()[:16]
        return f"embed_{embedding_type}_{text_hash}.json"

    def _is_cache_valid(self, cache_data: dict[str, Any]) -> bool:
        """Check if cached data is still valid (not too old)."""
        try:
            cached_at = datetime.fromisoformat(cache_data.get("cached_at", ""))
            age = datetime.now(UTC) - cached_at
            return age <= timedelta(days=self.max_age_days)
        except (ValueError, TypeError):
            return False

    def get_cached_embedding(self, text: str, embedding_type: str = "general") -> list[float] | None:
        """Retrieve cached embedding for text if available and valid."""
        if not text.strip():
            return None

        cache_key = self._get_text_cache_key(text, embedding_type)
        cache_file = self.cache_dir / cache_key

        if not cache_file.exists():
            return None

        try:
            with cache_file.open("r", encoding="utf-8") as f:
                cache_data = json.load(f)

            if self._is_cache_valid(cache_data):
                logger.debug(f"Embedding cache hit for {embedding_type} text (length: {len(text)})")
                embedding_result = cache_data.get("embedding")
                return embedding_result if isinstance(embedding_result, list) else None
            else:
                logger.debug(f"Embedding cache expired for {embedding_type} text")
                cache_file.unlink(missing_ok=True)
                return None

        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to read embedding cache: {e}")
            cache_file.unlink(missing_ok=True)
            return None

    def save_embedding(self, text: str, embedding: list[float], embedding_type: str = "general") -> None:
        """Save embedding to cache."""
        if not text.strip() or not embedding:
            return

        cache_key = self._get_text_cache_key(text, embedding_type)
        cache_file = self.cache_dir / cache_key

        cache_data = {
            "text_length": len(text),
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "embedding_type": embedding_type,
            "embedding_dimensions": len(embedding),
            "cached_at": datetime.now(UTC).isoformat(),
            "embedding": embedding,
        }

        try:
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f)
            logger.debug(f"Cached {embedding_type} embedding (dims: {len(embedding)})")
        except (OSError, TypeError) as e:
            logger.error(f"Failed to save embedding cache: {e}")

    def get_cv_embedding(self, cv_text: str) -> list[float] | None:
        """Specific method for CV embedding cache."""
        return self.get_cached_embedding(cv_text, "cv")

    def save_cv_embedding(self, cv_text: str, embedding: list[float]) -> None:
        """Specific method for saving CV embedding."""
        self.save_embedding(cv_text, embedding, "cv")

    def get_job_description_embedding(self, description: str) -> list[float] | None:
        """Specific method for job description embedding cache."""
        return self.get_cached_embedding(description, "job_description")

    def save_job_description_embedding(self, description: str, embedding: list[float]) -> None:
        """Specific method for saving job description embedding."""
        self.save_embedding(description, embedding, "job_description")

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache files and return count of removed files."""
        removed_count = 0

        if not self.cache_dir.exists():
            return 0

        try:
            for cache_file in self.cache_dir.glob("embed_*.json"):
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
                logger.info(f"Cleaned up {removed_count} expired/corrupted embedding cache files")

        except Exception as e:
            logger.error(f"Error during embedding cache cleanup: {e}")

        return removed_count

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the embedding cache."""
        if not self.cache_dir.exists():
            return {"total_files": 0, "valid_files": 0, "expired_files": 0, "by_type": {}}

        total_files = 0
        valid_files = 0
        expired_files = 0
        by_type: dict[str, int] = {}

        try:
            for cache_file in self.cache_dir.glob("embed_*.json"):
                total_files += 1
                try:
                    with cache_file.open("r", encoding="utf-8") as f:
                        cache_data = json.load(f)

                    embedding_type = cache_data.get("embedding_type", "unknown")
                    by_type[embedding_type] = by_type.get(embedding_type, 0) + 1

                    if self._is_cache_valid(cache_data):
                        valid_files += 1
                    else:
                        expired_files += 1

                except (OSError, json.JSONDecodeError):
                    expired_files += 1
                    by_type["corrupted"] = by_type.get("corrupted", 0) + 1

        except Exception as e:
            logger.error(f"Error getting embedding cache stats: {e}")

        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "expired_files": expired_files,
            "by_type": by_type,
        }
