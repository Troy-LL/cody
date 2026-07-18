# Matcher / Ranker (Cody)

| Field | Value |
|-------|-------|
| **Owner** | Person 5 |
| **Purpose** | Rank files against structured intent using Codex; emit best match + reasoning. |
| **Owns** | `matcher/` package, `match` entry point, and `ModelConfig` usage (`spec.md` §8.1). |
| **Does not own** | Indexing, extraction, NLU implementation, reveal/voice, UI shell. |
| **Frozen I/O** | `match(files, content, intent) -> MatchResult` per `spec.md` §6.4. |
| **Stub requirement** | Without `matcher/local_model.json` (or with `MATCHER_STUB=1`), returns a deterministic fixture-shaped stub. |
| **Test command** | `python -m pytest matcher/tests -q` |
| **Branch** | `rohart-branch` |
| **Done condition** | Section 7 fixtures yield the correct file with a one-sentence `reasoning` string (live path). |
| **Integration handoff** | Orchestration imports `matcher.match.match`. Consume contracts only — do not import sibling packages. |

## Call example

```python
from fixtures.load import load_extracted_content, load_file_records, load_query_intents
from matcher.match import match

files = load_file_records()
content = load_extracted_content()
intent = load_query_intents()[0]
result = match(files, content, intent)
print(result["best_match"]["path"], result["best_match"]["reasoning"])
```

## Config

1. Copy `matcher/local_model.example.json` to `matcher/local_model.json`.
2. Paste your API key. The real file is gitignored.
3. Set `MATCHER_STUB=0` to force the live Responses call (default is live when the config file exists).

## Errors for orchestration

`match` raises (never fabricates a path):

- `ValueError` if `files` is empty
- `matcher.config.ConfigError` if live mode needs config and it is missing/invalid
- `matcher.api.ModelCallError` on HTTP/transport failure
- `matcher.parse.MatchParseError` on unparseable JSON or a path not in the input set

Catch these and show an error state in the UI.

## Goldens

```bash
MATCHER_STUB=1 python matcher/run_golden.py --shape-only
MATCHER_STUB=0 python matcher/run_golden.py
python matcher/smoke.py
```
