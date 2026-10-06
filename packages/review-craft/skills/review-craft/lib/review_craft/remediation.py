from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from . import __version__
from .constants import ACTIONABLE_DECISIONS, ARTIFACT_PATHS, FIX_SCHEMA_VERSION
from .contracts import ContractError, validate_run
from .evidence import run_configured_command
from .jsonio import read_json, read_jsonl, sha256_json, write_json, write_jsonl
from .locking import exclusive_file_lock
from .remediation_contract import (
    assessment_rows,
    changes,
    current_source,
    file_sha256,
    fix_source_configuration,
    load_fix,
    session_file,
    stable_records,
    utc_now,
    validate_evidence_refs,
    validate_review_provenance,
    validate_schema,
    verification_status,
)
from .remediation_validation import validate_fix
from .repository import inspect_git, source_inventory_configuration

FIX_VERIFICATION_LOCK = ".fix-verification.lock"


def _selected_commands(
    available: dict[str, Any], requested: list[str], all_commands: bool
) -> tuple[list[str], dict[str, Any]]:
    if all_commands and requested:
        raise ValueError("--command and --all-commands cannot be combined")
    names = sorted(available) if all_commands else requested
    if len(names) != len(set(names)):
        raise ValueError("verification command names must be unique")
    unknown = sorted(set(names) - set(available))
    if unknown:
        raise ValueError(f"unknown configured verification commands: {', '.join(unknown)}")
    return names, {name: available[name] for name in names}


def prepare_fix(
    run_dir_value: str | Path,
    *,
    finding_ids: list[str],
    all_actionable: bool,
    command_names: list[str],
    all_commands: bool,
    output_root: str | Path | None = None,
    created_at: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    run_dir = Path(run_dir_value).expanduser().resolve(strict=True)
    data = validate_run(run_dir, final=True)
    manifest = data["manifest"]
    if manifest.get("status") != "final" or not manifest.get("sealedAt"):
        raise ValueError("prepare-fix requires a sealed final review run")
    if all_actionable and finding_ids:
        raise ValueError("--finding and --all-actionable cannot be combined")
    if not all_actionable and not finding_ids:
        raise ValueError("select --finding or --all-actionable")
    if len(finding_ids) != len(set(finding_ids)):
        raise ValueError("finding selections must be unique")

    findings = {row["id"]: row for row in data["findings"]["findings"]}
    decisions = {row["id"]: row for row in data["decisions"]["decisions"]}
    if all_actionable:
        selected_ids = sorted(
            finding_id
            for finding_id, finding in findings.items()
            if decisions[finding["decisionId"]]["decision"] in ACTIONABLE_DECISIONS
        )
    else:
        unknown = sorted(set(finding_ids) - set(findings))
        if unknown:
            raise ValueError(f"unknown findings: {', '.join(unknown)}")
        selected_ids = sorted(finding_ids)
    if not selected_ids:
        raise ValueError("the review contains no actionable findings")

    selections: list[dict[str, Any]] = []
    for finding_id in selected_ids:
        finding = findings[finding_id]
        decision = decisions[finding["decisionId"]]
        if decision["decision"] not in ACTIONABLE_DECISIONS:
            raise ValueError(
                f"finding {finding_id} has non-actionable decision {decision['decision']}"
            )
        criteria = list(dict.fromkeys(finding["verification"] + decision["verification"]))
        selections.append(
            {
                "findingId": finding_id,
                "findingSha256": sha256_json(finding),
                "decisionId": decision["id"],
                "decisionSha256": sha256_json(decision),
                "decision": decision["decision"],
                "locationPaths": sorted({row["path"] for row in finding["locations"]}),
                "verificationCriteria": criteria,
            }
        )

    available_commands = manifest["configuration"]["commands"]
    commands, command_config = _selected_commands(
        available_commands, command_names, all_commands
    )
    run_state = data["runState"]
    target = Path(run_state["targetRoot"]).expanduser().resolve(strict=True)
    source_configuration = source_inventory_configuration(manifest["configuration"])
    baseline_records, baseline = current_source(target, source_configuration)
    manifest_path = session_file(run_dir, "review-manifest.json")
    created_at = created_at or utc_now()
    seed = {
        "review": file_sha256(manifest_path),
        "baseline": baseline["sourceFingerprint"],
        "selections": selections,
        "commands": commands,
    }
    stamp = created_at.replace("-", "").replace(":", "").split(".", 1)[0].removesuffix("Z") + "Z"
    fix_id = f"rcf-{stamp}-{sha256_json(seed)[:12]}"
    root = (
        Path(output_root).expanduser().resolve()
        if output_root
        else Path(tempfile.gettempdir()) / "review-craft-fixes"
    )
    fix_dir = root / manifest["target"]["repositoryName"] / fix_id
    try:
        fix_dir.resolve().relative_to(target)
    except ValueError:
        pass
    else:
        raise ValueError("fix output resolves inside the target repository")
    suffix = 2
    while fix_dir.exists():
        fix_dir = fix_dir.with_name(f"{fix_id}-{suffix}")
        suffix += 1
    fix_dir.mkdir(parents=True, mode=0o700)

    plan = {
        "documentType": "review-craft.fix-plan",
        "schemaVersion": FIX_SCHEMA_VERSION,
        "toolVersion": __version__,
        "fixId": fix_dir.name,
        "createdAt": created_at,
        "review": {
            "runId": manifest["runId"],
            "manifestSha256": file_sha256(manifest_path),
            "targetIdentity": manifest["target"]["identity"],
            "repositoryName": manifest["target"]["repositoryName"],
        },
        "baseline": baseline,
        "selections": selections,
        "verification": {
            "commands": commands,
            "commandConfigSha256": sha256_json(command_config),
        },
        "authorization": {
            "sourceMutation": "EXPLICIT_USER_REQUIRED",
            "runtimeMutatesSource": False,
        },
    }
    validate_schema(plan, "fix-plan.schema.json")
    write_json(fix_dir / "fix-plan.json", plan, mode=0o600)
    write_jsonl(fix_dir / ARTIFACT_PATHS["commands"], [])
    write_json(
        fix_dir / "fix-state.json",
        {
            "targetRoot": str(target),
            "reviewRunDir": str(run_dir),
            "planSha256": sha256_json(plan),
            "baselineFiles": stable_records(baseline_records),
            "sourceConfiguration": source_configuration,
            "sourceConfigurationSha256": sha256_json(source_configuration),
            "commands": command_config,
            "commandConfigSha256": sha256_json(command_config),
        },
        mode=0o600,
    )
    validate_fix(fix_dir, require_verification=False)
    return fix_dir, plan


def _verification_wait_seconds(
    plan: dict[str, Any], state: dict[str, Any]
) -> int:
    return (
        sum(
            int(state["commands"][name].get("timeoutSeconds", 600))
            for name in plan["verification"]["commands"]
        )
        + 30
    )


def _require_fresh_verification_session(fix_dir: Path) -> None:
    result_exists = (fix_dir / "fix-verification.json").exists()
    assessment_exists = (fix_dir / "fix-assessment.json").exists()
    if result_exists and assessment_exists:
        raise ContractError(
            [
                "fix session is already completed; "
                "prepare a new fix session to verify again"
            ]
        )
    if result_exists or assessment_exists:
        raise ContractError(
            [
                "fix session contains incomplete terminal artifacts; "
                "prepare a new fix session"
            ]
        )
    if read_jsonl(fix_dir / ARTIFACT_PATHS["commands"]):
        raise ContractError(
            [
                "fix session contains prior command receipts; "
                "prepare a new fix session"
            ]
        )


def verify_fix(
    fix_dir_value: str | Path,
    *,
    assessment_path: str | Path,
    verified_at: str | None = None,
) -> dict[str, Any]:
    fix_dir, plan, state = load_fix(fix_dir_value)
    wait_seconds = _verification_wait_seconds(plan, state)
    with exclusive_file_lock(
        fix_dir,
        name=FIX_VERIFICATION_LOCK,
        wait_seconds=wait_seconds,
        timeout_message="timed out waiting for another fix verification to finish",
    ):
        fix_dir, plan, state = load_fix(fix_dir)
        validate_review_provenance(plan, state)
        _require_fresh_verification_session(fix_dir)
        return _verify_fix_locked(
            fix_dir=fix_dir,
            plan=plan,
            state=state,
            assessment_path=assessment_path,
            verified_at=verified_at,
        )


def _verify_fix_locked(
    *,
    fix_dir: Path,
    plan: dict[str, Any],
    state: dict[str, Any],
    assessment_path: str | Path,
    verified_at: str | None,
) -> dict[str, Any]:
    assessment = read_json(Path(assessment_path).expanduser().resolve(strict=True))
    assessment_by_id = assessment_rows(assessment, plan)
    target = Path(state["targetRoot"]).expanduser().resolve(strict=True)
    current_state = inspect_git(target)
    if current_state.remote != plan["baseline"]["remote"]:
        raise ContractError(["fix target remote changed after preparation"])
    source_configuration = fix_source_configuration(state)

    command_results: list[dict[str, Any]] = []
    planned_commands = plan["verification"]["commands"]
    for name in planned_commands:
        _, receipt = run_configured_command(
            session_dir=fix_dir,
            target=target,
            commands=state["commands"],
            command_name=name,
            allow_repository_mutation=False,
            source_configuration=source_configuration,
        )
        command_result = {
            "name": name,
            "receiptId": receipt["id"],
            "receiptSha256": sha256_json(receipt),
            "exitCode": receipt["exitCode"],
            "timedOut": receipt["timedOut"],
            "repositoryMutationDetected": receipt["repositoryMutationDetected"],
        }
        if "semanticEvidenceValid" in receipt:
            command_result["semanticEvidenceValid"] = receipt["semanticEvidenceValid"]
        command_results.append(command_result)
        if receipt["repositoryMutationDetected"]:
            break
    skipped_commands = planned_commands[len(command_results) :]

    current_records, current = current_source(target, source_configuration)
    source_changes = changes(state["baselineFiles"], stable_records(current_records))
    source_changed = current["sourceFingerprint"] != plan["baseline"]["sourceFingerprint"]
    validate_evidence_refs(
        assessment=assessment,
        changes=source_changes,
        command_results=command_results,
    )
    changed_paths = {row["path"] for row in source_changes}
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
        source_changed=source_changed,
        command_results=command_results,
        skipped_commands=skipped_commands,
        statuses=[row["status"] for row in finding_results],
    )
    write_json(fix_dir / "fix-assessment.json", assessment, mode=0o600)
    result = {
        "documentType": "review-craft.fix-verification",
        "schemaVersion": FIX_SCHEMA_VERSION,
        "toolVersion": __version__,
        "fixId": plan["fixId"],
        "verifiedAt": verified_at or utc_now(),
        "planSha256": sha256_json(plan),
        "assessmentSha256": sha256_json(assessment),
        "status": status,
        "sourceChanged": source_changed,
        "current": current,
        "changes": source_changes,
        "commands": command_results,
        "skippedCommands": skipped_commands,
        "findingResults": finding_results,
        "assessmentKind": assessment["kind"],
        "remainingRisks": assessment["remainingRisks"],
    }
    validate_schema(result, "fix-verification.schema.json")
    write_json(fix_dir / "fix-verification.json", result, mode=0o600)
    validate_fix(fix_dir, require_verification=True)
    return result
