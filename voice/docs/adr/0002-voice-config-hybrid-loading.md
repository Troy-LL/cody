# VoiceConfig local JSON loading

Person 6 loads `VoiceConfig` from `voice/config.local.json` (gitignored; example at `voice/config.example.json`). OpenVoice is local — there is no API key env var. Optional `OPENVOICE_DEVICE` can override `device` when the JSON omits it.
