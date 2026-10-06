from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .contract_core import (
    ContractError,
)
from .contract_core import (
    run_file as _run_file,
)
from .contract_core import (
    safe_relative as _safe_relative,
)
from .evidence import receipt_configuration_errors
from .evidence_registry import EVIDENCE_ID_PATTERN, registered_artifact_path
from .jsonio import sha256_bytes, sha256_json
from .semantic_evidence import receipt_identity_payload, receipt_semantic_errors


def _append_evidence_refs(
    result: list[tuple[str, str]],
    value: Any,
    prefix: str,
) -> None:
    if not isinstance(value, list):
        return
    for index, reference in enumerate(value):
        if isinstance(reference, str):
            result.append((f"{prefix}[{index}]", reference))


def _evidence_references(data: dict[str, Any]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    _coverage_evidence_references(data.get("coverage"), result)
    _candidate_evidence_references(data.get("candidates"), result)
    _finding_evidence_references(data.get("findings"), result)
    _scorecard_evidence_references(data.get("scorecard"), result)
    return result


def _coverage_evidence_references(coverage: Any, result: list[tuple[str, str]]) -> None:
    if not isinstance(coverage, dict):
        return
    for index, row in enumerate(coverage.get("files", [])):
        if isinstance(row, dict):
            _append_evidence_refs(
                result, row.get("evidenceRefs"), f"coverage.files[{index}].evidenceRefs"
            )


def _candidate_evidence_references(candidates: Any, result: list[tuple[str, str]]) -> None:
    if not isinstance(candidates, list):
        return
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            continue
        for evidence_index, evidence in enumerate(candidate.get("evidence", [])):
            if isinstance(evidence, dict) and isinstance(evidence.get("ref"), str):
                result.append(
                    (
                        f"candidate-ledger[{index}].evidence[{evidence_index}].ref",
                        evidence["ref"],
                    )
                )
        validation = candidate.get("validation")
        if isinstance(validation, dict):
            _append_evidence_refs(
                result,
                validation.get("evidenceRefs"),
                f"candidate-ledger[{index}].validation.evidenceRefs",
            )


def _finding_evidence_references(findings: Any, result: list[tuple[str, str]]) -> None:
    if not isinstance(findings, dict):
        return
    for index, finding in enumerate(findings.get("findings", [])):
        if isinstance(finding, dict):
            _append_evidence_refs(
                result,
                finding.get("evidenceRefs"),
                f"findings.findings[{index}].evidenceRefs",
            )


def _scorecard_evidence_references(scorecard: Any, result: list[tuple[str, str]]) -> None:
    if not isinstance(scorecard, dict):
        return
    for dimension_index, dimension in enumerate(scorecard.get("dimensions", [])):
        if not isinstance(dimension, dict):
            continue
        for deduction_index, deduction in enumerate(dimension.get("deductions", [])):
            if isinstance(deduction, dict):
                _append_evidence_refs(
                    result,
                    deduction.get("evidenceRefs"),
                    f"scorecard.dimensions[{dimension_index}].deductions"
                    f"[{deduction_index}].evidenceRefs",
                )
    assurance = scorecard.get("assurance")
    verifier = assurance.get("verifier") if isinstance(assurance, dict) else None
    if isinstance(verifier, dict) and isinstance(verifier.get("evidenceRef"), str):
        result.append(("scorecard.assurance.verifier.evidenceRef", verifier["evidenceRef"]))


def _validate_evidence_registry(
    run_dir: Path,
    registry: Any,
    references: list[tuple[str, str]],
    errors: list[str],
) -> None:
    if not isinstance(registry, dict):
        errors.append("evidence-registry: expected a JSON object")
        return
    artifacts = registry.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("evidence-registry.artifacts: expected an array")
        return
    identifiers, paths = _validate_registry_entries(run_dir, artifacts, errors)
    _validate_registered_tree(run_dir, paths, errors)
    _validate_registered_references(references, identifiers, errors)


def _validate_registry_entries(
    run_dir: Path, artifacts: list[Any], errors: list[str]
) -> tuple[set[str], set[str]]:
    identifiers: set[str] = set()
    paths: set[str] = set()
    for index, entry in enumerate(artifacts):
        prefix = f"evidence-registry.artifacts[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: expected an object")
            continue
        identifier = _validate_registry_identity(entry, prefix, identifiers, paths, errors)
        path = entry.get("path")
        if identifier is None or not _safe_relative(path):
            continue
        try:
            artifact = _run_file(run_dir, path)
        except ContractError as error:
            errors.extend(f"{prefix}: {message}" for message in error.errors)
            continue
        content = artifact.read_bytes()
        if entry.get("sha256") != sha256_bytes(content):
            errors.append(f"{prefix}.sha256: does not match {path}")
        size_bytes = entry.get("sizeBytes")
        if (
            not isinstance(size_bytes, int)
            or isinstance(size_bytes, bool)
            or size_bytes != len(content)
        ):
            errors.append(f"{prefix}.sizeBytes: does not match {path}")
    return identifiers, paths


def _validate_registry_identity(
    entry: dict[str, Any],
    prefix: str,
    identifiers: set[str],
    paths: set[str],
    errors: list[str],
) -> str | None:
    identifier = entry.get("id")
    if not isinstance(identifier, str) or EVIDENCE_ID_PATTERN.fullmatch(identifier) is None:
        errors.append(f"{prefix}.id: expected a canonical registered evidence ID")
        identifier = None
    elif identifier in identifiers:
        errors.append(f"{prefix}.id: duplicate {identifier!r}")
    else:
        identifiers.add(identifier)
    path = entry.get("path")
    if not _safe_relative(path):
        errors.append(f"{prefix}.path: expected a safe run-relative path")
        return None
    if path in paths:
        errors.append(f"{prefix}.path: duplicate {path!r}")
    else:
        paths.add(path)
    if identifier is not None and path != registered_artifact_path(identifier):
        errors.append(f"{prefix}.path: expected {registered_artifact_path(identifier)}")
        return None
    return identifier


def _validate_registered_tree(run_dir: Path, paths: set[str], errors: list[str]) -> None:
    registered_root = run_dir / "evidence/registered"
    if registered_root.is_symlink():
        errors.append("evidence-registry.artifacts: registered root must not be a symlink")
    elif registered_root.exists():
        for artifact in sorted(registered_root.rglob("*")):
            if not (artifact.is_file() or artifact.is_symlink()):
                continue
            relative = artifact.relative_to(run_dir).as_posix()
            if relative not in paths:
                errors.append(f"evidence-registry.artifacts: unregistered artifact path {relative}")


def _validate_registered_references(
    references: list[tuple[str, str]], identifiers: set[str], errors: list[str]
) -> None:
    for prefix, reference in references:
        if not reference.startswith("artifact:"):
            continue
        identifier = reference.removeprefix("artifact:")
        if EVIDENCE_ID_PATTERN.fullmatch(identifier) is None:
            errors.append(f"{prefix}: expected artifact:<registered-id>")
        elif identifier not in identifiers:
            errors.append(f"{prefix}: unknown registered evidence ID {identifier!r}")


def _validate_receipt_artifact(
    run_dir: Path,
    receipt: dict[str, Any],
    command_id: str,
    *,
    field: str,
    hash_field: str,
    suffix: str,
    receipt_artifacts: set[str],
    errors: list[str],
    prefix: str,
) -> bytes | None:
    expected = f"evidence/commands/{command_id}.{suffix}"
    if receipt.get(field) != expected:
        errors.append(f"{prefix}: {field} must be {expected}")
        return None
    if expected in receipt_artifacts:
        errors.append(f"{prefix}: duplicate artifact path {expected}")
    else:
        receipt_artifacts.add(expected)
    try:
        artifact = _run_file(run_dir, expected)
    except ContractError as error:
        errors.extend(f"{prefix}: {message}" for message in error.errors)
        return None
    content = artifact.read_bytes()
    if receipt.get(hash_field) != sha256_bytes(content):
        errors.append(f"{prefix}: {hash_field} does not match {expected}")
    return content


def _validate_receipt_identity(
    receipt: dict[str, Any],
    command_id: Any,
    prefix: str,
    receipt_ids: set[str],
    receipt_sequences: set[int],
    errors: list[str],
) -> None:
    if isinstance(command_id, str):
        if command_id in receipt_ids:
            errors.append(f"{prefix}: duplicate id")
        else:
            receipt_ids.add(command_id)
    sequence = receipt.get("sequence")
    if isinstance(sequence, int) and not isinstance(sequence, bool):
        if sequence in receipt_sequences:
            errors.append(f"{prefix}: duplicate sequence")
        else:
            receipt_sequences.add(sequence)
    if command_id != sha256_json(receipt_identity_payload(receipt))[:16]:
        errors.append(f"{prefix}: id does not match receipt identity fields")


def _validate_command_receipts(
    run_dir: Path,
    receipts: list[dict[str, Any]],
    commands: dict[str, Any],
    errors: list[str],
) -> None:
    receipt_ids: set[str] = set()
    receipt_sequences: set[int] = set()
    receipt_artifacts: set[str] = set()
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            continue
        command_id = receipt.get("id")
        prefix = f"command receipt {command_id if isinstance(command_id, str) else index}"
        errors.extend(receipt_configuration_errors(receipt, commands, prefix=prefix))
        _validate_receipt_identity(
            receipt, command_id, prefix, receipt_ids, receipt_sequences, errors
        )
        if not isinstance(command_id, str) or re.fullmatch(r"[a-f0-9]{16}", command_id) is None:
            continue
        stdout_bytes: bytes | None = None
        for field, hash_field, suffix in (
            ("stdoutArtifact", "stdoutSha256", "stdout"),
            ("stderrArtifact", "stderrSha256", "stderr"),
        ):
            content = _validate_receipt_artifact(
                run_dir,
                receipt,
                command_id,
                field=field,
                hash_field=hash_field,
                suffix=suffix,
                receipt_artifacts=receipt_artifacts,
                errors=errors,
                prefix=prefix,
            )
            if field == "stdoutArtifact":
                stdout_bytes = content
        command = commands.get(receipt.get("name"))
        if stdout_bytes is not None and isinstance(command, dict):
            errors.extend(
                receipt_semantic_errors(receipt, command, stdout_bytes, run_dir, prefix=prefix)
            )
    if receipt_sequences != set(range(len(receipts))):
        errors.append("command receipts: sequence values must be contiguous from zero")
