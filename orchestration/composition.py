"""Wire demo stubs (or later live components) for the orchestration shell."""

from __future__ import annotations

from dataclasses import dataclass

from orchestration.demo_stubs import DemoStubs


@dataclass
class AppBundle:
    """Minimal composition root for Task 2 — stubs only, no pipeline yet."""

    stubs: DemoStubs | None
    demo_stubs: bool


def build_app(*, demo_stubs: bool = False) -> AppBundle:
    """Build the orchestration composition root.

    When *demo_stubs* is True, attach fixture-backed stubs for all six entry points.
    Live teammate packages stay NotImplemented until their owners land.
    """
    stubs = DemoStubs() if demo_stubs else None
    return AppBundle(stubs=stubs, demo_stubs=demo_stubs)
