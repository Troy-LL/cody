"""Demo stubs, composition, and idle window smoke tests."""

from __future__ import annotations

from contracts.schemas import (
    EXTRACTED_CONTENT_KEYS,
    FILE_RECORD_KEYS,
    MATCH_RESULT_KEYS,
    QUERY_INTENT_KEYS,
    REVEAL_ANIMATION_KEYS,
)


def test_demo_stubs_return_contract_shapes() -> None:
    from orchestration.demo_stubs import DemoStubs

    stubs = DemoStubs()
    records = stubs.index_folder("C:/Users/troy/Desktop")
    assert records
    assert FILE_RECORD_KEYS <= records[0].keys()

    content = stubs.extract(records[0]["path"])
    assert EXTRACTED_CONTENT_KEYS <= content.keys()

    intent = stubs.parse_query("yung resibo ko sa Lazada last week")
    assert QUERY_INTENT_KEYS <= intent.keys()

    match = stubs.match(records, [content], intent)
    assert MATCH_RESULT_KEYS <= match.keys()

    assert stubs.reveal(match["best_match"]["path"]) is True
    assert stubs.speak("receipt_lazada.pdf", "tl") is True

    animation = stubs.build_reveal_animation(
        match["best_match"]["path"], "C:/Users/troy/Desktop"
    )
    assert REVEAL_ANIMATION_KEYS <= animation.keys()


def test_composition_builds_with_demo_stubs() -> None:
    from orchestration.composition import build_app

    app = build_app(demo_stubs=True)
    assert app is not None
    assert hasattr(app, "stubs")
    assert app.stubs is not None


def test_idle_window_constructs(qtbot) -> None:
    from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton

    from orchestration.window import ClickyWindow

    window = ClickyWindow(folder_label="C:/Users/troy/Desktop")
    qtbot.addWidget(window)

    assert window.windowTitle() == "Clicky"
    assert window.findChild(QLabel, "folderLabel") is not None
    assert window.findChild(QLineEdit, "queryEdit") is not None
    find_btn = window.findChild(QPushButton, "findButton")
    assert find_btn is not None
    assert find_btn.isEnabled() is False
    status = window.findChild(QLabel, "statusLabel")
    assert status is not None
    assert status.text() == "idle"
