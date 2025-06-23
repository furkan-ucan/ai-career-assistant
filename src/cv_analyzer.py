"""CV Analyzer: Extract key skills and job titles from CV text.

This module provides basic CV analysis with caching and skill normalization.
"""

# Standard Library
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

SKILL_BLACKLIST = {
    "ms office",
    "msoffice",
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

COMMON_SKILLS = {
    "python",
    "sql",
    "react",
    "javascript",
    "project management",
    "data analysis",
    "powerbi",
    "tableau",
}

COMMON_TITLES = {"developer", "analyst", "engineer", "consultant"}


class CVAnalyzer:
    """Analyze CV text and cache extracted metadata."""

    def __init__(self, cache_dir: str | Path = "data", token_limit: int = 4000) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.token_limit = token_limit

    # Caching utilities
    def get_cache_key(self, cv_text: str) -> str:
        return hashlib.sha256(cv_text.encode("utf-8")).hexdigest()[:16]

    def _cache_file(self, cv_text: str) -> Path:
        return self.cache_dir / f"meta_{self.get_cache_key(cv_text)}.json"

    def load_cached_metadata(self, cv_text: str) -> Optional[dict]:
        path = self._cache_file(cv_text)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            ts = data.get("generated_at")
            if ts and datetime.now() - datetime.fromisoformat(ts) < timedelta(days=7):
                logger.info("♻️  Önbellekten CV verisi kullanıldı")
                return data
        except Exception as e:  # noqa: BLE001
            logger.error("Önbellek okunamadı: %s", e, exc_info=True)
        return None

    def cache_metadata(self, cv_text: str, metadata: dict) -> None:
        cache_data = {
            "metadata": metadata,
            "generated_at": datetime.now().isoformat(),
            "cv_hash": self.get_cache_key(cv_text),
        }
        path = self._cache_file(cv_text)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info("📁 CV analizi önbelleğe kaydedildi: %s", path)

    # Normalization helpers
    def normalize_skills(self, skills: List[str]) -> List[str]:
        normalized = []
        for skill in skills:
            clean = skill.lower().replace(" ", "").replace("-", "")
            if clean not in SKILL_BLACKLIST and len(clean) > 2:
                normalized.append(clean)
        # Remove duplicates
        return list(set(normalized))

    def extract_metadata_from_cv(self, cv_text: str) -> dict:
        if not cv_text:
            return {"key_skills": [], "target_job_titles": []}
        cached = self.load_cached_metadata(cv_text)
        if cached:
            return cached["metadata"]

        text = cv_text[: self.token_limit]
        skills_found = [s for s in COMMON_SKILLS if s.lower() in text.lower()]
        titles_found = [t.title() for t in COMMON_TITLES if t.lower() in text.lower()]
        metadata = {
            "key_skills": self.normalize_skills(skills_found),
            "target_job_titles": titles_found,
        }
        self.cache_metadata(cv_text, metadata)
        return metadata


if __name__ == "__main__":  # Simple manual test
    sample_text = "Python developer with SQL and React experience. Proficient in PowerBI."
    analyzer = CVAnalyzer()
    meta = analyzer.extract_metadata_from_cv(sample_text)
    logger.info("Extracted metadata: %s", meta)
