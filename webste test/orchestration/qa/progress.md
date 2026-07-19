# QA progress — iteration 1

Evidence, in run order (all against the real artifact in `/tmp/party-game-cloud`):

- V1 clean rebuild: `rm -rf .next && npm run build` → exit 0.
- V2 typecheck: `npx tsc --noEmit` → clean.
- V3 developer smoke: `npm run smoke` → `SMOKE PASS (44 assertions)`.
- V4 QA edge probes (`orchestration/qa/probes.mjs`, QA-owned, independent of developer's suite) against `next start` on :4311 → `PROBES PASS (12 assertions)`: imposter tie vote → nobody accused, escape, +250 imposter / 0 crew; WYR 1-1 tie → both sides +25; join mid-game → 409; host force-reveal with a missing answer → absent player gains 0; unknown playerId → 403 on both read and action.
- V5 dev-mode store integrity: same 12 probes against `next dev` on :4312 → all pass (globalThis store survives dev module isolation; create/join/action see one room).
- V6 headless demo: FIRST RUN FAILED with `DEMO FAIL: App not reachable` — root cause: V5's `next dev` had overwritten the production build in `.next`, the self-booted `next start` exited immediately, and the demo script discards server output (`stdio: "ignore"`) so the real error was invisible. After `npm run build`, `HEADLESS=1 node record-demo.mjs` → `DEMO PASS: 15 screenshots`.
- V6 screenshot review: landing, lobby (1 and 3 players), trivia question/locked/reveal/podium, WYR vote/split/podium, imposter role card (imposter + crew)/reveal/final podium/back-in-lobby all render correctly. Fonts load (Lilita One + Outfit), ink-navy + coral/aqua/sunshine palette, no purple-on-white, motions defined with reduced-motion fallback.
- V7 brief conformance: 4-letter code host/join flow, 3 games end to end, lobby/select/play/results screens, README at repo root with install/run/verify/demo, `demo/` has the recording script + README. All present.

Verdict: the product itself passes everything. One tooling defect found (see suggestions.md): the smoke/demo self-boot failure mode is undiagnosable from script output, and the `next dev` → stale-`.next` trap is undocumented. Loop continues.

# QA progress — iteration 2

- V8 sabotage smoke (QA's own run, `.next` moved aside): exit 1, output contains Next's real "Could not find a production build" error instead of a blind 30s timeout. Fix verified.
- V9: root `README.md` and `demo/README.md` both document the dev-build trap. Fix verified.
- V10 full gate on the final tree, in sequence: `rm -rf .next && npm run build` exit 0 → `npm run smoke` → `SMOKE PASS (44 assertions)` → QA probes on :4314 → `PROBES PASS (12 assertions)` → `HEADLESS=1 node record-demo.mjs` → `DEMO PASS: 15 screenshots`.

Every planner task (T1-T20) is implemented and verified. All exit-predicate conditions hold: build green, all three games playable end to end over both HTTP and the real browser UI, demo assets and a reproducible record script exist under `demo/`.

Loop complete.

# QA progress — iteration 3 (independent re-verification)

Evidence, in run order, all against the real artifact:

- V11 static conformance, T1 to T20 checked against the tree. `app/package.json` pins next 15.5.20, react 19.2.7, typescript 5.9.3, both fontsource packages. `lib/types.ts` brands `RoomCode` and `PlayerId` and keeps votes inside phase variants. `lib/store.ts` hangs the Map off `globalThis` and bumps `version` on mutate. `lib/content.ts` has 12 trivia questions, 10 WYR prompts, 16 imposter entries. Four API route files exist. `hooks/useRoom.ts` polls keyed on version. `lib/engine.ts` gates min players (trivia and WYR at 2, imposter at 3). Components for lobby, all three games, and the shared podium exist. Root `README.md` and `demo/README.md` both document the dev-build trap (T20). `smoke.mjs` keeps the last 4000 bytes of server output and aborts when the server exits early (T19).
- V12 clean rebuild: `rm -rf .next && npm run build` exit 0.
- V13 typecheck: `npx tsc --noEmit` clean.
- V14 developer smoke: `npm run smoke` prints `SMOKE PASS (44 assertions)`.
- V15 QA probes: `next start` on :4321, then `node orchestration/qa/probes.mjs http://localhost:4321` prints `PROBES PASS (12 assertions)`. Covers imposter tie escape, WYR tie scoring, join mid-game 409, partial-answer reveal, outsider 403s.
- V16 fresh demo: `rm -rf shots && HEADLESS=1 node record-demo.mjs` prints `DEMO PASS: 15 screenshots`. All 15 files are 700 KB or larger, none empty or stale.
- V17 screenshot review of the fresh run: landing form, trivia reveal with vote counts and correct-answer highlight and score deltas, imposter secret role card with category, final podium with ranked scores. Theme, fonts, and palette render as designed.
- V18 T19 regression: with `.next` moved aside, `npm run smoke` exits 1 and prints Next's real "Could not find a production build" error. `.next` restored, smoke green again.

All exit-predicate conditions hold. Loop complete.
