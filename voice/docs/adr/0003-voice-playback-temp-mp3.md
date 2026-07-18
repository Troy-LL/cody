# Voice playback via temp MP3

`speak` writes ElevenLabs audio bytes to a temporary `.mp3` file and plays it with `os.startfile`. No new playback dependencies. The temp file is left on disk after start (avoid player file-lock races). Playback/start failures soft-fail as `false`.
