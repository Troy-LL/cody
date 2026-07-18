"""Structural checks for .codex/rules/team-sdd-memory.mdc."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RULE_PATH = REPO_ROOT / ".codex" / "rules" / "team-sdd-memory.mdc"

REQUIRED_PHRASES = [
    "alwaysApply: true",
    "root README",
    "component README",
    "openspec/specs",
    "No cross-edit",
    "Contract discipline",
    "TDD",
    "SDD review",
    "Grok 4.5",
    "SPEED MODE",
    "directly on `main`",
    "Do not delete remote branches",
    "granular commits",
    "Merge conflicts",
    "Evolution protocol",
    "source+date",
    "max 10 learned",
    "## Learned",
]


def _rule_text() -> str:
    assert RULE_PATH.is_file(), f"missing team rule at {RULE_PATH}"
    return RULE_PATH.read_text(encoding="utf-8")


def test_team_rule_always_apply_true() -> None:
    text = _rule_text()
    assert text.startswith("---\n")
    assert "alwaysApply: true" in text.split("---", 2)[1]


def test_team_rule_under_fifty_lines() -> None:
    lines = _rule_text().splitlines()
    assert len(lines) < 50, f"team rule has {len(lines)} lines; must be < 50"


def test_team_rule_required_phrases() -> None:
    text = _rule_text()
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in text]
    assert not missing, f"missing required phrases: {missing}"
