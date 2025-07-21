# src/data_collector.py
"""
Refactored job data collection module - Clean, efficient, and maintainable.

Following Single Responsibility Principle and DRY guidelines.
Implements Dr. Finch's tiered search strategy with proper separation of concerns.
"""

# Standard Library
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Third Party
import pandas as pd
from jobspy import scrape_jobs

# Local imports
from .core.constants import (
    DEDUP_COLUMNS,
    DEFAULT_SEARCH_PARAMS,
    SITE_INDEED,
    SITE_LINKEDIN,
    SUPPORTED_SITES,
    TIER_THRESHOLDS,
)
from .core.utils import add_metadata_to_dataframe, handle_scraping_error, safe_dataframe_concat, setup_enhanced_logging

logger = setup_enhanced_logging(__name__)


class TieredJobCollector:
    """
    Handles tiered job collection following Dr. Finch's strategic doctrine.

    Separates concerns: strategy execution, site scraping, and result aggregation.
    """

    def __init__(self, search_params: dict | None = None):
        """Initialize with configurable search parameters."""
        self.search_params = {**DEFAULT_SEARCH_PARAMS, **(search_params or {})}
        self.tier_thresholds = TIER_THRESHOLDS

    def collect_with_platform_queries(
        self, platform_queries: dict[str, str], persona_name: str, site_names: list[str] | None = None
    ) -> pd.DataFrame | None:
        """
        Main entry point for tiered collection using platform-specific queries.

        Args:
            platform_queries: Dict of platform_tier -> query mappings
            persona_name: Name for logging and metadata
            site_names: Sites to search (defaults to all supported)

        Returns:
            Combined results DataFrame or None
        """
        logger.info(f"\n🎯 === Dr. Finch Protocol: Persona '{persona_name}' ===")

        sites_to_search = site_names or SUPPORTED_SITES
        site_results = []

        for site in sites_to_search:
            site_df = self._collect_for_single_site(site, platform_queries, persona_name)
            if site_df is not None and not site_df.empty:
                site_results.append(site_df)

        if not site_results:
            logger.warning(f"❌ No results found for persona '{persona_name}'")
            return None

        # Combine all site results efficiently
        combined_df = safe_dataframe_concat(site_results, dedup_columns=DEDUP_COLUMNS)

        # Add persona metadata
        combined_df = add_metadata_to_dataframe(combined_df, {"persona_source": persona_name})

        logger.info(f"🎯 Persona '{persona_name}' final: {len(combined_df)} unique jobs")
        return combined_df

    def _collect_for_single_site(
        self, site: str, platform_queries: dict[str, str], persona_name: str
    ) -> pd.DataFrame | None:
        """Collect jobs for a single site using tiered strategy."""
        logger.info(f"\n--- Site '{site.upper()}' strategic search ---")

        tier_results: list[pd.DataFrame] = []

        # Execute tiers in sequence, with intelligent fallback
        for tier_num in [1, 2, 3]:
            should_run_tier = self._should_run_tier(tier_num, tier_results)

            if should_run_tier:
                tier_df = self._execute_tier(site, tier_num, platform_queries)
                if tier_df is not None and not tier_df.empty:
                    tier_results.append(tier_df)
                    logger.info(f"✅ TIER {tier_num} ({site}): {len(tier_df)} jobs")

        if not tier_results:
            return None

        # Combine tiers for this site
        site_df = safe_dataframe_concat(tier_results, dedup_columns=DEDUP_COLUMNS)
        logger.info(f"� {site} total: {len(site_df)} unique jobs")

        return site_df

    def _should_run_tier(self, tier_num: int, previous_results: list[pd.DataFrame]) -> bool:
        """Determine if a tier should be executed based on previous results."""
        if tier_num == 1:
            return True  # Always run tier 1

        total_results = sum(len(df) for df in previous_results if df is not None)

        if tier_num == 2:
            return total_results < self.tier_thresholds["tier2_activation"]
        elif tier_num == 3:
            return total_results < self.tier_thresholds["tier3_activation"]

        return False

    def _execute_tier(self, site: str, tier_num: int, platform_queries: dict[str, str]) -> pd.DataFrame | None:
        """Execute a specific tier search for a site."""
        query_key = f"{site}_tier{tier_num}_query"
        query = platform_queries.get(query_key)

        if not query:
            logger.debug(f"No query defined for {query_key}")
            return None

        logger.info(f"🔍 TIER {tier_num} ({site}): {query}")

        try:
            jobs_df = self._scrape_single_site(site, query)
            if jobs_df is not None and not jobs_df.empty:
                # Add tier metadata
                jobs_df = add_metadata_to_dataframe(
                    jobs_df, {"search_tier": f"tier{tier_num}", "query_used": query, "source_site": site}
                )
                return jobs_df
        except Exception as e:
            handle_scraping_error(e, f"TIER {tier_num} {site} scraping", logger)

        return None

    def _scrape_single_site(self, site: str, search_term: str) -> pd.DataFrame | None:
        """Execute actual scraping for a site with proper error handling."""
        try:
            scrape_params = {
                "site_name": site,
                "search_term": search_term,
                "location": self.search_params["location"],
                "results_wanted": self.search_params["results_per_site"],
                "hours_old": self.search_params["hours_old"],
            }

            # Site-specific parameters
            if site == SITE_INDEED:
                scrape_params["country_indeed"] = "Turkey"
            elif site == SITE_LINKEDIN:
                scrape_params["linkedin_fetch_description"] = True

            jobs_df = scrape_jobs(**scrape_params)
            # Type safety: ensure we return DataFrame or None
            if jobs_df is not None and hasattr(jobs_df, "empty"):
                return pd.DataFrame(jobs_df)  # Explicit cast to DataFrame
            return None

        except Exception as e:
            handle_scraping_error(e, f"{site} scraping", logger)
            return None


# Legacy functions for backward compatibility
def collect_job_data_with_tiers(
    platform_queries: dict[str, str],
    persona_name: str,
    location: str = "Turkey",  # Explicit default instead of dict lookup
    max_results_per_site: int = 50,  # Explicit default
    site_names: list[str] | None = None,
    hours_old: int = 72,  # Explicit default
) -> pd.DataFrame | None:
    """
    Legacy wrapper for the refactored TieredJobCollector.

    Maintained for backward compatibility while the system transitions.
    """
    search_params = {
        "location": location,
        "results_per_site": max_results_per_site,
        "hours_old": hours_old,
    }

    collector = TieredJobCollector(search_params)
    return collector.collect_with_platform_queries(platform_queries, persona_name, site_names)


def collect_job_data(
    search_term,
    location=DEFAULT_SEARCH_PARAMS["location"],
    max_results_per_site=DEFAULT_SEARCH_PARAMS["results_per_site"],
    site_names=None,
    hours_old=DEFAULT_SEARCH_PARAMS["hours_old"],
) -> pd.DataFrame | None:
    """
    LEGACY FUNCTION - Maintained for backward compatibility.

    For new development, use TieredJobCollector class directly.
    """
    logger.info("\n🔍 Legacy JobSpy Search (consider upgrading to TieredJobCollector)")
    logger.info(f"🔍 Search term: '{search_term}'")

    site_names = site_names or SUPPORTED_SITES
    all_jobs_list = []

    with ThreadPoolExecutor(max_workers=len(site_names)) as executor:
        future_to_site = {
            executor.submit(_legacy_scrape_site, site, search_term, location, max_results_per_site, hours_old): site
            for site in site_names
        }
        for future in as_completed(future_to_site):
            result = future.result()
            if result is not None:
                all_jobs_list.append(result)

    if not all_jobs_list:
        logger.error("❌ No jobs found from any site!")
        return None

    # Use the improved concatenation utility
    combined_df = safe_dataframe_concat(all_jobs_list, dedup_columns=DEDUP_COLUMNS)
    combined_df = add_metadata_to_dataframe(combined_df, {"search_term_used": search_term})

    logger.info(f"✅ Legacy search completed: {len(combined_df)} unique jobs")
    return combined_df


def _legacy_scrape_site(
    site: str, search_term: str, location: str, max_results_per_site: int, hours_old: int
) -> pd.DataFrame | None:
    """Legacy scraping function for backward compatibility."""
    logger.info(f"\n--- Searching site '{site}' ---")
    try:
        scrape_params = {
            "site_name": site,
            "search_term": search_term,
            "location": location,
            "results_wanted": max_results_per_site,
            "hours_old": hours_old,
        }

        if site == SITE_INDEED:
            scrape_params["country_indeed"] = "Turkey"
            logger.info("   🎯 Indeed: Turkey-specific settings active")
        elif site == SITE_LINKEDIN:
            scrape_params["linkedin_fetch_description"] = True
            logger.info("   💼 LinkedIn: Fetching detailed descriptions...")

        jobs_from_site = scrape_jobs(**scrape_params)
        # Type safety: ensure DataFrame handling
        if jobs_from_site is not None and hasattr(jobs_from_site, "empty") and not jobs_from_site.empty:
            logger.info(f"✅ '{site}': {len(jobs_from_site)} jobs collected")
            jobs_from_site["source_site"] = site
            return pd.DataFrame(jobs_from_site)  # Explicit DataFrame cast
        logger.info(f"ℹ️ '{site}': No jobs found for this search term")
    except Exception as e:
        handle_scraping_error(e, f"Legacy {site} scraping", logger)
    return None


# CSV saving function (optional utility)
def save_jobs_to_csv(jobs_df, filename_prefix="jobspy_jobs"):
    """Save job DataFrame to CSV file."""
    if jobs_df is None or jobs_df.empty:
        logger.error("❌ No data to save!")
        return None

    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"{filename_prefix}_{timestamp}.csv"

    jobs_df.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info(f"📁 File saved: {csv_path}")

    return csv_path


if __name__ == "__main__":
    # Test the refactored system
    logger.info("🧪 Testing Refactored JobSpy System...")

    test_df = collect_job_data(search_term="Software Engineer", max_results_per_site=10, hours_old=72)

    if test_df is not None:
        logger.info(f"\n✅ Test result: {len(test_df)} jobs found")
        logger.info(f"📊 Site distribution: {test_df['source_site'].value_counts().to_dict()}")
        save_jobs_to_csv(test_df, "test_refactored_jobspy")
    else:
        logger.error("❌ Test failed!")
