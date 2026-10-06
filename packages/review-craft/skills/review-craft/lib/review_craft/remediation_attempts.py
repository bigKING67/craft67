from __future__ import annotations

from pathlib import Path
from typing import Any

from . import __version__
from .constants import FIX_ATTEMPT_SCHEMA_VERSION
from .contracts import ContractError
from .evidence import run_configured_command
from .jsonio import read_json, read_jsonl, sha256_json, write_json, write_jsonl
from .locking import exclusive_file_lock
from .remediation_attempt_contract import (
    attempt_assessment_rows,
    attempt_directories,
    attempt_timestamp_errors,
    capture_failure_reasons,
    capture_status,
    claim_observations,
    command_result,
    final_failure_reasons,
    load_attempt,
    recovery_classification,
    require_attempt_protocol_root,
    validate_attempt_evidence_refs,
    validate_measurements,
)
from .remediation_attempt_validation import (
    validate_fix_attempt_snapshot,
    validate_fix_lineage,
)
from .remediation_contract import (
    changes,
    current_source,
    fix_source_configuration,
    load_fix,
    session_file,
    stable_records,
    utc_now,
    validate_review_provenance,
    validate_schema,
    verification_status,
)

FIX_ATTEMPT_LOCK = ".fix-attempt.lock"


def _attempt_wait_seconds(plan: dict[str, Any], state: dict[str, Any]) -> int:
    return (
        sum(
            int(state["commands"][name].get("timeoutSeconds", 600))
            for name in plan["verification"]["commands"]
        )
        + 30
    )


def _require_stable_repository_identity(
    plan: dict[str, Any], source: dict[str, Any]
) -> None:
    errors = [
        f"fix target {field} changed after preparation"
        for field in ("revision", "branch", "remote")
        if source[field] != plan["baseline"][field]
    ]
    if errors:
        raise ContractError(errors)


def capture_fix_attempt(
    fix_dir_value: str | Path,
    *,
    captured_at: str | None = None,
    completed_at: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    fix_dir, plan, state = load_fix(fix_dir_value)
    with exclusive_file_lock(
        fix_dir,
        name=FIX_ATTEMPT_LOCK,
        wait_seconds=_attempt_wait_seconds(plan, state),
        timeout_message="timed out waiting for another fix attempt to finish",
    ):
        fix_dir, plan, state = load_fix(fix_dir)
        validate_review_provenance(plan, state)
        require_attempt_protocol_root(fix_dir)
        lineage = validate_fix_lineage(fix_dir)["lineage"]
        if lineage["aggregateStatus"] == "AWAITING_ASSESSMENT":
            raise ContractError(
                ["latest fix attempt must be finalized before capturing a retry"]
            )
        if lineage["aggregateStatus"] in {"VERIFIED", "VERIFIED_WITH_RETRY"}:
            raise ContractError(
                ["latest fix attempt is already verified; prepare a new fix baseline"]
            )

        target = Path(state["targetRoot"]).expanduser().resolve(strict=True)
        source_configuration = fix_source_configuration(state)
        _, source_before = current_source(target, source_configuration)
        _require_stable_repository_identity(plan, source_before)
        existing = attempt_directories(fix_dir)
        previous_manifest: dict[str, Any] | None = None
        previous_verification: dict[str, Any] | None = None
        if existing:
            previous_dir = existing[-1]
            previous_manifest = read_json(
                session_file(previous_dir, "attempt-manifest.json")
            )
            previous_verification = read_json(
                session_file(previous_dir, "attempt-verification.json")
            )
            if source_before != previous_manifest["sourceBeforeCommands"]:
                raise ContractError(
                    [
                        "fix retry source, revision, branch, or Git status changed; "
                        "prepare a new fix baseline"
                    ]
                )
        elif (
            source_before["sourceFingerprint"]
            == plan["baseline"]["sourceFingerprint"]
        ):
            raise ContractError(
                ["first fix attempt requires a source change from the prepared baseline"]
            )

        captured_at = captured_at or utc_now()
        sequence = len(existing) + 1
        previous = (
            {
                "attemptId": previous_manifest["attemptId"],
                "verificationSha256": sha256_json(previous_verification),
            }
            if previous_manifest is not None and previous_verification is not None
            else None
        )
        seed = {
            "fixId": plan["fixId"],
            "sequence": sequence,
            "capturedAt": captured_at,
            "source": source_before,
            "previousAttempt": previous,
        }
        attempt_id = f"attempt-{sequence:04d}-{sha256_json(seed)[:12]}"
        attempt_dir = fix_dir / "attempts" / attempt_id
        attempt_dir.mkdir(parents=True, mode=0o700)
        write_jsonl(attempt_dir / "evidence/commands.jsonl", [])

        command_results: list[dict[str, Any]] = []
        planned_commands = plan["verification"]["commands"]
        for name in planned_commands:
            _, receipt = run_configured_command(
                session_dir=attempt_dir,
                target=target,
                commands=state["commands"],
                command_name=name,
                allow_repository_mutation=False,
                source_configuration=source_configuration,
            )
            command_results.append(command_result(receipt))
            if receipt["repositoryMutationDetected"]:
                break
        skipped_commands = planned_commands[len(command_results) :]
        after_records, current = current_source(target, source_configuration)
        current_files = stable_records(after_records)
        source_changes = changes(state["baselineFiles"], current_files)
        source_changed = (
            current["sourceFingerprint"] != plan["baseline"]["sourceFingerprint"]
        )
        receipt_rows = read_jsonl(attempt_dir / "evidence/commands.jsonl")
        receipts_by_id = {row["id"]: row for row in receipt_rows}
        ordered_receipts = [
            receipts_by_id[row["receiptId"]] for row in command_results
        ]
        observations = claim_observations(
            attempt_dir=attempt_dir,
            receipts=ordered_receipts,
            commands=state["commands"],
        )
        failure_reasons = capture_failure_reasons(
            source_changed=source_changed,
            command_results=command_results,
            skipped_commands=skipped_commands,
        )
        manifest = {
            "documentType": "review-craft.fix-attempt-manifest",
            "schemaVersion": FIX_ATTEMPT_SCHEMA_VERSION,
            "toolVersion": __version__,
            "fixId": plan["fixId"],
            "attemptId": attempt_id,
            "sequence": sequence,
            "capturedAt": captured_at,
            "planSha256": sha256_json(plan),
            "commandConfigSha256": plan["verification"]["commandConfigSha256"],
            "commands": planned_commands,
            "sourceBeforeCommands": source_before,
            "previousAttempt": previous,
        }
        evidence = {
            "documentType": "review-craft.fix-attempt-evidence",
            "schemaVersion": FIX_ATTEMPT_SCHEMA_VERSION,
            "toolVersion": __version__,
            "fixId": plan["fixId"],
            "attemptId": attempt_id,
            "capturedAt": captured_at,
            "completedAt": completed_at or utc_now(),
            "planSha256": sha256_json(plan),
            "manifestSha256": sha256_json(manifest),
            "sourceChanged": source_changed,
            "current": current,
            "currentFiles": current_files,
            "changes": source_changes,
            "commands": command_results,
            "skippedCommands": skipped_commands,
            "claimObservations": observations,
            "captureStatus": capture_status(
                source_changed=source_changed, failure_reasons=failure_reasons
            ),
            "failureReasons": failure_reasons,
        }
        validate_schema(manifest, "fix-attempt-manifest.schema.json")
        validate_schema(evidence, "fix-attempt-evidence.schema.json")
        write_json(attempt_dir / "attempt-manifest.json", manifest, mode=0o600)
        write_json(attempt_dir / "attempt-evidence.json", evidence, mode=0o600)
        validate_fix_attempt_snapshot(attempt_dir, require_finalized=False)
        validate_fix_lineage(fix_dir)
        return attempt_dir, evidence


def finalize_fix_attempt(
    attempt_dir_value: str | Path,
    *,
    assessment_path: str | Path,
    finalized_at: str | None = None,
) -> dict[str, Any]:
    attempt_dir, fix_dir, manifest, evidence = load_attempt(attempt_dir_value)
    _, plan, state = load_fix(fix_dir)
    with exclusive_file_lock(
        fix_dir,
        name=FIX_ATTEMPT_LOCK,
        wait_seconds=30,
        timeout_message="timed out waiting for another fix attempt operation",
    ):
        attempt_dir, fix_dir, manifest, evidence = load_attempt(attempt_dir)
        _, plan, state = load_fix(fix_dir)
        validate_review_provenance(plan, state)
        require_attempt_protocol_root(fix_dir)
        lineage = validate_fix_lineage(fix_dir)["lineage"]
        if lineage["latestAttemptId"] != manifest["attemptId"]:
            raise ContractError(["only the latest fix attempt can be finalized"])
        if (attempt_dir / "fix-assessment.json").exists() or (
            attempt_dir / "attempt-verification.json"
        ).exists():
            raise ContractError(["fix attempt is already finalized or incomplete"])
        validate_fix_attempt_snapshot(attempt_dir, require_finalized=False)

        assessment = read_json(
            Path(assessment_path).expanduser().resolve(strict=True)
        )
        assessment_by_id = attempt_assessment_rows(assessment, plan)
        evidence_hash = sha256_json(evidence)
        errors: list[str] = []
        if assessment["fixId"] != plan["fixId"]:
            errors.append("fix-attempt-assessment.fixId: plan mismatch")
        if assessment["attemptId"] != manifest["attemptId"]:
            errors.append("fix-attempt-assessment.attemptId: manifest mismatch")
        if assessment["evidenceSha256"] != evidence_hash:
            errors.append("fix-attempt-assessment.evidenceSha256: evidence mismatch")
        finalized_at_value = finalized_at or utc_now()
        errors.extend(
            attempt_timestamp_errors(
                evidence=evidence,
                assessment=assessment,
                finalized_at=finalized_at_value,
            )
        )
        try:
            validate_attempt_evidence_refs(assessment=assessment, evidence=evidence)
            validate_measurements(
                assessment=assessment,
                attempt_dir=attempt_dir,
                evidence=evidence,
            )
        except ContractError as error:
            errors.extend(error.errors)
        if errors:
            raise ContractError(errors)

        changed_paths = {row["path"] for row in evidence["changes"]}
        finding_results = []
        for selection in plan["selections"]:
            row = assessment_by_id[selection["findingId"]]
            finding_results.append(
                {
                    **row,
                    "locationPathsChanged": sorted(
                        changed_paths.intersection(selection["locationPaths"])
                    ),
                }
            )
        status = verification_status(
            source_changed=evidence["sourceChanged"],
            command_results=evidence["commands"],
            skipped_commands=evidence["skippedCommands"],
            statuses=[row["status"] for row in finding_results],
        )
        previous_verification = None
        if manifest["previousAttempt"] is not None:
            previous_verification = read_json(
                session_file(
                    fix_dir
                    / "attempts"
                    / manifest["previousAttempt"]["attemptId"],
                    "attempt-verification.json",
                )
            )
        verification = {
            "documentType": "review-craft.fix-attempt-verification",
            "schemaVersion": FIX_ATTEMPT_SCHEMA_VERSION,
            "toolVersion": __version__,
            "fixId": plan["fixId"],
            "attemptId": manifest["attemptId"],
            "finalizedAt": finalized_at_value,
            "planSha256": sha256_json(plan),
            "manifestSha256": sha256_json(manifest),
            "evidenceSha256": evidence_hash,
            "assessmentSha256": sha256_json(assessment),
            "status": status,
            "captureStatus": evidence["captureStatus"],
            "sourceChanged": evidence["sourceChanged"],
            "current": evidence["current"],
            "changes": evidence["changes"],
            "commands": evidence["commands"],
            "skippedCommands": evidence["skippedCommands"],
            "findingResults": finding_results,
            "assessmentKind": assessment["kind"],
            "measurements": assessment["measurements"],
            "remainingRisks": assessment["remainingRisks"],
            "failureReasons": final_failure_reasons(evidence, assessment),
            "recoveryClassification": recovery_classification(
                sequence=manifest["sequence"],
                status=status,
                previous_verification=previous_verification,
            ),
        }
        validate_schema(verification, "fix-attempt-verification.schema.json")
        write_json(attempt_dir / "fix-assessment.json", assessment, mode=0o600)
        write_json(
            attempt_dir / "attempt-verification.json", verification, mode=0o600
        )
        validate_fix_attempt_snapshot(attempt_dir, require_finalized=True)
        validate_fix_lineage(fix_dir)
        return verification
