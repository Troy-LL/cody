"""Tests for extractor.extract — spec.md §6.2 / openspec extractor."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from contracts.schemas import EXTRACTED_CONTENT_KEYS
from extractor.extract import extract

SNIPPET_MAX = 1000

# Minimal PDF-1.4 with a Helvetica text layer extractable by pypdf.
_LAZADA_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R
   /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 90 >>
stream
BT /F1 12 Tf 72 720 Td (Lazada Order Confirmation Total PHP 1240) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000407 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
486
%%EOF
"""

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _write_txt(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _write_pdf(path: Path, pdf_bytes: bytes = _LAZADA_PDF) -> Path:
    path.write_bytes(pdf_bytes)
    return path


def _write_docx(path: Path, paragraphs: list[str]) -> Path:
    """Build a minimal .docx (OOXML zip) without python-docx/lxml."""
    document = Element(f"{{{_W_NS}}}document")
    body = SubElement(document, f"{{{_W_NS}}}body")
    for text in paragraphs:
        p = SubElement(body, f"{{{_W_NS}}}p")
        r = SubElement(p, f"{{{_W_NS}}}r")
        t = SubElement(r, f"{{{_W_NS}}}t")
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    content_types = Element(f"{{{_CT_NS}}}Types")
    SubElement(
        content_types,
        f"{{{_CT_NS}}}Default",
        Extension="rels",
        ContentType="application/vnd.openxmlformats-package.relationships+xml",
    )
    SubElement(
        content_types,
        f"{{{_CT_NS}}}Default",
        Extension="xml",
        ContentType="application/xml",
    )
    SubElement(
        content_types,
        f"{{{_CT_NS}}}Override",
        PartName="/word/document.xml",
        ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    )

    rels = Element(f"{{{_REL_NS}}}Relationships")
    SubElement(
        rels,
        f"{{{_REL_NS}}}Relationship",
        Id="rId1",
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        Target="word/document.xml",
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            tostring(content_types, xml_declaration=True, encoding="UTF-8"),
        )
        zf.writestr(
            "_rels/.rels",
            tostring(rels, xml_declaration=True, encoding="UTF-8"),
        )
        zf.writestr(
            "word/document.xml",
            tostring(document, xml_declaration=True, encoding="UTF-8"),
        )
    return path


def test_txt_extracts_plain_text(tmp_path: Path) -> None:
    path = _write_txt(tmp_path / "todo_list.txt", "- buy groceries\n- pay electric bill\n- call mama")

    result = extract(str(path))

    assert EXTRACTED_CONTENT_KEYS <= result.keys()
    assert result["extractable"] is True
    assert result["extraction_method"] == "plain_text"
    assert result["text_snippet"] is not None
    assert "groceries" in result["text_snippet"]
    assert len(result["text_snippet"]) <= SNIPPET_MAX


def test_txt_snippet_is_capped(tmp_path: Path) -> None:
    path = _write_txt(tmp_path / "long.txt", "x" * 2500)

    result = extract(str(path))

    assert result["extractable"] is True
    assert result["text_snippet"] is not None
    assert 500 <= len(result["text_snippet"]) <= SNIPPET_MAX


def test_pdf_text_layer_extracts(tmp_path: Path) -> None:
    path = _write_pdf(tmp_path / "receipt_lazada.pdf")

    result = extract(str(path))

    assert result["extractable"] is True
    assert result["extraction_method"] == "pdf_text_layer"
    assert result["text_snippet"] is not None
    assert "Lazada" in result["text_snippet"]
    assert len(result["text_snippet"]) <= SNIPPET_MAX


def test_docx_paragraphs_extract(tmp_path: Path) -> None:
    path = _write_docx(
        tmp_path / "meeting_notes_july.docx",
        [
            "Sprint planning notes — blockers, owners, and demo checklist for Clicky MVP.",
            "Follow-ups for next week.",
        ],
    )

    result = extract(str(path))

    assert result["extractable"] is True
    assert result["extraction_method"] == "docx_paragraphs"
    assert result["text_snippet"] is not None
    assert "Sprint planning" in result["text_snippet"]
    assert len(result["text_snippet"]) <= SNIPPET_MAX


def test_png_unsupported_soft_fail(tmp_path: Path) -> None:
    path = tmp_path / "lazada_screenshot.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)

    result = extract(str(path))

    assert result["extractable"] is False
    assert result["text_snippet"] is None
    assert result["extraction_method"] == "unsupported"


def test_xlsx_unsupported_soft_fail(tmp_path: Path) -> None:
    path = tmp_path / "budget_q2.xlsx"
    path.write_bytes(b"PK\x03\x04fake-xlsx")

    result = extract(str(path))

    assert result["extractable"] is False
    assert result["text_snippet"] is None
    assert result["extraction_method"] == "unsupported"


def test_missing_file_soft_fail(tmp_path: Path) -> None:
    path = tmp_path / "gone.txt"

    result = extract(str(path))

    assert result["extractable"] is False
    assert result["text_snippet"] is None
    assert result["extraction_method"] == "unsupported"


def test_path_round_trip_windows_style(tmp_path: Path) -> None:
    path = _write_txt(tmp_path / "readme_project.txt", "Clicky demo notes")
    requested = str(path)

    result = extract(requested)

    assert result["path"] == requested


def test_extension_case_insensitive(tmp_path: Path) -> None:
    path = _write_txt(tmp_path / "NOTES.TXT", "hello from upper")

    result = extract(str(path))

    assert result["extractable"] is True
    assert result["extraction_method"] == "plain_text"
    assert "hello" in (result["text_snippet"] or "")


def test_corrupt_pdf_soft_fail(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"%PDF-not-a-real-file")

    result = extract(str(path))

    assert result["extractable"] is False
    assert result["text_snippet"] is None
    assert result["extraction_method"] == "unsupported"
