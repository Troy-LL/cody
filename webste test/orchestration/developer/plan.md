# Developer plan — iteration 1 (copied from planner, checkboxes live)

- [x] T1. Scaffold app (package.json pinned, tsconfig strict, next.config, layout, globals)
- [x] T2. Domain types `lib/types.ts`
- [x] T3. Store `lib/store.ts`
- [x] T4. Content `lib/content.ts`
- [x] T5. Engine `lib/engine.ts` (RoomAction union + applyAction reducer + scoring)
- [x] T6. API routes (create/join/get/action) with boundary parsing
- [x] T7. Client data layer + useRoom polling hook + sessionStorage identity
- [x] T8. Theme (fonts, palette, orbs, 3 motions, shared classes)
- [x] T9. Landing page (host + join forms)
- [x] T10. Room shell + Lobby
- [x] T11. Trivia Blitz screens
- [x] T12. Would You Rather screens
- [x] T13. Imposter Word screens
- [x] T14. Podium + back-to-lobby
- [x] T15. README (root) with install/run
- [x] T16. Smoke lever `app/scripts/smoke.mjs`
- [x] T17. Demo `demo/record-demo.mjs` (puppeteer-core + system Chrome)
- [x] T18. Full gate: build + smoke + demo headless green

Iteration 2:

- [x] T19. Diagnosable self-boot failures in smoke.mjs + record-demo.mjs (capture output, die fast on early exit)
- [x] T20. Document the dev-build/.next trap in root README.md and demo/README.md
