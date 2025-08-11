# src/pipeline.py
"""Core processing pipeline, with all functions fully implemented and integrated."""

from __future__ import annotations

import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    pass
from tqdm import tqdm

from .config import get_config
from .config_models import AppConfig
from .core.utils import get_app_directories
from .cv_analyzer import CVAnalyzer
from .cv_processor import CVProcessor
from .data_collector import TieredJobCollector
from .database_maintenance import DatabaseMaintenance
from .embedding_cache import EmbeddingCache
from .embedding_service import EmbeddingService
from .exceptions import CVNotFoundError
from .models.pipeline_context import PipelineContext
from .persona_builder import PersonaConfigBuilder
from .reporting import display_results, log_summary_statistics
from .reranking_cache import RerankingCache

# REMOVED: Manual scoring system - Pure AI-driven approach
from .utils.file_helpers import save_dataframe_csv
from .utils.json_helpers import extract_json_from_response
from .utils.prompt_loader import load_prompt
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

# Lazy load prompt template
_RERANK_PROMPT_TEMPLATE: str | None = None


def _get_rerank_prompt_template() -> str:
    """Lazy load and return the rerank prompt template."""
    global _RERANK_PROMPT_TEMPLATE
    if _RERANK_PROMPT_TEMPLATE is None:
        try:
            prompts_dir = get_app_directories()["prompts_dir"]
            _RERANK_PROMPT_TEMPLATE = load_prompt(prompts_dir / "rerank_prompt.md")
        except OSError as e:
            logger.error(f"Failed to load rerank prompt: {e}")
            # Fallback prompt in case of file error
            _RERANK_PROMPT_TEMPLATE = """Analyze job fit for candidate skills: {key_skills_list}"""
    return _RERANK_PROMPT_TEMPLATE


class JobAnalysisPipeline:
    """Orchestrator for the end-to-end job analysis workflow."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.cli_args: argparse.Namespace | None = None

        # Initialize caching systems
        self.embedding_cache = EmbeddingCache()
        self.reranking_cache = RerankingCache()

        # Initialize database maintenance
        chromadb_path = config.paths.chromadb_dir
        self.db_maintenance = DatabaseMaintenance(persist_directory=chromadb_path)

    def run(self, cli_args: argparse.Namespace) -> list[dict] | None:
        self.cli_args = cli_args
        if not self._validate_prerequisites():
            return None

        context = self._initialize_context()

        try:
            self._prepare_ai_components(context)
            self._collect_and_process_jobs(context)
            if context.raw_jobs_df is None or context.raw_jobs_df.empty:
                logger.warning("Veri toplama aşamasında hiç iş ilanı bulunamadı. İşlem sonlandırılıyor.")
                return []
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
        """Validate pipeline prerequisites and dependencies."""
        if not self.config.gemini_api_key:
            logger.error("❌ GEMINI_API_KEY eksik. .env dosyasına ekleyin.")
            return False
        cv_path = Path(self.config.paths.cv_file)
        if not cv_path.exists():
            logger.error(f"❌ CV dosyası bulunamadı: {cv_path}")
            return False
        return True

    def _initialize_context(self) -> PipelineContext:
        """Initialize the pipeline context with current configuration."""
        threshold = 60.0  # Default threshold
        if self.cli_args and hasattr(self.cli_args, "threshold") and self.cli_args.threshold:
            threshold = self.cli_args.threshold
        else:
            threshold = self.config.job_search_settings.min_similarity_threshold

        return PipelineContext(
            config=self.config.model_dump(),  # Convert to dict for compatibility
            cli_args=self.cli_args,
            threshold=threshold,
        )

    def _prepare_ai_components(self, context: PipelineContext) -> None:
        logger.info("\n🔄 1/5: AI bileşenleri ve kişisel kariyer personaları hazırlanıyor...")
        api_key = self.config.gemini_api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found.")

        # Initialize embedding service with cache support
        context.embedding_service = EmbeddingService(
            api_key=api_key, cache_enabled=True, cache_dir="data/embedding_cache"
        )
        context.cv_analyzer = CVAnalyzer(api_key=api_key)
        context.vector_store = VectorStore(embedding_service=context.embedding_service)

        cv_processor = CVProcessor(cv_path=self.config.paths.cv_file, embedding_service=context.embedding_service)
        if not cv_processor.load_cv() or not cv_processor.create_cv_embedding():
            raise CVNotFoundError("CV yüklenemedi veya embedding oluşturulamadı.")

        context.cv_text = cv_processor.get_cv_text()
        context.cv_embedding = cv_processor.get_cv_embedding()
        context.ai_metadata = context.cv_analyzer.extract_metadata_from_cv(context.cv_text or "")

        # REMOVED: Manual scoring system - Pure AI evaluation only
        # context.scoring_system = ScoringSystem(config=self.config.model_dump(), ai_metadata=context.ai_metadata)

        persona_builder = PersonaConfigBuilder()
        context.personas_config = persona_builder.build_from_metadata(context.ai_metadata)

    def _collect_and_process_jobs(self, context: PipelineContext) -> None:
        logger.info("\n🔄 2/5: İş ilanları paralel olarak toplanıyor...")

        # Perform database maintenance before adding new jobs
        logger.info("🔧 Veritabanı bakımı yapılıyor...")
        try:
            maintenance_stats = self.db_maintenance.perform_full_maintenance()
            if maintenance_stats:
                logger.info(f"📊 Temizlik istatistikleri: {maintenance_stats}")
        except Exception as e:
            logger.warning(f"⚠️ Veritabanı bakımı sırasında hata: {e}")

        raw_jobs_df = self._collect_data_for_all_personas(context)
        if raw_jobs_df is None or raw_jobs_df.empty:
            context.raw_jobs_df = pd.DataFrame()
            return

        context.raw_jobs_df = raw_jobs_df
        csv_path = save_dataframe_csv(raw_jobs_df, Path(self.config.paths.data_dir), "job_ilanlari")
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

        all_jobs_list: list[pd.DataFrame] = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_persona = {
                executor.submit(self._collect_jobs_for_single_persona, name, p_config): name
                for name, p_config in personas_to_run.items()
            }
            for future in tqdm(as_completed(future_to_persona), total=len(personas_to_run), desc="Persona Aramaları"):
                try:
                    future_result = future.result()
                    if future_result is not None and not future_result.empty:
                        all_jobs_list.append(future_result)
                except Exception as e:
                    logger.error(f"Error collecting for persona {future_to_persona[future]}: {e}")

        if all_jobs_list:
            final_result: pd.DataFrame = pd.concat(all_jobs_list, ignore_index=True)
            return final_result
        else:
            return None

    def _collect_jobs_for_single_persona(self, persona_name: str, persona_cfg: dict) -> pd.DataFrame | None:
        collector = TieredJobCollector()
        return collector.collect_with_platform_queries(
            platform_queries=persona_cfg.get("platform_queries", {}), persona_name=persona_name
        )

    def _search_and_rank_jobs(self, context: PipelineContext) -> None:
        if not all([context.vector_store, context.cv_embedding]):
            context.final_results = []
            return

        logger.info("\n🔄 4/5: Vektör veritabanında CV'nize en uygun ilanlar aranıyor...")

        # Type assertion for cv_embedding
        assert context.cv_embedding is not None, "CV embedding should not be None at this point"
        # Type assertion for vector_store
        assert context.vector_store is not None, "Vector store should not be None at this point"
        search_results = context.vector_store.search_jobs(context.cv_embedding)

        logger.info(f"🔍 {len(search_results)} adet potansiyel eşleşme bulundu. PURE AI EVALUATION başlatılıyor...")

        # PURE AI-DRIVEN: Skip all manual scoring, go straight to AI evaluation
        rerank_enabled = self.config.ai_reranking_settings.enabled
        rerank_pool_size = min(len(search_results), self.config.ai_reranking_settings.rerank_pool_size)

        if rerank_enabled and len(search_results) > 0:
            # Skip manual scoring - let AI decide everything
            logger.info(f"PURE AI MODE: {rerank_pool_size} ilan tamamen AI ile değerlendiriliyor...")

            # Only add minimal similarity score for context
            for job in search_results:
                job["similarity_score"] = job.get("similarity_score", 0.0)

            context.scored_jobs = search_results[:rerank_pool_size]
            context.final_results = self._rerank_with_ai_analysis(context)
        else:
            # NO FALLBACK: Pure AI-driven system requires AI reranking
            logger.warning("⚠️ AI Reranking disabled - No results without AI evaluation")
            context.scored_jobs = []
            context.final_results = []

    def _rerank_with_ai_analysis(self, context: PipelineContext) -> list[dict]:
        rerank_config = self.config.ai_reranking_settings

        # Use class-level reranking cache (already initialized)
        logger.info("✅ AI Reranking cache enabled")

        try:
            # Import at runtime to avoid dependency issues
            genai = __import__("google.generativeai", fromlist=[""])

            genai.configure(api_key=self.config.gemini_api_key)
            model = genai.GenerativeModel(rerank_config.llm_model)
        except ImportError:
            logger.error("Google Generative AI not installed. Install with: pip install google-generativeai")
            return context.scored_jobs or []
        except Exception as e:
            logger.error(f"Failed to create GenerativeModel: {e}")
            return context.scored_jobs or []

        jobs_to_rerank = context.scored_jobs
        if not jobs_to_rerank:
            return []

        analyzed_jobs = []
        with ThreadPoolExecutor(max_workers=rerank_config.max_workers) as executor:
            future_to_job = {
                executor.submit(self._analyse_single_job_for_rerank, job, context, model, self.reranking_cache): job
                for job in jobs_to_rerank
            }
            for future in tqdm(as_completed(future_to_job), total=len(jobs_to_rerank), desc="AI Reranking"):
                analyzed_jobs.append(future.result())

        analyzed_jobs.sort(key=lambda j: (j.get("is_recommended", False), j.get("fit_score", 0)), reverse=True)
        return analyzed_jobs

    def _analyse_single_job_for_rerank(
        self,
        job: dict,
        context: PipelineContext,
        model: Any,  # Use Any for GenerativeModel type
        reranking_cache: Any = None,  # RerankingCache type
    ) -> dict:
        if not context.ai_metadata:
            return job

        # Check cache first if available
        if reranking_cache:
            cached_result = reranking_cache.get_cached_reranking(job)
            if cached_result:
                job.update(cached_result)
                return job

        prompt = _get_rerank_prompt_template().format(
            key_skills_list="\n- ".join(context.ai_metadata.get("key_skills", [])),
            cv_summary=context.ai_metadata.get("cv_summary", ""),
            title=job.get("title", ""),
            description=str(job.get("description", ""))[:4000],
        )

        try:
            response = model.generate_content(prompt)
            rerank_data = extract_json_from_response(response.text)
            if rerank_data:
                job.update(rerank_data)
                # Save to cache if available
                if reranking_cache:
                    reranking_cache.save_reranking_result(job, rerank_data)
        except Exception as e:
            logger.warning(f"AI reranking for job '{job.get('title')}' failed: {e}")

        return job

    def _generate_final_report(self, context: PipelineContext) -> None:
        logger.info("\n" + "=" * 70)
        logger.info("🎉 OPERASYON TAMAMLANDI: SONUÇ RAPORU")
        logger.info("=" * 70)
        display_results(context.final_results, context.threshold)
        if context.raw_jobs_df is not None:
            log_summary_statistics(context.raw_jobs_df, context.final_results, context.ai_metadata)

        # Generate comprehensive markdown report
        try:
            from .report_generator import StrategicReportGenerator

            report_generator = StrategicReportGenerator()

            raw_jobs_count = len(context.raw_jobs_df) if context.raw_jobs_df is not None else 0
            report_file = report_generator.generate_comprehensive_report(
                final_results=context.final_results or [],
                ai_metadata=context.ai_metadata,
                raw_jobs_count=raw_jobs_count,
                threshold=context.threshold,
            )
            logger.info(f"📄 Detaylı analiz raporu oluşturuldu: {report_file}")

        except Exception as e:
            logger.error(f"❌ Rapor oluşturulurken hata: {e}")
            logger.info("⚠️ Konsol çıktısı ile devam ediliyor...")


def run_end_to_end_pipeline(cli_args: argparse.Namespace) -> list[dict] | None:
    """Public wrapper to configure and run the full analysis pipeline."""
    try:
        config = get_config()
        pipeline = JobAnalysisPipeline(config)
        return pipeline.run(cli_args)
    except Exception:
        logger.exception("Pipeline failed to run.")
        return None


# Legacy compatibility names expected by older tests
def analyze_and_find_best_jobs(*args, **kwargs):  # type: ignore[unused-ignore]
    """Legacy wrapper retained for tests; delegates to run_end_to_end_pipeline if args provided."""
    cli_args = kwargs.get("cli_args") or (args[0] if args else argparse.Namespace())
    return run_end_to_end_pipeline(cli_args)


# Legacy placeholder so tests can patch it
def collect_data_for_all_personas(*_args, **_kwargs):  # type: ignore[unused-ignore]
    return None
