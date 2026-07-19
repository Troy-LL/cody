"""Record a mic clip and transcribe via OpenAI Whisper."""
from __future__ import annotations

import io
import logging
import wave

logger = logging.getLogger("cody.stt")


def _read_frames(seconds: float, samplerate: int):
    import sounddevice as sd

    frames = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    return frames


def record_clip(seconds: float, samplerate: int = 16000) -> bytes:
    frames = _read_frames(seconds, samplerate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(frames.tobytes())
    return buf.getvalue()


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
