#!/usr/bin/env python3
"""Run real ephemeral Codex sessions to verify active-skill selection."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

from evidence_metadata import build_evidence_metadata
from live_runtime import (
    fake_codex_executor,
    load_manifest,
    run_ephemeral_codex,
    sha256_text,
    validate_case_id,
    validate_codex_config_overrides,
    verify_active_install,
    write_private_text,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = ROOT / "eval/forward-routing/cases.json"
DEFAULT_SCHEMA = ROOT / "eval/forward-routing/output.schema.json"
REASONING_EFFORT = "medium"


def load_cases(path: Path, case_ids: list[str]) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("forward-routing cases must be a non-empty list")
    if any(not isinstance(case, dict) for case in cases):
        raise ValueError("each forward-routing case must be an object")
    known_skills = {skill["name"] for skill in load_manifest()["skills"]}
    ids = [validate_case_id(case.get("id"), label="forward-routing case id") for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("forward-routing case ids must be unique strings")
    for case in cases:
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError(f"forward-routing prompt is missing: {case.get('id')}")
        expected = case.get("expected")
        if (
            not isinstance(expected, list)
            or not expected
            or len(expected) != len(set(expected))
            or any(name not in known_skills for name in expected)
        ):
            raise ValueError(f"forward-routing expected Skills are invalid: {case.get('id')}")
    if not case_ids:
        return cases
    by_id = {case["id"]: case for case in cases}
    missing = sorted(set(case_ids) - set(by_id))
    if missing:
        raise ValueError(f"unknown forward-routing cases: {', '.join(missing)}")
    return [by_id[case_id] for case_id in case_ids]


def run_case(
    case: dict[str, Any],
    schema: Path,
    model: str | None,
    timeout: int,
    *,
    config_overrides: list[str] | None = None,
    reasoning_effort: str = REASONING_EFFORT,
    executor=subprocess.run,
) -> dict[str, Any]:
    instruction = (
        "只做技能路由判断，不要读取仓库文件，不要调用任何工具，不要执行任务本身。"
        f"用户任务：{case['prompt']} "
        "选择完成任务所需的最小已安装 Skill 集合。必须遵守已安装 Skill description 中明确的职责所有权和组合边界；"
        "用户要求全年整合 Marketing、完整经营方案、综合诊断或跨专业冲突裁决时，选择对应 orchestrator 即可；"
        "除非用户显式要求某个 specialist 的独立深度交付，否则不要同时枚举该 orchestrator 内部编排的 specialists。"
        "对于有明确边界的跨域单项交付，直接组合拥有关键决策权的 specialists，不额外加入 orchestrator，也不能省略必要 specialist。"
        "selected_skills 必须使用精确 Skill name；reason 只写一句简短理由。"
    )
    runtime = run_ephemeral_codex(
        instruction,
        reasoning_effort=reasoning_effort,
        model=model,
        timeout=timeout,
        schema=schema,
        config_overrides=config_overrides,
        executor=executor,
    )
    base = {
        "id": case["id"],
        "prompt_sha256": sha256_text(case["prompt"]),
        "duration_seconds": runtime["duration_seconds"],
        "model": runtime.get("model"),
    }
    if not runtime["ok"]:
        return {**base, "passed": False, "error": runtime["error"]}
    try:
        payload = json.loads(runtime["answer"])
    except json.JSONDecodeError as exc:
        return {**base, "passed": False, "error": f"invalid structured output: {exc}"}
    selected = sorted(payload.get("selected_skills", []))
    expected = sorted(case["expected"])
    return {
        **base,
        "passed": selected == expected,
        "expected": expected,
        "selected": selected,
        "reason": payload.get("reason", ""),
        "response_sha256": runtime["answer_sha256"],
        "response": runtime["answer"],
    }


def build_summary(
    cases: list[dict[str, Any]],
    *,
    cases_path: Path,
    schema: Path,
    model: str | None,
    timeout: int,
    active_install: dict[str, Any],
    config_overrides: list[str] | None = None,
    reasoning_effort: str = REASONING_EFFORT,
) -> dict[str, Any]:
    results = [
        run_case(case, schema, model, timeout, config_overrides=config_overrides, reasoning_effort=reasoning_effort)
        for case in cases
    ]
    return {
        "metadata": build_evidence_metadata(
            "description-routing-probe",
            {"manifest": ROOT / "skill-pack.json", "cases": cases_path, "schema": schema},
            include_codex=True,
            requested_model=model,
            reasoning_effort=reasoning_effort,
            extra={
                "selected_case_ids": [case["id"] for case in cases],
                "active_install": active_install,
                "auto_activation_verified": False,
                "codex_config_override_keys": [
                    value.split("=", 1)[0] for value in (config_overrides or [])
                ],
                "codex_config_overrides_sha256": sha256_text(
                    json.dumps(config_overrides or [], ensure_ascii=True, separators=(",", ":"))
                ),
            },
        ),
        "auto_activation_verified": False,
        "passed": all(result["passed"] for result in results),
        "cases": len(results),
        "failed": [result["id"] for result in results if not result["passed"]],
        "results": results,
    }


def self_test() -> None:
    case = {"id": "fake", "prompt": "test prompt", "expected": ["commerce-growth-os"]}
    payload = json.dumps(
        {"selected_skills": ["commerce-growth-os"], "reason": "fake"},
        ensure_ascii=False,
    )
    def high_executor(command, **kwargs):
        if 'model_reasoning_effort="high"' not in command:
            raise AssertionError("high effort must reach routing Codex argv")
        return fake_codex_executor(payload)(command, **kwargs)

    result = run_case(
        case,
        DEFAULT_SCHEMA,
        None,
        1,
        reasoning_effort="high",
        executor=high_executor,
    )
    if not result["passed"] or result["selected"] != case["expected"]:
        raise AssertionError(f"fake runtime selection should pass: {result}")
    malformed = run_case(
        case,
        DEFAULT_SCHEMA,
        None,
        1,
        executor=fake_codex_executor("not-json"),
    )
    if malformed["passed"] or "invalid structured output" not in malformed["error"]:
        raise AssertionError(f"malformed selection output should fail: {malformed}")

    def timeout_executor(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(command, 1)

    timed_out = run_case(case, DEFAULT_SCHEMA, None, 1, executor=timeout_executor)
    if timed_out["passed"] or "timed out" not in timed_out["error"]:
        raise AssertionError(f"runtime timeout should be observable: {timed_out}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Exit codes: 0 passed, 1 routing mismatch, 2 setup or runtime failure.",
    )
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--model")
    parser.add_argument("--reasoning-effort", choices=["low", "medium", "high", "xhigh"], default=REASONING_EFFORT)
    parser.add_argument("--codex-config", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--install-root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", help="Optional JSON result artifact")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print("forward routing runner self-test passed")
            return 0
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        codex_config = validate_codex_config_overrides(args.codex_config)
        cases_path = Path(args.cases).expanduser().resolve()
        schema = Path(args.schema).expanduser().resolve()
        cases = load_cases(cases_path, args.case_id)
        json.loads(schema.read_text(encoding="utf-8"))
        active_install = verify_active_install(
            install_root=Path(args.install_root) if args.install_root else None,
        )
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "planned_model_calls": len(cases),
                        "selected_case_ids": [case["id"] for case in cases],
                        "codex_config_override_keys": [
                            value.split("=", 1)[0] for value in codex_config
                        ],
                        "codex_config_overrides_sha256": sha256_text(
                            json.dumps(codex_config, ensure_ascii=True, separators=(",", ":"))
                        ),
                        "active_install": active_install,
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        started = time.monotonic()
        summary = build_summary(
            cases,
            cases_path=cases_path,
            schema=schema,
            model=args.model,
            timeout=args.timeout,
            active_install=active_install,
            config_overrides=codex_config,
            reasoning_effort=args.reasoning_effort,
        )
        summary["duration_seconds"] = round(time.monotonic() - started, 3)
        rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        if args.output:
            output = Path(args.output).expanduser().resolve()
            write_private_text(output, rendered + "\n")
            print(f"forward routing artifact: {output}")
        print(json.dumps({key: summary[key] for key in ("passed", "cases", "failed")}, ensure_ascii=False))
        if any("error" in result for result in summary["results"]):
            return 2
        return 0 if summary["passed"] else 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"run_forward_routing_eval error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
