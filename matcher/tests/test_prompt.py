"""Prompt assembly tests."""

from __future__ import annotations

from fixtures.load import load_extracted_content, load_file_records, load_query_intents
from matcher.prompt import build_prompt


def test_lazada_prompt_contains_evidence() -> None:
    files = load_file_records()
    content = load_extracted_content()
    intent = load_query_intents()[0]
    prompt = build_prompt(files, content, intent)
    assert "receipt_lazada.pdf" in prompt
    assert "Lazada Order Confirmation" in prompt
    assert "2026-07-06T00:00:00Z" in prompt
    assert "time_hint=in_range" in prompt
    assert len(prompt) < 100_000
