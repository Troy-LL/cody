# Voice playback via in-process PCM

`speak` requests ElevenLabs `pcm_22050` (s16le mono) and plays it with `sounddevice` / `numpy` in-process. No temp `.mp3` and no `os.startfile`, so the OS media player does not pop up. Playback failures soft-fail as `false`.

Requires `sounddevice` and `numpy` (overlay optional deps).
