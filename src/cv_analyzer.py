# src/cv_analyzer.py
"""CV Analyzer using Gemini AI, refactored for dependency injection and clarity."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from tenacity import retry, stop_after_attempt, wait_fixed

from .core.constants import PROMPTS_DIR
from .utils.json_helpers import extract_json_from_response
from .utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

# Lazy loading for the prompt template to avoid module-level I/O
_PROMPT_TEMPLATE: str | None = None


def _get_prompt_template() -> str:
    """Lazy load and return the CV analysis prompt template."""
    global _PROMPT_TEMPLATE
    if _PROMPT_TEMPLATE is None:
        try:
            _PROMPT_TEMPLATE = load_prompt(PROMPTS_DIR / "cv_analysis_prompt.md")
        except OSError as e:
            logger.error(f"Failed to load CV analysis prompt: {e}")
            # Fallback prompt in case of file error
            _PROMPT_TEMPLATE = """Analyze the CV: {cv_text}. Extract key_skills, target_job_titles, skill_importance, cv_summary in JSON."""
    return _PROMPT_TEMPLATE


class CVAnalyzer:
    """Analyzes CV text using Gemini AI and caches the results."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-1.5-flash-latest",
        cache_dir: Path | None = None,
        prompt_version: str = "v2",
    ):
        """
        Initializes the CVAnalyzer with necessary dependencies.

        Args:
            api_key: The Google Gemini API key.
            model_name: The name of the generative model to use.
            cache_dir: The directory to store cached analysis results.
            prompt_version: A version string for the prompt to invalidate cache on change.
        """
        if not api_key:
            raise ValueError("Gemini API key is required.")

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Model: {e}")
            raise ValueError("Could not configure or create the GenerativeModel.") from e

        self.cache_dir = cache_dir or Path("data")
        self.cache_dir.mkdir(exist_ok=True)
        self.prompt_version = prompt_version
        self.token_limit = 4000  # A safe limit for most models

    def _get_cache_key(self, cv_text: str) -> str:
        """Generate a unique cache key based on CV content and prompt version."""
        content_hash = hashlib.sha256(cv_text.encode("utf-8")).hexdigest()[:16]
        return f"cv_meta_{self.prompt_version}_{content_hash}.json"

    def _load_from_cache(self, key: str) -> dict[str, Any] | None:
        """Load analysis result from a cache file if it exists and is valid."""
        cache_file = self.cache_dir / key
        if not cache_file.is_file():
            return None

        try:
            with cache_file.open("r", encoding="utf-8") as f:
                cached_data = json.load(f)

            # Check cache age (e.g., 7 days)
            generated_at = datetime.fromisoformat(cached_data.get("generated_at", ""))
            if datetime.now(UTC) - generated_at <= timedelta(days=7):
                logger.info(f"Cache hit: Loading analysis from {key}")
                return cast(dict[str, Any], cached_data.get("metadata"))
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Cache read failed for key {key}: {e}")

        return None

    def _save_to_cache(self, key: str, metadata: dict[str, Any]) -> None:
        """Save an analysis result to a cache file."""
        cache_file = self.cache_dir / key
        cache_data = {
            "metadata": metadata,
            "generated_at": datetime.now(UTC).isoformat(),
            "prompt_version": self.prompt_version,
        }
        try:
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except (OSError, TypeError) as e:
            logger.error(f"Cache write failed for key {key}: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def _make_gemini_request(self, prompt: str) -> str:
        """Make a single, retriable API call to Gemini."""
        response = self.model.generate_content(prompt)
        return response.text if hasattr(response, "text") else str(response)

    def _call_gemini_api(self, cv_text: str) -> dict[str, Any] | None:
        """Orchestrate the Gemini API call and response parsing."""
        truncated_cv = cv_text[: self.token_limit]
        prompt = _get_prompt_template().format(cv_text=truncated_cv)

        try:
            response_text = self._make_gemini_request(prompt)
            if not response_text:
                logger.warning("Gemini API returned an empty response.")
                return None
            return extract_json_from_response(response_text)
        except google_exceptions.ResourceExhausted:
            logger.error("Gemini API quota exceeded. Please check your billing or usage limits.")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occurred during the Gemini API call: {e}")
            return None

    def extract_metadata_from_cv(self, cv_text: str) -> dict[str, Any]:
        """
        Main method to extract, validate, and cache metadata from CV text.
        """
        if not cv_text:
            return {}

        cache_key = self._get_cache_key(cv_text)
        cached_metadata = self._load_from_cache(cache_key)
        if cached_metadata:
            return cached_metadata

        logger.info("No valid cache found. Analyzing CV with Gemini AI...")
        raw_metadata = self._call_gemini_api(cv_text)

        if not raw_metadata or not isinstance(raw_metadata, dict):
            logger.error("Failed to get valid metadata from Gemini API.")
            return {}

        # The validation and normalization logic can be expanded here
        # For now, we assume the structure is mostly correct.
        self._save_to_cache(cache_key, raw_metadata)
        return raw_metadata
