"""Resolve OpenAI credentials: pasted config key -> env -> Codex CLI."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "voice" / "config.local.json"
DEFAULT_CODEX = Path.home() / ".codex" / "auth.json"


@dataclass
class Credentials:
    api_key: str | None
    source: str  # "config" | "env" | "codex" | "none"


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _clean(value) -> str:
    """Stringify a JSON value, treating null / "none" / "null" as empty."""
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in ("none", "null") else text


def _codex_key(path: Path) -> str | None:
    # ponytail: best-effort parse of ~/.codex/auth.json; format not a stable contract.
    # Only accept a real API key (sk-...). A ChatGPT-subscription OAuth access_token
    # does NOT authenticate the standard OpenAI API, so we don't return it.
    data = _read_json(path)
    for key in ("OPENAI_API_KEY", "openai_api_key", "api_key"):
        val = _clean(data.get(key))
        if val.startswith("sk-"):
            return val
    return None


def resolve_openai(
    environ: dict | None = None,
    config_path: Path | None = None,
    codex_path: Path | None = None,
) -> Credentials:
    env = environ if environ is not None else os.environ
    cfg = config_path if config_path is not None else DEFAULT_CONFIG
    cdx = codex_path if codex_path is not None else DEFAULT_CODEX

    cfg_key = _clean(_read_json(cfg).get("openai_api_key")) if cfg.is_file() else ""
    if cfg_key:
        return Credentials(cfg_key, "config")

    env_key = _clean(env.get("OPENAI_API_KEY"))
    if env_key:
        return Credentials(env_key, "env")

    if cdx.is_file():
        codex = _codex_key(cdx)
        if codex:
            return Credentials(codex, "codex")

    return Credentials(None, "none")
