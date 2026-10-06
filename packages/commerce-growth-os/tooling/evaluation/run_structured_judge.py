#!/usr/bin/env python3
"""Validate or run semantic answer judging with bounded ephemeral Codex sessions."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable


sys.dont_write_bytecode = True

from evidence_metadata import build_evidence_metadata
from live_runtime import (
    fake_codex_executor,
    run_ephemeral_codex,
    sha256_text,
    validate_case_id,
    validate_codex_config_overrides,
    write_private_text,
)
from tooling.installation.tree_integrity import TreeIntegrityError, validate_real_directory, validate_tree


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = ROOT / "eval/structured-judge/cases.json"
DEFAULT_RUBRIC = ROOT / "eval/structured-judge/rubric.json"
DEFAULT_SCHEMA = ROOT / "eval/structured-judge/output.schema.json"
PROMPT_CATALOGS = [ROOT / "eval/marketing/cases.json", ROOT / "eval/cases.json"]
REASONING_EFFORT = "medium"


def load_prompt_catalogs(extra: list[Path] | None = None) -> dict[str, str]:
    prompts: dict[str, str] = {}
    for path in [*PROMPT_CATALOGS, *(extra or [])]:
        if not path.is_file():
            continue
        for case in json.loads(path.read_text(encoding="utf-8")).get("cases", []):
            if isinstance(case.get("id"), str) and isinstance(case.get("prompt"), str):
                prompts[case["id"]] = case["prompt"]
    return prompts


def load_contract(cases_path: Path, rubric_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))["cases"]
    rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
    dimensions = rubric.get("dimensions", {})
    if len(dimensions) != 6:
        raise ValueError("structured judge must define exactly 6 dimensions")
    emphasis = rubric.get("domain_emphasis", {})
    if not isinstance(emphasis, dict) or not emphasis:
        raise ValueError("structured judge domain emphasis must be non-empty")
    ids = [validate_case_id(case.get("id"), label="structured-judge case id") for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("structured judge case ids must be unique strings")
    for case in cases:
        if case.get("domain") not in emphasis:
            raise ValueError(f"invalid judge domain for {case['id']}: {case.get('domain')}")
        for field in ("prompt_id", "answer_id"):
            if field in case:
                validate_case_id(case[field], label=f"{field} for {case['id']}")
    return cases, rubric


def select_cases(cases: list[dict[str, Any]], requested: list[str]) -> list[dict[str, Any]]:
    if not requested:
        return cases
    by_id = {case["id"]: case for case in cases}
    missing = sorted(set(requested) - set(by_id))
    if missing:
        raise ValueError(f"unknown structured-judge cases: {', '.join(missing)}")
    return [by_id[case_id] for case_id in requested]


def resolve_prompt(case: dict[str, Any], prompts: dict[str, str]) -> str:
    if isinstance(case.get("prompt"), str):
        return case["prompt"]
    prompt_id = validate_case_id(
        case.get("prompt_id", case["id"]),
        label=f"prompt id for {case['id']}",
    )
    if prompt_id not in prompts:
        raise ValueError(f"missing source prompt for judge case: {case['id']} -> {prompt_id}")
    return prompts[prompt_id]


def resolve_answer(case: dict[str, Any], answers_dir: Path | None) -> Path:
    if answers_dir is not None:
        try:
            boundary = validate_real_directory(answers_dir)
        except TreeIntegrityError as exc:
            raise ValueError(f"answers directory must be a real directory: {answers_dir}: {exc}") from exc
        answer_id = validate_case_id(
            case.get("answer_id", case["id"]),
            label=f"answer id for {case['id']}",
        )
        answer = boundary / f"{answer_id}.txt"
    else:
        boundary = ROOT / "eval"
        configured = case.get("answer")
        if not isinstance(configured, str):
            raise ValueError(f"judge case has no answer path: {case['id']}")
        relative = Path(configured)
        if relative.is_absolute() or not relative.parts or relative.parts[0] != "eval" or ".." in relative.parts:
            raise ValueError(f"judge answer must be a repository-relative eval path: {configured}")
        answer = ROOT / relative
    if not answer.is_file():
        raise ValueError(f"missing judge answer for {case['id']}: {answer}")
    try:
        validate_tree(answer, allowed_root=boundary)
    except TreeIntegrityError as exc:
        raise ValueError(f"unsafe judge answer for {case['id']}: {answer}: {exc}") from exc
    return answer.resolve()


def judge_attempt(
    case: dict[str, Any],
    rubric: dict[str, Any],
    prompt: str,
    answer: str,
    schema: Path,
    timeout: int,
    model: str | None,
    *,
    config_overrides: list[str] | None = None,
    reasoning_effort: str = REASONING_EFFORT,
    executor=subprocess.run,
) -> dict[str, Any]:
    dimension_text = "\n".join(
        f"- {name}: {description}" for name, description in rubric["dimensions"].items()
    )
    emphasis = "; ".join(rubric["domain_emphasis"][case["domain"]])
    hard_failures = "\n".join(f"- {item}" for item in rubric["hard_failures"])
    instruction = f"""你是严格的消费品牌经营与 Marketing 答案质量 Judge。不要调用工具，不要补写答案。

用户问题：
{prompt}

待评答案：
{answer}

领域：{case['domain']}
领域重点：{emphasis}

请对每个维度给 0-5 的整数分：
{dimension_text}

Hard failures：
{hard_failures}

只有答案实际满足时才给分；不要因为关键词出现就给高分。hard_failures 只列实际命中的问题，没有则返回空数组。summary 用一句话说明最重要的优点和缺口。"""
    runtime = run_ephemeral_codex(
        instruction,
        reasoning_effort=reasoning_effort,
        model=model,
        timeout=timeout,
        schema=schema,
        config_overrides=config_overrides,
        executor=executor,
    )
    if not runtime["ok"]:
        return {
            "ok": False,
            "duration_seconds": runtime["duration_seconds"],
            "model": runtime.get("model"),
            "error": runtime["error"],
        }
    try:
        payload = json.loads(runtime["answer"])
        scores = payload["scores"]
        scale = rubric["scale"]
        invalid = [
            name
            for name, score in scores.items()
            if type(score) is not int or not scale["min"] <= score <= scale["max"]
        ]
        if set(scores) != set(rubric["dimensions"]) or invalid:
            raise ValueError(f"invalid scores: {invalid or sorted(scores)}")
        if (
            not isinstance(payload["hard_failures"], list)
            or any(not isinstance(item, str) for item in payload["hard_failures"])
            or not isinstance(payload["summary"], str)
            or not payload["summary"].strip()
        ):
            raise ValueError("hard_failures and summary do not match the judge contract")
        total = sum(scores.values())
        contract = rubric["pass"]
        quality_passed = (
            total >= contract["minimum_total"]
            and min(scores.values()) >= contract["minimum_dimension"]
            and (not contract["hard_failures_must_be_empty"] or not payload["hard_failures"])
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "duration_seconds": runtime["duration_seconds"],
            "model": runtime.get("model"),
            "error": f"invalid judge output: {exc}",
        }
    return {
        "ok": True,
        "quality_passed": quality_passed,
        "total": total,
        "scores": scores,
        "hard_failures": payload["hard_failures"],
        "summary": payload["summary"],
        "model": runtime.get("model"),
        "duration_seconds": runtime["duration_seconds"],
        "response_sha256": runtime["answer_sha256"],
        "response": runtime["answer"],
    }


def is_boundary(attempt: dict[str, Any], rubric: dict[str, Any], margin: int) -> bool:
    if not attempt.get("ok"):
        return False
    contract = rubric["pass"]
    return (
        abs(attempt["total"] - contract["minimum_total"]) <= margin
        or min(attempt["scores"].values()) == contract["minimum_dimension"]
    )


def aggregate_case(case: dict[str, Any], attempts: list[dict[str, Any]]) -> dict[str, Any]:
    base = {"id": case["id"], "domain": case["domain"], "attempts": attempts}
    errors = [attempt["error"] for attempt in attempts if not attempt.get("ok")]
    if errors:
        return {**base, "passed": False, "error": "; ".join(errors)}
    quality_votes = sum(bool(attempt["quality_passed"]) for attempt in attempts)
    quality_passed = quality_votes > len(attempts) / 2
    expected_pass = case.get("expected_pass", True)
    dimensions = attempts[0]["scores"]
    aggregate_scores = {
        name: statistics.median(attempt["scores"][name] for attempt in attempts)
        for name in dimensions
    }
    return {
        **base,
        "passed": quality_passed == expected_pass,
        "expected_quality_pass": expected_pass,
        "quality_passed": quality_passed,
        "quality_pass_votes": quality_votes,
        "attempt_count": len(attempts),
        "aggregate": "strict-majority quality verdict; median scores for reporting; ties fail quality",
        "median_total": statistics.median(attempt["total"] for attempt in attempts),
        "median_scores": aggregate_scores,
        "duration_seconds": round(sum(attempt["duration_seconds"] for attempt in attempts), 3),
    }


def run_case(
    case: dict[str, Any],
    rubric: dict[str, Any],
    prompt: str,
    answer: str,
    schema: Path,
    timeout: int,
    model: str | None,
    *,
    repeat: int,
    boundary_repeat: int,
    boundary_margin: int,
    config_overrides: list[str] | None = None,
    reasoning_effort: str = REASONING_EFFORT,
    executor=subprocess.run,
    timeout_provider: Callable[[], int] | None = None,
    before_attempt: Callable[[], None] | None = None,
) -> dict[str, Any]:
    def attempt() -> dict[str, Any]:
        if before_attempt:
            before_attempt()
        effective_timeout = timeout_provider() if timeout_provider else timeout
        return judge_attempt(
            case,
            rubric,
            prompt,
            answer,
            schema,
            effective_timeout,
            model,
            config_overrides=config_overrides,
            reasoning_effort=reasoning_effort,
            executor=executor,
        )

    attempts = [attempt() for _ in range(repeat)]
    if repeat == 1 and boundary_repeat and is_boundary(attempts[0], rubric, boundary_margin):
        attempts.extend(attempt() for _ in range(boundary_repeat))
    return aggregate_case(case, attempts)


def self_test() -> None:
    rubric = json.loads(DEFAULT_RUBRIC.read_text(encoding="utf-8"))
    cases, _ = load_contract(DEFAULT_CASES, DEFAULT_RUBRIC)
    positive_domains = {case["domain"] for case in cases if case.get("expected_pass", True)}
    if positive_domains != set(rubric["domain_emphasis"]):
        raise AssertionError("fixed Judge positive fixtures must cover every rubric domain")
    schema = DEFAULT_SCHEMA
    case = {"id": "fake", "domain": "growth", "expected_pass": True}
    scores = {name: 4 for name in rubric["dimensions"]}
    payload = json.dumps({"scores": scores, "hard_failures": [], "summary": "fake"})
    def high_executor(command, **kwargs):
        if 'model_reasoning_effort="high"' not in command:
            raise AssertionError("requested high effort must reach Codex argv")
        return fake_codex_executor(payload)(command, **kwargs)

    result = run_case(
        case,
        rubric,
        "prompt",
        "answer",
        schema,
        1,
        None,
        repeat=1,
        boundary_repeat=0,
        boundary_margin=1,
        reasoning_effort="high",
        executor=high_executor,
    )
    if not result["passed"] or result["attempt_count"] != 1:
        raise AssertionError(f"fake judge result should pass once: {result}")
    attempt_starts: list[int] = []
    repeated = run_case(
        case,
        rubric,
        "prompt",
        "answer",
        schema,
        1,
        None,
        repeat=2,
        boundary_repeat=0,
        boundary_margin=1,
        executor=fake_codex_executor(payload),
        before_attempt=lambda: attempt_starts.append(len(attempt_starts) + 1),
    )
    if repeated["attempt_count"] != 2 or attempt_starts != [1, 2]:
        raise AssertionError("before_attempt must run once for every judge model call")
    tie = aggregate_case(
        case,
        [
            {"ok": True, "quality_passed": True, "scores": scores, "total": 24, "duration_seconds": 0},
            {"ok": True, "quality_passed": False, "scores": scores, "total": 24, "duration_seconds": 0},
        ],
    )
    if tie["quality_passed"] or tie["passed"]:
        raise AssertionError(f"an even quality tie must fail closed: {tie}")
    boundary_scores = dict(scores)
    boundary_scores[next(iter(boundary_scores))] = 1
    boundary_payload = json.dumps(
        {"scores": boundary_scores, "hard_failures": [], "summary": "boundary"}
    )
    boundary = run_case(
        case,
        rubric,
        "prompt",
        "answer",
        schema,
        1,
        None,
        repeat=1,
        boundary_repeat=1,
        boundary_margin=1,
        executor=fake_codex_executor(boundary_payload),
    )
    if boundary["attempt_count"] != 2:
        raise AssertionError(f"boundary policy should add exactly one attempt: {boundary}")
    with tempfile.TemporaryDirectory(prefix="judge-self-test-") as temp:
        answer_root = validate_real_directory(Path(temp))
        answer = answer_root / "fake.txt"
        answer.write_text("fake", encoding="utf-8")
        if resolve_answer({"id": "dynamic", "answer_id": "fake"}, answer_root) != answer.resolve():
            raise AssertionError("dynamic answer resolver self-test failed")
        for unsafe_id in ("../outside", "/tmp/absolute", "a/b", "Upper Case"):
            try:
                resolve_answer({"id": "dynamic", "answer_id": unsafe_id}, answer_root)
            except ValueError:
                pass
            else:
                raise AssertionError(f"unsafe dynamic answer id must fail: {unsafe_id}")

        outside = answer_root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        linked_dir = answer_root / "linked-dir"
        linked_dir.symlink_to(answer_root, target_is_directory=True)
        try:
            resolve_answer({"id": "dynamic", "answer_id": "fake"}, linked_dir)
        except ValueError:
            pass
        else:
            raise AssertionError("dynamic answers directory with a symlink ancestor must fail")

    for configured in ("/tmp/absolute.txt", "eval/../outside.txt", "../outside.txt"):
        try:
            resolve_answer({"id": "configured", "answer": configured}, None)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe configured answer path must fail: {configured}")

    eval_root = ROOT / "eval"
    with tempfile.TemporaryDirectory(prefix="judge-path-self-test-", dir=eval_root) as temp:
        answer_root = validate_real_directory(Path(temp))
        external = Path(tempfile.mkdtemp(prefix="judge-external-self-test-"))
        try:
            external_answer = external / "outside.txt"
            external_answer.write_text("outside", encoding="utf-8")
            linked_answer = answer_root / "linked.txt"
            linked_answer.symlink_to(external_answer)
            configured = linked_answer.relative_to(ROOT).as_posix()
            try:
                resolve_answer({"id": "configured", "answer": configured}, None)
            except ValueError:
                pass
            else:
                raise AssertionError("configured answer symlink escaping eval must fail")
        finally:
            external_answer.unlink(missing_ok=True)
            external.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Exit codes: 0 passed, 1 quality mismatch, 2 setup or runtime failure.",
    )
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--rubric", default=str(DEFAULT_RUBRIC))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--prompt-cases", action="append", default=[])
    parser.add_argument("--answers-dir")
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--boundary-repeat", type=int, default=0)
    parser.add_argument("--boundary-margin", type=int, default=1)
    parser.add_argument("--max-model-calls", type=int)
    parser.add_argument("--model")
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high", "xhigh"), default=REASONING_EFFORT)
    parser.add_argument("--codex-config", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print("structured judge runner self-test passed")
            return 0
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        if args.repeat < 1 or args.boundary_repeat < 0 or args.boundary_margin < 0:
            raise ValueError("repeat must be >= 1; boundary controls must be >= 0")
        if args.repeat > 1 and args.boundary_repeat:
            raise ValueError("use either explicit --repeat or --boundary-repeat, not both")
        codex_config = validate_codex_config_overrides(args.codex_config)
        cases_path = Path(args.cases).expanduser().resolve()
        rubric_path = Path(args.rubric).expanduser().resolve()
        schema = Path(args.schema).expanduser().resolve()
        cases, rubric = load_contract(cases_path, rubric_path)
        chosen = select_cases(cases, args.case_id)
        json.loads(schema.read_text(encoding="utf-8"))
        prompts = load_prompt_catalogs(
            [Path(value).expanduser().resolve() for value in args.prompt_cases]
        )
        answers_dir = Path(args.answers_dir).expanduser().absolute() if args.answers_dir else None
        resolved = [
            (case, resolve_prompt(case, prompts), resolve_answer(case, answers_dir)) for case in chosen
        ]
        maximum_calls = len(chosen) * (args.repeat + args.boundary_repeat)
        if args.max_model_calls is not None and maximum_calls > args.max_model_calls:
            raise ValueError(
                f"judge worst-case model calls {maximum_calls} exceed budget {args.max_model_calls}"
            )
        if args.validate_only:
            print(f"structured judge contract passed: {len(chosen)} selected / {len(cases)} total cases")
            return 0
        started = time.monotonic()
        results = [
            run_case(
                case,
                rubric,
                prompt,
                answer_path.read_text(encoding="utf-8"),
                schema,
                args.timeout,
                args.model,
                repeat=args.repeat,
                boundary_repeat=args.boundary_repeat,
                boundary_margin=args.boundary_margin,
                config_overrides=codex_config,
                reasoning_effort=args.reasoning_effort,
            )
            for case, prompt, answer_path in resolved
        ]
        answer_inputs = {f"answer:{case['id']}": answer for case, _, answer in resolved}
        summary = {
            "metadata": build_evidence_metadata(
                "structured-judge",
                {
                    "manifest": ROOT / "skill-pack.json",
                    "cases": cases_path,
                    "rubric": rubric_path,
                    "schema": schema,
                    **answer_inputs,
                },
                include_codex=True,
                requested_model=args.model,
                reasoning_effort=args.reasoning_effort,
                extra={
                    "selected_case_ids": [case["id"] for case in chosen],
                    "answer_source": str(answers_dir) if answers_dir else "case-configured paths",
                    "repeat_policy": {
                        "repeat": args.repeat,
                        "boundary_repeat": args.boundary_repeat,
                        "boundary_margin": args.boundary_margin,
                        "aggregate": "strict majority; ties fail quality",
                    },
                    "codex_config_override_keys": [
                        value.split("=", 1)[0] for value in codex_config
                    ],
                    "codex_config_overrides_sha256": sha256_text(
                        json.dumps(codex_config, ensure_ascii=True, separators=(",", ":"))
                    ),
                },
            ),
            "passed": all(result["passed"] for result in results),
            "cases": len(results),
            "failed": [result["id"] for result in results if not result["passed"]],
            "duration_seconds": round(time.monotonic() - started, 3),
            "model_calls": sum(len(result["attempts"]) for result in results),
            "results": results,
        }
        rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        if args.output:
            output = Path(args.output).expanduser().resolve()
            write_private_text(output, rendered + "\n")
            print(f"structured judge artifact: {output}")
        print(json.dumps({key: summary[key] for key in ("passed", "cases", "failed", "model_calls")}, ensure_ascii=False))
        if any("error" in result for result in results):
            return 2
        return 0 if summary["passed"] else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"run_structured_judge error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
