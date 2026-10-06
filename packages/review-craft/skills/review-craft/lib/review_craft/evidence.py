from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import ARTIFACT_PATHS, SCHEMA_VERSION
from .jsonio import (
    canonical_compact,
    read_json,
    read_jsonl,
    sha256_bytes,
    write_jsonl,
)
from .locking import exclusive_file_lock
from .process_lifecycle import run_process
from .repository import inspect_git, worktree_fingerprint
from .semantic_evidence import (
    capture_semantic_evidence,
    receipt_identity_payload,
    semantic_evidence_declared,
    store_captured_artifacts,
)

LOCK_NAME = ".evidence-command.lock"


def receipt_configuration_errors(
    receipt: dict[str, Any], commands: dict[str, Any], *, prefix: str
) -> list[str]:
    """Bind a self-consistent receipt back to its canonical command configuration."""
    name = receipt.get("name")
    command = commands.get(name) if isinstance(name, str) else None
    if not isinstance(command, dict):
        return [f"{prefix}: name does not identify a configured command"]
    errors: list[str] = []
    if receipt.get("argv") != command.get("argv"):
        errors.append(f"{prefix}: argv does not match configured command {name}")
    if receipt.get("cwd") != command.get("cwd", "."):
        errors.append(f"{prefix}: cwd does not match configured command {name}")
    return errors


def resolve_repository_directory(root: Path, relative: str, field: str) -> Path:
    if Path(relative).is_absolute():
        raise ValueError(f"{field}: expected a repository-relative path")
    resolved = (root / relative).resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{field}: escapes the repository root") from error
    if not resolved.is_dir():
        raise ValueError(f"{field}: expected a directory")
    return resolved


def run_evidence_command(
    run_dir_value: str | Path,
    command_name: str,
    *,
    started_at: str | None = None,
) -> tuple[int, dict[str, Any]]:
    run_dir = Path(run_dir_value).expanduser().resolve(strict=True)
    manifest = read_json(run_dir / "review-manifest.json")
    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("run-evidence requires a current run.v5 review")
    if manifest.get("status") != "draft" or manifest.get("sealedAt") is not None:
        raise ValueError("run-evidence requires an unsealed draft review")
    if manifest.get("artifacts") != ARTIFACT_PATHS:
        raise ValueError("review manifest does not declare the current canonical artifact map")
    state = read_json(run_dir / "run-state.json")
    target = Path(state["targetRoot"]).resolve(strict=True)
    return run_configured_command(
        session_dir=run_dir,
        target=target,
        commands=manifest["configuration"]["commands"],
        command_name=command_name,
        allow_repository_mutation=manifest["configuration"]["policy"].get(
            "allowRepositoryMutation", False
        ),
        source_configuration=manifest["configuration"],
        started_at=started_at,
    )


def run_configured_command(
    *,
    session_dir: Path,
    target: Path,
    commands: dict[str, Any],
    command_name: str,
    allow_repository_mutation: bool,
    source_configuration: dict[str, Any] | None = None,
    started_at: str | None = None,
) -> tuple[int, dict[str, Any]]:
    """Run one already-validated command into a content-bound receipt stream."""
    session_dir = session_dir.expanduser().resolve(strict=True)
    target = target.expanduser().resolve(strict=True)
    command = commands.get(command_name)
    if not isinstance(command, dict):
        raise ValueError(f"unknown configured command: {command_name}")
    cwd = resolve_repository_directory(target, command.get("cwd", "."), "command.cwd")
    argv = command["argv"]
    timeout = command.get("timeoutSeconds", 600)
    # A run owns one receipt stream. Serialize the complete command lifecycle so
    # sequence assignment and before/after mutation evidence remain attributable.
    with exclusive_file_lock(
        session_dir,
        name=LOCK_NAME,
        wait_seconds=timeout + 30,
        timeout_message="timed out waiting for another evidence command to finish",
    ):
        return _run_evidence_command_locked(
            run_dir=session_dir,
            target=target,
            command_name=command_name,
            command=command,
            cwd=cwd,
            argv=argv,
            timeout=timeout,
            started_at=started_at or _utc_now(),
            allow_repository_mutation=allow_repository_mutation,
            source_configuration=source_configuration,
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_evidence_command_locked(
    *,
    run_dir: Path,
    target: Path,
    command_name: str,
    command: dict[str, Any],
    cwd: Path,
    argv: list[str],
    timeout: int,
    started_at: str,
    allow_repository_mutation: bool,
    source_configuration: dict[str, Any] | None,
) -> tuple[int, dict[str, Any]]:
    commands_path = run_dir / ARTIFACT_PATHS["commands"]
    rows = read_jsonl(commands_path)
    existing_sequences = [
        value
        for index, row in enumerate(rows)
        for value in [row.get("sequence", index)]
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
    ]
    sequence = max(existing_sequences, default=-1) + 1
    before_status = inspect_git(target).status
    before_worktree = worktree_fingerprint(target, configuration=source_configuration)
    start = time.monotonic()
    completed = run_process(argv, cwd=cwd, timeout=timeout)
    exit_code = completed.returncode
    stdout = completed.stdout
    stderr = completed.stderr
    timed_out = completed.timed_out
    duration_ms = round((time.monotonic() - start) * 1000)
    after_state = inspect_git(target)
    after_worktree = worktree_fingerprint(target, configuration=source_configuration)
    mutation = before_worktree != after_worktree or before_status != after_state.status
    claim_results, captured_artifacts, semantic_valid = capture_semantic_evidence(
        command=command,
        stdout=stdout,
        session_dir=run_dir,
        target=target,
    )
    semantic_declared = semantic_evidence_declared(command)
    identity = {
        "name": command_name,
        "argv": argv,
        "startedAt": started_at,
        "cwd": command.get("cwd", "."),
        "sequence": sequence,
    }
    if semantic_declared:
        identity.update(
            {
                "semanticEvidenceValid": semantic_valid,
                "evidenceClaims": claim_results,
                "evidenceArtifacts": [row for row, _ in captured_artifacts],
            }
        )
    command_id = sha256_bytes(
        canonical_compact(receipt_identity_payload(identity)).encode("utf-8")
    )[:16]
    evidence_dir = run_dir / "evidence" / "commands"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = evidence_dir / f"{command_id}.stdout"
    stderr_path = evidence_dir / f"{command_id}.stderr"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    receipt: dict[str, Any] = {
        "id": command_id,
        "sequence": sequence,
        "name": command_name,
        "argv": argv,
        "cwd": command.get("cwd", "."),
        "startedAt": started_at,
        "durationMs": duration_ms,
        "exitCode": exit_code,
        "timedOut": timed_out,
        "stdoutArtifact": stdout_path.relative_to(run_dir).as_posix(),
        "stderrArtifact": stderr_path.relative_to(run_dir).as_posix(),
        "stdoutSha256": sha256_bytes(stdout),
        "stderrSha256": sha256_bytes(stderr),
        "beforeStatusSha256": sha256_bytes(
            before_status.encode("utf-8", errors="surrogateescape")
        ),
        "afterStatusSha256": sha256_bytes(
            after_state.status.encode("utf-8", errors="surrogateescape")
        ),
        "repositoryMutationDetected": mutation,
    }
    if semantic_declared:
        receipt["semanticEvidenceValid"] = semantic_valid
        receipt["evidenceClaims"] = claim_results
        receipt["evidenceArtifacts"] = [row for row, _ in captured_artifacts]
        store_captured_artifacts(
            captured=captured_artifacts,
            evidence_dir=evidence_dir,
            command_id=command_id,
            session_dir=run_dir,
        )
    rows.append(receipt)
    write_jsonl(commands_path, rows)
    if mutation and not allow_repository_mutation:
        return 3, receipt
    if semantic_declared and not semantic_valid and exit_code == 0:
        return 4, receipt
    return exit_code, receipt
