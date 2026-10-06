#!/usr/bin/env python3
"""Unblind and record a hash-bound comparative judgment from a controlled judge run."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from design_craft_comparative_common import (
    BLIND_LABELS,
    BLIND_MAP_SCHEMA,
    JUDGE_RUN_SCHEMA,
    RESULT_SCHEMA,
    RUN_SCHEMA,
    VARIANTS_SCHEMA,
    load_scorecard,
    sha256_file,
    validate_judgment,
    validate_judgment_schema,
    variant_ids,
)
from design_craft_cross_agent_run import publish_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--judgment", help="Defaults to <case>/blind-judgment.json.")
    parser.add_argument("--judge-run", help="Defaults to <case>/run.judge.json.")
    parser.add_argument("--judge-host", help="Optional assertion against the run manifest.")
    parser.add_argument("--judge-version", help="Optional assertion against the run manifest.")
    parser.add_argument("--judge-model", help="Optional assertion against the run manifest.")
    parser.add_argument("--judge-reasoning", help="Optional assertion against the run manifest.")
    parser.add_argument("--output")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    case_dir = Path(args.case_dir).expanduser().resolve()
    judgment_path = (
        Path(args.judgment).expanduser().resolve()
        if args.judgment
        else case_dir / "blind-judgment.json"
    )
    judge_run_path = (
        Path(args.judge_run).expanduser().resolve()
        if args.judge_run
        else case_dir / "run.judge.json"
    )
    map_path = case_dir / "blind-map.json"
    packet_path = case_dir / "blind-packet.md"
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else case_dir / "comparison.json"
    )
    if output_path.exists() and not args.force:
        parser.error(f"refusing to overwrite comparative result: {output_path}")
    try:
        mapping = json.loads(map_path.read_text(encoding="utf-8"))
        judgment = json.loads(judgment_path.read_text(encoding="utf-8"))
        judge_run = json.loads(judge_run_path.read_text(encoding="utf-8"))
        variants_payload = json.loads(
            (case_dir / "variants.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    if variants_payload.get("schema") != VARIANTS_SCHEMA:
        parser.error(f"variants.json must use {VARIANTS_SCHEMA}")
    try:
        required_variants = variant_ids(variants_payload)
    except ValueError as exc:
        parser.error(str(exc))

    weights, errors = load_scorecard(case_dir)
    errors.extend(validate_judgment_schema(case_dir, weights))
    errors.extend(validate_judgment(judgment, weights))
    if errors:
        parser.error("; ".join(errors))
    if mapping.get("schema") != BLIND_MAP_SCHEMA:
        parser.error(f"blind map must use {BLIND_MAP_SCHEMA}")
    expected_map_hashes = {
        "packet_sha256": packet_path,
        "prompt_sha256": case_dir / "prompt.md",
        "scorecard_sha256": case_dir / "scorecard.md",
        "scorecard_json_sha256": case_dir / "scorecard.json",
        "judgment_schema_sha256": case_dir / "judgment.schema.json",
    }
    for field, path in expected_map_hashes.items():
        if not path.is_file() or mapping.get(field) != sha256_file(path):
            parser.error(f"blind map {field} does not match {path.name}")

    if judge_run.get("schema") != JUDGE_RUN_SCHEMA:
        parser.error(f"judge run must use {JUDGE_RUN_SCHEMA}")
    if judge_run.get("host") == "pi":
        parser.error("judge host must be independent from the Pi variant host")
    assertions = {
        "--judge-host": (args.judge_host, judge_run.get("host")),
        "--judge-version": (args.judge_version, judge_run.get("host_version")),
        "--judge-model": (args.judge_model, judge_run.get("model")),
        "--judge-reasoning": (
            args.judge_reasoning,
            judge_run.get("reasoning_profile"),
        ),
    }
    for label, (asserted, observed) in assertions.items():
        if asserted is not None and asserted != observed:
            parser.error(f"{label} must match the controlled judge run")
    if judge_run.get("packet_sha256") != sha256_file(packet_path):
        parser.error("judge run packet hash does not match blind-packet.md")
    if judge_run.get("judgment_schema_sha256") != sha256_file(
        case_dir / "judgment.schema.json"
    ):
        parser.error("judge run schema hash does not match judgment.schema.json")
    if judge_run.get("judgment_path") != judgment_path.name:
        parser.error("judge run judgment_path does not match the admitted judgment")
    if judge_run.get("judgment_sha256") != sha256_file(judgment_path):
        parser.error("judge run judgment hash does not match the admitted judgment")
    raw_output_path = case_dir / str(judge_run.get("raw_output_path", ""))
    if not raw_output_path.is_file() or judge_run.get("raw_output_sha256") != sha256_file(
        raw_output_path
    ):
        parser.error("judge raw output is missing or does not match the run manifest")
    if judge_run.get("returncode") != 0 or judge_run.get("worktree_unchanged") is not True:
        parser.error("judge run must be successful and non-mutating")
    if judge_run.get("worktree_before_sha256") != judge_run.get("worktree_after_sha256"):
        parser.error("judge run worktree fingerprints must match")

    label_map = {
        label: item.get("variant")
        for label, item in mapping.get("outputs", {}).items()
        if isinstance(item, dict)
    }
    if set(label_map) != set(BLIND_LABELS) or set(label_map.values()) != set(
        required_variants
    ):
        parser.error("blind map must assign A, B, and C to every comparative variant")

    results: dict[str, dict] = {}
    for item in judgment["results"]:
        label = item["label"]
        variant = label_map[label]
        results[variant] = {
            "blind_label": label,
            "score": item["total"],
            "criteria": item["criteria"],
            "summary": item["summary"],
        }
    winner_label = judgment["winner"]
    winner = label_map[winner_label]

    variant_runs: dict[str, dict] = {}
    for label, variant in label_map.items():
        mapping_item = mapping["outputs"][label]
        output_file = case_dir / str(mapping_item.get("path", ""))
        run_file = case_dir / str(mapping_item.get("run_path", ""))
        if not output_file.is_file() or mapping_item.get("sha256") != sha256_file(output_file):
            parser.error(f"blind map output for {variant} is missing or changed")
        if not run_file.is_file() or mapping_item.get("run_sha256") != sha256_file(run_file):
            parser.error(f"blind map run for {variant} is missing or changed")
        try:
            run_payload = json.loads(run_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            parser.error(f"invalid run manifest for {variant}: {exc}")
        if run_payload.get("schema") != RUN_SCHEMA or run_payload.get("variant") != variant:
            parser.error(f"run manifest for {variant} is incompatible")
        variant_runs[variant] = {
            "run_path": run_file.name,
            "run_sha256": sha256_file(run_file),
            "output_path": output_file.name,
            "output_sha256": sha256_file(output_file),
            "host": run_payload.get("host"),
            "host_version": run_payload.get("host_version"),
            "model": run_payload.get("model"),
            "thinking": run_payload.get("thinking"),
            "source_commit": run_payload.get("source_commit"),
            "skill_trees": run_payload.get("skill_trees"),
            "source_trees": run_payload.get("source_trees"),
            "source_fingerprints": run_payload.get("source_fingerprints"),
            "skill_install_mode": run_payload.get("skill_install_mode"),
            "contract_sha256": run_payload.get("contract_sha256"),
        }

    payload = {
        "schema": RESULT_SCHEMA,
        "case_id": case_dir.name,
        "focused_variant": variants_payload["focused_variant"],
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "judge": {
            "host": judge_run.get("host"),
            "version": judge_run.get("host_version"),
            "model": judge_run.get("model"),
            "model_observation": judge_run.get("model_observation"),
            "reasoning": judge_run.get("reasoning_profile"),
            "reasoning_observation": judge_run.get("reasoning_observation"),
            "runner_os": judge_run.get("runner_os"),
            "run_path": judge_run_path.name,
            "run_sha256": sha256_file(judge_run_path),
            "raw_output_path": raw_output_path.name,
            "raw_output_sha256": sha256_file(raw_output_path),
        },
        "prompt_sha256": sha256_file(case_dir / "prompt.md"),
        "scorecard_sha256": sha256_file(case_dir / "scorecard.md"),
        "scorecard_json_sha256": sha256_file(case_dir / "scorecard.json"),
        "judgment_schema_sha256": sha256_file(case_dir / "judgment.schema.json"),
        "blind_map_sha256": sha256_file(map_path),
        "blind_packet_sha256": sha256_file(packet_path),
        "judgment_path": judgment_path.name,
        "judgment_sha256": sha256_file(judgment_path),
        "variant_runs": variant_runs,
        "winner": winner,
        "rationale": judgment["rationale"],
        "results": results,
    }
    output_bytes = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    publish_files({output_path: output_bytes})
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
