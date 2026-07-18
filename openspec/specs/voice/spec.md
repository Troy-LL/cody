## Purpose

The voice layer supports **voice-controlled** Cody sessions: listen to the user, speak AI replies aloud via local OpenVoice/MeloTTS, and never block visual reveal/cursor when soft-failing.

## Requirements

### Requirement: SpeechRequest mapping
`speak` SHALL accept filename and language mode consistent with `SpeechRequest` in `spec.md` §6.6 and MUST play a templated phrase (not a live translation of matcher reasoning).

#### Scenario: English confirmation
- **GIVEN** filename `receipt_lazada.pdf` and `language_mode` `en`
- **WHEN** `speak` runs with voice enabled
- **THEN** audio MUST play a short English template including the filename and the function MUST return `true`

### Requirement: Free-form AI reply
`speak_text` SHALL speak arbitrary confirmation/acknowledgment text for voice-controlled turns.

#### Scenario: Not found reply
- **GIVEN** a transcript that resolves to no file
- **WHEN** the voice session handles it
- **THEN** Cody MUST speak a short not-found reply via `speak_text`

### Requirement: Listen (STT)
`listen` SHALL return a transcript string when SpeechRecognition + microphone are available, and MUST raise a documented unavailable error (not crash the OS) when the STT stack is missing.

#### Scenario: Missing SpeechRecognition
- **GIVEN** SpeechRecognition is not installed
- **WHEN** `listen` is called
- **THEN** it MUST raise `ListenUnavailable` (session soft-handles)

### Requirement: Non-blocking fallback
If voice is disabled or TTS fails, voice MUST soft-fail without preventing reveal/cursor success.

#### Scenario: OpenVoice unavailable
- **GIVEN** MeloTTS/OpenVoice is not installed
- **WHEN** `speak` / `speak_text` runs while enabled
- **THEN** the function MUST return `false` and MUST NOT raise to the caller
