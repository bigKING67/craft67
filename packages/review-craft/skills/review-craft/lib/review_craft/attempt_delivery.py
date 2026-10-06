from __future__ import annotations

from pathlib import Path
from typing import Any

from . import __version__
from .constants import ATTEMPT_DELIVERY_SCHEMA_VERSION, FIX_ATTEMPT_SCHEMA_VERSION
from .contracts import ContractError
from .delivery import (
    collect_delivery_evidence,
    delivery_remaining_risks,
    finalize_delivery_artifact,
)
from .delivery_contract import artifact_reference, delivery_status, utc_now
from .jsonio import sha256_json, write_json
from .remediation_attempt_validation import (
    validate_fix_attempt_snapshot,
    validate_fix_lineage,
)
from .remediation_contract import fix_source_configuration, session_file


def verify_attempt_delivery(
    attempt_dir_value: str | Path,
    *,
    verify_push: bool = False,
    github_run: int | None = None,
    output_root: str | Path | None = None,
    attested_at: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    snapshot = validate_fix_attempt_snapshot(
        attempt_dir_value, require_finalized=True
    )
    attempt_dir = Path(attempt_dir_value).expanduser().resolve(strict=True)
    fix_dir = snapshot["fixDir"]
    plan = snapshot["plan"]
    state = snapshot["state"]
    manifest = snapshot["manifest"]
    evidence = snapshot["evidence"]
    assessment = snapshot["assessment"]
    verification = snapshot["verification"]
    if assessment is None or verification is None:
        raise ContractError(
            ["verify-attempt-delivery requires a finalized fix attempt"]
        )

    lineage = validate_fix_lineage(fix_dir)["lineage"]
    if lineage["latestAttemptId"] != manifest["attemptId"]:
        raise ContractError(
            ["verify-attempt-delivery requires the latest finalized fix attempt"]
        )
    if verification["status"] != "VERIFIED":
        raise ContractError(
            ["verify-attempt-delivery requires a VERIFIED fix attempt"]
        )
    if lineage["aggregateStatus"] not in {"VERIFIED", "VERIFIED_WITH_RETRY"}:
        raise ContractError(
            ["verify-attempt-delivery requires a verified fix lineage"]
        )

    target = Path(state["targetRoot"]).expanduser().resolve(strict=True)
    source_configuration = fix_source_configuration(state)
    local_source, push, push_evidence, ci, ci_evidence = collect_delivery_evidence(
        target,
        source_configuration=source_configuration,
        expected_source_fingerprint=verification["current"]["sourceFingerprint"],
        verify_push=verify_push,
        github_run=github_run,
        schema_version=ATTEMPT_DELIVERY_SCHEMA_VERSION,
    )

    def populate_source_artifacts(staging: Path) -> dict[str, Any]:
        plan_destination = staging / "source/fix-plan.json"
        plan_destination.write_bytes(session_file(fix_dir, "fix-plan.json").read_bytes())
        plan_destination.chmod(0o600)
        configuration_destination = staging / "source/source-configuration.json"
        write_json(configuration_destination, source_configuration, mode=0o600)
        lineage_destination = staging / "source/fix-lineage.json"
        write_json(lineage_destination, lineage, mode=0o600)

        attempts: list[dict[str, Any]] = []
        for row in lineage["attempts"]:
            attempt_id = row["attemptId"]
            source_attempt = fix_dir / "attempts" / attempt_id
            destination_root = staging / "source/attempts" / attempt_id
            destination_root.mkdir(parents=True, mode=0o700)
            copied: dict[str, Any] = {"attemptId": attempt_id}
            for key, name in (
                ("manifest", "attempt-manifest.json"),
                ("evidence", "attempt-evidence.json"),
                ("assessment", "fix-assessment.json"),
                ("verification", "attempt-verification.json"),
            ):
                relative = f"source/attempts/{attempt_id}/{name}"
                destination = staging / relative
                destination.write_bytes(session_file(source_attempt, name).read_bytes())
                destination.chmod(0o600)
                copied[key] = artifact_reference(destination, relative)
            attempts.append(copied)
        return {
            "fixPlan": artifact_reference(plan_destination, "source/fix-plan.json"),
            "sourceConfiguration": artifact_reference(
                configuration_destination,
                "source/source-configuration.json",
            ),
            "fixLineage": artifact_reference(
                lineage_destination,
                "source/fix-lineage.json",
            ),
            "attempts": attempts,
        }

    remaining_risks = delivery_remaining_risks(
        local_source,
        push,
        ci,
        schema_version=ATTEMPT_DELIVERY_SCHEMA_VERSION,
    )
    remaining_risks.append(
        "Portable delivery.v2 does not include raw command stdout, stderr, or receipt ledgers."
    )
    attestation = {
        "documentType": "review-craft.delivery-attestation",
        "schemaVersion": ATTEMPT_DELIVERY_SCHEMA_VERSION,
        "toolVersion": __version__,
        "deliveryId": "pending",
        "attestedAt": attested_at or utc_now(),
        "status": delivery_status(
            source_status=local_source["status"],
            push_requested=push["requested"],
            push_status=push["status"],
            ci_requested=ci["requested"],
            ci_status=ci["status"],
        ),
        "fix": {
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
            "sourceConfigurationSha256": sha256_json(source_configuration),
        },
        "localSource": local_source,
        "push": push,
        "githubActions": ci,
        "githubRelease": {
            "status": "NOT_VERIFIED",
            "reason": "GitHub Release verification is not implemented in delivery.v2.",
        },
        "npmPackage": {
            "status": "NOT_VERIFIED",
            "reason": "npm registry verification is not implemented in delivery.v2.",
        },
        "remainingRisks": list(dict.fromkeys(remaining_risks)),
    }
    return finalize_delivery_artifact(
        target=target,
        repository_name=plan["review"]["repositoryName"],
        schema_version=ATTEMPT_DELIVERY_SCHEMA_VERSION,
        attestation=attestation,
        populate_source_artifacts=populate_source_artifacts,
        push_evidence=push_evidence,
        ci_evidence=ci_evidence,
        state_source={
            "sourceFixDir": str(fix_dir),
            "sourceAttemptDir": str(attempt_dir),
        },
        output_root=output_root,
    )
