from __future__ import annotations

# Standard Library
import hashlib
import json
import logging
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import google.generativeai as genai

# Third Party
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

# Prompt versioning for cache invalidation
PROMPT_VERSION = "v1.1"

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

PROMPT_TEMPLATE = """
**ROLE:** You are an *expert* Career Strategist for **Management Information
Systems (MIS / YBS)** professionals who also possess strong full-stack and data
science skills.

**PRIME DIRECTIVE:** The candidate is an MIS student—not a pure software
developer.  Your analysis *must* prioritise business-technology bridge roles
(e.g. ERP consultant, process analyst).  Failing to do so is a critical error.

**CONTEXT (read carefully):**
• Strong full-stack: NestJS, React, TypeScript, Flutter
• Advanced data analytics & ML (Python / Pandas / XGBoost)
• ERP & Business-Process focus (SAP, requirement & process improvement)
• GIS niche (QGIS, PostGIS, Leaflet.js)

**RESUME TEXT:**
---
{cv_text}
---

**TASK – Return **ONLY** a raw JSON object (no markdown, no commentary).**

1. `"key_skills"`   📋 *array [str]* – top 20-25 skills, ordered by PRIORITY.
   * **PRIORITY 1 (MUST include):** MIS/Business/Process Skills -> ERP, SAP,
     business_process_improvement, system_analysis, requirement_analysis,
     agile, scrum, project_management
   * **PRIORITY 2:** Core Software & Data Tech -> nestjs, react, python,
     typescript, postgresql, data_analysis, machine_learning
   * **PRIORITY 3 (Niche/Supporting):** GIS / Geospatial Skills -> gis, qgis,
     postgis, leafletjs
   * Normalise: lowercase, snake_case, no spaces/dashes (`"process_improvement"`).

2. `"target_job_titles"`   🎯 *array [str]* – 12-16 junior / entry / associate
   titles **ordered by best fit**.
   **≥ 60 %** of items *must* be MIS / Business / ERP / Data focused. Software roles are secondary.
   Mandatory buckets (if CV supports):
   - Business / Process Roles: “Business Analyst”, “Process Analyst”,
     “Business Systems Analyst”, “Junior Project Manager”
   - ERP / Consulting Roles: “Junior ERP Consultant”, “IT Consultant”
   - Hybrid Roles: “Technical Business Analyst”, “Data Analyst”
   - Dev Roles (max 30-40 %): “Full-Stack Developer”, “Mobile Developer (Flutter)”
   - **GIS Roles (if any, place at the end of the list):** “GIS Specialist”

3. `"skill_importance"`   ⭐ *array [float]* – same length as `key_skills`,
   values 0.00-1.00 (2 decimals).  Reflect how central the skill is to the
   candidate’s profile & projects.

**JSON SCHEMA (enforced):**
{{
  "type": "object",
  "properties": {{
    "key_skills":        {{"type": "array", "items": {{"type": "string"}}}},
    "target_job_titles": {{"type": "array", "items": {{"type": "string"}}}},
    "skill_importance":  {{"type": "array", "items": {{"type":"number"}}}}
  }},
  "required": ["key_skills", "target_job_titles", "skill_importance"]
}}

**ABSOLUTE RULES:**
* Do **NOT** wrap the JSON with ``` or any extra text.
* Exclude generic office basics (“ms office”, “excel”, “windows”, …).
* Ensure array lengths match; ordering in `key_skills` ↔ `skill_importance`
  must correspond.
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
            # Keep snake_case format, just lowercase and clean
            clean_skill = skill.lower().strip()
            if clean_skill not in NORMALIZED_BLACKLIST and len(clean_skill) > 2:
                normalized.append(clean_skill)
        return sorted(set(normalized))

    def _strip_markdown_fences(self, content: str) -> str:
        """Remove markdown code fences from JSON response."""
        # Remove code fences with various languages
        content = re.sub(r"^```[a-zA-Z]*\n", "", content, flags=re.MULTILINE)
        content = re.sub(r"\n```$", "", content, flags=re.MULTILINE)
        return content.strip()

    def _clean_job_titles(self, job_titles: list[str]) -> list[str]:
        """Clean and normalize job titles."""
        import re

        cleaned = []
        for title in job_titles:
            # Fix common formatting issues
            clean_title = title.strip()
            # Remove parentheses and content for snake_case compliance
            clean_title = re.sub(r"\s*\([^)]*\)", "", clean_title)
            # Convert to proper title case if needed
            if clean_title.islower() or "_" in clean_title:
                clean_title = clean_title.replace("_", " ").title()

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

        for skill, score in zip(skills, importance, strict=False):
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
            truncated = cv_text[:4000]
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

            self._cache_metadata(cv_text, metadata)
            job_titles = cast(list[str], metadata.get("target_job_titles", []))
            logger.info(f"Extracted {len(skills)} skills and {len(job_titles)} job titles from CV")
            return metadata

        logger.warning("Gemini API failed, using empty metadata")
        return {"key_skills": [], "target_job_titles": [], "skill_importance": []}
