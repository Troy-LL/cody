# Voice playback via OpenVoice WAV + startfile

`speak` synthesizes a WAV through OpenVoice/MeloTTS and plays it with `os.startfile`. Temp output is left on disk after start (avoid player file-lock races). Playback/synth failures soft-fail as `false`.
