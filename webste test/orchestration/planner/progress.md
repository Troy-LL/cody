# Planner progress — iteration 1

Decided this iteration:

- Named the product "Confetti Club" and fixed the stack: Next.js 15 App Router, React 19, TypeScript strict, no external DB, no websockets.
- Chose the domain shape before any task: one `Room` per room, `GameState` discriminated union with per-game phase unions, single `applyAction` reducer, `globalThis` Map store with a `version` counter and 1s client polling.
- Chose puppeteer-core + system Chrome for the demo (Chrome 148 is preinstalled; avoids Playwright browser downloads).
- Chose @fontsource packages over next/font/google so builds never depend on Google Fonts egress.
- Wrote 18 ordered, individually verifiable tasks (scaffold → domain → UI → games → demo) plus the QA verification contract.
- Scoring rules fixed up front so developer and QA agree: trivia 100 + speed bonus ≤50, WYR majority +25, imposter caught → voters +100 / escaped → imposter +250.

No prior QA suggestions existed (iteration 1).

# Planner progress — iteration 2

Folded both QA suggestions into two atomic tasks (T19, T20). Scope deliberately stays at the two flagged defects: the game code passed 56 assertions plus screenshot review, so no product changes. T19's verification is a sabotage run, since the defect is precisely that failures were undiagnosable. Developer may begin.
