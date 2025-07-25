# src/reporting.py
"""Reporting utilities for presenting final job results."""

from __future__ import annotations

import logging
from collections import Counter

import pandas as pd

logger = logging.getLogger(__name__)
# Constants
SITE_COUNT_FORMAT = "   %s: %s ilan"


def _log_single_job_details(job: dict, index: int) -> None:
    """Logs the detailed information for a single job."""
    logger.info(
        "\n%d. %s - %s",
        index,
        job.get("title", "Başlık belirtilmemiş"),
        job.get("company", "Şirket belirtilmemiş"),
    )
    logger.info("   📍 %s", job.get("location", "Lokasyon belirtilmemiş"))
    score = job.get("fit_score", job.get("match_score", job.get("similarity_score", 0)))
    logger.info("   📊 Uygunluk: %.1f", score)
    reasoning = job.get("reasoning")
    if reasoning:
        logger.info("   💡 %s", reasoning)
    mk = job.get("matching_keywords")
    if mk and isinstance(mk, list):
        logger.info("   ✅ Eşleşen: %s", ", ".join(mk))
    miss = job.get("missing_keywords")
    if miss and isinstance(miss, list):
        logger.info("   ❌ Eksik: %s", ", ".join(miss))
    logger.info("   💼 Site: %s", job.get("source_site", job.get("site", "Site belirtilmemiş")))
    logger.info("   👤 Persona: %s", job.get("persona_source", job.get("persona", "Persona belirtilmemiş")))
    logger.info("   🔗 %s", job.get("url", job.get("job_url", "URL bulunamadı")))
    logger.info("-" * 50)


def _log_persona_distribution(similar_jobs: list[dict]) -> None:
    """Logs the distribution of personas among similar jobs."""
    if similar_jobs and ("persona_source" in similar_jobs[0] or "persona" in similar_jobs[0]):
        persona_counts: dict[str, int] = {}
        for job in similar_jobs:
            persona = job.get("persona_source", job.get("persona", "Unknown"))
            persona_counts[persona] = persona_counts.get(persona, 0) + 1

        logger.info("\n📈 Persona Dağılımı:")
        for persona, count in sorted(persona_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(SITE_COUNT_FORMAT, persona, count)


def display_results(similar_jobs: list[dict], threshold: float) -> None:
    """Log formatted job search results with URL-based deduplication."""
    if not (0 <= threshold <= 100):
        logger.warning("Threshold should be between 0-100, got: %.1f", threshold)
        return

    try:
        if similar_jobs:
            # Deduplicate by URL - keep the highest scoring job for each URL
            deduplicated_jobs = _deduplicate_jobs_by_url(similar_jobs)

            original_count = len(similar_jobs)
            deduplicated_count = len(deduplicated_jobs)

            logger.info("✅ %s adet yüksek kaliteli pozisyon bulundu!", original_count)
            if original_count != deduplicated_count:
                logger.info(
                    "🔗 %s tekrar ilan URL'ye göre temizlendi (%s benzersiz ilan kaldı)",
                    original_count - deduplicated_count,
                    deduplicated_count,
                )

            logger.info("📊 Uygunluk eşiği: %%%.0f ve üzeri", threshold)
            logger.info("\n" + "=" * 70)
            logger.info("🎉 SİZE ÖZEL EN UYGUN İŞ İLANLARI (JobSpy Optimize)")
            logger.info("🎯 YBS + Full-Stack + Veri Analizi Odaklı")
            logger.info("=" * 70)
    except Exception:
        logger.exception("Failed to display job results")

        # Display up to 15 deduplicated jobs
        for i, job in enumerate(deduplicated_jobs[:15], 1):
            _log_single_job_details(job, i)

        logger.info(
            "\n🎯 Analiz tamamlandı! %s benzersiz yüksek kaliteli pozisyon listelendi.", min(15, deduplicated_count)
        )
        _log_persona_distribution(deduplicated_jobs)
    else:
        logger.warning("⚠️  0 ilan bulundu veya uygunluk eşiği (%%%.0f) altında.", threshold)
        logger.info("💡 Eşiği düşürmeyi veya persona terimlerini genişletmeyi düşünebilirsiniz.")


def log_summary_statistics(
    all_jobs_df: pd.DataFrame, high_quality_jobs: list[dict], ai_metadata: dict | None = None
) -> None:
    """Logs summary statistics about the job search process."""
    logger.info("\n📊 Özet İstatistikler:")

    try:
        _log_site_distribution(all_jobs_df)
    except Exception:
        logger.exception("Exception in site distribution logging")

    try:
        _log_top_skills(high_quality_jobs, ai_metadata)
    except Exception:
        logger.exception("Exception in top skills logging")

    try:
        _log_persona_success(high_quality_jobs)
    except Exception:
        logger.exception("Exception in persona success logging")


def _log_site_distribution(all_jobs_df: pd.DataFrame) -> None:
    """Log site distribution statistics."""
    try:
        if not all_jobs_df.empty and "source_site" in all_jobs_df.columns:
            logger.info("\n🔹 Bulunan İlanların Site Dağılımı:")
            for site, count in all_jobs_df["source_site"].value_counts().items():
                logger.info(SITE_COUNT_FORMAT, site, count)
    except Exception:
        logger.exception("Site distribution logging failed")


def _log_cv_skills(ai_metadata: dict | None = None) -> bool:
    """Log CV-based skills from AI metadata."""
    try:
        if not ai_metadata or not ai_metadata.get("key_skills"):
            return False

        logger.info("\n🔹 En Önemli Yetenekleriniz (CV'nize Göre):")
        key_skills = ai_metadata.get("key_skills", [])
        skill_importance = ai_metadata.get("skill_importance")

        for i, skill in enumerate(key_skills[:5]):
            if skill_importance and i < len(skill_importance):
                logger.info("   - %s (Önem: %.2f)", skill, skill_importance[i])
            else:
                logger.info("   - %s", skill)
        return True
    except Exception:
        logger.exception("CV skills logging failed")
        return False


def _log_keyword_skills(high_quality_jobs: list[dict]) -> None:
    """Log keyword-based skills from job matching data."""
    try:
        keywords: list[str] = []
        for job in high_quality_jobs:
            kw = job.get("matching_keywords")
            if isinstance(kw, list):
                keywords.extend(kw)

        if keywords:
            counts = Counter(keywords)
            logger.info("\n🔹 En Popüler 5 Skill:")
            for skill, count in counts.most_common(5):
                logger.info(SITE_COUNT_FORMAT, skill, count)
    except Exception:
        logger.exception("Keyword skills logging failed")


def _log_top_skills(high_quality_jobs: list[dict], ai_metadata: dict | None = None) -> None:
    """Log top skills based on AI metadata (priority) or matching keywords."""
    # Priority 1: Use key skills from AI metadata (user's CV)
    if _log_cv_skills(ai_metadata):
        return

    # Priority 2: Fallback to most common matching keywords from jobs
    _log_keyword_skills(high_quality_jobs)


def _log_persona_success(high_quality_jobs: list[dict]) -> None:
    """Log persona success statistics with error handling."""
    try:
        if not high_quality_jobs:
            return

        persona_counts = Counter(job.get("persona_source") for job in high_quality_jobs if job.get("persona_source"))

        if persona_counts:
            logger.info("\n🔹 En Başarılı Personalar:")
            for persona, count in persona_counts.most_common():
                logger.info(SITE_COUNT_FORMAT, persona, count)
    except Exception:
        logger.exception("Exception occurred while logging persona success statistics")


def _get_job_score(job: dict) -> float:
    """
    Extract job score from job dictionary, checking multiple score keys in order.

    Args:
        job: Job dictionary that may contain various score fields

    Returns:
        Score value (default 0 if none found or on error)
    """
    try:
        if not isinstance(job, dict):
            return 0.0

        # Check score keys in order of preference
        score = job.get("fit_score", job.get("match_score", job.get("similarity_score", 0.0)))
        return float(score) if score is not None else 0.0
    except (TypeError, AttributeError, ValueError):
        return 0.0


def _deduplicate_jobs_by_url(jobs: list[dict]) -> list[dict]:
    """
    Deduplicate jobs by URL, keeping the job with the highest score for each URL.

    Args:
        jobs: List of job dictionaries

    Returns:
        List of deduplicated jobs, sorted by score descending
    """
    if not jobs:
        return []

    url_to_best_job: dict[str, dict] = {}

    for job in jobs:
        url = job.get("job_url", "").strip()
        if not url:
            # If no URL, treat as unique (shouldn't happen but safe fallback)
            unique_key = f"no_url_{id(job)}"
            url_to_best_job[unique_key] = job
            continue

        # Get the current best score for scoring comparison
        current_score = _get_job_score(job)

        if url not in url_to_best_job:
            # First job with this URL
            url_to_best_job[url] = job
        else:
            # Compare with existing job for this URL
            existing_job = url_to_best_job[url]
            existing_score = _get_job_score(existing_job)

            if current_score > existing_score:
                # Current job has higher score, replace
                url_to_best_job[url] = job

    # Return deduplicated jobs sorted by score descending
    deduplicated = list(url_to_best_job.values())
    deduplicated.sort(key=_get_job_score, reverse=True)

    return deduplicated


__all__ = ["display_results", "log_summary_statistics"]
