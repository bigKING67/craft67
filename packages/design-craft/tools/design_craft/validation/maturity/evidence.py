from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

from ...benchmark.contract import compare_results
from ...benchmark.runner import run_suite
from ...release.github_runs import load_observation, workflow_binding
from .execution import command_gate, gate_result
from .model import GateRunner, MaturityContext, MaturityGateResult
from .process_runner import json_payload, run_command


TASKS = (
    "same-prompt-dashboard-review",
    "same-prompt-motion-review",
    "same-prompt-native-adaptive-review",
)


def performance_regression(context: MaturityContext) -> MaturityGateResult:
    started = time.perf_counter()
    path = context.baseline_path
    if path is None or not path.is_file():
        return gate_result(
            "performance_regression",
            False,
            (time.perf_counter() - started) * 1_000,
            {"baseline": str(path) if path else None},
            "benchmark baseline is required and must exist",
        )
    try:
        baseline = json.loads(path.read_text(encoding="utf-8"))
        if baseline.get("scale") != "full":
            return gate_result(
                "performance_regression",
                False,
                (time.perf_counter() - started) * 1_000,
                {"baseline": str(path), "scale": baseline.get("scale")},
                "release benchmark baseline must use the full suite",
            )
        benchmark_path = context.benchmark_result_path
        benchmark_run: dict[str, object] | None = None
        if benchmark_path is None:
            if context.phase == "final":
                return gate_result(
                    "performance_regression",
                    False,
                    (time.perf_counter() - started) * 1_000,
                    {"baseline": str(path)},
                    "final release verification requires a precomputed "
                    "benchmark result",
                )
            current = run_suite(str(baseline.get("scale", "smoke")))
            benchmark_digest = None
        else:
            if benchmark_path.is_symlink() or not benchmark_path.is_file():
                raise ValueError("precomputed benchmark result is missing or unsafe")
            current = json.loads(benchmark_path.read_text(encoding="utf-8"))
            benchmark_digest = hashlib.sha256(
                benchmark_path.read_bytes()
            ).hexdigest()
            head = run_command(["git", "rev-parse", "HEAD"], root=context.root)
            if (
                head.returncode != 0
                or current.get("source_commit") != head.stdout.strip()
            ):
                raise ValueError(
                    "precomputed benchmark result must match current HEAD"
                )
            if current.get("source_dirty") is not False:
                raise ValueError(
                    "precomputed benchmark result must come from a clean source"
                )
        if context.phase == "final":
            observation_path = context.benchmark_observation_path
            if observation_path is None:
                raise ValueError(
                    "final release verification requires a benchmark run observation"
                )
            benchmark_run = load_observation(
                observation_path,
                expected_kind="benchmark",
            )
        comparison = compare_results(baseline, current)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        return gate_result(
            "performance_regression",
            False,
            0,
            {"baseline": str(path)},
            str(exc),
        )
    evidence = {
        "baseline": str(path),
        "runner": current.get("runner"),
        "scale": current.get("scale"),
        "source_commit": current.get("source_commit"),
        "benchmark_result_sha256": benchmark_digest,
        "warnings": comparison.get("warnings", []),
        "comparisons": comparison.get("comparisons", []),
    }
    if benchmark_run is not None:
        evidence["workflow"] = workflow_binding(benchmark_run, kind="benchmark")
    return gate_result(
        "performance_regression",
        comparison.get("ok") is True,
        (time.perf_counter() - started) * 1_000,
        evidence,
        "; ".join(str(item) for item in comparison.get("errors", []))
        or "benchmark regression detected",
    )


def host_current_source(host: str) -> GateRunner:
    gate_id = f"host_{host}_current_source"

    def evaluate(context: MaturityContext) -> MaturityGateResult:
        started = time.perf_counter()
        failures: list[str] = []
        for task in TASKS:
            result = run_command(
                [
                    sys.executable,
                    "scripts/design_craft_cross_agent_validate.py",
                    "--observed-task",
                    f"evals/cross-agent/{task}",
                    "--require-host",
                    host,
                ],
                root=context.root,
                timeout=120,
            )
            if result.returncode != 0:
                failures.append(f"{task}: {result.stderr or result.stdout}")
        return gate_result(
            gate_id,
            not failures,
            (time.perf_counter() - started) * 1_000,
            {
                "host": host,
                "tasks": list(TASKS),
                "schema": "score-v5",
                "identity": "evidence-graph-v2",
            },
            "; ".join(failures),
        )

    return evaluate


def native_current_source(native: str) -> GateRunner:
    gate_id = f"native_{native}_current_source"

    def evaluate(context: MaturityContext) -> MaturityGateResult:
        evidence_root = Path(
            os.environ.get(
                "DESIGN_CRAFT_NATIVE_EVIDENCE_ROOT",
                context.root / "evals/native-runtime",
            )
        ).expanduser().resolve()
        command = [
            sys.executable,
            "scripts/design_craft_native_runtime_validate.py",
            "--validate",
            "--root",
            str(evidence_root),
            "--require-current-source",
            "--json",
        ]
        if native == "ios_simulator":
            command.extend(("--require", "ios"))
        elif native == "android_emulator":
            command.extend(("--require", "android"))
        elif native == "physical_device":
            command.append("--require-real-device")
        else:
            return gate_result(
                gate_id,
                False,
                0,
                {"native": native},
                "unknown native target",
            )
        result = run_command(command, root=context.root, timeout=180)
        payload = json_payload(result)
        evidence_key = {
            "ios_simulator": "ios",
            "android_emulator": "android",
            "physical_device": "real_device",
        }[native]
        evidence_payload = payload.get("evidence")
        record = (
            evidence_payload.get(evidence_key)
            if isinstance(evidence_payload, dict)
            else None
        )
        evidence_path = evidence_root / (
            "real-device-observed.json"
            if native == "physical_device"
            else f"{'ios' if native == 'ios_simulator' else 'android'}-observed.json"
        )
        display_path = str(evidence_path.relative_to(evidence_root))
        record_binding = {
            "native": native,
            "schema": record.get("schema") if isinstance(record, dict) else None,
            "evidence_path": display_path,
            "evidence_sha256": (
                hashlib.sha256(evidence_path.read_bytes()).hexdigest()
                if evidence_path.is_file()
                else None
            ),
            "source_commit": (
                record.get("source_commit") if isinstance(record, dict) else None
            ),
            "platform": (
                record.get("platform") if isinstance(record, dict) else None
            ),
            "runtime_kind": (
                record.get("runtime_kind") if isinstance(record, dict) else None
            ),
            "contract_sha256": (
                record.get("contract_sha256") if isinstance(record, dict) else None
            ),
            "observed_at": (
                record.get("observed_at") if isinstance(record, dict) else None
            ),
            "workflow": (
                record.get("workflow") if isinstance(record, dict) else None
            ),
            "artifacts": (
                record.get("artifacts") if isinstance(record, dict) else None
            ),
        }
        return gate_result(
            gate_id,
            result.returncode == 0 and payload.get("ok") is True,
            result.duration_ms,
            record_binding,
            result.stderr
            or "; ".join(str(item) for item in payload.get("errors", [])),
        )

    return evaluate


def comparative_evaluation(context: MaturityContext) -> MaturityGateResult:
    return command_gate(
        "comparative_evaluation",
        [
            sys.executable,
            "scripts/design_craft_comparative_validate.py",
            "--require-observed",
        ],
        timeout=240,
        evidence={"status": "current_source_required"},
    )(context)
