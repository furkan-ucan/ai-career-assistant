# src/embedding_service.py
"""
Embedding Service using Google Gemini API.
Refactored to use Dependency Injection for API keys and settings.
"""

import logging
import time

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Creates text embeddings using the Google Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str = "models/text-embedding-004",
        batch_size: int = 10,
        retry_count: int = 3,
        rate_limit_delay: float = 0.1,
    ):
        """
        Initializes the Gemini API and stores configuration settings.

        Args:
            api_key: The Google Gemini API key.
            model: The embedding model to use.
            batch_size: The default batch size for embedding multiple texts.
            retry_count: The default number of retries for API calls.
            rate_limit_delay: The default delay between API calls in a batch.
        """
        if not api_key:
            raise ValueError("Gemini API key is required and cannot be empty.")

        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            logger.exception(f"Failed to configure Gemini API: {e}")
            raise ValueError("Failed to configure Gemini API with the provided key.") from e

        self.model = model
        self.batch_size = batch_size
        self.retry_count = retry_count
        self.rate_limit_delay = rate_limit_delay
        logger.info("✅ EmbeddingService initialized successfully.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_embedding(self, text: str, max_chars: int = 8000) -> list[float] | None:
        """
        Creates an embedding for a single text, with token limit control.

        Args:
            text: The text to be embedded.
            max_chars: The maximum number of characters to consider.

        Returns:
            The embedding vector or None if an error occurs.
        """
        if not text:
            return None

        truncated_text = text[:max_chars]
        if len(text) > max_chars:
            logger.debug(f"Text truncated from {len(text)} to {max_chars} characters.")

        try:
            result = genai.embed_content(model=self.model, content=truncated_text, task_type="retrieval_document")
            embedding = result.get("embedding")
            if isinstance(embedding, list) and all(isinstance(x, (float, int)) for x in embedding):
                return [float(x) for x in embedding]
            return None
        except Exception:
            logger.exception(f"Failed to create embedding for text chunk: '{truncated_text[:50]}...'")
            # The @retry decorator will handle re-raising the exception after attempts.
            raise

    def create_embeddings_batch(self, texts: list[str], batch_size: int | None = None) -> list[list[float] | None]:
        """
        Creates embeddings for multiple texts in batches.

        Args:
            texts: A list of texts to be embedded.
            batch_size: The size of each batch. Defaults to instance setting.

        Returns:
            A list of embedding vectors. Each item is a list of floats or None.
        """
        effective_batch_size = batch_size if batch_size is not None else self.batch_size
        embeddings = []
        total_texts = len(texts)
        logger.info(f"🔄 Creating embeddings for {total_texts} texts in batches of {effective_batch_size}...")

        for i in range(0, total_texts, effective_batch_size):
            batch = texts[i : i + effective_batch_size]
            for text in batch:
                embedding = self.create_embedding(text)
                embeddings.append(embedding)
                time.sleep(self.rate_limit_delay)  # Rate limiting
            logger.info(f"📊 Progress: {min(i + effective_batch_size, total_texts)}/{total_texts}")

        successful_count = sum(1 for e in embeddings if e is not None)
        logger.info(f"✅ {successful_count}/{total_texts} embeddings created successfully.")
        return embeddings
