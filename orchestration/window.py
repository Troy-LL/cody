"""PySide6 Clicky shell wired to ClickyController."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from orchestration.controller import ClickyController
from orchestration.pipeline import PipelineResolution


class ClickyWindow(QMainWindow):
    """Happy-path UI: folder, query, Find, breadcrumb, reasoning."""

    def __init__(
        self,
        controller: ClickyController | None = None,
        folder: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self.setWindowTitle("Clicky")
        self.setMinimumWidth(560)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        folder_row = QHBoxLayout()
        self.folder_label = QLabel(folder or "(no folder)", central)
        self.folder_label.setObjectName("folderLabel")
        folder_row.addWidget(self.folder_label, stretch=1)
        self.browse_button = QPushButton("Folder…", central)
        self.browse_button.setObjectName("browseButton")
        self.browse_button.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.browse_button)
        layout.addLayout(folder_row)

        row = QHBoxLayout()
        self.query_edit = QLineEdit(central)
        self.query_edit.setObjectName("queryEdit")
        self.query_edit.setPlaceholderText("Describe a file…")
        row.addWidget(self.query_edit)

        self.find_button = QPushButton("Find", central)
        self.find_button.setObjectName("findButton")
        self.find_button.setEnabled(bool(folder))
        self.find_button.clicked.connect(self._on_find)
        row.addWidget(self.find_button)
        layout.addLayout(row)

        self.status_label = QLabel("idle", central)
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        self.breadcrumb_label = QLabel("", central)
        self.breadcrumb_label.setObjectName("breadcrumbLabel")
        layout.addWidget(self.breadcrumb_label)

        self.result_label = QLabel("", central)
        self.result_label.setObjectName("resultLabel")
        layout.addWidget(self.result_label)

        self.confidence_label = QLabel("", central)
        self.confidence_label.setObjectName("confidenceLabel")
        layout.addWidget(self.confidence_label)

        self.reasoning_label = QLabel("", central)
        self.reasoning_label.setObjectName("reasoningLabel")
        self.reasoning_label.setWordWrap(True)
        layout.addWidget(self.reasoning_label)

        self._lit_segments: list[str] = []

        if controller is not None:
            controller.state_changed.connect(self._on_state)
            controller.result_ready.connect(self._on_result)
            controller.error_occurred.connect(self._on_error)
            controller.segment_lit.connect(self._on_segment)

    def set_folder(self, folder: str) -> None:
        self.folder_label.setText(folder)
        self.find_button.setEnabled(bool(folder.strip()))

    @Slot()
    def _browse_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Choose folder")
        if chosen:
            self.set_folder(str(Path(chosen)))

    @Slot()
    def _on_find(self) -> None:
        if self._controller is None:
            return
        root = self.folder_label.text().strip()
        query = self.query_edit.text()
        self._lit_segments.clear()
        self.breadcrumb_label.setText("")
        self.result_label.setText("")
        self.confidence_label.setText("")
        self.reasoning_label.setText("")
        accepted = self._controller.submit(root, query)
        if not accepted and self._controller.state not in {"idle", "result", "error"}:
            # duplicate while active — ignore
            return

    @Slot(str)
    def _on_state(self, state: str) -> None:
        self.status_label.setText(state)
        busy = state in {"thinking", "revealing"}
        self.find_button.setEnabled(not busy and bool(self.folder_label.text().strip()))

    @Slot(str, int)
    def _on_segment(self, segment: str, index: int) -> None:
        del index
        self._lit_segments.append(segment)
        self.breadcrumb_label.setText(" › ".join(self._lit_segments))

    @Slot(object)
    def _on_result(self, resolution: object) -> None:
        assert isinstance(resolution, PipelineResolution)
        name = Path(resolution.path).name
        self.result_label.setText(name)
        self.confidence_label.setText(f"{resolution.confidence:.0%}")
        self.reasoning_label.setText(resolution.reasoning)

    @Slot(str)
    def _on_error(self, message: str) -> None:
        self.reasoning_label.setText(message)
