# Incomplete config defaults when enabled

When enabled, missing `provider` defaults to `openvoice`, missing `device` defaults to `cpu` (or `OPENVOICE_DEVICE`), and missing `checkpoints_dir` defaults to `voice/checkpoints_v2`. A usable `speaker` remains required; `reference_wav` is required only when `tone_convert` is true.
