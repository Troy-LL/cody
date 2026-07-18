# Orchestration / UI shell

| Field | Value |
|-------|-------|
| **Owner** | Person 1 — Troy |
| **Purpose** | Wire components end-to-end; own input/thinking/result UI and baseline reveal animation. |
| **Owns** | `orchestration/` package, pipeline glue, and `RevealAnimation` (`spec.md` §6.7). |
| **Does not own** | Internals of indexer/extractor/nlu/matcher/reveal/voice; stretch overlay. |
| **Frozen I/O** | Consumes §6.1–6.6 shapes; builds §6.7 animation segments from matched path + scan root. |
| **Stub requirement** | Teammate folders stay `NotImplemented`; use `orchestration/demo_stubs.py` with `--demo-stubs`. |
| **Test command** | `python -m pytest tests/orchestration tests/contracts -q` |
| **Branch** | `feature/orchestration` |
| **Done condition** | Full pipeline runs on the demo folder with baseline animation and voice call. |
| **Integration handoff** | **Only** this package may import other components. Prefer stub fixtures before live deps. |
