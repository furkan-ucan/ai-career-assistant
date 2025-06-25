class ConfigError(Exception):
    """Raised when configuration loading fails."""


class APIError(Exception):
    """Raised when external API calls fail."""


class CVNotFoundError(Exception):
    """Raised when CV file is missing."""
