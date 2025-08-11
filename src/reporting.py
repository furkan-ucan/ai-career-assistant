# src/reporting.py
"""Reporting utilities, fully restored to display all strategic insights."""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)
SITE_COUNT_FORMAT = "   %s: %s ilan"


def _get_job_score(job: dict[str, Any]) -> float:
    """Extract a job's score, prioritizing the AI fit_score."""
    try:
        # Prioritize fit_score, fallback to other scores, default to 0.0
        score = job.get("fit_score", job.get("score", job.get("similarity_score", 0.0)))
        return float(score) if score is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _deduplicate_jobs_by_url(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate jobs by URL, keeping the one with the highest score."""
    if not jobs:
        return []

    url_to_best_job: dict[str, dict[str, Any]] = {}
    for job in jobs:
        url = job.get("url", job.get("job_url", "")).strip()
        if not url:
            # If no URL, treat as unique to be safe
            unique_key = f"no_url_{id(job)}"
            url_to_best_job[unique_key] = job
            continue

        current_score = _get_job_score(job)
        if url not in url_to_best_job or current_score > _get_job_score(url_to_best_job[url]):
            url_to_best_job[url] = job

    deduplicated = list(url_to_best_job.values())
    deduplicated.sort(key=_get_job_score, reverse=True)
    return deduplicated


def _log_single_job_details(job: dict[str, Any], index: int) -> None:
    """Logs the detailed information for a single job."""
    logger.info("\n%d. %s - %s", index, job.get("title", "[Başlık Yok]"), job.get("company", "[Şirket Yok]"))
    logger.info("   📍 %s", job.get("location", "[Lokasyon Yok]"))

    fit_score = job.get("fit_score")
    if fit_score is not None:
        recommendation = "✅ TAVSİYE EDİLİR" if job.get("is_recommended") else "❌ TAVSİYE EDİLMEZ"
        logger.info(f"   📊 Stratejik Uygunluk: {fit_score}/100 ({recommendation})")
    else:
        similarity_score = job.get("score", 0)
        logger.info(f"   📊 Anlamsal Benzerlik: {similarity_score:.1f}")

    if reasoning := job.get("reasoning"):
        logger.info("   💡 Değerlendirme: %s", reasoning)
    if matching_keywords := job.get("matching_keywords", []):
        logger.info("   ✅ Eşleşen Yetenekler: %s", ", ".join(matching_keywords))
    if missing_keywords := job.get("missing_keywords", []):
        logger.info("   ⚠️ Gelişim Alanları: %s", ", ".join(missing_keywords))

    logger.info("   💼 Site: %s", job.get("source_site", "[Site Yok]"))
    logger.info("   👤 Persona: %s", job.get("persona_source", "[Persona Yok]"))
    logger.info("   🔗 %s", job.get("url", job.get("job_url", "[URL Yok]")))
    logger.info("-" * 50)


def display_results(similar_jobs: list[dict[str, Any]] | None, threshold: float) -> None:
    """Log formatted job search results."""
    if not similar_jobs:
        logger.warning("⚠️ Hiç uygun ilan bulunamadı veya tümü eşik (%%%.0f) altında kaldı.", threshold)
        return

    deduplicated_jobs = _deduplicate_jobs_by_url(similar_jobs)
    logger.info("✅ %s adet yüksek kaliteli pozisyon bulundu.", len(similar_jobs))
    if len(similar_jobs) != len(deduplicated_jobs):
        logger.info("🔗 %s tekrar eden ilan URL'ye göre temizlendi.", len(similar_jobs) - len(deduplicated_jobs))

    logger.info("\n" + "=" * 70)
    logger.info("🎉 SİZE ÖZEL STRATEJİK KARİYER FIRSATLARI")
    logger.info("=" * 70)

    for i, job in enumerate(deduplicated_jobs[:15], 1):
        _log_single_job_details(job, i)

    logger.info("\n🎯 Analiz tamamlandı! En uygun %s pozisyon listelendi.", min(15, len(deduplicated_jobs)))
    _log_persona_distribution(deduplicated_jobs)


def _log_persona_distribution(similar_jobs: list[dict[str, Any]]) -> None:
    """Logs the distribution of personas among similar jobs."""
    if not similar_jobs:
        return
    persona_counts = Counter(job.get("persona_source") for job in similar_jobs if job.get("persona_source"))
    if persona_counts:
        logger.info("\n📈 En Başarılı Personalar:")
        for persona, count in persona_counts.most_common():
            logger.info(SITE_COUNT_FORMAT, persona, count)


def _log_site_distribution(all_jobs_df: pd.DataFrame) -> None:
    """Log site distribution statistics."""
    if not all_jobs_df.empty and "source_site" in all_jobs_df.columns:
        logger.info("\n🔹 Bulunan İlanların Site Dağılımı:")
        for site, count in all_jobs_df["source_site"].value_counts().items():
            logger.info(SITE_COUNT_FORMAT, site, count)


def _log_cv_skills(ai_metadata: dict[str, Any] | None) -> bool:
    """Log CV-based skills from AI metadata."""
    if not ai_metadata or not ai_metadata.get("key_skills"):
        return False
    logger.info("\n🔹 En Önemli Yetenekleriniz (CV'nize Göre):")
    key_skills = ai_metadata.get("key_skills", [])
    skill_importance = ai_metadata.get("skill_importance", [])
    for i, skill in enumerate(key_skills[:5]):
        importance = skill_importance[i] if i < len(skill_importance) else 0.0
        logger.info("   - %s (Önem: %.2f)", skill, importance)
    return True


def log_summary_statistics(
    all_jobs_df: pd.DataFrame, high_quality_jobs: list[dict] | None, ai_metadata: dict[str, Any] | None = None
) -> None:
    """Logs summary statistics about the job search process."""
    logger.info("\n📊 Özet İstatistikler:")
    _log_site_distribution(all_jobs_df)
    if not _log_cv_skills(ai_metadata):
        logger.info("CV yetenekleri bulunamadı.")
    if high_quality_jobs:
        _log_persona_distribution(high_quality_jobs)
