# OpenVoice local engine replaces ElevenLabs

Person 6 uses the local [OpenVoice](https://github.com/myshell-ai/OpenVoice) stack (MeloTTS base TTS + optional OpenVoice tone-color convert) instead of ElevenLabs. No API key is required. `provider` must be `openvoice`. Missing installs/checkpoints soft-fail as `false`. Tagalog is spoken via Melo EN speakers because TL is not a native Melo/OpenVoice language.
