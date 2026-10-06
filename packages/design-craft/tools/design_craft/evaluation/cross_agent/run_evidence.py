from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.design_craft_evidence_common import sha256_file

from .contract import (
    CURRENT_RUN_KEYS,
    OBSERVED_SCHEMA_V3,
    OBSERVED_SCHEMA_V4,
    OBSERVED_SCHEMA_V5,
    RUN_SCHEMA_V2,
    RUN_SCHEMA_V3,
)


def validate_run_manifest(
    task_dir: Path,
    host: str,
    prompt_hash: str,
    *,
    score_payload: dict,
    score_schema: object,
    score_path: Path,
) -> list[str]:
    errors: list[str] = []
    run_manifest_value = score_payload.get("run_manifest_path")
    if not isinstance(run_manifest_value, str) or not run_manifest_value.strip():
        return [f"{score_path}: run_manifest_path must be a non-empty relative path"]

    run_relative = Path(run_manifest_value)
    run_path = task_dir / run_relative
    if run_relative.is_absolute() or ".." in run_relative.parts:
        return [f"{score_path}: run_manifest_path must stay inside the task directory"]
    if run_path.name != f"run.{host}.json" or not run_path.is_file():
        return [f"{score_path}: run_manifest_path must point to run.{host}.json"]
    if score_payload.get("run_manifest_sha256") != sha256_file(run_path):
        errors.append(f"{score_path}: run_manifest_sha256 must match {run_path.name}")
    try:
        run_payload = json.loads(run_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{run_path}: invalid run manifest: {exc}")
        return errors

    if score_schema == OBSERVED_SCHEMA_V5 and set(run_payload) != CURRENT_RUN_KEYS:
        errors.append(
            f"{run_path}: current run fields mismatch "
            f"missing={sorted(CURRENT_RUN_KEYS - set(run_payload))} "
            f"extra={sorted(set(run_payload) - CURRENT_RUN_KEYS)}"
        )
    expected_run_schema = (
        RUN_SCHEMA_V3 if score_schema == OBSERVED_SCHEMA_V5 else RUN_SCHEMA_V2
    )
    if run_payload.get("schema") != expected_run_schema:
        errors.append(f"{run_path}: run manifest schema must be {expected_run_schema}")
    if run_payload.get("host") != host:
        errors.append(f"{run_path}: host must be {host}")
    if run_payload.get("prompt_sha256") != prompt_hash:
        errors.append(f"{run_path}: prompt_sha256 must match prompt.md")
    if run_payload.get("output_sha256") != score_payload.get("output_sha256"):
        errors.append(f"{run_path}: output_sha256 must match the score artifact")
    if run_payload.get("worktree_unchanged") is not True:
        errors.append(f"{run_path}: worktree_unchanged must be true")

    if score_schema in {
        OBSERVED_SCHEMA_V3,
        OBSERVED_SCHEMA_V4,
        OBSERVED_SCHEMA_V5,
    }:
        run_score_pairs = {
            "host_version": "agent_version",
            "model": "model",
            "model_observation": "model_observation",
            "reasoning_profile": "reasoning_profile",
            "reasoning_observation": "reasoning_observation",
            "runner_os": "runner_os",
            "skill_path": "skill_path",
            "command": "command_summary",
        }
        if score_schema == OBSERVED_SCHEMA_V5:
            run_score_pairs.update(
                {
                    "source_skill_tree_sha256": "skill_tree_sha256",
                    "behavior_domain": "behavior_domain",
                    "behavior_sha256": "behavior_sha256",
                    "behavior_source_dirty": "behavior_source_dirty",
                    "projected_skill_tree_sha256": "projected_skill_tree_sha256",
                }
            )
        else:
            run_score_pairs["skill_tree_sha256"] = "skill_tree_sha256"
        for run_key, score_key in run_score_pairs.items():
            if run_payload.get(run_key) != score_payload.get(score_key):
                errors.append(
                    f"{run_path}: {run_key} must match score field {score_key}"
                )
        expected_install_mode = (
            "isolated_domain_projection"
            if score_schema == OBSERVED_SCHEMA_V5
            else "isolated_project_copy"
        )
        if run_payload.get("skill_install_mode") != expected_install_mode:
            errors.append(
                f"{run_path}: skill_install_mode must be {expected_install_mode}"
            )
        if run_payload.get("workspace_kind") != "repo_external_isolated_project":
            errors.append(
                f"{run_path}: workspace_kind must be repo_external_isolated_project"
            )
        if run_payload.get("returncode") != 0:
            errors.append(f"{run_path}: returncode must be zero")
        before_hash = run_payload.get("worktree_before_sha256")
        after_hash = run_payload.get("worktree_after_sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", str(before_hash or "")):
            errors.append(
                f"{run_path}: worktree_before_sha256 must be 64 lowercase hex characters"
            )
        if before_hash != after_hash:
            errors.append(f"{run_path}: worktree fingerprints must match")
        for key in ("skill_path", "command", "cwd"):
            value = str(run_payload.get(key, ""))
            if not value:
                errors.append(f"{run_path}: {key} must be non-empty")
            elif re.search(r"(?:/Users/|/home/|[A-Za-z]:[\\/]Users[\\/])", value):
                errors.append(f"{run_path}: {key} must redact local user paths")
    return errors
