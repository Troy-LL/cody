import json
from pathlib import Path
from overlay.auth import resolve_openai


def test_config_key_wins(tmp_path: Path):
    cfg = tmp_path / "config.local.json"
    cfg.write_text(json.dumps({"openai_api_key": "sk-cfg"}), encoding="utf-8")
    creds = resolve_openai(environ={"OPENAI_API_KEY": "sk-env"}, config_path=cfg, codex_path=tmp_path / "none.json")
    assert creds.api_key == "sk-cfg"
    assert creds.source == "config"


def test_env_when_no_config(tmp_path: Path):
    creds = resolve_openai(environ={"OPENAI_API_KEY": "sk-env"}, config_path=tmp_path / "none.json", codex_path=tmp_path / "none.json")
    assert creds.api_key == "sk-env"
    assert creds.source == "env"


def test_codex_fallback(tmp_path: Path):
    cdx = tmp_path / "auth.json"
    cdx.write_text(json.dumps({"OPENAI_API_KEY": "sk-codex"}), encoding="utf-8")
    creds = resolve_openai(environ={}, config_path=tmp_path / "none.json", codex_path=cdx)
    assert creds.api_key == "sk-codex"
    assert creds.source == "codex"


def test_none_found(tmp_path: Path):
    creds = resolve_openai(environ={}, config_path=tmp_path / "none.json", codex_path=tmp_path / "none.json")
    assert creds.api_key is None
    assert creds.source == "none"


def test_codex_null_key_is_not_used(tmp_path: Path):
    # ChatGPT-subscription login: OPENAI_API_KEY is JSON null, only OAuth tokens present.
    cdx = tmp_path / "auth.json"
    cdx.write_text(
        json.dumps({"OPENAI_API_KEY": None, "tokens": {"access_token": "eyJhbGci"}}),
        encoding="utf-8",
    )
    creds = resolve_openai(environ={}, config_path=tmp_path / "none.json", codex_path=cdx)
    assert creds.api_key is None
    assert creds.source == "none"


def test_codex_non_sk_value_rejected(tmp_path: Path):
    cdx = tmp_path / "auth.json"
    cdx.write_text(json.dumps({"api_key": "not-a-real-key"}), encoding="utf-8")
    creds = resolve_openai(environ={}, config_path=tmp_path / "none.json", codex_path=cdx)
    assert creds.source == "none"
