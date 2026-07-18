# ElevenLabs HTTP timeout

The TTS HTTP call uses a 10 second timeout. On timeout (or other HTTP failure), `speak` soft-fails with `false` so orchestration’s UI thread is not stuck after Reveal.
