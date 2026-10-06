#!/usr/bin/env python3
"""Create disposable Git snapshots without writing to the source repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


MANIFEST_SCHEMA = "design-craft.shadow-lab-manifest.v1"
ROOT_SCHEMA = "design-craft.shadow-lab-root.v1"
VERIFICATION_SCHEMA = "design-craft.shadow-lab-verification.v1"
CLEANUP_SCHEMA = "design-craft.shadow-lab-cleanup.v1"
MANIFEST_NAME = ".design-craft-shadow-lab.json"
ROOT_MARKER_NAME = ".design-craft-shadow-root.json"
RUNTIME_EVIDENCE_SCHEMA = "design-craft.runtime-evidence.v1"
RUNTIME_EVIDENCE_DIR = ".design-craft-runtime-evidence"
DEFAULT_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_FILES = 50_000
DEFAULT_MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
GIT_TIMEOUT_SECONDS = 120
DEFAULT_EXECUTION_TIMEOUT_SECONDS = 3600
MAX_EXECUTION_TIMEOUT_SECONDS = 7200
NETWORK_POLICIES = {"denied", "install_only", "allowed"}
NETWORK_MODES = {"denied", "allowed"}
EXECUTION_PHASES = {"install", "build", "test", "preview", "capture", "custom"}


class ShadowLabError(RuntimeError):
    """Expected safety or contract failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_timestamp(value: Any, *, label: str) -> None:
    if not isinstance(value, str) or "T" not in value:
        raise ShadowLabError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ShadowLabError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ShadowLabError(f"{label} must include a UTC offset")


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.absolute()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{secrets.token_hex(8)}.tmp"
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(json_text(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def run_git(
    source: Path,
    *arguments: str,
    allow_returncodes: Iterable[int] = (0,),
) -> bytes:
    command = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "core.hooksPath=/dev/null",
        *arguments,
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=source,
            env=git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise ShadowLabError(
            f"git command timed out after {GIT_TIMEOUT_SECONDS}s: {' '.join(command)}"
        ) from exc
    allowed = set(allow_returncodes)
    if completed.returncode not in allowed:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ShadowLabError(
            f"git command failed ({completed.returncode}): {' '.join(command)}"
            + (f": {message}" if message else "")
        )
    return completed.stdout


def resolve_source(source: Path) -> Path:
    candidate = source.expanduser().resolve(strict=True)
    if not candidate.is_dir():
        raise ShadowLabError(f"source is not a directory: {candidate}")
    root_text = run_git(candidate, "rev-parse", "--show-toplevel").decode().strip()
    root = Path(root_text).resolve(strict=True)
    if candidate != root:
        raise ShadowLabError(
            f"source must be the Git repository root: source={candidate} root={root}"
        )
    return root


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def ensure_disjoint(source: Path, output_root: Path) -> None:
    if source == output_root:
        raise ShadowLabError("output root must not equal the source repository")
    if is_relative_to(output_root, source):
        raise ShadowLabError("output root must not be inside the source repository")
    if is_relative_to(source, output_root):
        raise ShadowLabError("output root must not contain the source repository")


def parse_porcelain_z(raw: bytes) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    parts = raw.split(b"\0")
    index = 0
    while index < len(parts):
        value = parts[index]
        index += 1
        if not value:
            continue
        if len(value) < 4 or value[2:3] != b" ":
            raise ShadowLabError("unexpected Git porcelain status entry")
        status_code = value[:2].decode("ascii", errors="replace")
        path = os.fsdecode(value[3:])
        entry = {"status": status_code, "path": path}
        if "R" in status_code or "C" in status_code:
            if index >= len(parts) or not parts[index]:
                raise ShadowLabError("rename/copy status is missing its source path")
            entry["source_path"] = os.fsdecode(parts[index])
            index += 1
        entries.append(entry)
    return entries


def safe_status_path(source: Path, value: str) -> Path | None:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved_parent = (source / candidate).parent.resolve(strict=False)
    if not is_relative_to(resolved_parent, source):
        return None
    return source / candidate


def dirty_metadata(entries: list[dict[str, str]], source: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    paths = {
        value
        for entry in entries
        for value in (entry.get("path"), entry.get("source_path"))
        if value
    }
    for value in sorted(paths):
        path = safe_status_path(source, value)
        if path is None:
            records.append({"path": value, "state": "unsafe"})
            continue
        try:
            info = path.lstat()
        except FileNotFoundError:
            records.append({"path": value, "state": "missing"})
            continue
        records.append(
            {
                "path": value,
                "state": "present",
                "mode": stat.S_IFMT(info.st_mode),
                "size": info.st_size,
                "mtime_ns": info.st_mtime_ns,
            }
        )
    encoded = json.dumps(records, ensure_ascii=True, sort_keys=True).encode("utf-8")
    return {"sha256": sha256_bytes(encoded), "records": records}


def git_index_metadata(source: Path) -> dict[str, Any]:
    git_dir_text = run_git(source, "rev-parse", "--absolute-git-dir").decode().strip()
    index_path = Path(git_dir_text) / "index"
    try:
        info = index_path.lstat()
    except FileNotFoundError:
        return {"present": False, "size": 0, "mtime_ns": 0}
    return {"present": True, "size": info.st_size, "mtime_ns": info.st_mtime_ns}


def source_state(source: Path) -> dict[str, Any]:
    head = run_git(source, "rev-parse", "HEAD").decode().strip()
    branch_bytes = run_git(
        source,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
        allow_returncodes=(0, 1),
    )
    branch = branch_bytes.decode().strip() or None
    status_raw = run_git(
        source,
        "-c",
        "core.quotepath=false",
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignore-submodules=none",
    )
    entries = parse_porcelain_z(status_raw)
    diff_raw = run_git(
        source,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--binary",
        "HEAD",
        "--",
    )
    metadata = dirty_metadata(entries, source)
    return {
        "head": head,
        "branch": branch,
        "status_sha256": sha256_bytes(status_raw),
        "tracked_diff_sha256": sha256_bytes(diff_raw),
        "dirty_entry_count": len(entries),
        "dirty_entries": entries,
        "dirty_metadata_sha256": metadata["sha256"],
        "git_index": git_index_metadata(source),
        "untracked_content_read": False,
    }


def sanitize_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug or "source"


def default_output_root() -> Path:
    return Path(tempfile.gettempdir()) / "design-craft-shadow-labs"


def validate_output_root_permissions(
    root_info: os.stat_result,
    *,
    platform_name: str = os.name,
    current_uid: int | None = None,
) -> None:
    if platform_name == "nt":
        return
    if current_uid is None and hasattr(os, "getuid"):
        current_uid = os.getuid()
    if current_uid is not None and root_info.st_uid != current_uid:
        raise ShadowLabError("output root must be owned by the current user")
    if stat.S_IMODE(root_info.st_mode) & 0o077:
        raise ShadowLabError(
            "output root permissions must not allow group or other access"
        )


def prepare_output_root(output_root: Path) -> dict[str, Any]:
    expanded = output_root.expanduser().absolute()
    if expanded.is_symlink():
        raise ShadowLabError("output root must not be a symlink")
    output_root = expanded.resolve(strict=False)
    output_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root_info = output_root.lstat()
    if not stat.S_ISDIR(root_info.st_mode):
        raise ShadowLabError("output root must be a directory")
    validate_output_root_permissions(root_info)
    marker_path = output_root / ROOT_MARKER_NAME
    if marker_path.exists():
        if marker_path.is_symlink() or not marker_path.is_file():
            raise ShadowLabError("shadow root marker must be a regular file")
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if marker.get("schema") != ROOT_SCHEMA:
            raise ShadowLabError("shadow root marker has an unsupported schema")
        if Path(marker.get("root", "")).resolve(strict=False) != output_root:
            raise ShadowLabError("shadow root marker path does not match its directory")
        if not isinstance(marker.get("root_id"), str) or not marker["root_id"]:
            raise ShadowLabError("shadow root marker is missing root_id")
        return marker
    if any(output_root.iterdir()):
        raise ShadowLabError(
            "output root is non-empty and has no design-craft ownership marker"
        )
    marker = {
        "schema": ROOT_SCHEMA,
        "root": str(output_root),
        "root_id": secrets.token_hex(16),
        "created_at": utc_now(),
    }
    atomic_write_json(marker_path, marker)
    os.chmod(marker_path, 0o600)
    return marker


def fixed_commit(source: Path, requested_ref: str) -> str:
    value = run_git(source, "rev-parse", "--verify", f"{requested_ref}^{{commit}}")
    return value.decode().strip()


def special_git_entries(source: Path, commit: str) -> dict[str, list[str]]:
    raw = run_git(source, "ls-tree", "-r", "-z", commit)
    symlinks: list[str] = []
    submodules: list[str] = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        metadata, separator, path_bytes = entry.partition(b"\t")
        if not separator:
            raise ShadowLabError("unexpected git ls-tree entry")
        fields = metadata.split()
        if len(fields) < 3:
            raise ShadowLabError("unexpected git ls-tree metadata")
        mode = fields[0]
        path = os.fsdecode(path_bytes)
        if mode == b"120000":
            symlinks.append(path)
        elif mode == b"160000":
            submodules.append(path)
    return {"symlinks": symlinks, "submodules": submodules}


def safe_member_parts(name: str) -> tuple[str, ...]:
    if not name or "\\" in name:
        raise ShadowLabError(f"archive member has an unsafe path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ShadowLabError(f"archive member has an unsafe path: {name!r}")
    if re.match(r"^[A-Za-z]:", name):
        raise ShadowLabError(f"archive member has a drive path: {name!r}")
    return path.parts


def inspect_archive(
    archive_path: Path,
    *,
    max_files: int,
    max_total_bytes: int,
) -> tuple[list[tarfile.TarInfo], int, int]:
    members: list[tarfile.TarInfo] = []
    paths: set[str] = set()
    entry_count = 0
    file_count = 0
    total_bytes = 0
    try:
        with tarfile.open(archive_path, mode="r:") as archive:
            for member in archive:
                entry_count += 1
                if entry_count > max_files:
                    raise ShadowLabError(
                        f"archive exceeds max entry count: {entry_count} > {max_files}"
                    )
                safe_member_parts(member.name)
                if member.name in paths:
                    raise ShadowLabError(f"archive contains duplicate path: {member.name}")
                paths.add(member.name)
                if not (member.isdir() or member.isfile()):
                    raise ShadowLabError(
                        f"archive member must be a regular file or directory: {member.name}"
                    )
                if member.isfile():
                    file_count += 1
                    total_bytes += member.size
                    if total_bytes > max_total_bytes:
                        raise ShadowLabError(
                            "archive exceeds max extracted bytes: "
                            f"{total_bytes} > {max_total_bytes}"
                        )
                members.append(member)
    except tarfile.TarError as exc:
        raise ShadowLabError(f"cannot inspect Git archive: {exc}") from exc
    return members, file_count, total_bytes


def extract_archive(
    archive_path: Path,
    destination: Path,
    members: list[tarfile.TarInfo],
) -> None:
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    with tarfile.open(archive_path, mode="r:") as archive:
        for member in members:
            parts = safe_member_parts(member.name)
            target = destination.joinpath(*parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o755)
                continue
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            source_file = archive.extractfile(member)
            if source_file is None:
                raise ShadowLabError(f"cannot read archive member: {member.name}")
            with source_file, target.open("xb") as output:
                shutil.copyfileobj(source_file, output, length=1024 * 1024)
            os.chmod(target, 0o755 if member.mode & 0o111 else 0o644)


def tree_fingerprint(
    root: Path,
    *,
    allow_internal_symlinks: bool = False,
) -> dict[str, Any]:
    if not root.is_dir() or root.is_symlink():
        raise ShadowLabError(f"lab worktree must be a real directory: {root}")
    digest = hashlib.sha256()
    file_count = 0
    symlink_count = 0
    total_bytes = 0
    for current_root, directories, files in os.walk(root, followlinks=False):
        current = Path(current_root)
        directories.sort()
        files.sort()
        symlinked_directories: list[str] = []
        for name in directories:
            path = current / name
            if path.is_symlink():
                symlinked_directories.append(name)
        directories[:] = [name for name in directories if name not in symlinked_directories]
        for name in [*symlinked_directories, *files]:
            path = current / name
            if not path.is_symlink():
                continue
            if not allow_internal_symlinks:
                raise ShadowLabError(f"lab worktree contains a symlink: {path}")
            target = os.readlink(path)
            if os.path.isabs(target):
                raise ShadowLabError(f"lab worktree symlink escapes the lab: {path}")
            resolved_target = (path.parent / target).resolve(strict=False)
            if not is_relative_to(resolved_target, root):
                raise ShadowLabError(f"lab worktree symlink escapes the lab: {path}")
            relative = path.relative_to(root).as_posix()
            info = path.lstat()
            digest.update(relative.encode("utf-8", errors="surrogateescape"))
            digest.update(b"\0L\0")
            digest.update(str(stat.S_IMODE(info.st_mode)).encode())
            digest.update(b"\0")
            digest.update(os.fsencode(target))
            digest.update(b"\0")
            symlink_count += 1
        for name in files:
            path = current / name
            if path.is_symlink():
                continue
            relative = path.relative_to(root).as_posix()
            info = path.stat()
            if not stat.S_ISREG(info.st_mode):
                raise ShadowLabError(f"lab worktree contains a special file: {path}")
            digest.update(relative.encode("utf-8", errors="surrogateescape"))
            digest.update(b"\0")
            digest.update(str(stat.S_IMODE(info.st_mode)).encode())
            digest.update(b"\0")
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
                    total_bytes += len(chunk)
            digest.update(b"\0")
            file_count += 1
    return {
        "sha256": digest.hexdigest(),
        "file_count": file_count,
        "symlink_count": symlink_count,
        "total_bytes": total_bytes,
    }


def prepare_lab(
    *,
    source_path: Path,
    requested_ref: str,
    output_root_path: Path,
    max_archive_bytes: int = DEFAULT_MAX_ARCHIVE_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    network_policy: str = "denied",
    network_authorization: str = "shadow_lab_default",
) -> dict[str, Any]:
    if network_policy not in NETWORK_POLICIES:
        raise ShadowLabError(f"unsupported network policy: {network_policy}")
    if network_authorization not in {"shadow_lab_default", "caller_declared"}:
        raise ShadowLabError(
            f"unsupported network authorization source: {network_authorization}"
        )
    source = resolve_source(source_path)
    requested_output_root = output_root_path.expanduser().absolute()
    output_root = requested_output_root.resolve(strict=False)
    ensure_disjoint(source, output_root)
    root_marker = prepare_output_root(requested_output_root)
    output_root = Path(root_marker["root"]).resolve(strict=True)
    commit = fixed_commit(source, requested_ref)
    special = special_git_entries(source, commit)
    if special["symlinks"]:
        raise ShadowLabError(
            "fixed commit contains unsupported symlinks: "
            + ", ".join(special["symlinks"][:5])
        )
    if special["submodules"]:
        raise ShadowLabError(
            "fixed commit contains unsupported submodules: "
            + ", ".join(special["submodules"][:5])
        )

    before = source_state(source)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lab_id = (
        f"{sanitize_slug(source.name)}-{commit[:12]}-{stamp}-{secrets.token_hex(4)}"
    )
    lab_dir = output_root / lab_id
    worktree = lab_dir / "source"
    manifest_path = lab_dir / MANIFEST_NAME
    archive_path = lab_dir / ".snapshot.tar"
    lab_dir.mkdir(mode=0o700)
    try:
        run_git(
            source,
            "archive",
            "--format=tar",
            f"--output={archive_path}",
            commit,
        )
        archive_bytes = archive_path.stat().st_size
        if archive_bytes > max_archive_bytes:
            raise ShadowLabError(
                f"Git archive exceeds max bytes: {archive_bytes} > {max_archive_bytes}"
            )
        members, expected_files, expected_bytes = inspect_archive(
            archive_path,
            max_files=max_files,
            max_total_bytes=max_total_bytes,
        )
        extract_archive(archive_path, worktree, members)
        snapshot = tree_fingerprint(worktree)
        if snapshot["file_count"] != expected_files:
            raise ShadowLabError("extracted file count does not match inspected archive")
        if snapshot["total_bytes"] != expected_bytes:
            raise ShadowLabError("extracted byte count does not match inspected archive")
        after = source_state(source)
        if before != after:
            raise ShadowLabError("source Git state changed while preparing the shadow lab")

        manifest = {
            "schema": MANIFEST_SCHEMA,
            "lab_id": lab_id,
            "created_at": utc_now(),
            "state": "prepared",
            "source": {
                "repo_path": str(source),
                "requested_ref": requested_ref,
                "commit": commit,
                "baseline": before,
                "snapshot_mode": "git-archive-fixed-commit",
            },
            "isolation": {
                "source_writes_allowed": False,
                # Legacy field: the helper itself grants no network authority.
                # Execution truth lives in network_boundary plus phase receipts.
                "network_allowed": False,
                "network_boundary": {
                    "policy": network_policy,
                    "authorization": network_authorization,
                    "enforcement": "phase_receipts_required",
                    "observation": "phase_receipts",
                    "evidence_status": "pending",
                },
                "untracked_content_included": False,
                "output_root": str(output_root),
                "root_id": root_marker["root_id"],
                "lab_dir": str(lab_dir),
                "worktree": str(worktree),
                "manifest_path": str(manifest_path),
                "source_and_output_disjoint": True,
            },
            "snapshot": {
                **snapshot,
                "archive_bytes": archive_bytes,
                "symlink_count": 0,
                "submodule_count": 0,
            },
        }
        atomic_write_json(manifest_path, manifest)
        os.chmod(manifest_path, 0o600)
        return {
            "ok": True,
            "action": "prepare",
            "manifest": manifest,
        }
    except Exception:
        shutil.rmtree(lab_dir, ignore_errors=True)
        raise
    finally:
        archive_path.unlink(missing_ok=True)


def load_manifest(manifest_path: Path) -> tuple[Path, dict[str, Any]]:
    path = manifest_path.expanduser().absolute()
    if path.name != MANIFEST_NAME:
        raise ShadowLabError(f"manifest must be named {MANIFEST_NAME}")
    if path.is_symlink() or not path.is_file():
        raise ShadowLabError("manifest must be an existing regular file")
    if path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ShadowLabError("manifest exceeds the maximum supported size")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != MANIFEST_SCHEMA:
        raise ShadowLabError("manifest has an unsupported schema")
    if not isinstance(payload.get("source"), dict):
        raise ShadowLabError("manifest source must be an object")
    if not isinstance(payload.get("isolation"), dict):
        raise ShadowLabError("manifest isolation must be an object")
    return path, payload


def verify_ownership(manifest_path: Path, manifest: dict[str, Any]) -> dict[str, Path]:
    isolation = manifest.get("isolation")
    if not isinstance(isolation, dict):
        raise ShadowLabError("manifest isolation must be an object")
    output_root = Path(str(isolation.get("output_root", ""))).resolve(strict=True)
    lab_dir = Path(str(isolation.get("lab_dir", ""))).absolute()
    worktree = Path(str(isolation.get("worktree", ""))).absolute()
    declared_manifest = Path(str(isolation.get("manifest_path", ""))).absolute()
    if output_root.is_symlink() or lab_dir.is_symlink() or worktree.is_symlink():
        raise ShadowLabError("shadow lab ownership paths must not be symlinks")
    if lab_dir.parent.resolve(strict=True) != output_root:
        raise ShadowLabError("lab directory must be a direct child of its output root")
    if manifest_path != declared_manifest or manifest_path.parent != lab_dir:
        raise ShadowLabError("manifest path does not match the owned lab directory")
    if worktree.parent != lab_dir or worktree.name != "source":
        raise ShadowLabError("lab worktree path does not match the owned layout")
    root_marker_path = output_root / ROOT_MARKER_NAME
    if root_marker_path.is_symlink() or not root_marker_path.is_file():
        raise ShadowLabError("shadow root ownership marker is missing")
    root_marker = json.loads(root_marker_path.read_text(encoding="utf-8"))
    if root_marker.get("schema") != ROOT_SCHEMA:
        raise ShadowLabError("shadow root marker has an unsupported schema")
    if root_marker.get("root_id") != isolation.get("root_id"):
        raise ShadowLabError("shadow root ownership id does not match the manifest")
    if Path(str(root_marker.get("root", ""))).resolve(strict=True) != output_root:
        raise ShadowLabError("shadow root marker path does not match")
    source_payload = manifest.get("source")
    if not isinstance(source_payload, dict):
        raise ShadowLabError("manifest source must be an object")
    source = Path(str(source_payload.get("repo_path", ""))).resolve(strict=True)
    ensure_disjoint(source, output_root)
    return {
        "output_root": output_root,
        "lab_dir": lab_dir,
        "worktree": worktree,
        "source": source,
    }


def state_differences(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    keys = sorted(set(before) | set(after))
    return [key for key in keys if before.get(key) != after.get(key)]


def _network_mode_allowed(policy: str, phase: str, mode: str) -> bool:
    if mode == "denied":
        return True
    if policy == "allowed":
        return True
    return policy == "install_only" and phase == "install"


def _network_denied_command(
    command: list[str],
    *,
    platform_name: str | None = None,
    sandbox_path: Path = Path("/usr/bin/sandbox-exec"),
) -> tuple[list[str], str]:
    platform_name = platform_name or sys.platform
    if platform_name == "darwin" and sandbox_path.is_file():
        profile = "(version 1)(allow default)(deny network-outbound)"
        return [str(sandbox_path), "-p", profile, *command], "macos_sandbox_exec_egress"
    raise ShadowLabError(
        "network-denied enforcement is unavailable on this host; "
        "refusing to execute without a real enforcer"
    )


def _runtime_evidence_directory(lab_dir: Path) -> Path:
    path = lab_dir / RUNTIME_EVIDENCE_DIR
    if path.exists() and (path.is_symlink() or not path.is_dir()):
        raise ShadowLabError("runtime evidence path must be a real directory")
    path.mkdir(mode=0o700, exist_ok=True)
    return path


def _validate_evidence_id(value: str) -> str:
    if re.fullmatch(r"[a-z0-9][a-z0-9-]*", value) is None:
        raise ShadowLabError("evidence id must be a lowercase slug")
    return value


def _execution_receipt(
    path: Path,
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    owned: dict[str, Path],
) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ShadowLabError(f"runtime receipt must be a regular file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected_fields = {
        "schema",
        "kind",
        "id",
        "started_at",
        "completed_at",
        "authority",
        "phase",
        "enforcement",
        "command",
        "outputs",
        "source_audit",
        "status",
    }
    if not isinstance(payload, dict) or set(payload) != expected_fields:
        raise ShadowLabError(f"runtime receipt fields are invalid: {path}")
    if payload["schema"] != RUNTIME_EVIDENCE_SCHEMA or payload["kind"] != "shadow_command":
        raise ShadowLabError(f"runtime receipt schema or kind is invalid: {path}")
    _validate_evidence_id(payload.get("id", ""))
    validate_timestamp(payload.get("started_at"), label="runtime receipt.started_at")
    validate_timestamp(payload.get("completed_at"), label="runtime receipt.completed_at")
    authority = payload.get("authority")
    if not isinstance(authority, dict) or set(authority) != {
        "shadow_lab_manifest",
        "source_commit",
        "worktree",
    }:
        raise ShadowLabError(f"runtime receipt authority is invalid: {path}")
    expected_manifest = file_record(manifest_path)
    if authority["shadow_lab_manifest"] != expected_manifest:
        raise ShadowLabError(f"runtime receipt manifest binding is invalid: {path}")
    if authority["source_commit"] != manifest.get("source", {}).get("commit"):
        raise ShadowLabError(f"runtime receipt commit binding is invalid: {path}")
    if authority["worktree"] != str(owned["worktree"]):
        raise ShadowLabError(f"runtime receipt worktree binding is invalid: {path}")
    phase = payload.get("phase")
    if not isinstance(phase, dict) or set(phase) != {"kind", "network_mode"}:
        raise ShadowLabError(f"runtime receipt phase is invalid: {path}")
    if phase["kind"] not in EXECUTION_PHASES or phase["network_mode"] not in NETWORK_MODES:
        raise ShadowLabError(f"runtime receipt phase values are invalid: {path}")
    enforcement = payload.get("enforcement")
    if not isinstance(enforcement, dict) or set(enforcement) != {"kind", "status"}:
        raise ShadowLabError(f"runtime receipt enforcement is invalid: {path}")
    if phase["network_mode"] == "denied":
        if enforcement != {
            "kind": "macos_sandbox_exec_egress",
            "status": "enforced",
        }:
            raise ShadowLabError(f"runtime receipt lacks denied-network enforcement: {path}")
    elif enforcement != {"kind": "not_required", "status": "not_required"}:
        raise ShadowLabError(f"runtime receipt allowed-network enforcement is invalid: {path}")
    command = payload.get("command")
    if not isinstance(command, dict) or set(command) != {
        "executable",
        "argv_sha256",
        "exit_code",
    }:
        raise ShadowLabError(f"runtime receipt command is invalid: {path}")
    if (
        not isinstance(command["executable"], str)
        or not command["executable"]
        or not isinstance(command["argv_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", command["argv_sha256"]) is None
        or isinstance(command["exit_code"], bool)
        or not isinstance(command["exit_code"], int)
    ):
        raise ShadowLabError(f"runtime receipt command values are invalid: {path}")
    outputs = payload.get("outputs")
    if not isinstance(outputs, dict) or set(outputs) != {"stdout", "stderr"}:
        raise ShadowLabError(f"runtime receipt outputs are invalid: {path}")
    for name in ("stdout", "stderr"):
        record = outputs[name]
        if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
            raise ShadowLabError(f"runtime receipt {name} record is invalid: {path}")
        output_path = Path(str(record["path"])).absolute()
        if output_path.parent != path.parent or output_path.is_symlink() or not output_path.is_file():
            raise ShadowLabError(f"runtime receipt {name} path is invalid: {path}")
        if record != file_record(output_path):
            raise ShadowLabError(f"runtime receipt {name} hash is invalid: {path}")
    source_audit = payload.get("source_audit")
    if not isinstance(source_audit, dict) or set(source_audit) != {
        "source_unchanged",
        "difference_fields",
    }:
        raise ShadowLabError(f"runtime receipt source audit is invalid: {path}")
    if (
        not isinstance(source_audit["source_unchanged"], bool)
        or not isinstance(source_audit["difference_fields"], list)
        or any(
            not isinstance(field, str) or not field
            for field in source_audit["difference_fields"]
        )
        or len(source_audit["difference_fields"])
        != len(set(source_audit["difference_fields"]))
    ):
        raise ShadowLabError(f"runtime receipt source audit values are invalid: {path}")
    if source_audit["source_unchanged"] != (not source_audit["difference_fields"]):
        raise ShadowLabError(f"runtime receipt source audit is inconsistent: {path}")
    if payload["status"] not in {"pass", "fail"}:
        raise ShadowLabError(f"runtime receipt status is invalid: {path}")
    expected_status = (
        "pass"
        if command["exit_code"] == 0
        and source_audit["source_unchanged"]
        and not source_audit["difference_fields"]
        else "fail"
    )
    if payload["status"] != expected_status:
        raise ShadowLabError(f"runtime receipt status is inconsistent: {path}")
    return payload


def runtime_evidence_summary(
    manifest_path: Path,
    manifest: dict[str, Any],
    owned: dict[str, Path],
) -> dict[str, Any]:
    boundary = manifest.get("isolation", {}).get("network_boundary")
    if not isinstance(boundary, dict):
        boundary = {
            "policy": "denied",
            "authorization": "shadow_lab_default",
            "enforcement": "phase_receipts_required",
            "observation": "phase_receipts",
            "evidence_status": "pending",
        }
    expected_boundary_fields = {
        "policy",
        "authorization",
        "enforcement",
        "observation",
        "evidence_status",
    }
    if set(boundary) != expected_boundary_fields:
        raise ShadowLabError("network boundary fields are invalid")
    policy = boundary.get("policy")
    if (
        policy not in NETWORK_POLICIES
        or boundary.get("authorization")
        not in {"shadow_lab_default", "caller_declared"}
        or boundary.get("enforcement") != "phase_receipts_required"
        or boundary.get("observation") != "phase_receipts"
        or boundary.get("evidence_status") != "pending"
    ):
        raise ShadowLabError("network boundary values are invalid")
    evidence_dir = owned["lab_dir"] / RUNTIME_EVIDENCE_DIR
    receipts: list[dict[str, Any]] = []
    if evidence_dir.exists():
        if evidence_dir.is_symlink() or not evidence_dir.is_dir():
            raise ShadowLabError("runtime evidence path must be a real directory")
        for path in sorted(evidence_dir.glob("*.json")):
            receipt = _execution_receipt(
                path,
                manifest_path=manifest_path,
                manifest=manifest,
                owned=owned,
            )
            if not _network_mode_allowed(
                policy,
                receipt["phase"]["kind"],
                receipt["phase"]["network_mode"],
            ):
                raise ShadowLabError(
                    f"runtime receipt violates network policy: {path}"
                )
            receipts.append(
                {
                    "id": receipt["id"],
                    "phase": receipt["phase"]["kind"],
                    "network_mode": receipt["phase"]["network_mode"],
                    "status": receipt["status"],
                    "receipt_path": str(path),
                }
            )
    ids = [receipt["id"] for receipt in receipts]
    if len(ids) != len(set(ids)):
        raise ShadowLabError("runtime evidence ids must be unique")
    evidence_status = (
        "unverified"
        if not receipts
        else "observed"
        if all(receipt["status"] == "pass" for receipt in receipts)
        else "failed"
    )
    return {
        "policy": policy,
        "authorization": boundary.get("authorization"),
        "enforcement": boundary.get("enforcement"),
        "observation": boundary.get("observation"),
        "evidence_status": evidence_status,
        "receipt_count": len(receipts),
        "receipts": receipts,
    }


def execute_in_lab(
    *,
    manifest_path: Path,
    evidence_id: str,
    phase: str,
    network_mode: str,
    command: list[str],
    timeout_seconds: int = DEFAULT_EXECUTION_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    evidence_id = _validate_evidence_id(evidence_id)
    if phase not in EXECUTION_PHASES:
        raise ShadowLabError(f"unsupported execution phase: {phase}")
    if network_mode not in NETWORK_MODES:
        raise ShadowLabError(f"unsupported network mode: {network_mode}")
    if not command:
        raise ShadowLabError("execute requires a command after --")
    if timeout_seconds < 1 or timeout_seconds > MAX_EXECUTION_TIMEOUT_SECONDS:
        raise ShadowLabError(
            f"execution timeout must be between 1 and {MAX_EXECUTION_TIMEOUT_SECONDS} seconds"
        )
    path, manifest = load_manifest(manifest_path)
    owned = verify_ownership(path, manifest)
    policy = manifest.get("isolation", {}).get("network_boundary", {}).get(
        "policy", "denied"
    )
    if not _network_mode_allowed(policy, phase, network_mode):
        raise ShadowLabError(
            f"network mode {network_mode} is not allowed for phase {phase} under policy {policy}"
        )
    evidence_dir = _runtime_evidence_directory(owned["lab_dir"])
    receipt_path = evidence_dir / f"{evidence_id}.json"
    stdout_path = evidence_dir / f"{evidence_id}.stdout.log"
    stderr_path = evidence_dir / f"{evidence_id}.stderr.log"
    if any(candidate.exists() for candidate in (receipt_path, stdout_path, stderr_path)):
        raise ShadowLabError(f"runtime evidence id already exists: {evidence_id}")
    before = source_state(owned["source"])
    manifest_before = file_record(path)
    execution_command = list(command)
    if network_mode == "denied":
        execution_command, enforcement_kind = _network_denied_command(command)
        enforcement = {"kind": enforcement_kind, "status": "enforced"}
    else:
        enforcement = {"kind": "not_required", "status": "not_required"}
    started_at = utc_now()
    timed_out = False
    with stdout_path.open("xb") as stdout_handle, stderr_path.open("xb") as stderr_handle:
        try:
            completed = subprocess.run(
                execution_command,
                cwd=owned["worktree"],
                env=dict(os.environ),
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                check=False,
                timeout=timeout_seconds,
            )
            exit_code = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = 124
    completed_at = utc_now()
    manifest_after = file_record(path)
    if manifest_after != manifest_before:
        raise ShadowLabError("Shadow Lab manifest changed during execution")
    after = source_state(owned["source"])
    differences = state_differences(before, after)
    source_unchanged = not differences
    status_value = "pass" if exit_code == 0 and source_unchanged else "fail"
    receipt = {
        "schema": RUNTIME_EVIDENCE_SCHEMA,
        "kind": "shadow_command",
        "id": evidence_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "authority": {
            "shadow_lab_manifest": manifest_before,
            "source_commit": manifest.get("source", {}).get("commit"),
            "worktree": str(owned["worktree"]),
        },
        "phase": {"kind": phase, "network_mode": network_mode},
        "enforcement": enforcement,
        "command": {
            "executable": Path(command[0]).name,
            "argv_sha256": sha256_bytes(
                json.dumps(command, ensure_ascii=False, separators=(",", ":")).encode(
                    "utf-8"
                )
            ),
            "exit_code": exit_code,
        },
        "outputs": {
            "stdout": file_record(stdout_path),
            "stderr": file_record(stderr_path),
        },
        "source_audit": {
            "source_unchanged": source_unchanged,
            "difference_fields": differences,
        },
        "status": status_value,
    }
    atomic_write_json(receipt_path, receipt)
    os.chmod(receipt_path, 0o600)
    validated = _execution_receipt(
        receipt_path,
        manifest_path=path,
        manifest=manifest,
        owned=owned,
    )
    return {
        "schema": RUNTIME_EVIDENCE_SCHEMA,
        "ok": validated["status"] == "pass",
        "action": "execute",
        "receipt_path": str(receipt_path),
        "receipt": validated,
        "timed_out": timed_out,
    }


def verify_lab(manifest_path: Path) -> dict[str, Any]:
    path, manifest = load_manifest(manifest_path)
    owned = verify_ownership(path, manifest)
    baseline = manifest.get("source", {}).get("baseline")
    if not isinstance(baseline, dict):
        raise ShadowLabError("manifest source baseline must be an object")
    current = source_state(owned["source"])
    differences = state_differences(baseline, current)
    current_tree = tree_fingerprint(
        owned["worktree"],
        allow_internal_symlinks=True,
    )
    source_unchanged = not differences
    network = runtime_evidence_summary(path, manifest, owned)
    return {
        "schema": VERIFICATION_SCHEMA,
        "ok": source_unchanged and network["evidence_status"] != "failed",
        "action": "verify",
        "lab_id": manifest.get("lab_id"),
        "source": {
            "repo_path": str(owned["source"]),
            "commit": manifest.get("source", {}).get("commit"),
            "source_unchanged": source_unchanged,
            "difference_fields": differences,
            "untracked_content_read": False,
        },
        "boundary": {
            "owned_lab": True,
            "source_and_output_disjoint": True,
            "source_writes_allowed": False,
            "network_allowed": False,
            "network": network,
        },
        "lab": {
            "manifest_path": str(path),
            "worktree": str(owned["worktree"]),
            **current_tree,
        },
    }


def cleanup_lab(manifest_path: Path, *, confirm: bool) -> dict[str, Any]:
    if not confirm:
        raise ShadowLabError("cleanup requires explicit --confirm")
    path, manifest = load_manifest(manifest_path)
    owned = verify_ownership(path, manifest)
    baseline = manifest.get("source", {}).get("baseline")
    current = source_state(owned["source"])
    differences = (
        state_differences(baseline, current) if isinstance(baseline, dict) else ["baseline"]
    )
    lab_dir = owned["lab_dir"]
    shutil.rmtree(lab_dir)
    if lab_dir.exists():
        raise ShadowLabError(f"failed to remove owned lab directory: {lab_dir}")
    return {
        "schema": CLEANUP_SCHEMA,
        "ok": not differences,
        "action": "cleanup",
        "lab_id": manifest.get("lab_id"),
        "lab_removed": True,
        "source_unchanged": not differences,
        "source_difference_fields": differences,
        "source_writes_performed": False,
    }


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def bounded_timeout(value: str) -> int:
    parsed = positive_int(value)
    if parsed > MAX_EXECUTION_TIMEOUT_SECONDS:
        raise argparse.ArgumentTypeError(
            f"value must be <= {MAX_EXECUTION_TIMEOUT_SECONDS}"
        )
    return parsed


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Prepare, verify, and clean disposable read-only Git snapshots."
    )
    subcommands = command.add_subparsers(dest="action", required=True)

    prepare = subcommands.add_parser("prepare")
    prepare.add_argument("--source", required=True, type=Path)
    prepare.add_argument("--ref", default="HEAD")
    prepare.add_argument("--output-root", type=Path, default=default_output_root())
    prepare.add_argument(
        "--max-archive-bytes", type=positive_int, default=DEFAULT_MAX_ARCHIVE_BYTES
    )
    prepare.add_argument("--max-files", type=positive_int, default=DEFAULT_MAX_FILES)
    prepare.add_argument(
        "--max-total-bytes", type=positive_int, default=DEFAULT_MAX_TOTAL_BYTES
    )
    prepare.add_argument(
        "--network-policy",
        choices=sorted(NETWORK_POLICIES),
        default=None,
        help="Declare the caller's intended network boundary; execution receipts remain required for proof.",
    )

    verify = subcommands.add_parser("verify")
    verify.add_argument("--manifest", required=True, type=Path)

    execute = subcommands.add_parser("execute")
    execute.add_argument("--manifest", required=True, type=Path)
    execute.add_argument("--evidence-id", required=True)
    execute.add_argument("--phase", required=True, choices=sorted(EXECUTION_PHASES))
    execute.add_argument("--network-mode", required=True, choices=sorted(NETWORK_MODES))
    execute.add_argument(
        "--timeout-seconds",
        type=bounded_timeout,
        default=DEFAULT_EXECUTION_TIMEOUT_SECONDS,
    )
    execute.add_argument("command", nargs=argparse.REMAINDER)

    cleanup = subcommands.add_parser("cleanup")
    cleanup.add_argument("--manifest", required=True, type=Path)
    cleanup.add_argument("--confirm", action="store_true")
    return command


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        if arguments.action == "prepare":
            network_policy = arguments.network_policy or "denied"
            payload = prepare_lab(
                source_path=arguments.source,
                requested_ref=arguments.ref,
                output_root_path=arguments.output_root,
                max_archive_bytes=arguments.max_archive_bytes,
                max_files=arguments.max_files,
                max_total_bytes=arguments.max_total_bytes,
                network_policy=network_policy,
                network_authorization=(
                    "caller_declared"
                    if arguments.network_policy is not None
                    else "shadow_lab_default"
                ),
            )
        elif arguments.action == "verify":
            payload = verify_lab(arguments.manifest)
        elif arguments.action == "execute":
            command_arguments = list(arguments.command)
            if command_arguments and command_arguments[0] == "--":
                command_arguments.pop(0)
            payload = execute_in_lab(
                manifest_path=arguments.manifest,
                evidence_id=arguments.evidence_id,
                phase=arguments.phase,
                network_mode=arguments.network_mode,
                command=command_arguments,
                timeout_seconds=arguments.timeout_seconds,
            )
        else:
            payload = cleanup_lab(arguments.manifest, confirm=arguments.confirm)
        sys.stdout.write(json_text(payload))
        return 0 if payload.get("ok") else 2
    except (ShadowLabError, json.JSONDecodeError, OSError, ValueError) as exc:
        sys.stdout.write(
            json_text(
                {
                    "ok": False,
                    "action": getattr(arguments, "action", "unknown"),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
