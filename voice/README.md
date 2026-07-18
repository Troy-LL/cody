# Voice Layer (Cody speaks)

| Field | Value |
|-------|-------|
| **Owner** | Person 6 (also owns `reveal/`) |
| **Purpose** | Speak a short templated confirmation via ElevenLabs for the resolved filename. |
| **Owns** | `voice/` package, `speak` entry point, and `VoiceConfig` usage (`spec.md` §8.2). |
| **Does not own** | Open-ended translation of Matcher `reasoning`, speech-to-text input, reveal OS select. |
| **Frozen I/O** | `speak(filename: str, language_mode: str) -> bool` / `SpeechRequest` per `spec.md` §6.6. |
| **Stub / contract** | Returns `bool` (stub returns `True` until real TTS lands). |
| **Test command** | `python -m pytest voice/tests -q` |
| **Branch** | `feature/voice` |
| **Done condition** | Fixture filename speaks EN and TL templates; `enabled: false` / API failure falls back cleanly. |
| **Integration handoff** | Orchestration imports `voice.speak.speak`. Smoke-test Tagalog quality in first 30 minutes. |
| **Seat plan** | [`tasks/plan.md`](tasks/plan.md) / [`tasks/todo.md`](tasks/todo.md) |
| **Glossary** | [`CONTEXT.md`](CONTEXT.md) |

## Config

1. Copy [`config.example.json`](config.example.json) → `config.local.json` (gitignored via [`.gitignore`](.gitignore)).
2. Set real `voice_id` values (placeholders soft-fail).
3. Export `ELEVENLABS_API_KEY` (never commit keys).

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
