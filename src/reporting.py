"""Reporting utilities for presenting final job results."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


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
            score = job.get("match_score", job.get("similarity_score", 0))
            logger.info("   📊 Uygunluk: %%.1f", score)
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


__all__ = ["display_results"]
