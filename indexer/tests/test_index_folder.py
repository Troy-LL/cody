"""Indexer §6.1: top-level FileRecord emission (read-only metadata)."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from contracts.schemas import FILE_RECORD_KEYS
from indexer.index_folder import index_folder


def _fingerprint_tree(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full = Path(dirpath) / name
            rel = full.relative_to(root).as_posix()
            out[rel] = hashlib.sha256(full.read_bytes()).hexdigest()
    return out


def _write(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    return path


@pytest.fixture
def demo_folder(tmp_path: Path) -> Path:
    (tmp_path / "receipt_lazada.pdf").write_bytes(b"%PDF-1.4 demo")
    (tmp_path / "todo_list.txt").write_text("buy milk\n", encoding="utf-8")
    (tmp_path / "no_ext_file").write_text("plain", encoding="utf-8")
    nested = tmp_path / "nested_dir"
    nested.mkdir()
    (nested / "hidden_inside.txt").write_text("should not index", encoding="utf-8")
    return tmp_path


def test_returns_file_record_for_each_top_level_file(demo_folder: Path) -> None:
    records = index_folder(str(demo_folder))
    names = {r["filename"] for r in records}
    assert names == {"receipt_lazada.pdf", "todo_list.txt", "no_ext_file"}
    assert all(FILE_RECORD_KEYS <= r.keys() for r in records)


def test_skips_subdirectory_contents(demo_folder: Path) -> None:
    records = index_folder(str(demo_folder))
    paths = [r["path"] for r in records]
    assert not any("hidden_inside" in p for p in paths)
    assert not any(r["filename"] == "nested_dir" for r in records)


def test_extension_includes_leading_dot(demo_folder: Path) -> None:
    by_name = {r["filename"]: r for r in index_folder(str(demo_folder))}
    assert by_name["receipt_lazada.pdf"]["extension"] == ".pdf"
    assert by_name["todo_list.txt"]["extension"] == ".txt"
    assert by_name["no_ext_file"]["extension"] == ""


def test_path_is_absolute_posix(demo_folder: Path) -> None:
    for record in index_folder(str(demo_folder)):
        assert Path(record["path"]).is_absolute()
        assert record["filename"] == Path(record["path"]).name
        assert "\\" not in record["path"]


def test_size_bytes_matches_filesystem(demo_folder: Path) -> None:
    by_name = {r["filename"]: r for r in index_folder(str(demo_folder))}
    pdf = demo_folder / "receipt_lazada.pdf"
    assert by_name["receipt_lazada.pdf"]["size_bytes"] == pdf.stat().st_size


def test_timestamps_are_iso8601_utc(demo_folder: Path) -> None:
    for record in index_folder(str(demo_folder)):
        for key in ("created_at", "modified_at"):
            value = record[key]
            assert isinstance(value, str)
            assert value.endswith("Z")
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            assert parsed.tzinfo is not None


def test_empty_folder_returns_empty_list(tmp_path: Path) -> None:
    assert index_folder(str(tmp_path)) == []


def test_json_serializable_file_records(demo_folder: Path) -> None:
    payload = json.dumps(index_folder(str(demo_folder)))
    loaded = json.loads(payload)
    assert isinstance(loaded, list)
    assert all(FILE_RECORD_KEYS <= item.keys() for item in loaded)


def test_scan_does_not_modify_folder(demo_folder: Path) -> None:
    before = _fingerprint_tree(demo_folder)
    index_folder(str(demo_folder))
    after = _fingerprint_tree(demo_folder)
    assert before == after


def test_flat_folder_returns_file_records(tmp_path: Path) -> None:
    _write(tmp_path / "receipt_lazada.pdf", b"%PDF-sample")
    _write(tmp_path / "todo_list.txt", b"buy milk")
    _write(tmp_path / "notes", b"no extension")

    records = index_folder(str(tmp_path))
    by_name = {r["filename"]: r for r in records}
    assert set(by_name) == {"receipt_lazada.pdf", "todo_list.txt", "notes"}
    assert by_name["receipt_lazada.pdf"]["path"] == (
        tmp_path / "receipt_lazada.pdf"
    ).resolve().as_posix()
    assert by_name["notes"]["extension"] == ""


def test_does_not_recurse_into_subdirectory(tmp_path: Path) -> None:
    _write(tmp_path / "top.txt", b"top")
    nested = tmp_path / "subdir"
    nested.mkdir()
    _write(nested / "nested.txt", b"nested")

    names = {r["filename"] for r in index_folder(str(tmp_path))}
    assert names == {"top.txt"}


def test_read_only_does_not_modify_folder(tmp_path: Path) -> None:
    target = _write(tmp_path / "keep_me.bin", b"unchanged-bytes")
    before_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    before_names = sorted(p.name for p in tmp_path.iterdir())

    index_folder(str(tmp_path))

    assert hashlib.sha256(target.read_bytes()).hexdigest() == before_hash
    assert sorted(p.name for p in tmp_path.iterdir()) == before_names


def test_missing_path_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        index_folder(str(missing))


def test_file_path_raises_not_a_directory(tmp_path: Path) -> None:
    file_path = _write(tmp_path / "only_file.txt", b"x")
    with pytest.raises(NotADirectoryError):
        index_folder(str(file_path))
