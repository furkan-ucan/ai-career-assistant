import argparse
from pathlib import Path
from typing import List

import yaml


def load_persona_choices(config_path: Path = Path("config.yaml")) -> List[str]:
    """Return available persona names from the configuration."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return list(cfg.get("persona_search_configs", {}).keys())
    except Exception:
        return []


def build_parser(personas: List[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Akilli Kariyer Asistani komut satiri arayuzu"
    )
    parser.add_argument(
        "-p",
        "--persona",
        action="append",
        choices=personas,
        help="Sadece belirtilen persona(lar) icin arama yapar. Opsiyonel olarak birden fazla kullanilabilir.",
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
        help="Benzerlik esigi (%)",
    )
    return parser


def parse_args() -> argparse.Namespace:
    personas = load_persona_choices()
    parser = build_parser(personas)
    return parser.parse_args()
