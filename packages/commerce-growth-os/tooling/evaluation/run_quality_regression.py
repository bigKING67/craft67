#!/usr/bin/env python3
"""Run bounded selection, explicit execution, and semantic-judge quality layers."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable


sys.dont_write_bytecode = True

import run_execution_eval as execution
import run_forward_routing_eval as routing
import run_structured_judge as judge
from evidence_metadata import build_evidence_metadata
from live_runtime import (
    create_private_run_directory,
    ensure_private_directory,
    load_manifest,
    sha256_text,
    validate_codex_config_overrides,
    verify_active_install,
    write_private_text,
)
from tooling.installation.tree_integrity import TreeIntegrityError, validate_real_directory


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = ROOT / "eval/answers/quality-regression"
LAYERS = ("selection", "execution", "judge", "calibration")
DEFAULT_MAX_MODEL_CALLS = 50


class ModelCallPacer:
    """Apply an inter-call delay before every model call except the first."""

    def __init__(
        self,
        delay_seconds: float,
        max_total_seconds: float,
        started: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.max_total_seconds = max_total_seconds
        self.started = started
        self.clock = clock
        self.sleeper = sleeper
        self.calls_started = 0

    def before_call(self) -> None:
        required_delay = self.delay_seconds if self.calls_started else 0.0
        remaining = self.max_total_seconds - (self.clock() - self.started)
        if remaining <= required_delay:
            raise TimeoutError("max-total-seconds exhausted during inter-call pacing")
        if required_delay:
            self.sleeper(required_delay)
        self.calls_started += 1


def filter_known_cases(
    cases: list[dict[str, Any]], requested: list[str]
) -> list[dict[str, Any]]:
    if not requested:
        return cases
    requested_set = set(requested)
    return [case for case in cases if case["id"] in requested_set]


def planned_model_calls(
    selection_count: int,
    execution_count: int,
    judge_count: int,
    calibration_count: int = 0,
    *,
    repeat: int,
    boundary_repeat: int,
) -> int:
    return selection_count + execution_count + (judge_count + calibration_count) * (
        repeat + boundary_repeat
    )


def prepare_output_path(output_dir: Path, requested: str | None) -> Path:
    if requested:
        requested_output = Path(requested).expanduser()
        try:
            parent = validate_real_directory(requested_output.absolute().parent)
        except TreeIntegrityError as exc:
            raise ValueError(f"quality output parent must be a real directory: {exc}") from exc
        output = parent / requested_output.name
        if output.parent != output_dir:
            raise ValueError("--output must be a direct child of the private quality --output-dir")
    else:
        output = output_dir / "quality-regression.json"
    if output.name in {"checkpoint.json", ".quality-regression.lock", "answers"}:
        raise ValueError("--output conflicts with a reserved quality artifact path")
    if os.path.lexists(output):
        raise ValueError("quality output must not already exist")
    return output


def self_test() -> None:
    from contextlib import redirect_stderr, redirect_stdout
    from io import StringIO
    from unittest.mock import patch

    with tempfile.TemporaryDirectory(prefix="quality-preflight-test-") as temp:
        root = Path(temp).resolve()
        for index, name in enumerate(("checkpoint.json", ".quality-regression.lock", "answers", "../outside.json", "commercial_budget_decision.txt")):
            run = root / f"run-{index}"
            argv = ["quality", "--layer", "execution", "--case-id", "commercial_budget_decision",
                    "--output-dir", str(run), "--output", str(run / name)]
            if name == "commercial_budget_decision.txt":
                argv.extend(["--answer-dir", str(run)])
            with patch.object(sys, "argv", argv), patch(__name__ + ".verify_active_install", return_value={}), \
                 patch.object(execution, "run_case") as model_call, redirect_stderr(StringIO()):
                status = main()
            if status != 2 or model_call.called:
                raise AssertionError(f"invalid output must fail before any model call: {name}")

    # Exercise the real orchestration path with fake transports, including both
    # generated-answer Judge and negative calibration. No provider calls occur.
    import evidence_metadata
    from live_runtime import fake_codex_executor
    original_routing, original_execution, original_judge = routing.run_case, execution.run_case, judge.run_case
    original_command_value = evidence_metadata.command_value
    observed = []

    def fake_command_value(command):
        # Keep real Git provenance and input hashing, but do not require a
        # locally installed Codex CLI for this fake-transport self-test.
        if command == ["codex", "--version"]:
            return "codex fake-self-test"
        return original_command_value(command)

    def fake_routing(case, *args, **kwargs):
        observed.append(("selection", kwargs.get("reasoning_effort")))
        payload = json.dumps({"selected_skills": case["expected"], "reason": "fake"})
        return original_routing(case, *args, **kwargs, executor=fake_codex_executor(payload))

    def fake_execution(case, **kwargs):
        observed.append(("execution", kwargs.get("reasoning_effort")))
        return original_execution(case, **kwargs, executor=fake_codex_executor("fake generated answer"))

    def fake_judge(case, rubric, *args, **kwargs):
        observed.append(("calibration" if case.get("expected_pass") is False else "judge", kwargs.get("reasoning_effort")))
        score = 0 if case.get("expected_pass") is False else 4
        payload = json.dumps({"scores": {name: score for name in rubric["dimensions"]}, "hard_failures": [], "summary": "fake"})
        return original_judge(case, rubric, *args, **kwargs, executor=fake_codex_executor(payload))

    with tempfile.TemporaryDirectory(prefix="quality-effort-test-") as temp:
        argv = ["quality", "--reasoning-effort", "high", "--output-dir", str(Path(temp) / "run")]
        with patch.object(sys, "argv", argv), patch(__name__ + ".verify_active_install", return_value={}), \
             patch.object(evidence_metadata, "command_value", side_effect=fake_command_value), \
             patch.object(routing, "run_case", side_effect=fake_routing), \
             patch.object(execution, "run_case", side_effect=fake_execution), \
             patch.object(judge, "run_case", side_effect=fake_judge), redirect_stdout(StringIO()):
            status = main()
        report = json.loads((Path(temp) / "run/quality-regression.json").read_text())
        if status != 0 or len(observed) != 50 or any(effort != "high" for _, effort in observed):
            raise AssertionError(f"full orchestration effort propagation failed: {status}, {observed}")
        if {layer for layer, _ in observed} != set(LAYERS) or report["metadata"]["reasoning_effort"] != "high":
            raise AssertionError("all layer requests and metadata must preserve high effort")
        if report["metadata"]["codex_version"] != "codex fake-self-test":
            raise AssertionError("fake orchestration must not query a real Codex CLI version")

    safe_provider_config = [
        'model_provider="local"',
        'model_providers.local.name="local"',
        'model_providers.local.base_url="http://127.0.0.1:8317/v1"',
        'model_providers.local.wire_api="responses"',
        "model_providers.local.requires_openai_auth=true",
    ]
    if validate_codex_config_overrides(safe_provider_config) != safe_provider_config:
        raise AssertionError("safe isolated provider overrides changed during validation")
    for unsafe_override in (
        'openai_api_key="secret"',
        'model_providers.local.base_url="http://user:pass@127.0.0.1/v1"',
        'model_provider="local"=extra',
    ):
        try:
            validate_codex_config_overrides([unsafe_override])
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe isolated provider override must fail: {unsafe_override}")

    selection_count = len(routing.load_cases(routing.DEFAULT_CASES, []))
    execution_count = len(execution.load_cases(execution.DEFAULT_CASES, []))
    calibration_count = len(
        [
            case
            for case in judge.load_contract(judge.DEFAULT_CASES, judge.DEFAULT_RUBRIC)[0]
            if case.get("expected_pass") is False
        ]
    )
    calls = planned_model_calls(
        selection_count,
        execution_count,
        execution_count,
        calibration_count,
        repeat=1,
        boundary_repeat=0,
    )
    if (selection_count, execution_count, calibration_count, calls) != (22, 9, 10, 50):
        raise AssertionError(
            "fixture-derived full plan must remain 22 selection / 9 execution / "
            f"9 judge / 10 calibration / 50 calls, got "
            f"{selection_count}/{execution_count}/{execution_count}/{calibration_count}/{calls}"
        )
    if calls > DEFAULT_MAX_MODEL_CALLS:
        raise AssertionError(f"fixture-derived default plan exceeds budget {DEFAULT_MAX_MODEL_CALLS}")
    cases = [{"id": "a"}, {"id": "b"}]
    if filter_known_cases(cases, ["b"]) != [{"id": "b"}]:
        raise AssertionError("case selection self-test failed")
    bounded = planned_model_calls(1, 1, 1, 1, repeat=1, boundary_repeat=1)
    if bounded != 6:
        raise AssertionError(f"boundary worst-case budget should be explicit, got {bounded}")

    fake_time = [0.0]
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        fake_time[0] += seconds

    pacer = ModelCallPacer(
        2.0,
        30.0,
        0.0,
        clock=lambda: fake_time[0],
        sleeper=fake_sleep,
    )
    for _ in range(3):
        pacer.before_call()
    if pacer.calls_started != 3 or sleeps != [2.0, 2.0]:
        raise AssertionError(f"pacing must apply exactly between model calls: {pacer.calls_started}, {sleeps}")
    tight = ModelCallPacer(2.0, 2.0, 0.0, clock=lambda: 0.0, sleeper=fake_sleep)
    tight.before_call()
    try:
        tight.before_call()
    except TimeoutError:
        pass
    else:
        raise AssertionError("pacing must fail before sleeping past the total-time budget")

    with tempfile.TemporaryDirectory(prefix="quality-artifact-self-test-") as temp:
        root = Path(temp).resolve()
        run_id, run = create_private_run_directory(root / "runs")
        if not run_id.startswith("run-"):
            raise AssertionError(f"unexpected generated run id: {run_id}")
        for bad in (root / "outside.json", run / "checkpoint.json", run / ".quality-regression.lock", run / "answers"):
            try:
                prepare_output_path(run, str(bad))
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid output must fail preflight: {bad}")
        if prepare_output_path(run, None) != run / "quality-regression.json":
            raise AssertionError("default output path changed")
        artifact = run / "artifact.json"
        write_private_text(artifact, "{}\n", overwrite=False)
        try:
            prepare_output_path(run, str(artifact))
        except ValueError:
            pass
        else:
            raise AssertionError("existing output must fail preflight")
        if os.name != "nt":
            if run.stat().st_mode & 0o777 != 0o700:
                raise AssertionError("quality run directory must be mode 0700")
            if artifact.stat().st_mode & 0o777 != 0o600:
                raise AssertionError("quality artifact must be mode 0600")
        try:
            write_private_text(artifact, "overwritten\n", overwrite=False)
        except ValueError:
            pass
        else:
            raise AssertionError("quality answer/artifact overwrite must fail closed")

        nonempty = ensure_private_directory(root / "nonempty")
        write_private_text(nonempty / "existing.txt", "existing\n")
        try:
            ensure_private_directory(nonempty, require_empty=True)
        except ValueError:
            pass
        else:
            raise AssertionError("explicit non-empty quality run directory must fail")

        if os.name != "nt":
            real_parent = ensure_private_directory(root / "real-parent")
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            try:
                ensure_private_directory(linked_parent / "escaped-child")
            except ValueError:
                pass
            else:
                raise AssertionError("quality directory with a symlink ancestor must fail")
            if (real_parent / "escaped-child").exists():
                raise AssertionError("symlink-ancestor rejection must happen before creating descendants")

            regular_target = run / "regular-target.txt"
            write_private_text(regular_target, "target\n")
            linked_target = run / "linked-target.txt"
            linked_target.symlink_to(regular_target)
            try:
                write_private_text(linked_target, "replacement\n")
            except ValueError:
                pass
            else:
                raise AssertionError("private writer must reject an existing symlink target")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Exit codes: 0 passed, 1 quality mismatch, 2 setup or runtime failure.",
    )
    parser.add_argument("--layer", action="append", choices=LAYERS, default=[])
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--selection-cases", default=str(routing.DEFAULT_CASES))
    parser.add_argument("--execution-cases", default=str(execution.DEFAULT_CASES))
    parser.add_argument("--judge-rubric", default=str(judge.DEFAULT_RUBRIC))
    parser.add_argument("--judge-schema", default=str(judge.DEFAULT_SCHEMA))
    parser.add_argument("--calibration-cases", default=str(judge.DEFAULT_CASES))
    parser.add_argument("--answer-dir")
    parser.add_argument(
        "--output-dir",
        help="New empty run directory; omitted creates a unique private directory under eval/answers",
    )
    parser.add_argument("--output")
    parser.add_argument("--install-root")
    parser.add_argument("--model")
    parser.add_argument("--reasoning-effort", choices=["low", "medium", "high", "xhigh"], default="medium")
    parser.add_argument("--selection-model")
    parser.add_argument("--execution-model")
    parser.add_argument("--execution-backend", choices=["exec", "app-server"], default="exec")
    parser.add_argument("--judge-model")
    parser.add_argument("--codex-config", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--boundary-repeat", type=int, default=0)
    parser.add_argument("--boundary-margin", type=int, default=1)
    parser.add_argument("--max-model-calls", type=int, default=DEFAULT_MAX_MODEL_CALLS)
    parser.add_argument("--max-total-seconds", type=int, default=3600)
    parser.add_argument("--inter-call-delay", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print("quality regression orchestrator self-test passed")
            return 0
        layers = args.layer or (list(LAYERS[:3]) if args.case_id else list(LAYERS))
        if args.repeat < 1 or args.boundary_repeat < 0 or args.boundary_margin < 0:
            raise ValueError("repeat must be >= 1; boundary controls must be >= 0")
        if args.repeat > 1 and args.boundary_repeat:
            raise ValueError("use either explicit --repeat or --boundary-repeat, not both")
        if args.max_model_calls < 0 or args.max_total_seconds <= 0 or args.timeout <= 0:
            raise ValueError("budgets and timeout must be positive")
        if args.inter_call_delay < 0 or args.inter_call_delay > 60:
            raise ValueError("inter-call-delay must be between 0 and 60 seconds")
        codex_config = validate_codex_config_overrides(args.codex_config)

        selection_path = Path(args.selection_cases).expanduser().resolve()
        execution_path = Path(args.execution_cases).expanduser().resolve()
        rubric_path = Path(args.judge_rubric).expanduser().resolve()
        schema_path = Path(args.judge_schema).expanduser().resolve()
        calibration_path = Path(args.calibration_cases).expanduser().resolve()
        selection_model = args.selection_model or args.model
        execution_model = args.execution_model or args.model
        judge_model = args.judge_model or args.model
        if "execution" in layers and args.execution_backend == "app-server" and not execution_model:
            raise ValueError("App Server execution requires an explicit model")
        selection_all = routing.load_cases(selection_path, [])
        execution_all = execution.load_cases(execution_path, [])
        selection_cases = filter_known_cases(selection_all, args.case_id)
        execution_cases = filter_known_cases(execution_all, args.case_id)
        if args.case_id:
            active_ids = set()
            if "selection" in layers:
                active_ids.update(case["id"] for case in selection_all)
            if "execution" in layers or "judge" in layers:
                active_ids.update(case["id"] for case in execution_all)
            missing = sorted(set(args.case_id) - active_ids)
            if missing:
                raise ValueError(f"unknown quality-regression cases for selected layers: {', '.join(missing)}")

        judge_cases: list[dict[str, Any]] = []
        calibration_cases: list[dict[str, Any]] = []
        rubric: dict[str, Any] | None = None
        if "judge" in layers or "calibration" in layers:
            _, rubric = judge.load_contract(execution_path, rubric_path)
            json.loads(schema_path.read_text(encoding="utf-8"))
        if "judge" in layers:
            judge_cases = execution_cases
        if "calibration" in layers:
            calibration_all, _ = judge.load_contract(calibration_path, rubric_path)
            calibration_cases = [
                case for case in calibration_all if case.get("expected_pass") is False
            ]
            if not calibration_cases:
                raise ValueError("calibration suite must contain expected-fail cases")
        call_plan = planned_model_calls(
            len(selection_cases) if "selection" in layers else 0,
            len(execution_cases) if "execution" in layers else 0,
            len(judge_cases) if "judge" in layers else 0,
            len(calibration_cases) if "calibration" in layers else 0,
            repeat=args.repeat,
            boundary_repeat=args.boundary_repeat,
        )
        if call_plan > args.max_model_calls:
            raise ValueError(
                f"worst-case model calls {call_plan} exceed budget {args.max_model_calls}"
            )

        manifest = load_manifest()
        if "selection" in layers:
            skill_names = [skill["name"] for skill in manifest["skills"]]
        else:
            skill_names = sorted({case["skill"] for case in execution_cases})
        active_install = verify_active_install(
            install_root=Path(args.install_root) if args.install_root else None,
            skill_names=skill_names,
        )
        plan = {
            "layers": layers,
            "execution_backend": args.execution_backend,
            "selected_case_ids": {
                "selection": [case["id"] for case in selection_cases] if "selection" in layers else [],
                "execution": [case["id"] for case in execution_cases] if "execution" in layers else [],
                "judge": [case["id"] for case in judge_cases],
                "calibration": [case["id"] for case in calibration_cases],
            },
            "worst_case_model_calls": call_plan,
            "max_model_calls": args.max_model_calls,
            "max_total_seconds": args.max_total_seconds,
            "repeat": args.repeat,
            "boundary_repeat": args.boundary_repeat,
            "inter_call_delay_seconds": args.inter_call_delay,
            "reasoning_effort": args.reasoning_effort,
            "models": {
                "selection": selection_model,
                "execution": execution_model,
                "judge": judge_model,
            },
            "codex_config_override_keys": [
                value.split("=", 1)[0] for value in codex_config
            ],
            "codex_config_overrides_sha256": sha256_text(
                json.dumps(codex_config, ensure_ascii=True, separators=(",", ":"))
            ),
            "active_install": active_install,
        }
        if args.dry_run:
            print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
            return 0

        if args.output_dir:
            output_dir = ensure_private_directory(
                Path(args.output_dir).expanduser(),
                require_empty=True,
            )
            run_id = f"explicit-{secrets.token_hex(8)}"
        else:
            run_id, output_dir = create_private_run_directory(DEFAULT_OUTPUT_ROOT)
        if args.answer_dir:
            answer_dir = ensure_private_directory(
                Path(args.answer_dir).expanduser(),
                require_empty="execution" in layers,
            )
        else:
            answer_dir = ensure_private_directory(output_dir / "answers")
        output = prepare_output_path(output_dir, args.output)
        if "execution" in layers and output in {
            answer_dir / f"{case['id']}.txt" for case in execution_cases
        }:
            raise ValueError("--output conflicts with a planned generated answer")
        lock_path = output_dir / ".quality-regression.lock"
        write_private_text(lock_path, run_id + "\n", overwrite=False)
        started = time.monotonic()
        pacer = ModelCallPacer(
            args.inter_call_delay,
            args.max_total_seconds,
            started,
        )
        calls_used = 0
        selection_results: list[dict[str, Any]] = []
        execution_results: list[dict[str, Any]] = []
        judge_results: list[dict[str, Any]] = []
        calibration_results: list[dict[str, Any]] = []
        checkpoint_path = output_dir / "checkpoint.json"

        def checkpoint(stage: str, status: str = "running") -> None:
            payload = {
                "schema_version": 1,
                "run_id": run_id,
                "status": status,
                "stage": stage,
                "plan": plan,
                "model_calls": calls_used,
                "duration_seconds": round(time.monotonic() - started, 3),
                "selection": selection_results,
                "execution": execution_results,
                "judge": judge_results,
                "calibration": calibration_results,
            }
            write_private_text(
                checkpoint_path,
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )

        checkpoint("initialized")

        def remaining_timeout() -> int:
            remaining = args.max_total_seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise TimeoutError("max-total-seconds exhausted before next model call")
            return max(1, min(args.timeout, int(remaining)))

        if "selection" in layers:
            for case in selection_cases:
                pacer.before_call()
                selection_results.append(
                    routing.run_case(
                        case,
                        routing.DEFAULT_SCHEMA,
                        selection_model,
                        remaining_timeout(),
                        config_overrides=codex_config,
                        reasoning_effort=args.reasoning_effort,
                    )
                )
                calls_used += 1
                checkpoint(f"selection:{case['id']}")

        if "execution" in layers:
            for case in execution_cases:
                pacer.before_call()
                result = execution.run_case(
                    case,
                    model=execution_model,
                    timeout=remaining_timeout(),
                    config_overrides=codex_config,
                    reasoning_effort=args.reasoning_effort,
                    backend=args.execution_backend,
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
                execution_results.append(result)
                checkpoint(f"execution:{case['id']}")

        generated_ids = {
            result["id"] for result in execution_results if result.get("generated")
        }
        if "judge" in layers:
            assert rubric is not None
            for case in judge_cases:
                answer_path = answer_dir / f"{case['id']}.txt"
                generated_in_this_run = "execution" not in layers or case["id"] in generated_ids
                if not generated_in_this_run or not answer_path.is_file():
                    judge_results.append(
                        {
                            "id": case["id"],
                            "domain": case["domain"],
                            "passed": False,
                            "error": f"missing generated answer: {answer_path}",
                            "attempts": [],
                        }
                    )
                    checkpoint(f"judge:{case['id']}")
                    continue
                answer_path = judge.resolve_answer({"id": case["id"]}, answer_dir)
                result = judge.run_case(
                    case,
                    rubric,
                    case["prompt"],
                    answer_path.read_text(encoding="utf-8"),
                    schema_path,
                    args.timeout,
                    judge_model,
                    repeat=args.repeat,
                    boundary_repeat=args.boundary_repeat,
                    boundary_margin=args.boundary_margin,
                    config_overrides=codex_config,
                    reasoning_effort=args.reasoning_effort,
                    timeout_provider=remaining_timeout,
                    before_attempt=pacer.before_call,
                )
                calls_used += len(result["attempts"])
                judge_results.append(result)
                checkpoint(f"judge:{case['id']}")

        if "calibration" in layers:
            assert rubric is not None
            prompt_catalog = judge.load_prompt_catalogs()
            for case in calibration_cases:
                answer_path = judge.resolve_answer(case, None)
                result = judge.run_case(
                    case,
                    rubric,
                    judge.resolve_prompt(case, prompt_catalog),
                    answer_path.read_text(encoding="utf-8"),
                    schema_path,
                    args.timeout,
                    judge_model,
                    repeat=args.repeat,
                    boundary_repeat=args.boundary_repeat,
                    boundary_margin=args.boundary_margin,
                    config_overrides=codex_config,
                    reasoning_effort=args.reasoning_effort,
                    timeout_provider=remaining_timeout,
                    before_attempt=pacer.before_call,
                )
                calls_used += len(result["attempts"])
                calibration_results.append(result)
                checkpoint(f"calibration:{case['id']}")

        if pacer.calls_started != calls_used:
            raise ValueError(
                f"model-call pacing count {pacer.calls_started} does not match executed calls {calls_used}"
            )

        evidence_answer_ids = (
            {case["id"] for case in judge_cases}
            if "execution" not in layers
            else generated_ids
        )
        answer_inputs = {
            f"answer:{case['id']}": answer_dir / f"{case['id']}.txt"
            for case in judge_cases
            if case["id"] in evidence_answer_ids
            and (answer_dir / f"{case['id']}.txt").is_file()
        }
        calibration_answer_inputs = {
            f"calibration_answer:{case['id']}": judge.resolve_answer(case, None)
            for case in calibration_cases
        }
        runtime_errors = [
            result
            for result in [
                *selection_results,
                *execution_results,
                *judge_results,
                *calibration_results,
            ]
            if "error" in result
        ]
        quality_failures = [
            result["id"]
            for result in selection_results
            if not result.get("passed") and "error" not in result
        ] + [
            result["id"]
            for result in judge_results
            if not result.get("passed") and "error" not in result
        ] + [
            result["id"]
            for result in calibration_results
            if not result.get("passed") and "error" not in result
        ]
        summary = {
            "schema_version": 1,
            "run_id": run_id,
            "metadata": build_evidence_metadata(
                "quality-regression",
                {
                    "manifest": ROOT / "skill-pack.json",
                    "selection_cases": selection_path,
                    "execution_cases": execution_path,
                    "judge_rubric": rubric_path,
                    "judge_schema": schema_path,
                    "judge_calibration_cases": calibration_path,
                    "judge_prompt_commerce": ROOT / "eval/cases.json",
                    "judge_prompt_marketing": ROOT / "eval/marketing/cases.json",
                    **answer_inputs,
                    **calibration_answer_inputs,
                },
                include_codex=True,
                requested_model=args.model,
                reasoning_effort=args.reasoning_effort,
                extra={"plan": plan, "actual_model_calls": calls_used, "run_id": run_id},
            ),
            "passed": not runtime_errors and not quality_failures,
            "model_calls": calls_used,
            "duration_seconds": round(time.monotonic() - started, 3),
            "runtime_errors": [result["id"] for result in runtime_errors],
            "quality_failures": quality_failures,
            "selection": selection_results,
            "execution": execution_results,
            "judge": judge_results,
            "calibration": calibration_results,
        }
        write_private_text(
            output,
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            overwrite=False,
        )
        checkpoint("completed", "passed" if summary["passed"] else "failed")
        lock_path.unlink()
        print(f"quality regression artifact: {output}")
        print(
            json.dumps(
                {
                    key: summary[key]
                    for key in ("passed", "model_calls", "runtime_errors", "quality_failures")
                },
                ensure_ascii=False,
            )
        )
        if runtime_errors:
            return 2
        return 0 if summary["passed"] else 1
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        TimeoutError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(f"run_quality_regression error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
