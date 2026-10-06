from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ...repo import REPO_ROOT
from .gates import gate_runner
from .model import MaturityContext, MaturityGateResult
from .profiles import load_profile


SERIAL_GATE_IDS = frozenset({"performance_regression"})


def _evaluate_gate(
    gate_id: str, context: MaturityContext
) -> MaturityGateResult:
    try:
        return gate_runner(gate_id)(context)
    except Exception as exc:
        return MaturityGateResult(
            gate_id=gate_id,
            status="failed",
            duration_ms=0.0,
            evidence={},
            error=f"unhandled gate error: {exc}",
        )


def evaluate_maturity(
    profile_name: str,
    *,
    phase: str = "candidate",
    baseline_path: Path | None = None,
    benchmark_result_path: Path | None = None,
    benchmark_observation_path: Path | None = None,
    jobs: int = 0,
    root: Path = REPO_ROOT,
) -> dict[str, object]:
    profile = load_profile(profile_name, phase)
    context = MaturityContext(
        root=root,
        profile=profile_name,
        phase=phase,
        baseline_path=baseline_path,
        benchmark_result_path=benchmark_result_path,
        benchmark_observation_path=benchmark_observation_path,
    )
    worker_count = jobs if jobs > 0 else min(4, os.cpu_count() or 2)
    results: dict[str, MaturityGateResult] = {}
    parallel_gate_ids = tuple(
        gate_id
        for gate_id in profile.required_gate_ids
        if gate_id not in SERIAL_GATE_IDS
    )
    with ThreadPoolExecutor(max_workers=max(1, worker_count)) as executor:
        futures = {
            executor.submit(_evaluate_gate, gate_id, context): gate_id
            for gate_id in parallel_gate_ids
        }
        for future in as_completed(futures):
            gate_id = futures[future]
            results[gate_id] = future.result()
    for gate_id in profile.required_gate_ids:
        if gate_id in SERIAL_GATE_IDS:
            results[gate_id] = _evaluate_gate(gate_id, context)
    ordered = [results[gate_id] for gate_id in profile.required_gate_ids]
    failed = [result.gate_id for result in ordered if not result.passed]
    return {
        "profile": profile,
        "results": ordered,
        "failed_gate_ids": failed,
        "ok": not failed,
    }
