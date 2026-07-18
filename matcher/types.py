"""Re-export contract shapes used by the matcher."""

from __future__ import annotations

from contracts.schemas import (
    MATCH_RESULT_KEYS,
    ExtractedContent,
    FileRecord,
    MatchCandidate,
    MatchResult,
    QueryIntent,
)

__all__ = [
    "MATCH_RESULT_KEYS",
    "ExtractedContent",
    "FileRecord",
    "MatchCandidate",
    "MatchResult",
    "QueryIntent",
]
