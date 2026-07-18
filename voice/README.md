# Voice Layer (Cody speaks)

| Field | Value |
|-------|-------|
| **Owner** | Person 6 (also owns `reveal/`) |
| **Purpose** | Speak a short templated confirmation via ElevenLabs for the resolved filename. |
| **Owns** | `voice/` package, `speak` entry point, and `VoiceConfig` usage (`spec.md` §8.2). |
| **Does not own** | Open-ended translation of Matcher `reasoning`, speech-to-text input, reveal OS select. |
| **Frozen I/O** | `speak(filename: str, language_mode: str) -> bool` / `SpeechRequest` per `spec.md` §6.6. |
| **Contract** | Returns `bool` — soft-fail never blocks reveal. |
| **Test command** | `python -m pytest voice/tests -q` |
| **Branch** | `feature/voice` |
| **Done condition** | Fixture filename speaks EN and TL templates; `enabled: false` / API failure falls back cleanly. |
| **Integration handoff** | Orchestration imports `voice.speak.speak`. Smoke-test Tagalog quality early. |
| **Seat plan** | [`tasks/plan.md`](tasks/plan.md) |
| **Glossary** | [`CONTEXT.md`](CONTEXT.md) |

## Config

1. Copy [`config.example.json`](config.example.json) to `config.local.json` (gitignored via [`.gitignore`](.gitignore)).
2. Set real `voice_id` values (placeholders soft-fail).
3. Set `ELEVENLABS_API_KEY` in the environment, or put `api_key` in `config.local.json` (local demo only — never commit).

Overlay pointing (`speak_point`) uses **ElevenLabs only** (no Windows SAPI fallback).

The JSON `language_mode` field is kept for §8.2 shape but **ignored by `speak`** — orchestration owns `auto` resolution. Call `speak` with `en`, `tl`, or `taglish` only (`auto` soft-fails).

Missing `config.local.json` or `enabled: false` → `speak` returns `true` (planned no-op). Malformed config / missing key / TTS failure → `false`. Soft-fails log at WARNING.

## Templates

- EN: `Found it — {filename}.`
- TL / taglish: `Nakita ko na — {filename}.`

## Tagalog smoke

```
python voice/scripts/smoke_tl.py
```

Ear-check once; if unclear, swap model/voice once and re-run.
