# src/data_collector.py
"""Refactored job data collection module, hardened against network errors."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from jobspy import scrape_jobs
from tenacity import retry, stop_after_attempt, wait_exponential

from .core.constants import (
    DEDUP_COLUMNS,
    DEFAULT_SEARCH_PARAMS,
    SITE_INDEED,
    SITE_LINKEDIN,
    SUPPORTED_SITES,
    TIER_THRESHOLDS,
)
from .core.utils import add_metadata_to_dataframe, handle_scraping_error, safe_dataframe_concat

logger = logging.getLogger(__name__)


class TieredJobCollector:
    """Handles tiered job collection with improved resilience."""

    def __init__(self, search_params: dict | None = None):
        self.search_params = {**DEFAULT_SEARCH_PARAMS, **(search_params or {})}
        self.tier_thresholds = TIER_THRESHOLDS

    def collect_with_platform_queries(
        self, platform_queries: dict[str, str], persona_name: str, site_names: list[str] | None = None
    ) -> pd.DataFrame | None:
        logger.info(f"\n🎯 Dr. Finch Protocol Activated: Persona '{persona_name}'")
        sites_to_search = site_names or SUPPORTED_SITES
        site_results: list[pd.DataFrame] = []

        with ThreadPoolExecutor(max_workers=len(sites_to_search)) as executor:
            future_to_site = {
                executor.submit(self._collect_for_single_site, site, platform_queries): site
                for site in sites_to_search
            }
            for future in as_completed(future_to_site):
                site = future_to_site[future]
                try:
                    site_df = future.result()
                    if site_df is not None and not site_df.empty:
                        site_results.append(site_df)
                except Exception:
                    logger.exception(f"Error collecting data for site: {site}")

        if not site_results:
            logger.warning(f"❌ No results found for persona '{persona_name}' on any site.")
            return None

        combined_df = safe_dataframe_concat(site_results, dedup_columns=DEDUP_COLUMNS)
        combined_df = add_metadata_to_dataframe(combined_df, {"persona_source": persona_name})
        return combined_df

    def _collect_for_single_site(self, site: str, platform_queries: dict[str, str]) -> pd.DataFrame | None:
        logger.info(f"-- Executing strategic search on {site.upper()} --")
        tier_results: list[pd.DataFrame] = []
        for tier_num in [1, 2, 3]:
            if not self._should_run_tier(tier_num, tier_results):
                continue
            tier_df = self._execute_tier(site, tier_num, platform_queries)
            if tier_df is not None and not tier_df.empty:
                tier_results.append(tier_df)
        return safe_dataframe_concat(tier_results, dedup_columns=DEDUP_COLUMNS) if tier_results else None

    def _should_run_tier(self, tier_num: int, previous_results: list[pd.DataFrame]) -> bool:
        if tier_num == 1:
            return True
        total_results = sum(len(df) for df in previous_results if df is not None)
        return total_results < (
            self.tier_thresholds["tier2_activation"] if tier_num == 2 else self.tier_thresholds["tier3_activation"]
        )

    def _execute_tier(self, site: str, tier_num: int, platform_queries: dict[str, str]) -> pd.DataFrame | None:
        query = platform_queries.get(f"{site}_tier{tier_num}_query")
        if not query:
            return None
        logger.info(f"🔍 TIER {tier_num} ({site}): Searching for '{query}'")
        try:
            jobs_df = self._scrape_single_site_with_retry(site, query)
            if jobs_df is not None and not jobs_df.empty:
                return add_metadata_to_dataframe(
                    jobs_df, {"search_tier": f"tier{tier_num}", "query_used": query, "source_site": site}
                )
        except Exception as e:
            handle_scraping_error(e, f"TIER {tier_num} {site} scraping failed after retries", logger)
        return None

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True)
    def _scrape_single_site_with_retry(self, site: str, search_term: str) -> pd.DataFrame | None:
        """Execute the actual scraping with a retry mechanism for network errors."""
        scrape_params = {
            "site_name": site,
            "search_term": search_term,
            "location": self.search_params["location"],
            "results_wanted": self.search_params["results_per_site"],
            "hours_old": self.search_params["hours_old"],
        }
        if site == SITE_INDEED:
            scrape_params["country_indeed"] = "Turkey"
        elif site == SITE_LINKEDIN:
            scrape_params["linkedin_fetch_description"] = True

        jobs_df = scrape_jobs(**scrape_params)
        return pd.DataFrame(jobs_df) if jobs_df is not None and not jobs_df.empty else None
