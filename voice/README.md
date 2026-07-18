# Voice Layer (Cody speaks)

| Field | Value |
|-------|-------|
| **Owner** | Person 6 (also owns `reveal/`) |
| **Purpose** | Speak a short templated confirmation via local [OpenVoice](https://github.com/myshell-ai/OpenVoice) (MeloTTS + optional tone clone). |
| **Owns** | `voice/` package, `speak` entry point, and `VoiceConfig` usage. |
| **Does not own** | Open-ended translation of Matcher `reasoning`, speech-to-text input, reveal OS select. |
| **Frozen I/O** | `speak(filename: str, language_mode: str) -> bool` / `SpeechRequest` per `spec.md` §6.6. |
| **Test command** | `python -m pytest voice/tests -q` |
| **Branch** | `feature/voice` |
| **Done condition** | Fixture filename speaks EN and TL templates; disabled / engine failure falls back cleanly. |
| **Integration handoff** | Orchestration imports `voice.speak.speak`. |
| **Seat plan** | [`tasks/plan.md`](tasks/plan.md) / [`tasks/todo.md`](tasks/todo.md) |
| **Glossary** | [`CONTEXT.md`](CONTEXT.md) |

## Why OpenVoice (not ElevenLabs)

Local, no API key. Engine stack follows the official OpenVoice V2 path: **MeloTTS** synthesizes speech; **OpenVoice** optionally applies tone-color cloning from a reference wav ([OpenVoice repo](https://github.com/myshell-ai/OpenVoice)).

**Tagalog note:** OpenVoice/MeloTTS natively cover EN/ES/FR/ZH/JP/KR — not Tagalog. TL/taglish templates still speak the Tagalog *text* through the English Melo speaker (ear-check quality may vary).

## Config

1. Copy [`config.example.json`](config.example.json) → `config.local.json` (gitignored).
2. Default example sets `"tone_convert": false` so MeloTTS alone works after install (fastest demo path).
3. For full OpenVoice cloning, set `"tone_convert": true`, download checkpoints, and point `reference_wav` at a short clean clip.

JSON `language_mode` is kept for shape compatibility but **ignored by `speak`**. Call with `en` / `tl` / `taglish` only.

Missing `config.local.json` or `enabled: false` → `true` (planned no-op). Engine/install/checkpoint failures → `false`. Soft-fails log at WARNING.

## OpenVoice setup (demo machine)

```powershell
pip install git+https://github.com/myshell-ai/OpenVoice.git
pip install git+https://github.com/myshell-ai/MeloTTS.git
python -m unidic download
```

Optional tone convert (V2 checkpoints):

1. Download [checkpoints_v2_0417.zip](https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip)
2. Extract to `voice/checkpoints_v2/`
3. Put a reference wav at `voice/refs/speaker.wav`
4. Set `"tone_convert": true` in `config.local.json`

## Templates

- EN: `Found it — {filename}.`
- TL / taglish: `Nakita ko na — {filename}.`

## Smoke

```
python voice/scripts/smoke_tl.py
```
