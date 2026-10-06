from __future__ import annotations

import subprocess
import sys
from concurrent.futures import Executor, Future
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .probes import bundled_model_catalog, child_process_env, run_route_probe

RUNTIME_PROBE_WORKERS = 11
RouteProbeRequest = tuple[list[str], str | None, str | None]
RouteProbeResult = tuple[int, dict, str]


@dataclass(frozen=True)
class RuntimeProbeBatch:
    schema: Future[subprocess.CompletedProcess[str]]
    telemetry: Future[subprocess.CompletedProcess[str]]
    browser_capture: Future[subprocess.CompletedProcess[str]]
    browser_receipt: Future[subprocess.CompletedProcess[str]]
    routes: tuple[Future[RouteProbeResult], ...]
    model_catalog: Future[tuple[dict[str, dict], str | None]]


def _execute_route_probe(
    source_root: Path,
    request: RouteProbeRequest,
) -> RouteProbeResult:
    arguments, model, reasoning = request
    return run_route_probe(
        source_root,
        arguments,
        runtime_model=model,
        runtime_reasoning=reasoning,
    )


def submit_runtime_probe_batch(
    executor: Executor,
    source_root: Path,
    probe_requests: Sequence[RouteProbeRequest],
) -> RuntimeProbeBatch:
    """Submit every independent runtime certification probe before waiting."""
    tools_root = source_root / "tools"
    schema = executor.submit(
        subprocess.run,
        [
            sys.executable,
            str(tools_root / "frontend_route_schema_validate.py"),
            "--schema",
            str(tools_root / "frontend_agent_routing.schema.json"),
            "--instance",
            str(tools_root / "frontend_agent_routing.json"),
            "--json",
        ],
        cwd=source_root,
        env=child_process_env(),
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    telemetry = executor.submit(
        subprocess.run,
        [sys.executable, str(tools_root / "frontend_route_telemetry.py"), "--check"],
        cwd=source_root,
        env=child_process_env(
            FRONTEND_ROUTE_TELEMETRY_CONTEXT="test",
            FRONTEND_ROUTE_TELEMETRY_LOG_ENABLED="0",
        ),
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    browser_capture = executor.submit(
        subprocess.run,
        [sys.executable, str(tools_root / "tests/test_frontend_browser_capture.py")],
        cwd=source_root,
        env=child_process_env(),
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
    browser_receipt = executor.submit(
        subprocess.run,
        ["bash", str(tools_root / "tests/test_frontend_browser_lifecycle_receipt.sh")],
        cwd=source_root,
        env=child_process_env(),
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    routes = tuple(
        executor.submit(_execute_route_probe, source_root, request)
        for request in probe_requests
    )
    model_catalog = executor.submit(bundled_model_catalog)
    return RuntimeProbeBatch(
        schema=schema,
        telemetry=telemetry,
        browser_capture=browser_capture,
        browser_receipt=browser_receipt,
        routes=routes,
        model_catalog=model_catalog,
    )
