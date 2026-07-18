"""Content extractor entry point. See extractor/README.md and spec.md §6.2."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader

# Spec §6.2: keep matcher context manageable (500–1000 chars).
_SNIPPET_MAX = 1000

_WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

_SUPPORTED = {
    ".txt": "plain_text",
    ".pdf": "pdf_text_layer",
    ".docx": "docx_paragraphs",
}


def extract(path: str) -> dict:
    """Return ExtractedContent for *path* (soft-fail, never raises for pipeline safety)."""
    method = _SUPPORTED.get(Path(path).suffix.lower())
    if method is None:
        return _unsupported(path)

    file_path = Path(path)
    if not file_path.is_file():
        return _unsupported(path)

    try:
        if method == "plain_text":
            text = _read_txt(file_path)
        elif method == "pdf_text_layer":
            text = _read_pdf(file_path)
        else:
            text = _read_docx(file_path)
    except Exception:
        return _unsupported(path)

    text = (text or "").strip()
    if not text:
        return _unsupported(path)

    return {
        "path": path,
        "extractable": True,
        "text_snippet": _cap_snippet(text),
        "extraction_method": method,
    }


def _unsupported(path: str) -> dict:
    return {
        "path": path,
        "extractable": False,
        "text_snippet": None,
        "extraction_method": "unsupported",
    }


def _cap_snippet(text: str) -> str:
    if len(text) <= _SNIPPET_MAX:
        return text
    return text[:_SNIPPET_MAX]


def _read_txt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _read_docx(path: Path) -> str:
    """Read paragraph text from a docx via stdlib (no lxml / python-docx)."""
    with zipfile.ZipFile(path) as zf:
        xml_bytes = zf.read("word/document.xml")
    root = ElementTree.fromstring(xml_bytes)
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", _WORD_NS):
        texts = [node.text or "" for node in para.findall(".//w:t", _WORD_NS)]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)
