"""Voice-controlled Cody session: listen → AI speak → OS cursor → reveal."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from overlay.cursor import point_at, start_follow, stop
from reveal.reveal import reveal
from voice.listen import ListenUnavailable, listen
from voice.speak import speak, speak_text

logger = logging.getLogger(__name__)


@dataclass
class SessionResult:
    transcript: str
    path: str | None
    spoke: bool
    revealed: bool
    pointed: bool


def _default_resolve(transcript: str, root: Path) -> Path | None:
    """Naive voice resolver for demos without the full matcher pipeline.

    Looks for a filename-like token or substring match under *root*.
    """
    text = transcript.strip().lower()
    if not text or not root.is_dir():
        return None

    # Explicit "reveal foo.pdf" / "open foo.pdf"
    m = re.search(r"(?:reveal|open|find|show)\s+([\w.\- ]+\.[a-z0-9]+)", text, re.I)
    if m:
        candidate = root / m.group(1).strip()
        if candidate.is_file():
            return candidate

    files = [p for p in root.iterdir() if p.is_file()]
    for path in files:
        stem = path.stem.lower().replace("_", " ")
        name = path.name.lower()
        if name in text or stem in text:
            return path
        tokens = [t for t in re.split(r"\W+", text) if len(t) > 3]
        if any(t in stem or t in name for t in tokens):
            return path
    return None


def handle_transcript(
    transcript: str,
    *,
    root: str | Path,
    language_mode: str = "en",
    resolve: Callable[[str, Path], Path | None] | None = None,
) -> SessionResult:
    """Process one voice transcript end-to-end."""
    folder = Path(root)
    resolver = resolve or _default_resolve
    path = resolver(transcript, folder)

    if path is None:
        spoke = speak_text(
            "I could not find that file. Try naming it or describing it again.",
            language_mode,
        )
        return SessionResult(
            transcript=transcript,
            path=None,
            spoke=spoke,
            revealed=False,
            pointed=False,
        )

    spoke_ack = speak_text(f"Found it. Pointing to {path.name}.", language_mode)
    spoke_file = speak(path.name, language_mode)
    start_follow()
    revealed = reveal(str(path))
    pointed = point_at(str(path)) if revealed else False
    return SessionResult(
        transcript=transcript,
        path=str(path),
        spoke=spoke_ack or spoke_file,
        revealed=revealed,
        pointed=pointed,
    )


def run_voice_session(
    *,
    root: str | Path,
    language_mode: str = "en",
    rounds: int = 1,
    resolve: Callable[[str, Path], Path | None] | None = None,
) -> list[SessionResult]:
    """Run *rounds* of listen → respond → point.

    Purely voice-controlled loop for the redirected Clicky/Cody scope.
    """
    results: list[SessionResult] = []
    speak_text("Cody is listening. Tell me which file to find.", language_mode)
    try:
        for _ in range(max(1, rounds)):
            try:
                transcript = listen()
            except ListenUnavailable as exc:
                logger.warning("session: listen unavailable: %s", exc)
                speak_text(
                    "I cannot hear the microphone. Check SpeechRecognition setup.",
                    language_mode,
                )
                break
            if not transcript.strip():
                speak_text("I did not catch that. Please say it again.", language_mode)
                continue
            results.append(
                handle_transcript(
                    transcript,
                    root=root,
                    language_mode=language_mode,
                    resolve=resolve,
                )
            )
    finally:
        stop()
    return results
