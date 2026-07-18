"""Tests for matcher.match — spec.md §6.4, phase-1-stub.md."""

from __future__ import annotations

import json

import pytest

from fixtures.load import load_extracted_content, load_file_records, load_query_intents
from matcher.match import match
from matcher.types import MATCH_RESULT_KEYS


def test_match_returns_fixture_shaped_result() -> None:
    files = load_file_records()
    content = load_extracted_content()
    intents = load_query_intents()

    result = match(files, content, intents[0])

    assert MATCH_RESULT_KEYS <= result.keys()
    best = result["best_match"]
    assert best["path"] in {f["path"] for f in files}
    assert isinstance(best["confidence"], float)
    assert best["reasoning"]
    assert isinstance(result["alternatives"], list)


def test_match_best_path_is_first_file_deterministic() -> None:
    files = load_file_records()
    content = load_extracted_content()
    intents = load_query_intents()

    result = match(files, content, intents[0])

    assert result["best_match"]["path"] == files[0]["path"]


def test_match_result_is_json_serializable() -> None:
    files = load_file_records()
    content = load_extracted_content()
    intents = load_query_intents()

    result = match(files, content, intents[0])

    json.dumps(result)


def test_match_raises_on_empty_files() -> None:
    content = load_extracted_content()
    intents = load_query_intents()

    with pytest.raises(ValueError):
        match([], content, intents[0])
