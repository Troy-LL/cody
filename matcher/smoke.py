"""Throwaway Codex smoke for one Lazada golden (delete in Phase 8)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fixtures.load import load_extracted_content, load_file_records
from matcher.match import match

GOLDEN_PATH = Path(__file__).resolve().parent / "golden_cases.json"


def main() -> int:
    os.environ["MATCHER_STUB"] = "0"
    cases = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    case = next(c for c in cases if c["id"] == "lazada_receipt_taglish")
    files = load_file_records()
    content = load_extracted_content()
    result = match(files, content, case["intent"], use_stub=False)
    print(json.dumps(result, indent=2))
    if result["best_match"]["path"] != case["expected_path"]:
        print(
            f"smoke FAIL: got {result['best_match']['path']!r}, "
            f"expected {case['expected_path']!r}",
            file=sys.stderr,
        )
        return 1
    print("smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
