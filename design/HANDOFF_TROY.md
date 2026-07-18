# Handoff: optional §6.8 pointer overlay assets

This is a docs-only handoff. Nothing here has been wired into `orchestration/`, and nothing in `design/` should be treated as a dependency of the demo. Read this before anyone attempts the §6.8 stretch overlay.

## What exists

- `design/pointer/arrow.svg`, `design/pointer/ring.svg`, `design/pointer/hotspot.json`: locked, QA-approved pointer assets (signal blue) sized for a 24x24 viewBox, meant to render at small sizes (target ~64px) next to or on top of a real file icon. The metadata keeps the arrow tip at normalized `(0.5, 0.9167)` and the ring center at `(0.5, 0.5)`; select the entry for the asset being rendered.
- `design/brand/palette.json`, `design/brand/brief.md`: the palette and rationale behind them.
- `design/prototype/index.html`: a throwaway, standalone sketch (no dependencies) that shows the arrow animating from a fixed off-screen point onto a fake icon box, so the "land on icon" motion can be eyeballed before anyone writes real overlay code. Open it directly in a browser; it imports nothing from this repo's Python packages.

## What does not exist

- No `overlay-stretch/` package, no Python module, no PySide/Qt widget. This handoff describes *how* such a package should consume these assets if someone builds it; it does not build it.
- No changes anywhere in `orchestration/`. `orchestration/composition.py` and `orchestration/controller.py` are untouched by this design pass.

## If §6.8 is attempted (non-blocking, optional)

Per `spec.md` §6.7-6.8 and §11, and `orchestration/README.md`'s call order:

1. Match → §6.7 breadcrumb animation (`QTimer`-driven `segment_lit` loop in `orchestration/controller.py`) → `reveal(path)`.
2. Only **after** `reveal(path)` returns success does orchestration optionally call into an `overlay-stretch` component with the resolved path.
3. `overlay-stretch` (if it exists) locates the file's on-screen icon, then renders `design/pointer/arrow.svg` or `ring.svg` at that location using that asset's tip or center coordinates in `design/pointer/hotspot.json`. Package or copy the SVG as a data file; do not hand-transcribe its path data.
4. If icon lookup fails, times out, or the platform doesn't support it: no-op silently. Never raise into the main result flow, never block the UI, never retry indefinitely. This mirrors how voice failures are handled: a soft, visual-only failure with no crash.
5. `overlay-stretch` is a sole-consumer of these assets. It does not get to redefine the palette, tip point, or metaphor; those are locked pending a fresh QA pass if requirements change.

## What this handoff does not authorize

- Editing `orchestration/composition.py` to add an import. Only `orchestration/` may decide whether and when to call `overlay-stretch`; this doc does not pre-approve that decision, it only describes the contract if it's made.
- Replacing or restyling the §6.7 breadcrumb with these assets.
- Making the overlay call before `reveal()` succeeds, or treating overlay success as required for the demo to pass criterion 6. Baseline breadcrumb + reveal alone already satisfies it.
- Continuous mouse-follow behavior anywhere. The asset animates to one fixed, known coordinate and stops.

## Drop condition

If `overlay-stretch` is not stable well before the demo cutoff (spec calls out 2:00 as the point past which stretch work must not risk the baseline), drop it. The baseline §6.7 + reveal path has zero dependency on anything in this folder.
