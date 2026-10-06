from __future__ import annotations

from pathlib import Path
from typing import Any

from .attempt_delivery_validation import validate_attempt_delivery_source
from .constants import ATTEMPT_DELIVERY_SCHEMA_VERSION, DELIVERY_SCHEMA_VERSION
from .contracts import ContractError
from .delivery_contract import (
    attestation_base_id,
    delivery_file,
    delivery_id_matches,
    delivery_status,
    validate_artifact_reference,
    validate_delivery_schema,
    validate_delivery_state,
)
from .jsonio import read_json, sha256_json
from .remediation_contract import assessment_rows, validate_schema


def _validate_source_artifacts_v1(
    delivery_dir: Path, attestation: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    references = attestation["sourceArtifacts"]
    paths = {
        "fixPlan": "source/fix-plan.json",
        "fixAssessment": "source/fix-assessment.json",
        "fixVerification": "source/fix-verification.json",
        "sourceConfiguration": "source/source-configuration.json",
    }
    resolved = {
        key: validate_artifact_reference(
            delivery_dir,
            references[key],
            expected_path=relative,
        )
        for key, relative in paths.items()
    }
    plan = read_json(resolved["fixPlan"])
    assessment = read_json(resolved["fixAssessment"])
    verification = read_json(resolved["fixVerification"])
    configuration = read_json(resolved["sourceConfiguration"])
    validate_schema(plan, "fix-plan.schema.json")
    validate_schema(assessment, "fix-assessment.schema.json")
    validate_schema(verification, "fix-verification.schema.json")
    assessment_rows(assessment, plan)
    if not isinstance(configuration, dict):
        raise ContractError(["source-configuration.json: expected an object"])
    return plan, assessment, verification, configuration


def _validate_fix_binding(
    attestation: dict[str, Any],
    plan: dict[str, Any],
    assessment: dict[str, Any],
    verification: dict[str, Any],
    configuration: dict[str, Any],
) -> list[str]:
    fix = attestation["fix"]
    errors: list[str] = []
    expected = {
        "fixId": plan["fixId"],
        "reviewRunId": plan["review"]["runId"],
        "reviewTargetIdentity": plan["review"]["targetIdentity"],
        "repositoryName": plan["review"]["repositoryName"],
        "verificationStatus": verification["status"],
        "planSha256": sha256_json(plan),
        "assessmentSha256": sha256_json(assessment),
        "verificationSha256": sha256_json(verification),
        "sourceConfigurationSha256": sha256_json(configuration),
    }
    for field, value in expected.items():
        if fix[field] != value:
            errors.append(f"delivery fix.{field}: does not match copied source artifacts")
    if verification["fixId"] != plan["fixId"]:
        errors.append("copied fix-verification.fixId: does not match fix plan")
    if verification["planSha256"] != sha256_json(plan):
        errors.append("copied fix-verification.planSha256: does not match fix plan")
    if verification["assessmentSha256"] != sha256_json(assessment):
        errors.append("copied fix-verification.assessmentSha256: does not match assessment")
    if verification["status"] != "VERIFIED":
        errors.append("delivery source fix verification must have VERIFIED status")
    return errors


def _validate_local_source(
    attestation: dict[str, Any], verification: dict[str, Any]
) -> list[str]:
    source = attestation["localSource"]
    errors: list[str] = []
    expected_fingerprint = verification["current"]["sourceFingerprint"]
    if source["expectedSourceFingerprint"] != expected_fingerprint:
        errors.append("delivery localSource.expectedSourceFingerprint: fix mismatch")
    matches = source["sourceFingerprint"] == expected_fingerprint
    if source["sourceMatchesVerification"] != matches:
        errors.append("delivery localSource.sourceMatchesVerification: invalid value")
    expected_status = (
        "VERIFIED"
        if source["isGitRepository"]
        and source["revision"] is not None
        and source["clean"]
        and source["stableDuringCollection"]
        and matches
        else "FAILED"
    )
    if source["status"] != expected_status:
        errors.append("delivery localSource.status: does not match source proof")
    if expected_status == "VERIFIED" and source["failureReasons"]:
        errors.append("delivery localSource.failureReasons: verified source must have none")
    if expected_status == "FAILED" and not source["failureReasons"]:
        errors.append("delivery localSource.failureReasons: failed source requires a reason")
    return errors


def _validate_push(delivery_dir: Path, attestation: dict[str, Any]) -> list[str]:
    push = attestation["push"]
    source = attestation["localSource"]
    errors: list[str] = []
    if push["remote"] != source["remote"] or push["branch"] != source["branch"]:
        errors.append("delivery push target does not match local source")
    if push["localSha"] != source["revision"]:
        errors.append("delivery push.localSha does not match local source revision")
    reference = push["evidence"]
    if not push["requested"]:
        if push["status"] != "NOT_REQUESTED" or reference is not None:
            errors.append("delivery push: unrequested proof must be NOT_REQUESTED without evidence")
        return errors
    if reference is None:
        if push["status"] != "FAILED" or not push["failureReasons"]:
            errors.append("delivery push: missing requested evidence must be FAILED")
        return errors
    try:
        path = validate_artifact_reference(
            delivery_dir,
            reference,
            expected_path="evidence/git-remote.json",
        )
        evidence = read_json(path)
    except ContractError as error:
        errors.extend(error.errors)
        return errors
    if not isinstance(evidence, dict):
        return errors + ["git-remote evidence: expected an object"]
    if evidence.get("documentType") != "review-craft.delivery.git-remote-evidence":
        errors.append("git-remote evidence documentType is invalid")
    if evidence.get("schemaVersion") != attestation["schemaVersion"]:
        errors.append("git-remote evidence schemaVersion is invalid")
    bindings = {
        "remote": push["remote"],
        "ref": f"refs/heads/{push['branch']}",
        "localSha": push["localSha"],
        "remoteSha": push["remoteSha"],
        "failureReasons": push["failureReasons"],
    }
    for field, value in bindings.items():
        if evidence.get(field) != value:
            errors.append(f"git-remote evidence {field} does not match attestation")
    command = evidence.get("command")
    expected_argv = [
        "git",
        "ls-remote",
        "--exit-code",
        push["remote"],
        f"refs/heads/{push['branch']}",
    ]
    command_valid = (
        isinstance(command, dict)
        and command.get("argv") == expected_argv
        and command.get("cwd") == "."
        and command.get("exitCode") == 0
        and command.get("timedOut") is False
        and command.get("errorKind") is None
    )
    expected_match = command_valid and push["remoteSha"] == push["localSha"]
    if evidence.get("matches") is not expected_match:
        errors.append("git-remote evidence matches does not follow command and SHA evidence")
    expected_status = "VERIFIED" if expected_match else "FAILED"
    if push["status"] != expected_status:
        errors.append("delivery push.status does not match evidence")
    return errors


def _validate_ci(delivery_dir: Path, attestation: dict[str, Any]) -> list[str]:
    ci = attestation["githubActions"]
    source = attestation["localSource"]
    errors: list[str] = []
    reference = ci["evidence"]
    if not ci["requested"]:
        if ci["status"] != "NOT_REQUESTED" or reference is not None:
            errors.append(
                "delivery githubActions: unrequested proof must be NOT_REQUESTED without evidence"
            )
        return errors
    if reference is None:
        if ci["status"] != "FAILED" or not ci["failureReasons"]:
            errors.append("delivery githubActions: missing requested evidence must be FAILED")
        return errors
    try:
        path = validate_artifact_reference(
            delivery_dir,
            reference,
            expected_path="evidence/github-actions-run.json",
        )
        evidence = read_json(path)
    except ContractError as error:
        errors.extend(error.errors)
        return errors
    if not isinstance(evidence, dict):
        return errors + ["github-actions evidence: expected an object"]
    if evidence.get("documentType") != "review-craft.delivery.github-actions-evidence":
        errors.append("github-actions evidence documentType is invalid")
    if evidence.get("schemaVersion") != attestation["schemaVersion"]:
        errors.append("github-actions evidence schemaVersion is invalid")
    bindings = {
        "runId": ci["runId"],
        "expectedHeadSha": source["revision"],
        "headSha": ci["headSha"],
        "workflowName": ci["workflowName"],
        "status": ci["runStatus"],
        "conclusion": ci["conclusion"],
        "url": ci["url"],
        "jobs": ci["jobs"],
        "failureReasons": ci["failureReasons"],
    }
    for field, value in bindings.items():
        if evidence.get(field) != value:
            errors.append(f"github-actions evidence {field} does not match attestation")
    command = evidence.get("command")
    fields = "workflowName,status,conclusion,url,jobs,headSha,createdAt,updatedAt"
    expected_argv = ["gh", "run", "view", str(ci["runId"]), "--json", fields]
    command_valid = (
        isinstance(command, dict)
        and command.get("argv") == expected_argv
        and command.get("cwd") == "."
        and command.get("exitCode") == 0
        and command.get("timedOut") is False
        and command.get("errorKind") is None
    )
    jobs_valid = bool(ci["jobs"]) and all(
        job["status"] == "completed" for job in ci["jobs"]
    )
    expected_match = (
        command_valid
        and ci["headSha"] == source["revision"]
        and ci["runStatus"] == "completed"
        and ci["conclusion"] == "success"
        and jobs_valid
    )
    if evidence.get("matches") is not expected_match:
        errors.append("github-actions evidence matches does not follow command and run evidence")
    expected_status = "VERIFIED" if expected_match else "FAILED"
    if ci["status"] != expected_status:
        errors.append("delivery githubActions.status does not match evidence")
    return errors


def validate_delivery(delivery_dir_value: str | Path) -> dict[str, Any]:
    delivery_dir = Path(delivery_dir_value).expanduser().resolve(strict=True)
    attestation = read_json(delivery_file(delivery_dir, "delivery-attestation.json"))
    validate_delivery_schema(attestation)
    errors: list[str] = []
    if attestation["deliveryId"] != delivery_dir.name:
        errors.append("deliveryId must match the delivery directory name")
    if not delivery_id_matches(attestation):
        errors.append(
            f"deliveryId is not content-bound; expected base {attestation_base_id(attestation)}"
        )
    schema_version = attestation["schemaVersion"]
    if schema_version == DELIVERY_SCHEMA_VERSION:
        try:
            plan, assessment, verification, configuration = _validate_source_artifacts_v1(
                delivery_dir, attestation
            )
        except ContractError as error:
            errors.extend(error.errors)
        else:
            errors.extend(
                _validate_fix_binding(
                    attestation,
                    plan,
                    assessment,
                    verification,
                    configuration,
                )
            )
            errors.extend(_validate_local_source(attestation, verification))
    elif schema_version == ATTEMPT_DELIVERY_SCHEMA_VERSION:
        try:
            source = validate_attempt_delivery_source(delivery_dir, attestation)
        except ContractError as error:
            errors.extend(error.errors)
        else:
            errors.extend(_validate_local_source(attestation, source["verification"]))
    errors.extend(_validate_push(delivery_dir, attestation))
    errors.extend(_validate_ci(delivery_dir, attestation))
    expected_status = delivery_status(
        source_status=attestation["localSource"]["status"],
        push_requested=attestation["push"]["requested"],
        push_status=attestation["push"]["status"],
        ci_requested=attestation["githubActions"]["requested"],
        ci_status=attestation["githubActions"]["status"],
    )
    if attestation["status"] != expected_status:
        errors.append("delivery status does not match source, push, and CI proof")
    for field in ("githubRelease", "npmPackage"):
        if attestation[field]["status"] != "NOT_VERIFIED":
            errors.append(
                f"delivery {field}.status must remain NOT_VERIFIED in {schema_version}"
            )
    try:
        validate_delivery_state(delivery_dir, attestation)
    except ContractError as error:
        errors.extend(error.errors)
    if errors:
        raise ContractError(errors)
    return {"attestation": attestation}
