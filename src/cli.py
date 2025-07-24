# src/cli.py
"""Command line interface for Akilli Kariyer Asistani, hardened with input validation."""

import argparse
from pathlib import Path

import yaml


def _positive_int_in_range(min_val: int, max_val: int):
    """Factory for creating a range-checking type for argparse."""

    def checker(value: str) -> int:
        """Check if the value is a positive integer within a specified range."""
        try:
            ivalue = int(value)
            if not (min_val <= ivalue <= max_val):
                raise argparse.ArgumentTypeError(
                    f"Value {ivalue} is out of range. Must be between {min_val} and {max_val}."
                )
            return ivalue
        except ValueError:
            raise argparse.ArgumentTypeError(f"'{value}' is not a valid integer.")

    return checker


def load_persona_choices(config_path: Path = Path("config.yaml")) -> list[str]:
    """Return available persona names from the configuration."""
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return list(cfg.get("persona_search_configs", {}).keys())
    except Exception:
        return []


def build_parser(personas: list[str]) -> argparse.ArgumentParser:
    """Build the argument parser with all arguments and their validations."""
    parser = argparse.ArgumentParser(description="Akilli Kariyer Asistani Komut Satırı Arayüzü")

    parser.add_argument(
        "-p",
        "--persona",
        action="append",
        choices=personas,
        help="Sadece belirtilen persona(lar) için arama yapar. Birden fazla kullanılabilir.",
    )
    parser.add_argument(
        "-r",
        "--results",
        type=_positive_int_in_range(1, 500),
        help="Her site için çekilecek maksimum ilan sayısı (1-500).",
    )
    parser.add_argument(
        "-t", "--threshold", type=_positive_int_in_range(0, 100), help="Benzerlik eşiği (yüzde olarak, 0-100)."
    )
    parser.add_argument(
        "--no-rerank", action="store_true", help="AI derin analiz (reranking) aşamasını devre dışı bırakır."
    )
    return parser


def parse_args() -> argparse.Namespace:
    """Parse and return command line arguments."""
    personas = load_persona_choices()
    parser = build_parser(personas)
    return parser.parse_args()
