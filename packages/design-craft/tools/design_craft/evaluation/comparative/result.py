from __future__ import annotations

import json
from pathlib import Path

from scripts.design_craft_comparative_common import (
    RESULT_SCHEMA,
    RESULT_SCHEMA_V3,
    sha256_file,
)


def validate_result(
    case_dir: Path,
    *,
    blind_map: dict,
    judge_manifest: dict,
    judgment: dict,
    runs: dict[str, dict],
    required_variants: tuple[str, str, str],
    require_current_source: bool,
) -> list[str]:
    path = case_dir / "comparison.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: {exc}"]
    errors: list[str] = []
    result_schema = payload.get("schema")
    if (
        result_schema not in {RESULT_SCHEMA_V3, RESULT_SCHEMA}
        or payload.get("case_id") != case_dir.name
    ):
        errors.append(f"{path}: schema/case_id mismatch")
    if require_current_source and result_schema != RESULT_SCHEMA:
        errors.append(f"{path}: current result must use {RESULT_SCHEMA}")
    if payload.get("focused_variant") != required_variants[1]:
        errors.append(f"{path}: focused_variant mismatch")
    hashes = {
        "prompt_sha256": "prompt.md",
        "scorecard_sha256": "scorecard.md",
        "scorecard_json_sha256": "scorecard.json",
        "judgment_schema_sha256": "judgment.schema.json",
        "blind_map_sha256": "blind-map.json",
        "blind_packet_sha256": "blind-packet.md",
        "judgment_sha256": "blind-judgment.json",
    }
    for field, name in hashes.items():
        if payload.get(field) != sha256_file(case_dir / name):
            errors.append(f"{path}: {field} mismatch")
    judge = payload.get("judge")
    if not isinstance(judge, dict):
        errors.append(f"{path}: judge must be an object")
    else:
        expected_judge = {
            "host": judge_manifest.get("host"),
            "version": judge_manifest.get("host_version"),
            "model": judge_manifest.get("model"),
            "model_observation": judge_manifest.get("model_observation"),
            "reasoning": judge_manifest.get("reasoning_profile"),
            "reasoning_observation": judge_manifest.get("reasoning_observation"),
            "runner_os": judge_manifest.get("runner_os"),
            "run_path": "run.judge.json",
            "run_sha256": sha256_file(case_dir / "run.judge.json"),
            "raw_output_path": "judge-output.raw.txt",
            "raw_output_sha256": sha256_file(case_dir / "judge-output.raw.txt"),
        }
        if judge != expected_judge:
            errors.append(f"{path}: judge metadata must derive from run.judge.json")
    results = payload.get("results")
    if not isinstance(results, dict) or set(results) != set(required_variants):
        errors.append(f"{path}: results must cover every variant")
    else:
        scores = {
            variant: item.get("score") if isinstance(item, dict) else None
            for variant, item in results.items()
        }
        if not all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in scores.values()
        ):
            errors.append(f"{path}: every variant score must be an integer")
        elif not (
            all(
                scores["design-craft"] > scores[variant]
                for variant in required_variants
                if variant != "design-craft"
            )
            and payload.get("winner") == "design-craft"
        ):
            errors.append(
                f"{path}: certification requires design-craft to win the blind ablation"
            )
    if payload.get("rationale") != judgment.get("rationale"):
        errors.append(f"{path}: rationale must match the admitted judgment")
    variant_runs = payload.get("variant_runs")
    if not isinstance(variant_runs, dict) or set(variant_runs) != set(
        required_variants
    ):
        errors.append(f"{path}: variant_runs must cover every variant")
    else:
        for variant, run_payload in runs.items():
            expected = {
                "run_path": f"run.{variant}.json",
                "run_sha256": sha256_file(case_dir / f"run.{variant}.json"),
                "output_path": f"output.{variant}.md",
                "output_sha256": sha256_file(case_dir / f"output.{variant}.md"),
                "host": run_payload.get("host"),
                "host_version": run_payload.get("host_version"),
                "model": run_payload.get("model"),
                "thinking": run_payload.get("thinking"),
                "skill_trees": run_payload.get("skill_trees"),
                "contract_sha256": run_payload.get("contract_sha256"),
            }
            if result_schema == RESULT_SCHEMA:
                expected.update(
                    {
                        "source_trees": run_payload.get("source_trees"),
                        "source_commit": run_payload.get("source_commit"),
                        "source_fingerprints": run_payload.get(
                            "source_fingerprints"
                        ),
                        "skill_install_mode": run_payload.get("skill_install_mode"),
                    }
                )
            if variant_runs.get(variant) != expected:
                errors.append(
                    f"{path}: variant_runs.{variant} is not bound to current evidence"
                )
    label_map = {
        label: item.get("variant")
        for label, item in blind_map.get("outputs", {}).items()
        if isinstance(item, dict)
    }
    if label_map.get(judgment.get("winner")) != payload.get("winner"):
        errors.append(f"{path}: unblinded winner does not match the judgment")
    return errors
