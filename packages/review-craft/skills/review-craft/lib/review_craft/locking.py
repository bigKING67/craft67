from __future__ import annotations

import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

if os.name == "nt":
    import msvcrt

    fcntl = None
else:
    import fcntl

    msvcrt = None

LOCK_POLL_SECONDS = 0.05


def _try_lock(handle: BinaryIO) -> bool:
    try:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except (BlockingIOError, OSError):
        return False
    return True


def _unlock(handle: BinaryIO) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    else:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


@contextmanager
def exclusive_file_lock(
    directory: Path,
    *,
    name: str,
    wait_seconds: int,
    timeout_message: str,
) -> Iterator[None]:
    """Hold one cross-process advisory lock inside a controlled session directory."""
    directory = directory.expanduser().resolve(strict=True)
    lock_path = directory / name
    if lock_path.is_symlink():
        raise ValueError(f"session lock must not be a symlink: {name}")
    lock_path.touch(mode=0o600, exist_ok=True)
    with lock_path.open("r+b") as handle:
        if lock_path.stat().st_size == 0:
            handle.write(b"\0")
            handle.flush()
            os.fsync(handle.fileno())
        wait_deadline = time.monotonic() + wait_seconds
        while not _try_lock(handle):
            if time.monotonic() >= wait_deadline:
                raise TimeoutError(timeout_message) from None
            time.sleep(LOCK_POLL_SECONDS)
        try:
            yield
        finally:
            _unlock(handle)
