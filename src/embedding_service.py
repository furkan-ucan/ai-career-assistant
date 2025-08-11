# src/embedding_service.py
"""
Embedding Service using Google Gemini API with caching support.
Refactored to use Dependency Injection for API keys and settings.
"""

import logging
import time
from typing import Any

import google.generativeai as genai  # type: ignore[attr-defined]
from tenacity import retry, stop_after_attempt, wait_exponential

from .embedding_cache import EmbeddingCache

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Creates text embeddings using the Google Gemini API with caching."""

    def __init__(
        self,
        api_key: str,
        batch_size: int = 10,
        retry_count: int = 3,
        rate_limit_delay: float = 0.1,
        cache_enabled: bool = True,
        cache_dir: str = "data/embedding_cache",
    ):
        """Initialize the embedding service with caching support."""
        if not api_key:
            raise ValueError("API key is required for EmbeddingService")
        # google.generativeai stubs may not expose configure in type hints
        genai.configure(api_key=api_key)  # type: ignore[attr-defined]
        self.batch_size = batch_size
        self.retry_count = retry_count
        self.rate_limit_delay = rate_limit_delay

        # Initialize cache if enabled
        self.cache_enabled = cache_enabled
        if cache_enabled:
            self.cache = EmbeddingCache(cache_dir=cache_dir)
            logger.info("✅ Embedding cache enabled")
        else:
            self.cache = None
            logger.info("⚠️ Embedding cache disabled")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def create_embedding(self, text: str, max_chars: int = 8000) -> list[float] | None:
        """Create an embedding for the given text with cache support."""
        if not text.strip():
            logger.warning("Empty text provided for embedding.")
            return None

        # Check cache first
        if self.cache_enabled and self.cache:
            cached_embedding = self.cache.get_cached_embedding(text)
            if cached_embedding is not None:
                return cached_embedding

        # Truncate text if too long
        truncated_text = text[:max_chars] if len(text) > max_chars else text

        try:
            time.sleep(self.rate_limit_delay)
            # embed_content sometimes missing in stubs -> ignore for mypy
            response: Any = genai.embed_content(  # type: ignore[attr-defined]
                model="models/text-embedding-004",
                content=truncated_text,
                task_type="retrieval_query",
            )

            embedding = response.get("embedding") if isinstance(response, dict) else None
            if embedding and isinstance(embedding, list):
                # Save to cache
                if self.cache_enabled and self.cache:
                    self.cache.save_embedding(text, embedding)
                # Ensure all numeric
                typed_embedding: list[float] = [float(x) for x in embedding]
                return typed_embedding
            else:
                logger.warning("No embedding returned from Gemini API.")
                return None

        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            return None

    def create_embeddings_batch(self, texts: list[str], batch_size: int | None = None) -> list[list[float] | None]:
        """Create embeddings for multiple texts in batches with caching."""
        effective_batch_size = batch_size if batch_size is not None else self.batch_size
        embeddings = []
        total_texts = len(texts)
        logger.info(f"🔄 Creating embeddings for {total_texts} texts in batches of {effective_batch_size}...")

        for i in range(0, total_texts, effective_batch_size):
            batch = texts[i : i + effective_batch_size]
            for text in batch:
                embedding = self.create_embedding(text)
                embeddings.append(embedding if embedding is None else [float(x) for x in embedding])
                time.sleep(self.rate_limit_delay)  # Rate limiting
            logger.info(f"📊 Progress: {min(i + effective_batch_size, total_texts)}/{total_texts}")

        successful_count = sum(1 for e in embeddings if e is not None)
        logger.info(f"✅ {successful_count}/{total_texts} embeddings created successfully.")
        return embeddings
