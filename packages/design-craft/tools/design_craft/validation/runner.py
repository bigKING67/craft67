from __future__ import annotations

import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..repo import REPO_ROOT
from .model import GateResult, GateSpec


SUMMARY_LIMIT = 1_500


def _bounded_summary(value: str) -> str:
    normalized = value.strip()
    if len(normalized) <= SUMMARY_LIMIT:
        return normalized
    return normalized[:SUMMARY_LIMIT] + "\n...[truncated]"


def run_gate(gate: GateSpec, *, root: Path = REPO_ROOT) -> GateResult:
    environment = dict(os.environ)
    environment.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    environment.update(gate.environment)
    started = time.perf_counter()
    try:
        result = subprocess.run(
            list(gate.command),
            cwd=root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=gate.timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = (time.perf_counter() - started) * 1_000
        return GateResult(
            gate_id=gate.gate_id,
            status="failed",
            exit_code=None,
            duration_ms=round(duration_ms, 3),
            stdout_summary=_bounded_summary(exc.stdout or ""),
            stderr_summary=_bounded_summary(exc.stderr or ""),
            error_code="TIMEOUT",
        )
    except OSError as exc:
        duration_ms = (time.perf_counter() - started) * 1_000
        return GateResult(
            gate_id=gate.gate_id,
            status="failed",
            exit_code=None,
            duration_ms=round(duration_ms, 3),
            stdout_summary="",
            stderr_summary=str(exc),
            error_code="SPAWN_FAILED",
        )

    duration_ms = (time.perf_counter() - started) * 1_000
    return GateResult(
        gate_id=gate.gate_id,
        status="passed" if result.returncode == 0 else "failed",
        exit_code=result.returncode,
        duration_ms=round(duration_ms, 3),
        stdout_summary=_bounded_summary(result.stdout),
        stderr_summary=_bounded_summary(result.stderr),
        error_code=None if result.returncode == 0 else "NONZERO_EXIT",
    )


def _automatic_jobs(gate_count: int) -> int:
    cpu_count = os.cpu_count() or 2
    return max(1, min(gate_count, cpu_count, 4))


def run_gates(gates: tuple[GateSpec, ...], *, jobs: int = 0) -> tuple[GateResult, ...]:
    results: dict[str, GateResult] = {}
    parallel = sorted(
        (gate for gate in gates if gate.execution == "parallel"),
        key=lambda gate: -gate.priority,
    )
    serial = [gate for gate in gates if gate.execution == "serial"]

    if parallel:
        worker_count = jobs if jobs > 0 else _automatic_jobs(len(parallel))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {executor.submit(run_gate, gate): gate for gate in parallel}
            for future in as_completed(futures):
                result = future.result()
                results[result.gate_id] = result

    for gate in serial:
        blocked_by = [dependency for dependency in gate.depends_on if not results[dependency].passed]
        if blocked_by:
            results[gate.gate_id] = GateResult(
                gate_id=gate.gate_id,
                status="skipped",
                exit_code=None,
                duration_ms=0.0,
                stdout_summary="",
                stderr_summary=f"blocked by failed dependencies: {', '.join(blocked_by)}",
                error_code="DEPENDENCY_FAILED",
            )
            continue
        results[gate.gate_id] = run_gate(gate)

    return tuple(results[gate.gate_id] for gate in gates)
