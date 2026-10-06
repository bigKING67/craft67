from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..benchmark.contract import result_errors
from .assets import collect_native_evidence, load_release_evidence
from .github_runs import validate_workflow_binding
from .integrity import repository_head
from .policy import ReleaseLevel


def validate_release_run_bindings(
    evidence_path: Path,
    *,
    level: ReleaseLevel,
    native_run: dict[str, object],
    benchmark_run: dict[str, object],
    benchmark_result_path: Path,
    physical_run: dict[str, object] | None = None,
    evidence_root: Path | None = None,
) -> dict[str, object]:
    evidence = load_release_evidence(evidence_path, level)
    bindings = collect_native_evidence(
        evidence,
        level,
        evidence_root=evidence_root,
    )
    errors: list[str] = []
    checks = evidence.get("checks")
    performance = next(
        (
            check
            for check in checks
            if isinstance(check, dict) and check.get("id") == "performance_regression"
        ),
        None,
    ) if isinstance(checks, list) else None
    performance_evidence = (
        performance.get("evidence") if isinstance(performance, dict) else None
    )
    if not isinstance(performance_evidence, dict):
        errors.append("release evidence performance_regression evidence must be an object")
    else:
        errors.extend(
            validate_workflow_binding(
                performance_evidence.get("workflow"),
                benchmark_run,
                kind="benchmark",
                label="release evidence performance_regression",
            )
        )
        if benchmark_result_path.is_symlink() or not benchmark_result_path.is_file():
            errors.append("benchmark result is missing or unsafe")
        else:
            try:
                benchmark = json.loads(benchmark_result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"benchmark result is invalid: {exc}")
            else:
                errors.extend(result_errors(benchmark, label="selected"))
                digest = hashlib.sha256(benchmark_result_path.read_bytes()).hexdigest()
                if performance_evidence.get("benchmark_result_sha256") != digest:
                    errors.append(
                        "release evidence benchmark_result_sha256 does not match selected result"
                    )
                if benchmark.get("source_commit") != repository_head():
                    errors.append("selected benchmark result must match current HEAD")
                if performance_evidence.get("source_commit") != benchmark.get(
                    "source_commit"
                ):
                    errors.append(
                        "release evidence performance source_commit does not match selected result"
                    )
                if benchmark.get("source_dirty") is not False:
                    errors.append("selected benchmark result must come from a clean source")
                if benchmark.get("scale") != "full":
                    errors.append("selected benchmark result must use the full suite")
    for native, binding in bindings.items():
        is_physical = native == "physical_device"
        run = physical_run if is_physical else native_run
        kind = "physical" if is_physical else "native"
        if run is None:
            errors.append("physical-device evidence requires a selected physical run")
            continue
        errors.extend(
            validate_workflow_binding(
                binding.get("workflow"),
                run,
                kind=kind,
                label=f"release evidence {native}",
            )
        )
    return {
        "schema": "design-craft.release-run-bindings.v1",
        "release_level": level.name,
        "evidence": str(evidence_path),
        "benchmark_run_id": benchmark_run.get("id"),
        "native_targets": sorted(bindings),
        "ok": not errors,
        "errors": errors,
    }


__all__ = ["validate_release_run_bindings"]
