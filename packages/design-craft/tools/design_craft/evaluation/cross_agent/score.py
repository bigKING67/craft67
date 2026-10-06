from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.design_craft_evidence_common import sha256_file

from .contract import (
    CURRENT_SCORE_KEYS,
    OBSERVED_REQUIRED_CRITERIA,
    OBSERVED_SCHEMA_V2,
    OBSERVED_SCHEMA_V3,
    OBSERVED_SCHEMA_V4,
    OBSERVED_SCHEMA_V5,
    cross_agent_contract_sha256,
    read_text,
    scorecard_weights,
)
from .current_source import validate_current_source
from .history import historical_scorecard_weights
from .run_evidence import validate_run_manifest


OBSERVED_SCHEMAS = {
    OBSERVED_SCHEMA_V2,
    OBSERVED_SCHEMA_V3,
    OBSERVED_SCHEMA_V4,
    OBSERVED_SCHEMA_V5,
}
RUN_BOUND_SCHEMAS = {
    OBSERVED_SCHEMA_V3,
    OBSERVED_SCHEMA_V4,
    OBSERVED_SCHEMA_V5,
}
JSON_SCORECARD_SCHEMAS = {OBSERVED_SCHEMA_V4, OBSERVED_SCHEMA_V5}


def _validate_criteria(
    task_dir: Path,
    path: Path,
    payload: dict,
    schema: object,
    score: object,
) -> list[str]:
    errors: list[str] = []
    criteria = payload.get("criteria")
    if not isinstance(criteria, dict):
        return [f"{path}: criteria must be an object"]
    if set(criteria) != set(OBSERVED_REQUIRED_CRITERIA):
        errors.append(
            f"{path}: criteria must contain exactly "
            f"{list(OBSERVED_REQUIRED_CRITERIA)}"
        )
    if schema in JSON_SCORECARD_SCHEMAS:
        weights = scorecard_weights(task_dir / "scorecard.json")
    elif schema in {OBSERVED_SCHEMA_V2, OBSERVED_SCHEMA_V3}:
        weights = historical_scorecard_weights(task_dir / "scorecard.md")
    else:
        weights = {}
    earned_total = 0
    for criterion in OBSERVED_REQUIRED_CRITERIA:
        result = criteria.get(criterion)
        if not isinstance(result, dict):
            errors.append(f"{path}: criteria.{criterion} must be an object")
            continue
        expected_result_keys = (
            {"passed", "earned", "note"}
            if schema in OBSERVED_SCHEMAS
            else {"passed", "note"}
        )
        if set(result) != expected_result_keys:
            errors.append(
                f"{path}: criteria.{criterion} fields must be "
                f"{sorted(expected_result_keys)}"
            )
        if not isinstance(result.get("passed"), bool):
            errors.append(f"{path}: criteria.{criterion}.passed must be boolean")
        note = result.get("note")
        if not isinstance(note, str) or len(note.strip()) < 8:
            errors.append(
                f"{path}: criteria.{criterion}.note must explain the result"
            )
        if schema in OBSERVED_SCHEMAS:
            weight = weights.get(criterion)
            earned = result.get("earned")
            if weight is None:
                errors.append(
                    f"{path}: scorecard weight is unavailable for {criterion}"
                )
            elif (
                not isinstance(earned, int)
                or isinstance(earned, bool)
                or not 0 <= earned <= weight
            ):
                errors.append(
                    f"{path}: criteria.{criterion}.earned must be an integer "
                    f"from 0 to {weight}"
                )
            else:
                earned_total += earned
                if result.get("passed") is True and earned == 0:
                    errors.append(
                        f"{path}: criteria.{criterion} cannot pass with zero "
                        "earned points"
                    )
                if result.get("passed") is False and earned == weight:
                    errors.append(
                        f"{path}: criteria.{criterion} cannot fail with full "
                        "earned points"
                    )
    if schema in OBSERVED_SCHEMAS and isinstance(score, int) and score != earned_total:
        errors.append(
            f"{path}: score must equal the sum of criteria earned points "
            f"({earned_total}, observed {score})"
        )
    return errors


def validate_observed_score(
    task_dir: Path,
    host: str,
    prompt_hash: str,
    *,
    skill_root: Path,
    score_path: Path | None = None,
    require_current_schema: bool = False,
    require_current_source: bool = False,
) -> list[str]:
    errors: list[str] = []
    path = score_path or task_dir / f"score.{host}.json"
    if not path.is_file():
        return [f"{path}: missing observed score file"]
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"]

    schema = payload.get("schema")
    if schema not in OBSERVED_SCHEMAS:
        errors.append(
            f"{path}: schema must be historical v2/v3/v4 or current "
            f"{OBSERVED_SCHEMA_V5}"
        )
    if require_current_schema and schema != OBSERVED_SCHEMA_V5:
        errors.append(f"{path}: current evidence must use {OBSERVED_SCHEMA_V5}")
    if schema == OBSERVED_SCHEMA_V5 and set(payload) != CURRENT_SCORE_KEYS:
        errors.append(
            f"{path}: current score fields mismatch "
            f"missing={sorted(CURRENT_SCORE_KEYS - set(payload))} "
            f"extra={sorted(set(payload) - CURRENT_SCORE_KEYS)}"
        )
    if payload.get("task_id") != task_dir.name:
        errors.append(f"{path}: task_id must be {task_dir.name}")
    if payload.get("agent") != host:
        errors.append(f"{path}: agent must be {host}")
    if payload.get("verified") is not True:
        errors.append(f"{path}: observed host must set verified=true")
    if payload.get("prompt_sha256") != prompt_hash:
        errors.append(f"{path}: prompt_sha256 must match prompt.md")
    for key in ("agent_version", "date", "skill_path", "command_summary"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            errors.append(f"{path}: {key} must be a non-empty string")
    skill_path_value = str(payload.get("skill_path", ""))
    if re.match(r"^(?:/Users/|/home/|[A-Za-z]:[\\/]Users[\\/])", skill_path_value):
        errors.append(f"{path}: skill_path must redact the host home directory")
    score = payload.get("score")
    if (
        not isinstance(score, int)
        or isinstance(score, bool)
        or not 0 <= score <= 100
    ):
        errors.append(f"{path}: score must be an integer from 0 to 100")

    if schema in OBSERVED_SCHEMAS:
        for key in ("model", "reasoning_profile", "runner_os", "skill_version"):
            if not isinstance(payload.get(key), str) or not payload[key].strip():
                errors.append(f"{path}: {key} must be a non-empty string")
        if schema in RUN_BOUND_SCHEMAS:
            for key in (
                "model_observation",
                "reasoning_observation",
                "provenance_skill_path",
            ):
                if not isinstance(payload.get(key), str) or not payload[key].strip():
                    errors.append(f"{path}: {key} must be a non-empty string")

        source_commit = str(payload.get("skill_source_commit", ""))
        if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
            errors.append(
                f"{path}: skill_source_commit must be a full lowercase Git SHA"
            )
        source_dirty = payload.get("skill_source_dirty")
        if not isinstance(source_dirty, bool):
            errors.append(f"{path}: skill_source_dirty must be boolean")
        if "repo_dirty" in payload and not isinstance(payload.get("repo_dirty"), bool):
            errors.append(f"{path}: repo_dirty must be boolean when present")
        digest_keys = ["skill_tree_sha256", "output_sha256"]
        digest_keys.append(
            "scorecard_json_sha256"
            if schema in JSON_SCORECARD_SCHEMAS
            else "scorecard_sha256"
        )
        if schema in RUN_BOUND_SCHEMAS:
            digest_keys.extend(("contract_sha256", "run_manifest_sha256"))
        if schema == OBSERVED_SCHEMA_V5:
            digest_keys.extend(("behavior_sha256", "projected_skill_tree_sha256"))
        for key in digest_keys:
            if not re.fullmatch(r"[0-9a-f]{64}", str(payload.get(key, ""))):
                errors.append(f"{path}: {key} must be 64 lowercase hex characters")

        output_path_value = payload.get("output_path")
        if not isinstance(output_path_value, str) or not output_path_value.strip():
            errors.append(f"{path}: output_path must be a non-empty relative path")
        else:
            output_relative = Path(output_path_value)
            if output_relative.is_absolute() or ".." in output_relative.parts:
                errors.append(f"{path}: output_path must stay inside the task directory")
            else:
                output_path = task_dir / output_relative
                if output_path.name != f"{host}-output.md":
                    errors.append(
                        f"{path}: output_path must point to {host}-output.md"
                    )
                elif not output_path.is_file():
                    errors.append(f"{path}: output_path does not exist: {output_path}")
                elif payload.get("output_sha256") != sha256_file(output_path):
                    errors.append(
                        f"{path}: output_sha256 must match {output_path.name}"
                    )

        scorecard_path = task_dir / (
            "scorecard.json" if schema in JSON_SCORECARD_SCHEMAS else "scorecard.md"
        )
        scorecard_digest_key = (
            "scorecard_json_sha256"
            if schema in JSON_SCORECARD_SCHEMAS
            else "scorecard_sha256"
        )
        if (
            scorecard_path.is_file()
            and payload.get(scorecard_digest_key) != sha256_file(scorecard_path)
        ):
            errors.append(
                f"{path}: {scorecard_digest_key} must match {scorecard_path.name}"
            )

        if schema in RUN_BOUND_SCHEMAS:
            errors.extend(
                validate_run_manifest(
                    task_dir,
                    host,
                    prompt_hash,
                    score_payload=payload,
                    score_schema=schema,
                    score_path=path,
                )
            )

        if schema == OBSERVED_SCHEMA_V5:
            behavior_domain = payload.get("behavior_domain")
            if not isinstance(behavior_domain, str) or not behavior_domain:
                errors.append(
                    f"{path}: behavior_domain must be a non-empty string"
                )
            if payload.get("behavior_source_dirty") is not False:
                errors.append(f"{path}: behavior_source_dirty must be false")

        if require_current_source:
            errors.extend(
                validate_current_source(
                    task_dir,
                    skill_root,
                    payload,
                    schema,
                    path,
                )
            )

    errors.extend(_validate_criteria(task_dir, path, payload, schema, score))
    return errors
