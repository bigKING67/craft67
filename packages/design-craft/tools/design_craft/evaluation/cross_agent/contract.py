from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from scripts.design_craft_evidence_common import files_sha256

from ...repo import REPO_ROOT


OBSERVED_SCHEMA_V2 = "design-craft.cross-agent-score.v2"
OBSERVED_SCHEMA_V3 = "design-craft.cross-agent-score.v3"
OBSERVED_SCHEMA_V4 = "design-craft.cross-agent-score.v4"
OBSERVED_SCHEMA_V5 = "design-craft.cross-agent-score.v5"
RUN_SCHEMA_V2 = "design-craft.cross-agent-run.v2"
RUN_SCHEMA_V3 = "design-craft.cross-agent-run.v3"
STATUS_SCHEMA = "design-craft.cross-agent-status.v1"
HOSTS = ("codex", "pi", "cursor", "claude")
HOST_STATES = {"observed", "pending", "unverified"}
OBSERVED_REQUIRED_CRITERIA = (
    "style_authority",
    "reference_selection",
    "anti_generic_redesign",
    "evidence_level",
    "verified_boundary",
    "design_moves",
    "scope_control",
)
REQUIRED_FILES = (
    "prompt.md",
    "expected-findings.md",
    "scorecard.json",
    "evidence-status.json",
    "comparison.md",
)
PLACEHOLDER_PATTERN = re.compile(r"\bTODO\b|after real agent runs", re.I)
CURRENT_SCORE_KEYS = {
    "schema",
    "task_id",
    "agent",
    "verified",
    "agent_version",
    "model",
    "model_observation",
    "reasoning_profile",
    "reasoning_observation",
    "runner_os",
    "date",
    "prompt_sha256",
    "scorecard_json_sha256",
    "contract_sha256",
    "run_manifest_path",
    "run_manifest_sha256",
    "skill_version",
    "skill_source_commit",
    "skill_source_dirty",
    "repo_dirty",
    "release_state",
    "skill_tree_sha256",
    "behavior_domain",
    "behavior_sha256",
    "behavior_source_dirty",
    "projected_skill_tree_sha256",
    "skill_path",
    "provenance_skill_path",
    "command_summary",
    "output_path",
    "output_sha256",
    "score",
    "criteria",
}
CURRENT_RUN_KEYS = {
    "schema",
    "host",
    "host_version",
    "model",
    "model_observation",
    "reasoning_profile",
    "reasoning_observation",
    "runner_os",
    "started_at",
    "duration_seconds",
    "timeout_seconds",
    "prompt_path",
    "prompt_sha256",
    "prompt_transport",
    "output_path",
    "output_sha256",
    "skill_path",
    "source_skill_tree_sha256",
    "behavior_domain",
    "behavior_sha256",
    "behavior_source_dirty",
    "projected_skill_tree_sha256",
    "skill_install_mode",
    "workspace_kind",
    "cwd",
    "command",
    "returncode",
    "stderr_bytes",
    "stderr_sha256",
    "worktree_before_sha256",
    "worktree_after_sha256",
    "worktree_unchanged",
}
CROSS_AGENT_CONTRACT_FILES = (
    "scripts/design_craft_cross_agent_record.py",
    "scripts/design_craft_cross_agent_run.py",
    "scripts/design_craft_cross_agent_validate.py",
    "scripts/design_craft_evidence_common.py",
    "tools/design_craft/evaluation/evidence_graph.py",
    "tools/design_craft/evaluation/cross_agent/cli.py",
    "tools/design_craft/evaluation/cross_agent/contract.py",
    "tools/design_craft/evaluation/cross_agent/current_source.py",
    "tools/design_craft/evaluation/cross_agent/history.py",
    "tools/design_craft/evaluation/cross_agent/output.py",
    "tools/design_craft/evaluation/cross_agent/run_evidence.py",
    "tools/design_craft/evaluation/cross_agent/score.py",
    "tools/design_craft/evaluation/cross_agent/task.py",
    "contracts/evaluation/scorecard.schema.json",
    "contracts/evaluation/evidence-status.schema.json",
    "contracts/evaluation/evidence-graph.schema.json",
    "contracts/evaluation/cross-agent-score.schema.json",
    "contracts/evaluation/cross-agent-run.schema.json",
    "adapters/codex/README.md",
    "adapters/pi/README.md",
    "adapters/cursor/README.md",
    "adapters/claude/README.md",
)


def cross_agent_contract_sha256() -> str:
    return files_sha256(REPO_ROOT, CROSS_AGENT_CONTRACT_FILES)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_scorecard(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"]
    if not isinstance(payload, dict):
        return [f"{path}: scorecard must be a JSON object"]
    if set(payload) != {"schema", "task_id", "criteria"}:
        errors.append(f"{path}: top-level keys must be schema, task_id, and criteria")
    if payload.get("schema") != "design-craft.cross-agent-scorecard.v1":
        errors.append(f"{path}: invalid scorecard schema")
    if payload.get("task_id") != path.parent.name:
        errors.append(f"{path}: task_id must be {path.parent.name}")
    criteria = payload.get("criteria")
    if not isinstance(criteria, list):
        return [*errors, f"{path}: criteria must be an array"]
    expected_ids = list(OBSERVED_REQUIRED_CRITERIA)
    observed_ids: list[str] = []
    weights: list[int] = []
    allowed_keys = {"id", "label", "weight", "pass_evidence", "deduction_trigger"}
    for index, criterion in enumerate(criteria):
        if not isinstance(criterion, dict):
            errors.append(f"{path}: criteria[{index}] must be an object")
            continue
        extra = set(criterion) - allowed_keys
        missing = allowed_keys - set(criterion)
        if extra or missing:
            errors.append(
                f"{path}: criteria[{index}] keys mismatch "
                f"missing={sorted(missing)} extra={sorted(extra)}"
            )
        criterion_id = criterion.get("id")
        if not isinstance(criterion_id, str):
            errors.append(f"{path}: criteria[{index}].id must be a string")
        else:
            observed_ids.append(criterion_id)
        weight = criterion.get("weight")
        if not isinstance(weight, int) or isinstance(weight, bool) or weight <= 0:
            errors.append(f"{path}: criteria[{index}].weight must be a positive integer")
        else:
            weights.append(weight)
        for key in ("label", "pass_evidence", "deduction_trigger"):
            value = criterion.get(key)
            if not isinstance(value, str) or len(value.strip()) < 8:
                errors.append(
                    f"{path}: criteria[{index}].{key} must be descriptive text"
                )
    if observed_ids != expected_ids:
        errors.append(f"{path}: criteria ids must be {expected_ids}")
    if len(weights) == len(criteria) and sum(weights) != 100:
        errors.append(f"{path}: scorecard weights must sum to 100, got {sum(weights)}")
    return errors


def scorecard_weights(path: Path) -> dict[str, int]:
    try:
        payload = json.loads(read_text(path))
    except (OSError, json.JSONDecodeError):
        return {}
    criteria = payload.get("criteria") if isinstance(payload, dict) else None
    if not isinstance(criteria, list):
        return {}
    values: dict[str, int] = {}
    for criterion in criteria:
        if not isinstance(criterion, dict):
            return {}
        criterion_id = criterion.get("id")
        weight = criterion.get("weight")
        if (
            not isinstance(criterion_id, str)
            or criterion_id in values
            or not isinstance(weight, int)
            or isinstance(weight, bool)
        ):
            return {}
        values[criterion_id] = weight
    if tuple(values) != OBSERVED_REQUIRED_CRITERIA or sum(values.values()) != 100:
        return {}
    return values


def load_evidence_status(path: Path) -> tuple[dict[str, str], list[str]]:
    try:
        payload = json.loads(read_text(path))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"{path}: invalid evidence status JSON: {exc}"]
    errors: list[str] = []
    if not isinstance(payload, dict):
        return {}, [f"{path}: evidence status must be a JSON object"]
    if set(payload) != {"schema", "task_id", "hosts"}:
        errors.append(f"{path}: top-level keys must be schema, task_id, and hosts")
    if payload.get("schema") != STATUS_SCHEMA:
        errors.append(f"{path}: schema must be {STATUS_SCHEMA}")
    if payload.get("task_id") != path.parent.name:
        errors.append(f"{path}: task_id must be {path.parent.name}")
    hosts = payload.get("hosts")
    if not isinstance(hosts, dict) or set(hosts) != set(HOSTS):
        errors.append(f"{path}: hosts must contain {list(HOSTS)} exactly once")
        return {}, errors
    states: dict[str, str] = {}
    for host in HOSTS:
        item = hosts.get(host)
        if not isinstance(item, dict) or set(item) != {"status", "reason"}:
            errors.append(f"{path}: hosts.{host} must contain status and reason")
            continue
        status = item.get("status")
        reason = item.get("reason")
        if status not in HOST_STATES:
            errors.append(
                f"{path}: hosts.{host}.status must be one of {sorted(HOST_STATES)}"
            )
        else:
            states[host] = status
        if not isinstance(reason, str) or len(reason.strip()) < 12:
            errors.append(f"{path}: hosts.{host}.reason must explain the current state")
    return states, errors


def render_current_comparison(task_dir: Path) -> str:
    status_path = task_dir / "evidence-status.json"
    _, errors = load_evidence_status(status_path)
    if errors:
        raise ValueError("; ".join(errors))
    payload = json.loads(read_text(status_path))

    def cell(value: object) -> str:
        return " ".join(str(value).split()).replace("|", "\\|")

    lines = [
        "# Current cross-agent evidence status",
        "",
        "Generated from `evidence-status.json`; do not edit by hand.",
        "",
        "| Host | Status | Reason |",
        "|---|---|---|",
    ]
    for host in HOSTS:
        item = payload["hosts"][host]
        lines.append(
            f"| {cell(host)} | {cell(item['status'])} | {cell(item['reason'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def validate_task_definition(path: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        file_path = path / name
        if not file_path.is_file():
            errors.append(f"{path}: missing required file {name}")
            continue
        text = read_text(file_path)
        if PLACEHOLDER_PATTERN.search(text):
            errors.append(f"{file_path}: contains template placeholder text")
        if len(text.strip()) < 80:
            errors.append(f"{file_path}: file is too sparse for an active benchmark task")
    prompt_path = path / "prompt.md"
    if prompt_path.is_file() and "design-craft" not in read_text(prompt_path).lower():
        errors.append(f"{prompt_path}: prompt must explicitly route through design-craft")
    findings_path = path / "expected-findings.md"
    if findings_path.is_file():
        bullet_count = sum(
            1
            for line in read_text(findings_path).splitlines()
            if re.match(r"^\s*[-*]\s+\S", line)
        )
        if bullet_count < 3:
            errors.append(
                f"{findings_path}: expected findings must include at least three bullets"
            )
    scorecard_path = path / "scorecard.json"
    if scorecard_path.is_file():
        errors.extend(validate_scorecard(scorecard_path))
    status_path = path / "evidence-status.json"
    status_errors: list[str] = []
    if status_path.is_file():
        _, status_errors = load_evidence_status(status_path)
        errors.extend(status_errors)
    comparison_path = path / "comparison.md"
    if status_path.is_file() and comparison_path.is_file() and not status_errors:
        try:
            expected_comparison = render_current_comparison(path)
        except (OSError, ValueError) as exc:
            errors.append(f"{comparison_path}: cannot render evidence status: {exc}")
        else:
            if read_text(comparison_path) != expected_comparison:
                errors.append(
                    f"{comparison_path}: must be generated exactly from evidence-status.json"
                )
    for legacy_note in path.glob("*-unverified.md"):
        errors.append(
            f"{legacy_note}: active tasks must record host state in evidence-status.json"
        )
    return errors


def validate_definition_root(root: Path) -> list[str]:
    if not root.is_dir():
        return [f"{root}: cross-agent benchmark root does not exist"]
    task_dirs = sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and path.name.startswith("same-prompt-")
    )
    if not task_dirs:
        return [f"{root}: at least one active benchmark task directory is required"]
    errors: list[str] = []
    for task_dir in task_dirs:
        errors.extend(validate_task_definition(task_dir))
    return errors
