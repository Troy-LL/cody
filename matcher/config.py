"""Load ModelConfig from a gitignored local file (§8.1)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TypedDict

CONFIG_PATH = Path(
    os.environ.get("MATCHER_CONFIG", Path(__file__).resolve().parent / "local_model.json")
)


class ModelConfig(TypedDict):
    provider: str
    base_url: str
    api_key: str
    model: str


class ConfigError(RuntimeError):
    """Raised when ModelConfig is missing or invalid."""


def load_config(path: Path | None = None) -> ModelConfig:
    cfg_path = path or CONFIG_PATH
    if not cfg_path.is_file():
        raise ConfigError(
            f"ModelConfig not found at {cfg_path}. "
            "Copy matcher/local_model.example.json to matcher/local_model.json "
            "and paste your API key (never commit the key file)."
        )
    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("ModelConfig must be a JSON object")
    required = ("provider", "base_url", "api_key", "model")
    missing = [k for k in required if not raw.get(k)]
    if missing:
        raise ConfigError(f"ModelConfig missing fields: {', '.join(missing)}")
    return {
        "provider": str(raw["provider"]),
        "base_url": str(raw["base_url"]).rstrip("/"),
        "api_key": str(raw["api_key"]),
        "model": str(raw["model"]),
    }
