from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .exceptions import ConfigError

CONFIG_PATH = Path("config.yaml")


def load_settings() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {CONFIG_PATH}") from exc
    except yaml.YAMLError as exc:  # type: ignore[no-any-expr]
        raise ConfigError(f"Failed to parse config file: {exc}") from exc
