# src/config_models.py
"""
Configuration validation models using Pydantic
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobSearchSettings(BaseModel):
    """Job search configuration settings."""

    target_sites: list[str] = Field(default=["linkedin", "indeed"], description="Sites to search for jobs")
    default_hours_old: int = Field(default=72, ge=1, le=720, description="Default hours for job age")
    default_results_per_site: int = Field(default=25, ge=1, le=100, description="Results per site and persona")
    min_similarity_threshold: float = Field(default=60.0, ge=0.0, le=100.0, description="Minimum similarity threshold")

    @field_validator("target_sites")
    @classmethod
    def validate_sites(cls, v: list[str]) -> list[str]:
        valid_sites = {"linkedin", "indeed", "glassdoor", "monster"}
        invalid_sites = [site for site in v if site not in valid_sites]
        if invalid_sites:
            raise ValueError(f"Invalid sites: {invalid_sites}. Valid sites: {valid_sites}")
        return v


class PersonaSearchConfig(BaseModel):
    """Individual persona search configuration."""

    term: str = Field(description="Search term for the persona")
    hours_old: int = Field(default=72, ge=1, le=720, description="Hours old for this persona")
    results: int = Field(default=25, ge=1, le=100, description="Number of results for this persona")


class PathsConfig(BaseModel):
    """File paths configuration."""

    data_dir: str = Field(default="data", description="Data directory path")
    cv_file: str = Field(default="data/cv.txt", description="CV file path")
    chromadb_dir: str = Field(default="data/chromadb", description="ChromaDB directory")
    logs_dir: str = Field(default="logs", description="Logs directory")

    @field_validator("cv_file")
    @classmethod
    def validate_cv_file_exists(cls, v: str) -> str:
        cv_path = Path(v)
        if not cv_path.exists():
            raise ValueError(f"CV file does not exist: {v}")
        return v


class EmbeddingSettings(BaseModel):
    """Embedding service configuration."""

    batch_size: int = Field(default=10, ge=1, le=50, description="Embedding batch size")
    retry_count: int = Field(default=3, ge=1, le=10, description="Number of retries")
    rate_limit_delay: float = Field(default=0.1, ge=0.0, le=5.0, description="Rate limit delay in seconds")


class VectorStoreSettings(BaseModel):
    """Vector store configuration."""

    collection_name: str = Field(default="job_embeddings", description="ChromaDB collection name")
    similarity_metric: str = Field(default="cosine", description="Similarity metric")
    top_k_results: int = Field(default=50, ge=1, le=200, description="Top K results to retrieve")

    @field_validator("similarity_metric")
    @classmethod
    def validate_metric(cls, v: str) -> str:
        valid_metrics = {"cosine", "euclidean", "manhattan"}
        if v not in valid_metrics:
            raise ValueError(f"Invalid similarity metric: {v}. Valid metrics: {valid_metrics}")
        return v


class ScoringWeights(BaseModel):
    """Scoring system weights."""

    negative: int = Field(default=-30, description="Negative score weight")
    positive: int = Field(default=30, description="Positive score weight")


class TitleKeywords(BaseModel):
    """Title keywords configuration."""

    negative: list[str] = Field(
        default_factory=lambda: ["senior", "sr.", "lead"], description="Negative title keywords"
    )
    positive: list[str] = Field(default_factory=lambda: ["junior", "entry"], description="Positive title keywords")


class DescriptionWeights(BaseModel):
    """Description weights configuration."""

    positive: dict[str, int] = Field(default_factory=dict, description="Positive description keyword weights")
    negative: dict[str, int] = Field(default_factory=dict, description="Negative description keyword weights")


class ScoringSystemConfig(BaseModel):
    """Scoring system configuration."""

    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    title_keywords: TitleKeywords = Field(default_factory=TitleKeywords)
    description_weights: DescriptionWeights = Field(
        default_factory=DescriptionWeights, description="Description keyword weights"
    )
    experience_penalties: dict[str, int] = Field(default_factory=dict, description="Experience penalties")
    cv_skill_keywords: list[str] = Field(default_factory=list, description="CV skill keywords")
    threshold: float = Field(default=60.0, ge=0.0, le=100.0, description="Scoring threshold")
    cv_skill_boost_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="CV skill boost threshold")
    cv_skill_bonus_points: int = Field(default=10, ge=0, le=100, description="CV skill bonus points")
    dynamic_skill_weight: int = Field(default=10, ge=0, le=50, description="Dynamic skill weight")
    min_importance_for_scoring: float = Field(default=0.75, ge=0.0, le=1.0, description="Min importance for scoring")


class CVAnalyzerSettings(BaseModel):
    """CV analyzer configuration."""

    prompt_version: str = Field(default="v2.0", description="Prompt version")
    token_limit: int = Field(default=4000, ge=1000, le=10000, description="Token limit")


class AIRerankingSettings(BaseModel):
    """AI reranking configuration."""

    enabled: bool = Field(default=True, description="Enable AI reranking")
    rerank_pool_size: int = Field(default=75, ge=10, le=200, description="Pool size for reranking")
    max_workers: int = Field(default=2, ge=1, le=10, description="Max workers for parallel processing")
    llm_model: str = Field(default="gemini-2.5-flash", description="LLM model for reranking")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="LLM temperature")


class RerankingCacheConfig(BaseModel):
    """Reranking cache configuration."""

    enabled: bool = Field(default=True, description="Enable reranking cache")
    max_age_days: int = Field(default=30, ge=1, le=365, description="Maximum cache age in days")
    only_rerank_new: bool = Field(default=True, description="Only rerank new jobs")
    store_fields: list[str] = Field(
        default_factory=lambda: [
            "ai_fit_score",
            "ai_reasoning",
            "ai_matching_keywords",
            "ai_missing_keywords",
            "last_analyzed",
        ],
        description="Fields to store in cache",
    )


class PersonaBuilderSettings(BaseModel):
    """Persona builder configuration."""

    role_results: dict[str, int] = Field(
        default_factory=lambda: {"developer": 30, "analyst": 25}, description="Role-specific results"
    )
    default_results: int = Field(default=20, ge=1, le=100, description="Default results per persona")
    default_hours_old: int = Field(default=72, ge=1, le=720, description="Default hours old")


class PerformanceConfig(BaseModel):
    """Performance and caching configuration."""

    cache_ttl_days: int = Field(default=30, ge=1, le=365, description="Cache TTL in days")
    max_cache_size_mb: int = Field(default=500, ge=10, le=5000, description="Max cache size in MB")
    cleanup_interval_hours: int = Field(default=24, ge=1, le=168, description="Cleanup interval in hours")


class AppConfig(BaseModel):
    """Main application configuration model."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    # API Keys - Optional in YAML, required from environment
    gemini_api_key: str | None = Field(default=None, description="Gemini API key (from environment)")
    github_token: str | None = Field(default=None, description="GitHub token (from environment)")
    gemini_model: str = Field(default="gemini-2.5-flash", description="Gemini model name")
    embedding_model: str = Field(default="text-embedding-004", description="Embedding model name")

    # Configuration sections
    job_search_settings: JobSearchSettings = Field(default_factory=JobSearchSettings)
    persona_search_configs: dict[str, PersonaSearchConfig] = Field(default_factory=dict)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    embedding_settings: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    vector_store_settings: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    scoring_system: ScoringSystemConfig = Field(default_factory=ScoringSystemConfig)
    cv_analyzer_settings: CVAnalyzerSettings = Field(default_factory=CVAnalyzerSettings)
    ai_reranking_settings: AIRerankingSettings = Field(default_factory=AIRerankingSettings)
    reranking_cache: RerankingCacheConfig = Field(default_factory=RerankingCacheConfig)
    persona_builder_settings: PersonaBuilderSettings = Field(default_factory=PersonaBuilderSettings)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    @field_validator("persona_search_configs")
    @classmethod
    def validate_persona_configs(cls, v: dict[str, Any]) -> dict[str, PersonaSearchConfig]:
        """Convert dict values to PersonaSearchConfig objects."""
        validated = {}
        for key, value in v.items():
            if isinstance(value, dict):
                validated[key] = PersonaSearchConfig(**value)
            elif isinstance(value, PersonaSearchConfig):
                validated[key] = value
            else:
                raise ValueError(f"Invalid persona config for {key}: {value}")
        return validated

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format compatible with existing code."""
        data: dict[str, Any] = self.model_dump()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        """Create config from dictionary."""
        instance = cls(**data)
        return instance
