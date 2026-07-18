# Clicky pointer overlay final design QA

Reviewed once on `rohart-branch` at `2026-07-18T15:15:31+08:00` against the Clicky design plan, `design/README.md`, `spec.md` §6.7–6.8, and `openspec/specs/overlay-stretch/spec.md`. The two reported blockers were remediated and the affected assets were validated again. Files checked: locked SVGs, PNG fallbacks, hotspot metadata, prototype, brand brief and board, and handoff.

## Checklist

1. **Tip clarity at 64px — PASS.** The locked dart has one geometric tip at `(12,22)`. Its 2-unit outline renders at about 5.3px in a 64px box without obscuring the point. `arrow-64.png` is 64×64 RGBA, has visible bounds `(16,3)–(49,62)`, and has an opaque pixel at the scaled logical tip `(32,59)`.

2. **Light/dark contrast — PASS.** Charcoal `#0F172A` gives 17.85:1 against `#FFFFFF`, and paper `#F8FAFC` gives 15.93:1 against `#1E1E1E`. `arrow.svg`, `ring.svg`, and `hotspot.json` document theme selection, while PNG fallbacks are explicitly light-theme only. The dark prototype uses the documented paper outline and signal-blue-light tip facet, so the pointer remains legible on its `#1E1E1E` stage.

3. **Exact icon-center landing and hotspot sanity — PASS.** The arrow path and `hotspot.json` agree on `(12,22)` inside the `0 0 24 24` viewBox. The prototype correctly computes the target box center and subtracts the 36px render's scaled tip `(18,33)`, so the arrow lands exactly at icon center. The metadata now separately declares the ring center at `(12,12)`, normalized `(0.5,0.5)`, and the handoff directs integrators to select the entry for the asset being rendered.

4. **No continuous mouse-follow — PASS.** The prototype uses one fixed trajectory, holds at the endpoint, and registers no pointer-motion listener. Replay requires a button click.

5. **§6.7 primacy and optional §6.8 timing — PASS.** The README, brief, prototype copy, and handoff keep Troy's breadcrumb as the sole demo-critical animation. They permit the overlay only after `reveal(path)` returns success and preserve the 2:00 drop condition.

6. **Silent failure — PASS.** The handoff requires lookup failure or timeout to no-op without raising, blocking the UI, or retrying indefinitely, matching the overlay OpenSpec.

7. **Anti-generic and no purple glow — PASS.** The assets and brand board stay in the signal-blue family. There is no purple or violet, stock cursor pack, pill mascot, shimmer, or particle effect.

8. **No orchestration edits — PASS.** Working-tree status contains only `design/` paths. Both the working-tree check and `origin/main...HEAD` comparison show no path under `orchestration/`. Design docs discuss the boundary but do not authorize an orchestration edit.

## Status: LOCKED

The pointer pack is approved for the optional §6.8 prototype and handoff. This approval does not authorize orchestration changes or make the overlay demo-critical.
