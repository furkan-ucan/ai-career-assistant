"""Core processing pipeline for job matching."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import google.generativeai as genai
import pandas as pd
from tqdm import tqdm

from .config import load_settings
from .cv_analyzer import TOKEN_LIMIT, CVAnalyzer
from .cv_processor import CVProcessor
from .data_collector import collect_job_data
from .embedding_service import EmbeddingService
from .exceptions import CVNotFoundError
from .filter import score_jobs
from .intelligent_scoring import IntelligentScoringSystem
from .persona_builder import build_dynamic_personas
from .reporting import display_results, log_summary_statistics
from .utils.file_helpers import save_dataframe_csv
from .vector_store import VectorStore

RERANK_PROMPT_TEMPLATE = """
You are an expert career assistant. Candidate summary: {cv_summary}

JOB TITLE: {title}
JOB DESCRIPTION: {description}

Return ONLY JSON with fields:
{{
  "fit_score": int,          # 0-100 suitability
  "is_recommended": bool,    # True if worth applying
  "reasoning": str,          # short reasoning
  "matching_keywords": [str],
  "missing_keywords": [str]
}}
"""

logger = logging.getLogger(__name__)

config = load_settings()

scoring_system: IntelligentScoringSystem | None = None

embedding_settings = config.get("embedding_settings", {})

job_settings = config["job_search_settings"]
MIN_SIMILARITY_THRESHOLD = job_settings["min_similarity_threshold"]
TARGET_SITES = job_settings["target_sites"]
DEFAULT_HOURS_OLD = job_settings["default_hours_old"]
DEFAULT_RESULTS_PER_PERSONA_SITE = job_settings["default_results_per_site"]

persona_search_config = config["persona_search_configs"]

rerank_settings = config.get("ai_reranking_settings", {})


def _collect_jobs_for_persona(
    persona_name: str, persona_cfg: dict, results_per_site: int | None
) -> pd.DataFrame | None:
    """Collect jobs for a single persona."""
    logger.info("\n--- Persona '%s' için JobSpy Gelişmiş Arama ---", persona_name)
    logger.info("🎯 Optimize edilmiş terim: '%s'", persona_cfg["term"])
    logger.info("⏰ Tarih filtresi: Son %s saat", persona_cfg["hours_old"])

    try:
        max_results = results_per_site if results_per_site is not None else persona_cfg["results"]
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


def _deduplicate_and_save_jobs(all_jobs_list: list[pd.DataFrame]) -> str | None:
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

    output_dir = Path(config["paths"]["data_dir"])
    csv_path = save_dataframe_csv(final_df, output_dir, "jobspy_optimize_ilanlar")
    logger.info("📁 JobSpy optimize edilmiş veriler: %s", csv_path)
    return str(csv_path)


def collect_data_for_all_personas(selected_personas=None, results_per_site=None, persona_configs=None):
    """Collect data for all personas and return CSV path."""
    logger.info("🔍 JobSpy Gelişmiş Özellikler ile Stratejik Veri Toplama Başlatılıyor...")
    logger.info("=" * 70)

    all_collected_jobs_list = []
    cfg = persona_configs or persona_search_config
    personas = cfg.items()
    if selected_personas:
        personas = [(p, cfg[p]) for p in selected_personas if p in cfg]

    for persona_name, persona_cfg in tqdm(personas, desc="Persona Aramaları"):
        jobs_df = _collect_jobs_for_persona(persona_name, persona_cfg, results_per_site)
        if jobs_df is not None:
            all_collected_jobs_list.append(jobs_df)

    return _deduplicate_and_save_jobs(all_collected_jobs_list)


def _setup_ai_metadata_and_personas() -> tuple[dict, dict]:
    """
    Extracts AI metadata from the CV and determines the personas configuration.

    Returns:
        ai_metadata (dict): Metadata extracted from the CV, including target job titles and skill information.
        personas_cfg (dict): Persona configuration, dynamically built from AI metadata if available, otherwise static.

    Raises:
        CVNotFoundError: If CV processing fails.
    """
    try:
        cv_text = Path(config["paths"]["cv_file"]).read_text(encoding="utf-8")
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

    return ai_metadata, personas_cfg


def _validate_skill_metadata(key_skills: object, skill_importance: object) -> bool:
    """Validate skill metadata structure and types."""
    return (
        isinstance(key_skills, list)
        and isinstance(skill_importance, list)
        and len(key_skills) == len(skill_importance)
        and all(isinstance(skill, str) for skill in key_skills)
        and all(isinstance(score, int | float) for score in skill_importance)
    )


def _apply_skill_weights(skill: str, importance: float, base_weight: int, min_imp: float) -> None:
    """Apply dynamic weight based on skill importance."""
    if importance >= min_imp:
        weight = int(round(base_weight * importance))
        config["scoring_system"]["description_weights"]["positive"][skill] = weight
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


def _configure_scoring_system(ai_metadata: dict) -> bool:
    """Configure the scoring system with AI metadata and skill importance."""
    global scoring_system
    try:
        if not (ai_metadata.get("key_skills") and ai_metadata.get("skill_importance")):
            logger.info("No AI skill data available - using static scoring")
            scoring_system = IntelligentScoringSystem(config)
            return True

        key_skills = ai_metadata["key_skills"]
        skill_importance = ai_metadata["skill_importance"]

        if not _validate_skill_metadata(key_skills, skill_importance):
            logger.warning("AI metadata skills format invalid - using static scoring")
            scoring_system = IntelligentScoringSystem(config)
            return True

        base_weight = config["scoring_system"].get("dynamic_skill_weight", 10)
        min_imp = config["scoring_system"].get("min_importance_for_scoring", 0.75)
        logger.info("🎯 Configuring enhanced scoring with %s AI-detected skills", len(key_skills))

        if len(skill_importance) != len(key_skills):
            skill_importance = [1.0] * len(key_skills)

        for skill, importance in zip(key_skills, skill_importance, strict=False):
            _apply_skill_weights(skill, float(importance), base_weight, min_imp)

        logger.info("✅ Enhanced AI-driven scoring system configured")
        scoring_system = IntelligentScoringSystem(config)
        return True
    except (ValueError, TypeError, KeyError) as e:
        logger.error("❌ Scoring system configuration failed: %s", e)
        return False
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


def _setup_cv_processor() -> CVProcessor | None:
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


def _setup_vector_store() -> VectorStore | None:
    """Prepare vector store."""
    logger.info("\n🗃️ 3/6: Vector store hazırlığı...")
    vector_store = VectorStore(
        persist_directory=config["paths"]["chromadb_dir"],
        collection_name=config["vector_store_settings"]["collection_name"],
    )

    if not vector_store.create_collection():
        logger.error("❌ Vector store koleksiyon oluşturma başarısız!")
        return None

    return vector_store


def _process_job_embeddings(jobs_df: pd.DataFrame, vector_store: VectorStore) -> list[list[float] | None]:
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


def _search_and_score_jobs(cv_embedding: list[float], vector_store: VectorStore, threshold: float) -> list[dict]:
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
    scored_jobs = score_jobs(similar_jobs, scoring_system, debug=False)
    return [job for job in scored_jobs if job["similarity_score"] >= threshold]


def _analyse_single_job(job: dict, cv_summary: str, model, temperature: float) -> dict:
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
        text = text.strip().strip("`")
        data = json.loads(text)
        job.update(
            {
                "fit_score": data.get("fit_score", 0),
                "is_recommended": data.get("is_recommended", False),
                "reasoning": data.get("reasoning", ""),
                "matching_keywords": data.get("matching_keywords", []),
                "missing_keywords": data.get("missing_keywords", []),
            }
        )
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse AI response for job %s: %s", job.get("title"), exc)
    except Exception as exc:
        # Handle rate limit and other API errors gracefully
        if "ResourceExhausted" in str(exc) or "429" in str(exc):
            logger.warning("API rate limit reached for job %s, skipping AI analysis", job.get("title"))
        else:
            logger.exception("Unexpected error during AI analysis for job %s", job.get("title"))
    return job


def _rerank_with_ai_analysis(jobs: list[dict], cv_summary: str) -> list[dict]:
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


def _process_and_load_jobs(csv_path: str, vector_store: VectorStore):
    """Process and load jobs into vector store."""
    logger.info("🔄 4/6: İş ilanları vector store'a yükleniyor...")
    jobs_df = _load_and_validate_csv(csv_path)
    if jobs_df is None:
        return

    job_embeddings = _process_job_embeddings(jobs_df, vector_store)
    success = vector_store.add_jobs(jobs_df, job_embeddings)
    if not success:
        logger.error("❌ Vector store yükleme başarısız!")


def _execute_full_pipeline(
    selected_personas, results_per_site, personas_cfg, threshold, ai_metadata, rerank_flag: bool = True
):
    """
    Runs the complete job matching pipeline, including job data collection, CV processing, embedding creation, vector storage, job scoring, result display, and summary statistics logging.

    Parameters:
        selected_personas (list[str] | None): List of persona names to process, or None to use all configured personas.
        results_per_site (int | None): Number of job results to collect per site, or None for default.
        personas_cfg (dict): Configuration dictionary for personas.
        threshold (float): Minimum similarity threshold for job matching.
        ai_metadata (dict): AI-extracted metadata for reporting.
        rerank_flag (bool): Whether to run the AI reranking stage.
    """
    logger.info("\n🔄 1/6: JobSpy Gelişmiş Özellikler ile veri toplama...")
    csv_path = collect_data_for_all_personas(selected_personas, results_per_site, personas_cfg)
    if not csv_path:
        logger.error("❌ Veri toplama başarısız - analiz durduruluyor!")
        return

    cv_processor = _setup_cv_processor()
    if not cv_processor:
        return

    if not cv_processor.create_cv_embedding():
        logger.error("❌ CV embedding oluşturma başarısız!")
        return

    cv_embedding = cv_processor.cv_embedding
    logger.info("✅ CV embedding oluşturuldu")

    vector_store = _setup_vector_store()
    if not vector_store:
        return

    _process_and_load_jobs(csv_path, vector_store)

    if cv_embedding is None:
        logger.error("❌ CV embedding oluşturulamadı, arama yapılamıyor")
        return

    similar_jobs = _search_and_score_jobs(cv_embedding, vector_store, threshold)

    if rerank_settings.get("enabled", False) and ai_metadata.get("cv_summary") and rerank_flag and similar_jobs:
        pool_size = rerank_settings.get("rerank_pool_size", len(similar_jobs))
        if pool_size <= 0:
            pool_size = len(similar_jobs)
        similar_jobs = _rerank_with_ai_analysis(similar_jobs[:pool_size], str(ai_metadata.get("cv_summary")))

    display_results(similar_jobs, threshold)
    try:
        jobs_df = pd.read_csv(Path(csv_path))
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
        logger.warning("Özet istatistikler için CSV okunamadı: %s", e)
        jobs_df = pd.DataFrame()
    except Exception:
        logger.exception("❌ Unexpected error reading CSV for summary statistics")
        jobs_df = pd.DataFrame()
    log_summary_statistics(jobs_df, similar_jobs, ai_metadata)


def analyze_and_find_best_jobs(
    selected_personas=None, results_per_site=None, similarity_threshold=None, rerank: bool = True
):
    """Run full pipeline and print best jobs."""
    logger.info("\n🚀 Tam Otomatik AI Kariyer Analizi Başlatılıyor...")
    logger.info("=" * 60)

    threshold = similarity_threshold if similarity_threshold is not None else MIN_SIMILARITY_THRESHOLD

    try:
        ai_metadata, personas_cfg = _setup_ai_metadata_and_personas()
    except CVNotFoundError as e:
        logger.error("İşlem durduruldu: %s", e)
        return None

    if not _configure_scoring_system(ai_metadata):
        return

    _execute_full_pipeline(selected_personas, results_per_site, personas_cfg, threshold, ai_metadata, rerank)


def run_end_to_end_pipeline(
    selected_personas=None, results_per_site=None, similarity_threshold=None, rerank: bool = True
):
    """Public wrapper to run the full analysis pipeline."""
    analyze_and_find_best_jobs(selected_personas, results_per_site, similarity_threshold, rerank)


__all__ = [
    "collect_data_for_all_personas",
    "analyze_and_find_best_jobs",
    "run_end_to_end_pipeline",
    "_validate_skill_metadata",
    "_apply_skill_weights",
    "_configure_scoring_system",
]
