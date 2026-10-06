#!/usr/bin/env python3
"""Replace byte-identical evidence copies with copy-on-write clones (APFS clonefile / Linux FICLONE)."""

from __future__ import annotations

import collections
import contextlib
import ctypes
import ctypes.util
import errno
import hashlib
import os
import stat
import sys
import uuid
from pathlib import Path
from typing import Any, Callable

from fsutil import sha256_file

SCHEMA = "money-craft.storage-dedupe.v1"
DEFAULT_MIN_BYTES = 64 * 1024
MAX_REPORTED_ERRORS = 50
PREFIX_BYTES = 64 * 1024
LINUX_FICLONE = 0x40049409
UNSUPPORTED_ERRNOS = {errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV, errno.EINVAL, errno.ENOTTY, errno.ENOSYS}


class StorageError(Exception):
    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def _darwin_clone() -> Callable[[Path, Path], None]:
    libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    clonefile = libc.clonefile
    clonefile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32]

    def clone(source: Path, destination: Path) -> None:
        if clonefile(os.fsencode(source), os.fsencode(destination), 1) != 0:  # CLONE_NOFOLLOW
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code))

    return clone


def _linux_clone(source: Path, destination: Path) -> None:
    import fcntl

    with source.open("rb") as reader, destination.open("xb") as writer:
        try:
            fcntl.ioctl(writer.fileno(), LINUX_FICLONE, reader.fileno())
        except OSError:
            writer.close()
            with contextlib.suppress(OSError):  # keep the ioctl errno for classification
                destination.unlink()
            raise


def platform_clone() -> Callable[[Path, Path], None] | None:
    if sys.platform == "darwin":
        return _darwin_clone()
    if sys.platform.startswith("linux"):
        return _linux_clone
    return None


def _is_mutable_area(name: str) -> bool:
    # In-progress tracking workspaces and staging trees may be written concurrently.
    return name == ".working" or ".staging." in name


def _scan(root: Path, min_bytes: int, errors: list[str]) -> tuple[list[tuple[Path, os.stat_result]], int, int]:
    files: list[tuple[Path, os.stat_result]] = []
    scanned = 0
    mutable_skipped = 0
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=lambda _exc: errors.append("unreadable_directory")):
        kept = []
        for name in dirs:
            if os.path.islink(os.path.join(directory, name)):
                continue
            if _is_mutable_area(name):
                mutable_skipped += 1
                continue
            kept.append(name)
        dirs[:] = kept
        for name in names:
            path = Path(directory) / name
            try:
                metadata = path.lstat()
            except OSError:
                errors.append("local_io_error")
                continue
            if not stat.S_ISREG(metadata.st_mode):
                continue
            scanned += 1
            if metadata.st_size >= min_bytes:
                files.append((path, metadata))
    return files, scanned, mutable_skipped


def _prefix_digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.sha256(handle.read(PREFIX_BYTES)).hexdigest()


def _replaceable(path: Path, metadata: os.stat_result) -> bool:
    # Replacing a path swaps its inode: never do that to sealed (read-only) files or directories,
    # files owned by someone else (the clone would change owner/group), or hard-linked files
    # whose other links would keep the old bytes alive. Mode bits are checked explicitly because
    # os.access() is always true for root.
    try:
        parent = path.parent.stat()
    except OSError:
        return False
    owner_ok = not hasattr(os, "geteuid") or metadata.st_uid == os.geteuid()
    return (
        owner_ok
        and metadata.st_nlink == 1
        and bool(metadata.st_mode & stat.S_IWUSR)
        and bool(parent.st_mode & stat.S_IWUSR)
        and os.access(path, os.W_OK)
        and os.access(path.parent, os.W_OK)
    )


def _unchanged(path: Path, metadata: os.stat_result) -> bool:
    current = path.lstat()
    return (current.st_ino, current.st_size, current.st_mtime_ns) == (
        metadata.st_ino, metadata.st_size, metadata.st_mtime_ns
    )


def dedupe(
    root: Path | str,
    *,
    apply: bool = False,
    min_bytes: int = DEFAULT_MIN_BYTES,
    clone: Callable[[Path, Path], None] | None = None,
) -> dict[str, Any]:
    root = Path(os.path.abspath(Path(root).expanduser()))
    if root.is_symlink() or not root.is_dir():
        raise StorageError("invalid_root", "storage root must be an existing, non-symlinked directory")
    if min_bytes < 1:
        raise StorageError("usage_error", "min-bytes must be positive")
    clone = clone or platform_clone()
    if apply and clone is None:
        raise StorageError("unsupported_platform", "copy-on-write clones are unavailable on this platform")

    error_kinds: list[str] = []
    files, scanned, mutable_skipped = _scan(root, min_bytes, error_kinds)
    errors: list[dict[str, str]] = []

    def record(path: Path | None, kind: str) -> None:
        error_kinds.append(kind)
        if path is not None and len(errors) < MAX_REPORTED_ERRORS:
            errors.append({"path": str(path.relative_to(root)), "kind": kind})

    # One representative path per inode; hard links to the same inode are already shared.
    by_inode: dict[tuple[int, int], tuple[Path, os.stat_result]] = {}
    for path, metadata in sorted(files, key=lambda item: str(item[0])):
        by_inode.setdefault((metadata.st_dev, metadata.st_ino), (path, metadata))
    by_size: dict[tuple[int, int], list[tuple[Path, os.stat_result]]] = collections.defaultdict(list)
    for path, metadata in by_inode.values():
        by_size[(metadata.st_dev, metadata.st_size)].append((path, metadata))

    groups = 0
    cloned = 0
    duplicate_bytes = 0
    not_replaceable = 0
    unsupported = False
    for (_device, size), candidates in sorted(by_size.items()):
        if unsupported:
            break
        if len(candidates) < 2:
            continue
        digests: dict[str, list[tuple[Path, os.stat_result]]] = collections.defaultdict(list)
        prefixes: dict[str, list[tuple[Path, os.stat_result]]] = collections.defaultdict(list)
        for path, metadata in candidates:
            try:
                prefixes[_prefix_digest(path)].append((path, metadata))
            except OSError:
                record(path, "local_io_error")
        for same_prefix in prefixes.values():
            if len(same_prefix) < 2:
                continue
            for path, metadata in same_prefix:
                try:
                    digests[sha256_file(path)].append((path, metadata))
                except OSError:
                    record(path, "local_io_error")
        for digest, members in digests.items():
            if len(members) < 2:
                continue
            # Prefer a sealed copy as the clone source: it is the one guaranteed not to change.
            members.sort(key=lambda item: (_replaceable(*item), str(item[0])))
            keeper, keeper_meta = members[0]
            targets = []
            for path, metadata in members[1:]:
                if _replaceable(path, metadata):
                    targets.append((path, metadata))
                else:
                    not_replaceable += 1
            if not targets:
                continue
            groups += 1
            for path, metadata in targets:
                if not apply:
                    cloned += 1
                    duplicate_bytes += size
                    continue
                if unsupported:
                    break
                temporary = path.with_name(f".{path.name}.dedup-{uuid.uuid4().hex}")
                try:
                    if not _unchanged(keeper, keeper_meta) or not _unchanged(path, metadata):
                        record(path, "changed_during_scan")
                        continue
                    clone(keeper, temporary)
                    if sha256_file(temporary) != digest:
                        raise StorageError("changed_during_scan", "clone does not match hashed content")
                    os.chmod(temporary, stat.S_IMODE(metadata.st_mode))
                    os.utime(temporary, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
                    os.replace(temporary, path)
                    cloned += 1
                    duplicate_bytes += size
                except StorageError as exc:
                    record(path, exc.kind)
                except OSError as exc:
                    if exc.errno in UNSUPPORTED_ERRNOS:
                        unsupported = True
                        record(None, "clone_unsupported")
                    else:
                        record(path, "local_io_error")
                finally:
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError:
                        record(path, "cleanup_failed")

    return {
        "schema": SCHEMA,
        "valid": not error_kinds,
        "applied": apply,
        "method": "copy-on-write-clone",
        "min_bytes": min_bytes,
        "scanned_files": scanned,
        "mutable_areas_skipped": mutable_skipped,
        "non_replaceable_copies": not_replaceable,
        "duplicate_groups": groups,
        "clones_created" if apply else "clones_planned": cloned,
        # Clone sharing is invisible to stat/du, so previously cloned copies are counted again.
        "duplicate_bytes": duplicate_bytes,
        "error_count": len(error_kinds),
        "error_kinds": dict(sorted(collections.Counter(error_kinds).items())),
        "errors": errors,
    }
