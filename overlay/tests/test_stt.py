from overlay import stt


def test_transcribe_empty_bytes_returns_empty():
    assert stt.transcribe(b"", api_key="sk-x") == ""


def test_wav_header(monkeypatch):
    import numpy as np

    monkeypatch.setattr(stt, "_read_frames", lambda s, r: np.zeros((r, 1), dtype="int16"))
    data = stt.record_clip(0.1, samplerate=16000)
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE"
