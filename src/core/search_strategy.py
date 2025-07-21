# src/core/search_strategy.py
"""
Search Strategy Factory implementing Dr. Finch's platform-specific doctrines.
Follows Strategy Pattern for flexible and extensible search implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .constants import NEGATIVE_FILTERS, PLATFORM_CONFIGS, SITE_INDEED, SITE_LINKEDIN


@dataclass
class SearchQuery:
    """Immutable search query representation."""

    platform: str
    tier: str
    query: str
    metadata: dict[str, str]


class SearchStrategy(ABC):
    """Abstract base class for platform-specific search strategies."""

    @abstractmethod
    def build_tier1_query(self, persona_data: dict) -> str | None:
        """Build high-precision tier 1 query."""
        pass

    @abstractmethod
    def build_tier2_query(self, persona_data: dict) -> str | None:
        """Build alias/localized tier 2 query."""
        pass

    @abstractmethod
    def build_tier3_query(self, persona_data: dict) -> str | None:
        """Build broad keyword tier 3 query."""
        pass


class LinkedInStrategy(SearchStrategy):
    """LinkedIn-specific search strategy following Dr. Finch's LinkedIn Doctrine."""

    def __init__(self):
        self.max_or_operators = PLATFORM_CONFIGS[SITE_LINKEDIN]["max_or_operators"]
        self.negative_filters = " ".join(NEGATIVE_FILTERS)

    def build_tier1_query(self, persona_data: dict) -> str | None:
        """LinkedIn Tier 1: Simple, quoted precision search."""
        high_precision = persona_data.get("high_precision_term")
        if not high_precision:
            # Fallback to primary title
            primary_en = persona_data.get("primary_title_en")
            primary_tr = persona_data.get("primary_title_tr")
            if primary_en:
                high_precision = f'"{primary_en}"'
            elif primary_tr:
                high_precision = f'"{primary_tr}"'

        if high_precision:
            return f"{high_precision} {self.negative_filters}"
        return None

    def build_tier2_query(self, persona_data: dict) -> str | None:
        """LinkedIn Tier 2: Limited OR for aliases (max 2 per doctrine)."""
        alias_terms = persona_data.get("alias_terms", [])

        if alias_terms:
            # LinkedIn Doctrine: Limit OR usage to prevent dilution
            limited_terms = alias_terms[: self.max_or_operators]
            if limited_terms:
                or_clause = " OR ".join(limited_terms)
                return f"({or_clause}) {self.negative_filters}"

        return None

    def build_tier3_query(self, persona_data: dict) -> str | None:
        """LinkedIn Tier 3: Broad keyword search with AND logic."""
        broad_keywords = persona_data.get("broad_keywords", [])

        if broad_keywords:
            # Quote multi-word terms, use AND for relevance
            processed_keywords = []
            for kw in broad_keywords[:4]:  # Limit to 4 for readability
                if " " in kw:
                    processed_keywords.append(f'"{kw}"')
                else:
                    processed_keywords.append(kw)

            keyword_query = " AND ".join(processed_keywords)
            return f"({keyword_query}) {self.negative_filters}"

        return None


class IndeedStrategy(SearchStrategy):
    """Indeed-specific search strategy following Dr. Finch's Indeed Doctrine."""

    def __init__(self):
        self.max_or_operators = PLATFORM_CONFIGS[SITE_INDEED]["max_or_operators"]
        self.negative_filters = " ".join(NEGATIVE_FILTERS)

    def build_tier1_query(self, persona_data: dict) -> str | None:
        """Indeed Tier 1: title:() operator for precision (mandatory per doctrine)."""
        high_precision = persona_data.get("high_precision_term")
        if not high_precision:
            # Fallback to primary title
            primary_en = persona_data.get("primary_title_en")
            primary_tr = persona_data.get("primary_title_tr")
            if primary_en:
                high_precision = primary_en
            elif primary_tr:
                high_precision = primary_tr

        if high_precision:
            # Remove quotes for title: operator
            clean_term = high_precision.strip('"')
            return f'title:("{clean_term}") {self.negative_filters}'

        return None

    def build_tier2_query(self, persona_data: dict) -> str | None:
        """Indeed Tier 2: title:() with grouped OR (Indeed handles this well)."""
        alias_terms = persona_data.get("alias_terms", [])

        if alias_terms:
            # Clean quotes and build OR clause for title: operator
            clean_aliases = [term.strip('"') for term in alias_terms]
            if clean_aliases:
                or_clause = " OR ".join([f'"{term}"' for term in clean_aliases])
                return f"title:({or_clause}) {self.negative_filters}"

        return None

    def build_tier3_query(self, persona_data: dict) -> str | None:
        """Indeed Tier 3: General content search (same as LinkedIn)."""
        broad_keywords = persona_data.get("broad_keywords", [])

        if broad_keywords:
            processed_keywords = []
            for kw in broad_keywords[:4]:
                if " " in kw:
                    processed_keywords.append(f'"{kw}"')
                else:
                    processed_keywords.append(kw)

            keyword_query = " AND ".join(processed_keywords)
            return f"({keyword_query}) {self.negative_filters}"

        return None


class SearchStrategyFactory:
    """Factory for creating platform-specific search strategies."""

    _strategies = {
        SITE_LINKEDIN: LinkedInStrategy,
        SITE_INDEED: IndeedStrategy,
    }

    @classmethod
    def get_strategy(cls, platform: str) -> SearchStrategy:
        """Get strategy instance for platform."""
        strategy_class = cls._strategies.get(platform)
        if not strategy_class:
            raise ValueError(f"Unsupported platform: {platform}")
        return strategy_class()

    @classmethod
    def build_all_queries(cls, persona_data: dict) -> dict[str, str]:
        """Build all platform-tier query combinations."""
        queries = {}

        for platform in [SITE_LINKEDIN, SITE_INDEED]:
            strategy = cls.get_strategy(platform)

            # Build all tiers for this platform
            tier1 = strategy.build_tier1_query(persona_data)
            if tier1:
                queries[f"{platform}_tier1_query"] = tier1

            tier2 = strategy.build_tier2_query(persona_data)
            if tier2:
                queries[f"{platform}_tier2_query"] = tier2

            tier3 = strategy.build_tier3_query(persona_data)
            if tier3:
                queries[f"{platform}_tier3_query"] = tier3

        return queries
