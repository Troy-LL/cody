"""Tests for indexer.index_folder — spec.md §6.1 / openspec indexer."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import pytest

from contracts.schemas import FILE_RECORD_KEYS
from indexer.index_folder import index_folder


def _write(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    return path


def test_empty_folder_returns_empty_list(tmp_path: Path) -> None:
    assert index_folder(str(tmp_path)) == []


def test_flat_folder_returns_file_records(tmp_path: Path) -> None:
    _write(tmp_path / "receipt_lazada.pdf", b"%PDF-sample")
    _write(tmp_path / "todo_list.txt", b"buy milk")
    _write(tmp_path / "notes", b"no extension")

    records = index_folder(str(tmp_path))

    assert len(records) == 3
    by_name = {r["filename"]: r for r in records}
    assert set(by_name) == {"receipt_lazada.pdf", "todo_list.txt", "notes"}

    for record in records:
        assert FILE_RECORD_KEYS <= record.keys()
        assert isinstance(record["size_bytes"], int)
        assert isinstance(record["created_at"], str)
        assert isinstance(record["modified_at"], str)
        assert record["created_at"].endswith("Z")
        assert record["modified_at"].endswith("Z")
        datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(record["modified_at"].replace("Z", "+00:00"))
        assert Path(record["path"]).is_absolute()

    pdf = by_name["receipt_lazada.pdf"]
    assert pdf["extension"] == ".pdf"
    assert pdf["size_bytes"] == len(b"%PDF-sample")
    assert pdf["path"] == str((tmp_path / "receipt_lazada.pdf").resolve())

    assert by_name["todo_list.txt"]["extension"] == ".txt"
    assert by_name["notes"]["extension"] == ""


def test_does_not_recurse_into_subdirectory(tmp_path: Path) -> None:
    _write(tmp_path / "top.txt", b"top")
    nested = tmp_path / "subdir"
    nested.mkdir()
    _write(nested / "nested.txt", b"nested")

    records = index_folder(str(tmp_path))

    names = {r["filename"] for r in records}
    assert names == {"top.txt"}
    assert "nested.txt" not in names


def test_read_only_does_not_modify_folder(tmp_path: Path) -> None:
    target = _write(tmp_path / "keep_me.bin", b"unchanged-bytes")
    before_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    before_names = sorted(p.name for p in tmp_path.iterdir())

    index_folder(str(tmp_path))

    after_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    after_names = sorted(p.name for p in tmp_path.iterdir())
    assert after_hash == before_hash
    assert after_names == before_names


def test_missing_path_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        index_folder(str(missing))


def test_file_path_raises_not_a_directory(tmp_path: Path) -> None:
    file_path = _write(tmp_path / "only_file.txt", b"x")
    with pytest.raises(NotADirectoryError):
        index_folder(str(file_path))
