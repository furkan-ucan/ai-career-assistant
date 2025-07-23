# src/core/constants.py
"""
Centralized constants to eliminate magic strings and numbers throughout the codebase.
Following the principle of configuration over hard-coding.
"""

from pathlib import Path

# === PLATFORM CONSTANTS ===
SITE_INDEED = "indeed"
SITE_LINKEDIN = "linkedin"
SUPPORTED_SITES = [SITE_INDEED, SITE_LINKEDIN]

# === DEFAULT SEARCH PARAMETERS ===
DEFAULT_SEARCH_PARAMS = {
    "location": "Turkey",
    "hours_old": 72,
    "results_per_site": 50,
    "max_workers": 2,  # For concurrent scraping
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
ENHANCED_DEDUP_COLUMNS = ["title", "company", "location", "description_short"]

# === LOGGING CONFIGURATION ===
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
}

# === FILE PATH CONSTANTS ===
# Repository root (where this file's parent.parent.parent is located)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = _REPO_ROOT / "data"
LOGS_DIR = _REPO_ROOT / "logs"
CONFIG_DIR = _REPO_ROOT / "config"
PROMPTS_DIR = _REPO_ROOT / "prompts"

# === QUERY BUILDING CONSTANTS ===
NEGATIVE_FILTERS = ["-Senior", "-Kıdemli", "-Lead", "-Principal", "-Direktör"]

# === ERROR HANDLING CONSTANTS ===
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 30
CRITICAL_ERRORS = (SystemError, MemoryError, KeyboardInterrupt)

# === PERFORMANCE THRESHOLDS ===
MAX_FUNCTION_LENGTH = 30  # Lines - SRP guideline
MAX_CONCAT_OPERATIONS = 1  # Per function - Performance guideline
MAX_DATAFRAME_SIZE = 10000  # Rows - Memory management
