"""Assemble the matcher prompt from contract-shaped inputs."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_ts(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _in_range(modified_at: str | None, resolved_range: list[str] | None) -> str:
    if not resolved_range or len(resolved_range) < 2:
        return "time_hint=none"
    start = _parse_ts(resolved_range[0])
    end = _parse_ts(resolved_range[1])
    mod = _parse_ts(modified_at)
    if start is None or end is None or mod is None:
        return "time_hint=unknown"
    if start <= mod <= end:
        return "time_hint=in_range"
    return "time_hint=out_of_range"


def _type_match(extension: str | None, type_hint: str | None) -> str:
    if not type_hint:
        return "type_hint=none"
    ext = (extension or "").lstrip(".").lower()
    hint = type_hint.lstrip(".").lower()
    if ext == hint or extension == type_hint:
        return "type_hint=match"
    return "type_hint=mismatch"


def build_prompt(
    files: list[dict[str, Any]],
    content: list[dict[str, Any]],
    intent: dict[str, Any],
) -> str:
    by_path = {c.get("path"): c for c in content if isinstance(c, dict)}
    time_hint = intent.get("time_hint") or {}
    resolved = None
    if isinstance(time_hint, dict):
        resolved = time_hint.get("resolved_range")
    type_hint = intent.get("type_hint")

    lines: list[str] = [
        "You are Cody, a file matcher. Pick the single best file for the query.",
        "Return ONLY JSON matching this shape:",
        '{"best_match":{"path":"...","confidence":0.0,"reasoning":"one sentence"},'
        '"alternatives":[{"path":"...","confidence":0.0}]}',
        "best_match.path MUST be one of the candidate paths exactly.",
        "reasoning MUST be one legible sentence naming the snippet or metadata that matched.",
        "",
        "INTENT",
        f"description: {intent.get('description')}",
        f"resolved_range: {resolved}",
        f"type_hint: {type_hint}",
        f"language_mix: {intent.get('language_mix')}",
        "",
        "CANDIDATES",
    ]
    for f in files:
        path = f.get("path")
        ext = f.get("extension")
        modified = f.get("modified_at")
        row = by_path.get(path) or {}
        snippet = row.get("text_snippet") if row.get("extractable") else None
        if snippet is None:
            snippet = "(no text; metadata only)"
        lines.append(
            f"- path={path} | filename={f.get('filename')} | extension={ext} | "
            f"modified_at={modified} | {_in_range(modified, resolved)} | "
            f"{_type_match(ext if isinstance(ext, str) else None, type_hint if isinstance(type_hint, str) else None)} | "
            f"snippet={snippet}"
        )
    lines.append("")
    lines.append("Choose the best match now.")
    return "\n".join(lines)
