# Cody — Person 6 glossary

Product language for the Reveal + Voice seat. Implementation details live in ADRs and code, not here.

## Language

**Reveal**:
The OS-native action that opens the containing folder and selects the resolved file path. Owned by Person 6 (`reveal/`).
_Avoid_: Baseline animation, pointing overlay, in-app breadcrumb

**Baseline Animation**:
Cody's in-app path breadcrumb that lights up before/as Reveal fires. Owned by orchestration (`spec.md` §6.7), not by Person 6.
_Avoid_: Reveal, overlay

**Pointing Overlay**:
Optional stretch highlight drawn on the real Explorer icon via accessibility APIs (`spec.md` §6.8). Not owned by Person 6.
_Avoid_: Reveal, baseline animation

**SpeechRequest**:
The voice input contract: filename + language mode (`en` / `tl` / `taglish` after orchestration resolves `auto`).
_Avoid_: Free-form prompt, full matcher reasoning string

**VoiceConfig**:
Local settings for whether voice is on, provider/base URL, model id, and per-language voice routing. Non-secrets live in gitignored JSON; the API key comes from the environment only. The JSON `language_mode` field is orchestration's concern — `speak` ignores it.
_Avoid_: Hardcoded API keys, provider secrets in source or committed JSON

**Speech soft-fail**:
Voice must never block visual Reveal. Intentionally disabled (or missing config) is a planned no-op; a failed speak attempt is a soft failure that still leaves the demo visually successful.
_Avoid_: Treating voice as demo-blocking
