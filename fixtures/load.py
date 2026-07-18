"""Load checked-in JSON fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent


def _load_json(name: str) -> Any:
    path = FIXTURES_DIR / name
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_file_records() -> list[dict[str, Any]]:
    data = _load_json("file_records.json")
    assert isinstance(data, list)
    return data


def load_extracted_content() -> list[dict[str, Any]]:
    data = _load_json("extracted_content.json")
    assert isinstance(data, list)
    return data


def load_query_intents() -> list[dict[str, Any]]:
    data = _load_json("query_intents.json")
    assert isinstance(data, list)
    return data
