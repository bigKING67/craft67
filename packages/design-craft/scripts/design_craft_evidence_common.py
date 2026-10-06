#!/usr/bin/env python3
"""Shared evidence hashing and Git provenance helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


INSTALL_METADATA = ".design-craft-install.json"
DEFAULT_IGNORED_DIRS = {".git", "__pycache__"}
DEFAULT_IGNORED_FILES = {".DS_Store", INSTALL_METADATA}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def command_version(executable: str) -> str:
    try:
        result = subprocess.run(
            [executable, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"cannot resolve {executable} version: {exc}") from exc
    value = result.stdout.strip()
    if result.returncode != 0 or not value:
        raise RuntimeError(f"cannot resolve {executable} version")
    return value


def run_git_bytes(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.decode("utf-8", errors="replace").strip()
            or f"git {' '.join(args)} failed"
        )
    return result.stdout


def worktree_fingerprint(root: Path) -> str:
    """Hash tracked diffs plus untracked content, including already-dirty files."""

    digest = hashlib.sha256()
    for label, args in (
        (b"status\0", ("status", "--porcelain=v1", "-z", "--untracked-files=all")),
        (b"diff\0", ("diff", "--binary", "--no-ext-diff")),
        (b"cached\0", ("diff", "--cached", "--binary", "--no-ext-diff")),
    ):
        digest.update(label)
        digest.update(run_git_bytes(root, *args))

    untracked = run_git_bytes(root, "ls-files", "--others", "--exclude-standard", "-z")
    for raw_relative in sorted(item for item in untracked.split(b"\0") if item):
        relative = raw_relative.decode("utf-8", errors="surrogateescape")
        path = root / relative
        digest.update(b"untracked\0")
        digest.update(raw_relative)
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0")
            digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
        elif path.is_file():
            digest.update(path.read_bytes())
        else:
            digest.update(b"missing-or-non-file")
    return digest.hexdigest()


def publish_files(files: dict[Path, bytes]) -> None:
    """Stage every evidence file before replacing any destination."""

    staged: dict[Path, Path] = {}
    originals = {path: path.read_bytes() if path.is_file() else None for path in files}
    try:
        for destination, content in files.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            descriptor, raw_stage = tempfile.mkstemp(
                prefix=f".{destination.name}.", dir=destination.parent
            )
            stage = Path(raw_stage)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            staged[destination] = stage
        for destination, stage in staged.items():
            os.replace(stage, destination)
    except OSError:
        for destination, original in originals.items():
            if original is None:
                destination.unlink(missing_ok=True)
            else:
                descriptor, raw_restore = tempfile.mkstemp(
                    prefix=f".{destination.name}.restore.", dir=destination.parent
                )
                restore = Path(raw_restore)
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(original)
                os.replace(restore, destination)
        raise
    finally:
        for stage in staged.values():
            stage.unlink(missing_ok=True)


def snapshot_tree(
    root: Path,
    *,
    ignored_dirs: set[str] | None = None,
    ignored_files: set[str] | None = None,
) -> dict[str, str]:
    ignored_dir_names = DEFAULT_IGNORED_DIRS | set(ignored_dirs or ())
    ignored_file_names = DEFAULT_IGNORED_FILES | set(ignored_files or ())
    values: dict[str, str] = {}
    if not root.is_dir():
        return values
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in ignored_dir_names for part in relative.parts):
            continue
        if not path.is_file() or path.name in ignored_file_names or path.suffix in {".pyc", ".pyo"}:
            continue
        values[relative.as_posix()] = sha256_file(path)
    return values


def digest_snapshot(values: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for relative, file_digest in sorted(values.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def tree_sha256(
    root: Path,
    *,
    ignored_dirs: set[str] | None = None,
    ignored_files: set[str] | None = None,
) -> str:
    return digest_snapshot(
        snapshot_tree(root, ignored_dirs=ignored_dirs, ignored_files=ignored_files)
    )


def files_sha256(root: Path, relative_paths: list[str] | tuple[str, ...]) -> str:
    """Hash a named contract without making unrelated repository files decisive."""
    values: dict[str, str] = {}
    for relative in sorted(relative_paths):
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"contract file is missing: {path}")
        values[relative] = sha256_file(path)
    return digest_snapshot(values)


def git_output(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def git_root(path: Path) -> Path:
    return Path(git_output(path, "rev-parse", "--show-toplevel")).resolve()


def git_head(root: Path) -> str:
    return git_output(root, "rev-parse", "HEAD")


def git_dirty(root: Path, path: Path | None = None) -> bool:
    args = ["status", "--porcelain=v1", "--untracked-files=all"]
    if path is not None:
        resolved_root = root.expanduser().resolve()
        resolved_path = path.expanduser().resolve()
        try:
            relative = resolved_path.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"Git dirty path must stay inside {resolved_root}: {resolved_path}") from exc
        args.extend(("--", relative.as_posix()))
    return bool(git_output(root, *args))


def git_is_ancestor(root: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def git_snapshot_tree(
    root: Path,
    path: Path,
    commit: str,
    *,
    ignored_dirs: set[str] | None = None,
    ignored_files: set[str] | None = None,
) -> dict[str, str]:
    resolved_root = git_root(root.expanduser().resolve())
    resolved_path = path.expanduser().resolve()
    try:
        relative_root = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"Git tree path must stay inside {resolved_root}: {resolved_path}"
        ) from exc

    result = subprocess.run(
        [
            "git",
            "-C",
            str(resolved_root),
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            commit,
            "--",
            relative_root.as_posix(),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )

    ignored_dir_names = DEFAULT_IGNORED_DIRS | set(ignored_dirs or ())
    ignored_file_names = DEFAULT_IGNORED_FILES | set(ignored_files or ())
    prefix = relative_root.as_posix().rstrip("/") + "/"
    values: dict[str, str] = {}
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        repository_path = raw_path.decode("utf-8", errors="strict")
        if not repository_path.startswith(prefix):
            continue
        relative = Path(repository_path[len(prefix) :])
        if any(part in ignored_dir_names for part in relative.parts):
            continue
        if (
            relative.name in ignored_file_names
            or relative.suffix in {".pyc", ".pyo"}
        ):
            continue
        content = subprocess.check_output(
            ["git", "-C", str(resolved_root), "show", f"{commit}:{repository_path}"],
            stderr=subprocess.DEVNULL,
        )
        values[relative.as_posix()] = sha256_bytes(content)
    return values


def git_tree_sha256(
    root: Path,
    path: Path,
    commit: str,
    *,
    ignored_dirs: set[str] | None = None,
    ignored_files: set[str] | None = None,
) -> str:
    return digest_snapshot(
        git_snapshot_tree(
            root,
            path,
            commit,
            ignored_dirs=ignored_dirs,
            ignored_files=ignored_files,
        )
    )


def read_version(skill_root: Path) -> str:
    path = skill_root / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


def redacted_path(path: Path) -> str:
    resolved = path.expanduser().resolve()
    try:
        repository = git_root(resolved)
    except (OSError, RuntimeError, subprocess.CalledProcessError):
        repository = None
    if repository is not None and (repository / "skills/design-craft/SKILL.md").is_file():
        try:
            relative = resolved.relative_to(repository)
        except ValueError:
            pass
        else:
            suffix = relative.as_posix()
            return "$DESIGN_CRAFT_HOME" if suffix == "." else f"$DESIGN_CRAFT_HOME/{suffix}"
    home = Path.home().resolve()
    try:
        relative = resolved.relative_to(home)
    except ValueError:
        return str(resolved)
    return f"~/{relative.as_posix()}"


def skill_provenance(skill_root: Path) -> dict[str, object]:
    skill_root = skill_root.expanduser().resolve()
    digest = tree_sha256(skill_root)
    metadata_path = skill_root / INSTALL_METADATA
    if metadata_path.is_file():
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        schema = payload.get("schema")
        if schema not in {"design-craft.install.v1", "design-craft.install.v2"}:
            raise ValueError(f"unsupported installation metadata schema in {metadata_path}")
        recorded_digest = payload.get("source_tree_sha256")
        if recorded_digest != digest:
            raise ValueError(
                f"installed skill tree hash does not match {metadata_path}: "
                f"expected {recorded_digest}, observed {digest}"
            )
        skill_source_dirty = payload.get(
            "skill_source_dirty", payload.get("source_dirty")
        )
        if not isinstance(skill_source_dirty, bool):
            raise ValueError(f"installation metadata has invalid skill dirty state: {metadata_path}")
        repo_dirty = payload.get("repo_dirty")
        if schema == "design-craft.install.v2" and not isinstance(repo_dirty, bool):
            raise ValueError(f"installation metadata has invalid repo dirty state: {metadata_path}")
        release_state = payload.get("release_state")
        if schema == "design-craft.install.v2" and release_state not in {
            "development",
            "release_candidate",
            "released",
            "unknown",
        }:
            raise ValueError(f"installation metadata has invalid release state: {metadata_path}")
        source_commit = str(payload.get("source_commit", ""))
        if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
            raise ValueError(f"installation metadata has invalid source commit: {metadata_path}")
        source_root_value = payload.get("source_root")
        source_path_value = payload.get("source_path")
        if isinstance(source_root_value, str) and isinstance(source_path_value, str):
            source_root = Path(source_root_value).expanduser().resolve()
            source_path = Path(source_path_value).expanduser().resolve()
            if source_root.is_dir() and source_path.is_dir():
                if not git_is_ancestor(source_root, source_commit):
                    raise ValueError(
                        f"installation source commit is not current history: {metadata_path}"
                    )
                committed_digest = git_tree_sha256(
                    source_root,
                    source_path,
                    source_commit,
                )
                if committed_digest != digest:
                    raise ValueError(
                        f"installation source commit tree does not match {metadata_path}"
                    )
        return {
            "skill_version": str(payload.get("version", "")),
            "skill_source_commit": source_commit,
            "skill_source_dirty": skill_source_dirty,
            "repo_dirty": repo_dirty,
            "release_state": release_state,
            "skill_tree_sha256": digest,
            "skill_path": redacted_path(skill_root),
        }

    root = git_root(skill_root)
    return {
        "skill_version": read_version(skill_root),
        "skill_source_commit": git_head(root),
        "skill_source_dirty": git_dirty(root, skill_root),
        "repo_dirty": git_dirty(root),
        "release_state": "unknown",
        "skill_tree_sha256": digest,
        "skill_path": redacted_path(skill_root),
    }
