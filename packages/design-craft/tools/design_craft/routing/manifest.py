from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .path_policy import (
    normalize_manifest_path,
    validate_manifest_source_path,
)


SCHEMA = "design-craft.codex-route-pack.v2"
ROUTE_PACK_MANIFEST_SCHEMA = "codex.frontend-route-pack.manifest.v1"
ROUTE_PACK_MANIFEST_PATH = "tools/frontend_route_pack_manifest.json"


@dataclass(frozen=True)
class PackFile:
    path: str
    required: bool
    kind: str


SUGGESTED_VALIDATION_COMMANDS = [
    "bash ~/.codex/tools/frontend_preflight_verify.sh",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_source_root() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_entry(source_root: Path, spec: PackFile) -> dict:
    path = source_root / spec.path
    entry = {
        "path": spec.path,
        "required": spec.required,
        "kind": spec.kind,
        "exists": path.is_file(),
    }
    if path.is_file():
        mode = path.stat().st_mode
        entry.update(
            {
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "executable": bool(mode & stat.S_IXUSR),
            }
        )
    return entry


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def load_route_pack_files(source_root: Path) -> tuple[list[PackFile], dict]:
    manifest_path = source_root / ROUTE_PACK_MANIFEST_PATH
    manifest = load_json(manifest_path)
    errors: list[str] = []

    if manifest.get("schema") != ROUTE_PACK_MANIFEST_SCHEMA:
        errors.append(
            "route-pack manifest schema must be "
            f"{ROUTE_PACK_MANIFEST_SCHEMA}, got {manifest.get('schema')!r}"
        )
    if manifest.get("version") != 1:
        errors.append("route-pack manifest version must be 1")

    raw_files = manifest.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        errors.append("route-pack manifest files must be a non-empty array")
        raw_files = []

    seen: set[str] = set()
    route_pack_files: list[PackFile] = []
    snapshot_paths: set[str] = set()
    route_pack_metadata: dict[str, dict] = {}
    for index, raw in enumerate(raw_files):
        prefix = f"route-pack manifest files[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix} must be an object")
            continue
        try:
            rel_path = normalize_manifest_path(raw.get("path"))
            validate_manifest_source_path(source_root, rel_path)
        except ValueError as exc:
            errors.append(f"{prefix}: {exc}")
            continue
        if rel_path in seen:
            errors.append(f"route-pack manifest contains duplicate path: {rel_path}")
            continue
        seen.add(rel_path)

        required = raw.get("required")
        route_pack = raw.get("route_pack")
        snapshot = raw.get("snapshot")
        kind = raw.get("kind")
        if not isinstance(required, bool):
            errors.append(f"{prefix}.required must be boolean")
        if not isinstance(route_pack, bool):
            errors.append(f"{prefix}.route_pack must be boolean")
        if not isinstance(snapshot, bool):
            errors.append(f"{prefix}.snapshot must be boolean")
        if not isinstance(kind, str) or not kind.strip():
            errors.append(f"{prefix}.kind must be a non-empty string")
        if not all(
            [
                isinstance(required, bool),
                isinstance(route_pack, bool),
                isinstance(snapshot, bool),
                isinstance(kind, str) and bool(kind.strip()),
            ]
        ):
            continue

        if snapshot:
            snapshot_paths.add(rel_path)
        if route_pack:
            route_pack_files.append(PackFile(rel_path, required, kind.strip()))
            route_pack_metadata[rel_path] = raw

    manifest_entry = route_pack_metadata.get(ROUTE_PACK_MANIFEST_PATH)
    if not manifest_entry or manifest_entry.get("required") is not True:
        errors.append(
            f"{ROUTE_PACK_MANIFEST_PATH} must include itself as required route_pack=true"
        )
    required_without_snapshot = sorted(
        spec.path
        for spec in route_pack_files
        if spec.required and spec.path not in snapshot_paths
    )
    if required_without_snapshot:
        errors.append(
            "required route-pack files must also be snapshot=true: "
            + ", ".join(required_without_snapshot)
        )
    if not route_pack_files:
        errors.append("route-pack manifest selects no route_pack=true files")
    if errors:
        raise ValueError("; ".join(errors))

    return route_pack_files, {
        "schema": manifest["schema"],
        "version": manifest["version"],
        "path": ROUTE_PACK_MANIFEST_PATH,
        "sha256": sha256_file(manifest_path),
        "declared_files": len(raw_files),
        "selected_files": len(route_pack_files),
        "required_files": sum(1 for spec in route_pack_files if spec.required),
        "snapshot_files": len(snapshot_paths),
        "required_snapshot_covered": not required_without_snapshot,
    }
