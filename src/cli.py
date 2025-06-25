"""Command line interface for Akilli Kariyer Asistani.
This module provides a command line interface for the Akilli Kariyer
Asistani application, allowing users to specify personas, result limits,
and similarity thresholds."""

# Standard Library
import argparse
from pathlib import Path

# Third Party
import yaml


def load_persona_choices(config_path: Path = Path("config.yaml")) -> list[str]:
    """Return available persona names from the configuration."""
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return list(cfg.get("persona_search_configs", {}).keys())
    except Exception:
        return []


def build_parser(personas: list[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Akilli Kariyer Asistani komut satiri arayuzu")
    parser.add_argument(
        "-p",
        "--persona",
        action="append",
        choices=personas,
        help=("Sadece belirtilen persona(lar) icin arama yapar. Opsiyonel olarak birden fazla kullanilabilir."),
    )
    parser.add_argument(
        "-r",
        "--results",
        type=int,
        help="Her site icin cekilecek maksimum ilan sayisi",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=int,
        help="Benzerlik esigi (yuzde)",
    )
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help="AI derin analiz asamasini devre disi birakir",
    )
    return parser


def parse_args() -> argparse.Namespace:
    personas = load_persona_choices()
    parser = build_parser(personas)
    return parser.parse_args()
