"""TypedDict shapes for Cody contracts (spec.md sections 6.1-6.7).

Consumers must tolerate unknown fields at runtime (spec section 6.9): TypedDict is a
static shape, not a validator — never reject extra keys when reading dicts.
"""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict


class TimeHint(TypedDict, total=False):
    type: str
    value: str
    resolved_range: list[str]


class FileRecord(TypedDict):
    path: str
    filename: str
    extension: str
    size_bytes: int
    created_at: str
    modified_at: str


class ExtractedContent(TypedDict):
    path: str
    extractable: bool
    text_snippet: str | None
    extraction_method: str


class QueryIntent(TypedDict):
    raw_query: str
    description: str
    time_hint: TimeHint | None
    type_hint: str | None
    language_mix: str


class MatchCandidate(TypedDict):
    path: str
    confidence: float
    reasoning: NotRequired[str]


class MatchResult(TypedDict):
    best_match: MatchCandidate
    alternatives: list[MatchCandidate]


class RevealRequest(TypedDict):
    path: str


class SpeechRequest(TypedDict):
    filename: str
    language_mode: str


class RevealAnimation(TypedDict):
    path: str
    root: str
    segments: list[str]


FILE_RECORD_KEYS: frozenset[str] = frozenset(
    {"path", "filename", "extension", "size_bytes", "created_at", "modified_at"}
)
EXTRACTED_CONTENT_KEYS: frozenset[str] = frozenset(
    {"path", "extractable", "text_snippet", "extraction_method"}
)
QUERY_INTENT_KEYS: frozenset[str] = frozenset(
    {"raw_query", "description", "time_hint", "type_hint", "language_mix"}
)
MATCH_RESULT_KEYS: frozenset[str] = frozenset({"best_match", "alternatives"})
REVEAL_REQUEST_KEYS: frozenset[str] = frozenset({"path"})
SPEECH_REQUEST_KEYS: frozenset[str] = frozenset({"filename", "language_mode"})
REVEAL_ANIMATION_KEYS: frozenset[str] = frozenset({"path", "root", "segments"})

LanguageMix = Literal["en", "tl", "taglish"]
LanguageMode = Literal["en", "tl", "auto"]
