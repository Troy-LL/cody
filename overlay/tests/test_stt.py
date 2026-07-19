from __future__ import annotations

import sys
import types

from overlay import stt


def test_transcribe_empty_bytes_returns_empty():
    assert stt.transcribe(b"", api_key="sk-x") == ""


def test_wav_header(monkeypatch):
    import numpy as np

    monkeypatch.setattr(stt, "_read_frames", lambda s, r: np.zeros((r, 1), dtype="int16"))
    data = stt.record_clip(0.1, samplerate=16000)
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE"


def test_record_clip_while_stops_when_released(monkeypatch):
    import numpy as np

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, chunk):
            return np.zeros((chunk, 1), dtype="int16"), None

    fake_sd = types.SimpleNamespace(InputStream=lambda **_k: FakeStream())
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)

    calls = {"n": 0}

    def is_held() -> bool:
        calls["n"] += 1
        return calls["n"] <= 2

    data = stt.record_clip_while(
        is_held,
        samplerate=16000,
        min_seconds=0.05,
        max_seconds=2.0,
    )
    assert data[:4] == b"RIFF"
    assert calls["n"] >= 2
