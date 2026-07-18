"""Build in-app RevealAnimation segments from matched path + scan root."""

from __future__ import annotations

from pathlib import PureWindowsPath

from contracts.schemas import RevealAnimation


class PathOutsideRootError(ValueError):
    """Raised when the matched path is not under the scanned root."""


def build_reveal_animation(path: str, root: str) -> RevealAnimation:
    """Split *path* relative to *root* into breadcrumb segments.

    Segments are ``[root_name, ...relative parts]`` without duplicating the
    full root path. Paths outside *root* raise ``PathOutsideRootError``.
    """
    file_path = PureWindowsPath(path)
    root_path = PureWindowsPath(root)
    try:
        relative = file_path.relative_to(root_path)
    except ValueError as exc:
        raise PathOutsideRootError(
            f"matched path {path!r} is outside scanned root {root!r}"
        ) from exc

    segments = [root_path.name, *relative.parts]
    return {
        "path": path,
        "root": root,
        "segments": list(segments),
    }
