# Ignore Explorer exit code

After a successful spawn (no `OSError`), `reveal` returns `true` regardless of process returncode. Explorer commonly exits non-zero even when select worked.
