"""Command line entry for Akıllı Kariyer Asistanı."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from src.cli import parse_args
from src.config import load_settings
from src.logger_config import setup_logging
from src.pipeline import run_end_to_end_pipeline

load_dotenv()
logger = setup_logging()
config = load_settings()


def load_config() -> dict:
    """Backward compatibility wrapper for tests."""
    return config


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
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.error("❌ HATA: Gemini API key bulunamadı!")
        logger.info("📝 Lütfen .env dosyasında GEMINI_API_KEY değerini ayarlayın.")
        return

    cv_path = Path(config["paths"]["cv_file"])
    try:
        if not cv_path.exists():
            logger.error("❌ HATA: CV dosyası bulunamadı: %s", cv_path)
            logger.info("📝 Lütfen CV'nizi data/cv.txt dosyasına ekleyin.")
            return
        if cv_path.stat().st_size == 0:
            logger.error("❌ HATA: CV dosyası boş: %s", cv_path)
            return
    except OSError as exc:
        logger.error("❌ HATA: CV dosyası erişim hatası: %s", exc)
        return

    logger.info("✅ Sistem kontrolleri başarılı")
    logger.info("🎯 12 farklı JobSpy optimize edilmiş persona ile veri toplama başlatılıyor...\n")

    run_end_to_end_pipeline(selected_personas, results_per_site, similarity_threshold, rerank)


if __name__ == "__main__":
    args = parse_args()
    main(
        selected_personas=args.persona,
        results_per_site=args.results,
        similarity_threshold=args.threshold,
        rerank=not args.no_rerank,
    )
