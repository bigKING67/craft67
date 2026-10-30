"""Deterministic, source-independent packaging for Workflow Craft.

The installable product is exactly one skill directory.  Development helpers in
the package root deliberately never appear in the archive, so an installed
skill cannot accidentally depend on the craft67 checkout.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
import re


SKILL_NAME = "workflow-craft"
LEGACY_SKILL_NAME = "team-workflow-craft"
ARCHIVE_SCHEMA = "workflow-craft.artifact.v1"
INSTALL_SCHEMA = "workflow-craft.install.v1"
INSTALL_MARKER = ".twc-install.json"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$")


class PackagingError(ValueError):
    """Raised when an artifact or installation cannot be trusted."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def package_root_from_script(script_file: str | Path) -> Path:
    return Path(script_file).resolve().parent.parent


def read_version(package_root: Path) -> str:
    version_file = package_root / "VERSION"
    if version_file.is_symlink() or not version_file.is_file():
        raise PackagingError("package VERSION must be a regular file")
    version = version_file.read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(version):
        raise PackagingError("package VERSION must be a SemVer 2.0.0 version")
    return version


def _regular_file(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError as error:
        raise PackagingError(f"missing {label}: {path}") from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise PackagingError(f"{label} must be a regular non-symlink file: {path}")


def runtime_files(package_root: Path) -> dict[str, bytes]:
    """Return archive-relative bytes for the only supported runtime surface."""
    runtime_root = package_root / "skills" / SKILL_NAME
    if runtime_root.is_symlink() or not runtime_root.is_dir():
        raise PackagingError(f"runtime skill directory is missing or unsafe: {runtime_root}")

    files: dict[str, bytes] = {}
    for path in sorted(runtime_root.rglob("*")):
        relative = path.relative_to(runtime_root)
        if path.is_symlink():
            raise PackagingError(f"runtime must not contain symlinks: {relative.as_posix()}")
        if path.is_dir():
            continue
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        _regular_file(path, "runtime file")
        name = relative.as_posix()
        if not name or name.startswith("../") or "/../" in name:
            raise PackagingError(f"unsafe runtime path: {name}")
        if name == INSTALL_MARKER:
            raise PackagingError("runtime source must not contain its installation marker")
        files[name] = path.read_bytes()

    if "SKILL.md" not in files:
        raise PackagingError("runtime skill must contain SKILL.md")
    if "scripts/twc.py" not in files:
        raise PackagingError("runtime skill must contain scripts/twc.py")

    license_file = package_root / "LICENSE"
    _regular_file(license_file, "package LICENSE")
    files["VERSION"] = (read_version(package_root) + "\n").encode("utf-8")
    files["LICENSE"] = license_file.read_bytes()
    return dict(sorted(files.items()))


def artifact_manifest(artifact_name: str, version: str, files: dict[str, bytes], artifact_hash: str) -> dict[str, Any]:
    return {
        "schema": ARCHIVE_SCHEMA,
        "artifact": artifact_name,
        "artifact_sha256": artifact_hash,
        "archive_prefix": SKILL_NAME,
        "version": version,
        "files": [
            {"path": path, "sha256": sha256_bytes(contents), "size": len(contents)}
            for path, contents in sorted(files.items())
        ],
    }


def artifact_paths(output_dir: Path, version: str) -> tuple[Path, Path]:
    artifact = output_dir / f"{SKILL_NAME}-{version}.zip"
    return artifact, artifact.with_suffix(".zip.manifest.json")


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as archive:
            for relative, contents in sorted(files.items()):
                member = f"{SKILL_NAME}/{relative}"
                info = zipfile.ZipInfo(member, date_time=FIXED_ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.flag_bits |= 0x800
                archive.writestr(info, contents, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        stream.seek(0)
        return stream.read()


def _atomic_write(path: Path, contents: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def create_artifact(package_root: Path, output_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    """Build a ZIP and its external content/hash manifest in *output_dir*."""
    package_root = package_root.resolve()
    output_dir = output_dir.expanduser().resolve()
    version = read_version(package_root)
    files = runtime_files(package_root)
    artifact, manifest_path = artifact_paths(output_dir, version)
    archive_bytes = _zip_bytes(files)
    manifest = artifact_manifest(artifact.name, version, files, sha256_bytes(archive_bytes))
    _atomic_write(artifact, archive_bytes)
    _atomic_write(manifest_path, canonical_json(manifest))
    return artifact, manifest_path, manifest


def _safe_relative(value: str) -> PurePosixPath:
    if "\\" in value or ":" in value:
        raise PackagingError(f"unsafe artifact path: {value!r}")
    raw_parts = value.split("/")
    if not value or any(part in {"", ".", ".."} for part in raw_parts):
        raise PackagingError(f"unsafe artifact path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        raise PackagingError(f"unsafe artifact path: {value!r}")
    return path


def load_manifest(path: Path) -> dict[str, Any]:
    _regular_file(path, "artifact manifest")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PackagingError(f"invalid artifact manifest: {path}") from error
    if not isinstance(data, dict) or data.get("schema") != ARCHIVE_SCHEMA:
        raise PackagingError("artifact manifest schema is not supported")
    if not isinstance(data.get("artifact"), str) or not isinstance(data.get("version"), str):
        raise PackagingError("artifact manifest lacks artifact identity")
    if not isinstance(data.get("artifact_sha256"), str) or len(data["artifact_sha256"]) != 64:
        raise PackagingError("artifact manifest lacks a SHA-256")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise PackagingError("artifact manifest lacks files")
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise PackagingError("artifact manifest has invalid file metadata")
        relative = item["path"]
        _safe_relative(relative)
        if relative == INSTALL_MARKER:
            raise PackagingError("artifact must not contain its installation marker")
        if relative in seen or not isinstance(item.get("sha256"), str) or not isinstance(item.get("size"), int):
            raise PackagingError("artifact manifest has duplicate or invalid file metadata")
        if len(item["sha256"]) != 64 or item["size"] < 0:
            raise PackagingError("artifact manifest has invalid file digest or size")
        seen.add(relative)
    return data


def read_artifact(artifact: Path, manifest_path: Path) -> tuple[dict[str, Any], dict[str, bytes], str]:
    """Validate a ZIP and return its vetted runtime files and manifest digest."""
    _regular_file(artifact, "artifact")
    manifest = load_manifest(manifest_path)
    if artifact.name != manifest["artifact"]:
        raise PackagingError("artifact filename does not match its manifest")
    if sha256_file(artifact) != manifest["artifact_sha256"]:
        raise PackagingError("artifact SHA-256 does not match its manifest")
    prefix = manifest.get("archive_prefix")
    if prefix != SKILL_NAME:
        raise PackagingError("artifact archive prefix is not supported")

    expected = {entry["path"]: entry for entry in manifest["files"]}
    files: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(artifact) as archive:
            members = archive.infolist()
            names: set[str] = set()
            for info in members:
                if info.is_dir():
                    continue
                name = info.filename
                required_prefix = f"{SKILL_NAME}/"
                if not name.startswith(required_prefix):
                    raise PackagingError(f"artifact member is outside the runtime root: {name!r}")
                relative = name[len(required_prefix) :]
                _safe_relative(relative)
                if relative == INSTALL_MARKER:
                    raise PackagingError("artifact must not contain its installation marker")
                if relative in names:
                    raise PackagingError(f"artifact has duplicate member: {relative}")
                names.add(relative)
                mode = (info.external_attr >> 16) & 0o170000
                if mode == stat.S_IFLNK:
                    raise PackagingError(f"artifact contains a symlink: {relative}")
                if mode not in {0, stat.S_IFREG}:
                    raise PackagingError(f"artifact contains a non-regular file: {relative}")
                if relative not in expected:
                    raise PackagingError(f"artifact contains an unmanifested file: {relative}")
                contents = archive.read(info)
                entry = expected[relative]
                if len(contents) != entry["size"] or sha256_bytes(contents) != entry["sha256"]:
                    raise PackagingError(f"artifact content does not match manifest: {relative}")
                files[relative] = contents
    except zipfile.BadZipFile as error:
        raise PackagingError("artifact is not a readable ZIP") from error
    if set(files) != set(expected):
        missing = sorted(set(expected) - set(files))
        raise PackagingError(f"artifact is missing manifest files: {', '.join(missing)}")
    if "SKILL.md" not in files or "scripts/twc.py" not in files or "VERSION" not in files or "LICENSE" not in files:
        raise PackagingError("artifact lacks a required independent runtime file")
    if files["VERSION"].decode("utf-8").strip() != manifest["version"]:
        raise PackagingError("artifact VERSION does not match manifest version")
    return manifest, files, sha256_file(manifest_path)


def install_marker(manifest: dict[str, Any], manifest_sha256: str) -> bytes:
    return canonical_json(
        {
            "schema": INSTALL_SCHEMA,
            "artifact": manifest["artifact"],
            "artifact_sha256": manifest["artifact_sha256"],
            "artifact_manifest_sha256": manifest_sha256,
            "files": manifest["files"],
            "skill": SKILL_NAME,
            "version": manifest["version"],
        }
    )


def verify_installed(target: Path, files: dict[str, bytes], marker: bytes) -> bool:
    """Return true only for an exact, known installation with no extra files."""
    if target.is_symlink() or not target.is_dir():
        return False
    actual: dict[str, bytes] = {}
    for path in target.rglob("*"):
        if path.is_symlink() or path.is_dir():
            if path.is_symlink():
                return False
            continue
        try:
            relative = path.relative_to(target).as_posix()
            _safe_relative(relative)
            _regular_file(path, "installed file")
        except PackagingError:
            return False
        actual[relative] = path.read_bytes()
    expected = dict(files)
    expected[INSTALL_MARKER] = marker
    return actual == expected


def safe_remove_tree(path: Path) -> None:
    """Remove a staging/known-backup directory without following symlinks."""
    if path.is_symlink() or not path.is_dir():
        raise PackagingError(f"refusing to remove unsafe directory: {path}")
    for child in path.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
        elif child.is_dir():
            safe_remove_tree(child)
        else:
            raise PackagingError(f"refusing to remove unsupported filesystem entry: {child}")
    path.rmdir()


def write_staging(parent: Path, target_name: str, files: dict[str, bytes], marker: bytes) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target_name}.twc-staging-", dir=parent))
    try:
        for relative, contents in files.items():
            destination = staging.joinpath(*_safe_relative(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents)
        (staging / INSTALL_MARKER).write_bytes(marker)
        return staging
    except BaseException:
        safe_remove_tree(staging)
        raise
