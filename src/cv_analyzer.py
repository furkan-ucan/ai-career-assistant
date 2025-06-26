from __future__ import annotations

# Standard Library
import hashlib
import json
import logging
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import google.generativeai as genai
from dotenv import load_dotenv

# Third Party
from tenacity import retry, stop_after_attempt, wait_fixed

from .config import get_config
from .constants import PROMPTS_DIR
from .utils.prompt_loader import load_prompt

load_dotenv(dotenv_path=PROMPTS_DIR.parent / ".env")

logger = logging.getLogger(__name__)

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

PROMPT_TEMPLATE = load_prompt(PROMPTS_DIR / "cv_analysis_prompt.md")


class CVAnalyzer:
    """Analyze CV text using Gemini AI and cache the results."""

    def __init__(self) -> None:
        config = get_config()
        api_key = config.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.cache_dir = Path("data")
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
                data = cast(dict[str, object], json.load(f))
            ts = str(data.get("generated_at", ""))
            if ts:
                generated_at = datetime.fromisoformat(ts)
                if datetime.now(UTC) - generated_at <= timedelta(days=7):
                    return cast(dict[str, object], data.get("metadata", data))
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

    def _strip_markdown_fences(self, content: str) -> str:
        """Remove markdown code fences from JSON response."""
        # Remove code fences with various languages
        content = re.sub(r"^```[a-zA-Z]*\n", "", content, flags=re.MULTILINE)
        content = re.sub(r"\n\s*```$", "", content, flags=re.MULTILINE)
        return content.strip()

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
            if clean_title.upper() == "SENIOR DEVELOPER":
                clean_title = "Senior Developer"

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
    def _call_gemini_api(self, cv_text: str) -> dict | None:
        try:
            truncated = cv_text[:TOKEN_LIMIT]
            prompt = PROMPT_TEMPLATE.format(cv_text=truncated)
            logger.debug(f"Sending prompt to Gemini: {prompt[:200]}...")

            response = self.model.generate_content(prompt)
            content = response.text if hasattr(response, "text") else str(response)

            logger.debug(f"Gemini response: {content[:200]}...")

            if not content or content.strip() == "":
                logger.warning("Gemini returned empty response")
                return None

            # Clean JSON from markdown code blocks - enhanced version
            content = self._strip_markdown_fences(content)

            # Additional cleanup for common issues
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove closing ```
            content = content.strip()

            parsed_data = cast(dict[str, object], json.loads(content))

            # Validate required fields
            if "key_skills" not in parsed_data or "target_job_titles" not in parsed_data:
                logger.warning("Gemini response missing required fields")
                return None

            return parsed_data
        except json.JSONDecodeError as e:
            logger.error(
                f"Gemini JSON decode error: {e}. Response was: {content[:500] if 'content' in locals() else 'No content'}"
            )
            return None
        except Exception:  # noqa: BLE001
            logger.exception("Gemini API call failed")
            return None

    def extract_metadata_from_cv(self, cv_text: str) -> dict[str, object]:
        cached = self._load_cached_metadata(cv_text)
        if cached:
            logger.info("Using cached CV metadata")
            return cached

        data = self._call_gemini_api(cv_text)
        if data is not None:
            metadata = cast(dict[str, object], data)

            # Normalize skills
            skills = self._normalize_skills(cast(list[str], metadata.get("key_skills", [])))
            metadata["key_skills"] = skills

            # Ensure skill_importance matches skills length
            importance = cast(list[float], metadata.get("skill_importance", []))
            if len(importance) != len(skills):
                logger.warning(
                    f"skill_importance length ({len(importance)}) doesn't match skills ({len(skills)}), padding with 0.8"
                )
                importance = importance[: len(skills)] + [0.8] * (len(skills) - len(importance))
            metadata["skill_importance"] = importance

            cv_summary = cast(str, metadata.get("cv_summary", ""))
            metadata["cv_summary"] = cv_summary.strip()

            self._cache_metadata(cv_text, metadata)
            job_titles = cast(list[str], metadata.get("target_job_titles", []))
            logger.info(f"Extracted {len(skills)} skills and {len(job_titles)} job titles from CV")
            return metadata

        logger.warning("Gemini API failed, using empty metadata")
        return {
            "key_skills": [],
            "target_job_titles": [],
            "skill_importance": [],
            "cv_summary": "",
        }
