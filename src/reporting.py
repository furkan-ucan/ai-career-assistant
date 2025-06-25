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
    if mk:
        logger.info("   ✅ Eşleşen: %s", ", ".join(mk))
    miss = job.get("missing_keywords")
    if miss:
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
    """Log formatted job search results."""
    if similar_jobs:
        logger.info("✅ %s adet yüksek kaliteli pozisyon bulundu!", len(similar_jobs))
        logger.info("📊 Uygunluk eşiği: %%%.0f ve üzeri", threshold)
        logger.info("\n" + "=" * 70)
        logger.info("🎉 SİZE ÖZEL EN UYGUN İŞ İLANLARI (JobSpy Optimize)")
        logger.info("🎯 YBS + Full-Stack + Veri Analizi Odaklı")
        logger.info("=" * 70)
        for i, job in enumerate(similar_jobs[:15], 1):
            _log_single_job_details(job, i)
        logger.info("\n🎯 Analiz tamamlandı! %s yüksek kaliteli pozisyon listelendi.", len(similar_jobs))
        _log_persona_distribution(similar_jobs)
    else:
        logger.warning("⚠️  0 ilan bulundu veya uygunluk eşiği (%%%.0f) altında.", threshold)
        logger.info("💡 Eşiği düşürmeyi veya persona terimlerini genişletmeyi düşünebilirsiniz.")


def log_summary_statistics(
    all_jobs_df: pd.DataFrame, high_quality_jobs: list[dict], ai_metadata: dict | None = None
) -> None:
    """Logs summary statistics about the job search process."""
    logger.info("\n📊 Özet İstatistikler:")

    _log_site_distribution(all_jobs_df)
    _log_top_skills(high_quality_jobs, ai_metadata)
    _log_persona_success(high_quality_jobs)


def _log_site_distribution(all_jobs_df: pd.DataFrame) -> None:
    """Log site distribution statistics."""
    if not all_jobs_df.empty and "source_site" in all_jobs_df.columns:
        logger.info("\n🔹 Bulunan İlanların Site Dağılımı:")
        for site, count in all_jobs_df["source_site"].value_counts().items():
            logger.info(SITE_COUNT_FORMAT, site, count)


def _log_top_skills(high_quality_jobs: list[dict], ai_metadata: dict | None = None) -> None:
    """Log top skills based on AI metadata (priority) or matching keywords."""
    # Priority 1: Use key skills from AI metadata (user's CV)
    if ai_metadata and ai_metadata.get("key_skills"):
        logger.info("\n🔹 En Önemli Yetenekleriniz (CV'nize Göre):")
        key_skills = ai_metadata.get("key_skills", [])
        skill_importance = ai_metadata.get("skill_importance")

        for i, skill in enumerate(key_skills[:5]):
            if skill_importance and i < len(skill_importance):
                logger.info("   - %s (Önem: %.2f)", skill, skill_importance[i])
            else:
                logger.info("   - %s", skill)
        return

    # Priority 2: Fallback to most common matching keywords from jobs
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


def _log_persona_success(high_quality_jobs: list[dict]) -> None:
    """Log persona success statistics."""
    if not high_quality_jobs:
        return

    persona_counts = Counter(job.get("persona_source") for job in high_quality_jobs if job.get("persona_source"))

    if persona_counts:
        logger.info("\n🔹 En Başarılı Personalar:")
        for persona, count in persona_counts.most_common():
            logger.info(SITE_COUNT_FORMAT, persona, count)


__all__ = ["display_results", "log_summary_statistics"]
