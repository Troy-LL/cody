# Voice soft-fail return policy

`speak` returns `true` when voice is intentionally disabled (`enabled: false`) or `config.local.json` is missing — that is a planned no-op. It returns `false` when voice was supposed to speak and could not (malformed config, missing key, unsupported provider, bad language mode, placeholder voice_id, TTS/API/timeout/playback failure). Reveal must never depend on this boolean.
