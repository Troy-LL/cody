# VoiceConfig hybrid loading

Person 6 loads non-secret `VoiceConfig` fields from `voice/config.local.json` (gitignored; example at `voice/config.example.json`). The ElevenLabs API key comes from the `ELEVENLABS_API_KEY` environment variable only. Secrets stay out of files that are easy to commit; the routing table stays editable without code changes.
