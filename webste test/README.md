# Confetti Club

A party game website. The host opens a room, shares a 4-letter code, and friends join from their own devices. Three mini-games, one running scoreboard for the whole party.

- **Trivia Blitz.** Five quickfire multiple-choice questions. Correct answers score 100 plus a speed bonus of up to 50.
- **Would You Rather.** Pick a side, watch the room's split. The majority side scores 25.
- **Imposter Word.** Everyone gets a secret word except one imposter, who only knows the category. Describe, suspect, vote. Catching the imposter scores accusers 100; a clean escape scores the imposter 250.

## Stack

Next.js 15 (App Router) + React 19 + TypeScript, no external database. Rooms live in an in-memory store; every room mutation goes through one typed reducer, and clients poll about once a second. State resets when the server restarts, which is fine for a party.

## Run it

```bash
cd app
npm install
npm run dev        # http://localhost:3000
```

Production:

```bash
npm run build
npm run start
```

Open the site, host a room, then join from other tabs or devices with the code. Imposter Word needs 3+ players; the other games need 2+.

## Verify it

```bash
cd app
npm run build
npm run smoke      # plays a full round of all three games over HTTP, 44 assertions
```

Heads up: `npm run dev` overwrites the production build in `.next`. If you have run the dev server since the last build, re-run `npm run build` before `npm run smoke` or the demo script, or they will fail at server boot.

## Record a demo

`demo/record-demo.mjs` drives host + two player tabs through every game using the system Chrome. See `demo/README.md`.

```bash
cd demo && npm install
HEADLESS=1 node record-demo.mjs          # CI check + screenshots
SLOWMO=120 PAUSE=1500 node record-demo.mjs   # headful, paced for video capture
```

## Layout

- `app/lib/types.ts` owns the domain model: branded ids, per-game phase unions, client view types.
- `app/lib/engine.ts` owns all game rules: the `applyAction` reducer, scoring, and the per-player redacted views (secret words and correct answers never leave the server early).
- `app/lib/store.ts` owns the in-memory room map.
- `app/app/api/**` are thin HTTP adapters that parse untrusted JSON and call the engine.
- `app/components/**` render one screen per game phase.
- `app/scripts/smoke.mjs` is the end-to-end API check; `demo/record-demo.mjs` is the browser walkthrough.
