from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from contextlib import contextmanager
from collections.abc import Callable, Iterable
from pathlib import Path

from ..repo import REPO_ROOT


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@contextmanager
def release_output_lock(output_dir: Path):
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    lock_path = output_dir.parent / f".{output_dir.name}.release.lock"
    with lock_path.open("a+b") as handle:
        handle.seek(0)
        if handle.read(1) != b"\0":
            handle.seek(0)
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError(f"release output is locked: {output_dir}") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def publish_asset_set(
    staging: Path,
    output_dir: Path,
    names: Iterable[str],
    *,
    force: bool,
    validate_published: Callable[[Path], None] | None = None,
) -> None:
    selected = tuple(names)
    if not selected or len(selected) != len(set(selected)):
        raise ValueError("release asset names must be a non-empty unique sequence")
    for name in selected:
        source = staging / name
        if source.is_symlink() or not source.is_file():
            raise FileNotFoundError(f"staged release asset is missing or unsafe: {source}")
    with release_output_lock(output_dir):
        if output_dir.is_symlink():
            raise ValueError(f"release output directory is unsafe: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        existing = [
            output_dir / name
            for name in selected
            if (output_dir / name).exists() or (output_dir / name).is_symlink()
        ]
        if any(path.is_dir() and not path.is_symlink() for path in existing):
            raise ValueError("release asset destination must not be a directory")
        if existing and not force:
            raise FileExistsError(
                "release assets already exist: "
                + ", ".join(str(path) for path in existing)
            )
        with tempfile.TemporaryDirectory(
            prefix=f".{output_dir.name}.release-backup-", dir=output_dir.parent
        ) as backup_value:
            backup = Path(backup_value)
            moved_existing: list[tuple[Path, Path]] = []
            published: list[Path] = []
            try:
                for destination in existing:
                    backup_path = backup / destination.name
                    destination.replace(backup_path)
                    moved_existing.append((destination, backup_path))
                for name in selected:
                    destination = output_dir / name
                    (staging / name).replace(destination)
                    published.append(destination)
                if validate_published is not None:
                    validate_published(output_dir)
            except BaseException as exc:
                rollback_errors: list[str] = []
                for destination in published:
                    try:
                        destination.unlink(missing_ok=True)
                    except OSError as rollback_exc:
                        rollback_errors.append(str(rollback_exc))
                for destination, backup_path in moved_existing:
                    try:
                        if backup_path.exists() or backup_path.is_symlink():
                            backup_path.replace(destination)
                    except OSError as rollback_exc:
                        rollback_errors.append(str(rollback_exc))
                if rollback_errors:
                    raise RuntimeError(
                        f"release asset publish failed ({exc}); rollback failed: "
                        + "; ".join(rollback_errors)
                    ) from exc
                raise


def repository_version(root: Path = REPO_ROOT) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def repository_head(root: Path = REPO_ROOT) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
