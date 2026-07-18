"""One-shot OpenAI Responses API call via stdlib HTTP."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from matcher.config import ModelConfig


class ModelCallError(RuntimeError):
    """Responses API call failed."""


def call_responses(config: ModelConfig, prompt: str) -> str:
    url = f"{config['base_url']}/responses"
    body: dict[str, Any] = {
        "model": config["model"],
        "input": prompt,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ModelCallError(f"Responses API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ModelCallError(f"Responses API transport error: {exc}") from exc

    text = _extract_output_text(payload)
    if not text:
        raise ModelCallError("Responses API returned empty output text")
    return text


def _extract_output_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return payload["output_text"]
    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        for part in item.get("content") or []:
            if not isinstance(part, dict):
                continue
            if part.get("type") in {"output_text", "text"} and isinstance(
                part.get("text"), str
            ):
                chunks.append(part["text"])
    return "\n".join(chunks).strip()
