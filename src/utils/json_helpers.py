import json
import logging
import re
from typing import Any, cast

logger = logging.getLogger(__name__)


def extract_json_from_response(text: str) -> dict[str, Any] | None:
    """Extracts a JSON object from a string, prioritizing markdown code blocks.

    This function attempts to find a JSON object within a markdown code block first.
    If not found, it then searches for a JSON object by looking for the first and last
    curly braces. It handles JSON decoding errors gracefully.
    """
    # 1. Try to find JSON within a markdown code block first
    match = re.search(r"```(?:json)?\n(.*?)\n```", text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            return cast(dict[str, Any], json.loads(json_str))
        except json.JSONDecodeError:
            logger.warning(f"Markdown block's JSON could not be parsed. Block: {json_str[:200]}")

    # 2. If no markdown block, find the first and last curly brace
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if not json_match:
        logger.warning(f"No valid JSON block found in text. Text: {text[:200]}")
        return None

    json_str = json_match.group(0)
    try:
        return cast(dict[str, Any], json.loads(json_str))
    except json.JSONDecodeError:
        logger.error(f"JSON could not be parsed even after cleanup. Text: {text[:200]}", exc_info=True)
        return None
