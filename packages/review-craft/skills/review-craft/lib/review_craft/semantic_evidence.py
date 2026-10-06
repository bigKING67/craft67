from __future__ import annotations

import hashlib
import os
import re
import stat
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

from .configuration import DEFAULT_ARTIFACT_MAX_BYTES
from .jsonio import json_pointer_value, parse_json_bytes

SEMANTIC_FIELDS = ("semanticEvidenceValid", "evidenceClaims", "evidenceArtifacts")
CapturedArtifact = tuple[dict[str, Any], Path | None]


def receipt_identity_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "name": receipt.get("name"),
        "argv": receipt.get("argv"),
        "startedAt": receipt.get("startedAt"),
        "cwd": receipt.get("cwd"),
        "sequence": receipt.get("sequence"),
    }
    if any(field in receipt for field in SEMANTIC_FIELDS):
        payload["semanticEvidenceValid"] = receipt.get("semanticEvidenceValid")
        payload["evidenceClaims"] = receipt.get("evidenceClaims")
        payload["evidenceArtifacts"] = [
            {key: value for key, value in row.items() if key != "storedArtifact"}
            for row in receipt.get("evidenceArtifacts", [])
            if isinstance(row, dict)
        ]
    return payload


def semantic_evidence_declared(command: dict[str, Any]) -> bool:
    return bool(command.get("evidenceClaims") or command.get("artifacts"))


def _structured_output(stdout: bytes) -> tuple[bool, Any]:
    try:
        return True, parse_json_bytes(stdout)
    except (UnicodeDecodeError, ValueError):
        return False, None


def _claim_results(
    command: dict[str, Any], document: Any, output_valid: bool
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for declaration in command.get("evidenceClaims", []):
        found, actual = (
            json_pointer_value(document, declaration["jsonPointer"])
            if output_valid
            else (False, None)
        )
        expected = declaration["equals"]
        matches = (
            found
            and actual == expected
            and (not isinstance(actual, bool) or isinstance(expected, bool))
            and (not isinstance(expected, bool) or isinstance(actual, bool))
        )
        results.append(
            {
                "id": declaration["id"],
                "kind": declaration["kind"],
                "status": "VERIFIED" if matches else "UNVERIFIED",
            }
        )
    return results


def _pointer_scalar(document: Any, output_valid: bool, pointer: str | None) -> tuple[bool, Any]:
    if pointer is None:
        return True, None
    if not output_valid:
        return False, None
    return json_pointer_value(document, pointer)


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _artifact_roots(session_dir: Path) -> list[Path]:
    candidates = [Path(tempfile.gettempdir()), Path("/tmp"), Path("/private/tmp"), session_dir]
    roots: list[Path] = []
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve(strict=True)
        except OSError:
            continue
        if resolved not in roots:
            roots.append(resolved)
    return roots


def _stage_artifact(
    *, source: Path, session_dir: Path, maximum: int
) -> tuple[Path | None, str | None, int | None, str | None]:
    try:
        metadata = source.stat(follow_symlinks=False)
    except OSError:
        return None, None, None, "MISSING"
    if not stat.S_ISREG(metadata.st_mode) or source.is_symlink():
        return None, None, None, "REJECTED"
    if metadata.st_size > maximum:
        return None, None, None, "TOO_LARGE"
    staging_dir = session_dir / "evidence" / ".artifact-staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    staged: Path | None = None
    try:
        digest = hashlib.sha256()
        size = 0
        with (
            source.open("rb") as input_handle,
            tempfile.NamedTemporaryFile(
                mode="wb", dir=staging_dir, prefix="artifact-", delete=False
            ) as output_handle,
        ):
            staged = Path(output_handle.name)
            before = os.fstat(input_handle.fileno())
            while chunk := input_handle.read(1024 * 1024):
                size += len(chunk)
                if size > maximum:
                    output_handle.close()
                    staged.unlink(missing_ok=True)
                    return None, None, None, "TOO_LARGE"
                digest.update(chunk)
                output_handle.write(chunk)
            output_handle.flush()
            os.fsync(output_handle.fileno())
            after = os.fstat(input_handle.fileno())
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            staged.unlink(missing_ok=True)
            return None, None, None, "REJECTED"
        return staged, digest.hexdigest(), size, None
    except OSError:
        if staged is not None:
            staged.unlink(missing_ok=True)
        return None, None, None, "MISSING"


def _file_digest_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def _capture_artifacts(
    *,
    command: dict[str, Any],
    document: Any,
    output_valid: bool,
    session_dir: Path,
    target: Path,
) -> list[CapturedArtifact]:
    captured: list[CapturedArtifact] = []
    roots = _artifact_roots(session_dir)
    for declaration in command.get("artifacts", []):
        found, raw_path = _pointer_scalar(document, output_valid, declaration["pathJsonPointer"])
        row: dict[str, Any] = {
            "id": declaration["id"],
            "status": "INVALID_OUTPUT" if not output_valid else "MISSING",
            "sourcePath": raw_path if found and isinstance(raw_path, str) else None,
            "storedArtifact": None,
            "sha256": None,
            "sizeBytes": None,
        }
        if not output_valid:
            captured.append((row, None))
            continue
        if not found or not isinstance(raw_path, str) or not raw_path:
            captured.append((row, None))
            continue
        source = Path(raw_path)
        if not source.is_absolute() or source.is_symlink():
            row["status"] = "REJECTED"
            captured.append((row, None))
            continue
        try:
            resolved = source.resolve(strict=True)
        except OSError:
            row["status"] = "MISSING"
            captured.append((row, None))
            continue
        if _path_within(resolved, target) or not any(
            _path_within(resolved, root) for root in roots
        ):
            row["status"] = "REJECTED"
            captured.append((row, None))
            continue
        staged, digest, size, capture_status = _stage_artifact(
            source=source,
            session_dir=session_dir,
            maximum=declaration.get("maxBytes", DEFAULT_ARTIFACT_MAX_BYTES),
        )
        if digest is None or size is None:
            row["status"] = capture_status or "MISSING"
            captured.append((row, None))
            continue
        row["sha256"] = digest
        row["sizeBytes"] = size
        expected_sha_found, expected_sha = _pointer_scalar(
            document, output_valid, declaration.get("sha256JsonPointer")
        )
        expected_size_found, expected_size = _pointer_scalar(
            document, output_valid, declaration.get("sizeBytesJsonPointer")
        )
        metadata_valid = (
            expected_sha_found
            and expected_size_found
            and (
                "sha256JsonPointer" not in declaration
                or (
                    isinstance(expected_sha, str)
                    and re.fullmatch(r"[a-f0-9]{64}", expected_sha) is not None
                )
            )
            and (
                "sizeBytesJsonPointer" not in declaration
                or (
                    isinstance(expected_size, int)
                    and not isinstance(expected_size, bool)
                    and expected_size >= 0
                )
            )
        )
        if not metadata_valid:
            row["status"] = "INVALID_OUTPUT"
        elif ("sha256JsonPointer" in declaration and expected_sha != digest) or (
            "sizeBytesJsonPointer" in declaration and expected_size != size
        ):
            row["status"] = "MISMATCH"
        else:
            row["status"] = "VERIFIED"
        captured.append((row, staged))
    return captured


def capture_semantic_evidence(
    *,
    command: dict[str, Any],
    stdout: bytes,
    session_dir: Path,
    target: Path,
) -> tuple[list[dict[str, Any]], list[CapturedArtifact], bool]:
    output_valid, document = _structured_output(stdout)
    claims = _claim_results(command, document, output_valid)
    artifacts = _capture_artifacts(
        command=command,
        document=document,
        output_valid=output_valid,
        session_dir=session_dir,
        target=target,
    )
    valid = all(row["status"] == "VERIFIED" for row in claims) and all(
        row["status"] == "VERIFIED" for row, _ in artifacts
    )
    return claims, artifacts, valid


def store_captured_artifacts(
    *,
    captured: list[CapturedArtifact],
    evidence_dir: Path,
    command_id: str,
    session_dir: Path,
) -> None:
    for row, staged in captured:
        if staged is None:
            continue
        destination = evidence_dir / f"{command_id}.artifacts" / row["id"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        staged.replace(destination)
        row["storedArtifact"] = destination.relative_to(session_dir).as_posix()
    staging_dir = session_dir / "evidence" / ".artifact-staging"
    with suppress(OSError):
        staging_dir.rmdir()


def receipt_semantic_errors(
    receipt: dict[str, Any],
    command: dict[str, Any],
    stdout: bytes,
    session_dir: Path,
    *,
    prefix: str,
) -> list[str]:
    declarations_present = semantic_evidence_declared(command)
    fields_present = any(field in receipt for field in SEMANTIC_FIELDS)
    if not declarations_present:
        return (
            [f"{prefix}: semantic evidence is not configured for this command"]
            if fields_present
            else []
        )
    errors: list[str] = []
    if not all(field in receipt for field in SEMANTIC_FIELDS):
        return [f"{prefix}: semantic evidence fields are required by the configured command"]
    output_valid, document = _structured_output(stdout)
    expected_claims = _claim_results(command, document, output_valid)
    if receipt.get("evidenceClaims") != expected_claims:
        errors.append(f"{prefix}: evidenceClaims do not match structured stdout assertions")
    artifact_rows = receipt.get("evidenceArtifacts")
    if not isinstance(artifact_rows, list):
        errors.append(f"{prefix}: evidenceArtifacts must be an array")
        artifact_rows = []
    declarations = command.get("artifacts", [])
    if [row.get("id") for row in artifact_rows if isinstance(row, dict)] != [
        row["id"] for row in declarations
    ]:
        errors.append(f"{prefix}: evidenceArtifacts do not match configured artifact order")
    for declaration, row in zip(declarations, artifact_rows, strict=False):
        if not isinstance(row, dict):
            continue
        _validate_semantic_artifact(
            receipt, declaration, row, document, output_valid, session_dir, prefix, errors
        )
    semantic_valid = all(row["status"] == "VERIFIED" for row in expected_claims) and all(
        isinstance(row, dict) and row.get("status") == "VERIFIED" for row in artifact_rows
    )
    if receipt.get("semanticEvidenceValid") is not semantic_valid:
        errors.append(f"{prefix}: semanticEvidenceValid does not match claim and artifact status")
    return errors


def _validate_semantic_artifact(
    receipt: dict[str, Any],
    declaration: dict[str, Any],
    row: dict[str, Any],
    document: Any,
    output_valid: bool,
    session_dir: Path,
    prefix: str,
    errors: list[str],
) -> None:
    found, raw_path = _pointer_scalar(document, output_valid, declaration["pathJsonPointer"])
    expected_source = raw_path if found and isinstance(raw_path, str) else None
    if row.get("sourcePath") != expected_source:
        errors.append(
            f"{prefix}: evidence artifact {declaration['id']} sourcePath does not match stdout"
        )
    stored = row.get("storedArtifact")
    digest = row.get("sha256")
    size = row.get("sizeBytes")
    if stored is None:
        if row.get("status") in {"VERIFIED", "MISMATCH"} or digest is not None or size is not None:
            errors.append(
                f"{prefix}: evidence artifact {declaration['id']} has incomplete stored evidence"
            )
        return
    resolved = _resolve_semantic_artifact(receipt, declaration, stored, session_dir, prefix, errors)
    if resolved is None:
        return
    actual_digest, actual_size = _file_digest_size(resolved)
    if digest != actual_digest:
        errors.append(f"{prefix}: evidence artifact sha256 does not match {declaration['id']}")
    if size != actual_size:
        errors.append(f"{prefix}: evidence artifact sizeBytes does not match {declaration['id']}")
    expected_status = _semantic_artifact_status(
        declaration, document, output_valid, actual_digest, actual_size
    )
    if row.get("status") != expected_status:
        errors.append(
            f"{prefix}: evidence artifact {declaration['id']} status must be {expected_status}"
        )


def _resolve_semantic_artifact(
    receipt: dict[str, Any],
    declaration: dict[str, Any],
    stored: Any,
    session_dir: Path,
    prefix: str,
    errors: list[str],
) -> Path | None:
    expected = f"evidence/commands/{receipt.get('id')}.artifacts/{declaration['id']}"
    if stored != expected:
        errors.append(
            f"{prefix}: evidence artifact {declaration['id']} storedArtifact must be {expected}"
        )
        return None
    path = session_dir / stored
    if path.is_symlink():
        errors.append(f"{prefix}: evidence artifact {declaration['id']} must not be a symlink")
        return None
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(session_dir)
    except (OSError, ValueError) as error:
        errors.append(f"{prefix}: invalid evidence artifact {declaration['id']}: {error}")
        return None
    if not resolved.is_file():
        errors.append(f"{prefix}: evidence artifact {declaration['id']} must be a file")
        return None
    maximum = declaration.get("maxBytes", DEFAULT_ARTIFACT_MAX_BYTES)
    if resolved.stat().st_size > maximum:
        errors.append(f"{prefix}: evidence artifact {declaration['id']} exceeds maxBytes {maximum}")
        return None
    return resolved


def _semantic_artifact_status(
    declaration: dict[str, Any],
    document: Any,
    output_valid: bool,
    actual_digest: str,
    actual_size: int,
) -> str:
    sha_found, expected_sha = _pointer_scalar(
        document, output_valid, declaration.get("sha256JsonPointer")
    )
    size_found, expected_size = _pointer_scalar(
        document, output_valid, declaration.get("sizeBytesJsonPointer")
    )
    metadata_valid = (
        output_valid
        and sha_found
        and size_found
        and (
            "sha256JsonPointer" not in declaration
            or isinstance(expected_sha, str)
            and re.fullmatch(r"[a-f0-9]{64}", expected_sha) is not None
        )
        and (
            "sizeBytesJsonPointer" not in declaration
            or isinstance(expected_size, int)
            and not isinstance(expected_size, bool)
            and expected_size >= 0
        )
    )
    if not metadata_valid:
        return "INVALID_OUTPUT"
    if (
        "sha256JsonPointer" in declaration
        and expected_sha != actual_digest
        or "sizeBytesJsonPointer" in declaration
        and expected_size != actual_size
    ):
        return "MISMATCH"
    return "VERIFIED"
