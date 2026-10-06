from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def repo_path(relative: str) -> Path:
    """Resolve a repository-relative path without allowing path escape."""

    candidate = (REPO_ROOT / relative).resolve()
    if candidate != REPO_ROOT and REPO_ROOT not in candidate.parents:
        raise ValueError(f"path escapes repository root: {relative!r}")
    return candidate
