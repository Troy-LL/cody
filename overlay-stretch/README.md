# Pointing Overlay (stretch)

| Field | Value |
|-------|-------|
| **Owner** | Unassigned (optional seat) |
| **Purpose** | Draw an always-on-top highlight on the real Explorer file icon via accessibility APIs. |
| **Owns** | `overlay-stretch/` package and overlay entry behavior (`spec.md` §6.8). |
| **Does not own** | Baseline in-app animation (§6.7), Reveal Layer OS select, matcher/NLU. |
| **Frozen I/O** | `overlay(path: str) -> bool` / `OverlayRequest` per `spec.md` §6.8. |
| **Stub requirement** | Optional; if picked up, stub by 0:30. Fail silently if coordinates unavailable. |
| **Test command** | `python -m pytest overlay-stretch/tests -q` (owner adds tests). |
| **Branch** | `feature/overlay-stretch` |
| **Done condition** | Overlay lands on the icon by the 2:00 cutoff — otherwise drop with zero demo impact. |
| **Integration handoff** | Orchestration may call only after reveal succeeds. Never block demo readiness. |
