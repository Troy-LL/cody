"""Record a mic clip and transcribe via OpenAI Whisper."""
from __future__ import annotations

import io
import logging
import wave
from collections.abc import Callable

logger = logging.getLogger("cody.stt")

# int16 RMS at which the level meter reads full-scale (~normal speaking voice)
LEVEL_FULL_SCALE = 3000.0


def _read_frames(seconds: float, samplerate: int):
    import sounddevice as sd

    frames = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    return frames


def _wav_bytes(frames, samplerate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(frames.tobytes())
    return buf.getvalue()


def record_clip(seconds: float, samplerate: int = 16000) -> bytes:
    return _wav_bytes(_read_frames(seconds, samplerate), samplerate)


def record_clip_metered(
    seconds: float,
    on_level: Callable[[float], None] | None = None,
    samplerate: int = 16000,
) -> bytes:
    """Record `seconds` of mic audio, reporting live RMS level (0..1) per chunk."""
    import numpy as np
    import sounddevice as sd

    total = int(seconds * samplerate)
    chunk = max(1, int(0.05 * samplerate))  # ~50ms → 20 updates/sec
    parts = []
    got = 0
    with sd.InputStream(samplerate=samplerate, channels=1, dtype="int16") as stream:
        while got < total:
            data, _ = stream.read(min(chunk, total - got))
            parts.append(data.copy())
            got += len(data)
            if on_level is not None:
                rms = float(np.sqrt(np.mean(data.astype(np.float32) ** 2)))
                try:
                    on_level(min(1.0, rms / LEVEL_FULL_SCALE))
                except Exception:
                    logger.debug("on_level failed", exc_info=True)
    return _wav_bytes(np.concatenate(parts), samplerate)


def record_clip_while(
    is_held: Callable[[], bool],
    on_level: Callable[[float], None] | None = None,
    samplerate: int = 16000,
    min_seconds: float = 0.3,
    max_seconds: float = 15.0,
) -> bytes:
    """Record for as long as `is_held()` is True (hold-to-talk).

    Always captures at least `min_seconds` (so a quick tap isn't empty) and
    stops at `max_seconds` as a safety cap.
    """
    import numpy as np
    import sounddevice as sd

    chunk = max(1, int(0.05 * samplerate))  # ~50ms
    parts = []
    elapsed = 0.0
    with sd.InputStream(samplerate=samplerate, channels=1, dtype="int16") as stream:
        while True:
            data, _ = stream.read(chunk)
            parts.append(data.copy())
            elapsed += len(data) / samplerate
            if on_level is not None:
                rms = float(np.sqrt(np.mean(data.astype(np.float32) ** 2)))
                try:
                    on_level(min(1.0, rms / LEVEL_FULL_SCALE))
                except Exception:
                    logger.debug("on_level failed", exc_info=True)
            if elapsed >= min_seconds and not is_held():
                break
            if elapsed >= max_seconds:
                break
    return _wav_bytes(np.concatenate(parts), samplerate)


def transcribe(wav_bytes: bytes, api_key: str) -> str:
    if not wav_bytes:
        return ""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        audio = io.BytesIO(wav_bytes)
        audio.name = "clip.wav"
        resp = client.audio.transcriptions.create(model="whisper-1", file=audio)
        return (resp.text or "").strip()
    except Exception:
        logger.warning("whisper transcribe failed", exc_info=True)
        return ""
