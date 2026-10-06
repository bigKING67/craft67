from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import FIX_ATTEMPT_SCHEMA_VERSION
from .contracts import ContractError
from .delivery_contract import validate_artifact_reference
from .jsonio import read_json, sha256_json
from .remediation_attempt_contract import (
    attempt_assessment_rows,
    capture_failure_reasons,
    capture_status,
    final_failure_reasons,
    parse_timestamp,
    recovery_classification,
    validate_attempt_evidence_refs,
)
from .remediation_contract import validate_schema, verification_status
from .repository import fingerprint_inventory


def _read_artifact(
    delivery_dir: Path,
    reference: dict[str, Any],
    *,
    expected_path: str,
    schema_name: str | None = None,
) -> dict[str, Any]:
    path = validate_artifact_reference(
        delivery_dir,
        reference,
        expected_path=expected_path,
    )
    document = read_json(path)
    if not isinstance(document, dict):
        raise ContractError([f"{expected_path}: expected an object"])
    if schema_name is not None:
        validate_schema(document, schema_name)
    return document


def _delivery_identity_errors(
    *,
    plan: dict[str, Any],
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    assessment: dict[str, Any],
    verification: dict[str, Any],
    sequence: int,
) -> tuple[list[str], str]:
    attempt_id = manifest["attemptId"]
    errors: list[str] = []
    if manifest["sequence"] != sequence:
        errors.append(f"{attempt_id}: sequence must be contiguous from one")
    for document, label in (
        (manifest, "manifest"),
        (evidence, "evidence"),
        (assessment, "assessment"),
        (verification, "verification"),
    ):
        if document["fixId"] != plan["fixId"]:
            errors.append(f"{attempt_id}: {label} fixId does not match fix plan")
        if label != "manifest" and document["attemptId"] != attempt_id:
            errors.append(f"{attempt_id}: {label} attemptId does not match manifest")
    plan_hash = sha256_json(plan)
    if manifest["planSha256"] != plan_hash or evidence["planSha256"] != plan_hash:
        errors.append(f"{attempt_id}: plan hash does not match copied fix plan")
    if manifest["commandConfigSha256"] != plan["verification"]["commandConfigSha256"]:
        errors.append(f"{attempt_id}: command configuration hash does not match plan")
    if manifest["commands"] != plan["verification"]["commands"]:
        errors.append(f"{attempt_id}: command order does not match plan")
    if evidence["manifestSha256"] != sha256_json(manifest):
        errors.append(f"{attempt_id}: evidence manifest hash mismatch")
    if evidence["capturedAt"] != manifest["capturedAt"]:
        errors.append(f"{attempt_id}: evidence capturedAt does not match manifest")
    if parse_timestamp(
        evidence["completedAt"], f"{attempt_id}.evidence.completedAt"
    ) < parse_timestamp(manifest["capturedAt"], f"{attempt_id}.manifest.capturedAt"):
        errors.append(f"{attempt_id}: evidence completion precedes capture")
    return errors, plan_hash


def _delivery_predecessor_errors(
    *,
    manifest: dict[str, Any],
    previous: dict[str, Any] | None,
) -> list[str]:
    attempt_id = manifest["attemptId"]
    if previous is None:
        return (
            [f"{attempt_id}: first attempt must not name a predecessor"]
            if manifest["previousAttempt"] is not None
            else []
        )
    previous_manifest = previous["manifest"]
    expected_previous = {
        "attemptId": previous_manifest["attemptId"],
        "verificationSha256": sha256_json(previous["verification"]),
    }
    errors = []
    if manifest["previousAttempt"] != expected_previous:
        errors.append(f"{attempt_id}: predecessor binding mismatch")
    if manifest["sourceBeforeCommands"] != previous_manifest["sourceBeforeCommands"]:
        errors.append(f"{attempt_id}: retry source differs from predecessor")
    return errors


def _delivery_capture_errors(
    *,
    plan: dict[str, Any],
    manifest: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[list[str], bool]:
    attempt_id = manifest["attemptId"]
    errors: list[str] = []
    current_files = evidence["currentFiles"]
    if len({row["path"] for row in current_files}) != len(current_files):
        errors.append(f"{attempt_id}: current file paths must be unique")
    if fingerprint_inventory(current_files) != evidence["current"]["sourceFingerprint"]:
        errors.append(f"{attempt_id}: current file fingerprint mismatch")
    source_changed = (
        evidence["current"]["sourceFingerprint"] != plan["baseline"]["sourceFingerprint"]
    )
    if evidence["sourceChanged"] != source_changed:
        errors.append(f"{attempt_id}: sourceChanged does not match source fingerprint")
    result_names = [row["name"] for row in evidence["commands"]]
    if result_names + evidence["skippedCommands"] != plan["verification"]["commands"]:
        errors.append(f"{attempt_id}: command summaries do not follow plan order")
    capture_reasons = capture_failure_reasons(
        source_changed=source_changed,
        command_results=evidence["commands"],
        skipped_commands=evidence["skippedCommands"],
    )
    if evidence["failureReasons"] != capture_reasons:
        errors.append(f"{attempt_id}: capture failure reasons do not match evidence")
    if evidence["captureStatus"] != capture_status(
        source_changed=source_changed,
        failure_reasons=capture_reasons,
    ):
        errors.append(f"{attempt_id}: capture status does not match evidence")
    if (
        not any(row["repositoryMutationDetected"] for row in evidence["commands"])
        and manifest["sourceBeforeCommands"] != evidence["current"]
    ):
        errors.append(f"{attempt_id}: source changed during commands without mutation evidence")
    return errors, source_changed


def _delivery_assessment_errors(
    *,
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    assessment: dict[str, Any],
    verification: dict[str, Any],
) -> list[str]:
    attempt_id = manifest["attemptId"]
    errors: list[str] = []
    if assessment["attemptId"] != attempt_id:
        errors.append(f"{attempt_id}: assessment attemptId mismatch")
    if assessment["evidenceSha256"] != sha256_json(evidence):
        errors.append(f"{attempt_id}: assessment evidence hash mismatch")
    if parse_timestamp(
        assessment["assessedAt"], f"{attempt_id}.assessment.assessedAt"
    ) < parse_timestamp(evidence["completedAt"], f"{attempt_id}.evidence.completedAt"):
        errors.append(f"{attempt_id}: assessment precedes evidence completion")
    try:
        validate_attempt_evidence_refs(assessment=assessment, evidence=evidence)
    except ContractError as error:
        errors.extend(f"{attempt_id}: {message}" for message in error.errors)
    finalized_at = parse_timestamp(
        verification["finalizedAt"], f"{attempt_id}.verification.finalizedAt"
    )
    if finalized_at < parse_timestamp(
        assessment["assessedAt"], f"{attempt_id}.assessment.assessedAt"
    ) or finalized_at < parse_timestamp(
        evidence["completedAt"], f"{attempt_id}.evidence.completedAt"
    ):
        errors.append(f"{attempt_id}: verification precedes evidence or assessment")
    return errors


def _delivery_binding_errors(
    *,
    plan_hash: str,
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    assessment: dict[str, Any],
    verification: dict[str, Any],
) -> list[str]:
    terminal_bindings = {
        "planSha256": plan_hash,
        "manifestSha256": sha256_json(manifest),
        "evidenceSha256": sha256_json(evidence),
        "assessmentSha256": sha256_json(assessment),
        "captureStatus": evidence["captureStatus"],
        "sourceChanged": evidence["sourceChanged"],
        "current": evidence["current"],
        "changes": evidence["changes"],
        "commands": evidence["commands"],
        "skippedCommands": evidence["skippedCommands"],
        "assessmentKind": assessment["kind"],
        "measurements": assessment["measurements"],
        "remainingRisks": assessment["remainingRisks"],
    }
    attempt_id = manifest["attemptId"]
    return [
        f"{attempt_id}: verification {field} binding mismatch"
        for field, expected in terminal_bindings.items()
        if verification[field] != expected
    ]


def _delivery_finding_errors(
    *,
    plan: dict[str, Any],
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    assessment_rows: dict[str, dict[str, Any]],
    verification: dict[str, Any],
) -> list[str]:
    attempt_id = manifest["attemptId"]
    result_ids = [row["findingId"] for row in verification["findingResults"]]
    if len(result_ids) != len(set(result_ids)) or set(result_ids) != set(assessment_rows):
        return [f"{attempt_id}: verification finding results mismatch assessment"]
    errors: list[str] = []
    changed_paths = {row["path"] for row in evidence["changes"]}
    selections = {row["findingId"]: row for row in plan["selections"]}
    for result in verification["findingResults"]:
        assessed = assessment_rows[result["findingId"]]
        for field in ("status", "rationale", "evidenceRefs"):
            if result[field] != assessed[field]:
                errors.append(f"{attempt_id}: finding {result['findingId']} {field} mismatch")
        expected_locations = sorted(
            changed_paths.intersection(selections[result["findingId"]]["locationPaths"])
        )
        if result["locationPathsChanged"] != expected_locations:
            errors.append(f"{attempt_id}: finding {result['findingId']} changed locations mismatch")
    return errors


def _delivery_outcome_errors(
    *,
    sequence: int,
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    assessment: dict[str, Any],
    verification: dict[str, Any],
    previous: dict[str, Any] | None,
    source_changed: bool,
) -> list[str]:
    attempt_id = manifest["attemptId"]
    errors: list[str] = []
    expected_status = verification_status(
        source_changed=source_changed,
        command_results=evidence["commands"],
        skipped_commands=evidence["skippedCommands"],
        statuses=[row["status"] for row in verification["findingResults"]],
    )
    if verification["status"] != expected_status:
        errors.append(f"{attempt_id}: verification status does not match evidence")
    if verification["failureReasons"] != final_failure_reasons(evidence, assessment):
        errors.append(f"{attempt_id}: verification failure reasons mismatch")
    expected_recovery = recovery_classification(
        sequence=sequence,
        status=expected_status,
        previous_verification=(previous["verification"] if previous else None),
    )
    if verification["recoveryClassification"] != expected_recovery:
        errors.append(f"{attempt_id}: recovery classification mismatch")
    return errors


def _validate_attempt_documents(
    *,
    plan: dict[str, Any],
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    assessment: dict[str, Any],
    verification: dict[str, Any],
    previous: dict[str, Any] | None,
    sequence: int,
) -> tuple[list[str], dict[str, Any]]:
    assessment_rows = attempt_assessment_rows(assessment, plan)
    errors, plan_hash = _delivery_identity_errors(
        plan=plan,
        manifest=manifest,
        evidence=evidence,
        assessment=assessment,
        verification=verification,
        sequence=sequence,
    )
    errors.extend(_delivery_predecessor_errors(manifest=manifest, previous=previous))
    capture_errors, source_changed = _delivery_capture_errors(
        plan=plan, manifest=manifest, evidence=evidence
    )
    errors.extend(capture_errors)
    errors.extend(
        _delivery_assessment_errors(
            manifest=manifest,
            evidence=evidence,
            assessment=assessment,
            verification=verification,
        )
    )
    errors.extend(
        _delivery_binding_errors(
            plan_hash=plan_hash,
            manifest=manifest,
            evidence=evidence,
            assessment=assessment,
            verification=verification,
        )
    )
    errors.extend(
        _delivery_finding_errors(
            plan=plan,
            manifest=manifest,
            evidence=evidence,
            assessment_rows=assessment_rows,
            verification=verification,
        )
    )
    errors.extend(
        _delivery_outcome_errors(
            sequence=sequence,
            manifest=manifest,
            evidence=evidence,
            assessment=assessment,
            verification=verification,
            previous=previous,
            source_changed=source_changed,
        )
    )
    projection = {
        "attemptId": manifest["attemptId"],
        "sequence": manifest["sequence"],
        "capturedAt": manifest["capturedAt"],
        "captureStatus": evidence["captureStatus"],
        "status": verification["status"],
        "verificationSha256": sha256_json(verification),
        "recoveryClassification": verification["recoveryClassification"],
    }
    return errors, projection


def validate_attempt_delivery_source(
    delivery_dir: Path, attestation: dict[str, Any]
) -> dict[str, Any]:
    references = attestation["sourceArtifacts"]
    plan = _read_artifact(
        delivery_dir,
        references["fixPlan"],
        expected_path="source/fix-plan.json",
        schema_name="fix-plan.schema.json",
    )
    configuration = _read_artifact(
        delivery_dir,
        references["sourceConfiguration"],
        expected_path="source/source-configuration.json",
    )
    lineage = _read_artifact(
        delivery_dir,
        references["fixLineage"],
        expected_path="source/fix-lineage.json",
        schema_name="fix-lineage.schema.json",
    )
    errors: list[str] = []
    if lineage["schemaVersion"] != FIX_ATTEMPT_SCHEMA_VERSION:
        errors.append("copied fix lineage uses an unsupported protocol")
    if not isinstance(configuration, dict):
        errors.append("source-configuration.json: expected an object")

    rows = references["attempts"]
    attempt_ids = [row["attemptId"] for row in rows]
    if len(attempt_ids) != len(set(attempt_ids)):
        errors.append("delivery source attempt ids must be unique")
    attempts, projections, attempt_errors = _load_delivery_attempts(delivery_dir, plan, rows)
    errors.extend(attempt_errors)

    latest = projections[-1] if projections else None
    if latest is None:
        errors.append("delivery v2 requires at least one finalized attempt")
        aggregate = "NO_ATTEMPTS"
        recovery = "NONE"
    elif latest["status"] == "VERIFIED" and any(
        row["status"] != "VERIFIED" for row in projections[:-1]
    ):
        aggregate = "VERIFIED_WITH_RETRY"
        recovery = latest["recoveryClassification"]
    else:
        aggregate = latest["status"]
        recovery = latest["recoveryClassification"]
    expected_lineage = {
        "documentType": "review-craft.fix-lineage",
        "schemaVersion": FIX_ATTEMPT_SCHEMA_VERSION,
        "fixId": plan["fixId"],
        "planSha256": sha256_json(plan),
        "aggregateStatus": aggregate,
        "latestAttemptId": latest["attemptId"] if latest else None,
        "recoveryClassification": recovery,
        "attempts": projections,
    }
    if lineage != expected_lineage:
        errors.append("copied fix-lineage.json does not match copied attempt artifacts")

    fix = attestation["fix"]
    selected = attempts[-1] if attempts else None
    if selected is not None:
        manifest = selected["manifest"]
        evidence = selected["evidence"]
        assessment = selected["assessment"]
        verification = selected["verification"]
        expected_fix = {
            "protocol": FIX_ATTEMPT_SCHEMA_VERSION,
            "fixId": plan["fixId"],
            "attemptId": manifest["attemptId"],
            "reviewRunId": plan["review"]["runId"],
            "reviewTargetIdentity": plan["review"]["targetIdentity"],
            "repositoryName": plan["review"]["repositoryName"],
            "verificationStatus": verification["status"],
            "lineageStatus": lineage["aggregateStatus"],
            "recoveryClassification": lineage["recoveryClassification"],
            "planSha256": sha256_json(plan),
            "manifestSha256": sha256_json(manifest),
            "evidenceSha256": sha256_json(evidence),
            "assessmentSha256": sha256_json(assessment),
            "verificationSha256": sha256_json(verification),
            "lineageSha256": sha256_json(lineage),
            "sourceConfigurationSha256": sha256_json(configuration),
        }
        for field, expected in expected_fix.items():
            if fix[field] != expected:
                errors.append(f"delivery fix.{field}: does not match copied attempt lineage")
        if lineage["latestAttemptId"] != manifest["attemptId"]:
            errors.append("delivery selected attempt is not the latest lineage attempt")
        if verification["status"] != "VERIFIED":
            errors.append("delivery selected attempt verification must be VERIFIED")
        if lineage["aggregateStatus"] not in {"VERIFIED", "VERIFIED_WITH_RETRY"}:
            errors.append("delivery fix lineage must be verified")
    if errors:
        raise ContractError(errors)
    return {
        "plan": plan,
        "configuration": configuration,
        "lineage": lineage,
        "attempts": attempts,
        "verification": selected["verification"],
    }


def _load_delivery_attempts(
    delivery_dir: Path,
    plan: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    attempts: list[dict[str, Any]] = []
    projections: list[dict[str, Any]] = []
    errors: list[str] = []
    previous: dict[str, Any] | None = None
    for sequence, row in enumerate(rows, 1):
        attempt_id = row["attemptId"]
        root = f"source/attempts/{attempt_id}"
        manifest = _read_artifact(
            delivery_dir,
            row["manifest"],
            expected_path=f"{root}/attempt-manifest.json",
            schema_name="fix-attempt-manifest.schema.json",
        )
        evidence = _read_artifact(
            delivery_dir,
            row["evidence"],
            expected_path=f"{root}/attempt-evidence.json",
            schema_name="fix-attempt-evidence.schema.json",
        )
        assessment = _read_artifact(
            delivery_dir,
            row["assessment"],
            expected_path=f"{root}/fix-assessment.json",
            schema_name="fix-attempt-assessment.schema.json",
        )
        verification = _read_artifact(
            delivery_dir,
            row["verification"],
            expected_path=f"{root}/attempt-verification.json",
            schema_name="fix-attempt-verification.schema.json",
        )
        if manifest["attemptId"] != attempt_id:
            errors.append(f"{attempt_id}: manifest attemptId does not match artifact row")
        attempt = {
            "manifest": manifest,
            "evidence": evidence,
            "assessment": assessment,
            "verification": verification,
        }
        attempt_errors, projection = _validate_attempt_documents(
            plan=plan,
            manifest=manifest,
            evidence=evidence,
            assessment=assessment,
            verification=verification,
            previous=previous,
            sequence=sequence,
        )
        errors.extend(attempt_errors)
        attempts.append(attempt)
        projections.append(projection)
        previous = attempt
    return attempts, projections, errors
