# Developer progress — iteration 1

Built and verified this iteration (all 18 planner tasks):

## What exists

- `/tmp/party-game-cloud/app` — Next.js 15.5.20 + React 19.2.7 + TS 5.9.3 strict (`noUncheckedIndexedAccess` on), pinned deps.
- Domain: `lib/types.ts` (branded `RoomCode`/`PlayerId`, per-game phase unions, redacted client-view types), `lib/store.ts` (globalThis Map, TTL prune, version bump on mutate), `lib/engine.ts` (single `applyAction` reducer with exhaustive switch, scoring, per-player view redaction, boundary parsers), `lib/content.ts` (12 trivia Qs, 10 WYR prompts, 16 imposter entries).
- API: `POST /api/rooms`, `POST /api/rooms/[code]/join`, `GET /api/rooms/[code]?player=`, `POST /api/rooms/[code]/action`. Untrusted JSON parsed at the boundary; ApiError → typed JSON error with status.
- Client: `lib/client.ts` + `hooks/useRoom.ts` (1s polling keyed on room version, snap-update after actions, sessionStorage identity per tab so multiple tabs are multiple players).
- UI: landing (host/join), lobby with code badge + game tiles + min-player gating, all three games with question/vote/reveal/final screens, shared podium. Theme: Lilita One + Outfit (self-hosted via fontsource), ink-navy background with drifting coral/aqua/sunshine orbs + grain, three motions (orb drift, pop-in entrance, button squish/selection pulse), `prefers-reduced-motion` respected.
- Levers: `app/scripts/smoke.mjs` (boots `next start` on a free port, plays all 3 games over HTTP, 44 assertions), `demo/record-demo.mjs` (puppeteer-core + system Chrome, host + 2 player tabs, full walkthrough, 15 screenshots, HEADLESS/SLOWMO/PAUSE/BASE_URL knobs).
- Docs: root `README.md`, `demo/README.md`.

## Verification run (real artifact, this iteration)

- `npx tsc --noEmit` clean.
- `npm run build` exit 0 (all routes compile; landing static, room + API dynamic).
- `node scripts/smoke.mjs` → `SMOKE PASS (44 assertions)`: room lifecycle, 403/404/409 errors, trivia auto-reveal + speed scoring + no answer leak, WYR 2-1 split + majority scoring, imposter role redaction + majority catch + gains.
- `HEADLESS=1 node record-demo.mjs` → `DEMO PASS: 15 screenshots` covering every screen.
- Screenshots eyeballed: theme renders as designed, no purple-on-white, fonts load.

## Fixed along the way

- `noUncheckedIndexedAccess` error on the reveal counts tuple (Trivia.tsx).
- Demo deadlock: puppeteer's `waitForSelector` polls via requestAnimationFrame, which backgrounded headless tabs never fire. Replaced all waits with node-side `page.evaluate` polling and added background-throttling-disable Chrome flags.

QA may begin. Run: `cd /tmp/party-game-cloud/app && npm install && npm run build && npm run smoke`; then `cd ../demo && npm install && HEADLESS=1 node record-demo.mjs`. Dev server: `npm run dev` in `app/`.

# Developer progress — iteration 2

T19: both self-boot scripts now spawn `next start` with piped stdio, keep the last 4000 bytes of server output, abort the readiness wait the moment the server process exits, and include the output tail in the failure message.

T20: dev-build trap documented in root `README.md` (Verify section) and `demo/README.md`.

Verified on the real artifact:
- Sabotage smoke (`.next` moved away): exit 1, message contains "Server exited with code 1 before becoming ready" plus Next's "Could not find a production build" error. Previously this was a blind 30s timeout.
- Sabotage demo: exit 1 with the same diagnosis.
- Green paths after restoring `.next`: `SMOKE PASS (44 assertions)`, `DEMO PASS: 15 screenshots`.

QA may begin.
