"""Protocol / callable types for the six primary entry points."""

from __future__ import annotations

from typing import Protocol

from contracts.schemas import (
    ExtractedContent,
    FileRecord,
    MatchResult,
    QueryIntent,
    RevealAnimation,
)


class IndexFolder(Protocol):
    def __call__(self, path: str) -> list[FileRecord]: ...


class Extract(Protocol):
    def __call__(self, path: str) -> ExtractedContent: ...


class ParseQuery(Protocol):
    def __call__(self, text: str) -> QueryIntent: ...


class Match(Protocol):
    def __call__(
        self,
        files: list[FileRecord],
        content: list[ExtractedContent],
        intent: QueryIntent,
    ) -> MatchResult: ...


class Reveal(Protocol):
    def __call__(self, path: str) -> bool: ...


class Speak(Protocol):
    def __call__(self, filename: str, language_mode: str) -> bool: ...


class BuildRevealAnimation(Protocol):
    def __call__(self, path: str, root: str) -> RevealAnimation: ...
