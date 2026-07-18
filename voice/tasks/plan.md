# Person 6 seat plan — Voice

Owned under `voice/`. Reveal lands on `feature/reveal` separately.

## Build order

1. Docs + ignore + example config
2. Voice stub + config loader + Tagalog smoke script
3. Full `speak` implementation + unit tests
4. Manual checklist + PR

## Commands

```
python -m pytest voice/tests -q
python voice/scripts/smoke_tl.py
```
