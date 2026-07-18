"""Minimal idle PySide6 window for Clicky (no pipeline yet)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ClickyWindow(QMainWindow):
    """Idle shell: folder label, query field, disabled Find, status idle."""

    def __init__(self, folder_label: str = "(no folder)", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Clicky")
        self.setMinimumWidth(480)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        folder = QLabel(folder_label, central)
        folder.setObjectName("folderLabel")
        layout.addWidget(folder)

        row = QHBoxLayout()
        query = QLineEdit(central)
        query.setObjectName("queryEdit")
        query.setPlaceholderText("Describe a file…")
        row.addWidget(query)

        find_btn = QPushButton("Find", central)
        find_btn.setObjectName("findButton")
        find_btn.setEnabled(False)
        row.addWidget(find_btn)
        layout.addLayout(row)

        status = QLabel("idle", central)
        status.setObjectName("statusLabel")
        layout.addWidget(status)
