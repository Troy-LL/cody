# Cody cursor demo

Clicky-style helper cursor in a fullscreen browser overlay.

- Your normal mouse stays.
- A **small Cody cursor** rides in the **lower-right** of the mouse (not glued — soft spring).
- On command, Cody **leaves** that slot and points at a file.
- A **caption** floats next to Cody with what it thinks.
- **Voice** (Chrome/Edge): say “find my boarding pass” — mic bar shows volume while listening, and Cody answers out loud.
- **Text commands**: same pipeline as voice, no mic needed — type into the HUD box.

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
| **🎤 Voice** (click) or `V` | Toggle continuous voice listening + volume meter |
| Say “find my boarding pass”, “point at the Shopee invoice”, “where’s the budget” | Point + caption + spoken reply |
| Say “follow me” / “stop” / “never mind” / “cancel” / bare “resume” | Back to follow mode (“find my resume” still points at the resume file) |
| Text box (`/` to focus) + **Run** or Enter | Same command pipeline as voice, no mic needed |
| `1` | Point at `receipt_lazada.pdf` |
| `2` | Point at `invoice_shopee.pdf` |
| **Follow again** / `Esc` | Cody returns to companion mode |

Single-key shortcuts (`1`, `2`, `v`, `/`) are ignored while the text box is focused; `Esc` in the box just unfocuses it.

## Mock desktop files

Each icon has a `data-id` and a `data-keywords` list used for voice/text matching (filename words + the raw id also match).

| id | File | Keywords |
|----|------|----------|
| `lazada` | receipt_lazada.pdf | lazada receipt resibo order shopping pdf |
| `shopee` | invoice_shopee.pdf | shopee invoice bill order shopping pdf |
| `notes` | meeting_notes.txt | meeting notes minutes standup memo text |
| `budget` | budget_2026.xlsx | budget spreadsheet finance excel money expenses 2026 |
| `resume` | resume_troy.pdf | resume cv curriculum vitae job troy application |
| `boarding` | boarding_pass.pdf | boarding pass flight ticket travel plane airline trip |
| `photo` | family_photo.png | photo picture image family jpeg png snapshot |
| `contract` | rent_contract.docx | contract lease rent agreement doc apartment landlord |

## Voice notes

- Uses only the browser-native **Web Speech API** (`SpeechRecognition` for input, `speechSynthesis` for the spoken reply) — no libraries, no SDKs.
- Needs a mic plus Chrome or Edge (recognition is Chromium-only and goes through the browser vendor's speech service). Firefox/headless browsers: the mic button is disabled and a note is shown — use the text box instead.
- Recognition runs continuous (`lang: en-US`) and auto-restarts after silence until you toggle it off.

## Files

| Path | Role |
|------|------|
| `overlay.html` | Cursor, caption, voice + text commands, mock files |
| `host.html` | Fullscreen iframe wrapper |
| `../../assets/cody-cursor/*.svg` | Cody pointer art |

## Embed notes

Default: mock files stay visible so pointing works.

- `?nomock=1` — hide mock desktop (only when overlaying a real page).
- Host → overlay `postMessage`: `cody-mouse`, `cody-point`, `cody-follow`, `cody-heard`, and `cody-command`:
  - `{ type: "cody-command", text: "find my boarding pass" }` — routed to the same `handleCommand()` used by voice and the text box.
- Overlay → host: `cody-ready`, `cody-status`.

## SPEED MODE

Work lands straight on `main` (no feature-branch PR gate for this sprint demo). Push from `main` after each slice.
