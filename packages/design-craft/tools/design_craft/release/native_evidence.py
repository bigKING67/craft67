from __future__ import annotations

import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..repo import REPO_ROOT


# The native runtime validator is still a repository script; keep this adapter local
# until that validator moves into the package in the next evaluation refactor.
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from design_craft_native_runtime_validate import (  # noqa: E402
    DEFAULT_FIXTURE_ROOT,
    DEFAULT_SKILL_ROOT,
    EVIDENCE_SCHEMA,
    validate_evidence,
)

from .integrity import sha256_bytes, sha256_file  # noqa: E402
from .native_archive import (
    MAX_ARCHIVE_ENTRIES,
    MAX_MEMBER_BYTES,
    MAX_TOTAL_BYTES,
    extract_entries,
    inspect_archive,
    safe_relative,
)  # noqa: E402


EVIDENCE_LAYOUT = {
    "ios": ("ios", "ios-observed.json", "ios_simulator"),
    "android": ("android", "android-observed.json", "android_emulator"),
    "real_device": ("real-device", "real-device-observed.json", None),
}


@dataclass(frozen=True)
class ArchiveInspection:
    bundle: Path
    bundle_sha256: str | None
    entries: dict[str, bytes]
    payloads: dict[str, dict[str, object]]
    errors: tuple[str, ...]


def _path_has_symlink(root: Path, relative: str) -> bool:
    candidate = root
    for part in Path(relative).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            return True
    return False


def copy_evidence(source_dir: Path, target_dir: Path, json_name: str) -> dict[str, object]:
    source_dir = source_dir.expanduser()
    if source_dir.is_symlink() or not source_dir.is_dir():
        raise FileNotFoundError(f"native evidence root is missing or unsafe: {source_dir}")
    source_dir = source_dir.resolve()
    source_json = source_dir / json_name
    if _path_has_symlink(source_dir, json_name) or not source_json.is_file():
        raise FileNotFoundError(f"native evidence JSON is missing or unsafe: {source_json}")
    payload = json.loads(source_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"native evidence JSON must be an object: {source_json}")
    target_dir.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source_json, target_dir / json_name)
    observed_paths: set[str] = set()
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError(f"native evidence artifacts must be an array: {source_json}")
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ValueError(f"native evidence artifact must be an object: {source_json}")
        relative_raw = artifact.get("path")
        if not isinstance(relative_raw, str):
            raise ValueError(f"native artifact path is missing: {source_json}")
        relative = safe_relative(relative_raw)
        if relative in observed_paths:
            raise ValueError(f"duplicate native artifact path: {relative}")
        observed_paths.add(relative)
        source = source_dir / Path(relative)
        resolved_source = source.resolve()
        if _path_has_symlink(source_dir, relative) or not source.is_file():
            raise FileNotFoundError(f"native artifact is missing or unsafe: {source}")
        if source_dir != resolved_source and source_dir not in resolved_source.parents:
            raise ValueError(f"native artifact escapes its evidence root: {source}")
        destination = target_dir / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return payload


def evidence_members(prefix: str, json_name: str, payload: dict[str, object]) -> set[str]:
    expected = {f"{prefix}/{json_name}"}
    artifact_paths: set[str] = set()
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError(f"{json_name} artifacts must be an array")
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
            raise ValueError(f"{json_name} contains an invalid artifact")
        relative = safe_relative(artifact["path"])
        if relative in artifact_paths:
            raise ValueError(f"{json_name} repeats artifact path {relative}")
        artifact_paths.add(relative)
        expected.add(f"{prefix}/{relative}")
    return expected


def archive_files(
    evidence_root: Path, payloads: dict[str, dict[str, object]]
) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    total_bytes = 0
    for key, payload in payloads.items():
        prefix, json_name, _ = EVIDENCE_LAYOUT[key]
        for relative in evidence_members(prefix, json_name, payload):
            path = evidence_root / Path(relative)
            if path.is_symlink() or not path.is_file():
                raise FileNotFoundError(
                    f"native release member is missing or unsafe: {path}"
                )
            size = path.stat().st_size
            if size > MAX_MEMBER_BYTES:
                raise ValueError(f"native release member is too large: {relative}")
            total_bytes += size
            if total_bytes > MAX_TOTAL_BYTES:
                raise ValueError("native release evidence is too large")
            files[relative] = path.read_bytes()
    if len(files) > MAX_ARCHIVE_ENTRIES:
        raise ValueError("native release evidence contains too many files")
    return files


def inspect_evidence_archive(
    bundle: Path,
) -> ArchiveInspection:
    entries, errors = inspect_archive(bundle)
    bundle_digest = (
        sha256_file(bundle) if bundle.is_file() and not bundle.is_symlink() else None
    )
    payloads: dict[str, dict[str, object]] = {}
    expected: set[str] = set()
    for key, (prefix, json_name, _) in EVIDENCE_LAYOUT.items():
        member_name = f"{prefix}/{json_name}"
        raw = entries.get(member_name)
        if raw is None:
            errors.append(f"native bundle is missing required member: {member_name}")
            continue
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"native bundle contains invalid {member_name}: {exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"native bundle {member_name} must contain a JSON object")
            continue
        payloads[key] = payload
        try:
            expected.update(evidence_members(prefix, json_name, payload))
        except ValueError as exc:
            errors.append(f"native bundle {member_name} is invalid: {exc}")
    if len(payloads) == len(EVIDENCE_LAYOUT):
        missing = sorted(expected - set(entries))
        unexpected = sorted(set(entries) - expected)
        if missing:
            errors.append("native bundle is missing declared files: " + ", ".join(missing))
        if unexpected:
            errors.append(
                "native bundle contains unexpected files: " + ", ".join(unexpected)
            )
    return ArchiveInspection(
        bundle=bundle,
        bundle_sha256=bundle_digest,
        entries=entries,
        payloads=payloads,
        errors=tuple(errors),
    )


def validate_bundle_evidence(
    inspection: ArchiveInspection,
    *,
    require_current_source: bool,
) -> list[str]:
    entries = inspection.entries
    payloads = inspection.payloads
    errors = list(inspection.errors)
    if errors:
        return errors
    with tempfile.TemporaryDirectory(prefix="design-craft-native-verify-") as raw:
        extracted = Path(raw)
        extract_entries(entries, extracted)
        for key, (prefix, json_name, expected_kind) in EVIDENCE_LAYOUT.items():
            payload = payloads[key]
            platform = key if key in {"ios", "android"} else payload.get("platform")
            if platform not in {"ios", "android"}:
                errors.append("real-device evidence platform must be ios or android")
                continue
            runtime_kind = expected_kind or f"{platform}_device"
            _, evidence_errors = validate_evidence(
                extracted / prefix / json_name,
                platform,
                runtime_kind,
                require_current_source=require_current_source,
                skill_root=DEFAULT_SKILL_ROOT,
                fixture_root=DEFAULT_FIXTURE_ROOT,
            )
            errors.extend(evidence_errors)
    return errors


def evidence_summary(
    prefix: str,
    json_name: str,
    payload: dict[str, object],
    evidence_json: bytes,
) -> dict[str, object]:
    return {
        "path": f"{prefix}/{json_name}",
        "sha256": sha256_bytes(evidence_json),
        "schema": payload.get("schema"),
        "platform": payload.get("platform"),
        "runtime_kind": payload.get("runtime_kind"),
        "source_commit": payload.get("source_commit"),
        "contract_sha256": payload.get("contract_sha256"),
        "artifact_count": len(payload.get("artifacts", [])),
    }


__all__ = [
    "ArchiveInspection",
    "EVIDENCE_LAYOUT",
    "EVIDENCE_SCHEMA",
    "archive_files",
    "copy_evidence",
    "evidence_summary",
    "inspect_evidence_archive",
    "validate_bundle_evidence",
]
