from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .constants import (
    ARTIFACT_PATHS,
    REGISTERED_EVIDENCE_KINDS,
    REGISTERED_EVIDENCE_MAX_BYTES,
    SCHEMA_VERSION,
)
from .jsonio import atomic_write_bytes, read_json, sha256_bytes, write_json
from .locking import exclusive_file_lock

REGISTRY_LOCK = ".evidence-registry.lock"
EVIDENCE_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


def registered_artifact_path(identifier: str) -> str:
    return f"evidence/registered/{identifier}/artifact"


def _canonical_file(run_dir: Path, relative: str) -> Path:
    path = run_dir / relative
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"run artifact must be a regular non-symlink file: {relative}")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(run_dir)
    except ValueError as error:
        raise ValueError(f"run artifact escapes the review directory: {relative}") from error
    return resolved


def _prepare_target_parent(run_dir: Path, target: Path) -> None:
    current = run_dir
    for part in target.parent.relative_to(run_dir).parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"registered evidence parent must not be a symlink: {current}")
        if current.exists():
            if not current.is_dir():
                raise ValueError(f"registered evidence parent must be a directory: {current}")
            continue
        current.mkdir(mode=0o700)


def register_evidence(
    run_dir_value: str | Path,
    *,
    identifier: str,
    source_value: str | Path,
    kind: str,
    producer: str,
    description: str,
    media_type: str,
    registered_at: str,
    max_bytes: int = REGISTERED_EVIDENCE_MAX_BYTES,
) -> dict[str, Any]:
    run_dir = Path(run_dir_value).expanduser().resolve(strict=True)
    source = _validate_registration_input(
        source_value,
        identifier=identifier,
        kind=kind,
        producer=producer,
        description=description,
        media_type=media_type,
        max_bytes=max_bytes,
    )

    with exclusive_file_lock(
        run_dir,
        name=REGISTRY_LOCK,
        wait_seconds=30,
        timeout_message="timed out waiting for the evidence registry lock",
    ):
        return _register_locked(
            run_dir,
            source=source,
            identifier=identifier,
            kind=kind,
            producer=producer,
            description=description,
            media_type=media_type,
            registered_at=registered_at,
            max_bytes=max_bytes,
        )


def _validate_registration_input(
    source_value: str | Path,
    *,
    identifier: str,
    kind: str,
    producer: str,
    description: str,
    media_type: str,
    max_bytes: int,
) -> Path:
    source_path = Path(source_value).expanduser()
    if source_path.is_symlink():
        raise ValueError("--source: expected a regular non-symlink file")
    source = source_path.resolve(strict=True)
    if EVIDENCE_ID_PATTERN.fullmatch(identifier) is None:
        raise ValueError(
            "--id must start with a lowercase letter or digit and contain only "
            "lowercase letters, digits, '.', '_' or '-'"
        )
    if kind not in REGISTERED_EVIDENCE_KINDS:
        raise ValueError(f"--kind: unsupported registered evidence kind {kind!r}")
    if not producer.strip():
        raise ValueError("--producer: expected a non-empty value")
    if not description.strip():
        raise ValueError("--description: expected a non-empty value")
    if not media_type.strip():
        raise ValueError("--media-type: expected a non-empty value")
    if max_bytes < 1:
        raise ValueError("--max-bytes: expected a positive integer")
    if not source.is_file():
        raise ValueError("--source: expected a regular non-symlink file")
    source_size = source.stat().st_size
    if source_size > max_bytes:
        raise ValueError(f"registered evidence exceeds --max-bytes: {source_size} > {max_bytes}")
    return source


def _register_locked(
    run_dir: Path,
    *,
    source: Path,
    identifier: str,
    kind: str,
    producer: str,
    description: str,
    media_type: str,
    registered_at: str,
    max_bytes: int,
) -> dict[str, Any]:
    manifest = read_json(_canonical_file(run_dir, "review-manifest.json"))
    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("register-evidence requires a current run.v5 review")
    if manifest.get("status") != "draft" or manifest.get("sealedAt") is not None:
        raise ValueError("register-evidence requires an unsealed draft review")
    if manifest.get("artifacts") != ARTIFACT_PATHS:
        raise ValueError("review manifest does not declare the current canonical artifact map")

    registry_path = run_dir / ARTIFACT_PATHS["evidenceRegistry"]
    registry = read_json(_canonical_file(run_dir, ARTIFACT_PATHS["evidenceRegistry"]))
    rows = registry.get("artifacts")
    if not isinstance(rows, list):
        raise ValueError("evidence registry artifacts must be an array")
    if any(isinstance(row, dict) and row.get("id") == identifier for row in rows):
        raise ValueError(f"registered evidence id already exists: {identifier}")

    content = source.read_bytes()
    if len(content) > max_bytes:
        raise ValueError(f"registered evidence exceeds --max-bytes: {len(content)} > {max_bytes}")
    relative = registered_artifact_path(identifier)
    target = run_dir / relative
    if target.exists() or target.is_symlink():
        raise ValueError(f"registered evidence target already exists: {relative}")
    _prepare_target_parent(run_dir, target)

    entry = {
        "id": identifier,
        "kind": kind,
        "path": relative,
        "sha256": sha256_bytes(content),
        "sizeBytes": len(content),
        "mediaType": media_type.strip(),
        "producer": producer.strip(),
        "description": description.strip(),
        "registeredAt": registered_at,
    }
    atomic_write_bytes(target, content, mode=0o600)
    registry["artifacts"] = sorted([*rows, entry], key=lambda row: row["id"])
    write_json(registry_path, registry, mode=0o600)
    return {**entry, "ref": f"artifact:{identifier}"}
