"""Background mic listener for 'Hey Cody…' (SpeechRecognition + sounddevice/PyAudio)."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16_000
CHANNELS = 1
SAMPLE_WIDTH = 2  # int16


def listen_available() -> tuple[bool, str]:
    """Return (ok, reason) for mic STT dependencies."""
    try:
        import speech_recognition as sr  # noqa: F401
    except ImportError:
        return False, "pip install SpeechRecognition"
    try:
        import sounddevice as sd  # noqa: F401
        import numpy as np  # noqa: F401

        return True, "sounddevice"
    except ImportError:
        pass
    try:
        import pyaudio  # noqa: F401

        return True, "pyaudio"
    except ImportError:
        return False, "pip install sounddevice numpy (or pyaudio)"


class HeyCodyListener:
    def __init__(
        self,
        on_transcript: Callable[[str], None],
        on_level: Callable[[float], None] | None = None,
    ) -> None:
        self._on_transcript = on_transcript
        self._on_level = on_level
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        ok, backend = listen_available()
        self.available = ok
        self.backend = backend if ok else ""
        self.error: str | None = None if ok else backend
        if not ok:
            logger.warning(self.error)

    def start(self) -> bool:
        if not self.available or self._thread:
            return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        self._thread = None

    def _loop(self) -> None:
        if self.backend == "sounddevice":
            self._loop_sounddevice()
        else:
            self._loop_pyaudio()

    def _recognize(self, raw: bytes) -> str | None:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        audio = sr.AudioData(raw, SAMPLE_RATE, SAMPLE_WIDTH)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return None
        except sr.RequestError as exc:
            logger.warning("speech API error: %s", exc)
            return None
        except Exception:
            logger.exception("recognize failed")
            return None

    def _emit(self, text: str) -> None:
        logger.info("heard: %s", text)
        try:
            self._on_transcript(text)
        except Exception:
            logger.exception("on_transcript failed")

    def _report_level(self, energy: float, threshold: float) -> None:
        if self._on_level is None:
            return
        # Quiet ≈ 0, speaking ≈ 0.4–1.0
        level = min(1.0, max(0.0, energy / max(threshold * 2.2, 1.0)))
        try:
            self._on_level(level)
        except Exception:
            logger.exception("on_level failed")

    def _loop_sounddevice(self) -> None:
        import numpy as np
        import sounddevice as sd

        logger.info("Hey Cody listener running (sounddevice)")
        # Calibrate ambient briefly
        cal = sd.rec(int(0.4 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16")
        sd.wait()
        ambient = float(np.sqrt(np.mean(cal.astype(np.float32) ** 2)))
        threshold = max(350.0, ambient * 3.5)

        while not self._stop.is_set():
            # Wait for speech energy
            chunk = sd.rec(int(0.35 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16")
            sd.wait()
            if self._stop.is_set():
                break
            energy = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
            self._report_level(energy, threshold)
            if energy < threshold:
                continue

            # Capture phrase (up to ~6s, stop early on trailing silence)
            parts = [chunk]
            silence_runs = 0
            for _ in range(16):  # ~5.6s more
                if self._stop.is_set():
                    break
                part = sd.rec(int(0.35 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16")
                sd.wait()
                parts.append(part)
                e = float(np.sqrt(np.mean(part.astype(np.float32) ** 2)))
                self._report_level(e, threshold)
                if e < threshold * 0.7:
                    silence_runs += 1
                    if silence_runs >= 3 and len(parts) >= 4:
                        break
                else:
                    silence_runs = 0

            raw = np.concatenate(parts).tobytes()
            text = self._recognize(raw)
            if text:
                self._emit(text)

    def _loop_pyaudio(self) -> None:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        try:
            mic = sr.Microphone()
        except OSError as exc:
            self.error = f"No microphone: {exc}"
            logger.warning(self.error)
            return

        with mic as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
            except Exception:
                pass

        logger.info("Hey Cody listener running (pyaudio)")
        while not self._stop.is_set():
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=2.5, phrase_time_limit=7)
            except sr.WaitTimeoutError:
                continue
            except Exception:
                logger.exception("listen failed")
                continue
            try:
                text = recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                continue
            except sr.RequestError as exc:
                logger.warning("speech API error: %s", exc)
                continue
            except Exception:
                logger.exception("recognize failed")
                continue
            if text:
                self._emit(text)
