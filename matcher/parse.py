"""Parse and validate MatchResult JSON from the model."""

from __future__ import annotations

import json
from typing import Any


class MatchParseError(ValueError):
    """Model output could not be turned into a valid MatchResult."""


def parse_result(raw: str, valid_paths: set[str]) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MatchParseError(f"unparseable MatchResult JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise MatchParseError("MatchResult must be a JSON object")
    best = data.get("best_match")
    if not isinstance(best, dict):
        raise MatchParseError("best_match must be an object")
    path = best.get("path")
    if path not in valid_paths:
        raise MatchParseError(
            f"best_match.path {path!r} is not in the input file set"
        )
    confidence = best.get("confidence")
    reasoning = best.get("reasoning")
    if not isinstance(confidence, (int, float)):
        raise MatchParseError("best_match.confidence must be a number")
    if not isinstance(reasoning, str) or not reasoning.strip():
        raise MatchParseError("best_match.reasoning must be a non-empty string")
    alternatives = data.get("alternatives", [])
    if not isinstance(alternatives, list):
        raise MatchParseError("alternatives must be a list")
    clean_alts: list[dict[str, Any]] = []
    for alt in alternatives:
        if not isinstance(alt, dict):
            continue
        alt_path = alt.get("path")
        if alt_path not in valid_paths:
            continue
        alt_conf = alt.get("confidence", 0.0)
        if not isinstance(alt_conf, (int, float)):
            continue
        clean_alts.append({"path": alt_path, "confidence": float(alt_conf)})
    return {
        "best_match": {
            "path": path,
            "confidence": float(confidence),
            "reasoning": reasoning.strip(),
        },
        "alternatives": clean_alts,
    }
