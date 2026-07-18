"""Folder indexer entry point. See indexer/README.md and spec.md §6.1."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path


def _iso_utc(epoch_seconds: float) -> str:
    return (
        datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _created_epoch(stat_result: os.stat_result) -> float:
    birth = getattr(stat_result, "st_birthtime", None)
    if birth is not None:
        return float(birth)
    return float(stat_result.st_ctime)


def index_folder(path: str) -> list[dict]:
    """Walk *path* (top-level only) and return FileRecord dicts.

    Emits one record per immediate child file. Subdirectories are skipped.
    Does not read file contents or modify the folder.
    """
    root = Path(path).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
    root = root.resolve()

    records: list[dict] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_file():
            continue
        stat_result = child.stat()
        records.append(
            {
                "path": child.resolve().as_posix(),
                "filename": child.name,
                "extension": child.suffix,
                "size_bytes": stat_result.st_size,
                "created_at": _iso_utc(_created_epoch(stat_result)),
                "modified_at": _iso_utc(stat_result.st_mtime),
            }
        )
    return records
