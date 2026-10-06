from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from scripts.design_craft_evidence_common import (
    sha256_file,
    skill_provenance,
    tree_sha256,
)
from tools.design_craft.evaluation.evidence_graph import (
    domain_fingerprint,
    projected_skill_tree_sha256,
)
from tools.design_craft.repo import REPO_ROOT

from .contract import (
    HOSTS,
    OBSERVED_SCHEMA_V5,
    RUN_SCHEMA_V3,
    STATUS_SCHEMA,
    cross_agent_contract_sha256,
    read_text,
    render_current_comparison,
    scorecard_weights,
    sha256_text,
    validate_definition_root,
    validate_task_definition,
)
from .output import validate_output
from .task import validate_observed_task


def _write_valid_task(root: Path) -> None:
    task = root / "same-prompt-generic"
    task.mkdir(parents=True)
    (task / "prompt.md").write_text(
        "# Same prompt: generic\n\n"
        "Use design-craft to critique a generic product surface with evidence "
        "labels.\n",
        encoding="utf-8",
    )
    (task / "expected-findings.md").write_text(
        "# Expected findings\n\n"
        "- Respect style authority.\n"
        "- Label missing browser evidence.\n"
        "- Recommend concrete design moves.\n",
        encoding="utf-8",
    )
    criteria = [
        ("style_authority", "Style authority and product context", 15),
        ("reference_selection", "Reference selection", 15),
        ("anti_generic_redesign", "Anti-generic redesign", 15),
        ("evidence_level", "Evidence level labeling", 15),
        ("verified_boundary", "Verified/unverified boundary", 15),
        ("design_moves", "Concrete design moves", 15),
        ("scope_control", "Scope control and unrelated changes", 10),
    ]
    (task / "scorecard.json").write_text(
        json.dumps(
            {
                "schema": "design-craft.cross-agent-scorecard.v1",
                "task_id": task.name,
                "criteria": [
                    {
                        "id": criterion_id,
                        "label": label,
                        "weight": weight,
                        "pass_evidence": (
                            "Self-check provides concrete pass evidence."
                        ),
                        "deduction_trigger": (
                            "Self-check provides a concrete deduction trigger."
                        ),
                    }
                    for criterion_id, label, weight in criteria
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (task / "evidence-status.json").write_text(
        json.dumps(
            {
                "schema": STATUS_SCHEMA,
                "task_id": task.name,
                "hosts": {
                    host: {
                        "status": "pending",
                        "reason": (
                            "Self-check has not admitted current observed evidence."
                        ),
                    }
                    for host in HOSTS
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (task / "comparison.md").write_text(
        render_current_comparison(task), encoding="utf-8"
    )


def _write_observed_fixture(task: Path) -> tuple[Path, dict]:
    output = task / "codex-output.md"
    output.write_text(
        "Evidence, unverified boundaries, and design moves. " * 20,
        encoding="utf-8",
    )
    behavior_domain = "skill-production-review"
    behavior_hash = domain_fingerprint(REPO_ROOT, behavior_domain)
    projected_tree = projected_skill_tree_sha256(
        REPO_ROOT,
        REPO_ROOT / "skills/design-craft",
        behavior_domain,
    )
    run_manifest = task / "run.codex.json"
    run_manifest.write_text(
        json.dumps(
            {
                "schema": RUN_SCHEMA_V3,
                "host": "codex",
                "host_version": "self-check",
                "model": "fixture-model",
                "model_observation": "requested_by_cli",
                "reasoning_profile": "fixture",
                "reasoning_observation": "requested_by_cli",
                "runner_os": "fixture",
                "started_at": "2026-01-01T00:00:00Z",
                "duration_seconds": 1.0,
                "timeout_seconds": 60,
                "prompt_path": "prompt.md",
                "prompt_sha256": sha256_text(read_text(task / "prompt.md")),
                "prompt_transport": "stdin",
                "output_path": output.name,
                "output_sha256": sha256_file(output),
                "skill_path": "$BENCHMARK_WORKSPACE/.agents/skills/design-craft",
                "source_skill_tree_sha256": tree_sha256(
                    REPO_ROOT / "skills/design-craft"
                ),
                "behavior_domain": behavior_domain,
                "behavior_sha256": behavior_hash,
                "behavior_source_dirty": False,
                "projected_skill_tree_sha256": projected_tree,
                "skill_install_mode": "isolated_domain_projection",
                "workspace_kind": "repo_external_isolated_project",
                "cwd": "$BENCHMARK_WORKSPACE",
                "command": (
                    "codex exec --sandbox read-only $BENCHMARK_WORKSPACE"
                ),
                "returncode": 0,
                "stderr_bytes": 0,
                "stderr_sha256": sha256_text(""),
                "worktree_before_sha256": "a" * 64,
                "worktree_after_sha256": "a" * 64,
                "worktree_unchanged": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    provenance = skill_provenance(REPO_ROOT / "skills/design-craft")
    weights = scorecard_weights(task / "scorecard.json")
    score_payload = {
        "schema": OBSERVED_SCHEMA_V5,
        "task_id": task.name,
        "agent": "codex",
        "verified": True,
        "agent_version": "self-check",
        "model": "fixture-model",
        "model_observation": "requested_by_cli",
        "reasoning_profile": "fixture",
        "reasoning_observation": "requested_by_cli",
        "runner_os": "fixture",
        "date": "2026-01-01",
        "prompt_sha256": sha256_text(read_text(task / "prompt.md")),
        "scorecard_json_sha256": sha256_file(task / "scorecard.json"),
        "contract_sha256": cross_agent_contract_sha256(),
        "run_manifest_path": run_manifest.name,
        "run_manifest_sha256": sha256_file(run_manifest),
        "skill_path": "$BENCHMARK_WORKSPACE/.agents/skills/design-craft",
        "provenance_skill_path": provenance["skill_path"],
        "skill_version": provenance["skill_version"],
        "skill_source_commit": provenance["skill_source_commit"],
        "skill_source_dirty": provenance["skill_source_dirty"],
        "repo_dirty": provenance["repo_dirty"],
        "release_state": provenance["release_state"],
        "skill_tree_sha256": provenance["skill_tree_sha256"],
        "behavior_domain": behavior_domain,
        "behavior_sha256": behavior_hash,
        "behavior_source_dirty": False,
        "projected_skill_tree_sha256": projected_tree,
        "command_summary": (
            "codex exec --sandbox read-only $BENCHMARK_WORKSPACE"
        ),
        "output_path": output.name,
        "output_sha256": sha256_file(output),
        "score": 100,
        "criteria": {
            criterion: {
                "passed": True,
                "earned": weight,
                "note": "Self-check earned points match the scorecard contract.",
            }
            for criterion, weight in weights.items()
        },
    }
    score_path = task / "score.codex.json"
    score_path.write_text(
        json.dumps(score_payload, indent=2) + "\n", encoding="utf-8"
    )
    status_payload = json.loads(
        (task / "evidence-status.json").read_text(encoding="utf-8")
    )
    status_payload["hosts"]["codex"] = {
        "status": "observed",
        "reason": "Self-check admitted a complete current observed artifact pair.",
    }
    (task / "evidence-status.json").write_text(
        json.dumps(status_payload, indent=2) + "\n", encoding="utf-8"
    )
    (task / "comparison.md").write_text(
        render_current_comparison(task), encoding="utf-8"
    )
    return score_path, score_payload


def run_self_check() -> list[str]:
    temp_root = Path(tempfile.mkdtemp(prefix="design-craft-cross-agent-"))
    try:
        _write_valid_task(temp_root)
        errors = validate_definition_root(temp_root)
        invalid = temp_root / "same-prompt-invalid"
        shutil.copytree(temp_root / "same-prompt-generic", invalid)
        invalid_scorecard = json.loads(
            (invalid / "scorecard.json").read_text(encoding="utf-8")
        )
        invalid_scorecard["criteria"][0]["weight"] = "15"
        (invalid / "scorecard.json").write_text(
            json.dumps(invalid_scorecard, indent=2) + "\n", encoding="utf-8"
        )
        invalid_errors = validate_task_definition(invalid)
        if not any(
            "weight must be a positive integer" in error
            for error in invalid_errors
        ):
            errors.append("self-check failed to reject an invalid JSON scorecard")

        task = temp_root / "same-prompt-generic"
        errors.extend(validate_observed_task(task))
        (task / "cursor-output.md").write_text(
            "Evidence and unverified design moves. " * 20,
            encoding="utf-8",
        )
        partial_errors = validate_observed_task(task)
        if not any("score.cursor.json" in error for error in partial_errors):
            errors.append(
                "self-check failed to reject a partial observed-host artifact pair"
            )
        (task / "cursor-output.md").unlink()

        output = task / "codex-output.md"
        output.write_text(
            "证据、未验证边界和具体设计改动。" * 40,
            encoding="utf-8",
        )
        localized_errors = validate_output(task, "codex")
        if localized_errors:
            errors.append(
                "self-check failed to accept localized design-change wording: "
                + "; ".join(localized_errors)
            )

        score_path, score_payload = _write_observed_fixture(task)
        errors.extend(validate_observed_task(task))
        score_payload["score"] = 99
        score_path.write_text(
            json.dumps(score_payload, indent=2) + "\n", encoding="utf-8"
        )
        score_errors = validate_observed_task(task)
        if not any(
            "sum of criteria earned points" in error for error in score_errors
        ):
            errors.append(
                "self-check failed to reject a non-computed cross-agent score"
            )
        return errors
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
