from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.design_craft_comparative_common import (
    RUN_SCHEMA,
    RUN_SCHEMA_V3,
    SOURCE_BRAND_PATTERN,
    contract_sha256,
    sha256_file,
)
from scripts.design_craft_evidence_common import (
    git_dirty,
    git_is_ancestor,
    tree_sha256,
)
from tools.design_craft.evaluation.evidence_graph import (
    binding_domain,
    domain_dirty,
    domain_fingerprint,
    git_domain_fingerprint,
    git_projected_skill_tree_sha256,
    projected_skill_tree_sha256,
)
from tools.design_craft.repo import REPO_ROOT


def validate_run(
    case_dir: Path,
    variant_id: str,
    variant: dict,
    *,
    prompt_hash: str,
    require_current_source: bool,
) -> tuple[dict, list[str]]:
    output = case_dir / f"output.{variant_id}.md"
    manifest = case_dir / f"run.{variant_id}.json"
    errors: list[str] = []
    if not output.is_file() or not manifest.is_file():
        return {}, [f"{case_dir}: incomplete observed variant {variant_id}"]
    output_text = output.read_text(encoding="utf-8")
    if len(output_text.strip()) < 200:
        errors.append(f"{output}: observed output is too sparse")
    match = SOURCE_BRAND_PATTERN.search(output_text)
    if match:
        errors.append(f"{output}: reveals a skill/source brand near {match.group(0)!r}")
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [*errors, f"{manifest}: {exc}"]
    schema = payload.get("schema")
    if schema not in {RUN_SCHEMA_V3, RUN_SCHEMA}:
        errors.append(f"{manifest}: schema must be {RUN_SCHEMA_V3} or {RUN_SCHEMA}")
    if require_current_source and schema != RUN_SCHEMA:
        errors.append(f"{manifest}: current evidence must use {RUN_SCHEMA}")
    if payload.get("variant") != variant_id or payload.get("host") != "pi":
        errors.append(f"{manifest}: variant/host mismatch")
    if payload.get("prompt_sha256") != prompt_hash:
        errors.append(f"{manifest}: prompt hash mismatch")
    if (
        payload.get("output_path") != output.name
        or payload.get("output_sha256") != sha256_file(output)
    ):
        errors.append(f"{manifest}: output path/hash mismatch")
    for key in (
        "host_version",
        "model",
        "model_observation",
        "thinking",
        "thinking_observation",
        "runner_os",
        "command",
        "cwd",
    ):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            errors.append(f"{manifest}: {key} must be non-empty")
    if payload.get("model_observation") != "requested_by_cli":
        errors.append(f"{manifest}: model_observation must be requested_by_cli")
    if payload.get("thinking_observation") != "requested_by_cli":
        errors.append(f"{manifest}: thinking_observation must be requested_by_cli")
    observed_contract = str(payload.get("contract_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", observed_contract):
        errors.append(
            f"{manifest}: contract_sha256 must be 64 lowercase hex characters"
        )
    elif require_current_source and observed_contract != contract_sha256():
        errors.append(f"{manifest}: comparative contract hash is stale")
    expected_install_mode = (
        "isolated_case_projection" if schema == RUN_SCHEMA else "isolated_project_copy"
    )
    if payload.get("skill_install_mode") != expected_install_mode:
        errors.append(
            f"{manifest}: skill_install_mode must be {expected_install_mode}"
        )
    if payload.get("workspace_kind") != "repo_external_isolated_project":
        errors.append(
            f"{manifest}: workspace_kind must be repo_external_isolated_project"
        )
    if payload.get("returncode") != 0 or payload.get("worktree_unchanged") is not True:
        errors.append(f"{manifest}: run must be successful and non-mutating")
    before_hash = payload.get("worktree_before_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", str(before_hash or "")):
        errors.append(f"{manifest}: worktree_before_sha256 is invalid")
    if before_hash != payload.get("worktree_after_sha256"):
        errors.append(f"{manifest}: worktree fingerprints must match")
    for key in ("command", "cwd"):
        if re.search(
            r"(?:/Users/|/home/|[A-Za-z]:[\\/]Users[\\/])",
            str(payload.get(key, "")),
        ):
            errors.append(f"{manifest}: {key} leaks a local user path")
    expected_tree_paths = {
        str(relative) for relative in variant.get("skill_paths", [])
    }
    observed_trees = payload.get("skill_trees")
    if not isinstance(observed_trees, dict) or set(observed_trees) != expected_tree_paths:
        errors.append(f"{manifest}: skill_trees must cover every variant skill")
        observed_trees = {}
    for relative, digest in observed_trees.items():
        if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
            errors.append(
                f"{manifest}: skill_trees.{relative} must be 64 lowercase hex characters"
            )
    if schema == RUN_SCHEMA:
        source_commit = str(payload.get("source_commit", ""))
        if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
            errors.append(f"{manifest}: source_commit must be a full lowercase Git SHA")
        source_trees = payload.get("source_trees")
        source_fingerprints = payload.get("source_fingerprints")
        if not isinstance(source_trees, dict) or set(source_trees) != expected_tree_paths:
            errors.append(f"{manifest}: source_trees must cover every variant skill")
            source_trees = {}
        if (
            not isinstance(source_fingerprints, dict)
            or set(source_fingerprints) != expected_tree_paths
        ):
            errors.append(
                f"{manifest}: source_fingerprints must cover every variant skill"
            )
            source_fingerprints = {}
        for relative, digest in source_trees.items():
            if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
                errors.append(
                    f"{manifest}: source_trees.{relative} must be 64 lowercase hex characters"
                )
        for relative, item in source_fingerprints.items():
            if not isinstance(item, dict):
                errors.append(
                    f"{manifest}: source_fingerprints.{relative} must be an object"
                )
                continue
            kind = item.get("kind")
            expected_keys = (
                {
                    "kind",
                    "domain",
                    "sha256",
                    "source_dirty",
                    "projected_tree_sha256",
                }
                if kind == "evidence_domain"
                else {"kind", "sha256", "source_dirty", "projected_tree_sha256"}
            )
            if set(item) != expected_keys:
                errors.append(
                    f"{manifest}: source_fingerprints.{relative} fields mismatch"
                )
            if kind not in {"evidence_domain", "tree"}:
                errors.append(
                    f"{manifest}: source_fingerprints.{relative}.kind is invalid"
                )
            for key in ("sha256", "projected_tree_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", str(item.get(key, ""))):
                    errors.append(
                        f"{manifest}: source_fingerprints.{relative}.{key} is invalid"
                    )
            if not isinstance(item.get("source_dirty"), bool):
                errors.append(
                    f"{manifest}: source_fingerprints.{relative}.source_dirty must be boolean"
                )

    if require_current_source and schema == RUN_SCHEMA:
        errors.extend(
            _validate_current_source(
                case_dir,
                manifest,
                payload,
                variant,
                observed_trees,
            )
        )
    installed_paths = payload.get("installed_skill_paths")
    if (
        not isinstance(installed_paths, dict)
        or set(installed_paths) != expected_tree_paths
    ):
        errors.append(
            f"{manifest}: installed_skill_paths must cover every variant skill"
        )
    elif any(
        not str(value).startswith("$VARIANT_WORKSPACE/")
        for value in installed_paths.values()
    ):
        errors.append(
            f"{manifest}: installed skill paths must be redacted workspace paths"
        )
    return payload, errors


def _validate_current_source(
    case_dir: Path,
    manifest: Path,
    payload: dict,
    variant: dict,
    observed_trees: dict,
) -> list[str]:
    errors: list[str] = []
    behavior_domain = binding_domain("comparative", case_dir.name, root=REPO_ROOT)
    expected_installed: dict[str, str] = {}
    expected_fingerprints: dict[str, dict[str, object]] = {}
    for relative_value in variant.get("skill_paths", []):
        relative = str(relative_value)
        source = REPO_ROOT / relative
        source_tree = tree_sha256(source)
        if relative == "skills/design-craft":
            projected_tree = projected_skill_tree_sha256(
                REPO_ROOT, source, behavior_domain
            )
            expected_installed[relative] = projected_tree
            expected_fingerprints[relative] = {
                "kind": "evidence_domain",
                "domain": behavior_domain,
                "sha256": domain_fingerprint(REPO_ROOT, behavior_domain),
                "source_dirty": domain_dirty(REPO_ROOT, behavior_domain),
                "projected_tree_sha256": projected_tree,
            }
        else:
            expected_installed[relative] = source_tree
            expected_fingerprints[relative] = {
                "kind": "tree",
                "sha256": source_tree,
                "source_dirty": git_dirty(REPO_ROOT, source),
                "projected_tree_sha256": source_tree,
            }
    if observed_trees != expected_installed:
        errors.append(f"{manifest}: skill_trees must match current case projections")
    if payload.get("source_fingerprints") != expected_fingerprints:
        errors.append(
            f"{manifest}: source_fingerprints must match current variant sources"
        )
    if any(item["source_dirty"] for item in expected_fingerprints.values()):
        errors.append(f"{manifest}: current comparative source projection is dirty")
    source_commit = str(payload.get("source_commit", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        return errors
    if not git_is_ancestor(REPO_ROOT, source_commit):
        errors.append(f"{manifest}: source_commit must be an ancestor of current HEAD")
        return errors
    if "skills/design-craft" not in expected_fingerprints:
        return errors
    expected_behavior = expected_fingerprints["skills/design-craft"]
    try:
        committed_behavior = git_domain_fingerprint(
            REPO_ROOT, behavior_domain, source_commit
        )
        committed_projection = git_projected_skill_tree_sha256(
            REPO_ROOT,
            REPO_ROOT / "skills/design-craft",
            behavior_domain,
            source_commit,
        )
    except (OSError, ValueError) as exc:
        errors.append(
            f"{manifest}: cannot inspect behavior domain at source_commit: {exc}"
        )
        return errors
    if expected_behavior["sha256"] != committed_behavior:
        errors.append(
            f"{manifest}: source_commit behavior must match the current behavior fingerprint"
        )
    if expected_behavior["projected_tree_sha256"] != committed_projection:
        errors.append(
            f"{manifest}: source_commit projection must match the current projected tree"
        )
    return errors
