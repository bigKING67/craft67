from __future__ import annotations

from tools.design_craft.benchmark.contract import (
    ABSOLUTE_REGRESSION_LIMIT_MS,
    CACHE_CAPACITY,
    MIN_FULL_SAMPLES,
    POLICY_VERSION,
    RELATIVE_REGRESSION_LIMIT,
    SCHEMA,
    SMOKE_METRIC_NAMES,
)


def benchmark_metric(p95: float) -> dict[str, object]:
    return {
        "unit": "ms",
        "iterations": 1,
        "p50": p95,
        "p95": p95,
        "max": p95,
        "samples": [p95],
    }


def benchmark_metrics(p95: float) -> dict[str, dict[str, object]]:
    values = {name: benchmark_metric(p95) for name in SMOKE_METRIC_NAMES}
    values["route_pack"]["fixture_scope"] = "portable_self_check"
    values["portable_validation"].update(
        {
            "execution_scope": "real_portable_validation_profile",
            "resource_scope": "wall_clock_only",
            "validation_profile": "portable",
            "validation_schema": "design-craft.validation-run.v2",
            "gate_count": 27,
        }
    )
    for count in (1_000, 10_000):
        values[f"tree_scan_{count}"].update(
            {
                "file_count": count,
                "fixture_scope": "benchmark_only_synthetic_tree_digest",
                "scan_operation": "sha256_file_tree",
            }
        )
    for count in (1, 10, 100):
        values[f"incremental_validation_{count}"].update(
            {
                "changed_files": count,
                "validation_scope": "explicit_changed_files",
                "fixture_root": "temporary_directory",
                "fixture_scope": "benchmark_only_synthetic_changed_files",
            }
        )
    values["validation_cache_cold"].update(
        {
            "cache_capacity": CACHE_CAPACITY,
            "working_set": CACHE_CAPACITY,
            "cache_hits": 0,
            "cache_misses": CACHE_CAPACITY,
            "cache_evictions": 0,
            "max_entries_observed": CACHE_CAPACITY,
            "warm": False,
            "fixture_scope": "benchmark_only_synthetic_digest_cache",
        }
    )
    values["validation_cache_warm"].update(
        {
            "cache_capacity": CACHE_CAPACITY,
            "working_set": CACHE_CAPACITY,
            "cache_hits": CACHE_CAPACITY,
            "cache_misses": 0,
            "cache_evictions": 0,
            "max_entries_observed": CACHE_CAPACITY,
            "warm": True,
            "fixture_scope": "benchmark_only_synthetic_digest_cache",
        }
    )
    values["validation_cache_overflow"].update(
        {
            "cache_capacity": CACHE_CAPACITY,
            "working_set": CACHE_CAPACITY * 2,
            "cache_hits": 0,
            "cache_misses": CACHE_CAPACITY * 2,
            "cache_evictions": CACHE_CAPACITY,
            "max_entries_observed": CACHE_CAPACITY,
            "warm": False,
            "fixture_scope": "benchmark_only_synthetic_digest_cache",
        }
    )
    values["install_rollback"].update(
        {
            "failure_point": "after_switch",
            "expected_exit_code": 1,
            "rollback_verified": True,
            "install_root": "temporary_directory",
        }
    )
    values["installer_lock_contention"].update(
        {
            "lock_timeout_seconds": 0,
            "contention_observed": True,
            "real_install_touched": False,
            "install_root": "temporary_directory",
        }
    )
    values["release_bundle_build"].update(
        {
            "bundle_kind": "operational_npm_package",
            "artifact_bytes": 1024,
            "deterministic": True,
            "output_root": "temporary_directory",
        }
    )
    return values


def benchmark_result(
    p95: float,
    *,
    os_name: str = "linux",
    arch: str = "x86_64",
    image: str = "ubuntu-24.04",
    python: str = "3.13.5",
    platform_name: str = "Linux-fixture-one",
    scale: str = "smoke",
) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "scale": scale,
        "runner": {
            "os": os_name,
            "arch": arch,
            "image": image,
            "image_version": "20260720.1",
            "python": python,
            "node": "24.18.0",
        },
        "diagnostics": {
            "platform": platform_name,
            "kernel": platform_name,
        },
        "source_commit": "a" * 40,
        "source_dirty": False,
        "policy": {
            "version": POLICY_VERSION,
            "relative_regression_limit": RELATIVE_REGRESSION_LIMIT,
            "absolute_regression_limit_ms": ABSOLUTE_REGRESSION_LIMIT_MS,
        },
        "metrics": benchmark_metrics(p95),
    }


def full_benchmark_result(p95: float) -> dict[str, object]:
    payload = benchmark_result(p95, scale="full")
    payload["metrics"]["tree_scan_100000"] = benchmark_metric(p95)
    payload["metrics"]["tree_scan_100000"].update(
        {
            "file_count": 100_000,
            "fixture_scope": "benchmark_only_synthetic_tree_digest",
            "scan_operation": "sha256_file_tree",
        }
    )
    for value in payload["metrics"].values():
        value["iterations"] = MIN_FULL_SAMPLES
        value["samples"] = [p95] * MIN_FULL_SAMPLES
    return payload
