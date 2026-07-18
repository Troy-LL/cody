"""Tests for dependency-correct concurrent pipeline."""

from __future__ import annotations

import threading
from typing import Any

import pytest

from orchestration.pipeline import run_pipeline
from orchestration.reveal_animation import PathOutsideRootError, build_reveal_animation


def test_build_reveal_animation_segments() -> None:
    anim = build_reveal_animation(
        r"C:\Users\troy\Desktop\receipt_lazada.pdf",
        r"C:\Users\troy\Desktop",
    )
    assert anim["segments"] == ["Desktop", "receipt_lazada.pdf"]
    assert anim["root"] == r"C:\Users\troy\Desktop"


def test_build_reveal_animation_rejects_outside_root() -> None:
    with pytest.raises(PathOutsideRootError):
        build_reveal_animation(
            r"C:\Other\file.pdf",
            r"C:\Users\troy\Desktop",
        )


def test_extract_waits_for_index_completion() -> None:
    index_done = threading.Event()
    extract_started = threading.Event()
    extract_before_index = threading.Event()

    def index_folder(path: str) -> list[dict[str, Any]]:
        del path
        threading.Event().wait(0.05)  # hold lock briefly so NLU overlaps
        index_done.set()
        return [
            {
                "path": r"C:\Users\troy\Desktop\a.pdf",
                "filename": "a.pdf",
                "extension": ".pdf",
                "size_bytes": 1,
                "created_at": "2026-07-01T00:00:00Z",
                "modified_at": "2026-07-01T00:00:00Z",
            }
        ]

    def extract(path: str) -> dict[str, Any]:
        if not index_done.is_set():
            extract_before_index.set()
        extract_started.set()
        return {
            "path": path,
            "extractable": True,
            "text_snippet": "x",
            "extraction_method": "txt",
        }

    def parse_query(text: str) -> dict[str, Any]:
        del text
        return {
            "raw_query": "q",
            "description": "q",
            "time_hint": None,
            "type_hint": None,
            "language_mix": "en",
        }

    def match(files, content, intent):
        del files, content, intent
        return {
            "best_match": {
                "path": r"C:\Users\troy\Desktop\a.pdf",
                "confidence": 0.9,
                "reasoning": "ok",
            },
            "alternatives": [],
        }

    run_pipeline(
        root=r"C:\Users\troy\Desktop",
        query="q",
        index_folder=index_folder,
        extract=extract,
        parse_query=parse_query,
        match=match,
    )
    assert extract_started.is_set()
    assert not extract_before_index.is_set()


def test_indexer_and_nlu_overlap() -> None:
    index_entered = threading.Event()
    nlu_entered = threading.Event()
    both_in_flight = threading.Event()
    release = threading.Event()

    def index_folder(path: str) -> list[dict[str, Any]]:
        del path
        index_entered.set()
        if nlu_entered.wait(timeout=1.0):
            both_in_flight.set()
        release.wait(timeout=1.0)
        return []

    def parse_query(text: str) -> dict[str, Any]:
        del text
        nlu_entered.set()
        if index_entered.wait(timeout=1.0):
            both_in_flight.set()
        release.wait(timeout=1.0)
        return {
            "raw_query": "q",
            "description": "q",
            "time_hint": None,
            "type_hint": None,
            "language_mix": "en",
        }

    def extract(path: str) -> dict[str, Any]:
        raise AssertionError(f"extract should not run for empty index: {path}")

    match_called = threading.Event()

    def match(files, content, intent):
        assert files == []
        assert content == []
        match_called.set()
        return {
            "best_match": {
                "path": r"C:\Users\troy\Desktop\placeholder.pdf",
                "confidence": 0.1,
                "reasoning": "empty",
            },
            "alternatives": [],
        }

    # Release blockers after both entered — run in thread so we can set release
    def runner() -> None:
        # Force path under root for animation; match returns Desktop path
        def match_ok(files, content, intent):
            del files, content, intent
            match_called.set()
            return {
                "best_match": {
                    "path": r"C:\Users\troy\Desktop\placeholder.pdf",
                    "confidence": 0.1,
                    "reasoning": "empty",
                },
                "alternatives": [],
            }

        run_pipeline(
            root=r"C:\Users\troy\Desktop",
            query="q",
            index_folder=index_folder,
            extract=extract,
            parse_query=parse_query,
            match=match_ok,
        )

    t = threading.Thread(target=runner)
    t.start()
    assert both_in_flight.wait(timeout=2.0)
    release.set()
    t.join(timeout=2.0)
    assert match_called.is_set()


def test_empty_folder_still_calls_match() -> None:
    calls: list[str] = []

    def index_folder(path: str) -> list:
        del path
        return []

    def extract(path: str):
        raise AssertionError(path)

    def parse_query(text: str) -> dict[str, Any]:
        return {
            "raw_query": text,
            "description": text,
            "time_hint": None,
            "type_hint": None,
            "language_mix": "en",
        }

    def match(files, content, intent):
        calls.append("match")
        assert files == []
        assert content == []
        return {
            "best_match": {
                "path": r"C:\Users\troy\Desktop\x.pdf",
                "confidence": 0.0,
                "reasoning": "none",
            },
            "alternatives": [],
        }

    run_pipeline(
        root=r"C:\Users\troy\Desktop",
        query="anything",
        index_folder=index_folder,
        extract=extract,
        parse_query=parse_query,
        match=match,
    )
    assert calls == ["match"]


def test_extractable_false_passed_through() -> None:
    seen: list[bool] = []

    def index_folder(path: str) -> list[dict[str, Any]]:
        del path
        return [
            {
                "path": r"C:\Users\troy\Desktop\shot.png",
                "filename": "shot.png",
                "extension": ".png",
                "size_bytes": 2,
                "created_at": "2026-07-01T00:00:00Z",
                "modified_at": "2026-07-01T00:00:00Z",
            }
        ]

    def extract(path: str) -> dict[str, Any]:
        return {
            "path": path,
            "extractable": False,
            "text_snippet": None,
            "extraction_method": "unsupported",
        }

    def parse_query(text: str) -> dict[str, Any]:
        return {
            "raw_query": text,
            "description": "picture",
            "time_hint": None,
            "type_hint": "image",
            "language_mix": "en",
        }

    def match(files, content, intent):
        del files, intent
        seen.append(content[0]["extractable"] is False)
        return {
            "best_match": {
                "path": content[0]["path"],
                "confidence": 0.5,
                "reasoning": "image",
            },
            "alternatives": [],
        }

    run_pipeline(
        root=r"C:\Users\troy\Desktop",
        query="picture",
        index_folder=index_folder,
        extract=extract,
        parse_query=parse_query,
        match=match,
    )
    assert seen == [True]


def test_unknown_fields_tolerated() -> None:
    def index_folder(path: str) -> list[dict[str, Any]]:
        del path
        return [
            {
                "path": r"C:\Users\troy\Desktop\a.pdf",
                "filename": "a.pdf",
                "extension": ".pdf",
                "size_bytes": 1,
                "created_at": "2026-07-01T00:00:00Z",
                "modified_at": "2026-07-01T00:00:00Z",
                "extra_indexer_field": True,
            }
        ]

    def extract(path: str) -> dict[str, Any]:
        return {
            "path": path,
            "extractable": True,
            "text_snippet": "hi",
            "extraction_method": "pdf",
            "debug_score": 99,
        }

    def parse_query(text: str) -> dict[str, Any]:
        return {
            "raw_query": text,
            "description": text,
            "time_hint": None,
            "type_hint": None,
            "language_mix": "taglish",
            "nlu_version": "x",
        }

    def match(files, content, intent):
        return {
            "best_match": {
                "path": files[0]["path"],
                "confidence": 0.8,
                "reasoning": "ok",
                "model_trace": "secret",
            },
            "alternatives": [],
            "latency_ms": 12,
        }

    result = run_pipeline(
        root=r"C:\Users\troy\Desktop",
        query="yung pdf",
        index_folder=index_folder,
        extract=extract,
        parse_query=parse_query,
        match=match,
    )
    assert result.language_mix == "taglish"
    assert result.path.endswith("a.pdf")
    assert result.reasoning == "ok"
