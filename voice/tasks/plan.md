# Person 6 seat plan — Reveal + Voice

See the Cursor plan “Person 6 Reveal Voice” and grilled decision log in ADRs under `voice/docs/adr/` and `reveal/docs/adr/`.

## Build order

1. Docs + ignore + example config (this folder)
2. Voice stub + config loader + Tagalog smoke script
3. Reveal stub + TDD + Explorer select (`feature/reveal`)
4. Full voice TDD implementation
5. Manual checklist + two PRs

## Commands

```
python -m pytest reveal/tests -q
python -m pytest voice/tests -q
python voice/scripts/smoke_tl.py
```
