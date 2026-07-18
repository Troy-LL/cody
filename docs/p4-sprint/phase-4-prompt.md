# Phase 4. Prompt assembly

Back to [overview.md](overview.md).

## Goal

A pure function builds the prompt from the three inputs. No network call.

## Changes

- `matcher/prompt.py` (new). `build_prompt(files, content, intent) -> str`.
- One line per candidate joining §6.1 metadata to its §6.2 snippet.
- Intent block quotes `description`, `time_hint.resolved_range`, and `type_hint`. Soft in-range and type-match annotations only. Never drop candidates in code.
- Instruction to answer as §6.4 JSON with one-sentence reasoning naming the matched evidence.
- Ignore unknown input fields. `extractable: false` rows appear with metadata only.

## Data structures

Prompt is a single `str`. No new public types.

## Verification

**Static.** Unit test. Lazada golden prompt contains the receipt filename, snippet text, and resolved range.

**Runtime.** Print prompt length for the full fixture set and confirm it is nowhere near context limits.
