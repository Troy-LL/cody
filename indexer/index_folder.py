"""Folder indexer entry point. See indexer/README.md and spec.md §6.1."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _iso_utc(timestamp: float) -> str:
    """Format a POSIX timestamp as ISO-8601 UTC ending in Z."""
    return (
        datetime.fromtimestamp(timestamp, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _created_at(stat_result: Any) -> str:
    """Prefer birth time when available (Windows); fall back to ctime."""
    birth = getattr(stat_result, "st_birthtime", None)
    if birth is not None:
        return _iso_utc(float(birth))
    return _iso_utc(stat_result.st_ctime)


def index_folder(path: str) -> list[dict]:
    """Walk *path* (top-level) and return FileRecord dicts.

    Enumerates only immediate file children (non-recursive). Does not read
    file contents or modify the scanned folder.
    """
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    records: list[dict] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_file():
            continue
        stat_result = child.stat()
        records.append(
            {
                "path": str(child.resolve()),
                "filename": child.name,
                "extension": child.suffix,
                "size_bytes": stat_result.st_size,
                "created_at": _created_at(stat_result),
                "modified_at": _iso_utc(stat_result.st_mtime),
            }
        )
    return records
