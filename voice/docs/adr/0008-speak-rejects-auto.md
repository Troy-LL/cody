# speak rejects auto

If `speak` receives `language_mode="auto"`, it soft-fails with `false`. Callers (smoke script, tests, orchestration) must pass `en`, `tl`, or `taglish` explicitly.
