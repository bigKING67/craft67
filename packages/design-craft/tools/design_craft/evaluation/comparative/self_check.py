from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.design_craft_comparative_common import (
    JUDGE_RUN_SCHEMA,
    RUN_SCHEMA,
    contract_sha256,
    load_scorecard,
    render_scorecard_markdown,
    sha256_file,
)
from scripts.design_craft_evidence_common import git_dirty, git_head, tree_sha256
from tools.design_craft.evaluation.evidence_graph import (
    binding_domain,
    domain_dirty,
    domain_fingerprint,
    projected_skill_tree_sha256,
)
from tools.design_craft.repo import REPO_ROOT

from .case import validate_case
from .contract import REQUIRED_DEFINITION_FILES
from .definition import load_variants, validate_definition


def _copy_definition_fixture(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    for name in REQUIRED_DEFINITION_FILES:
        shutil.copy2(source / name, destination / name)


def run_self_check() -> list[str]:
    errors: list[str] = []
    source = REPO_ROOT / "evals/comparative/emil-motion-ablation"
    if validate_definition(source)[2]:
        errors.append("comparative self-check source definition is invalid")
    with tempfile.TemporaryDirectory(
        prefix="design-craft-comparative-validate-"
    ) as raw:
        case = Path(raw) / "invalid-case"
        _copy_definition_fixture(source, case)
        variants = json.loads((case / "variants.json").read_text(encoding="utf-8"))
        variants["variants"] = []
        (case / "variants.json").write_text(json.dumps(variants), encoding="utf-8")
        if not validate_definition(case)[2]:
            errors.append("comparative self-check accepted an empty variant set")
        shutil.copy2(source / "variants.json", case / "variants.json")
        scorecard = json.loads(
            (case / "scorecard.json").read_text(encoding="utf-8")
        )
        scorecard["criteria"][0]["weight"] -= 1
        (case / "scorecard.json").write_text(
            json.dumps(scorecard), encoding="utf-8"
        )
        if not validate_definition(case)[2]:
            errors.append("comparative self-check accepted a non-100 scorecard")
        shutil.copy2(source / "scorecard.json", case / "scorecard.json")
        (case / "scorecard.md").write_text(
            render_scorecard_markdown(case), encoding="utf-8"
        )
        if validate_definition(case)[2]:
            errors.append(
                "comparative self-check rejected generated scorecard Markdown"
            )
        (case / "scorecard.md").write_text("# drift\n", encoding="utf-8")
        if not any(
            "must be generated exactly" in error
            for error in validate_definition(case)[2]
        ):
            errors.append("comparative self-check accepted scorecard Markdown drift")
        (case / "scorecard.md").write_text(
            render_scorecard_markdown(case), encoding="utf-8"
        )

    with tempfile.TemporaryDirectory(prefix="design-craft-comparative-e2e-") as raw:
        case = Path(raw) / source.name
        _copy_definition_fixture(source, case)
        variants, definition_errors = load_variants(case)
        weights, scorecard_errors = load_scorecard(case)
        if definition_errors or scorecard_errors:
            errors.append("comparative e2e self-check could not load its fixture")
            return errors
        prompt_hash = sha256_file(case / "prompt.md")
        behavior_domain = binding_domain(
            "comparative", case.name, root=REPO_ROOT
        )
        source_commit = git_head(REPO_ROOT)
        current_source_clean = not domain_dirty(REPO_ROOT, behavior_domain) and all(
            not git_dirty(REPO_ROOT, REPO_ROOT / str(relative))
            for item in variants["variants"]
            for relative in item.get("skill_paths", [])
            if str(relative) != "skills/design-craft"
        )
        for item in variants["variants"]:
            variant = item["id"]
            output = case / f"output.{variant}.md"
            output.write_text(
                "Static evidence only. Runtime behavior remains unverified. "
                "The response provides prioritized motion findings, concrete plans, "
                "Reduced Motion checks, and bounded verification steps. "
                * 3,
                encoding="utf-8",
            )
            skill_trees: dict[str, str] = {}
            source_trees: dict[str, str] = {}
            source_fingerprints: dict[str, dict[str, object]] = {}
            for relative_value in item.get("skill_paths", []):
                relative = str(relative_value)
                source_path = REPO_ROOT / relative
                source_tree = tree_sha256(source_path)
                source_trees[relative] = source_tree
                if relative == "skills/design-craft":
                    projected_tree = projected_skill_tree_sha256(
                        REPO_ROOT, source_path, behavior_domain
                    )
                    skill_trees[relative] = projected_tree
                    source_fingerprints[relative] = {
                        "kind": "evidence_domain",
                        "domain": behavior_domain,
                        "sha256": domain_fingerprint(REPO_ROOT, behavior_domain),
                        "source_dirty": False,
                        "projected_tree_sha256": projected_tree,
                    }
                else:
                    skill_trees[relative] = source_tree
                    source_fingerprints[relative] = {
                        "kind": "tree",
                        "sha256": source_tree,
                        "source_dirty": False,
                        "projected_tree_sha256": source_tree,
                    }
            installed_paths = {
                relative: f"$VARIANT_WORKSPACE/.pi/skills/{index:02d}-skill"
                for index, relative in enumerate(skill_trees, start=1)
            }
            (case / f"run.{variant}.json").write_text(
                json.dumps(
                    {
                        "schema": RUN_SCHEMA,
                        "variant": variant,
                        "host": "pi",
                        "host_version": "self-check",
                        "model": "fixture-model",
                        "model_observation": "requested_by_cli",
                        "thinking": "high",
                        "thinking_observation": "requested_by_cli",
                        "runner_os": "fixture",
                        "source_commit": source_commit,
                        "prompt_sha256": prompt_hash,
                        "output_path": output.name,
                        "output_sha256": sha256_file(output),
                        "skill_trees": skill_trees,
                        "source_trees": source_trees,
                        "source_fingerprints": source_fingerprints,
                        "installed_skill_paths": installed_paths,
                        "skill_install_mode": "isolated_case_projection",
                        "workspace_kind": "repo_external_isolated_project",
                        "cwd": "$VARIANT_WORKSPACE",
                        "command": "pi --print --no-skills",
                        "contract_sha256": contract_sha256(),
                        "returncode": 0,
                        "worktree_before_sha256": "a" * 64,
                        "worktree_after_sha256": "a" * 64,
                        "worktree_unchanged": True,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        blind = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/design_craft_comparative_blind.py"),
                "--case-dir",
                str(case),
                "--seed",
                "self-check-seed",
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if blind.returncode != 0:
            errors.append(
                "comparative e2e self-check blind step failed: "
                + (blind.stderr.strip() or blind.stdout.strip())
            )
            return errors
        blind_map = json.loads(
            (case / "blind-map.json").read_text(encoding="utf-8")
        )
        focused_variant = variants["focused_variant"]
        points_by_variant = {
            "baseline": {key: max(0, value - 5) for key, value in weights.items()},
            focused_variant: {
                key: max(0, value - 2) for key, value in weights.items()
            },
            "design-craft": dict(weights),
        }
        results = []
        winner_label = ""
        for label, item in blind_map["outputs"].items():
            variant = item["variant"]
            criteria = points_by_variant[variant]
            if variant == "design-craft":
                winner_label = label
            results.append(
                {
                    "label": label,
                    "criteria": criteria,
                    "total": sum(criteria.values()),
                    "summary": "A sufficiently detailed self-check comparative judgment summary.",
                }
            )
        judgment = {
            "results": results,
            "winner": winner_label,
            "rationale": "The self-check winner has the highest recomputed score under the exact scorecard.",
        }
        judgment_bytes = (
            json.dumps(judgment, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        judgment_path = case / "blind-judgment.json"
        raw_output_path = case / "judge-output.raw.txt"
        judgment_path.write_bytes(judgment_bytes)
        raw_output_path.write_bytes(judgment_bytes)
        (case / "run.judge.json").write_text(
            json.dumps(
                {
                    "schema": JUDGE_RUN_SCHEMA,
                    "host": "codex",
                    "host_version": "self-check",
                    "model": "fixture-model",
                    "model_observation": "requested_by_cli",
                    "reasoning_profile": "high",
                    "reasoning_observation": "requested_by_cli",
                    "runner_os": "fixture",
                    "packet_path": "blind-packet.md",
                    "packet_sha256": sha256_file(case / "blind-packet.md"),
                    "judgment_schema_sha256": sha256_file(
                        case / "judgment.schema.json"
                    ),
                    "raw_output_path": raw_output_path.name,
                    "raw_output_sha256": sha256_file(raw_output_path),
                    "judgment_path": judgment_path.name,
                    "judgment_sha256": sha256_file(judgment_path),
                    "workspace_kind": "repo_external_empty_project",
                    "cwd": "$JUDGE_WORKSPACE",
                    "command": "codex exec --sandbox read-only",
                    "returncode": 0,
                    "worktree_before_sha256": "b" * 64,
                    "worktree_after_sha256": "b" * 64,
                    "worktree_unchanged": True,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        record = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/design_craft_comparative_record.py"),
                "--case-dir",
                str(case),
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if record.returncode != 0:
            errors.append(
                "comparative e2e self-check record step failed: "
                + (record.stderr.strip() or record.stdout.strip())
            )
            return errors
        observed_errors = validate_case(
            case,
            require_observed=True,
            require_current_source=current_source_clean,
        )
        if observed_errors:
            errors.append(
                "comparative e2e self-check rejected valid observed evidence: "
                + "; ".join(observed_errors)
            )
        if not current_source_clean:
            current_source_errors = validate_case(
                case,
                require_observed=True,
                require_current_source=True,
            )
            if not any("dirty" in error for error in current_source_errors):
                errors.append(
                    "comparative e2e self-check accepted dirty current-source evidence"
                )
        comparison = json.loads(
            (case / "comparison.json").read_text(encoding="utf-8")
        )
        comparison["results"]["design-craft"]["score"] = 0
        (case / "comparison.json").write_text(
            json.dumps(comparison), encoding="utf-8"
        )
        if not validate_case(case, require_observed=True):
            errors.append("comparative e2e self-check accepted a tampered winner score")
    return errors
