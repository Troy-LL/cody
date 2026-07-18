"""Run matcher golden cases for shape and optional path checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fixtures.load import load_extracted_content, load_file_records
from matcher.match import match
from matcher.types import MATCH_RESULT_KEYS

GOLDEN_PATH = Path(__file__).resolve().parent / "golden_cases.json"


def load_goldens() -> list[dict]:
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    return data


def _validate_shape(result: dict) -> None:
    missing = MATCH_RESULT_KEYS - set(result)
    if missing:
        raise AssertionError(f"MatchResult missing keys: {sorted(missing)}")
    best = result["best_match"]
    for key in ("path", "confidence", "reasoning"):
        if key not in best:
            raise AssertionError(f"best_match missing {key}")
    if not isinstance(best["reasoning"], str) or not best["reasoning"].strip():
        raise AssertionError("reasoning must be a non-empty string")


def run(*, shape_only: bool) -> int:
    files = load_file_records()
    content = load_extracted_content()
    paths = {f["path"] for f in files}
    failures = 0
    for case in load_goldens():
        expected = case["expected_path"]
        if expected not in paths:
            print(f"FAIL {case['id']}: expected_path not in fixtures")
            failures += 1
            continue
        result = match(files, content, case["intent"])
        try:
            _validate_shape(result)
        except AssertionError as exc:
            print(f"FAIL {case['id']}: {exc}")
            failures += 1
            continue
        if not shape_only and result["best_match"]["path"] != expected:
            print(
                f"FAIL {case['id']}: path {result['best_match']['path']!r} "
                f"!= {expected!r}"
            )
            failures += 1
            continue
        print(f"ok {case['id']}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--shape-only",
        action="store_true",
        help="Assert MatchResult shape only; skip expected_path equality",
    )
    args = parser.parse_args(argv)
    return run(shape_only=args.shape_only)


if __name__ == "__main__":
    sys.exit(main())
