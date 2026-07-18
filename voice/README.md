# Voice Layer — voice-controlled Cody

| Field | Value |
|-------|-------|
| **Owner** | Person 6 (also owns `reveal/`, `overlay/`) |
| **Purpose** | Pure voice control + AI spoken replies (OpenVoice) for the redirected Clicky/Cody scope. |
| **Owns** | `listen`, `speak` / `speak_text`, `session` voice loop |
| **Frozen I/O** | `speak(filename, language_mode) -> bool`; additive: `listen()`, `speak_text()`, `run_voice_session()` |
| **Test command** | `python -m pytest voice/tests -q` |
| **Branch** | `feature/voice` |

## New scope features

1. **Purely voice controlled** — `listen()` (SpeechRecognition) → session resolves a file under `--root`
2. **AI voice responds** — `speak_text(...)` acknowledgments + templated `speak(filename, ...)` via local [OpenVoice](https://github.com/myshell-ai/OpenVoice)/MeloTTS
3. **AI cursor on the OS** — session calls `overlay.start_follow` / `point_at` after `reveal`

## Run voice session

```powershell
pip install SpeechRecognition pyaudio
pip install git+https://github.com/myshell-ai/OpenVoice.git
pip install git+https://github.com/myshell-ai/MeloTTS.git
python -m unidic download
Copy-Item voice\config.example.json voice\config.local.json
python -m voice --root $env:USERPROFILE\Desktop --lang en --rounds 1
```

Say e.g. *"find receipt_lazada.pdf"* (file must exist in that folder).

## Config

See `config.example.json` (`provider: openvoice`, `tone_convert: false` for fastest smoke).
