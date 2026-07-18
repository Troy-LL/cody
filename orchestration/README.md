# Orchestration / UI shell

| Field | Value |
|-------|-------|
| **Owner** | Person 1 — Troy |
| **Purpose** | Wire components end-to-end; own input/thinking/result UI and baseline reveal animation. |
| **Owns** | `orchestration/` + stewardship of `contracts/` and `fixtures/`; UI shell; baseline breadcrumb animation (§6.7). |
| **Does not own** | Real Indexer/Extractor/NLU/Matcher/Reveal/Voice implementations (call their public entry points only). |
| **Frozen I/O** | Consumes §6.1–6.6; builds §6.7 animation. Pipeline: Indexer+NLU concurrent → extract fan-out → Matcher → Reveal+Voice. |
| **Stub requirement** | Teammate folders stay `NotImplemented`; run `python -m orchestration.main --demo-stubs`. |
| **Test command** | `python -m pytest tests/orchestration tests/contracts -q` |
| **Branch** | `feature/orchestration` |
| **Done condition** | Typed query e2e: match + breadcrumb animation + reveal + speak (voice failure = visual-only OK). |
| **Integration handoff** | **Only** this package may import other components. Prefer `--demo-stubs` before live deps. |
