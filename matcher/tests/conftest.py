"""Default matcher tests to stub mode so CI needs no API key."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _matcher_stub_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MATCHER_STUB", "1")
