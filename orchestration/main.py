"""Entry: python -m orchestration.main --demo-stubs"""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from orchestration.composition import build_app
from orchestration.window import ClickyWindow


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clicky orchestration shell")
    parser.add_argument(
        "--demo-stubs",
        action="store_true",
        help="Wire fixture-backed stubs for all six entry points",
    )
    parser.add_argument(
        "--folder",
        default="C:/Users/troy/Desktop",
        help="Folder label shown in the idle window (scan wired in later tasks)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle = build_app(demo_stubs=args.demo_stubs)
    del bundle  # reserved for Tasks 3+ pipeline wiring

    app = QApplication.instance() or QApplication(sys.argv)
    window = ClickyWindow(folder_label=args.folder)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
