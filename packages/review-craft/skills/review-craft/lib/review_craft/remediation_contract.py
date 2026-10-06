from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import ARTIFACT_PATHS
from .contracts import ContractError
from .jsonio import read_json, sha256_bytes, sha256_json
from .repository import (
    fingerprint_inventory,
    inspect_git,
    inventory_for_configuration,
    source_inventory_configuration,
    worktree_fingerprint,
)
from .schema_validation import validate_instance, validate_schema_definition

SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def schema(name: str) -> dict[str, Any]:
    value = read_json(SCHEMA_ROOT / name)
    if not isinstance(value, dict):
        raise ValueError(f"schema {name}: expected an object")
    errors = validate_schema_definition(value)
    if errors:
        raise ValueError(f"schema {name}: {'; '.join(errors)}")
    return value


def validate_schema(document: Any, schema_name: str) -> None:
    errors = [
        f"{schema_name}: {message}" for message in validate_instance(document, schema(schema_name))
    ]
    if errors:
        raise ContractError(errors)


def session_file(directory: Path, relative: str) -> Path:
    path = directory / relative
    if path.is_symlink():
        raise ContractError([f"fix artifact must not be a symlink: {relative}"])
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(directory)
    except (OSError, ValueError) as error:
        raise ContractError([f"invalid fix artifact {relative}: {error}"]) from error
    if not resolved.is_file():
        raise ContractError([f"fix artifact must be a file: {relative}"])
    return resolved


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _status_fingerprint(status: str) -> str:
    return sha256_bytes(status.encode("utf-8", errors="surrogateescape"))


def stable_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "path",
        "kind",
        "sizeBytes",
        "sha256",
        "binary",
        "classification",
        "diffStatus",
        "previousPath",
        "untracked",
        "sourceIdentity",
    )
    return [
        {field: row[field] for field in fields if field in row}
        for row in sorted(records, key=lambda item: item["path"])
    ]


def current_source(
    target: Path,
    configuration: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records, _, _ = inventory_for_configuration(target, configuration)
    state = inspect_git(target)
    return records, {
        "revision": state.revision,
        "branch": state.branch,
        "remote": state.remote,
        "sourceFingerprint": fingerprint_inventory(records),
        "worktreeFingerprint": worktree_fingerprint(target, records=records),
        "statusFingerprint": _status_fingerprint(state.status),
    }


def fix_source_configuration(state: dict[str, Any]) -> dict[str, Any]:
    configuration = state.get("sourceConfiguration")
    if isinstance(configuration, dict):
        return source_inventory_configuration(configuration)
    try:
        run_dir = Path(state["reviewRunDir"]).expanduser().resolve(strict=True)
        manifest = read_json(session_file(run_dir, "review-manifest.json"))
        manifest_configuration = manifest["configuration"]
    except (KeyError, OSError, TypeError, ValueError, ContractError) as error:
        raise ContractError([f"fix source configuration is unavailable: {error}"]) from error
    if not isinstance(manifest_configuration, dict):
        raise ContractError(["fix source configuration: review configuration is invalid"])
    return source_inventory_configuration(manifest_configuration)


def load_fix(
    fix_dir_value: str | Path,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    fix_dir = Path(fix_dir_value).expanduser().resolve(strict=True)
    plan = read_json(session_file(fix_dir, "fix-plan.json"))
    state = read_json(session_file(fix_dir, "fix-state.json"))
    validate_schema(plan, "fix-plan.schema.json")
    if not isinstance(state, dict):
        raise ContractError(["fix-state.json: expected an object"])
    errors: list[str] = []
    _validate_fix_plan_identity(fix_dir, plan, errors)
    _validate_fix_state_baseline(plan, state, errors)
    _validate_fix_state_commands(plan, state, errors)
    _normalize_fix_source_configuration(state, errors)
    if errors:
        raise ContractError(errors)
    return fix_dir, plan, state


def _validate_fix_plan_identity(fix_dir: Path, plan: dict[str, Any], errors: list[str]) -> None:
    if plan.get("fixId") != fix_dir.name:
        errors.append("fix-plan.fixId: must match the fix directory name")
    selection_ids = [row["findingId"] for row in plan["selections"]]
    if len(selection_ids) != len(set(selection_ids)):
        errors.append("fix-plan.selections: finding ids must be unique")
    for selection in plan["selections"]:
        for field in ("locationPaths", "verificationCriteria"):
            values = selection[field]
            if len(values) != len(set(values)):
                errors.append(
                    f"fix-plan selection {selection['findingId']}: {field} must be unique"
                )
    planned_commands = plan["verification"]["commands"]
    if len(planned_commands) != len(set(planned_commands)):
        errors.append("fix-plan.verification.commands: names must be unique")


def _validate_fix_state_baseline(
    plan: dict[str, Any], state: dict[str, Any], errors: list[str]
) -> None:
    if state.get("planSha256") != sha256_json(plan):
        errors.append("fix-state.planSha256: does not match fix-plan.json")
    baseline_files = state.get("baselineFiles")
    if not isinstance(baseline_files, list) or not all(
        isinstance(row, dict) for row in baseline_files
    ):
        errors.append("fix-state.baselineFiles: expected an array of objects")
    elif fingerprint_inventory(baseline_files) != plan["baseline"]["sourceFingerprint"]:
        errors.append("fix-state.baselineFiles: does not match baseline source fingerprint")
    elif len({row.get("path") for row in baseline_files}) != len(baseline_files):
        errors.append("fix-state.baselineFiles: paths must be unique")


def _validate_fix_state_commands(
    plan: dict[str, Any], state: dict[str, Any], errors: list[str]
) -> None:
    commands = state.get("commands")
    if not isinstance(commands, dict):
        errors.append("fix-state.commands: expected an object")
        return
    command_hash = sha256_json(commands)
    if command_hash != state.get("commandConfigSha256"):
        errors.append("fix-state.commandConfigSha256: does not match commands")
    if command_hash != plan["verification"]["commandConfigSha256"]:
        errors.append("fix-plan.verification.commandConfigSha256: does not match state")
    if sorted(commands) != sorted(plan["verification"]["commands"]):
        errors.append("fix-state.commands: names do not match fix plan")


def _normalize_fix_source_configuration(state: dict[str, Any], errors: list[str]) -> None:
    stored = state.get("sourceConfiguration")
    try:
        resolved = fix_source_configuration(state)
    except ContractError as error:
        errors.extend(error.errors)
        return
    if stored is not None and stored != resolved:
        errors.append("fix-state.sourceConfiguration: is not canonical")
    source_hash = sha256_json(resolved)
    stored_hash = state.get("sourceConfigurationSha256")
    if stored_hash is not None and stored_hash != source_hash:
        errors.append("fix-state.sourceConfigurationSha256: does not match sourceConfiguration")
    # Legacy v1 sessions derive these fields from their sealed review manifest.
    state["sourceConfiguration"] = resolved
    state["sourceConfigurationSha256"] = source_hash


def validate_review_provenance(plan: dict[str, Any], state: dict[str, Any]) -> None:
    errors: list[str] = []
    try:
        run_dir = Path(state["reviewRunDir"]).expanduser().resolve(strict=True)
        manifest_path = session_file(run_dir, "review-manifest.json")
        manifest = read_json(manifest_path)
        findings_doc = read_json(session_file(run_dir, ARTIFACT_PATHS["findings"]))
        decisions_doc = read_json(session_file(run_dir, ARTIFACT_PATHS["decisions"]))
    except (KeyError, OSError, ValueError, ContractError) as error:
        raise ContractError([f"fix review provenance is unavailable: {error}"]) from error
    _validate_review_manifest_provenance(plan, state, manifest, manifest_path, errors)
    findings = {
        row.get("id"): row for row in findings_doc.get("findings", []) if isinstance(row, dict)
    }
    decisions = {
        row.get("id"): row for row in decisions_doc.get("decisions", []) if isinstance(row, dict)
    }
    _validate_review_command_provenance(plan, manifest, errors)
    for selection in plan["selections"]:
        _validate_review_selection_provenance(selection, findings, decisions, errors)
    if errors:
        raise ContractError(errors)


def _validate_review_manifest_provenance(
    plan: dict[str, Any],
    state: dict[str, Any],
    manifest: dict[str, Any],
    manifest_path: Path,
    errors: list[str],
) -> None:
    if file_sha256(manifest_path) != plan["review"]["manifestSha256"]:
        errors.append("fix-plan.review.manifestSha256: review manifest changed")
    if manifest.get("status") != "final" or not manifest.get("sealedAt"):
        errors.append("fix review provenance: source review is not sealed and final")
    if manifest.get("runId") != plan["review"]["runId"]:
        errors.append("fix-plan.review.runId: does not match review manifest")
    configuration = manifest.get("configuration", {})
    if not isinstance(configuration, dict):
        errors.append("fix review provenance: review configuration is invalid")
    else:
        expected = source_inventory_configuration(configuration)
        if state.get("sourceConfiguration") != expected:
            errors.append("fix-state.sourceConfiguration: does not match review provenance")
        if state.get("sourceConfigurationSha256") != sha256_json(expected):
            errors.append("fix-state.sourceConfigurationSha256: review provenance mismatch")
    target = manifest.get("target")
    if not isinstance(target, dict) or target.get("identity") != plan["review"]["targetIdentity"]:
        errors.append("fix-plan.review.targetIdentity: does not match review manifest")


def _validate_review_command_provenance(
    plan: dict[str, Any], manifest: dict[str, Any], errors: list[str]
) -> None:
    commands = manifest.get("configuration", {}).get("commands", {})
    selected = {name: commands.get(name) for name in plan["verification"]["commands"]}
    if any(value is None for value in selected.values()):
        errors.append("fix-plan.verification.commands: command is absent from review provenance")
    elif sha256_json(selected) != plan["verification"]["commandConfigSha256"]:
        errors.append("fix-plan.verification.commandConfigSha256: review provenance mismatch")


def _validate_review_selection_provenance(
    selection: dict[str, Any],
    findings: dict[str, dict[str, Any]],
    decisions: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    finding_id = selection["findingId"]
    finding = findings.get(finding_id)
    decision = decisions.get(selection["decisionId"])
    if finding is None or sha256_json(finding) != selection["findingSha256"]:
        errors.append(f"fix selection {finding_id}: finding provenance changed")
    if decision is None or sha256_json(decision) != selection["decisionSha256"]:
        errors.append(f"fix selection {finding_id}: decision provenance changed")
    if finding is not None:
        expected_locations = sorted({row["path"] for row in finding.get("locations", [])})
        if selection["locationPaths"] != expected_locations:
            errors.append(f"fix selection {finding_id}: location paths do not match finding")
        if finding.get("decisionId") != selection["decisionId"]:
            errors.append(f"fix selection {finding_id}: decision id does not match finding")
    if decision is None:
        return
    expected_criteria = list(
        dict.fromkeys(
            (finding.get("verification", []) if finding else []) + decision.get("verification", [])
        )
    )
    if selection["verificationCriteria"] != expected_criteria:
        errors.append(f"fix selection {finding_id}: verification criteria changed")
    if decision.get("decision") != selection["decision"]:
        errors.append(f"fix selection {finding_id}: decision action changed")
    if finding_id not in decision.get("findingRefs", []):
        errors.append(f"fix selection {finding_id}: decision does not reference finding")


def changes(
    baseline_files: list[dict[str, Any]], current_files: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    before = {row["path"]: row for row in baseline_files}
    after = {row["path"]: row for row in current_files}
    result: list[dict[str, Any]] = []
    for path in sorted(set(before) | set(after)):
        old = before.get(path)
        new = after.get(path)
        if old is None:
            status = "ADDED"
        elif new is None:
            status = "DELETED"
        elif all(
            old.get(field) == new.get(field) for field in ("sha256", "kind", "sourceIdentity")
        ):
            continue
        else:
            status = "MODIFIED"
        result.append(
            {
                "path": path,
                "status": status,
                "beforeSha256": old.get("sha256") if old else None,
                "afterSha256": new.get("sha256") if new else None,
            }
        )
    return result


def assessment_rows(assessment: dict[str, Any], plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_schema(assessment, "fix-assessment.schema.json")
    rows = assessment["findings"]
    identifiers = [row["findingId"] for row in rows]
    expected = [row["findingId"] for row in plan["selections"]]
    errors: list[str] = []
    if len(identifiers) != len(set(identifiers)):
        errors.append("fix-assessment.findings: finding ids must be unique")
    if set(identifiers) != set(expected):
        errors.append("fix-assessment.findings: must assess every selected finding exactly once")
    for row in rows:
        if len(row["evidenceRefs"]) != len(set(row["evidenceRefs"])):
            errors.append(f"fix-assessment {row['findingId']}: evidence references must be unique")
    if errors:
        raise ContractError(errors)
    return {row["findingId"]: row for row in rows}


def validate_evidence_refs(
    *,
    assessment: dict[str, Any],
    changes: list[dict[str, Any]],
    command_results: list[dict[str, Any]],
) -> None:
    changed_paths = {row["path"] for row in changes}
    command_names = {row["name"] for row in command_results}
    errors: list[str] = []
    for result in assessment["findings"]:
        for reference in result["evidenceRefs"]:
            kind, separator, value = reference.partition(":")
            if not separator or not value:
                errors.append(
                    f"fix-assessment {result['findingId']}: invalid evidence ref {reference!r}"
                )
            elif kind == "change" and value not in changed_paths:
                errors.append(
                    f"fix-assessment {result['findingId']}: change evidence is not present: {value}"
                )
            elif kind == "command" and value not in command_names:
                errors.append(
                    f"fix-assessment {result['findingId']}: command evidence was not run: {value}"
                )
            elif kind == "manual" and assessment["kind"] != "HUMAN":
                errors.append(
                    f"fix-assessment {result['findingId']}: manual evidence requires HUMAN kind"
                )
            elif kind not in {"change", "command", "manual"}:
                errors.append(
                    f"fix-assessment {result['findingId']}: unsupported evidence ref {reference!r}"
                )
        if (
            assessment["kind"] == "AUTOMATED"
            and result["status"]
            in {
                "RESOLVED",
                "LIKELY_RESOLVED",
            }
            and not any(ref.startswith("command:") for ref in result["evidenceRefs"])
        ):
            errors.append(
                f"fix-assessment {result['findingId']}: automated resolution "
                "requires command evidence"
            )
    if errors:
        raise ContractError(errors)


def verification_status(
    *,
    source_changed: bool,
    command_results: list[dict[str, Any]],
    skipped_commands: list[str],
    statuses: list[str],
) -> str:
    if not source_changed:
        return "NO_CHANGES"
    if (
        skipped_commands
        or any(
            row["exitCode"] != 0
            or row["timedOut"]
            or row["repositoryMutationDetected"]
            or row.get("semanticEvidenceValid") is False
            for row in command_results
        )
        or any(status in {"UNRESOLVED", "REGRESSED"} for status in statuses)
    ):
        return "FAILED"
    if any(status in {"LIKELY_RESOLVED", "PARTIAL"} for status in statuses):
        return "PARTIAL"
    return "VERIFIED"
