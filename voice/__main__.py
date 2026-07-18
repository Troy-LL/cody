"""Voice-controlled Cody entry: python -m voice --root PATH"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from voice.session import run_voice_session


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Voice-controlled Cody (listen → speak → point)")
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Folder to search (top-level files)",
    )
    parser.add_argument("--lang", default="en", choices=["en", "tl", "taglish"])
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()

    results = run_voice_session(root=args.root, language_mode=args.lang, rounds=args.rounds)
    for item in results:
        print(
            f"heard={item.transcript!r} path={item.path!r} "
            f"spoke={item.spoke} revealed={item.revealed} pointed={item.pointed}"
        )
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
