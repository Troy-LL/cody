# QA plan — iteration 1 (derived from planner plan.md)

- [x] V1. Clean rebuild: delete `.next`, `npm run build` exits 0.
- [x] V2. `npx tsc --noEmit` clean.
- [x] V3. Developer smoke suite passes (`npm run smoke`, 44 assertions).
- [x] V4. Independent edge probes (QA-owned script, not developer's):
  - imposter tie vote → nobody accused, imposter escapes with +250
  - WYR tie → both sides score 25
  - join while a game is running → 409
  - host force-reveal with partial answers → unanswered players gain 0
  - action from a player not in the room → 403
- [x] V5. Dev-mode store integrity: against `next dev`, create + join + action still see the same room (globalThis store survives dev module isolation).
- [x] V6. Headless demo run green; inspect screenshots for visual defects (fonts, layout, contrast, all screens present).
- [x] V7. Brief conformance: 4-letter code flow, 3 games end to end, lobby/select/play/results screens, expressive non-slop UI with 2-3 intentional motions, README accurate, demo recording path documented.

Iteration 2 (verifying T19/T20 fixes, then the full gate again):

- [x] V8. Sabotage smoke without `.next`: exits 1 and prints the real Next.js boot error, not a blind timeout.
- [x] V9. Both READMEs document the dev-build/.next trap.
- [x] V10. Full gate re-run on the final tree: clean build → smoke → edge probes → headless demo, all green.

Iteration 3 (independent re-verification of the full gate on the current tree):

- [x] V11. Static conformance of every planner task T1 to T20 against the real files. Pinned deps, branded types, globalThis store with version bump, 12 trivia plus 10 WYR plus 16 imposter entries, 4 API routes, polling hook, min-player gating, all game components, shared podium, both READMEs with the dev-build trap, smoke and demo levers with server-output capture.
- [x] V12. Clean rebuild: `rm -rf .next && npm run build` exits 0.
- [x] V13. `npx tsc --noEmit` clean.
- [x] V14. Developer smoke: `npm run smoke` passes with 44 assertions.
- [x] V15. QA edge probes against `next start` on :4321 pass with 12 assertions.
- [x] V16. Headless demo with fresh screenshots: `rm -rf shots && HEADLESS=1 node record-demo.mjs` passes and writes 15 non-empty screenshots.
- [x] V17. Screenshot review: landing, trivia reveal with scores, imposter secret role card, final podium all render with the intended theme and fonts.
- [x] V18. T19 regression: sabotage smoke without `.next` exits 1 and prints the real "Could not find a production build" error. Green path restored afterward.
