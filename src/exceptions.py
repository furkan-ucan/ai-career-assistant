# src/exceptions.py
"""Custom exceptions for Akilli Kariyer Asistani."""


class AkilliKariyerError(Exception):
    """Base exception class for all Akilli Kariyer Asistani errors."""


class ConfigError(AkilliKariyerError):
    """Raised when configuration loading fails."""


class APIError(AkilliKariyerError):
    """Raised when external API calls fail."""


class CVNotFoundError(AkilliKariyerError):
    """Raised when CV file is missing."""


__all__ = ["AkilliKariyerError", "ConfigError", "APIError", "CVNotFoundError"]
