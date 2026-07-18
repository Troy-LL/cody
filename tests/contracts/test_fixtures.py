"""Fixture load + content presence checks."""

from __future__ import annotations

from fixtures.load import (
    load_extracted_content,
    load_file_records,
    load_query_intents,
)


def test_fixtures_load_nonempty() -> None:
    records = load_file_records()
    content = load_extracted_content()
    intents = load_query_intents()
    assert 5 <= len(records) <= 10
    assert 5 <= len(content) <= 10
    assert 5 <= len(intents) <= 10


def test_taglish_relative_time_query_present() -> None:
    intents = load_query_intents()
    lazada = [
        i
        for i in intents
        if "lazada" in i.get("raw_query", "").lower()
        and i.get("language_mix") == "taglish"
    ]
    assert lazada, "expected Taglish Lazada relative-time query fixture"
    assert lazada[0]["time_hint"]["type"] == "relative"
    assert "last week" in lazada[0]["raw_query"].lower()


def test_unsupported_file_extractable_false() -> None:
    content = load_extracted_content()
    unsupported = [c for c in content if c.get("extractable") is False]
    assert unsupported, "expected at least one extractable: false fixture"
    for item in unsupported:
        assert item.get("text_snippet") is None
