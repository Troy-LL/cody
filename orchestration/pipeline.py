"""Dependency-correct concurrent orchestration pipeline (injected callables)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Mapping

from contracts.interfaces import Extract, IndexFolder, Match, ParseQuery
from contracts.schemas import (
    ExtractedContent,
    FileRecord,
    MatchResult,
    QueryIntent,
    RevealAnimation,
)
from orchestration.reveal_animation import build_reveal_animation


@dataclass(frozen=True)
class PipelineResolution:
    """UI-ready result from a successful pipeline run."""

    path: str
    confidence: float
    reasoning: str
    language_mix: str
    animation: RevealAnimation
    match_result: MatchResult
    intent: QueryIntent


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    raise TypeError(f"expected mapping, got {type(value)!r}")


def run_pipeline(
    *,
    root: str,
    query: str,
    index_folder: IndexFolder,
    extract: Extract,
    parse_query: ParseQuery,
    match: Match,
    max_workers: int = 8,
) -> PipelineResolution:
    """Run Indexer+NLU concurrently, then extract, then match.

    Reads only known contract keys so unknown fields are ignored (spec 6.9).
    """
    with ThreadPoolExecutor(max_workers=2) as starter:
        index_future = starter.submit(index_folder, root)
        intent_future = starter.submit(parse_query, query)
        raw_files = index_future.result()
        raw_intent = intent_future.result()

    files: list[FileRecord] = []
    for item in raw_files:
        m = _as_mapping(item)
        files.append(
            {
                "path": str(m["path"]),
                "filename": str(m["filename"]),
                "extension": str(m["extension"]),
                "size_bytes": int(m["size_bytes"]),
                "created_at": str(m["created_at"]),
                "modified_at": str(m["modified_at"]),
            }
        )

    intent_map = _as_mapping(raw_intent)
    intent: QueryIntent = {
        "raw_query": str(intent_map["raw_query"]),
        "description": str(intent_map["description"]),
        "time_hint": intent_map.get("time_hint"),  # type: ignore[typeddict-item]
        "type_hint": intent_map.get("type_hint"),  # type: ignore[typeddict-item]
        "language_mix": str(intent_map["language_mix"]),
    }

    content_by_path: dict[str, ExtractedContent] = {}
    if files:
        workers = max(1, min(max_workers, len(files)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(extract, rec["path"]): rec["path"] for rec in files
            }
            for future in as_completed(futures):
                path = futures[future]
                raw = _as_mapping(future.result())
                content_by_path[path] = {
                    "path": str(raw.get("path", path)),
                    "extractable": bool(raw["extractable"]),
                    "text_snippet": raw.get("text_snippet"),  # type: ignore[typeddict-item]
                    "extraction_method": str(raw["extraction_method"]),
                }

    # Preserve indexer order for path alignment
    content: list[ExtractedContent] = [
        content_by_path[rec["path"]] for rec in files
    ]

    raw_match = _as_mapping(match(files, content, intent))
    best = _as_mapping(raw_match["best_match"])
    alternatives_raw = raw_match.get("alternatives", [])
    alternatives = []
    for alt in alternatives_raw:
        am = _as_mapping(alt)
        alternatives.append(
            {"path": str(am["path"]), "confidence": float(am["confidence"])}
        )

    match_result: MatchResult = {
        "best_match": {
            "path": str(best["path"]),
            "confidence": float(best["confidence"]),
            "reasoning": str(best.get("reasoning", "")),
        },
        "alternatives": alternatives,
    }

    path = match_result["best_match"]["path"]
    animation = build_reveal_animation(path, root)

    return PipelineResolution(
        path=path,
        confidence=float(match_result["best_match"]["confidence"]),
        reasoning=str(match_result["best_match"].get("reasoning", "")),
        language_mix=str(intent["language_mix"]),
        animation=animation,
        match_result=match_result,
        intent=intent,
    )
