"""Fixture-backed stubs for all six pipeline entry points (orchestration path only)."""

from __future__ import annotations

from pathlib import PureWindowsPath

from contracts.schemas import (
    ExtractedContent,
    FileRecord,
    MatchResult,
    QueryIntent,
    RevealAnimation,
)
from fixtures.load import (
    load_extracted_content,
    load_file_records,
    load_query_intents,
)


class DemoStubs:
    """Return checked-in fixture shapes so orchestration can wire without live deps."""

    def __init__(self) -> None:
        self._records = load_file_records()
        self._content = load_extracted_content()
        self._intents = load_query_intents()
        self._content_by_path = {item["path"]: item for item in self._content}

    def index_folder(self, path: str) -> list[FileRecord]:
        del path  # demo stubs ignore live folder
        return list(self._records)  # type: ignore[return-value]

    def extract(self, path: str) -> ExtractedContent:
        if path in self._content_by_path:
            return self._content_by_path[path]  # type: ignore[return-value]
        return {
            "path": path,
            "extractable": False,
            "text_snippet": None,
            "extraction_method": "unsupported",
        }

    def parse_query(self, text: str) -> QueryIntent:
        lowered = text.strip().lower()
        for intent in self._intents:
            if intent["raw_query"].strip().lower() == lowered:
                return intent  # type: ignore[return-value]
        # Prefer canonical Taglish Lazada fixture when query is close / default demo
        for intent in self._intents:
            if intent.get("language_mix") == "taglish" and "lazada" in intent["raw_query"].lower():
                return {**intent, "raw_query": text}  # type: ignore[return-value]
        return self._intents[0]  # type: ignore[return-value]

    def match(
        self,
        files: list[FileRecord],
        content: list[ExtractedContent],
        intent: QueryIntent,
    ) -> MatchResult:
        del files, content
        target = "C:/Users/troy/Desktop/receipt_lazada.pdf"
        if "shopee" in intent.get("description", "").lower() or "shopee" in intent.get(
            "raw_query", ""
        ).lower():
            target = "C:/Users/troy/Desktop/invoice_shopee.pdf"
        return {
            "best_match": {
                "path": target,
                "confidence": 0.91,
                "reasoning": (
                    "Fixture stub match — filename/content align with query; "
                    "replace with live matcher."
                ),
            },
            "alternatives": [
                {
                    "path": "C:/Users/troy/Desktop/lazada_screenshot.png",
                    "confidence": 0.34,
                }
            ],
        }

    def reveal(self, path: str) -> bool:
        del path
        return True

    def speak(self, filename: str, language_mode: str) -> bool:
        del filename, language_mode
        return True

    def build_reveal_animation(self, path: str, root: str) -> RevealAnimation:
        file_path = PureWindowsPath(path)
        root_path = PureWindowsPath(root)
        try:
            relative = file_path.relative_to(root_path)
            segments = [root_path.name, *relative.parts]
        except ValueError:
            segments = list(file_path.parts[-2:]) if len(file_path.parts) >= 2 else [file_path.name]
        return {
            "path": path,
            "root": root,
            "segments": segments,
        }
