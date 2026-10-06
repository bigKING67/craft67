from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import __version__
from .constants import DELIVERY_SCHEMA_VERSION
from .contracts import ContractError
from .delivery_contract import (
    artifact_reference,
    attestation_base_id,
    delivery_status,
    utc_now,
    validate_delivery_schema,
)
from .delivery_validation import validate_delivery
from .jsonio import sha256_bytes, sha256_json, write_json
from .remediation_contract import current_source, fix_source_configuration, session_file
from .remediation_validation import validate_fix_snapshot
from .repository import inspect_git

COMMAND_TIMEOUT_SECONDS = 60


def _bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8", errors="replace")


def _run_read_only_command(
    argv: list[str],
    *,
    cwd: Path,
    captured_at: str | None = None,
) -> tuple[dict[str, Any], bytes]:
    started_at = captured_at or utc_now()
    started = time.monotonic()
    stdout = b""
    stderr = b""
    exit_code: int | None = None
    timed_out = False
    error_kind: str | None = None
    environment = dict(os.environ)
    environment.update(
        {
            "GH_PAGER": "cat",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
            "NO_COLOR": "1",
            "PAGER": "cat",
        }
    )
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=environment,
            capture_output=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        exit_code = completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout = _bytes(error.stdout)
        stderr = _bytes(error.stderr)
        timed_out = True
        error_kind = "TIMEOUT"
    except FileNotFoundError:
        error_kind = "COMMAND_NOT_FOUND"
    duration_ms = max(0, round((time.monotonic() - started) * 1000))
    return (
        {
            "argv": argv,
            "cwd": ".",
            "startedAt": started_at,
            "durationMs": duration_ms,
            "exitCode": exit_code,
            "timedOut": timed_out,
            "errorKind": error_kind,
            "stdoutSha256": sha256_bytes(stdout),
            "stderrSha256": sha256_bytes(stderr),
            "stdoutBytes": len(stdout),
            "stderrBytes": len(stderr),
        },
        stdout,
    )


def _push_proof(
    target: Path,
    *,
    remote: str,
    branch: str,
    revision: str,
    schema_version: str = DELIVERY_SCHEMA_VERSION,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ref = f"refs/heads/{branch}"
    failures: list[str] = []
    remote_sha: str | None = None
    if remote.startswith("-") or any(character in remote for character in "\0\r\n"):
        command = {
            "argv": ["git", "ls-remote", "--exit-code", "<rejected-remote>", ref],
            "cwd": ".",
            "startedAt": utc_now(),
            "durationMs": 0,
            "exitCode": None,
            "timedOut": False,
            "errorKind": "INVALID_REMOTE",
            "stdoutSha256": sha256_bytes(b""),
            "stderrSha256": sha256_bytes(b""),
            "stdoutBytes": 0,
            "stderrBytes": 0,
        }
        stdout = b""
    else:
        command, stdout = _run_read_only_command(
            ["git", "ls-remote", "--exit-code", remote, ref],
            cwd=target,
        )
    if command["errorKind"] is not None:
        failures.append(f"git ls-remote could not run ({command['errorKind']}).")
    elif command["exitCode"] != 0:
        failures.append(f"git ls-remote exited with {command['exitCode']}.")
    else:
        lines = stdout.decode("utf-8", errors="replace").splitlines()
        matches = [line.split("\t", 1)[0] for line in lines if line.endswith(f"\t{ref}")]
        if len(matches) != 1:
            failures.append("git ls-remote did not return exactly one matching branch ref.")
        else:
            remote_sha = matches[0]
            if remote_sha != revision:
                failures.append("Remote branch SHA does not match the local HEAD commit.")
    evidence = {
        "documentType": "review-craft.delivery.git-remote-evidence",
        "schemaVersion": schema_version,
        "capturedAt": command["startedAt"],
        "command": command,
        "remote": remote,
        "ref": ref,
        "localSha": revision,
        "remoteSha": remote_sha,
        "matches": not failures,
        "failureReasons": failures,
    }
    summary = {
        "requested": True,
        "status": "VERIFIED" if not failures else "FAILED",
        "remote": remote,
        "branch": branch,
        "localSha": revision,
        "remoteSha": remote_sha,
        "evidence": None,
        "failureReasons": failures,
    }
    return summary, evidence


def _normalized_jobs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "name": item.get("name"),
                "status": item.get("status"),
                "conclusion": item.get("conclusion"),
                "startedAt": item.get("startedAt"),
                "completedAt": item.get("completedAt"),
                "url": item.get("url"),
            }
        )
    return rows


def _github_actions_proof(
    target: Path,
    *,
    run_id: int,
    revision: str,
    schema_version: str = DELIVERY_SCHEMA_VERSION,
) -> tuple[dict[str, Any], dict[str, Any]]:
    fields = "workflowName,status,conclusion,url,jobs,headSha,createdAt,updatedAt"
    command, stdout = _run_read_only_command(
        ["gh", "run", "view", str(run_id), "--json", fields],
        cwd=target,
    )
    failures: list[str] = []
    payload: dict[str, Any] = {}
    if command["errorKind"] is not None:
        failures.append(f"gh run view could not run ({command['errorKind']}).")
    elif command["exitCode"] != 0:
        failures.append(f"gh run view exited with {command['exitCode']}.")
    else:
        try:
            loaded = json.loads(stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            failures.append("gh run view did not return valid UTF-8 JSON.")
        else:
            if not isinstance(loaded, dict):
                failures.append("gh run view returned a non-object JSON document.")
            else:
                payload = loaded
    jobs = _normalized_jobs(payload.get("jobs"))
    head_sha = payload.get("headSha") if isinstance(payload.get("headSha"), str) else None
    run_status = payload.get("status") if isinstance(payload.get("status"), str) else None
    conclusion = (
        payload.get("conclusion") if isinstance(payload.get("conclusion"), str) else None
    )
    if payload:
        if head_sha != revision:
            failures.append("GitHub Actions run headSha does not match the local HEAD commit.")
        if run_status != "completed":
            failures.append("GitHub Actions run is not completed.")
        if conclusion != "success":
            failures.append("GitHub Actions run conclusion is not success.")
        if not jobs:
            failures.append("GitHub Actions run contains no jobs.")
        elif any(job["status"] != "completed" for job in jobs):
            failures.append("At least one GitHub Actions job is not completed.")
    evidence = {
        "documentType": "review-craft.delivery.github-actions-evidence",
        "schemaVersion": schema_version,
        "capturedAt": command["startedAt"],
        "command": command,
        "runId": run_id,
        "expectedHeadSha": revision,
        "headSha": head_sha,
        "workflowName": payload.get("workflowName"),
        "status": run_status,
        "conclusion": conclusion,
        "url": payload.get("url"),
        "createdAt": payload.get("createdAt"),
        "updatedAt": payload.get("updatedAt"),
        "jobs": jobs,
        "matches": not failures,
        "failureReasons": failures,
    }
    summary = {
        "requested": True,
        "status": "VERIFIED" if not failures else "FAILED",
        "runId": run_id,
        "headSha": head_sha,
        "workflowName": payload.get("workflowName"),
        "runStatus": run_status,
        "conclusion": conclusion,
        "url": payload.get("url"),
        "jobs": jobs,
        "evidence": None,
        "failureReasons": failures,
    }
    return summary, evidence


def _not_requested_push(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "requested": False,
        "status": "NOT_REQUESTED",
        "remote": source["remote"],
        "branch": source["branch"],
        "localSha": source["revision"],
        "remoteSha": None,
        "evidence": None,
        "failureReasons": [],
    }


def _not_requested_ci() -> dict[str, Any]:
    return {
        "requested": False,
        "status": "NOT_REQUESTED",
        "runId": None,
        "headSha": None,
        "workflowName": None,
        "runStatus": None,
        "conclusion": None,
        "url": None,
        "jobs": [],
        "evidence": None,
        "failureReasons": [],
    }


def _failed_requested_push(source: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        **_not_requested_push(source),
        "requested": True,
        "status": "FAILED",
        "failureReasons": [reason],
    }


def _failed_requested_ci(run_id: int, reason: str) -> dict[str, Any]:
    return {
        **_not_requested_ci(),
        "requested": True,
        "status": "FAILED",
        "runId": run_id,
        "failureReasons": [reason],
    }


def delivery_remaining_risks(
    source: dict[str, Any],
    push: dict[str, Any],
    ci: dict[str, Any],
    *,
    schema_version: str = DELIVERY_SCHEMA_VERSION,
) -> list[str]:
    risks = list(source["failureReasons"])
    if push["status"] == "NOT_REQUESTED":
        risks.append("Remote push state was not verified.")
    elif push["status"] == "FAILED":
        risks.extend(push["failureReasons"])
    if ci["status"] == "NOT_REQUESTED":
        risks.append("GitHub Actions state was not verified.")
    elif ci["status"] == "FAILED":
        risks.extend(ci["failureReasons"])
    risks.extend(
        [
            f"GitHub Release state is not verified by {schema_version}.",
            f"npm registry state is not verified by {schema_version}.",
        ]
    )
    return list(dict.fromkeys(risks))


def collect_delivery_evidence(
    target: Path,
    *,
    source_configuration: dict[str, Any],
    expected_source_fingerprint: str,
    verify_push: bool,
    github_run: int | None,
    schema_version: str = DELIVERY_SCHEMA_VERSION,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any] | None,
    dict[str, Any],
    dict[str, Any] | None,
]:
    target_state = inspect_git(target)
    _, source_current = current_source(target, source_configuration)
    source_failures: list[str] = []
    if not target_state.is_repository or source_current["revision"] is None:
        source_failures.append("The delivery target is not bound to a Git commit.")
    if target_state.status:
        source_failures.append("The delivery target worktree is not clean.")
    if source_current["sourceFingerprint"] != expected_source_fingerprint:
        source_failures.append("Current source fingerprint does not match fix verification.")
    local_source = {
        "status": "VERIFIED" if not source_failures else "FAILED",
        "isGitRepository": target_state.is_repository,
        "clean": not bool(target_state.status),
        "stableDuringCollection": True,
        **source_current,
        "expectedSourceFingerprint": expected_source_fingerprint,
        "sourceMatchesVerification": (
            source_current["sourceFingerprint"] == expected_source_fingerprint
        ),
        "failureReasons": source_failures,
    }

    push = _not_requested_push(local_source)
    push_evidence: dict[str, Any] | None = None
    ci = _not_requested_ci()
    ci_evidence: dict[str, Any] | None = None
    if verify_push:
        if local_source["status"] != "VERIFIED":
            push = _failed_requested_push(
                local_source,
                "Push verification was skipped because local source proof failed.",
            )
        elif not local_source["remote"] or not local_source["branch"]:
            push = _failed_requested_push(
                local_source,
                "Push verification requires both an origin remote and a branch.",
            )
        else:
            push, push_evidence = _push_proof(
                target,
                remote=local_source["remote"],
                branch=local_source["branch"],
                revision=local_source["revision"],
                schema_version=schema_version,
            )
    if github_run is not None:
        if github_run < 1:
            raise ValueError("--github-run must be a positive GitHub Actions run id")
        if local_source["status"] != "VERIFIED":
            ci = _failed_requested_ci(
                github_run,
                "GitHub Actions verification was skipped because local source proof failed.",
            )
        else:
            ci, ci_evidence = _github_actions_proof(
                target,
                run_id=github_run,
                revision=local_source["revision"],
                schema_version=schema_version,
            )

    _, source_after = current_source(target, source_configuration)
    target_state_after = inspect_git(target)
    if source_after != source_current or target_state_after.status != target_state.status:
        local_source["status"] = "FAILED"
        local_source["stableDuringCollection"] = False
        local_source["failureReasons"].append(
            "Target source changed while delivery evidence was being collected."
        )
    return local_source, push, push_evidence, ci, ci_evidence


def finalize_delivery_artifact(
    *,
    target: Path,
    repository_name: str,
    schema_version: str,
    attestation: dict[str, Any],
    populate_source_artifacts: Callable[[Path], dict[str, Any]],
    push_evidence: dict[str, Any] | None,
    ci_evidence: dict[str, Any] | None,
    state_source: dict[str, Any],
    output_root: str | Path | None,
) -> tuple[Path, dict[str, Any]]:
    root = (
        Path(output_root).expanduser().resolve()
        if output_root
        else Path(tempfile.gettempdir()) / "review-craft-deliveries"
    )
    repository_root = root / repository_name
    try:
        repository_root.resolve().relative_to(target)
    except ValueError:
        pass
    else:
        raise ValueError("delivery output resolves inside the target repository")

    repository_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = Path(tempfile.mkdtemp(prefix=".delivery-", dir=repository_root))
    final_dir: Path | None = None
    try:
        (staging / "source").mkdir(mode=0o700)
        (staging / "evidence").mkdir(mode=0o700)
        attestation["sourceArtifacts"] = populate_source_artifacts(staging)
        push = attestation["push"]
        ci = attestation["githubActions"]
        if push_evidence is not None:
            path = staging / "evidence/git-remote.json"
            write_json(path, push_evidence, mode=0o600)
            push["evidence"] = artifact_reference(path, "evidence/git-remote.json")
        if ci_evidence is not None:
            path = staging / "evidence/github-actions-run.json"
            write_json(path, ci_evidence, mode=0o600)
            ci["evidence"] = artifact_reference(path, "evidence/github-actions-run.json")

        attestation["deliveryId"] = attestation_base_id(attestation)
        base_id = attestation["deliveryId"]
        suffix = 1
        while True:
            name = base_id if suffix == 1 else f"{base_id}-{suffix}"
            candidate = repository_root / name
            attestation["deliveryId"] = name
            validate_delivery_schema(attestation)
            write_json(staging / "delivery-attestation.json", attestation, mode=0o600)
            write_json(
                staging / "delivery-state.json",
                {
                    "documentType": "review-craft.delivery-state",
                    "schemaVersion": schema_version,
                    "deliveryId": attestation["deliveryId"],
                    "targetRoot": str(target),
                    **state_source,
                    "attestationSha256": sha256_json(attestation),
                },
                mode=0o600,
            )
            try:
                staging.rename(candidate)
            except OSError:
                if candidate.exists():
                    suffix += 1
                    continue
                raise
            final_dir = candidate
            break
        validate_delivery(final_dir)
        return final_dir, attestation
    except Exception:
        if final_dir is not None and final_dir.exists():
            shutil.rmtree(final_dir)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def verify_delivery(
    fix_dir_value: str | Path,
    *,
    verify_push: bool = False,
    github_run: int | None = None,
    output_root: str | Path | None = None,
    attested_at: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    snapshot = validate_fix_snapshot(fix_dir_value, require_verification=True)
    plan = snapshot["plan"]
    state = snapshot["state"]
    verification = snapshot["verification"]
    if verification is None or verification["status"] != "VERIFIED":
        raise ContractError(["verify-delivery requires a VERIFIED fix verification"])

    fix_dir = Path(fix_dir_value).expanduser().resolve(strict=True)
    target = Path(state["targetRoot"]).expanduser().resolve(strict=True)
    source_configuration = fix_source_configuration(state)
    local_source, push, push_evidence, ci, ci_evidence = collect_delivery_evidence(
        target,
        source_configuration=source_configuration,
        expected_source_fingerprint=verification["current"]["sourceFingerprint"],
        verify_push=verify_push,
        github_run=github_run,
    )

    def populate_source_artifacts(staging: Path) -> dict[str, Any]:
        copied = {
            "fixPlan": ("fix-plan.json", "source/fix-plan.json"),
            "fixAssessment": ("fix-assessment.json", "source/fix-assessment.json"),
            "fixVerification": ("fix-verification.json", "source/fix-verification.json"),
        }
        source_artifacts: dict[str, Any] = {}
        for key, (source_name, relative) in copied.items():
            source_path = session_file(fix_dir, source_name)
            destination = staging / relative
            destination.write_bytes(source_path.read_bytes())
            destination.chmod(0o600)
            source_artifacts[key] = artifact_reference(destination, relative)
        configuration_path = staging / "source/source-configuration.json"
        write_json(configuration_path, source_configuration, mode=0o600)
        source_artifacts["sourceConfiguration"] = artifact_reference(
            configuration_path,
            "source/source-configuration.json",
        )
        return source_artifacts

    attestation = {
        "documentType": "review-craft.delivery-attestation",
        "schemaVersion": DELIVERY_SCHEMA_VERSION,
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
            "fixId": plan["fixId"],
            "reviewRunId": plan["review"]["runId"],
            "reviewTargetIdentity": plan["review"]["targetIdentity"],
            "repositoryName": plan["review"]["repositoryName"],
            "verificationStatus": verification["status"],
            "planSha256": sha256_json(plan),
            "assessmentSha256": verification["assessmentSha256"],
            "verificationSha256": sha256_json(verification),
            "sourceConfigurationSha256": sha256_json(source_configuration),
        },
        "localSource": local_source,
        "push": push,
        "githubActions": ci,
        "githubRelease": {
            "status": "NOT_VERIFIED",
            "reason": "GitHub Release verification is not implemented in delivery.v1.",
        },
        "npmPackage": {
            "status": "NOT_VERIFIED",
            "reason": "npm registry verification is not implemented in delivery.v1.",
        },
        "remainingRisks": delivery_remaining_risks(local_source, push, ci),
    }
    return finalize_delivery_artifact(
        target=target,
        repository_name=plan["review"]["repositoryName"],
        schema_version=DELIVERY_SCHEMA_VERSION,
        attestation=attestation,
        populate_source_artifacts=populate_source_artifacts,
        push_evidence=push_evidence,
        ci_evidence=ci_evidence,
        state_source={"sourceFixDir": str(fix_dir)},
        output_root=output_root,
    )
