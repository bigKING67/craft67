from __future__ import annotations

import re
import subprocess
from pathlib import Path

from scripts.design_craft_evidence_common import (
    git_is_ancestor,
    git_root,
    git_tree_sha256,
    read_version,
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

from .contract import (
    OBSERVED_SCHEMA_V3,
    OBSERVED_SCHEMA_V4,
    OBSERVED_SCHEMA_V5,
    cross_agent_contract_sha256,
)


def validate_current_source(
    task_dir: Path,
    skill_root: Path,
    payload: dict,
    schema: object,
    score_path: Path,
) -> list[str]:
    errors: list[str] = []
    source_commit = str(payload.get("skill_source_commit", ""))
    source_dirty = payload.get("skill_source_dirty")
    if (
        schema in {OBSERVED_SCHEMA_V3, OBSERVED_SCHEMA_V4, OBSERVED_SCHEMA_V5}
        and payload.get("contract_sha256") != cross_agent_contract_sha256()
    ):
        errors.append(
            f"{score_path}: contract_sha256 must match the current cross-agent contract"
        )
    if source_dirty is not False:
        errors.append(
            f"{score_path}: certified evidence must record skill_source_dirty=false"
        )

    if schema == OBSERVED_SCHEMA_V5:
        try:
            expected_domain = binding_domain(
                "cross_agent", task_dir.name, root=REPO_ROOT
            )
            expected_behavior = domain_fingerprint(REPO_ROOT, expected_domain)
            expected_projection = projected_skill_tree_sha256(
                REPO_ROOT, skill_root, expected_domain
            )
        except (OSError, ValueError) as exc:
            errors.append(
                f"{score_path}: cannot resolve current behavior domain: {exc}"
            )
        else:
            if payload.get("behavior_domain") != expected_domain:
                errors.append(
                    f"{score_path}: behavior_domain must match current task domain "
                    f"{expected_domain}"
                )
            if payload.get("behavior_sha256") != expected_behavior:
                errors.append(
                    f"{score_path}: behavior_sha256 must match the current domain projection"
                )
            if payload.get("projected_skill_tree_sha256") != expected_projection:
                errors.append(
                    f"{score_path}: projected_skill_tree_sha256 must match the current projection"
                )
            if domain_dirty(REPO_ROOT, expected_domain):
                errors.append(
                    f"{score_path}: current behavior domain {expected_domain} is dirty"
                )
    else:
        current_version = read_version(skill_root)
        current_tree = tree_sha256(skill_root)
        if payload.get("skill_version") != current_version:
            errors.append(
                f"{score_path}: skill_version must match current skill version "
                f"{current_version}"
            )
        if payload.get("skill_tree_sha256") != current_tree:
            errors.append(
                f"{score_path}: skill_tree_sha256 must match the current skill tree"
            )

    if re.fullmatch(r"[0-9a-f]{40}", source_commit):
        try:
            repository = git_root(skill_root)
        except (OSError, ValueError, RuntimeError):
            errors.append(
                f"{score_path}: current skill source is not in a Git repository"
            )
            return errors
        if not git_is_ancestor(repository, source_commit):
            errors.append(
                f"{score_path}: skill_source_commit must be an ancestor of current HEAD"
            )
        elif schema == OBSERVED_SCHEMA_V5:
            try:
                committed_behavior = git_domain_fingerprint(
                    repository,
                    str(payload.get("behavior_domain", "")),
                    source_commit,
                )
                committed_projection = git_projected_skill_tree_sha256(
                    repository,
                    skill_root,
                    str(payload.get("behavior_domain", "")),
                    source_commit,
                )
            except (OSError, ValueError) as exc:
                errors.append(
                    f"{score_path}: cannot inspect behavior domain at "
                    f"skill_source_commit: {exc}"
                )
            else:
                if payload.get("behavior_sha256") != committed_behavior:
                    errors.append(
                        f"{score_path}: skill_source_commit behavior must match "
                        "behavior_sha256"
                    )
                if (
                    payload.get("projected_skill_tree_sha256")
                    != committed_projection
                ):
                    errors.append(
                        f"{score_path}: skill_source_commit projection must match "
                        "projected_skill_tree_sha256"
                    )
        else:
            try:
                committed_tree = git_tree_sha256(
                    repository,
                    skill_root,
                    source_commit,
                )
            except (OSError, ValueError, subprocess.CalledProcessError) as exc:
                errors.append(
                    f"{score_path}: cannot inspect skill tree at "
                    f"skill_source_commit: {exc}"
                )
            else:
                if payload.get("skill_tree_sha256") != committed_tree:
                    errors.append(
                        f"{score_path}: skill_source_commit tree must match "
                        "skill_tree_sha256"
                    )
    return errors
