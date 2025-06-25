"""Reporting utilities for presenting final job results."""

from __future__ import annotations

import logging
from collections import Counter

import pandas as pd

logger = logging.getLogger(__name__)

# Constants
SITE_COUNT_FORMAT = "   %s: %s ilan"


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
            logger.info(
                "\n%d. %s - %s",
                i,
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

        logger.info("\n🎯 Analiz tamamlandı! %s yüksek kaliteli pozisyon listelendi.", len(similar_jobs))

        if similar_jobs and ("persona_source" in similar_jobs[0] or "persona" in similar_jobs[0]):
            persona_counts: dict[str, int] = {}
            for job in similar_jobs:
                persona = job.get("persona_source", job.get("persona", "Unknown"))
                persona_counts[persona] = persona_counts.get(persona, 0) + 1

            logger.info("\n📈 Persona Dağılımı:")
            for persona, count in sorted(persona_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info("   %s: %s ilan", persona, count)
    else:
        logger.warning("⚠️  0 ilan bulundu veya uygunluk eşiği (%%%.0f) altında.", threshold)
        logger.info("💡 Eşiği düşürmeyi veya persona terimlerini genişletmeyi düşünebilirsiniz.")


def log_summary_statistics(
    all_jobs_df: pd.DataFrame, high_quality_jobs: list[dict], ai_metadata: dict | None = None
) -> None:
    """Log summary statistics about the search process."""
    logger.info("\n📊 Özet İstatistikler:")

    _log_site_distribution(all_jobs_df)
    _log_top_skills(high_quality_jobs)
    _log_persona_success(high_quality_jobs)


def _log_site_distribution(all_jobs_df: pd.DataFrame) -> None:
    """Log site distribution statistics."""
    if not all_jobs_df.empty and "source_site" in all_jobs_df.columns:
        logger.info("\n🔹 Site Dağılımı:")
        for site, count in all_jobs_df["source_site"].value_counts().items():
            logger.info(SITE_COUNT_FORMAT, site, count)


def _log_top_skills(high_quality_jobs: list[dict]) -> None:
    """Log most common matching skills from high-quality jobs."""
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
