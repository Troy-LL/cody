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
| `1` or HUD | Point at `receipt_lazada.pdf` |
| `2` or HUD | Point at `invoice_shopee.pdf` |
| `Esc` | Resume follow |

## Embed API (`postMessage`)

Host → overlay:

- `{ type: "cody-mouse", x, y }`
- `{ type: "cody-point", id: "lazada" }` or `{ type: "cody-point", x, y }`
- `{ type: "cody-follow" }`

Overlay → host: `{ type: "cody-ready" }`, `{ type: "cody-status", mode }`

Assets: [`../../assets/cody-cursor/`](../../assets/cody-cursor/).
