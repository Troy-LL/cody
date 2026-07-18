# Voice Layer (Cody speaks)

| Field | Value |
|-------|-------|
| **Owner** | Person 6 (also owns `reveal/`) |
| **Purpose** | Speak a short templated confirmation via ElevenLabs for the resolved filename. |
| **Owns** | `voice/` package, `speak` entry point, and `VoiceConfig` usage (`spec.md` §8.2). |
| **Does not own** | Open-ended translation of Matcher `reasoning`, speech-to-text input, reveal OS select. |
| **Frozen I/O** | `speak(filename: str, language_mode: str) -> bool` / `SpeechRequest` per `spec.md` §6.6. |
| **Stub requirement** | Stub raises `NotImplementedError` until fixture-shaped return lands (Task 2 / 0:30). |
| **Test command** | `python -m pytest voice/tests -q` (owner adds tests). |
| **Branch** | `feature/voice` |
| **Done condition** | Fixture filename speaks EN and TL templates; `enabled: false` / API failure falls back cleanly. |
| **Integration handoff** | Orchestration imports `voice.speak.speak`. Smoke-test Tagalog quality in first 30 minutes. |
