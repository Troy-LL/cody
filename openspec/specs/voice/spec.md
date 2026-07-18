## Purpose

The voice layer speaks a short templated confirmation for the resolved filename through ElevenLabs, routed by language mode, and never blocks the visual reveal when disabled or failing.

## Requirements

### Requirement: SpeechRequest mapping
`speak` SHALL accept filename and language mode consistent with `SpeechRequest` in `spec.md` §6.6 and MUST play a templated phrase (not a live translation of matcher reasoning).

#### Scenario: English confirmation
- **GIVEN** filename `receipt_lazada.pdf` and `language_mode` `en`
- **WHEN** `speak` runs with voice enabled
- **THEN** audio MUST play a short English template including the filename and the function MUST return `true`

### Requirement: Language routing
Voice SHALL resolve `language_mode` through `VoiceConfig.routing` (`spec.md` §8.2). When mode is `auto`, it MUST mirror `QueryIntent.language_mix` supplied by orchestration.

#### Scenario: Tagalog template
- **GIVEN** `language_mode` `tl` and a configured Tagalog voice id
- **WHEN** `speak` runs
- **THEN** the Tagalog template MUST be used with the routed `voice_id`

### Requirement: Non-blocking fallback
If `enabled` is false or the TTS call fails, voice MUST return `false` (or no-op success policy documented by owner) without preventing visual reveal success.

#### Scenario: Missing API key
- **GIVEN** voice config with no usable API key
- **WHEN** orchestration still reveals a file
- **THEN** speak MUST fail soft and the demo MUST continue visually
