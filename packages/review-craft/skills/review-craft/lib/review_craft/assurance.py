from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import CONTENT_BOUND_SCHEMA_VERSIONS, EVIDENCE_LEVELS, SCORE_DIMENSIONS
from .jsonio import read_json, sha256_json
from .schema_validation import validate_instance

ASSURANCE_LEVELS = {"fast", "standard", "assured"}
ASSURANCE_BUDGETS = {
    "fast": {
        "maxEligibleFiles": 200,
        "maxEvidenceCommands": 3,
        "maxCandidates": 12,
    },
    "standard": {
        "maxEligibleFiles": None,
        "maxEvidenceCommands": None,
        "maxCandidates": None,
    },
    "assured": {
        "maxEligibleFiles": None,
        "maxEvidenceCommands": None,
        "maxCandidates": None,
    },
}
INELIGIBLE_DISPOSITIONS = {"GENERATED", "VENDORED", "BINARY", "OUT_OF_SCOPE"}


def assurance_level(configuration: dict[str, Any]) -> str:
    value = configuration.get("assuranceLevel", "standard")
    return value if value in ASSURANCE_LEVELS else "standard"


def eligible_file_count(coverage: dict[str, Any]) -> int:
    return sum(
        isinstance(row, dict) and row.get("disposition") not in INELIGIBLE_DISPOSITIONS
        for row in coverage.get("files", [])
    )


def fast_budget_errors(
    *,
    eligible_files: int,
    evidence_commands: int,
    candidates: int,
) -> list[str]:
    usage = {
        "maxEligibleFiles": eligible_files,
        "maxEvidenceCommands": evidence_commands,
        "maxCandidates": candidates,
    }
    errors = []
    for field, consumed in usage.items():
        maximum = ASSURANCE_BUDGETS["fast"][field]
        if maximum is not None and consumed > maximum:
            errors.append(f"assurance.fast.{field}: budget exceeded ({consumed} > {maximum})")
    return errors


def draft_assurance_state(
    configuration: dict[str, Any],
    review_scope: dict[str, Any],
    coverage: dict[str, Any],
) -> dict[str, Any]:
    level = assurance_level(configuration)
    budget = ASSURANCE_BUDGETS[level]
    skipped = [
        identifier
        for identifier, _label, _maximum in SCORE_DIMENSIONS
        if identifier not in review_scope["dimensions"]
    ]
    gaps = sum(
        row.get("disposition") in {"PENDING", "DEFERRED", "UNREADABLE", "OUT_OF_SCOPE"}
        for row in coverage.get("files", [])
    )
    return {
        "level": level,
        "completionStatus": "PARTIAL",
        "budget": {
            **budget,
            "eligibleFiles": eligible_file_count(coverage),
            "evidenceCommands": 0,
            "candidates": 0,
        },
        "verifier": {
            "required": level == "assured",
            "status": "MISSING" if level == "assured" else "NOT_REQUIRED",
            "evidenceRef": None,
        },
        "unverifiedClaims": [f"coverage-gaps:{gaps}"] if gaps else [],
        "skippedDimensions": skipped,
    }


def verification_input(data: dict[str, Any]) -> dict[str, Any]:
    """The exact canonical document an independent verifier must assess."""
    return {
        "reviewRunId": data["manifest"]["runId"],
        "sourceFingerprint": data["manifest"]["target"]["sourceFingerprint"],
        "findingsSha256": sha256_json(data["findings"]),
        "findings": data["findings"],
    }


def _verification_schema(version: str | None) -> dict[str, Any]:
    name = (
        "assurance-verification.schema.json"
        if version == "review-craft.assurance-verification.v1"
        else "assurance-verification-v2.schema.json"
    )
    return read_json(Path(__file__).resolve().parents[2] / "schemas" / name)


def _verification_artifacts(
    data: dict[str, Any], run_dir: Path
) -> list[tuple[dict[str, Any], dict[str, Any] | None, list[str]]]:
    results = []
    for artifact in data.get("evidenceRegistry", {}).get("artifacts", []):
        if not isinstance(artifact, dict) or artifact.get("kind") != "verification":
            continue
        path = run_dir / str(artifact.get("path", ""))
        try:
            payload = read_json(path)
        except (OSError, ValueError) as error:
            results.append((artifact, None, [f"invalid JSON: {error}"]))
            continue
        version = payload.get("schema") if isinstance(payload, dict) else None
        errors = validate_instance(payload, _verification_schema(version))
        results.append((artifact, payload, errors))
    return results


def _verification_errors(payload: dict[str, Any], data: dict[str, Any]) -> list[str]:
    errors = []
    manifest = data["manifest"]
    if payload["reviewRunId"] != manifest["runId"]:
        errors.append("reviewRunId does not match the canonical run")
    if payload["sourceFingerprint"] != manifest["target"]["sourceFingerprint"]:
        errors.append("sourceFingerprint does not match the canonical run")
    finding_ids = [row["id"] for row in data["findings"]["findings"]]
    assessment_ids = [row["findingId"] for row in payload["assessments"]]
    if len(assessment_ids) != len(set(assessment_ids)):
        errors.append("assessments contain duplicate findingId values")
    if assessment_ids != finding_ids:
        errors.append("assessments must cover canonical findings in canonical order")
    if any(row["disposition"] != "AGREED" for row in payload["assessments"]):
        errors.append("all canonical findings must be independently agreed")
    if payload["unverifiedClaims"]:
        errors.append("independent verifier contains unverified claims")
    return errors


def _current_verifications(
    data: dict[str, Any], artifacts: list[tuple[dict[str, Any], Any, list[str]]]
) -> list[tuple[dict[str, Any], Any, list[str]]]:
    digest = verification_input(data)["findingsSha256"]
    # Only sealed historical reads retain v1 semantics. A current v2 record
    # never falls back to a v1 agreement when its content binding becomes stale.
    historical = (
        data["manifest"].get("status") == "final"
        and bool(data["manifest"].get("sealedAt"))
        and all(
            payload.get("schema") == "review-craft.assurance-verification.v1"
            for _, payload, _ in artifacts
        )
    )
    return [entry for entry in artifacts if historical or entry[1].get("findingsSha256") == digest]


def _verifier_state(
    data: dict[str, Any], run_dir: Path, required: bool
) -> tuple[dict[str, Any], list[str]]:
    missing = {"required": required, "status": "MISSING", "evidenceRef": None}
    if not required:
        return {**missing, "status": "NOT_REQUIRED"}, []
    artifacts = _verification_artifacts(data, run_dir)
    errors = [
        f"verification artifact {artifact.get('id')}: {error}"
        for artifact, _payload, problems in artifacts
        for error in problems
    ]
    if errors:
        return missing, errors
    if not artifacts:
        return missing, ["assured review requires one registered verification artifact"]
    current = _current_verifications(data, artifacts)
    if len(current) != 1:
        return missing, [
            "assured review requires exactly one current content-bound verification artifact "
            "(findingsSha256); stale or legacy draft agreements do not qualify"
        ]
    artifact, payload, _ = current[0]
    errors = _verification_errors(payload, data)
    if errors:
        return missing, [f"verification artifact {artifact.get('id')}: {error}" for error in errors]
    return {
        "required": True,
        "status": "VERIFIED",
        "evidenceRef": f"artifact:{artifact['id']}",
    }, []


def _unverified_claims(data: dict[str, Any]) -> list[str]:
    claims = [
        f"candidate:{row['id']}"
        for row in data["candidates"]
        if row.get("validation", {}).get("status") == "BLOCKED"
    ]
    claims.extend(f"quality-model:{value}" for value in data["qualityModel"].get("unknowns", []))
    gaps = sum(
        row.get("disposition") in {"PENDING", "DEFERRED", "UNREADABLE", "OUT_OF_SCOPE"}
        for row in data["coverage"].get("files", [])
        if isinstance(row, dict)
    )
    if gaps:
        claims.append(f"coverage-gaps:{gaps}")
    return claims


def build_assurance_state(data: dict[str, Any], run_dir: Path) -> tuple[dict[str, Any], list[str]]:
    level = assurance_level(data["manifest"]["configuration"])
    budget = ASSURANCE_BUDGETS[level]
    consumption = {
        "eligibleFiles": eligible_file_count(data["coverage"]),
        "evidenceCommands": len(data["commands"]),
        "candidates": len(data["candidates"]),
    }
    skipped = [
        identifier
        for identifier, _label, _maximum in SCORE_DIMENSIONS
        if identifier not in data["reviewScope"]["dimensions"]
    ]
    unverified = _unverified_claims(data)
    verifier, verifier_errors = _verifier_state(data, run_dir, required=level == "assured")
    scorecard = data["scorecard"]
    complete = (
        level != "fast"
        and scorecard.get("status") == "final"
        and not unverified
        and (level != "assured" or verifier["status"] == "VERIFIED")
    )
    return {
        "level": level,
        "completionStatus": "COMPLETE" if complete else "PARTIAL",
        "budget": {**budget, **consumption},
        "verifier": verifier,
        "unverifiedClaims": unverified,
        "skippedDimensions": skipped,
    }, verifier_errors


def validate_assurance(
    data: dict[str, Any], run_dir: Path, errors: list[str], *, final: bool
) -> None:
    configuration = data["manifest"]["configuration"]
    if (
        "assuranceLevel" not in configuration
        or data["manifest"].get("schemaVersion") not in CONTENT_BOUND_SCHEMA_VERSIONS
    ):
        return
    level = assurance_level(configuration)
    if data["reviewScope"].get("assuranceLevel") != level:
        errors.append("review-scope.assuranceLevel: must match canonical configuration")
    expected, verifier_errors = build_assurance_state(data, run_dir)
    if data["manifest"].get("status") == "final" and data["scorecard"].get("assurance") != expected:
        errors.append("scorecard.assurance: must match derived assurance state")
    if level == "fast":
        errors.extend(
            fast_budget_errors(
                eligible_files=expected["budget"]["eligibleFiles"],
                evidence_commands=expected["budget"]["evidenceCommands"],
                candidates=expected["budget"]["candidates"],
            )
        )
        if data["scorecard"].get("status") != "provisional":
            errors.append("scorecard.status: fast assurance must remain provisional")
        evidence_level = data["scorecard"].get("evidenceLevel")
        if evidence_level in EVIDENCE_LEVELS and EVIDENCE_LEVELS[evidence_level] > 2:
            errors.append("scorecard.evidenceLevel: fast assurance is capped at E2")
    if final and level == "assured":
        errors.extend(verifier_errors)
        if data["scorecard"].get("status") != "final":
            errors.append("scorecard.status: assured assurance requires final status")
        evidence_level = data["scorecard"].get("evidenceLevel")
        if evidence_level in EVIDENCE_LEVELS and EVIDENCE_LEVELS[evidence_level] < 3:
            errors.append("scorecard.evidenceLevel: assured assurance requires E3+")
        if expected["unverifiedClaims"]:
            errors.append("scorecard.assurance: assured review has unverified claims")
        if expected["completionStatus"] != "COMPLETE":
            errors.append("scorecard.assurance: assured review is not complete")
