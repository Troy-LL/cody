"""Parse and config boundary tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from matcher.config import ConfigError, load_config
from matcher.match import match
from matcher.parse import MatchParseError, parse_result


def test_parse_result_accepts_valid_path() -> None:
    raw = json.dumps(
        {
            "best_match": {
                "path": "/a.pdf",
                "confidence": 0.9,
                "reasoning": "Snippet names Lazada.",
            },
            "alternatives": [],
        }
    )
    result = parse_result(raw, {"/a.pdf", "/b.pdf"})
    assert result["best_match"]["path"] == "/a.pdf"


def test_parse_result_rejects_fabricated_path() -> None:
    raw = json.dumps(
        {
            "best_match": {
                "path": "/evil.pdf",
                "confidence": 0.9,
                "reasoning": "Nope.",
            },
            "alternatives": [],
        }
    )
    with pytest.raises(MatchParseError):
        parse_result(raw, {"/a.pdf"})


def test_load_config_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path / "missing.json")


def test_match_with_injected_model() -> None:
    files = [
        {
            "path": "/receipt.pdf",
            "filename": "receipt.pdf",
            "extension": ".pdf",
            "size_bytes": 1,
            "created_at": "2026-07-10T00:00:00Z",
            "modified_at": "2026-07-10T00:00:00Z",
        }
    ]
    content = [
        {
            "path": "/receipt.pdf",
            "extractable": True,
            "text_snippet": "Lazada",
            "extraction_method": "plain_text",
        }
    ]
    intent = {
        "raw_query": "lazada",
        "description": "lazada receipt",
        "time_hint": None,
        "type_hint": None,
        "language_mix": "en",
    }

    def fake_call(_config: object, _prompt: str) -> str:
        return json.dumps(
            {
                "best_match": {
                    "path": "/receipt.pdf",
                    "confidence": 0.88,
                    "reasoning": "Snippet mentions Lazada.",
                },
                "alternatives": [],
            }
        )

    result = match(files, content, intent, call_model=fake_call, use_stub=False)
    assert result["best_match"]["path"] == "/receipt.pdf"
    assert "Lazada" in result["best_match"]["reasoning"]
