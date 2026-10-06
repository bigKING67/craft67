from __future__ import annotations

import math
import re

from .measurement import SUMMARY_TOLERANCE_MS, summarize_samples


SCHEMA_V1 = "design-craft.benchmark-result.v1"
SCHEMA = "design-craft.benchmark-result.v2"
COMPARISON_SCHEMA = "design-craft.benchmark-comparison.v2"
POLICY_VERSION = "v1"
RELATIVE_REGRESSION_LIMIT = 0.15
ABSOLUTE_REGRESSION_LIMIT_MS = 50.0
MIN_FULL_SAMPLES = 20
INCREMENTAL_FILE_COUNTS = (1, 10, 100)
CACHE_CAPACITY = 32
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
LEGACY_RUNNER_PATTERN = re.compile(
    r"(?P<os>[a-z0-9_]+)-(?P<arch>[a-z0-9_]+)-python(?P<python>[0-9]+\.[0-9]+)"
)

SMOKE_METRIC_NAMES = frozenset(
    {
        "route_selection",
        "route_pack",
        "tree_scan_1000",
        "tree_scan_10000",
        "validation_registry",
        "portable_validation",
        "lint_full",
        "evidence_validation",
        "package_validation",
        "incremental_validation_1",
        "incremental_validation_10",
        "incremental_validation_100",
        "validation_cache_cold",
        "validation_cache_warm",
        "validation_cache_overflow",
        "install_atomic",
        "install_rollback",
        "installer_lock_contention",
        "release_bundle_build",
    }
)
FULL_METRIC_NAMES = SMOKE_METRIC_NAMES | {"tree_scan_100000"}


def _is_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def metric_errors(name: str, metric: object) -> list[str]:
    if not isinstance(metric, dict):
        return [f"metric {name} must be an object"]
    errors: list[str] = []
    if metric.get("unit") != "ms":
        errors.append(f"metric {name} unit must be ms")
    iterations = metric.get("iterations")
    samples = metric.get("samples")
    if not isinstance(iterations, int) or isinstance(iterations, bool) or iterations <= 0:
        errors.append(f"metric {name} iterations must be a positive integer")
    if not isinstance(samples, list) or not samples:
        errors.append(f"metric {name} samples must be a non-empty array")
        numeric_samples: list[float] = []
    else:
        numeric_samples = [
            float(value)
            for value in samples
            if _is_number(value) and float(value) >= 0
        ]
        if len(numeric_samples) != len(samples):
            errors.append(f"metric {name} samples must be finite non-negative numbers")
        if (
            isinstance(iterations, int)
            and not isinstance(iterations, bool)
            and len(samples) != iterations
        ):
            errors.append(f"metric {name} sample count must match iterations")
    timing_values: dict[str, float] = {}
    for field in ("p50", "p95", "max"):
        value = metric.get(field)
        if not _is_number(value) or float(value) < 0:
            errors.append(f"metric {name} {field} must be a finite non-negative number")
        else:
            timing_values[field] = float(value)
    if set(timing_values) == {"p50", "p95", "max"} and not (
        timing_values["p50"] <= timing_values["p95"] <= timing_values["max"]
    ):
        errors.append(f"metric {name} must satisfy p50 <= p95 <= max")
    if numeric_samples and len(numeric_samples) == len(samples):
        expected_summary = summarize_samples(numeric_samples)
        for field, expected in expected_summary.items():
            if field in timing_values and not math.isclose(
                timing_values[field],
                expected,
                rel_tol=0.0,
                abs_tol=SUMMARY_TOLERANCE_MS,
            ):
                errors.append(f"metric {name} {field} must match its samples")
    return errors


def specialized_metric_errors(name: str, metric: object) -> list[str]:
    if not isinstance(metric, dict):
        return []
    errors: list[str] = []
    if name.startswith("incremental_validation_"):
        try:
            expected = int(name.rsplit("_", 1)[1])
        except ValueError:
            return [f"metric {name} has an invalid incremental file count"]
        if metric.get("changed_files") != expected:
            errors.append(f"metric {name} changed_files must be {expected}")
        if metric.get("validation_scope") != "explicit_changed_files":
            errors.append(f"metric {name} must declare explicit_changed_files scope")
        if metric.get("fixture_root") != "temporary_directory":
            errors.append(f"metric {name} must use a temporary fixture root")
        fixture_scope = metric.get("fixture_scope")
        if fixture_scope != "benchmark_only_synthetic_changed_files":
            errors.append(f"metric {name} has an invalid synthetic fixture scope")
    if name.startswith("validation_cache_"):
        fixture_scope = metric.get("fixture_scope")
        if fixture_scope != "benchmark_only_synthetic_digest_cache":
            errors.append(f"metric {name} has an invalid synthetic cache scope")
        integer_fields = (
            "cache_capacity",
            "working_set",
            "cache_hits",
            "cache_misses",
            "cache_evictions",
            "max_entries_observed",
        )
        for field in integer_fields:
            value = metric.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"metric {name} {field} must be a non-negative integer")
        capacity = metric.get("cache_capacity")
        max_entries = metric.get("max_entries_observed")
        if (
            isinstance(capacity, int)
            and isinstance(max_entries, int)
            and max_entries > capacity
        ):
            errors.append(f"metric {name} exceeded its declared cache capacity")
        if name == "validation_cache_cold" and (
            metric.get("warm") is not False
            or metric.get("cache_hits") != 0
            or not isinstance(metric.get("cache_misses"), int)
            or metric["cache_misses"] <= 0
        ):
            errors.append("metric validation_cache_cold must record only cache misses")
        if name == "validation_cache_warm" and (
            metric.get("warm") is not True
            or not isinstance(metric.get("cache_hits"), int)
            or metric["cache_hits"] <= 0
            or metric.get("cache_misses") != 0
        ):
            errors.append("metric validation_cache_warm must record only cache hits")
        if name == "validation_cache_overflow" and (
            not isinstance(metric.get("cache_evictions"), int)
            or metric["cache_evictions"] <= 0
        ):
            errors.append("metric validation_cache_overflow must record bounded evictions")
    if name == "install_rollback" and (
        metric.get("failure_point") != "after_switch"
        or metric.get("expected_exit_code") != 1
        or metric.get("rollback_verified") is not True
        or metric.get("install_root") != "temporary_directory"
    ):
        errors.append("metric install_rollback must prove temporary after-switch restoration")
    if name == "installer_lock_contention" and (
        metric.get("lock_timeout_seconds") != 0
        or metric.get("contention_observed") is not True
        or metric.get("real_install_touched") is not False
        or metric.get("install_root") != "temporary_directory"
    ):
        errors.append("metric installer_lock_contention must fail closed in a temporary root")
    if name == "release_bundle_build" and (
        metric.get("bundle_kind") != "operational_npm_package"
        or not isinstance(metric.get("artifact_bytes"), int)
        or metric["artifact_bytes"] <= 0
        or metric.get("deterministic") is not True
        or metric.get("output_root") != "temporary_directory"
    ):
        errors.append("metric release_bundle_build must prove deterministic temporary output")
    if name == "route_pack" and metric.get("fixture_scope") != "portable_self_check":
        errors.append("metric route_pack must use the portable self-check fixture")
    if name.startswith("tree_scan_"):
        try:
            expected_count = int(name.rsplit("_", 1)[1])
        except ValueError:
            return [*errors, f"metric {name} has an invalid tree file count"]
        if (
            metric.get("file_count") != expected_count
            or metric.get("fixture_scope")
            != "benchmark_only_synthetic_tree_digest"
            or metric.get("scan_operation") != "sha256_file_tree"
        ):
            errors.append(
                f"metric {name} must declare its synthetic SHA-256 tree fixture"
            )
    if name == "portable_validation" and (
        metric.get("execution_scope") != "real_portable_validation_profile"
        or metric.get("resource_scope") != "wall_clock_only"
        or metric.get("validation_profile") != "portable"
        or metric.get("validation_schema") != "design-craft.validation-run.v2"
        or not isinstance(metric.get("gate_count"), int)
        or isinstance(metric.get("gate_count"), bool)
        or metric["gate_count"] <= 0
    ):
        errors.append(
            "metric portable_validation must prove real portable wall-clock execution"
        )
    return errors


def _python_minor(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"([0-9]+\.[0-9]+)(?:\.[0-9]+)?", value)
    return match.group(1) if match else None


def _policy(payload: dict[str, object]) -> dict[str, object] | None:
    value = payload.get("policy")
    if not isinstance(value, dict):
        return None
    return {
        "version": value.get("version", POLICY_VERSION),
        "relative_regression_limit": value.get("relative_regression_limit"),
        "absolute_regression_limit_ms": value.get("absolute_regression_limit_ms"),
    }


def runner_identity(payload: dict[str, object]) -> dict[str, str] | None:
    if payload.get("schema") == SCHEMA:
        runner = payload.get("runner")
        if not isinstance(runner, dict):
            return None
        python_minor = _python_minor(runner.get("python"))
        required = {
            "os": runner.get("os"),
            "arch": runner.get("arch"),
            "image": runner.get("image"),
        }
        if python_minor is None or not all(
            isinstance(value, str) and value for value in required.values()
        ):
            return None
        return {
            "os": str(required["os"]),
            "arch": str(required["arch"]),
            "image": str(required["image"]),
            "python_minor": python_minor,
        }

    runner_id = payload.get("runner_id")
    python_minor = _python_minor(payload.get("python"))
    if not isinstance(runner_id, str) or python_minor is None:
        return None
    match = LEGACY_RUNNER_PATTERN.fullmatch(runner_id)
    if match is None or match.group("python") != python_minor:
        return None
    return {
        "os": match.group("os"),
        "arch": match.group("arch"),
        "image": "legacy-unbound",
        "python_minor": python_minor,
    }


def migrate_v1_result(
    payload: dict[str, object],
    *,
    runner_image: str,
    image_version: str,
    node_version: str,
) -> dict[str, object]:
    errors = result_errors(payload, label="legacy baseline")
    if payload.get("schema") != SCHEMA_V1:
        raise ValueError(f"benchmark migration requires {SCHEMA_V1}")
    if errors:
        raise ValueError("; ".join(errors))
    identity = runner_identity(payload)
    assert identity is not None
    if not all(value.strip() for value in (runner_image, image_version, node_version)):
        raise ValueError("benchmark migration identity fields must be non-empty")
    return {
        "schema": SCHEMA,
        "scale": payload["scale"],
        "runner": {
            "os": identity["os"],
            "arch": identity["arch"],
            "image": runner_image,
            "image_version": image_version,
            "python": payload["python"],
            "node": node_version,
        },
        "diagnostics": {
            "platform": payload["platform"],
            "kernel": "not-recorded-v1",
        },
        "migration": {
            "from_schema": SCHEMA_V1,
            "identity_limitations": ["kernel", "image_version", "node"],
        },
        "source_commit": payload["source_commit"],
        "source_dirty": payload["source_dirty"],
        "policy": {
            "version": POLICY_VERSION,
            "relative_regression_limit": RELATIVE_REGRESSION_LIMIT,
            "absolute_regression_limit_ms": ABSOLUTE_REGRESSION_LIMIT_MS,
        },
        "metrics": payload["metrics"],
    }


def result_errors(payload: object, *, label: str) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} benchmark result must be an object"]
    errors: list[str] = []
    schema = payload.get("schema")
    if schema not in {SCHEMA_V1, SCHEMA}:
        errors.append(f"{label} benchmark schema must be {SCHEMA_V1} or {SCHEMA}")
    scale = payload.get("scale")
    if scale not in {"smoke", "full"}:
        errors.append(f"{label} benchmark scale must be smoke or full")
    source_commit = payload.get("source_commit")
    if not isinstance(source_commit, str) or COMMIT_PATTERN.fullmatch(source_commit) is None:
        errors.append(f"{label} source_commit must be a full lowercase Git SHA")
    if not isinstance(payload.get("source_dirty"), bool):
        errors.append(f"{label} source_dirty must be boolean")
    if schema == SCHEMA_V1:
        runner_id = payload.get("runner_id")
        if not isinstance(runner_id, str) or not runner_id.strip():
            errors.append(f"{label} runner_id must be a non-empty string")
        for field in ("python", "platform"):
            if not isinstance(payload.get(field), str) or not str(payload[field]).strip():
                errors.append(f"{label} {field} must be a non-empty string")
    elif schema == SCHEMA:
        runner = payload.get("runner")
        if not isinstance(runner, dict):
            errors.append(f"{label} runner must be an object")
        else:
            for field in ("os", "arch", "image", "image_version", "python", "node"):
                if not isinstance(runner.get(field), str) or not str(runner[field]).strip():
                    errors.append(f"{label} runner.{field} must be a non-empty string")
            if _python_minor(runner.get("python")) is None:
                errors.append(f"{label} runner.python must be a semantic Python version")
        diagnostics = payload.get("diagnostics")
        if not isinstance(diagnostics, dict):
            errors.append(f"{label} diagnostics must be an object")
        else:
            for field in ("platform", "kernel"):
                if not isinstance(diagnostics.get(field), str) or not str(
                    diagnostics[field]
                ).strip():
                    errors.append(
                        f"{label} diagnostics.{field} must be a non-empty string"
                    )
        migration = payload.get("migration")
        if migration is not None and (
            not isinstance(migration, dict)
            or migration.get("from_schema") != SCHEMA_V1
            or not isinstance(migration.get("identity_limitations"), list)
            or not all(
                isinstance(item, str) and item
                for item in migration.get("identity_limitations", [])
            )
        ):
            errors.append(f"{label} migration metadata is invalid")
    expected_policy = {
        "version": POLICY_VERSION,
        "relative_regression_limit": RELATIVE_REGRESSION_LIMIT,
        "absolute_regression_limit_ms": ABSOLUTE_REGRESSION_LIMIT_MS,
    }
    if _policy(payload) != expected_policy:
        errors.append(f"{label} benchmark policy does not match the comparison contract")
    if runner_identity(payload) is None:
        errors.append(f"{label} runner identity is invalid")
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"{label} benchmark result must contain a metrics object")
        return errors
    expected_names = FULL_METRIC_NAMES if scale == "full" else SMOKE_METRIC_NAMES
    if set(metrics) != set(expected_names):
        errors.append(
            f"{label} metric set mismatch expected={sorted(expected_names)} "
            f"actual={sorted(metrics)}"
        )
    for name, metric in metrics.items():
        errors.extend(f"{label}: {error}" for error in metric_errors(str(name), metric))
        errors.extend(
            f"{label}: {error}"
            for error in specialized_metric_errors(str(name), metric)
        )
        if scale == "full" and isinstance(metric, dict):
            iterations = metric.get("iterations")
            if (
                isinstance(iterations, int)
                and not isinstance(iterations, bool)
                and iterations < MIN_FULL_SAMPLES
            ):
                errors.append(
                    f"{label}: full metric {name} must use at least "
                    f"{MIN_FULL_SAMPLES} samples"
                )
    return errors


def compare_results(
    baseline: dict[str, object], current: dict[str, object]
) -> dict[str, object]:
    errors = [
        *result_errors(baseline, label="baseline"),
        *result_errors(current, label="current"),
    ]
    comparisons: list[dict[str, object]] = []
    warnings: list[str] = []
    if not isinstance(baseline, dict) or not isinstance(current, dict):
        return {
            "schema": COMPARISON_SCHEMA,
            "ok": False,
            "errors": errors,
            "warnings": warnings,
            "comparisons": comparisons,
        }
    if baseline.get("scale") != current.get("scale"):
        errors.append("baseline scale must match the current benchmark")
    elif baseline.get("scale") == "smoke":
        warnings.append(
            "smoke benchmark comparison is diagnostic only; use full results for "
            "regression and release evidence"
        )
    if _policy(baseline) != _policy(current):
        errors.append("baseline policy must match the current benchmark")
    baseline_runner = runner_identity(baseline)
    current_runner = runner_identity(current)
    if baseline_runner is not None and current_runner is not None:
        for field in ("os", "arch", "python_minor"):
            if baseline_runner[field] != current_runner[field]:
                errors.append(f"baseline runner {field} must match the current benchmark")
        if baseline.get("schema") == SCHEMA and current.get("schema") == SCHEMA:
            if baseline_runner["image"] != current_runner["image"]:
                errors.append("baseline runner image must match the current benchmark")
        else:
            warnings.append(
                "legacy v1 benchmark identity does not bind the runner image family; "
                "migrate the baseline explicitly before the next release"
            )
    baseline_metrics = baseline.get("metrics")
    current_metrics = current.get("metrics")
    if not isinstance(baseline_metrics, dict) or not isinstance(current_metrics, dict):
        return {
            "schema": COMPARISON_SCHEMA,
            "ok": False,
            "errors": errors,
            "warnings": warnings,
            "comparisons": comparisons,
        }
    if set(baseline_metrics) != set(current_metrics):
        errors.append("baseline and current metric sets must match exactly")
    for name in sorted(set(baseline_metrics) & set(current_metrics)):
        baseline_metric = baseline_metrics[name]
        current_metric = current_metrics[name]
        if metric_errors(name, baseline_metric) or metric_errors(name, current_metric):
            continue
        assert isinstance(baseline_metric, dict)
        assert isinstance(current_metric, dict)
        if baseline_metric.get("iterations") != current_metric.get("iterations"):
            errors.append(f"{name} sample count must match between baseline and current")
            continue
        baseline_p95 = float(baseline_metric["p95"])
        current_p95 = float(current_metric["p95"])
        absolute_delta = current_p95 - baseline_p95
        relative_delta = absolute_delta / max(baseline_p95, 0.001)
        regressed = (
            absolute_delta > ABSOLUTE_REGRESSION_LIMIT_MS
            and relative_delta > RELATIVE_REGRESSION_LIMIT
        )
        if regressed:
            errors.append(
                f"{name} regressed by {relative_delta:.1%} and {absolute_delta:.3f} ms"
            )
        comparisons.append(
            {
                "name": name,
                "baseline_p95_ms": baseline_p95,
                "current_p95_ms": current_p95,
                "absolute_delta_ms": round(absolute_delta, 3),
                "relative_delta": round(relative_delta, 6),
                "regressed": regressed,
            }
        )
    return {
        "schema": COMPARISON_SCHEMA,
        "baseline_commit": baseline.get("source_commit"),
        "current_commit": current.get("source_commit"),
        "runner": current_runner,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "comparisons": comparisons,
    }
