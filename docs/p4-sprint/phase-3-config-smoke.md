# Phase 3. ModelConfig loader and Codex smoke

Back to [overview.md](overview.md).

## Goal

Config comes from a gitignored local file. One live Responses call proves the key and model before the 0:30 window closes. Last cheap moment to swap models.

## Changes

- `matcher/config.py` (new). `load_config() -> ModelConfig` with `provider`, `base_url`, `api_key`, `model` (§8.1).
- `.gitignore` entry for the matcher config path (e.g. `matcher/local_model.json` or `.env.matcher`). Additive. Safe for other seats.
- `matcher/smoke.py` (throwaway). One raw Responses call on the Lazada golden. Deleted in Phase 8.
- Confirm live model ID against OpenAI's list. Spec provisional ID is `gpt-5.3-codex`.

## Data structures

`ModelConfig = {provider, base_url, api_key, model}`.

## Verification

**Static.** `git check-ignore -v <config-path>` confirms the secret file cannot be committed.

**Runtime.** Missing config raises a clear error. Live smoke returns the Lazada receipt path for the Taglish golden. Wrong path means escalate model choice now, not at 2:00.
