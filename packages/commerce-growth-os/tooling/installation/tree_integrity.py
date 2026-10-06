"""Shared filesystem integrity checks for Skill sources and installed trees."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path


_IGNORED_CACHE_SUFFIXES = {".pyc", ".pyo"}
_IGNORED_CACHE_DIRECTORIES = {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
_IGNORED_CACHE_FILES = {".DS_Store", "Thumbs.db"}


class TreeIntegrityError(RuntimeError):
    """Raised when a tree contains links, special files, or escapes its boundary."""


def is_runtime_cache(relative: Path) -> bool:
    return (
        any(part in _IGNORED_CACHE_DIRECTORIES for part in relative.parts)
        or relative.suffix in _IGNORED_CACHE_SUFFIXES
        or relative.name in _IGNORED_CACHE_FILES
    )


def lexical_absolute(path: Path) -> Path:
    """Return an absolute path without dereferencing any symlink component."""

    return Path(os.path.abspath(os.fspath(path)))


def validate_real_directory(path: Path) -> Path:
    """Require every existing path component to be a real directory, not a symlink."""

    candidate = lexical_absolute(path)
    # macOS exposes its real temporary tree through the fixed /var -> /private/var system alias.
    # Normalize only that OS-owned leading alias; user-controlled descendant links still fail.
    system_var = Path("/var")
    if os.name != "nt" and system_var.is_symlink():
        try:
            relative_to_var = candidate.relative_to(system_var)
        except ValueError:
            pass
        else:
            candidate = system_var.resolve(strict=True) / relative_to_var
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError as exc:
            raise TreeIntegrityError(f"missing path: {current}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise TreeIntegrityError(f"symlink is not allowed: {current}")
        if not stat.S_ISDIR(metadata.st_mode):
            raise TreeIntegrityError(f"expected a directory: {current}")
    return candidate


def _validate_boundary(path: Path, allowed_root: Path) -> tuple[Path, Path]:
    candidate = lexical_absolute(path)
    boundary = lexical_absolute(allowed_root)
    try:
        relative = candidate.relative_to(boundary)
    except ValueError as exc:
        raise TreeIntegrityError(f"path escapes allowed root: {candidate}") from exc

    current = boundary
    for part in relative.parts:
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError as exc:
            raise TreeIntegrityError(f"missing path: {current}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise TreeIntegrityError(f"symlink is not allowed: {current}")

    try:
        candidate.resolve(strict=True).relative_to(boundary.resolve(strict=True))
    except (FileNotFoundError, ValueError) as exc:
        raise TreeIntegrityError(f"path escapes allowed root or is missing: {candidate}") from exc
    return candidate, boundary


def validate_tree(
    root: Path,
    *,
    allowed_root: Path | None = None,
    require_directory: bool = False,
) -> list[Path]:
    """Validate a tree without following links and return its regular files."""

    candidate = lexical_absolute(root)
    if allowed_root is not None:
        candidate, _ = _validate_boundary(candidate, allowed_root)

    try:
        root_metadata = candidate.lstat()
    except FileNotFoundError as exc:
        raise TreeIntegrityError(f"missing path: {candidate}") from exc
    if stat.S_ISLNK(root_metadata.st_mode):
        raise TreeIntegrityError(f"symlink is not allowed: {candidate}")
    if require_directory and not stat.S_ISDIR(root_metadata.st_mode):
        raise TreeIntegrityError(f"expected a directory: {candidate}")
    if stat.S_ISREG(root_metadata.st_mode):
        return [candidate]
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise TreeIntegrityError(f"non-regular filesystem entry is not allowed: {candidate}")

    files: list[Path] = []
    pending = [candidate]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                metadata = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(metadata.st_mode):
                    raise TreeIntegrityError(f"symlink is not allowed: {path}")
                if stat.S_ISDIR(metadata.st_mode):
                    pending.append(path)
                elif stat.S_ISREG(metadata.st_mode):
                    files.append(path)
                else:
                    raise TreeIntegrityError(f"non-regular filesystem entry is not allowed: {path}")
    return sorted(files)


def tree_hashes(root: Path) -> dict[str, str]:
    """Hash regular content after enforcing the canonical tree-integrity contract."""

    candidate = lexical_absolute(root)
    files = validate_tree(candidate, require_directory=True)
    hashes: dict[str, str] = {}
    for path in files:
        relative = path.relative_to(candidate)
        if is_runtime_cache(relative):
            continue
        hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes
