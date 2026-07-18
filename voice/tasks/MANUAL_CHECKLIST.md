# Person 6 manual checklist — voice-controlled + AI cursor

## Voice control + AI reply

- [ ] Install SpeechRecognition + PyAudio; OpenVoice + MeloTTS (see `voice/README.md`)
- [ ] `Copy-Item voice\config.example.json voice\config.local.json`
- [ ] Put a demo file in a folder (e.g. Desktop `receipt_lazada.pdf`)
- [ ] `python -m voice --root $env:USERPROFILE\Desktop --lang en --rounds 1`
- [ ] Say “find receipt_lazada.pdf” — Cody speaks back, Explorer selects, cursor points
- [ ] `enabled: false` → no audio, reveal/cursor still attempted if you call them directly

## AI cursor / reveal

- [ ] Explorer opens with file selected
- [ ] Cursor animates (with or without `uiautomation`)
- [ ] Optional: `pip install uiautomation` for real icon bounds
- [ ] `python -m pytest voice/tests overlay/tests reveal/tests -q` green
