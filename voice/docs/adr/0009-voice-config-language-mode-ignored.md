# JSON language_mode ignored by speak

`config.example.json` keeps `language_mode` for §8.2 shape. `speak` ignores that field; orchestration owns auto-resolution via `ControllerDeps.language_mode`.
