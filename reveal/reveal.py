"""Reveal entry point. See reveal/README.md and spec.md §6.5."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def reveal(path: str) -> bool:
    """Open containing folder and select *path* on Windows.

    Returns:
        True when Explorer was spawned for an existing file.
        False on missing/non-file paths, non-Windows, or spawn failure.
    """
    if sys.platform != "win32":
        logger.warning("reveal: unsupported platform %s", sys.platform)
        return False

    try:
        resolved = Path(path).expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        logger.warning("reveal: cannot resolve path %r: %s", path, exc)
        return False

    if not resolved.is_file():
        logger.warning("reveal: not an existing file: %s", resolved)
        return False

    abs_path = str(resolved)
    try:
        subprocess.run(
            ["explorer", f"/select,{abs_path}"],
            shell=False,
            check=False,
        )
    except OSError as exc:
        logger.warning("reveal: failed to spawn explorer: %s", abs_path, exc_info=exc)
        return False

    return True
