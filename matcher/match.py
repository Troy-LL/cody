"""Matcher entry point. See matcher/README.md and spec.md §6.4."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from matcher.api import call_responses
from matcher.config import CONFIG_PATH, load_config
from matcher.parse import parse_result
from matcher.prompt import build_prompt


def _stub_result(files: list[dict[str, Any]]) -> dict[str, Any]:
    path = files[0]["path"]
    return {
        "best_match": {
            "path": path,
            "confidence": 0.5,
            "reasoning": "Stub match: returning the first indexed file path.",
        },
        "alternatives": [],
    }


def _resolve_stub(use_stub: bool | None, call_model: Callable[..., str] | None) -> bool:
    if call_model is not None:
        return False
    if use_stub is not None:
        return use_stub
    env = os.environ.get("MATCHER_STUB")
    if env == "1":
        return True
    if env == "0":
        return False
    return not CONFIG_PATH.is_file()


def match(
    files: list[dict[str, Any]],
    content: list[dict[str, Any]],
    intent: dict[str, Any],
    *,
    call_model: Callable[[Any, str], str] | None = None,
    use_stub: bool | None = None,
) -> dict[str, Any]:
    """Rank *files*/*content* against *intent* and return MatchResult.

    Raises ConfigError / ModelCallError / MatchParseError for orchestration to catch.
    Stub when MATCHER_STUB=1, or when no local_model.json exists and stub is unset.
    Force live with MATCHER_STUB=0 after pasting matcher/local_model.json.
    """
    if not files:
        raise ValueError("files must be non-empty")
    if _resolve_stub(use_stub, call_model):
        return _stub_result(files)

    prompt = build_prompt(files, content, intent)
    if call_model is not None:
        raw = call_model(None, prompt)
    else:
        config = load_config()
        raw = call_responses(config, prompt)
    valid_paths = {f["path"] for f in files if "path" in f}
    return parse_result(raw, valid_paths)
