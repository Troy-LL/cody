"""pytest-qt smoke for ClickyWindow wiring."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt

from orchestration.controller import ClickyController, ControllerDeps
from orchestration.window import ClickyWindow


def _fast_deps() -> ControllerDeps:
    def index_folder(path: str) -> list[dict[str, Any]]:
        del path
        return [
            {
                "path": r"C:\Users\troy\Desktop\receipt_lazada.pdf",
                "filename": "receipt_lazada.pdf",
                "extension": ".pdf",
                "size_bytes": 1,
                "created_at": "2026-07-01T00:00:00Z",
                "modified_at": "2026-07-01T00:00:00Z",
            }
        ]

    def extract(path: str) -> dict[str, Any]:
        return {
            "path": path,
            "extractable": True,
            "text_snippet": "Lazada",
            "extraction_method": "pdf",
        }

    def parse_query(text: str) -> dict[str, Any]:
        return {
            "raw_query": text,
            "description": "receipt",
            "time_hint": None,
            "type_hint": None,
            "language_mix": "taglish",
        }

    def match(files, content, intent):
        del content, intent
        return {
            "best_match": {
                "path": files[0]["path"],
                "confidence": 0.91,
                "reasoning": "Lazada receipt matched",
            },
            "alternatives": [],
        }

    return ControllerDeps(
        index_folder=index_folder,
        extract=extract,
        parse_query=parse_query,
        match=match,
        reveal=lambda p: True,
        speak=lambda f, m: True,
        voice_enabled=True,
        language_mode="auto",
    )


def test_window_find_updates_result(qtbot) -> None:
    ctl = ClickyController(_fast_deps())
    window = ClickyWindow(controller=ctl, folder=r"C:\Users\troy\Desktop")
    qtbot.addWidget(window)

    window.query_edit.setText("yung resibo ko sa Lazada last week")
    qtbot.mouseClick(window.find_button, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: window.status_label.text() == "result", timeout=3000)
    assert window.result_label.text() == "receipt_lazada.pdf"
    assert "Lazada" in window.reasoning_label.text()
    assert "Desktop" in window.breadcrumb_label.text()


def test_window_idle_without_controller(qtbot) -> None:
    window = ClickyWindow(folder=r"C:\Users\troy\Desktop")
    qtbot.addWidget(window)
    assert window.status_label.text() == "idle"
    assert window.find_button.isEnabled()
