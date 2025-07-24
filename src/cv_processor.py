# src/cv_processor.py
"""
CV Processing Module - Reads and creates embeddings for the user's CV.
Refactored to accept an EmbeddingService instance via dependency injection.
"""

import logging
from pathlib import Path

from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class CVProcessor:
    """Handles loading the CV file and orchestrating embedding creation."""

    def __init__(self, cv_path: str, embedding_service: EmbeddingService):
        """
        Initializes the CV processor.

        Args:
            cv_path: The file path to the user's CV.
            embedding_service: An initialized instance of the EmbeddingService.
        """
        self.cv_path = Path(cv_path)
        self.embedding_service = embedding_service
        self.cv_text: str | None = None
        self.cv_embedding: list[float] | None = None

    def load_cv(self) -> bool:
        """Load the CV text from the specified file path."""
        try:
            if not self.cv_path.is_file():
                logger.error(f"❌ CV file not found: {self.cv_path}")
                return False

            self.cv_text = self.cv_path.read_text(encoding="utf-8").strip()

            if not self.cv_text:
                logger.error(f"❌ CV file is empty: {self.cv_path}")
                return False

            logger.info(f"✅ CV loaded successfully ({len(self.cv_text)} characters).")
            return True
        except (OSError, FileNotFoundError) as e:
            logger.error(f"❌ Error reading CV file at {self.cv_path}: {e}", exc_info=True)
            return False

    def create_cv_embedding(self) -> bool:
        """Create an embedding for the loaded CV text."""
        if self.cv_text is None:
            logger.error("Cannot create embedding: CV text is not loaded.")
            return False

        logger.info("🔄 Creating CV embedding...")
        self.cv_embedding = self.embedding_service.create_embedding(self.cv_text)

        if self.cv_embedding:
            logger.info(f"✅ CV embedding created (dimensions: {len(self.cv_embedding)}).")
            return True
        else:
            logger.error("❌ Failed to create CV embedding.")
            return False

    def get_cv_embedding(self) -> list[float] | None:
        """Return the CV embedding, creating it if it doesn't exist."""
        if self.cv_embedding is None:
            if self.cv_text is None:
                self.load_cv()
            self.create_cv_embedding()
        return self.cv_embedding

    def get_cv_text(self) -> str | None:
        """Return the CV text, loading it if it hasn't been."""
        if self.cv_text is None:
            self.load_cv()
        return self.cv_text
