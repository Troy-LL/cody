"""Contract shape checks — required keys on fixture-shaped examples."""

from __future__ import annotations

from contracts.schemas import (
    FILE_RECORD_KEYS,
    EXTRACTED_CONTENT_KEYS,
    QUERY_INTENT_KEYS,
    MATCH_RESULT_KEYS,
    REVEAL_REQUEST_KEYS,
    SPEECH_REQUEST_KEYS,
    REVEAL_ANIMATION_KEYS,
)


def test_file_record_required_keys() -> None:
    sample = {
        "path": "C:/Users/troy/Desktop/receipt_lazada.pdf",
        "filename": "receipt_lazada.pdf",
        "extension": ".pdf",
        "size_bytes": 84213,
        "created_at": "2026-07-10T14:22:00Z",
        "modified_at": "2026-07-10T14:22:00Z",
        "extra_future_field": "ok",
    }
    assert FILE_RECORD_KEYS <= sample.keys()


def test_extracted_content_required_keys() -> None:
    sample = {
        "path": "C:/Users/troy/Desktop/receipt_lazada.pdf",
        "extractable": True,
        "text_snippet": "Lazada Order Confirmation...",
        "extraction_method": "pdf_text_layer",
    }
    assert EXTRACTED_CONTENT_KEYS <= sample.keys()


def test_query_intent_required_keys() -> None:
    sample = {
        "raw_query": "yung resibo ko sa Lazada last week",
        "description": "a receipt from Lazada",
        "time_hint": {
            "type": "relative",
            "value": "last_week",
            "resolved_range": ["2026-07-06T00:00:00Z", "2026-07-12T23:59:59Z"],
        },
        "type_hint": None,
        "language_mix": "taglish",
    }
    assert QUERY_INTENT_KEYS <= sample.keys()


def test_match_result_required_keys() -> None:
    sample = {
        "best_match": {
            "path": "C:/Users/troy/Desktop/receipt_lazada.pdf",
            "confidence": 0.91,
            "reasoning": "Filename and content reference Lazada.",
        },
        "alternatives": [],
    }
    assert MATCH_RESULT_KEYS <= sample.keys()
    assert {"path", "confidence", "reasoning"} <= sample["best_match"].keys()


def test_reveal_speech_animation_required_keys() -> None:
    reveal = {"path": "C:/Users/troy/Desktop/receipt_lazada.pdf"}
    speech = {"filename": "receipt_lazada.pdf", "language_mode": "tl"}
    animation = {
        "path": "C:/Users/troy/Desktop/receipt_lazada.pdf",
        "root": "C:/Users/troy/Desktop",
        "segments": ["Desktop", "receipt_lazada.pdf"],
    }
    assert REVEAL_REQUEST_KEYS <= reveal.keys()
    assert SPEECH_REQUEST_KEYS <= speech.keys()
    assert REVEAL_ANIMATION_KEYS <= animation.keys()


def test_unknown_fields_tolerated_on_typed_dicts() -> None:
    """Runtime consumers must not reject unknown keys (spec 6.9)."""
    from contracts.schemas import FileRecord

    record: FileRecord = {
        "path": "C:/x.pdf",
        "filename": "x.pdf",
        "extension": ".pdf",
        "size_bytes": 1,
        "created_at": "2026-07-10T14:22:00Z",
        "modified_at": "2026-07-10T14:22:00Z",
    }
    loose = {**record, "owner_note": "additive"}
    assert FILE_RECORD_KEYS <= loose.keys()
    assert loose["owner_note"] == "additive"
