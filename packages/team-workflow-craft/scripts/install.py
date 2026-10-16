#!/usr/bin/env python3
"""Preview or apply an explicit, verified Team Workflow Craft skill install."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path, PureWindowsPath

from packaging import (
    INSTALL_MARKER,
    PackagingError,
    SKILL_NAME,
    install_marker,
    read_artifact,
    safe_remove_tree,
    verify_installed,
    write_staging,
)


HOST_PATHS = {
    "codex": Path(".agents") / "skills" / "team-workflow-craft",
    "pi": Path(".agents") / "skills" / "team-workflow-craft",
    "claude": Path(".claude") / "skills" / "team-workflow-craft",
}
PLATFORM_PARENT_SYMLINKS = {Path("/tmp"), Path("/var"), Path("/etc")}


def _is_windows() -> bool:
    return os.name == "nt"


def _validate_explicit_path_syntax(value: Path | PureWindowsPath, label: str, *, is_windows: bool) -> None:
    """Validate an input path's native flavor without touching the filesystem."""
    raw = value.expanduser() if isinstance(value, Path) else value
    raw_text = str(raw)
    if ".." in raw.parts:
        raise PackagingError(f"{label} must not contain '..'")
    if not is_windows and ("\\" in raw_text or PureWindowsPath(raw_text).drive):
        raise PackagingError(f"{label} must not contain a Windows drive, backslash, or '..'")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, type=Path, help="ZIP produced by scripts/build.py")
    parser.add_argument("--manifest", type=Path, help="Artifact manifest; defaults beside --artifact")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--project", type=Path, help="Project root for a host-specific project installation")
    target_group.add_argument("--target", type=Path, help="Exact skill directory to install into")
    parser.add_argument("--host", choices=sorted(HOST_PATHS), help="Required with --project")
    parser.add_argument("--apply", action="store_true", help="Write only after this explicit flag")
    parser.add_argument("--allow-upgrade", action="store_true", help="Replace a known, unchanged older installation")
    arguments = parser.parse_args(argv)
    if arguments.project is not None and arguments.host is None:
        parser.error("--project requires --host")
    if arguments.target is not None and arguments.host is not None:
        parser.error("--host is only valid with --project")
    return arguments


def _canonical_explicit_path(value: Path, label: str) -> Path:
    """Resolve platform links but refuse user-controlled parent-link escapes."""
    _validate_explicit_path_syntax(value, label, is_windows=_is_windows())
    raw = value.expanduser()
    absolute = raw.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        candidate = current / part
        if candidate.is_symlink():
            if candidate in PLATFORM_PARENT_SYMLINKS:
                current = candidate.resolve(strict=True)
                continue
            raise PackagingError(f"{label} path contains a non-platform symlink: {candidate}")
        current = candidate
    return current


def resolve_target(arguments: argparse.Namespace) -> Path:
    if arguments.target is not None:
        target = _canonical_explicit_path(arguments.target, "--target")
    else:
        project = _canonical_explicit_path(arguments.project, "--project")
        if not project.is_dir():
            raise PackagingError("--project must name an existing non-symlink directory")
        relative = HOST_PATHS[arguments.host]
        target = _canonical_explicit_path(project / relative, "project target")
    home = Path.home()
    global_targets = {
        (home / ".agents" / "skills" / SKILL_NAME).resolve(strict=False),
        (home / ".codex" / "skills" / SKILL_NAME).resolve(strict=False),
        (home / ".claude" / "skills" / SKILL_NAME).resolve(strict=False),
        (home / ".pi" / "agent" / "skills" / SKILL_NAME).resolve(strict=False),
    }
    if target in global_targets:
        raise PackagingError("global skill installation is not supported; provide a project-local target")
    if target.exists() and target.is_symlink():
        raise PackagingError(f"target must not be a symlink: {target}")
    return target


def plan_install(target: Path, files: dict[str, bytes], marker: bytes, version: str, allow_upgrade: bool) -> str:
    if not target.exists():
        return "install"
    if verify_installed(target, files, marker):
        return "already_installed"
    marker_path = target / INSTALL_MARKER
    if not marker_path.is_file() or marker_path.is_symlink():
        raise PackagingError("refusing to overwrite a directory without a trusted TWC installation marker")
    try:
        prior = json.loads(marker_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PackagingError("refusing to overwrite an unreadable TWC installation marker") from error
    if prior.get("schema") != "team-workflow-craft.install.v1" or prior.get("skill") != "team-workflow-craft":
        raise PackagingError("refusing to overwrite an unknown TWC installation marker")
    if not _matches_prior_installation(target, prior):
        raise PackagingError("known installation has drifted; refusing to overwrite it")
    if not allow_upgrade:
        raise PackagingError("known installation differs; rerun with --allow-upgrade after reviewing it")
    if prior.get("version") == version:
        raise PackagingError("same-version installation drifted; refusing to overwrite it")
    return "upgrade"


def _matches_prior_installation(target: Path, marker: dict) -> bool:
    """Accept only an exact prior installation described by its own marker."""
    if target.is_symlink() or not target.is_dir():
        return False
    entries = marker.get("files")
    if not isinstance(entries, list) or not entries:
        return False
    expected: dict[str, tuple[str, int]] = {}
    try:
        for entry in entries:
            path = entry["path"]
            digest = entry["sha256"]
            size = entry["size"]
            if not isinstance(path, str) or not isinstance(digest, str) or not isinstance(size, int):
                return False
            if not path or path.startswith("/") or path.startswith("../") or "/../" in path:
                return False
            if path in expected or len(digest) != 64 or size < 0:
                return False
            expected[path] = (digest, size)
    except (KeyError, TypeError):
        return False
    actual: dict[str, tuple[str, int]] = {}
    for path in target.rglob("*"):
        if path.is_symlink():
            return False
        if path.is_dir():
            continue
        if not path.is_file():
            return False
        relative = path.relative_to(target).as_posix()
        if relative == INSTALL_MARKER:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            return False
        actual[relative] = (hashlib.sha256(data).hexdigest(), len(data))
    return actual == expected


def apply_install(
    target: Path, files: dict[str, bytes], marker: bytes, action: str, expected_prior_marker: bytes | None
) -> None:
    staging = write_staging(target.parent, target.name, files, marker)
    backup: Path | None = None
    try:
        if action == "install" and target.exists():
            raise PackagingError("target appeared during installation; no files were replaced")
        if action == "upgrade":
            if not target.exists():
                raise PackagingError("target disappeared during upgrade; no files were replaced")
            marker_path = target / INSTALL_MARKER
            if expected_prior_marker is None or not marker_path.is_file() or marker_path.is_symlink():
                raise PackagingError("target changed during upgrade; no files were replaced")
            if marker_path.read_bytes() != expected_prior_marker:
                raise PackagingError("target marker changed during upgrade; no files were replaced")
            try:
                current_marker = json.loads(expected_prior_marker.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise PackagingError("target marker changed during upgrade; no files were replaced") from error
            if not _matches_prior_installation(target, current_marker):
                raise PackagingError("target content changed during upgrade; no files were replaced")
            backup = target.parent / f".{target.name}.twc-backup-{uuid.uuid4().hex}"
            os.replace(target, backup)
        os.replace(staging, target)
        if backup is not None:
            safe_remove_tree(backup)
    except BaseException:
        if staging.exists():
            safe_remove_tree(staging)
        if backup is not None and backup.exists() and not target.exists():
            os.replace(backup, target)
        raise


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(sys.argv[1:] if argv is None else argv)
    manifest_path = arguments.manifest or arguments.artifact.with_suffix(".zip.manifest.json")
    try:
        manifest, files, manifest_sha256 = read_artifact(arguments.artifact.expanduser(), manifest_path.expanduser())
        target = resolve_target(arguments)
        marker = install_marker(manifest, manifest_sha256)
        marker_path = target / INSTALL_MARKER
        expected_prior_marker = marker_path.read_bytes() if marker_path.is_file() and not marker_path.is_symlink() else None
        action = plan_install(target, files, marker, manifest["version"], arguments.allow_upgrade)
        result = {
            "status": "dry_run" if not arguments.apply else action,
            "action": action,
            "target": str(target),
            "version": manifest["version"],
            "host": arguments.host,
            "host_loading": "UNVERIFIED",
        }
        if arguments.apply and action in {"install", "upgrade"}:
            apply_install(target, files, marker, action, expected_prior_marker)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, PackagingError) as error:
        print(f"install failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
