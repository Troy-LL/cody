# Reveal requires an existing file

Before calling Explorer, `reveal` normalizes with `Path(path).expanduser().resolve()` and requires `is_file()`. Missing paths, directories, and resolve failures return `false` without spawning Explorer.
