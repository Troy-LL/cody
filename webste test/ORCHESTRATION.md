# Party Game Cloud Orchestration

**Parent:** Grok (Cursor cloud run `bc-019f766d-6dd0-7939-a2a9-e9531e25fd81`)  
**Orchestrator model:** Claude Fable 5 Thinking Extra High (`claude-fable-5-thinking-xhigh`)  
**Style:** `/poteto-mode`  
**Subagents (via `/create-subagent` defs):** planner → developer → QA  
**Isolated workspace:** `/tmp/party-game-cloud` (never pollute `/workspace` Cody repo)

## Loop

```
for iteration = 1..N:
  1. PLANNER  updates orchestration/planner/{plan,progress,suggestions}.md
  2. DEVELOPER implements plan → orchestration/developer/{plan,progress,suggestions}.md
  3. QA        verifies → orchestration/qa/{plan,progress,suggestions}.md
  4. if qa/suggestions.md == "NONE": break
  5. else: feed suggestions back into planner and continue
```

## Exit condition

`orchestration/qa/suggestions.md` is exactly `NONE` and the Next.js party game builds and runs.

## Export (parent only)

When the loop exits, parent copies `/tmp/party-game-cloud/**` → `/workspace/webste test/` only.

## Product brief

Full working party game website: Next.js + React, host/join rooms, ≥3 mini-games, polished UI, macOS-style browser video demo.
