# Person 6 manual demo-box checklist

Run on the Windows demo machine. Unit tests do not replace these.

## Reveal (`feature/reveal`)

- [ ] Existing file path opens Explorer with the file selected
- [ ] Path containing spaces still selects correctly
- [ ] Missing / deleted path returns `false` and does not crash the shell
- [ ] `python -m pytest reveal/tests -q` green

## Voice (`feature/voice`)

- [ ] Copy `config.example.json` → `config.local.json`, set real voice ids, set `ELEVENLABS_API_KEY`
- [ ] `python voice/scripts/smoke_tl.py` — Tagalog ear-check (swap model/voice once if unclear)
- [ ] `speak("receipt_lazada.pdf", "en")` plays English template
- [ ] `enabled: false` → returns `true`, no audio
- [ ] Bad / missing API key → returns `false`, reveal still works in the app
- [ ] `python -m pytest voice/tests -q` green
