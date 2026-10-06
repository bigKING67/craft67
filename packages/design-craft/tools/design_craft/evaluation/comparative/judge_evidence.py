from __future__ import annotations

import json
from pathlib import Path

from scripts.design_craft_comparative_common import (
    BLIND_LABELS,
    BLIND_MAP_SCHEMA,
    JUDGE_RUN_SCHEMA,
    sha256_file,
    validate_judgment,
)


def validate_judge_evidence(
    case_dir: Path, weights: dict[str, int]
) -> tuple[dict, dict, list[str]]:
    manifest_path = case_dir / "run.judge.json"
    judgment_path = case_dir / "blind-judgment.json"
    raw_path = case_dir / "judge-output.raw.txt"
    errors: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        judgment = json.loads(judgment_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, {}, [f"{case_dir}: invalid judge evidence: {exc}"]
    if manifest.get("schema") != JUDGE_RUN_SCHEMA:
        errors.append(f"{manifest_path}: schema must be {JUDGE_RUN_SCHEMA}")
    if manifest.get("host") == "pi":
        errors.append(f"{manifest_path}: judge must be independent from Pi")
    if manifest.get("packet_sha256") != sha256_file(case_dir / "blind-packet.md"):
        errors.append(f"{manifest_path}: packet hash mismatch")
    if manifest.get("judgment_schema_sha256") != sha256_file(
        case_dir / "judgment.schema.json"
    ):
        errors.append(f"{manifest_path}: judgment schema hash mismatch")
    if (
        manifest.get("judgment_path") != judgment_path.name
        or manifest.get("judgment_sha256") != sha256_file(judgment_path)
    ):
        errors.append(f"{manifest_path}: judgment path/hash mismatch")
    if (
        not raw_path.is_file()
        or manifest.get("raw_output_path") != raw_path.name
        or manifest.get("raw_output_sha256") != sha256_file(raw_path)
    ):
        errors.append(f"{manifest_path}: raw judge output path/hash mismatch")
    if manifest.get("workspace_kind") != "repo_external_empty_project":
        errors.append(
            f"{manifest_path}: judge workspace must be repo-external and empty"
        )
    if (
        manifest.get("returncode") != 0
        or manifest.get("worktree_unchanged") is not True
    ):
        errors.append(
            f"{manifest_path}: judge run must be successful and non-mutating"
        )
    if manifest.get("worktree_before_sha256") != manifest.get(
        "worktree_after_sha256"
    ):
        errors.append(f"{manifest_path}: judge worktree fingerprints must match")
    for key in (
        "host_version",
        "model",
        "model_observation",
        "reasoning_profile",
        "reasoning_observation",
        "runner_os",
        "command",
        "cwd",
    ):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            errors.append(f"{manifest_path}: {key} must be non-empty")
    errors.extend(
        f"{judgment_path}: {item}" for item in validate_judgment(judgment, weights)
    )
    return manifest, judgment, errors


def validate_blind_map(
    case_dir: Path, required_variants: tuple[str, str, str]
) -> tuple[dict, list[str]]:
    path = case_dir / "blind-map.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"{path}: {exc}"]
    errors: list[str] = []
    if payload.get("schema") != BLIND_MAP_SCHEMA:
        errors.append(f"{path}: schema must be {BLIND_MAP_SCHEMA}")
    if payload.get("case_id") != case_dir.name:
        errors.append(f"{path}: case_id mismatch")
    if payload.get("focused_variant") != required_variants[1]:
        errors.append(f"{path}: focused_variant mismatch")
    hashes = {
        "prompt_sha256": "prompt.md",
        "scorecard_sha256": "scorecard.md",
        "scorecard_json_sha256": "scorecard.json",
        "judgment_schema_sha256": "judgment.schema.json",
        "packet_sha256": "blind-packet.md",
    }
    for field, name in hashes.items():
        target = case_dir / name
        if not target.is_file() or payload.get(field) != sha256_file(target):
            errors.append(f"{path}: {field} mismatch")
    outputs = payload.get("outputs")
    if not isinstance(outputs, dict) or set(outputs) != set(BLIND_LABELS):
        errors.append(f"{path}: outputs must contain A, B, and C")
    else:
        variants = set()
        for label, item in outputs.items():
            if not isinstance(item, dict):
                errors.append(f"{path}: output {label} must be an object")
                continue
            variant = item.get("variant")
            variants.add(variant)
            for field, file_field in (
                ("sha256", "path"),
                ("run_sha256", "run_path"),
            ):
                target = case_dir / str(item.get(file_field, ""))
                if not target.is_file() or item.get(field) != sha256_file(target):
                    errors.append(f"{path}: output {label} {field} mismatch")
        if variants != set(required_variants):
            errors.append(f"{path}: blind labels must map every variant exactly once")
    return payload, errors
