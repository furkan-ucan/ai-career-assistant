"""Command line entry for Akıllı Kariyer Asistanı."""

from __future__ import annotations

import argparse
from typing import Any

from dotenv import load_dotenv

from src.cli import parse_args
from src.config import get_config
from src.logger_config import setup_logging
from src.pipeline import JobAnalysisPipeline

load_dotenv()
logger = setup_logging()
config = get_config()


def load_config() -> dict[str, Any]:
    """Backward compatibility wrapper for tests with explicit dict typing."""
    cfg_dict: dict[str, Any] = config.model_dump()
    return cfg_dict


def print_manual_validation_guide() -> None:
    """Display manual validation instructions."""
    logger.info("\n" + "=" * 80)
    logger.info("📋 JOBSPY GELİŞMİŞ ÖZELLİKLER - MANUEL DOĞRULAMA PROTOKOLÜ")
    logger.info("=" * 80)
    logger.info("🎯 SİSTEM DURUMU: JobSpy Native (hours_old=72, cosine similarity)")
    logger.info("🚀 Optimize Özellikler: Çoklu site, gelişmiş operatörler, 12 persona")
    logger.info("📊 Beklenen Performans: 100-300 benzersiz ilan, %80+ uygunluk oranı")
    logger.info("=" * 80)


def main(selected_personas=None, results_per_site=None, similarity_threshold=None, rerank=True):
    """Run the end to end career assistant pipeline."""
    logger.info("🚀 Akıllı Kariyer Asistanı - Böl ve Fethet Stratejisi")
    logger.info("=" * 60)

    print_manual_validation_guide()
    # All validation is now handled by the pipeline
    logger.info("🎯 12 farklı JobSpy optimize edilmiş persona ile veri toplama başlatılıyor...\n")

    cli_args = argparse.Namespace(
        persona=selected_personas,
        results=results_per_site,
        threshold=similarity_threshold,
        no_rerank=not rerank,
        hours_old=72,  # Default hours_old value
    )
    pipeline = JobAnalysisPipeline(config)
    pipeline.run(cli_args)


if __name__ == "__main__":
    args = parse_args()
    main(
        selected_personas=args.persona,
        results_per_site=args.results,
        similarity_threshold=args.threshold,
        rerank=not args.no_rerank,
    )
