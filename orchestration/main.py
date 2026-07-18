"""Entry: python -m orchestration.main --demo-stubs"""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from orchestration.composition import build_app
from orchestration.window import CodyWindow


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cody orchestration shell")
    parser.add_argument(
        "--demo-stubs",
        action="store_true",
        help="Wire fixture-backed stubs for all six entry points",
    )
    parser.add_argument(
        "--folder",
        default="C:/Users/troy/Desktop",
        help="Initial scanned folder path",
    )
    parser.add_argument(
        "--no-voice",
        action="store_true",
        help="Disable voice (visual-only reveal)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle = build_app(demo_stubs=args.demo_stubs, voice_enabled=not args.no_voice)

    app = QApplication.instance() or QApplication(sys.argv)
    window = CodyWindow(controller=bundle.controller, folder=args.folder)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
