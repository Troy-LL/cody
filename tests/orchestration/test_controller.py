"""Controller state machine and fallback tests."""

from __future__ import annotations

import time
from typing import Any

from orchestration.controller import CodyController, ControllerDeps, map_language_mode


def _deps(
    *,
    reveal_ok: bool = True,
    speak_ok: bool = True,
    voice_enabled: bool = True,
    boom: bool = False,
    segment_delay_ms: int = 0,
) -> ControllerDeps:
    def index_folder(path: str) -> list[dict[str, Any]]:
        del path
        if boom:
            raise RuntimeError("index failed")
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
                "reasoning": "Lazada receipt",
            },
            "alternatives": [],
        }

    def reveal(path: str) -> bool:
        del path
        return reveal_ok

    def speak(filename: str, language_mode: str) -> bool:
        del filename, language_mode
        return speak_ok

    return ControllerDeps(
        index_folder=index_folder,
        extract=extract,
        parse_query=parse_query,
        match=match,
        reveal=reveal,
        speak=speak,
        voice_enabled=voice_enabled,
        language_mode="auto",
        segment_delay_ms=segment_delay_ms,
    )


def test_map_language_mode_auto() -> None:
    assert map_language_mode("auto", "taglish") == "taglish"
    assert map_language_mode("auto", "tl") == "tl"
    assert map_language_mode("en", "taglish") == "en"


def test_happy_path_states(qtbot) -> None:
    ctl = CodyController(_deps())
    states: list[str] = []
    ctl.state_changed.connect(states.append)
    results: list[object] = []
    ctl.result_ready.connect(results.append)
    segments: list[str] = []
    ctl.segment_lit.connect(lambda s, i: segments.append(s))

    assert ctl.submit(r"C:\Users\troy\Desktop", "yung resibo")
    assert not ctl.submit(r"C:\Users\troy\Desktop", "second")  # duplicate blocked

    qtbot.waitUntil(lambda: ctl.state == "result", timeout=3000)
    assert "thinking" in states
    assert "revealing" in states
    assert states[-1] == "result"
    assert results
    assert segments[0] == "Desktop"


def test_segments_sequenced_before_reveal(qtbot) -> None:
    """§6.7: segments light with delay; OS reveal lands on the final segment."""
    ctl = CodyController(_deps(segment_delay_ms=40))
    events: list[tuple[str, float]] = []

    ctl.segment_lit.connect(lambda s, i: events.append((f"seg:{s}", time.perf_counter())))
    ctl.reveal_triggered.connect(lambda ok: events.append((f"reveal:{ok}", time.perf_counter())))

    ctl.submit(r"C:\Users\troy\Desktop", "q")
    qtbot.waitUntil(lambda: ctl.state == "result", timeout=3000)

    kinds = [name for name, _ in events]
    assert kinds[0].startswith("seg:")
    assert kinds[-1] == "reveal:True"
    assert any(k == "seg:Desktop" for k in kinds)
    assert any(k.endswith("receipt_lazada.pdf") for k in kinds)

    seg_times = [t for name, t in events if name.startswith("seg:")]
    reveal_time = next(t for name, t in events if name.startswith("reveal:"))
    assert len(seg_times) >= 2
    assert seg_times[-1] <= reveal_time
    # Gap between first two segments roughly respects delay (not a tight sync loop).
    assert seg_times[1] - seg_times[0] >= 0.02


def test_reveal_failure_is_error(qtbot) -> None:
    ctl = CodyController(_deps(reveal_ok=False))
    errors: list[str] = []
    ctl.error_occurred.connect(errors.append)
    ctl.submit(r"C:\Users\troy\Desktop", "q")
    qtbot.waitUntil(lambda: ctl.state == "error", timeout=3000)
    assert errors
    assert "Reveal" in errors[0]


def test_voice_failure_still_result(qtbot) -> None:
    ctl = CodyController(_deps(speak_ok=False))
    speak_flags: list[bool] = []
    ctl.speak_triggered.connect(speak_flags.append)
    ctl.submit(r"C:\Users\troy\Desktop", "q")
    qtbot.waitUntil(lambda: ctl.state == "result", timeout=3000)
    assert speak_flags == [False]


def test_voice_disabled_skips_speak(qtbot) -> None:
    ctl = CodyController(_deps(voice_enabled=False, speak_ok=False))
    speak_flags: list[bool] = []
    ctl.speak_triggered.connect(speak_flags.append)
    ctl.submit(r"C:\Users\troy\Desktop", "q")
    qtbot.waitUntil(lambda: ctl.state == "result", timeout=3000)
    assert speak_flags == [True]


def test_pipeline_exception_errors(qtbot) -> None:
    ctl = CodyController(_deps(boom=True))
    ctl.submit(r"C:\Users\troy\Desktop", "q")
    qtbot.waitUntil(lambda: ctl.state == "error", timeout=3000)
