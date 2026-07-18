# Reveal uses Explorer /select, argv

On Windows, `reveal` spawns `subprocess.run(["explorer", f"/select,{abs_path}"], shell=False)`. The `/select,` flag is glued to the absolute path (no shell quoting). Success ignores Explorer’s process exit code (often non-zero even when the window opened).
