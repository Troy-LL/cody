"""Matcher entry point. See matcher/README.md and spec.md §6.4."""

from __future__ import annotations

from typing import Any


def match(
    files: list[dict[str, Any]],
    content: list[dict[str, Any]],
    intent: dict[str, Any],
) -> dict[str, Any]:
    """Rank *files*/*content* against *intent* and return MatchResult."""
    _ = (content, intent)
    if not files:
        raise ValueError("files must be non-empty")
    path = files[0]["path"]
    return {
        "best_match": {
            "path": path,
            "confidence": 0.5,
            "reasoning": "Stub match: returning the first indexed file path.",
        },
        "alternatives": [],
    }
