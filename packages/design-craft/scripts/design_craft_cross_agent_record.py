#!/usr/bin/env python3
"""Record a cryptographically bound cross-agent score artifact."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.design_craft.evaluation.cross_agent.contract import (
    OBSERVED_REQUIRED_CRITERIA,
    OBSERVED_SCHEMA_V5,
    RUN_SCHEMA_V3,
    cross_agent_contract_sha256,
    read_text,
    scorecard_weights,
    sha256_text,
)
from design_craft_evidence_common import redacted_path, sha256_file, skill_provenance, tree_sha256
from tools.design_craft.evaluation.evidence_graph import (
    binding_domain,
    domain_dirty,
    domain_fingerprint,
    git_domain_fingerprint,
    git_projected_skill_tree_sha256,
    projected_skill_tree_sha256,
)
from tools.design_craft.evaluation.cross_agent.output import validate_output
from tools.design_craft.evaluation.cross_agent.score import validate_observed_score

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--agent", required=True, choices=("codex", "pi", "cursor", "claude"))
    parser.add_argument("--agent-version", help="Deprecated assertion; derived from --run-manifest.")
    parser.add_argument("--model", help="Deprecated assertion; derived from --run-manifest.")
    parser.add_argument("--reasoning-profile", help="Deprecated assertion; derived from --run-manifest.")
    parser.add_argument("--runner-os", help="Deprecated assertion; derived from --run-manifest.")
    parser.add_argument(
        "--skill-root",
        required=True,
        help="Exact skill directory read by the observed host.",
    )
    parser.add_argument(
        "--provenance-skill-root",
        help=(
            "Optional clean installed skill carrying provenance metadata. Its tree must "
            "exactly match --skill-root; defaults to --skill-root."
        ),
    )
    parser.add_argument(
        "--canonical-skill-root",
        default=str(ROOT / "skills/design-craft"),
        help="Current canonical source tree used to validate an installed skill copy.",
    )
    parser.add_argument("--command-summary", help="Deprecated assertion; derived from --run-manifest.")
    parser.add_argument("--criteria-json", required=True)
    parser.add_argument("--run-manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument("--score-output")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument(
        "--allow-dirty-source",
        action="store_true",
        help="Allow a development-only record with skill_source_dirty=true.",
    )
    args = parser.parse_args()

    task_dir = Path(args.task_dir).expanduser().resolve()
    skill_root = Path(args.skill_root).expanduser().resolve()
    provenance_skill_root = (
        Path(args.provenance_skill_root).expanduser().resolve()
        if args.provenance_skill_root
        else skill_root
    )
    canonical_skill_root = Path(args.canonical_skill_root).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else task_dir / f"{args.agent}-output.md"
    score_output = (
        Path(args.score_output).expanduser().resolve()
        if args.score_output
        else task_dir / f"score.{args.agent}.json"
    )
    criteria_path = Path(args.criteria_json).expanduser().resolve()
    run_manifest_path = Path(args.run_manifest).expanduser().resolve()

    for path, label in (
        (task_dir / "prompt.md", "prompt"),
        (task_dir / "scorecard.json", "machine scorecard"),
        (output, "agent output"),
        (criteria_path, "criteria JSON"),
        (run_manifest_path, "run manifest"),
    ):
        if not path.is_file():
            parser.error(f"{label} does not exist: {path}")

    if not skill_root.is_dir():
        parser.error(f"observed host skill root does not exist: {skill_root}")
    if not provenance_skill_root.is_dir():
        parser.error(f"provenance skill root does not exist: {provenance_skill_root}")

    provenance = skill_provenance(provenance_skill_root)
    observed_tree = tree_sha256(skill_root)
    if provenance.get("skill_tree_sha256") != observed_tree:
        parser.error(
            "observed host skill tree does not match the clean provenance skill tree"
        )
    provenance_skill_path = redacted_path(provenance_skill_root)
    if provenance.get("skill_source_dirty") is not False and not args.allow_dirty_source:
        parser.error("refusing to record certified evidence from a dirty skill source")

    try:
        criteria = json.loads(criteria_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        parser.error(f"invalid criteria JSON: {exc}")
    if not isinstance(criteria, dict):
        parser.error("criteria JSON must contain an object")
    try:
        run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        parser.error(f"invalid run manifest JSON: {exc}")
    if run_manifest.get("schema") != RUN_SCHEMA_V3:
        parser.error(f"run manifest must use {RUN_SCHEMA_V3}")
    if run_manifest.get("host") != args.agent:
        parser.error("run manifest host must match --agent")
    asserted_values = {
        "--agent-version": (args.agent_version, run_manifest.get("host_version")),
        "--model": (args.model, run_manifest.get("model")),
        "--reasoning-profile": (
            args.reasoning_profile,
            run_manifest.get("reasoning_profile"),
        ),
        "--runner-os": (args.runner_os, run_manifest.get("runner_os")),
        "--command-summary": (args.command_summary, run_manifest.get("command")),
    }
    for label, (asserted, observed) in asserted_values.items():
        if asserted is not None and asserted != observed:
            parser.error(f"{label} must match the observed run manifest")
    if run_manifest.get("prompt_sha256") != sha256_text(read_text(task_dir / "prompt.md")):
        parser.error("run manifest prompt hash must match prompt.md")
    if run_manifest.get("output_sha256") != sha256_file(output):
        parser.error("run manifest output hash must match the observed output")
    if run_manifest.get("output_path") != output.name:
        parser.error("run manifest output_path must match the observed output")
    if run_manifest.get("source_skill_tree_sha256") != observed_tree:
        parser.error("run manifest source tree must match the provenance skill tree")
    behavior_domain = binding_domain("cross_agent", task_dir.name, root=ROOT)
    behavior_sha256 = domain_fingerprint(ROOT, behavior_domain)
    projected_tree = projected_skill_tree_sha256(
        ROOT, canonical_skill_root, behavior_domain
    )
    if domain_dirty(ROOT, behavior_domain):
        parser.error(f"refusing to record dirty behavior domain {behavior_domain}")
    if run_manifest.get("behavior_domain") != behavior_domain:
        parser.error("run manifest behavior domain must match the task binding")
    if run_manifest.get("behavior_sha256") != behavior_sha256:
        parser.error("run manifest behavior hash must match the current domain projection")
    if run_manifest.get("behavior_source_dirty") is not False:
        parser.error("run manifest behavior source must be clean")
    if run_manifest.get("projected_skill_tree_sha256") != projected_tree:
        parser.error("run manifest projected tree must match the current domain projection")
    source_commit = str(provenance.get("skill_source_commit", ""))
    try:
        committed_behavior = git_domain_fingerprint(
            ROOT, behavior_domain, source_commit
        )
        committed_projection = git_projected_skill_tree_sha256(
            ROOT, canonical_skill_root, behavior_domain, source_commit
        )
    except (OSError, ValueError) as exc:
        parser.error(f"cannot bind behavior domain to source commit: {exc}")
    if committed_behavior != behavior_sha256 or committed_projection != projected_tree:
        parser.error("behavior domain does not match the recorded source commit")
    if run_manifest.get("skill_install_mode") != "isolated_domain_projection":
        parser.error("run manifest must use an isolated behavior-domain projection")
    if run_manifest.get("workspace_kind") != "repo_external_isolated_project":
        parser.error("run manifest workspace must be repo-external and isolated")
    if run_manifest.get("returncode") != 0 or run_manifest.get("worktree_unchanged") is not True:
        parser.error("run manifest must record a successful, non-mutating host run")
    if run_manifest.get("worktree_before_sha256") != run_manifest.get("worktree_after_sha256"):
        parser.error("run manifest worktree fingerprints must match")
    for key in (
        "host_version",
        "model",
        "model_observation",
        "reasoning_profile",
        "reasoning_observation",
        "runner_os",
        "skill_path",
        "command",
    ):
        if not isinstance(run_manifest.get(key), str) or not run_manifest[key].strip():
            parser.error(f"run manifest {key} must be a non-empty string")

    weights = scorecard_weights(task_dir / "scorecard.json")
    if set(weights) != set(OBSERVED_REQUIRED_CRITERIA):
        parser.error("scorecard does not expose the canonical seven criteria")

    normalized: dict[str, dict[str, object]] = {}
    score = 0
    for criterion in OBSERVED_REQUIRED_CRITERIA:
        raw = criteria.get(criterion)
        if not isinstance(raw, dict):
            parser.error(f"criteria JSON is missing object {criterion!r}")
        earned = raw.get("earned")
        passed = raw.get("passed")
        note = raw.get("note")
        weight = weights[criterion]
        if not isinstance(earned, int) or isinstance(earned, bool) or not 0 <= earned <= weight:
            parser.error(f"{criterion}.earned must be an integer from 0 to {weight}")
        if not isinstance(passed, bool):
            parser.error(f"{criterion}.passed must be boolean")
        if not isinstance(note, str) or len(note.strip()) < 8:
            parser.error(f"{criterion}.note must explain the score")
        normalized[criterion] = {
            "passed": passed,
            "earned": earned,
            "note": note.strip(),
        }
        score += earned

    try:
        output_relative = output.relative_to(task_dir).as_posix()
    except ValueError:
        parser.error("agent output must be stored inside the task directory")
    try:
        run_manifest_relative = run_manifest_path.relative_to(task_dir).as_posix()
    except ValueError:
        parser.error("run manifest must be stored inside the task directory")

    payload = {
        "schema": OBSERVED_SCHEMA_V5,
        "task_id": task_dir.name,
        "agent": args.agent,
        "verified": True,
        "agent_version": run_manifest["host_version"],
        "model": run_manifest["model"],
        "model_observation": run_manifest["model_observation"],
        "reasoning_profile": run_manifest["reasoning_profile"],
        "reasoning_observation": run_manifest["reasoning_observation"],
        "runner_os": run_manifest["runner_os"],
        "date": args.date,
        "prompt_sha256": sha256_text(read_text(task_dir / "prompt.md")),
        "scorecard_json_sha256": sha256_file(task_dir / "scorecard.json"),
        "contract_sha256": cross_agent_contract_sha256(),
        "run_manifest_path": run_manifest_relative,
        "run_manifest_sha256": sha256_file(run_manifest_path),
        **provenance,
        "behavior_domain": behavior_domain,
        "behavior_sha256": behavior_sha256,
        "behavior_source_dirty": False,
        "projected_skill_tree_sha256": projected_tree,
        "skill_path": run_manifest["skill_path"],
        "provenance_skill_path": provenance_skill_path,
        "command_summary": run_manifest["command"],
        "output_path": output_relative,
        "output_sha256": sha256_file(output),
        "score": score,
        "criteria": normalized,
    }
    score_output.parent.mkdir(parents=True, exist_ok=True)
    score_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    errors = validate_output(task_dir, args.agent)
    errors.extend(validate_observed_score(
        task_dir,
        args.agent,
        payload["prompt_sha256"],
        skill_root=canonical_skill_root,
        score_path=score_output,
        require_current_schema=True,
        require_current_source=not args.allow_dirty_source,
    ))
    if errors:
        score_output.unlink(missing_ok=True)
        parser.error("generated evidence did not validate: " + "; ".join(errors))

    print(score_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
