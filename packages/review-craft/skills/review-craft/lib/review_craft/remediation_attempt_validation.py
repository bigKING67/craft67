from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import ContractError
from .jsonio import read_json, sha256_json
from .remediation_attempt_contract import (
    attempt_assessment_rows,
    attempt_directories,
    attempt_timestamp_errors,
    capture_failure_reasons,
    capture_status,
    claim_observations,
    final_failure_reasons,
    load_attempt,
    parse_timestamp,
    recovery_classification,
    require_attempt_protocol_root,
    validate_attempt_evidence_refs,
    validate_measurements,
)
from .remediation_contract import (
    changes,
    current_source,
    fix_source_configuration,
    load_fix,
    session_file,
    stable_records,
    validate_review_provenance,
    validate_schema,
    verification_status,
)
from .remediation_validation import validate_command_receipts
from .repository import fingerprint_inventory


def _previous_verification(
    *, fix_dir: Path, manifest: dict[str, Any]
) -> dict[str, Any] | None:
    previous = manifest["previousAttempt"]
    if previous is None:
        return None
    path = fix_dir / "attempts" / previous["attemptId"]
    try:
        verification = read_json(session_file(path, "attempt-verification.json"))
    except (OSError, ValueError, ContractError) as error:
        raise ContractError(
            [f"fix attempt previous verification is unavailable: {error}"]
        ) from error
    validate_schema(verification, "fix-attempt-verification.schema.json")
    if sha256_json(verification) != previous["verificationSha256"]:
        raise ContractError(
            ["fix-attempt-manifest.previousAttempt: verification hash mismatch"]
        )
    return verification


def _capture_identity_errors(
    *, plan: dict[str, Any], manifest: dict[str, Any], evidence: dict[str, Any]
) -> tuple[list[str], str]:
    errors: list[str] = []
    plan_hash = sha256_json(plan)
    if manifest["fixId"] != plan["fixId"] or evidence["fixId"] != plan["fixId"]:
        errors.append("fix attempt fixId: does not match fix plan")
    if manifest["planSha256"] != plan_hash or evidence["planSha256"] != plan_hash:
        errors.append("fix attempt planSha256: does not match fix plan")
    if manifest["commandConfigSha256"] != plan["verification"]["commandConfigSha256"]:
        errors.append("fix-attempt-manifest.commandConfigSha256: plan mismatch")
    if manifest["commands"] != plan["verification"]["commands"]:
        errors.append("fix-attempt-manifest.commands: plan order mismatch")
    if evidence["manifestSha256"] != sha256_json(manifest):
        errors.append("fix-attempt-evidence.manifestSha256: manifest mismatch")
    if evidence["capturedAt"] != manifest["capturedAt"]:
        errors.append("fix-attempt-evidence.capturedAt: manifest mismatch")
    if parse_timestamp(evidence["completedAt"], "fix-attempt-evidence.completedAt") < (
        parse_timestamp(manifest["capturedAt"], "fix-attempt-manifest.capturedAt")
    ):
        errors.append("fix-attempt-evidence.completedAt: precedes capture start")
    return errors, plan_hash


def _capture_source_errors(
    *, plan: dict[str, Any], state: dict[str, Any], evidence: dict[str, Any]
) -> tuple[list[str], bool]:
    errors: list[str] = []
    current_files = evidence["currentFiles"]
    if len({row.get("path") for row in current_files}) != len(current_files):
        errors.append("fix-attempt-evidence.currentFiles: paths must be unique")
    if fingerprint_inventory(current_files) != evidence["current"]["sourceFingerprint"]:
        errors.append("fix-attempt-evidence.currentFiles: source fingerprint mismatch")
    expected_changes = changes(state["baselineFiles"], current_files)
    if evidence["changes"] != expected_changes:
        errors.append("fix-attempt-evidence.changes: current files mismatch")
    source_changed = (
        evidence["current"]["sourceFingerprint"] != plan["baseline"]["sourceFingerprint"]
    )
    if evidence["sourceChanged"] != source_changed:
        errors.append("fix-attempt-evidence.sourceChanged: captured source mismatch")
    return errors, source_changed


def _capture_receipt_errors(
    *, evidence: dict[str, Any], receipts: dict[str, dict[str, Any]]
) -> list[str]:
    errors: list[str] = []
    referenced = [row["receiptId"] for row in evidence["commands"]]
    if len(referenced) != len(receipts) or set(referenced) != set(receipts):
        errors.append("fix attempt receipt ledger must exactly match evidence references")
    for result in evidence["commands"]:
        receipt = receipts.get(result["receiptId"])
        if receipt is None or sha256_json(receipt) != result["receiptSha256"]:
            errors.append(f"fix-attempt-evidence command {result['name']}: receipt mismatch")
            continue
        for field in ("name", "exitCode", "timedOut", "repositoryMutationDetected"):
            if result[field] != receipt[field]:
                errors.append(
                    f"fix-attempt-evidence command {result['name']}: "
                    f"{field} does not match receipt"
                )
        if result.get("semanticEvidenceValid") != receipt.get("semanticEvidenceValid"):
            errors.append(
                f"fix-attempt-evidence command {result['name']}: "
                "semanticEvidenceValid does not match receipt"
            )
    return errors


def _capture_evidence_errors(
    *,
    attempt_dir: Path,
    plan: dict[str, Any],
    state: dict[str, Any],
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    receipts: dict[str, dict[str, Any]],
    source_changed: bool,
) -> list[str]:
    errors: list[str] = []
    result_names = [row["name"] for row in evidence["commands"]]
    if result_names + evidence["skippedCommands"] != plan["verification"]["commands"]:
        errors.append("fix-attempt-evidence commands: planned order mismatch")
    ordered_receipts = [
        receipt
        for row in evidence["commands"]
        if (receipt := receipts.get(row["receiptId"])) is not None
    ]
    if len(ordered_receipts) != len(evidence["commands"]):
        errors.append("fix-attempt-evidence.claimObservations: referenced receipt is missing")
        return errors
    expected_observations = claim_observations(
        attempt_dir=attempt_dir,
        receipts=ordered_receipts,
        commands=state["commands"],
    )
    if evidence["claimObservations"] != expected_observations:
        errors.append("fix-attempt-evidence.claimObservations: receipt output mismatch")
    expected_reasons = capture_failure_reasons(
        source_changed=source_changed,
        command_results=evidence["commands"],
        skipped_commands=evidence["skippedCommands"],
    )
    if evidence["failureReasons"] != expected_reasons:
        errors.append("fix-attempt-evidence.failureReasons: evidence mismatch")
    if evidence["captureStatus"] != capture_status(
        source_changed=source_changed, failure_reasons=expected_reasons
    ):
        errors.append("fix-attempt-evidence.captureStatus: evidence mismatch")
    if (
        not any(row["repositoryMutationDetected"] for row in evidence["commands"])
        and manifest["sourceBeforeCommands"] != evidence["current"]
    ):
        errors.append(
            "fix-attempt-evidence.current: changed during commands without mutation evidence"
        )
    return errors


def _terminal_paths(attempt_dir: Path, *, require_finalized: bool) -> bool:
    assessment_exists = (attempt_dir / "fix-assessment.json").exists()
    verification_exists = (attempt_dir / "attempt-verification.json").exists()
    if not assessment_exists and not verification_exists:
        if require_finalized:
            raise ContractError(["fix attempt is awaiting post-command assessment"])
        return False
    if not assessment_exists or not verification_exists:
        raise ContractError(["fix attempt assessment and verification artifacts must both exist"])
    return True


def _terminal_identity_errors(
    *,
    plan: dict[str, Any],
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    assessment: dict[str, Any],
    verification: dict[str, Any],
) -> tuple[list[str], str]:
    errors: list[str] = []
    evidence_hash = sha256_json(evidence)
    if assessment["fixId"] != plan["fixId"]:
        errors.append("fix-attempt-assessment.fixId: plan mismatch")
    if assessment["attemptId"] != manifest["attemptId"]:
        errors.append("fix-attempt-assessment.attemptId: manifest mismatch")
    if assessment["evidenceSha256"] != evidence_hash:
        errors.append("fix-attempt-assessment.evidenceSha256: evidence mismatch")
    errors.extend(
        attempt_timestamp_errors(
            evidence=evidence,
            assessment=assessment,
            finalized_at=verification["finalizedAt"],
        )
    )
    return errors, evidence_hash


def _terminal_binding_errors(
    *,
    plan: dict[str, Any],
    plan_hash: str,
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    evidence_hash: str,
    assessment: dict[str, Any],
    verification: dict[str, Any],
) -> list[str]:
    expected_fields = (
        ("fixId", plan["fixId"]),
        ("attemptId", manifest["attemptId"]),
        ("planSha256", plan_hash),
        ("manifestSha256", sha256_json(manifest)),
        ("evidenceSha256", evidence_hash),
        ("assessmentSha256", sha256_json(assessment)),
        ("captureStatus", evidence["captureStatus"]),
        ("sourceChanged", evidence["sourceChanged"]),
        ("current", evidence["current"]),
        ("changes", evidence["changes"]),
        ("commands", evidence["commands"]),
        ("skippedCommands", evidence["skippedCommands"]),
        ("assessmentKind", assessment["kind"]),
        ("measurements", assessment["measurements"]),
        ("remainingRisks", assessment["remainingRisks"]),
    )
    return [
        f"fix-attempt-verification.{field}: terminal artifact mismatch"
        for field, expected in expected_fields
        if verification[field] != expected
    ]


def _terminal_finding_errors(
    *,
    plan: dict[str, Any],
    evidence: dict[str, Any],
    assessment_by_id: dict[str, dict[str, Any]],
    verification: dict[str, Any],
) -> list[str]:
    result_ids = [row["findingId"] for row in verification["findingResults"]]
    if len(result_ids) != len(set(result_ids)) or set(result_ids) != set(assessment_by_id):
        return ["fix-attempt-verification.findingResults: assessment mismatch"]
    errors: list[str] = []
    changed_paths = {row["path"] for row in evidence["changes"]}
    selections = {row["findingId"]: row for row in plan["selections"]}
    for result in verification["findingResults"]:
        assessed = assessment_by_id[result["findingId"]]
        for field in ("status", "rationale", "evidenceRefs"):
            if result[field] != assessed[field]:
                errors.append(
                    f"fix-attempt-verification finding {result['findingId']}: "
                    f"{field} does not match assessment"
                )
        expected_locations = sorted(
            changed_paths.intersection(selections[result["findingId"]]["locationPaths"])
        )
        if result["locationPathsChanged"] != expected_locations:
            errors.append(
                f"fix-attempt-verification finding {result['findingId']}: "
                "changed locations mismatch"
            )
    return errors


def _terminal_conclusion_errors(
    *,
    fix_dir: Path,
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    assessment: dict[str, Any],
    verification: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected_status = verification_status(
        source_changed=evidence["sourceChanged"],
        command_results=evidence["commands"],
        skipped_commands=evidence["skippedCommands"],
        statuses=[row["status"] for row in verification["findingResults"]],
    )
    if verification["status"] != expected_status:
        errors.append("fix-attempt-verification.status: evidence mismatch")
    expected_failures = final_failure_reasons(evidence, assessment)
    if verification["failureReasons"] != expected_failures:
        errors.append("fix-attempt-verification.failureReasons: evidence mismatch")
    previous_verification = _previous_verification(fix_dir=fix_dir, manifest=manifest)
    expected_recovery = recovery_classification(
        sequence=manifest["sequence"],
        status=expected_status,
        previous_verification=previous_verification,
    )
    if verification["recoveryClassification"] != expected_recovery:
        errors.append("fix-attempt-verification.recoveryClassification: lineage mismatch")
    return errors


def _attempt_data(
    *,
    fix_dir: Path,
    plan: dict[str, Any],
    state: dict[str, Any],
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    assessment: dict[str, Any] | None,
    verification: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "fixDir": fix_dir,
        "plan": plan,
        "state": state,
        "manifest": manifest,
        "evidence": evidence,
        "assessment": assessment,
        "verification": verification,
    }


def validate_fix_attempt_snapshot(
    attempt_dir_value: str | Path, *, require_finalized: bool = True
) -> dict[str, Any]:
    attempt_dir, fix_dir, manifest, evidence = load_attempt(attempt_dir_value)
    _, plan, state = load_fix(fix_dir)
    validate_review_provenance(plan, state)
    require_attempt_protocol_root(fix_dir)
    receipts = validate_command_receipts(attempt_dir, state["commands"])
    errors, plan_hash = _capture_identity_errors(
        plan=plan, manifest=manifest, evidence=evidence
    )
    source_errors, source_changed = _capture_source_errors(
        plan=plan, state=state, evidence=evidence
    )
    errors.extend(source_errors)
    errors.extend(_capture_receipt_errors(evidence=evidence, receipts=receipts))
    errors.extend(
        _capture_evidence_errors(
            attempt_dir=attempt_dir,
            plan=plan,
            state=state,
            manifest=manifest,
            evidence=evidence,
            receipts=receipts,
            source_changed=source_changed,
        )
    )
    if errors:
        raise ContractError(errors)
    if not _terminal_paths(attempt_dir, require_finalized=require_finalized):
        return _attempt_data(
            fix_dir=fix_dir,
            plan=plan,
            state=state,
            manifest=manifest,
            evidence=evidence,
            assessment=None,
            verification=None,
        )

    assessment = read_json(session_file(attempt_dir, "fix-assessment.json"))
    verification = read_json(session_file(attempt_dir, "attempt-verification.json"))
    assessment_by_id = attempt_assessment_rows(assessment, plan)
    validate_schema(verification, "fix-attempt-verification.schema.json")
    terminal_errors, evidence_hash = _terminal_identity_errors(
        plan=plan,
        manifest=manifest,
        evidence=evidence,
        assessment=assessment,
        verification=verification,
    )
    try:
        validate_attempt_evidence_refs(assessment=assessment, evidence=evidence)
        validate_measurements(
            assessment=assessment, attempt_dir=attempt_dir, evidence=evidence
        )
    except ContractError as error:
        terminal_errors.extend(error.errors)
    terminal_errors.extend(
        _terminal_binding_errors(
            plan=plan,
            plan_hash=plan_hash,
            manifest=manifest,
            evidence=evidence,
            evidence_hash=evidence_hash,
            assessment=assessment,
            verification=verification,
        )
    )
    terminal_errors.extend(
        _terminal_finding_errors(
            plan=plan,
            evidence=evidence,
            assessment_by_id=assessment_by_id,
            verification=verification,
        )
    )
    terminal_errors.extend(
        _terminal_conclusion_errors(
            fix_dir=fix_dir,
            manifest=manifest,
            evidence=evidence,
            assessment=assessment,
            verification=verification,
        )
    )
    if terminal_errors:
        raise ContractError(terminal_errors)
    return _attempt_data(
        fix_dir=fix_dir,
        plan=plan,
        state=state,
        manifest=manifest,
        evidence=evidence,
        assessment=assessment,
        verification=verification,
    )


def validate_fix_attempt(
    attempt_dir_value: str | Path, *, compare_live: bool = True
) -> dict[str, Any]:
    data = validate_fix_attempt_snapshot(attempt_dir_value, require_finalized=True)
    if not compare_live:
        return data
    target = Path(data["state"]["targetRoot"]).expanduser().resolve(strict=True)
    records, current = current_source(
        target, fix_source_configuration(data["state"])
    )
    live_errors: list[str] = []
    if current != data["evidence"]["current"]:
        live_errors.append("fix attempt target source changed after evidence capture")
    if changes(data["state"]["baselineFiles"], stable_records(records)) != data[
        "evidence"
    ]["changes"]:
        live_errors.append("fix attempt target changes no longer match evidence")
    if live_errors:
        raise ContractError(live_errors)
    return data


def validate_fix_lineage(fix_dir_value: str | Path) -> dict[str, Any]:
    fix_dir, plan, state = load_fix(fix_dir_value)
    validate_review_provenance(plan, state)
    require_attempt_protocol_root(fix_dir)
    directories = attempt_directories(fix_dir)
    attempts: list[dict[str, Any]] = []
    previous_data: dict[str, Any] | None = None
    errors: list[str] = []
    for index, directory in enumerate(directories, 1):
        try:
            data = validate_fix_attempt_snapshot(
                directory, require_finalized=False
            )
        except ContractError as error:
            errors.extend(
                f"{directory.name}: {message}" for message in error.errors
            )
            continue
        manifest = data["manifest"]
        verification = data["verification"]
        if manifest["sequence"] != index:
            errors.append(
                f"{directory.name}: sequence must be contiguous from one"
            )
        if previous_data is None:
            if manifest["previousAttempt"] is not None:
                errors.append(
                    f"{directory.name}: first attempt must not name a predecessor"
                )
        else:
            previous_verification = previous_data["verification"]
            if previous_verification is None:
                errors.append(
                    f"{directory.name}: predecessor is not finalized"
                )
            else:
                expected_previous = {
                    "attemptId": previous_data["manifest"]["attemptId"],
                    "verificationSha256": sha256_json(previous_verification),
                }
                if manifest["previousAttempt"] != expected_previous:
                    errors.append(
                        f"{directory.name}: predecessor binding mismatch"
                    )
            if (
                manifest["sourceBeforeCommands"]
                != previous_data["manifest"]["sourceBeforeCommands"]
            ):
                errors.append(
                    f"{directory.name}: retry source differs from predecessor"
                )
        if verification is None and index != len(directories):
            errors.append(
                f"{directory.name}: only the latest attempt may await assessment"
            )
        attempts.append(
            {
                "attemptId": manifest["attemptId"],
                "sequence": manifest["sequence"],
                "capturedAt": manifest["capturedAt"],
                "captureStatus": data["evidence"]["captureStatus"],
                "status": (
                    verification["status"]
                    if verification is not None
                    else "AWAITING_ASSESSMENT"
                ),
                "verificationSha256": (
                    sha256_json(verification) if verification is not None else None
                ),
                "recoveryClassification": (
                    verification["recoveryClassification"]
                    if verification is not None
                    else None
                ),
            }
        )
        previous_data = data
    if errors:
        raise ContractError(errors)

    latest = attempts[-1] if attempts else None
    if latest is None:
        aggregate = "NO_ATTEMPTS"
        recovery = "NONE"
    elif latest["status"] == "AWAITING_ASSESSMENT":
        aggregate = "AWAITING_ASSESSMENT"
        recovery = "NONE"
    elif latest["status"] == "VERIFIED" and any(
        row["status"] != "VERIFIED" for row in attempts[:-1]
    ):
        aggregate = "VERIFIED_WITH_RETRY"
        recovery = latest["recoveryClassification"] or "NONE"
    else:
        aggregate = latest["status"]
        recovery = latest["recoveryClassification"] or "NONE"
    lineage = {
        "documentType": "review-craft.fix-lineage",
        "schemaVersion": "review-craft.fix-attempt.v1",
        "fixId": plan["fixId"],
        "planSha256": sha256_json(plan),
        "aggregateStatus": aggregate,
        "latestAttemptId": latest["attemptId"] if latest else None,
        "recoveryClassification": recovery,
        "attempts": attempts,
    }
    validate_schema(lineage, "fix-lineage.schema.json")
    return {"fixDir": fix_dir, "plan": plan, "lineage": lineage}
