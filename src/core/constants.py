# src/core/constants.py
"""
Centralized constants to eliminate magic strings and numbers throughout the codebase.
Following the principle of configuration over hard-coding.
"""

# === PLATFORM CONSTANTS ===
SITE_INDEED = "indeed"
SITE_LINKEDIN = "linkedin"
SUPPORTED_SITES = (SITE_INDEED, SITE_LINKEDIN)

# === VECTOR STORE CONSTANTS ===
COSINE_METRIC = "cosine"
DEFAULT_COLLECTION_NAME = "job_embeddings"

# === DEFAULT SEARCH PARAMETERS ===
DEFAULT_SEARCH_PARAMS = {
    "location": "Turkey",
    "hours_old": 72,
    "results_per_site": 50,
    "max_workers": 4,  # For concurrent scraping
}

# === TIERED SEARCH CONFIGURATION ===
TIER_THRESHOLDS = {
    "tier2_activation": 10,  # Minimum results before activating tier 2
    "tier3_activation": 5,  # Minimum results before activating tier 3 (fallback)
}

# === PLATFORM-SPECIFIC CONFIGURATIONS ===
PLATFORM_CONFIGS = {
    SITE_LINKEDIN: {
        "max_or_operators": 2,  # LinkedIn Doctrine: Limit OR usage
        "fetch_description": True,
        "preferred_tier": "tier1",  # LinkedIn works best with precise queries
    },
    SITE_INDEED: {
        "max_or_operators": 5,  # Indeed handles more complex queries
        "country_param": "Turkey",
        "title_operator_required": True,  # Indeed Doctrine: title:() is mandatory
        "preferred_tier": "tier2",  # Indeed excels with alias searches
    },
}

# === PERSONA BUILDING CONSTANTS ===
PERSONA_DEFAULTS = {
    "hours_old": 72,
    "results": 20,
}

# === DEDUPLICATION COLUMNS ===
DEDUP_COLUMNS = ["title", "company", "location"]

# === FILE PATH CONSTANTS ===
# Note: Directory paths are now constructed at runtime to support installed packages
# These will be built lazily when needed, avoiding hardcoded repository assumptions

# === QUERY BUILDING CONSTANTS ===
NEGATIVE_FILTERS = ("-Senior", "-Kıdemli", "-Lead", "-Principal", "-Direktör")
