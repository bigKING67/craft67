from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import ARTIFACT_PATHS
from .contracts import ContractError
from .evidence import receipt_configuration_errors
from .jsonio import read_json, read_jsonl, sha256_bytes, sha256_json
from .remediation_contract import (
    assessment_rows,
    changes,
    current_source,
    fix_source_configuration,
    load_fix,
    schema,
    session_file,
    stable_records,
    validate_evidence_refs,
    validate_review_provenance,
    validate_schema,
    verification_status,
)
from .schema_validation import validate_instance
from .semantic_evidence import receipt_identity_payload, receipt_semantic_errors


def validate_command_receipts(fix_dir: Path, commands: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = read_jsonl(session_file(fix_dir, ARTIFACT_PATHS["commands"]))
    errors: list[str] = []
    receipts: dict[str, dict[str, Any]] = {}
    sequences: set[int] = set()
    artifacts: set[str] = set()
    for index, row in enumerate(rows):
        errors.extend(
            f"command-receipt.schema.json[{index}]: {message}"
            for message in validate_instance(row, schema("command-receipt.schema.json"))
        )
        identifier = row.get("id")
        if not isinstance(identifier, str) or identifier in receipts:
            errors.append(f"fix command receipt {index}: id must be unique")
            continue
        receipts[identifier] = row
        errors.extend(
            receipt_configuration_errors(
                row,
                commands,
                prefix=f"fix command receipt {identifier}",
            )
        )
        sequence = row.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence in sequences:
            errors.append(f"fix command receipt {identifier}: sequence must be unique")
        else:
            sequences.add(sequence)
        expected_id = sha256_json(receipt_identity_payload(row))[:16]
        if identifier != expected_id:
            errors.append(f"fix command receipt {identifier}: id does not match identity fields")
        stdout_bytes: bytes | None = None
        for artifact_field, hash_field, suffix in (
            ("stdoutArtifact", "stdoutSha256", "stdout"),
            ("stderrArtifact", "stderrSha256", "stderr"),
        ):
            relative = row.get(artifact_field)
            if not isinstance(relative, str):
                continue
            expected = f"evidence/commands/{identifier}.{suffix}"
            if relative != expected:
                errors.append(
                    f"fix command receipt {identifier}: {artifact_field} must be {expected}"
                )
                continue
            if relative in artifacts:
                errors.append(f"fix command receipt {identifier}: duplicate artifact {relative}")
            artifacts.add(relative)
            try:
                artifact = session_file(fix_dir, relative)
            except ContractError as error:
                errors.extend(error.errors)
                continue
            content = artifact.read_bytes()
            if sha256_bytes(content) != row.get(hash_field):
                errors.append(f"fix command receipt {identifier}: {hash_field} mismatch")
            if artifact_field == "stdoutArtifact":
                stdout_bytes = content
        command = commands.get(row.get("name"))
        if stdout_bytes is not None and isinstance(command, dict):
            errors.extend(
                receipt_semantic_errors(
                    row,
                    command,
                    stdout_bytes,
                    fix_dir,
                    prefix=f"fix command receipt {identifier}",
                )
            )
    if sequences != set(range(len(rows))):
        errors.append("fix command receipts: sequence values must be contiguous from zero")
    if errors:
        raise ContractError(errors)
    return receipts


def validate_fix_snapshot(
    fix_dir_value: str | Path, *, require_verification: bool = True
) -> dict[str, Any]:
    """Validate immutable fix artifacts without comparing them to the live target."""
    fix_dir, plan, state = load_fix(fix_dir_value)
    validate_review_provenance(plan, state)
    receipts = validate_command_receipts(fix_dir, state["commands"])
    result_path = fix_dir / "fix-verification.json"
    assessment_path = fix_dir / "fix-assessment.json"
    if not require_verification and not result_path.exists() and not assessment_path.exists():
        if receipts:
            raise ContractError(
                ["prepared/incomplete fix session must not contain command receipts"]
            )
        return {"plan": plan, "verification": None}
    if not result_path.exists() or not assessment_path.exists():
        raise ContractError(["fix verification and assessment artifacts must both exist"])
    result = read_json(session_file(fix_dir, "fix-verification.json"))
    assessment = read_json(session_file(fix_dir, "fix-assessment.json"))
    validate_schema(result, "fix-verification.schema.json")
    assessment_rows(assessment, plan)
    errors: list[str] = []
    _validate_fix_verification_identity(result, plan, assessment, errors)
    _validate_fix_verification_commands(result, plan, receipts, errors)
    expected_changes = result["changes"]
    expected_source_changed = (
        result["current"]["sourceFingerprint"] != plan["baseline"]["sourceFingerprint"]
    )
    if result["sourceChanged"] != expected_source_changed:
        errors.append("fix-verification.sourceChanged: does not match captured source")
    _validate_fix_finding_results(result, plan, assessment, expected_changes, errors)
    expected_status = verification_status(
        source_changed=expected_source_changed,
        command_results=result["commands"],
        skipped_commands=result["skippedCommands"],
        statuses=[row["status"] for row in result["findingResults"]],
    )
    if result["status"] != expected_status:
        errors.append("fix-verification.status: does not match evidence and assessment")
    try:
        validate_evidence_refs(
            assessment=assessment,
            changes=expected_changes,
            command_results=result["commands"],
        )
    except ContractError as error:
        errors.extend(error.errors)
    if errors:
        raise ContractError(errors)
    return {"plan": plan, "state": state, "verification": result}


def _validate_fix_verification_identity(
    result: dict[str, Any],
    plan: dict[str, Any],
    assessment: dict[str, Any],
    errors: list[str],
) -> None:
    comparisons = (
        ("fixId", plan["fixId"], "fix plan"),
        ("planSha256", sha256_json(plan), "fix plan"),
        ("assessmentSha256", sha256_json(assessment), "assessment"),
        ("assessmentKind", assessment["kind"], "assessment"),
        ("remainingRisks", assessment["remainingRisks"], "assessment"),
    )
    for field, expected, source in comparisons:
        if result[field] != expected:
            errors.append(f"fix-verification.{field}: does not match {source}")


def _validate_fix_verification_commands(
    result: dict[str, Any],
    plan: dict[str, Any],
    receipts: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    names = [row["name"] for row in result["commands"]]
    if names + result["skippedCommands"] != plan["verification"]["commands"]:
        errors.append("fix-verification commands and skippedCommands: must match the planned order")
    receipt_ids = [row["receiptId"] for row in result["commands"]]
    if len(receipt_ids) != len(receipts) or set(receipt_ids) != set(receipts):
        errors.append("fix command receipt ledger must exactly match verification references")
    for command in result["commands"]:
        _validate_fix_verification_command(command, receipts, errors)


def _validate_fix_verification_command(
    command: dict[str, Any],
    receipts: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    receipt = receipts.get(command["receiptId"])
    if receipt is None or sha256_json(receipt) != command["receiptSha256"]:
        errors.append(f"fix-verification command {command['name']}: receipt content does not match")
        return
    for field in ("name", "exitCode", "timedOut", "repositoryMutationDetected"):
        if command[field] != receipt[field]:
            errors.append(
                f"fix-verification command {command['name']}: {field} does not match receipt"
            )
    if command.get("semanticEvidenceValid") != receipt.get("semanticEvidenceValid"):
        errors.append(
            f"fix-verification command {command['name']}: "
            "semanticEvidenceValid does not match receipt"
        )


def _validate_fix_finding_results(
    result: dict[str, Any],
    plan: dict[str, Any],
    assessment: dict[str, Any],
    changes: list[dict[str, Any]],
    errors: list[str],
) -> None:
    changed_paths = {row["path"] for row in changes}
    assessment_by_id = {row["findingId"]: row for row in assessment["findings"]}
    selection_by_id = {row["findingId"]: row for row in plan["selections"]}
    result_ids = [row["findingId"] for row in result["findingResults"]]
    if len(result_ids) != len(set(result_ids)) or set(result_ids) != set(assessment_by_id):
        errors.append("fix-verification.findingResults: must match assessed findings")
        return
    for row in result["findingResults"]:
        finding_id = row["findingId"]
        assessed = assessment_by_id[finding_id]
        for field in ("status", "rationale", "evidenceRefs"):
            if row[field] != assessed[field]:
                errors.append(
                    f"fix-verification finding {finding_id}: {field} does not match assessment"
                )
        expected_locations = sorted(
            changed_paths.intersection(selection_by_id[finding_id]["locationPaths"])
        )
        if row["locationPathsChanged"] != expected_locations:
            errors.append(
                f"fix-verification finding {finding_id}: changed locations do not match source"
            )


def validate_fix(fix_dir_value: str | Path, *, require_verification: bool = True) -> dict[str, Any]:
    data = validate_fix_snapshot(
        fix_dir_value,
        require_verification=require_verification,
    )
    result = data["verification"]
    if result is None:
        return {"plan": data["plan"], "verification": None}

    state = data["state"]
    target = Path(state["targetRoot"]).expanduser().resolve(strict=True)
    records, current = current_source(target, fix_source_configuration(state))
    expected_changes = changes(state["baselineFiles"], stable_records(records))
    errors: list[str] = []
    if current != result["current"]:
        errors.append("fix-verification.current: target source changed after verification")
    if expected_changes != result["changes"]:
        errors.append("fix-verification.changes: target changes no longer match verification")
    if errors:
        raise ContractError(errors)
    return {"plan": data["plan"], "verification": result}
