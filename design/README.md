# Clicky pointer assets

Design assets for Clicky's optional **§6.8 stretch overlay**: an arrow or ring that lands on the real file icon in Explorer after `reveal()` succeeds. This folder never contains, replaces, or restyles Troy's **§6.7 in-app breadcrumb**, which stays the sole demo-critical animation, built entirely inside `orchestration/`.

## Troy's orchestration non-negotiables (why this folder is shaped the way it is)

Source: [`orchestration/README.md`](../orchestration/README.md), [`openspec/specs/orchestration/spec.md`](../openspec/specs/orchestration/spec.md), `spec.md` §6.7-6.8 and §11.

1. Troy owns `orchestration/` only: wiring, UI shell, and the §6.7 breadcrumb. Nothing in `design/` edits that folder.
2. `orchestration/` is the sole importer of sibling packages. Nothing here adds imports to `orchestration/composition.py`.
3. §6.7 is the guaranteed baseline. It lights path segments via `QTimer` in `orchestration/controller.py` and fires the OS reveal on the last segment. This folder's assets never claim to be that animation.
4. §6.8 stretch is optional and non-blocking. An arrow/ring lands on the real icon only after `reveal()` returns true. It fails silently and gets dropped by the 2:00 sprint cutoff with zero demo impact.
5. Call order is match, then breadcrumb, then `reveal(path)`, then optionally `overlay(path)`. Overlay never runs before reveal.
6. No cross-editing. This work never touches `orchestration/`, `matcher/`, or any other owner's folder.

## Contents

- [`brand/`](brand/). Palette, brand brief, and the brand-kit overview board.
- [`pointer/`](pointer/). Arrow and ring SVGs, PNG fallbacks, and `hotspot.json` (the tip coordinate that must land on the icon).
- [`prototype/`](prototype/). A throwaway, standalone HTML sketch that shows the arrow landing on a fake icon box. Not connected to orchestration, matcher, or any pipeline code. For eyeballing the motion only.
- [`QA.md`](QA.md). The design QA checklist and lock status for the pointer assets (written by `clicky-design-qa`).
- [`HANDOFF_TROY.md`](HANDOFF_TROY.md). Docs-only notes for whoever eventually wires `overlay-stretch/` into orchestration.
- `decisions.tsv`. Local decision trail for this design pass.

## Palette

Signal blue, chosen for action and pointing rather than a generic AI-glow purple:

| Token | Hex | Use |
|-------|-----|-----|
| `signal-blue` | `#2563EB` | Primary fill |
| `signal-blue-light` | `#93C5FD` | Highlight, hover, secondary strokes |
| `signal-blue-deep` | `#1E3A8A` | Outline/stroke for contrast on light backgrounds |
| `charcoal` | `#0F172A` | Outline/stroke for contrast on dark backgrounds |
| `paper` | `#F8FAFC` | Neutral background/negative space |

## Ownership and branch

Person 5 seat, `rohart-branch`. This folder is new and top-level; it does not belong to any existing component folder in `README.md`'s team map. If a stretch owner later claims `overlay-stretch/`, they consume these assets per `HANDOFF_TROY.md`; they do not move this folder.
