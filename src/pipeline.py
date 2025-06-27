"""Core processing pipeline for job matching."""

from __future__ import annotations

import copy
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import google.generativeai as genai
import pandas as pd
from google.api_core import exceptions as google_exceptions
from tqdm import tqdm

from .config import get_config
from .constants import PROMPTS_DIR
from .cv_analyzer import TOKEN_LIMIT, CVAnalyzer
from .cv_processor import CVProcessor
from .data_collector import collect_job_data
from .embedding_service import EmbeddingService
from .exceptions import CVNotFoundError
from .filter import score_jobs
from .intelligent_scoring import IntelligentScoringSystem
from .models.pipeline_context import PipelineContext
from .persona_builder import build_dynamic_personas
from .reporting import display_results, log_summary_statistics
from .utils.file_helpers import save_dataframe_csv
from .utils.json_helpers import extract_json_from_response
from .utils.prompt_loader import load_prompt
from .vector_store import VectorStore

RERANK_PROMPT_TEMPLATE = load_prompt(PROMPTS_DIR / "rerank_prompt.md")

logger = logging.getLogger(__name__)

config = get_config()

embedding_settings = config.get("embedding_settings", {})

job_settings = config["job_search_settings"]
MIN_SIMILARITY_THRESHOLD = job_settings["min_similarity_threshold"]
TARGET_SITES = job_settings["target_sites"]
DEFAULT_HOURS_OLD = job_settings["default_hours_old"]
DEFAULT_RESULTS_PER_PERSONA_SITE = job_settings["default_results_per_site"]

persona_search_config = config["persona_search_configs"]

rerank_settings = config.get("ai_reranking_settings", {})


class JobAnalysisPipeline:
    """High level orchestrator for the job analysis workflow."""

    def __init__(self, config: dict) -> None:
        self.config = config

    def validate_prerequisites(self) -> bool:
        """Validate API key and CV file before processing."""
        # API key validation
        api_key = self.config.get("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            logger.error("❌ HATA: Gemini API key bulunamadı!")
            logger.info("📝 Lütfen .env dosyasında GEMINI_API_KEY değerini ayarlayın.")
            return False

        # CV file validation
        cv_path = Path(self.config["paths"]["cv_file"])
        try:
            if not cv_path.exists():
                logger.error("❌ HATA: CV dosyası bulunamadı: %s", cv_path)
                logger.info("📝 Lütfen CV'nizi data/cv.txt dosyasına ekleyin.")
                return False
            if cv_path.stat().st_size == 0:
                logger.error("❌ HATA: CV dosyası boş: %s", cv_path)
                return False
        except OSError as exc:
            logger.error("❌ HATA: CV dosyası erişim hatası: %s", exc)
            return False

        logger.info("✅ Sistem kontrolleri başarılı")
        return True

    def run(self, cli_args: Any) -> PipelineContext:
        """Execute the end-to-end pipeline."""
        context = PipelineContext(config=self.config, cli_args=cli_args)
        if not self.validate_prerequisites():
            return context
        context.threshold = cli_args.threshold if cli_args.threshold is not None else MIN_SIMILARITY_THRESHOLD
        context.rerank_flag = not getattr(cli_args, "no_rerank", False)

        try:
            _setup_ai_metadata_and_personas(context)
        except CVNotFoundError as exc:  # pragma: no cover - error path
            logger.error("İşlem durduruldu: %s", exc)
            return context

        scoring_sys = _configure_scoring_system(self.config, context.ai_metadata)
        if scoring_sys is None:
            return context

        context.scoring_system = scoring_sys
        _execute_full_pipeline(context)

        return context


def _collect_jobs_for_persona(persona_name: str, persona_cfg: dict, context: PipelineContext) -> pd.DataFrame | None:
    """Collect jobs for a single persona."""
    logger.info("\n--- Persona '%s' için JobSpy Gelişmiş Arama ---", persona_name)
    logger.info("🎯 Optimize edilmiş terim: '%s'", persona_cfg["term"])
    logger.info("⏰ Tarih filtresi: Son %s saat", persona_cfg["hours_old"])

    try:
        max_results = context.cli_args.results if context.cli_args.results is not None else persona_cfg["results"]
        jobs_df_for_persona = collect_job_data(
            search_term=persona_cfg["term"],
            site_names=TARGET_SITES,
            location="Turkey",
            max_results_per_site=max_results,
            hours_old=persona_cfg["hours_old"],
        )
        if jobs_df_for_persona is not None and not jobs_df_for_persona.empty:
            jobs_df_for_persona["persona_source"] = persona_name
            jobs_df_for_persona["search_term_used"] = persona_cfg["term"]
            logger.info("✨ Persona '%s' için %s ilan bulundu.", persona_name, len(jobs_df_for_persona))
            return jobs_df_for_persona
        logger.info("ℹ️ Persona '%s' için hiçbir siteden ilan bulunamadı.", persona_name)
        return None
    except (ValueError, TypeError, KeyError) as e:
        logger.error("❌ Persona '%s' için hata: %s", persona_name, e, exc_info=True)
        return None
    except Exception:
        logger.exception("❌ Unexpected error for persona '%s'", persona_name)
        raise


def _deduplicate_and_save_jobs(all_jobs_list: list[pd.DataFrame], context: PipelineContext) -> str | None:
    """Merge, deduplicate and save collected jobs."""
    non_empty = [df for df in all_jobs_list if df is not None and not df.empty]
    if not non_empty:
        logger.error("❌ Hiçbir persona ve site kombinasyonundan ilan bulunamadı.")
        return None

    final_df = pd.concat(non_empty, ignore_index=True)
    logger.info("\n📊 Birleştirme öncesi (tüm personalar): %s ilan", len(final_df))

    if not final_df.empty:
        subset_cols = ["title", "company"]
        if "location" in final_df.columns:
            subset_cols.append("location")
        if "description" in final_df.columns:
            final_df["description_short"] = final_df["description"].astype(str).str[:100]
            subset_cols.append("description_short")
        final_df.drop_duplicates(subset=subset_cols, inplace=True, keep="first")
        if "description_short" in final_df.columns:
            final_df.drop(columns=["description_short"], inplace=True)

    logger.info("✨✨✨ TOPLAM: %s adet BENZERSİZ ilan (JobSpy optimize edilmiş)! ✨✨✨", len(final_df))

    output_dir = Path(context.config["paths"]["data_dir"])
    csv_path = save_dataframe_csv(final_df, output_dir, "jobspy_optimize_ilanlar")
    logger.info("📁 JobSpy optimize edilmiş veriler: %s", csv_path)
    return str(csv_path)


def collect_data_for_all_personas(context: PipelineContext) -> str | None:
    """Collect data for all personas and return CSV path."""
    logger.info("🔍 JobSpy Gelişmiş Özellikler ile Stratejik Veri Toplama Başlatılıyor...")
    logger.info("=" * 70)

    all_collected_jobs_list = []
    cfg = context.personas_config or persona_search_config
    personas = cfg.items()
    if context.cli_args.persona:
        personas = [(p, cfg[p]) for p in context.cli_args.persona if p in cfg]

    for persona_name, persona_cfg in tqdm(personas, desc="Persona Aramaları"):
        jobs_df = _collect_jobs_for_persona(persona_name, persona_cfg, context)
        if jobs_df is not None:
            all_collected_jobs_list.append(jobs_df)

    return _deduplicate_and_save_jobs(all_collected_jobs_list, context)


def _setup_ai_metadata_and_personas(context: PipelineContext) -> None:
    """
    Extracts AI metadata from the CV and determines the personas configuration.

    Returns:
        ai_metadata (dict): Metadata extracted from the CV, including target job titles and skill information.
        personas_cfg (dict): Persona configuration, dynamically built from AI metadata if available, otherwise static.

    Raises:
        CVNotFoundError: If CV processing fails.
    """
    try:
        cv_text = Path(context.config["paths"]["cv_file"]).read_text(encoding="utf-8")
        analyzer = CVAnalyzer()
        ai_metadata = analyzer.extract_metadata_from_cv(cv_text)
    except CVNotFoundError as e:
        logger.error("CV işleme hatası: %s", e)
        raise

    personas_cfg = persona_search_config
    if ai_metadata and ai_metadata.get("target_job_titles"):
        target_titles = ai_metadata["target_job_titles"]
        if isinstance(target_titles, list) and all(isinstance(title, str) for title in target_titles):
            personas_cfg = build_dynamic_personas(target_titles)
        else:
            logger.warning("AI metadata target_job_titles geçersiz format - static personas kullanılıyor")
    else:
        logger.warning("AI metadata missing - using static personas")

    context.ai_metadata = ai_metadata
    context.personas_config = personas_cfg


def _validate_skill_metadata(key_skills: object, skill_importance: object) -> bool:
    """Validate skill metadata structure and types."""
    return (
        isinstance(key_skills, list)
        and isinstance(skill_importance, list)
        and len(key_skills) == len(skill_importance)
        and all(isinstance(skill, str) for skill in key_skills)
        and all(isinstance(score, int | float) for score in skill_importance)
    )


def _apply_skill_weights(cfg: dict, skill: str, importance: float, base_weight: int, min_imp: float) -> dict:
    """Return updated config with dynamic skill weights applied."""
    new_cfg = copy.deepcopy(cfg)
    if importance >= min_imp:
        weight = int(round(base_weight * importance))
        new_cfg["scoring_system"]["description_weights"]["positive"][skill] = weight
        logger.debug(
            "  ⭐ Skill: %s (importance: %.2f) → weight: %s",
            skill,
            importance,
            weight,
        )
    else:
        logger.debug(
            "  ⏭️  Skill %s below importance threshold %.2f (score %.2f)",
            skill,
            min_imp,
            importance,
        )
    return new_cfg


def _configure_scoring_system(config_data: dict, ai_metadata: dict) -> IntelligentScoringSystem | None:
    """Return a scoring system configured with AI metadata."""
    try:
        cfg = copy.deepcopy(config_data)
        if not (ai_metadata.get("key_skills") and ai_metadata.get("skill_importance")):
            logger.info("No AI skill data available - using static scoring")
            return IntelligentScoringSystem(cfg)

        key_skills = ai_metadata["key_skills"]
        skill_importance = ai_metadata["skill_importance"]

        if not _validate_skill_metadata(key_skills, skill_importance):
            logger.warning("AI metadata skills format invalid - using static scoring")
            return IntelligentScoringSystem(cfg)

        base_weight = cfg["scoring_system"].get("dynamic_skill_weight", 10)
        min_imp = cfg["scoring_system"].get("min_importance_for_scoring", 0.75)
        logger.info("🎯 Configuring enhanced scoring with %s AI-detected skills", len(key_skills))

        if len(skill_importance) != len(key_skills):
            skill_importance = [1.0] * len(key_skills)

        temp_cfg = cfg
        for skill, importance in zip(key_skills, skill_importance, strict=False):
            temp_cfg = _apply_skill_weights(temp_cfg, skill, float(importance), base_weight, min_imp)

        logger.info("✅ Enhanced AI-driven scoring system configured")
        return IntelligentScoringSystem(temp_cfg)
    except (ValueError, TypeError, KeyError) as e:
        logger.error("❌ Scoring system configuration failed: %s", e)
        return None
    except Exception:
        logger.exception("❌ Unexpected error in scoring system configuration")
        raise


def _load_and_validate_csv(csv_path: str) -> pd.DataFrame | None:
    """Load CSV and validate content."""
    try:
        csv_path_obj = Path(csv_path)
        jobs_df = pd.read_csv(csv_path_obj)
        logger.info("📊 %s iş ilanı yüklendi", len(jobs_df))
        return jobs_df
    except FileNotFoundError:
        logger.error("❌ CSV dosyası bulunamadı: %s", csv_path)
        return None
    except pd.errors.EmptyDataError:
        logger.error("❌ CSV dosyası boş!")
        return None
    except (pd.errors.ParserError, UnicodeDecodeError) as e:
        logger.error("❌ CSV okuma hatası: %s", e)
        return None
    except Exception:
        logger.exception("❌ Unexpected error reading CSV file")
        raise


def _setup_cv_processor(context: PipelineContext) -> CVProcessor | None:  # pragma: no cover
    """Prepare CV processor."""
    logger.info("\n📄 2/6: CV analizi...")
    cv_processor = CVProcessor(embedding_settings=embedding_settings)

    if not cv_processor.load_cv():
        logger.error("❌ CV yükleme başarısız!")
        return None

    if not cv_processor.create_cv_embedding():
        logger.error("❌ CV embedding oluşturma başarısız!")
        return None

    logger.info("✅ CV embedding oluşturuldu")
    return cv_processor


def _setup_vector_store(context: PipelineContext) -> VectorStore | None:  # pragma: no cover
    """Prepare vector store."""
    logger.info("\n🗃️ 3/6: Vector store hazırlığı...")
    vector_store = VectorStore(
        persist_directory=context.config["paths"]["chromadb_dir"],
        collection_name=context.config["vector_store_settings"]["collection_name"],
    )

    if not vector_store.create_collection():
        logger.error("❌ Vector store koleksiyon oluşturma başarısız!")
        return None

    return vector_store


def _process_job_embeddings(
    jobs_df: pd.DataFrame, vector_store: VectorStore
) -> list[list[float] | None]:  # pragma: no cover
    """Create embeddings for job descriptions."""
    embedding_service = EmbeddingService(**embedding_settings)
    logger.info("🔄 5/6: İş ilanları için AI embeddings oluşturuluyor...")

    job_embeddings: list[list[float] | None] = []
    for _, job in tqdm(jobs_df.iterrows(), total=len(jobs_df), desc="İlan Embeddings"):
        job_dict = job.to_dict()

        if vector_store.job_exists(job_dict):
            job_embeddings.append(None)
            continue

        if pd.notna(job.get("description", "")):
            try:
                embedding = embedding_service.create_embedding(str(job["description"]))
                job_embeddings.append(embedding)
            except (ValueError, TypeError, ConnectionError) as e:
                logger.warning("⚠️ Embedding oluşturma hatası: %s", e)
                job_embeddings.append(None)
            except Exception:
                logger.exception("❌ Unexpected error creating embedding")
                job_embeddings.append(None)
        else:
            job_embeddings.append(None)

    return job_embeddings


def _search_and_score_jobs(
    cv_embedding: list[float],
    vector_store: VectorStore,
    threshold: float,
    scoring_sys: IntelligentScoringSystem,
    context: PipelineContext,
) -> list[dict]:
    """Search and score jobs."""
    logger.info("\n🔄 6/6: Akıllı eşleştirme ve filtreleme...")

    top_k = config["vector_store_settings"]["top_k_results"]
    search_results = vector_store.search_jobs(cv_embedding, n_results=top_k)

    similar_jobs = [
        dict(metadata, similarity_score=(1 - dist) * 100)
        for metadata, dist in zip(
            search_results.get("metadatas", []), search_results.get("distances", []), strict=False
        )
    ]

    if not similar_jobs:
        return []

    logger.info("🔍 Sonuçlar akıllı puanlama ile değerlendiriliyor...")
    scored_jobs = score_jobs(similar_jobs, scoring_sys, debug=False)
    return [job for job in scored_jobs if job["similarity_score"] >= threshold]


def _analyse_single_job(job: dict, cv_summary: str, model, temperature: float) -> dict:  # pragma: no cover
    """Analyse a single job with Gemini for reranking."""
    description = job.get("description", "")[:TOKEN_LIMIT]
    prompt = RERANK_PROMPT_TEMPLATE.format(
        cv_summary=cv_summary,
        title=job.get("title", ""),
        description=description,
    )
    try:
        response = model.generate_content(prompt, generation_config={"temperature": temperature})
        text = response.text if hasattr(response, "text") else str(response)

        if not text or text.strip() == "":
            logger.warning("AI returned empty response for job %s, keeping original scores", job.get("title"))
            return job

        data = extract_json_from_response(text)

        if data is None:
            logger.warning(
                "Could not extract JSON from AI response for job %s, keeping original scores", job.get("title")
            )
            return job

        job.update(
            {
                "fit_score": data.get("fit_score", 0),
                "is_recommended": data.get("is_recommended", False),
                "reasoning": data.get("reasoning", ""),
                "matching_keywords": data.get("matching_keywords", []),
                "missing_keywords": data.get("missing_keywords", []),
            }
        )
    except google_exceptions.ResourceExhausted as exc:
        logger.warning(
            f"API rate limit or quota exhausted for job '{job.get('title')}'. Skipping AI analysis. Details: {exc}"
        )
    except google_exceptions.DeadlineExceeded as exc:
        logger.warning(f"API call timed out for job '{job.get('title')}'. Skipping AI analysis. Details: {exc}")
    except Exception as exc:
        logger.warning(f"Unexpected error during AI analysis for job '{job.get('title')}': {exc}", exc_info=True)
    return job


def _rerank_with_ai_analysis(jobs: list[dict], cv_summary: str) -> list[dict]:  # pragma: no cover
    """Deep analysis with Gemini to rerank jobs."""
    if not jobs:
        return []

    model_name = rerank_settings.get("llm_model", "gemini-1.5-flash-latest")
    temperature = rerank_settings.get("llm_temperature", 0.1)
    workers = rerank_settings.get("max_workers", 4)
    model = genai.GenerativeModel(model_name)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        analysed = list(executor.map(lambda j: _analyse_single_job(j, cv_summary, model, temperature), jobs))

    analysed.sort(
        key=lambda j: (not j.get("is_recommended", False), -j.get("fit_score", 0), -j.get("similarity_score", 0))
    )
    return analysed


def _process_and_load_jobs(
    csv_path: str, vector_store: VectorStore, context: PipelineContext
) -> None:  # pragma: no cover
    """Process and load jobs into vector store."""
    logger.info("🔄 4/6: İş ilanları vector store'a yükleniyor...")
    jobs_df = _load_and_validate_csv(csv_path)
    if jobs_df is None:
        return

    job_embeddings = _process_job_embeddings(jobs_df, vector_store)
    success = vector_store.add_jobs(jobs_df, job_embeddings)
    if not success:
        logger.error("❌ Vector store yükleme başarısız!")


def _collect_and_prepare_data(context: PipelineContext) -> tuple[str | None, list[float] | None, VectorStore | None]:
    """Collect job data and prepare vector store and embeddings."""
    csv_path = collect_data_for_all_personas(context)
    if not csv_path:
        logger.error("❌ Veri toplama başarısız - analiz durduruluyor!")
        return None, None, None

    cv_processor = _setup_cv_processor(context)
    if not cv_processor:
        return None, None, None

    cv_embedding = cv_processor.cv_embedding

    vector_store = _setup_vector_store(context)
    if not vector_store:
        return csv_path, None, None

    _process_and_load_jobs(csv_path, vector_store, context)
    return csv_path, cv_embedding, vector_store


def _score_and_rank_jobs(
    cv_embedding: list[float],
    vector_store: VectorStore,
    context: PipelineContext,
) -> list[dict]:
    """Search, score and optionally rerank jobs."""
    if context.scoring_system is None:
        logger.error("Scoring system is not configured. Cannot score jobs.")
        return []

    similar_jobs = _search_and_score_jobs(
        cv_embedding,
        vector_store,
        context.threshold,
        context.scoring_system,
        context,
    )

    if (
        rerank_settings.get("enabled", False)
        and context.ai_metadata.get("cv_summary")
        and context.rerank_flag
        and similar_jobs
    ):
        pool_size = rerank_settings.get("rerank_pool_size", len(similar_jobs))
        if pool_size <= 0:
            pool_size = len(similar_jobs)
        similar_jobs = _rerank_with_ai_analysis(
            similar_jobs[:pool_size],
            str(context.ai_metadata.get("cv_summary")),
        )
    return similar_jobs


def _execute_full_pipeline(context: PipelineContext) -> None:
    """Run the complete job matching pipeline using a context object."""
    logger.info("\n🔄 1/6: JobSpy Gelişmiş Özellikler ile veri toplama...")
    csv_path, cv_embedding, vector_store = _collect_and_prepare_data(context)
    if not csv_path or cv_embedding is None or vector_store is None:
        return

    if context.scoring_system is None:
        logger.error("Scoring system not configured")
        return

    similar_jobs = _score_and_rank_jobs(cv_embedding, vector_store, context)

    display_results(similar_jobs, context.threshold)
    try:
        jobs_df = pd.read_csv(Path(csv_path))
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
        logger.warning("Özet istatistikler için CSV okunamadı: %s", e)
        jobs_df = pd.DataFrame()
    except Exception:
        logger.exception("❌ Unexpected error reading CSV for summary statistics")
        jobs_df = pd.DataFrame()
    log_summary_statistics(jobs_df, similar_jobs, context.ai_metadata)


def analyze_and_find_best_jobs(
    selected_personas=None, results_per_site=None, similarity_threshold=None, rerank: bool = True
):
    """Run full pipeline and print best jobs via the orchestrator."""
    logger.info("\n🚀 Tam Otomatik AI Kariyer Analizi Başlatılıyor...")
    logger.info("=" * 60)

    args = SimpleNamespace(
        persona=selected_personas,
        results=results_per_site,
        threshold=similarity_threshold,
        no_rerank=not rerank,
    )

    pipeline = JobAnalysisPipeline(config)
    pipeline.run(args)


def run_end_to_end_pipeline(
    selected_personas=None, results_per_site=None, similarity_threshold=None, rerank: bool = True
):
    """Public wrapper to run the full analysis pipeline."""
    analyze_and_find_best_jobs(selected_personas, results_per_site, similarity_threshold, rerank)


__all__ = [
    "JobAnalysisPipeline",
    "collect_data_for_all_personas",
    "analyze_and_find_best_jobs",
    "run_end_to_end_pipeline",
]
