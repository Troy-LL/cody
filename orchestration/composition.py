"""Composition root: demo stubs or live public entry points."""

from __future__ import annotations

from dataclasses import dataclass

from orchestration.controller import CodyController, ControllerDeps
from orchestration.demo_stubs import DemoStubs


@dataclass
class AppBundle:
    """Wired controller + optional stubs for recovery path."""

    controller: CodyController
    stubs: DemoStubs | None
    demo_stubs: bool


def _live_deps(*, voice_enabled: bool = True) -> ControllerDeps:
    """Import only the six public entry points (no component internals)."""
    from indexer.index_folder import index_folder
    from extractor.extract import extract
    from nlu.parse_query import parse_query
    from matcher.match import match
    from reveal.reveal import reveal
    from voice.speak import speak

    return ControllerDeps(
        index_folder=index_folder,
        extract=extract,
        parse_query=parse_query,
        match=match,
        reveal=reveal,
        speak=speak,
        voice_enabled=voice_enabled,
        language_mode="auto",
    )


def build_app(
    *,
    demo_stubs: bool = False,
    voice_enabled: bool = True,
) -> AppBundle:
    """Build orchestration composition root.

    ``--demo-stubs`` keeps the recovery path when teammate packages still raise
    NotImplementedError.
    """
    stubs: DemoStubs | None = None
    if demo_stubs:
        stubs = DemoStubs()
        deps = ControllerDeps(
            index_folder=stubs.index_folder,
            extract=stubs.extract,
            parse_query=stubs.parse_query,
            match=stubs.match,
            reveal=stubs.reveal,
            speak=stubs.speak,
            voice_enabled=voice_enabled,
            language_mode="auto",
        )
    else:
        deps = _live_deps(voice_enabled=voice_enabled)

    controller = CodyController(deps)
    return AppBundle(controller=controller, stubs=stubs, demo_stubs=demo_stubs)
