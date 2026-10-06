#!/usr/bin/env python3
"""Generate answers through explicit active Skill invocations for quality evaluation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

from evidence_metadata import build_evidence_metadata
from live_runtime import (
    create_private_run_directory,
    ensure_private_directory,
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
DEFAULT_CASES = ROOT / "eval/execution/cases.json"
DEFAULT_ANSWERS = ROOT / "eval/answers/execution"
REASONING_EFFORT = "medium"


def load_cases(path: Path, case_ids: list[str]) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("execution cases must be a non-empty list")
    manifest_skills = {skill["name"] for skill in load_manifest()["skills"]}
    ids: set[str] = set()
    for case in cases:
        case_id = validate_case_id(case.get("id"), label="execution case id")
        if case_id in ids:
            raise ValueError(f"invalid or duplicate execution case id: {case_id!r}")
        ids.add(case_id)
        if case.get("skill") not in manifest_skills:
            raise ValueError(f"unknown execution skill for {case_id}: {case.get('skill')}")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError(f"execution case prompt is missing: {case_id}")
        if not isinstance(case.get("domain"), str):
            raise ValueError(f"execution case domain is missing: {case_id}")
    if not case_ids:
        return cases
    by_id = {case["id"]: case for case in cases}
    missing = sorted(set(case_ids) - set(by_id))
    if missing:
        raise ValueError(f"unknown execution cases: {', '.join(missing)}")
    return [by_id[case_id] for case_id in case_ids]


def run_case(
    case: dict[str, Any],
    *,
    model: str | None,
    timeout: int,
    config_overrides: list[str] | None = None,
    executor=subprocess.run,
    backend: str = "exec",
    reasoning_effort: str = REASONING_EFFORT,
) -> dict[str, Any]:
    maximum_characters = 6000 if case["domain"] in {
        "commerce_orchestration",
        "marketing_orchestration",
    } else 4000
    instruction = f"""${case['skill']}

必须使用上面显式指定的已安装 Skill 作为主工作流回答下面任务。不要读取当前仓库源码，不要修改文件，不要执行外部写操作；直接给出完整的简体中文最终答案。事实不足时明确区分已知事实、假设和待核验信息，不得虚构平台当前规则或业务数据。优先保留决策、机制、护栏、责任人和复盘信号，避免重复题目或铺陈；正文控制在约 {maximum_characters} 个中文字符以内。

用户任务：
{case['prompt']}"""
    if backend == "app-server":
        from app_server_runtime import run_app_server
        runtime = run_app_server(
            instruction, skill_name=case["skill"], model=model,
            reasoning_effort=reasoning_effort, timeout=timeout,
            config_overrides=config_overrides,
        )
    elif backend == "exec":
        runtime = run_ephemeral_codex(
            instruction,
            reasoning_effort=reasoning_effort,
            model=model,
            timeout=timeout,
            config_overrides=config_overrides,
            executor=executor,
        )
    else:
        raise ValueError("unknown execution backend")
    base = {
        "id": case["id"],
        "skill": case["skill"],
        "backend": backend,
        "reasoning_effort": reasoning_effort,
        "skill_input_receipt": runtime.get("skill_input_receipt"),
        "runtime_skill_loading_verified": False,
        "execution_events": runtime.get("execution_events"),
        "domain": case["domain"],
        "prompt_sha256": sha256_text(case["prompt"]),
        "duration_seconds": runtime["duration_seconds"],
        "model": runtime.get("model"),
    }
    if not runtime["ok"]:
        return {**base, "generated": False, "error": runtime["error"]}
    if not runtime["answer"].strip():
        return {**base, "generated": False, "error": "empty generated answer"}
    return {
        **base,
        "generated": True,
        "answer": runtime["answer"],
        "answer_sha256": runtime["answer_sha256"],
    }


def self_test() -> None:
    case = {
        "id": "fake",
        "skill": "commerce-growth-os",
        "domain": "orchestration",
        "prompt": "fake prompt",
    }
    result = run_case(
        case,
        model=None,
        timeout=1,
        executor=fake_codex_executor("fake generated answer"),
    )
    if not result["generated"] or result["answer_sha256"] != sha256_text("fake generated answer"):
        raise AssertionError(f"fake execution should produce a hashed answer: {result}")
    empty = run_case(
        case,
        model=None,
        timeout=1,
        executor=fake_codex_executor("   "),
    )
    if empty["generated"] or empty.get("error") != "empty generated answer":
        raise AssertionError(f"empty execution answer should fail: {empty}")
    with tempfile.TemporaryDirectory(prefix="execution-self-test-") as temp:
        answer = Path(temp) / "fake.txt"
        answer.write_text(result["answer"], encoding="utf-8")
        if sha256_text(answer.read_text(encoding="utf-8")) != result["answer_sha256"]:
            raise AssertionError("written execution answer hash changed")
        cases_path = Path(temp) / "cases.json"
        for unsafe_id in ("/tmp/absolute", "../escape", "a/b", "Upper Case"):
            cases_path.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "id": unsafe_id,
                                "skill": "commerce-growth-os",
                                "domain": "commerce_orchestration",
                                "prompt": "fake prompt",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            try:
                load_cases(cases_path, [])
            except ValueError:
                pass
            else:
                raise AssertionError(f"unsafe execution case id must fail: {unsafe_id}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Exit codes: 0 generated all answers, 2 setup or runtime failure.",
    )
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--answer-dir")
    parser.add_argument("--install-root")
    parser.add_argument("--model")
    parser.add_argument("--reasoning-effort", choices=["low", "medium", "high", "xhigh"], default=REASONING_EFFORT)
    parser.add_argument("--backend", choices=["exec", "app-server"], default="exec")
    parser.add_argument("--codex-config", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-model-calls", type=int)
    parser.add_argument("--max-total-seconds", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print("explicit-skill execution runner self-test passed")
            return 0
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        if args.backend == "app-server" and not args.model:
            raise ValueError("--backend app-server requires --model")
        codex_config = validate_codex_config_overrides(args.codex_config)
        cases_path = Path(args.cases).expanduser().resolve()
        cases = load_cases(cases_path, args.case_id)
        if args.max_model_calls is not None and len(cases) > args.max_model_calls:
            raise ValueError(
                f"planned execution calls {len(cases)} exceed budget {args.max_model_calls}"
            )
        if args.max_total_seconds is not None and args.max_total_seconds <= 0:
            raise ValueError("max-total-seconds must be positive")
        active_install = verify_active_install(
            install_root=Path(args.install_root) if args.install_root else None,
            skill_names=sorted({case["skill"] for case in cases}),
        )
        plan = {
            "planned_model_calls": len(cases),
            "backend": args.backend,
            "reasoning_effort": args.reasoning_effort,
            "selected_case_ids": [case["id"] for case in cases],
            "selected_skills": sorted({case["skill"] for case in cases}),
            "codex_config_override_keys": [value.split("=", 1)[0] for value in codex_config],
            "codex_config_overrides_sha256": sha256_text(
                json.dumps(codex_config, ensure_ascii=True, separators=(",", ":"))
            ),
            "active_install": active_install,
        }
        if args.dry_run:
            print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
            return 0

        if args.answer_dir:
            answer_dir = ensure_private_directory(
                Path(args.answer_dir).expanduser(),
                require_empty=True,
            )
        else:
            _, answer_dir = create_private_run_directory(DEFAULT_ANSWERS)
        started = time.monotonic()
        results: list[dict[str, Any]] = []
        calls_used = 0
        for index, case in enumerate(cases):
            elapsed = time.monotonic() - started
            if args.max_total_seconds is not None and elapsed >= args.max_total_seconds:
                results.extend(
                    {
                        "id": pending["id"],
                        "skill": pending["skill"],
                        "generated": False,
                        "error": "max-total-seconds exhausted before model call",
                    }
                    for pending in cases[index:]
                )
                break
            timeout = args.timeout
            if args.max_total_seconds is not None:
                timeout = max(1, min(timeout, int(args.max_total_seconds - elapsed)))
            result = run_case(
                case,
                model=args.model,
                timeout=timeout,
                config_overrides=codex_config,
                backend=args.backend,
                reasoning_effort=args.reasoning_effort,
            )
            calls_used += 1
            if result["generated"]:
                answer_path = answer_dir / f"{case['id']}.txt"
                write_private_text(
                    answer_path,
                    result.pop("answer").rstrip() + "\n",
                    overwrite=False,
                )
                result["answer_path"] = str(answer_path)
                result["answer_sha256"] = sha256_text(answer_path.read_text(encoding="utf-8"))
            results.append(result)

        answer_inputs = {
            f"answer:{result['id']}": Path(result["answer_path"])
            for result in results
            if result.get("generated")
        }
        summary = {
            "metadata": build_evidence_metadata(
                "explicit-skill-execution",
                {"manifest": ROOT / "skill-pack.json", "cases": cases_path, **answer_inputs},
                include_codex=True,
                requested_model=args.model,
                reasoning_effort=args.reasoning_effort,
                extra={
                    "selected_case_ids": [case["id"] for case in cases],
                    "active_install": active_install,
                    "answer_dir": str(answer_dir),
                    "codex_config_override_keys": [
                        value.split("=", 1)[0] for value in codex_config
                    ],
                    "codex_config_overrides_sha256": sha256_text(
                        json.dumps(codex_config, ensure_ascii=True, separators=(",", ":"))
                    ),
                },
            ),
            "passed": len(results) == len(cases) and all(result.get("generated") for result in results),
            "cases": len(results),
            "failed": [result["id"] for result in results if not result.get("generated")],
            "model_calls": calls_used,
            "duration_seconds": round(time.monotonic() - started, 3),
            "results": results,
        }
        rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        if args.output:
            output = Path(args.output).expanduser().resolve()
            write_private_text(output, rendered + "\n")
            print(f"execution artifact: {output}")
        print(json.dumps({key: summary[key] for key in ("passed", "cases", "failed", "model_calls")}, ensure_ascii=False))
        return 0 if summary["passed"] else 2
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"run_execution_eval error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
