# Cody cursor iframe demo

Fullscreen **iframe** overlay with a **small companion cursor** (lower-right of the real OS mouse). Your system cursor stays visible; Cody springs toward that slot on its own, then can leave to point at a source.

## Run locally

From the repo root (needs a tiny static server so SVG paths resolve):

```bash
python -m http.server 8765
```

Open:

- http://localhost:8765/demo/cody-cursor/host.html — host page + fullscreen iframe  
- http://localhost:8765/demo/cody-cursor/overlay.html — overlay alone (mock desktop)

## Controls

| Input | Action |
|-------|--------|
| Mouse move | Real cursor stays; small Cody sits lower-right (independent spring) |
| 🎤 Listen / `V` | Voice: say “where’s Lazada” (Chrome/Edge) |
| `1` or HUD | Point at `receipt_lazada.pdf` + thought caption |
| `2` or HUD | Point at `invoice_shopee.pdf` |
| `Esc` | Resume follow |

Caption floats beside the small Cody cursor with what Cody thinks.

## Embed API (`postMessage`)

Host → overlay:

- `{ type: "cody-mouse", x, y }`
- `{ type: "cody-point", id: "lazada", thought?: string }` or `{ type: "cody-point", x, y, thought? }`
- `{ type: "cody-heard", transcript: "where's lazada" }`
- `{ type: "cody-follow" }`

Use `?nomock=1` only when embedding over a real page (hides mock desktop). Default keeps mock files so pointing works.

Overlay → host: `{ type: "cody-ready" }`, `{ type: "cody-status", mode }`

Assets: [`../../assets/cody-cursor/`](../../assets/cody-cursor/).
