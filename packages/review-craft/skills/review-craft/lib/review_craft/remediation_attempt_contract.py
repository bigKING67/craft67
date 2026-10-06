from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .constants import ARTIFACT_PATHS
from .contracts import ContractError
from .jsonio import (
    json_pointer_value,
    parse_json_bytes,
    read_json,
    read_jsonl,
    sha256_json,
)
from .remediation_contract import session_file, validate_schema

ATTEMPT_DIRECTORY_PATTERN = re.compile(r"^attempt-([0-9]{4})-([a-f0-9]{12})$")
COMMAND_FAILURE_CODES = {
    "COMMAND_NON_ZERO",
    "COMMAND_TIMEOUT",
    "SEMANTIC_EVIDENCE_FAILURE",
}


def require_attempt_protocol_root(fix_dir: Path) -> None:
    errors: list[str] = []
    if (fix_dir / "fix-assessment.json").exists() or (
        fix_dir / "fix-verification.json"
    ).exists():
        errors.append(
            "fix session already uses the legacy single-attempt terminal protocol"
        )
    commands_path = fix_dir / ARTIFACT_PATHS["commands"]
    if commands_path.exists() and read_jsonl(commands_path):
        errors.append(
            "fix session contains legacy root command receipts and cannot start attempts"
        )
    if errors:
        raise ContractError(errors)


def parse_timestamp(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise ContractError([f"{field}: invalid date-time"]) from error


def attempt_timestamp_errors(
    *,
    evidence: dict[str, Any],
    assessment: dict[str, Any],
    finalized_at: str | None = None,
) -> list[str]:
    completed = parse_timestamp(
        evidence["completedAt"], "fix-attempt-evidence.completedAt"
    )
    assessed = parse_timestamp(
        assessment["assessedAt"], "fix-attempt-assessment.assessedAt"
    )
    errors: list[str] = []
    if assessed < completed:
        errors.append(
            "fix-attempt-assessment.assessedAt: must not precede evidence completion"
        )
    if finalized_at is not None:
        finalized = parse_timestamp(
            finalized_at, "fix-attempt-verification.finalizedAt"
        )
        if finalized < assessed or finalized < completed:
            errors.append(
                "fix-attempt-verification.finalizedAt: precedes evidence or assessment"
            )
    return errors


def scalar_equal(actual: Any, expected: Any) -> bool:
    return actual == expected and (
        not isinstance(actual, bool) or isinstance(expected, bool)
    ) and (not isinstance(expected, bool) or isinstance(actual, bool))


def attempt_directories(fix_dir: Path) -> list[Path]:
    root = fix_dir / "attempts"
    if not root.exists():
        return []
    if root.is_symlink() or not root.is_dir():
        raise ContractError(["fix attempts path must be a real directory"])
    errors: list[str] = []
    directories: list[Path] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.name.startswith("."):
            continue
        if path.is_symlink() or not path.is_dir():
            errors.append(f"invalid fix attempt entry: attempts/{path.name}")
            continue
        if ATTEMPT_DIRECTORY_PATTERN.fullmatch(path.name) is None:
            errors.append(f"invalid fix attempt directory name: attempts/{path.name}")
            continue
        directories.append(path.resolve(strict=True))
    if errors:
        raise ContractError(errors)
    return directories


def attempt_number(attempt_id: str) -> int:
    match = ATTEMPT_DIRECTORY_PATTERN.fullmatch(attempt_id)
    if match is None:
        raise ContractError(["fix attempt id has an invalid format"])
    return int(match.group(1))


def load_attempt(
    attempt_dir_value: str | Path,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    attempt_dir = Path(attempt_dir_value).expanduser().resolve(strict=True)
    if attempt_dir.parent.name != "attempts":
        raise ContractError(["fix attempt directory must be inside <fix-dir>/attempts"])
    fix_dir = attempt_dir.parent.parent.resolve(strict=True)
    manifest = read_json(session_file(attempt_dir, "attempt-manifest.json"))
    evidence = read_json(session_file(attempt_dir, "attempt-evidence.json"))
    validate_schema(manifest, "fix-attempt-manifest.schema.json")
    validate_schema(evidence, "fix-attempt-evidence.schema.json")
    errors: list[str] = []
    if manifest.get("attemptId") != attempt_dir.name:
        errors.append("fix-attempt-manifest.attemptId: must match directory name")
    if manifest.get("sequence") != attempt_number(attempt_dir.name):
        errors.append("fix-attempt-manifest.sequence: must match attempt id")
    if evidence.get("attemptId") != attempt_dir.name:
        errors.append("fix-attempt-evidence.attemptId: must match directory name")
    if errors:
        raise ContractError(errors)
    return attempt_dir, fix_dir, manifest, evidence


def command_result(receipt: dict[str, Any]) -> dict[str, Any]:
    result = {
        "name": receipt["name"],
        "receiptId": receipt["id"],
        "receiptSha256": sha256_json(receipt),
        "exitCode": receipt["exitCode"],
        "timedOut": receipt["timedOut"],
        "repositoryMutationDetected": receipt["repositoryMutationDetected"],
    }
    if "semanticEvidenceValid" in receipt:
        result["semanticEvidenceValid"] = receipt["semanticEvidenceValid"]
    return result


def claim_observations(
    *,
    attempt_dir: Path,
    receipts: list[dict[str, Any]],
    commands: dict[str, Any],
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for receipt in receipts:
        command = commands[receipt["name"]]
        declarations = command.get("evidenceClaims", [])
        if not declarations:
            continue
        stdout = session_file(attempt_dir, receipt["stdoutArtifact"]).read_bytes()
        try:
            document = parse_json_bytes(stdout)
        except (UnicodeDecodeError, ValueError):
            document = None
        receipt_claims = {
            row["id"]: row for row in receipt.get("evidenceClaims", [])
        }
        for declaration in declarations:
            found, actual = (
                json_pointer_value(document, declaration["jsonPointer"])
                if document is not None
                else (False, None)
            )
            claim = receipt_claims.get(declaration["id"], {})
            observations.append(
                {
                    "command": receipt["name"],
                    "claimId": declaration["id"],
                    "kind": declaration["kind"],
                    "status": claim.get("status", "UNVERIFIED"),
                    "jsonPointer": declaration["jsonPointer"],
                    "expected": declaration["equals"],
                    "actualAvailable": found,
                    "actual": actual if found else None,
                }
            )
    return observations


def capture_failure_reasons(
    *,
    source_changed: bool,
    command_results: list[dict[str, Any]],
    skipped_commands: list[str],
) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    if not source_changed:
        reasons.append({"code": "NO_SOURCE_CHANGES", "command": None})
    for result in command_results:
        name = result["name"]
        if result["timedOut"]:
            reasons.append({"code": "COMMAND_TIMEOUT", "command": name})
        elif result["exitCode"] != 0:
            reasons.append({"code": "COMMAND_NON_ZERO", "command": name})
        if result["repositoryMutationDetected"]:
            reasons.append({"code": "SOURCE_MUTATION", "command": name})
        if result.get("semanticEvidenceValid") is False:
            reasons.append(
                {"code": "SEMANTIC_EVIDENCE_FAILURE", "command": name}
            )
    for name in skipped_commands:
        reasons.append({"code": "COMMAND_SKIPPED", "command": name})
    return reasons


def capture_status(
    *, source_changed: bool, failure_reasons: list[dict[str, Any]]
) -> str:
    if not source_changed:
        return "NO_CHANGES"
    return "FAILED" if failure_reasons else "PASSED"


def validate_attempt_evidence_refs(
    *,
    assessment: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    changed_paths = {row["path"] for row in evidence["changes"]}
    command_names = {row["name"] for row in evidence["commands"]}
    observations = {
        (row["command"], row["claimId"]): row
        for row in evidence["claimObservations"]
    }
    measurements = {row["id"] for row in assessment["measurements"]}
    errors: list[str] = []
    for result in assessment["findings"]:
        for reference in result["evidenceRefs"]:
            parts = reference.split(":", 2)
            kind = parts[0]
            if kind in {"change", "command", "measurement", "manual"}:
                value = reference.partition(":")[2]
                if not value:
                    errors.append(
                        f"fix-attempt-assessment {result['findingId']}: "
                        f"invalid evidence ref {reference!r}"
                    )
                elif kind == "change" and value not in changed_paths:
                    errors.append(
                        f"fix-attempt-assessment {result['findingId']}: "
                        f"change evidence is not present: {value}"
                    )
                elif kind == "command" and value not in command_names:
                    errors.append(
                        f"fix-attempt-assessment {result['findingId']}: "
                        f"command evidence was not run: {value}"
                    )
                elif kind == "measurement" and value not in measurements:
                    errors.append(
                        f"fix-attempt-assessment {result['findingId']}: "
                        f"measurement evidence is not present: {value}"
                    )
                elif kind == "manual" and assessment["kind"] != "HUMAN":
                    errors.append(
                        f"fix-attempt-assessment {result['findingId']}: "
                        "manual evidence requires HUMAN kind"
                    )
                continue
            if kind == "claim" and len(parts) == 3 and parts[1] and parts[2]:
                observation = observations.get((parts[1], parts[2]))
                if observation is None:
                    errors.append(
                        f"fix-attempt-assessment {result['findingId']}: "
                        f"claim evidence is not present: {parts[1]}:{parts[2]}"
                    )
                elif (
                    result["status"] in {"RESOLVED", "LIKELY_RESOLVED"}
                    and observation["status"] != "VERIFIED"
                ):
                    errors.append(
                        f"fix-attempt-assessment {result['findingId']}: "
                        f"resolved result references unverified claim: {parts[1]}:{parts[2]}"
                    )
                continue
            errors.append(
                f"fix-attempt-assessment {result['findingId']}: "
                f"unsupported evidence ref {reference!r}"
            )
        if assessment["kind"] == "AUTOMATED" and result["status"] in {
            "RESOLVED",
            "LIKELY_RESOLVED",
        } and not any(
            ref.startswith(("command:", "claim:"))
            for ref in result["evidenceRefs"]
        ):
            errors.append(
                f"fix-attempt-assessment {result['findingId']}: automated resolution "
                "requires command or claim evidence"
            )
    if errors:
        raise ContractError(errors)


def attempt_assessment_rows(
    assessment: dict[str, Any], plan: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    validate_schema(assessment, "fix-attempt-assessment.schema.json")
    rows = assessment["findings"]
    identifiers = [row["findingId"] for row in rows]
    expected = [row["findingId"] for row in plan["selections"]]
    errors: list[str] = []
    if len(identifiers) != len(set(identifiers)):
        errors.append("fix-attempt-assessment.findings: finding ids must be unique")
    if set(identifiers) != set(expected):
        errors.append(
            "fix-attempt-assessment.findings: must assess every selected finding exactly once"
        )
    for row in rows:
        if len(row["evidenceRefs"]) != len(set(row["evidenceRefs"])):
            errors.append(
                f"fix-attempt-assessment {row['findingId']}: "
                "evidence references must be unique"
            )
    if errors:
        raise ContractError(errors)
    return {row["findingId"]: row for row in rows}


def validate_measurements(
    *,
    assessment: dict[str, Any],
    attempt_dir: Path,
    evidence: dict[str, Any],
) -> None:
    receipts = {
        row["name"]: row for row in read_jsonl(
            session_file(attempt_dir, "evidence/commands.jsonl")
        )
    }
    executed = {row["name"] for row in evidence["commands"]}
    errors: list[str] = []
    identifiers: set[str] = set()
    for measurement in assessment["measurements"]:
        identifier = measurement["id"]
        if identifier in identifiers:
            errors.append(
                f"fix-attempt-assessment.measurements: duplicate id {identifier}"
            )
        identifiers.add(identifier)
        name = measurement["command"]
        if name not in executed or name not in receipts:
            errors.append(
                f"fix-attempt-assessment measurement {identifier}: "
                f"command evidence was not run: {name}"
            )
            continue
        receipt = receipts[name]
        stdout = session_file(attempt_dir, receipt["stdoutArtifact"]).read_bytes()
        try:
            document = parse_json_bytes(stdout)
            found, actual = json_pointer_value(document, measurement["jsonPointer"])
        except (UnicodeDecodeError, ValueError):
            found, actual = False, None
        if not found:
            errors.append(
                f"fix-attempt-assessment measurement {identifier}: JSON pointer "
                "is absent from structured command stdout"
            )
        elif isinstance(actual, (dict, list)):
            errors.append(
                f"fix-attempt-assessment measurement {identifier}: expected a JSON scalar"
            )
        elif not scalar_equal(actual, measurement["value"]):
            errors.append(
                f"fix-attempt-assessment measurement {identifier}: value conflicts "
                "with captured command evidence"
            )
    if errors:
        raise ContractError(errors)


def final_failure_reasons(
    evidence: dict[str, Any], assessment: dict[str, Any]
) -> list[dict[str, Any]]:
    reasons = list(evidence["failureReasons"])
    for result in assessment["findings"]:
        if result["status"] == "UNRESOLVED":
            reasons.append(
                {
                    "code": "ASSESSMENT_UNRESOLVED",
                    "command": None,
                    "findingId": result["findingId"],
                }
            )
        elif result["status"] == "REGRESSED":
            reasons.append(
                {
                    "code": "ASSESSMENT_REGRESSED",
                    "command": None,
                    "findingId": result["findingId"],
                }
            )
    return reasons


def recovery_classification(
    *, sequence: int, status: str, previous_verification: dict[str, Any] | None
) -> str:
    if sequence == 1 or previous_verification is None:
        return "NONE"
    if status != "VERIFIED":
        return "RETRY_NOT_RECOVERED"
    previous_codes = {
        row["code"] for row in previous_verification["failureReasons"]
    }
    if previous_verification["status"] == "FAILED" and previous_codes and (
        previous_codes <= COMMAND_FAILURE_CODES
    ):
        return "FLAKY_COMMAND_RECOVERED"
    if previous_verification["status"] in {"FAILED", "PARTIAL"}:
        return "ASSESSMENT_RECOVERED"
    return "NONE"
