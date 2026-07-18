"""Tagalog ear-check for OpenVoice/MeloTTS (not run in CI).

Requires:
  - OpenVoice + MeloTTS installed (see voice/README.md)
  - copy voice/config.example.json → voice/config.local.json
  - for tone_convert=true: checkpoints_v2 + reference wav

Usage (from repo root):
  python voice/scripts/smoke_tl.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice.speak import speak  # noqa: E402


def main() -> int:
    ok = speak("receipt_lazada.pdf", "tl")
    print(f"speak(... 'tl') -> {ok}")
    print("Ear-check: TL text uses Melo EN speaker (OpenVoice has no native Tagalog).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
