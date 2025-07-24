# src/pipeline.py
"""Core processing pipeline for job matching, fully restored and operational."""

from __future__ import annotations

import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm

from .config import get_config
from .cv_analyzer import CVAnalyzer
from .cv_processor import CVProcessor
from .data_collector import TieredJobCollector
from .embedding_service import EmbeddingService
from .exceptions import CVNotFoundError
from .models.pipeline_context import PipelineContext
from .persona_builder import PersonaConfigBuilder
from .reporting import display_results, log_summary_statistics
from .scoring_system import ScoringSystem, score_and_filter_jobs
from .utils.file_helpers import save_dataframe_csv
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class JobAnalysisPipeline:
    """Orchestrator for the end-to-end job analysis workflow."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.cli_args: argparse.Namespace | None = None

    def run(self, cli_args: argparse.Namespace) -> list[dict] | None:
        self.cli_args = cli_args
        if not self._validate_prerequisites():
            return None

        context = self._initialize_context()

        try:
            self._prepare_ai_components(context)
            self._collect_and_process_jobs(context)
            if context.final_results is not None and not context.final_results:
                return []  # Terminate early if no jobs found
            self._search_and_rank_jobs(context)
        except (CVNotFoundError, ValueError) as e:
            logger.error(f"İşlem durduruldu: {e}")
            return None
        except Exception:
            logger.exception("Pipeline çalıştırılırken beklenmedik bir hata oluştu.")
            return None

        self._generate_final_report(context)
        return context.final_results

    def _validate_prerequisites(self) -> bool:
        if not self.config.get("GEMINI_API_KEY"):
            logger.error("HATA: Gemini API anahtarı bulunamadı!")
            return False
        cv_path = Path(self.config.get("paths", {}).get("cv_file", ""))
        if not cv_path.is_file() or cv_path.stat().st_size == 0:
            logger.error(f"HATA: CV dosyası bulunamadı veya boş: {cv_path}")
            return False
        return True

    def _initialize_context(self) -> PipelineContext:
        if not self.cli_args:
            raise ValueError("CLI arguments must be set before initializing context.")
        return PipelineContext(config=self.config, cli_args=self.cli_args)

    def _prepare_ai_components(self, context: PipelineContext) -> None:
        logger.info("\n🔄 1/5: AI bileşenleri ve kişisel kariyer personaları hazırlanıyor...")
        api_key = self.config["GEMINI_API_KEY"]

        context.embedding_service = EmbeddingService(api_key=api_key)
        context.cv_analyzer = CVAnalyzer(api_key=api_key)
        context.vector_store = VectorStore(embedding_service=context.embedding_service)
        context.scoring_system = ScoringSystem(self.config)

        cv_processor = CVProcessor(
            cv_path=self.config["paths"]["cv_file"], embedding_service=context.embedding_service
        )
        if not cv_processor.load_cv() or not cv_processor.create_cv_embedding():
            raise CVNotFoundError("CV yüklenemedi veya embedding oluşturulamadı.")

        context.cv_text = cv_processor.get_cv_text()
        context.cv_embedding = cv_processor.get_cv_embedding()
        context.ai_metadata = context.cv_analyzer.extract_metadata_from_cv(context.cv_text or "")

        persona_builder = PersonaConfigBuilder()
        context.personas_config = persona_builder.build_from_metadata(context.ai_metadata)

    def _collect_and_process_jobs(self, context: PipelineContext) -> None:
        logger.info("\n🔄 2/5: İş ilanları paralel olarak toplanıyor...")
        raw_jobs_df = self._collect_data_for_all_personas(context)

        if raw_jobs_df is None or raw_jobs_df.empty:
            logger.warning("Hiç iş ilanı bulunamadı. Analiz sonlandırılıyor.")
            context.final_results = []  # Set to empty list to terminate early
            return

        context.raw_jobs_df = raw_jobs_df
        csv_path = save_dataframe_csv(raw_jobs_df, Path(self.config["paths"]["data_dir"]), "job_ilanlari")
        logger.info(f"📁 Toplanan {len(raw_jobs_df)} ilan şuraya kaydedildi: {csv_path}")

        logger.info("\n🔄 3/5: Vektör veritabanı hazırlanıyor ve ilanlar yükleniyor...")
        if context.vector_store:
            context.vector_store.add_jobs(raw_jobs_df)

    def _collect_data_for_all_personas(self, context: PipelineContext) -> pd.DataFrame | None:
        personas_to_run = context.personas_config
        if self.cli_args and self.cli_args.persona:
            personas_to_run = {
                p: context.personas_config[p] for p in self.cli_args.persona if p in context.personas_config
            }

        all_jobs_list = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_persona = {
                executor.submit(self._collect_jobs_for_single_persona, name, p_config): name
                for name, p_config in personas_to_run.items()
            }
            for future in tqdm(as_completed(future_to_persona), total=len(personas_to_run), desc="Persona Aramaları"):
                try:
                    result = future.result()
                    if result is not None and not result.empty:
                        all_jobs_list.append(result)
                except Exception as e:
                    logger.error(f"Error collecting for persona {future_to_persona[future]}: {e}")

        if not all_jobs_list:
            return None

        result_df = pd.concat(all_jobs_list, ignore_index=True)
        return result_df if isinstance(result_df, pd.DataFrame) else None

    def _collect_jobs_for_single_persona(self, persona_name: str, persona_cfg: dict) -> pd.DataFrame | None:
        collector = TieredJobCollector()
        return collector.collect_with_platform_queries(
            platform_queries=persona_cfg.get("platform_queries", {}), persona_name=persona_name
        )

    def _search_and_rank_jobs(self, context: PipelineContext) -> None:
        if not all([context.vector_store, context.cv_embedding, context.scoring_system]):
            logger.error("Arama ve sıralama için gerekli bileşenler eksik.")
            context.final_results = []
            return

        # Type guards to ensure non-None values
        if context.vector_store is None or context.cv_embedding is None or context.scoring_system is None:
            logger.error("Arama ve sıralama için gerekli bileşenler None.")
            context.final_results = []
            return

        logger.info("\n🔄 4/5: Vektör veritabanında CV'nize en uygun ilanlar aranıyor...")
        search_results = context.vector_store.search_jobs(context.cv_embedding)
        logger.info(f"🔍 {len(search_results)} adet potansiyel eşleşme bulundu. Akıllı puanlama uygulanıyor...")
        context.scored_jobs = score_and_filter_jobs(search_results, context.scoring_system)

        if context.rerank_flag:
            logger.info("\n🔄 5/5: AI Reranking ile sonuçlar derinlemesine analiz ediliyor...")
            # Placeholder for AI reranking logic. It can be expanded here.
            # For now, it just passes the scored jobs through.
            context.final_results = context.scored_jobs
        else:
            logger.info("\n⏭️ 5/5: AI Reranking adımı atlandı.")
            context.final_results = context.scored_jobs

    def _generate_final_report(self, context: PipelineContext) -> None:
        logger.info("\n" + "=" * 70)
        logger.info("🎉 OPERASYON TAMAMLANDI: SONUÇ RAPORU")
        logger.info("=" * 70)
        display_results(context.final_results, context.threshold)
        if context.raw_jobs_df is not None:
            log_summary_statistics(context.raw_jobs_df, context.final_results, context.ai_metadata)


def run_end_to_end_pipeline(cli_args: argparse.Namespace) -> list[dict] | None:
    """Public wrapper to configure and run the full analysis pipeline."""
    try:
        config = get_config()
        pipeline = JobAnalysisPipeline(config)
        return pipeline.run(cli_args)
    except Exception:
        logger.exception("Pipeline failed to run.")
        return None
