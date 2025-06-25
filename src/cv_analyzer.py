from __future__ import annotations

# Standard Library
import hashlib
import json
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import google.generativeai as genai

# Third Party
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

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
}
NORMALIZED_BLACKLIST = {s.replace(" ", "").replace("-", "") for s in SKILL_BLACKLIST}

PROMPT_TEMPLATE = """**Role:** Expert Technical Recruiter and Career Strategist
**Context:** Analyze Management Information Systems student resume (Turkish/English mixed)
**Task:** Extract structured data with skill normalization
**Skills Priority:** Technical skills > Soft skills > Tools
**Output:** Valid JSON with normalized keys (lowercase, no spaces)
{
  \"key_skills\": [\"python\", \"sql\", \"projectmanagement\", ...],
  \"target_job_titles\": [\"Junior Developer\", \"Business Analyst\", ...],
  \"skill_importance\": [0.9, 0.8, 0.7, ...] // Future enhancement
}
CV:\n{cv_text}"
"""


class CVAnalyzer:
    """Analyze CV text using Gemini AI and cache the results."""

    def __init__(self) -> None:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.cache_dir = Path("data")
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, cv_text: str) -> str:
        return hashlib.sha256(cv_text.encode("utf-8")).hexdigest()[:16]

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
        except Exception:  # noqa: BLE001
            logger.exception("Cache load failed")
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
        except Exception:  # noqa: BLE001
            logger.exception("Cache write failed")

    def _normalize_skills(self, skills: list[str]) -> list[str]:
        normalized = []
        for skill in skills or []:
            clean_skill = skill.lower().replace(" ", "").replace("-", "")
            if clean_skill not in NORMALIZED_BLACKLIST and len(clean_skill) > 2:
                normalized.append(clean_skill)
        return sorted(set(normalized))

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=False)
    def _call_gemini_api(self, cv_text: str) -> dict | None:
        try:
            truncated = cv_text[:4000]
            prompt = PROMPT_TEMPLATE.format(cv_text=truncated)
            response = self.model.generate_content(prompt)
            content = response.text if hasattr(response, "text") else str(response)
            return cast(dict[str, object], json.loads(content))
        except json.JSONDecodeError:
            logger.exception("Gemini JSON decode error")
            return None
        except Exception:  # noqa: BLE001
            logger.exception("Gemini API call failed")
            return None

    def extract_metadata_from_cv(self, cv_text: str) -> dict[str, object]:
        cached = self._load_cached_metadata(cv_text)
        if cached:
            return cached

        data = self._call_gemini_api(cv_text)
        if data is not None:
            metadata = cast(dict[str, object], data)
            skills = self._normalize_skills(cast(list[str], metadata.get("key_skills", [])))
            metadata["key_skills"] = skills
            self._cache_metadata(cv_text, metadata)
            return metadata

        logger.warning("Gemini API failed, using empty metadata")
        return {"key_skills": [], "target_job_titles": []}
