"""UI state controller: idle -> thinking -> revealing -> result | error."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QThread, Signal, Slot

from contracts.interfaces import Extract, IndexFolder, Match, ParseQuery, Reveal, Speak
from orchestration.pipeline import PipelineResolution, run_pipeline


@dataclass(frozen=True)
class ControllerDeps:
    index_folder: IndexFolder
    extract: Extract
    parse_query: ParseQuery
    match: Match
    reveal: Reveal
    speak: Speak
    voice_enabled: bool = True
    language_mode: str = "auto"


class _PipelineWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        *,
        root: str,
        query: str,
        deps: ControllerDeps,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._root = root
        self._query = query
        self._deps = deps

    @Slot()
    def run(self) -> None:
        try:
            resolution = run_pipeline(
                root=self._root,
                query=self._query,
                index_folder=self._deps.index_folder,
                extract=self._deps.extract,
                parse_query=self._deps.parse_query,
                match=self._deps.match,
            )
            self.finished.emit(resolution)
        except Exception as exc:  # noqa: BLE001 — surface to UI as error state
            self.failed.emit(str(exc))


class ClickyController(QObject):
    """Owns query lifecycle and Qt signals for the shell."""

    state_changed = Signal(str)
    result_ready = Signal(object)  # PipelineResolution
    error_occurred = Signal(str)
    segment_lit = Signal(str, int)  # segment name, index
    reveal_triggered = Signal(bool)
    speak_triggered = Signal(bool)

    def __init__(self, deps: ControllerDeps, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._deps = deps
        self._state = "idle"
        self._thread: QThread | None = None
        self._worker: _PipelineWorker | None = None
        self._pending: PipelineResolution | None = None

    @property
    def state(self) -> str:
        return self._state

    def _set_state(self, state: str) -> None:
        self._state = state
        self.state_changed.emit(state)

    def submit(self, root: str, query: str) -> bool:
        """Start a query. Returns False if a query is already active."""
        if self._state not in {"idle", "result", "error"}:
            return False
        text = query.strip()
        if not text:
            self.error_occurred.emit("Query is empty")
            self._set_state("error")
            return False

        self._set_state("thinking")
        thread = QThread(self)
        worker = _PipelineWorker(root=root, query=text, deps=self._deps)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_pipeline_finished)
        worker.failed.connect(self._on_pipeline_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_thread)
        self._thread = thread
        self._worker = worker
        thread.start()
        return True

    @Slot()
    def _clear_thread(self) -> None:
        self._thread = None
        self._worker = None

    @Slot(object)
    def _on_pipeline_finished(self, resolution: object) -> None:
        assert isinstance(resolution, PipelineResolution)
        self._pending = resolution
        self._set_state("revealing")
        self._run_reveal_sequence(resolution)

    @Slot(str)
    def _on_pipeline_failed(self, message: str) -> None:
        self.error_occurred.emit(message)
        self._set_state("error")

    def _resolve_language_mode(self, language_mix: str) -> str:
        mode = self._deps.language_mode
        if mode == "auto":
            mix = language_mix.lower()
            if mix in {"en", "tl", "taglish"}:
                return mix
            return "en"
        return mode

    def _run_reveal_sequence(self, resolution: PipelineResolution) -> None:
        segments = resolution.animation["segments"]
        for index, segment in enumerate(segments):
            self.segment_lit.emit(segment, index)

        ok = bool(self._deps.reveal(resolution.path))
        self.reveal_triggered.emit(ok)
        if not ok:
            self.error_occurred.emit("Reveal failed")
            self._set_state("error")
            return

        speak_ok = True
        if self._deps.voice_enabled:
            from pathlib import PureWindowsPath

            filename = PureWindowsPath(resolution.path).name
            lang = self._resolve_language_mode(resolution.language_mix)
            speak_ok = bool(self._deps.speak(filename, lang))
        self.speak_triggered.emit(speak_ok)
        # Voice failure is visual-only success
        self.result_ready.emit(resolution)
        self._set_state("result")


def map_language_mode(language_mode: str, language_mix: str) -> str:
    """Pure helper for tests: auto mirrors NLU language_mix."""
    if language_mode == "auto":
        mix = language_mix.lower()
        return mix if mix in {"en", "tl", "taglish"} else "en"
    return language_mode
