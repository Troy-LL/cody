"""Speech-to-text listen for voice-controlled Cody sessions."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ListenUnavailable(RuntimeError):
    """Microphone / STT stack not available."""


def listen(*, timeout_s: float = 5.0, phrase_time_limit_s: float = 12.0) -> str:
    """Listen once and return transcript text.

    Soft contract for callers: raises ``ListenUnavailable`` when STT cannot run
    (missing SpeechRecognition/PyAudio, no mic). Empty transcript → ``""``.
    """
    try:
        import speech_recognition as sr  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ListenUnavailable(
            "SpeechRecognition not installed. pip install SpeechRecognition pyaudio"
        ) from exc

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(
                source,
                timeout=timeout_s,
                phrase_time_limit=phrase_time_limit_s,
            )
    except Exception as exc:  # noqa: BLE001 — mic hardware / portaudio
        raise ListenUnavailable(f"microphone listen failed: {exc}") from exc

    try:
        # Offline-friendly path first when available.
        return str(recognizer.recognize_sphinx(audio))
    except Exception:
        pass

    try:
        return str(recognizer.recognize_google(audio))
    except Exception as exc:  # noqa: BLE001
        logger.warning("listen: recognition failed: %s", exc)
        return ""
