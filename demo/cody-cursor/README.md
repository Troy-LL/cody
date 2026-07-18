# Cody cursor demo

Clicky-style helper cursor in a fullscreen browser overlay.

- Your normal mouse stays.
- A **small Cody cursor** rides in the **lower-right** of the mouse (not glued — soft spring).
- On command, Cody **leaves** that slot and points at a file.
- A **caption** floats next to Cody with what it thinks.
- **Voice** (Chrome/Edge): say “where’s Lazada” — mic bar shows volume while listening.

## Quick start

```bash
# from repo root
python -m http.server 8765
```

| URL | What |
|-----|------|
| http://localhost:8765/demo/cody-cursor/overlay.html | Full demo (mock desktop + Cody) |
| http://localhost:8765/demo/cody-cursor/host.html | Same overlay in a fullscreen iframe |

Allow the mic when the browser asks (localhost is fine).

## Controls

| Input | Action |
|-------|--------|
| Move mouse | Cody companion stays lower-right |
| **Listen** or `V` (release once) | Start/stop voice listen + volume meter |
| Say “where’s Lazada” / “Shopee” / “notes” | Point + caption |
| `1` | Point at `receipt_lazada.pdf` |
| `2` | Point at `invoice_shopee.pdf` |
| **Follow again** / `Esc` | Cody returns to companion mode |

## Files

| Path | Role |
|------|------|
| `overlay.html` | Cursor, caption, voice, mock files |
| `host.html` | Fullscreen iframe wrapper |
| `../../assets/cody-cursor/*.svg` | Cody pointer art |

## Embed notes

Default: mock files stay visible so pointing works.

- `?nomock=1` — hide mock desktop (only when overlaying a real page).
- Host → overlay `postMessage`: `cody-mouse`, `cody-point`, `cody-heard`, `cody-follow`.
- Overlay → host: `cody-ready`, `cody-status`.

## SPEED MODE

Work lands straight on `main` (no feature-branch PR gate for this sprint demo). Push from `main` after each slice.
