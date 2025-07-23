# src/cv_analyzer.py
"""CV Analyzer for Akilli Kariyer Asistani.
This module provides functionality to analyze CV text using Gemini AI,
extract key metadata, and cache results for efficient reuse.
It includes methods for normalizing skills, cleaning job titles,
and categorizing skills by importance.
"""

from __future__ import annotations

# Standard Library
import hashlib
import json
import logging
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

try:
    import google.generativeai as genai
    from google.api_core import exceptions as google_exceptions

    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    genai = None
    google_exceptions = None

from dotenv import load_dotenv

# Third Party
from tenacity import retry, stop_after_attempt, wait_fixed

from .config import get_config
from .core.constants import PROMPTS_DIR
from .utils.json_helpers import extract_json_from_response
from .utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

try:
    load_dotenv(dotenv_path=PROMPTS_DIR.parent / ".env")
except OSError:
    logger.exception("Failed to load .env file")
config = get_config()

# Prompt versioning for cache invalidation
PROMPT_VERSION = config.get("cv_analyzer_settings", {}).get("prompt_version", "v1")
TOKEN_LIMIT = config.get("cv_analyzer_settings", {}).get("token_limit", 4000)

SKILL_BLACKLIST = {
    "ms office",
    "microsoft office",
    "word",
    "excel",
    "powerpoint",
    "windows",
    "email",
    "internet",
    "computer",
    "keyboard",
    "office",
}
NORMALIZED_BLACKLIST = {s.replace(" ", "").replace("-", "") for s in SKILL_BLACKLIST}

# Lazy loading için prompt template'i module level'da yükleme
_PROMPT_TEMPLATE: str | None = None


def _get_prompt_template() -> str:
    """Lazy load prompt template to avoid module-level I/O operations."""
    global _PROMPT_TEMPLATE
    if _PROMPT_TEMPLATE is None:
        try:
            _PROMPT_TEMPLATE = load_prompt(PROMPTS_DIR / "cv_analysis_prompt.md")
        except OSError as e:
            logger.error(f"Failed to load prompt template: {e}")
            _PROMPT_TEMPLATE = """Analyze the provided CV text and extract key metadata in JSON format.

CV Text:
{cv_text}

Respond with a JSON object containing:
- "key_skills": A list of the top 10-15 most important technical and soft skills.
- "target_job_titles": A list of 3-5 suitable job titles for the candidate.
- "skill_importance": A list of floats (0.0 to 1.0) corresponding to the importance of each skill in "key_skills".
- "cv_summary": A 2-3 sentence summary of the candidate's profile.
"""
    return _PROMPT_TEMPLATE


# Persona count validation
MAX_RETRIES = 3
MIN_PERSONAS = 12
MAX_PERSONAS = 16


class CVAnalyzer:
    """Analyze CV text using Gemini AI and cache the results."""

    def __init__(self, model=None, cache_dir: Path | None = None) -> None:
        if model is None:
            if not HAS_GEMINI:
                raise ImportError(
                    "google.generativeai is not available. Please install it with: pip install google-generativeai"
                )

            config = get_config()
            api_key = config.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")

            genai.configure(api_key=api_key)  # type: ignore
            model = genai.GenerativeModel("gemini-1.5-flash-latest")  # type: ignore

        self.model = model
        self.cache_dir = cache_dir or Path("data")
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, cv_text: str) -> str:
        # Include prompt version to invalidate cache when prompt changes
        content_hash = hashlib.sha256(cv_text.encode("utf-8")).hexdigest()[:16]
        return f"{PROMPT_VERSION}_{content_hash}"

    def _load_cached_metadata(self, cv_text: str) -> dict | None:
        cache_key = self._get_cache_key(cv_text)
        cache_file = self.cache_dir / f"meta_{cache_key}.json"
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)

            # Ensure we actually got a dict
            if not isinstance(data, dict):
                logger.warning("Cached data is not a dictionary")
                return None
            ts = str(data.get("generated_at", ""))
            if ts:
                try:
                    generated_at = datetime.fromisoformat(ts)
                    if datetime.now(UTC) - generated_at <= timedelta(days=7):
                        metadata = data.get("metadata", data)
                        if isinstance(metadata, dict):
                            return cast(dict[str, object], metadata)
                except ValueError as dt_error:
                    logger.warning("Invalid datetime format in cache: %s", dt_error)
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.exception("Cache load failed: %s", e)
        return None

    def _cache_metadata(self, cv_text: str, metadata: dict) -> None:
        cache_key = self._get_cache_key(cv_text)
        cache_file = self.cache_dir / f"meta_{cache_key}.json"
        cache_data = {
            "metadata": metadata,
            "generated_at": datetime.now(UTC).isoformat(),
            "cv_hash": cache_key,
        }
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except (OSError, TypeError) as e:
            logger.exception("Cache write failed: %s", e)

    def _normalize_skills(self, skills: list[str]) -> list[str]:
        normalized = []
        for skill in skills or []:
            # Clean skill for comparison with normalized blacklist
            clean_skill_for_output = skill.lower().strip()
            clean_skill_for_comparison = clean_skill_for_output.replace(" ", "").replace("-", "")

            if clean_skill_for_comparison not in NORMALIZED_BLACKLIST and len(clean_skill_for_output) > 2:
                normalized.append(clean_skill_for_output)
        return sorted(set(normalized))

    def _clean_job_titles(self, job_titles: list[str]) -> list[str]:
        """Clean and normalize job titles."""
        cleaned = []
        for title in job_titles:
            # Fix common formatting issues
            clean_title = title.strip()
            # Remove parentheses and content for snake_case compliance
            clean_title = re.sub(r"\s*\([^)]*\)", "", clean_title)
            # Convert to proper title case
            clean_title = clean_title.title()
            # Handle specific cases where title() might not be ideal (e.g., acronyms)
            # Add more specific rules here if needed

            cleaned.append(clean_title)
        return cleaned

    def _categorize_skills_by_importance(self, skills: list[str], importance: list[float]) -> dict[str, list[str]]:
        """Categorize skills by importance levels for scoring system integration."""
        if len(skills) != len(importance):
            logger.warning(f"Skill count ({len(skills)}) != importance count ({len(importance)})")
            importance = (
                importance[: len(skills)]
                if len(importance) > len(skills)
                else importance + [0.7] * (len(skills) - len(importance))
            )

        categorized: dict[str, list[str]] = {"core": [], "secondary": [], "familiar": []}

        for skill, score in zip(skills, importance, strict=True):
            if score >= 0.85:
                categorized["core"].append(skill)
            elif score >= 0.7:
                categorized["secondary"].append(skill)
            else:
                categorized["familiar"].append(skill)

        return categorized

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=False)
    def _make_gemini_request(self, prompt: str) -> str:
        """Handle single API call to Gemini."""
        response = self.model.generate_content(prompt)
        return response.text if hasattr(response, "text") else str(response)

    def _validate_persona_count(self, data: dict) -> bool:
        """Validate persona count is within acceptable range."""
        personas = data.get("search_personas", [])
        return MIN_PERSONAS <= len(personas) <= MAX_PERSONAS

    def _call_gemini_with_retry(self, cv_text: str) -> dict | None:
        """Orchestrate retries for Gemini API calls with persona count validation."""
        truncated = cv_text[:TOKEN_LIMIT]
        prompt = _get_prompt_template().format(cv_text=truncated)
        logger.debug(f"Sending prompt to Gemini: {prompt[:200]}...")

        last_parsed_data = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                content = self._make_gemini_request(prompt)
                logger.debug(f"Gemini response (attempt {attempt}): {content[:200]}...")

                if not content or content.strip() == "":
                    logger.warning(f"Gemini returned empty response (attempt {attempt})")
                    continue

                parsed_data = extract_json_from_response(content)
                if parsed_data is None:
                    logger.warning(f"Could not extract JSON from Gemini response (attempt {attempt}): {content[:500]}")
                    continue

                last_parsed_data = parsed_data

                if self._validate_persona_count(parsed_data):
                    personas = parsed_data.get("search_personas", [])
                    logger.info(f"✅ Received {len(personas)} personas (target: {MIN_PERSONAS}-{MAX_PERSONAS})")
                    return cast(dict, parsed_data)

                personas = parsed_data.get("search_personas", [])
                logger.warning(
                    f"Gemini returned {len(personas)} personas (need {MIN_PERSONAS}-{MAX_PERSONAS}). Retrying {attempt}/{MAX_RETRIES}"
                )

            except Exception as e:
                logger.warning(f"API call attempt {attempt} failed: {e}")
                if attempt == MAX_RETRIES:
                    raise

        # Return last attempt even if persona count is not ideal
        if last_parsed_data:
            personas = last_parsed_data.get("search_personas", [])
            logger.warning(f"After {MAX_RETRIES} attempts, using response with {len(personas)} personas")
            return cast(dict, last_parsed_data)

        return None

    def _call_gemini_api(self, cv_text: str) -> dict | None:
        """Main entry point for Gemini API calls with error handling."""
        try:
            return self._call_gemini_with_retry(cv_text)
        except Exception as e:
            if google_exceptions and isinstance(e, google_exceptions.ResourceExhausted):
                logger.exception("Gemini API Quota Exceeded")
                return None
            logger.exception("An unexpected Gemini API call failed")
            raise

    def _validate_and_normalize_metadata(self, metadata: dict[str, object]) -> dict[str, object] | None:
        """Validate and normalize metadata extracted from the CV."""
        # We can be flexible with missing keys, but log it
        required_keys = ["key_skills", "skill_importance", "cv_summary"]
        optional_keys = ["target_job_titles", "search_personas"]

        if not all(key in metadata for key in required_keys):
            logger.warning(f"AI response is missing one of a required key. Found: {list(metadata.keys())}")

        # At least one of these should exist for persona generation
        has_personas = any(key in metadata for key in optional_keys)
        if not has_personas:
            logger.error("AI response missing both target_job_titles and search_personas")
            return None

        # ---------- SKILLS ----------
        skills = self._normalize_skills(cast(list[str], metadata.get("key_skills", [])))
        importance = cast(list[float], metadata.get("skill_importance", []))

        # Ensure skill_importance matches skills length
        if len(importance) != len(skills):
            logger.warning(
                f"skill_importance length ({len(importance)}) doesn't match skills ({len(skills)}), padding with 0.8"
            )
            importance = importance[: len(skills)] + [0.8] * (len(skills) - len(importance))

        metadata["skill_importance"] = importance
        metadata["key_skills"] = skills

        # ---------- SEARCH PERSONAS ----------
        personas = cast(list[dict[str, object]], metadata.get("search_personas", []))
        if not isinstance(personas, list):
            logger.error("search_personas is not a list")
            return None

        # quick sanity filter: keep only items with mandatory keys
        cleaned_personas: list[dict[str, object]] = []
        for p in personas:
            if not isinstance(p, dict):
                continue
            if {"primary_title_en", "primary_title_tr", "search_keywords"} <= p.keys():
                cleaned_personas.append(p)
        metadata["search_personas"] = cleaned_personas

        return metadata

    def extract_metadata_from_cv(self, cv_text: str) -> dict[str, object]:
        cached = self._load_cached_metadata(cv_text)
        if cached:
            logger.info("Using cached CV metadata")
            return cached

        data = self._call_gemini_api(cv_text)
        if data:
            # Validate and normalize the data from the API
            normalized_metadata = self._validate_and_normalize_metadata(cast(dict[str, object], data))

            if normalized_metadata:
                self._cache_metadata(cv_text, normalized_metadata)
                skills = cast(list[str], normalized_metadata.get("key_skills", []))
                job_titles = cast(list[str], normalized_metadata.get("target_job_titles", []))
                logger.info(f"Extracted {len(skills)} skills and {len(job_titles)} job titles from CV")
                return normalized_metadata

        logger.warning("Gemini API failed or returned invalid data, using empty metadata")
        return {
            "key_skills": [],
            "target_job_titles": [],
            "skill_importance": [],
            "cv_summary": "",
        }
