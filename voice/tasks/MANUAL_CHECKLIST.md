# Person 6 manual demo-box checklist

Run on the Windows demo machine. Unit tests do not replace these.

## Reveal (`feature/reveal` — already merged)

- [ ] Existing file path opens Explorer with the file selected
- [ ] Path containing spaces still selects correctly
- [ ] Missing / deleted path returns `false` and does not crash the shell
- [ ] `python -m pytest reveal/tests -q` green

## Voice (`feature/voice` — OpenVoice)

- [ ] Install OpenVoice + MeloTTS per `voice/README.md`
- [ ] Copy `config.example.json` → `config.local.json` (`tone_convert: false` for first smoke)
- [ ] `python voice/scripts/smoke_tl.py` — Tagalog text via EN Melo speaker (ear-check)
- [ ] `speak("receipt_lazada.pdf", "en")` plays English template
- [ ] `enabled: false` → returns `true`, no audio
- [ ] Optional: download checkpoints + set `tone_convert: true` + reference wav
- [ ] `python -m pytest voice/tests -q` green
