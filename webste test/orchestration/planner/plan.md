# Planner master plan — Party Game Website (iteration 1)

Product: "Confetti Club" — a party game website. Host creates a room, shares a 4-letter code, players join on their own devices. Three mini-games playable end to end. Next.js App Router + React + TypeScript under `/tmp/party-game-cloud/app`.

## Foundational decisions (read before implementing)

- **Data shape first.** One `Room` object per room. `Room.state` is a discriminated union (`lobby | trivia | wyr | imposter`), and each game's inner `phase` is its own discriminated union. No scattered booleans. All mutations go through one reducer `applyAction(room, playerId, action)` where `action` is a discriminated `RoomAction` union.
- **Store.** In-memory `Map<string, Room>` hung off `globalThis` (survives Next dev hot reload). `Room.version` increments on every mutation; clients poll `GET /api/rooms/[code]` about once per second and re-render when version changes. No external DB, no websockets (polling is enough at party scale and has fewer failure modes).
- **Identity.** `playerId` issued by the server on create/join, kept in the client's `sessionStorage` keyed by room code, so two browser tabs are two players (needed for the demo).
- **Types.** Branded `RoomCode` / `PlayerId`. Illegal states unrepresentable: e.g. votes live inside the phase variant that accepts them.
- **UI.** Party-expressive, not AI slop: @fontsource "Lilita One" (display) + "Outfit" (body), deep ink-navy background with floating blurred color orbs and grain, coral/sunshine/aqua accents. Exactly three intentional motions: ambient orb drift, screen-entrance pop, button squish/selection pulse. CSS only, no animation library.
- **Demo.** puppeteer-core driving the system Chrome (installed at /usr/local/bin/google-chrome), so no browser download. One script walks host + 2 players through all three games; headful for recording, `HEADLESS=1` for CI.

## Tasks (ordered scaffold → domain → UI → games → demo)

- [ ] T1. Scaffold app: `app/package.json` (pinned deps: next 15, react 19, typescript 5, @fontsource/lilita-one, @fontsource/outfit), `tsconfig.json` strict, `next.config.ts`, `app/layout.tsx`, `app/globals.css`. Verify: `npm install` succeeds.
- [ ] T2. Domain types `lib/types.ts`: branded RoomCode/PlayerId, Player, TriviaState/WyrState/ImposterState with per-game phase unions, GameState union, Room. Verify: `npx tsc --noEmit`.
- [ ] T3. Store `lib/store.ts`: globalThis Map, createRoom (4-letter code, collision retry), getRoom, mutateRoom(code, fn) bumping version. Verify: tsc.
- [ ] T4. Content `lib/content.ts`: ≥10 trivia questions, ≥8 would-you-rather prompts, ≥12 imposter category/word entries.
- [ ] T5. Engine `lib/engine.ts`: `RoomAction` union (join, startGame, trivia answer/advance, wyr vote/advance, imposter vote/advance, backToLobby) + `applyAction` reducer with scoring (trivia: 100 + speed bonus ≤50; wyr: majority side +25; imposter: caught → correct voters +100, survives → imposter +250). Verify: tsc.
- [ ] T6. API routes: `POST /api/rooms` (create), `POST /api/rooms/[code]/join`, `GET /api/rooms/[code]`, `POST /api/rooms/[code]/action`. Parse request bodies at the boundary; typed JSON responses; 404/409/400 on bad room/name/action. Verify: tsc.
- [ ] T7. Client data layer `lib/client.ts` + `hooks/useRoom.ts`: fetch helpers, 1s polling hook keyed on version, sessionStorage identity helper.
- [ ] T8. Theme: fonts wired in layout, globals.css palette + orb background + motion keyframes + shared component classes (buttons, cards, pills).
- [ ] T9. Landing `app/page.tsx`: hero, create-room form (name+emoji), join form (code+name+emoji). Redirect to `/room/[code]`.
- [ ] T10. Room shell `app/room/[code]/page.tsx` (client): render by `room.state.game`; lobby screen: player grid, shareable code, host-only game picker, min-players gating (trivia/wyr ≥2, imposter ≥3).
- [ ] T11. Trivia Blitz screens: question w/ countdown-free flow (host advances), answer lock-in, reveal with per-choice counts + correct highlight, running scoreboard, final podium.
- [ ] T12. Would You Rather screens: A/B vote cards, reveal with split-percentage bars, final.
- [ ] T13. Imposter Word screens: private role/word card (tap to peek), discussion hint list, vote grid, reveal (imposter caught or escaped + word shown), final.
- [ ] T14. Results/podium shared component + "Back to lobby" host action.
- [ ] T15. `README.md` at repo root (`/tmp/party-game-cloud/README.md`) and app-level run notes: install, dev, build, start, smoke, demo.
- [ ] T16. Smoke lever `app/scripts/smoke.mjs`: boots `next start` on a free port, drives the HTTP API through create → join ×2 → full round of each of the 3 games → asserts phases and scores → exits 0/1. Verify: run it green after build.
- [ ] T17. Demo `demo/record-demo.mjs` + `demo/package.json` (puppeteer-core pinned) + `demo/README.md`: launches system Chrome, host tab + 2 player tabs, walks lobby → trivia → wyr → imposter → results, screenshots into `demo/shots/`. `HEADLESS=1` supported. Verify: headless run completes and screenshots exist.
- [ ] T18. Full gate: `npm run build` green, smoke green, demo headless green.

## Iteration 2 tasks (from QA suggestions, iteration 1)

- [ ] T19. Diagnosable self-boot failures: in `app/scripts/smoke.mjs` and `demo/record-demo.mjs`, capture the spawned server's stdout+stderr, fail immediately if the server process exits before the port opens, and include the output tail in the failure message. Verify: sabotage run (`rm -rf app/.next`, run smoke) prints the real Next.js "no production build" error.
- [ ] T20. Document the trap: `npm run dev` overwrites the production build in `.next`; re-run `npm run build` before smoke/demo. Add to root `README.md` and `demo/README.md`. Verify: both files mention it.

## Verification contract (QA will hold developer to this)

1. `cd /tmp/party-game-cloud/app && npm run build` exits 0.
2. `node scripts/smoke.mjs` exits 0 (plays all three games over HTTP).
3. `cd /tmp/party-game-cloud/demo && HEADLESS=1 node record-demo.mjs` exits 0 and writes screenshots.
4. README instructions reproduce the above.

Developer may begin.
