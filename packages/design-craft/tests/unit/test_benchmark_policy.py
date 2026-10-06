from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.fixtures.benchmark import (
    benchmark_result as result,
    full_benchmark_result as full_result,
)
from tools.design_craft.benchmark.contract import (
    ABSOLUTE_REGRESSION_LIMIT_MS,
    CACHE_CAPACITY,
    MIN_FULL_SAMPLES,
    RELATIVE_REGRESSION_LIMIT,
    SCHEMA,
    SCHEMA_V1,
    compare_results,
    metric_errors,
    migrate_v1_result,
    result_errors,
)
from tools.design_craft.benchmark.fixtures import (
    _BoundedDigestCache,
    _validate_changed_files,
)
from tools.design_craft.benchmark.runner import (
    _measure_cache,
    _percentile,
    _portable_validation_gate_count,
    _source_binding,
)


def legacy_result(p95: float) -> dict[str, object]:
    payload = result(p95)
    return {
        "schema": SCHEMA_V1,
        "scale": payload["scale"],
        "runner_id": "linux-x86_64-python3.13",
        "source_commit": payload["source_commit"],
        "source_dirty": payload["source_dirty"],
        "python": "3.13.5",
        "platform": "Linux-legacy-kernel",
        "policy": {
            "relative_regression_limit": RELATIVE_REGRESSION_LIMIT,
            "absolute_regression_limit_ms": ABSOLUTE_REGRESSION_LIMIT_MS,
        },
        "metrics": payload["metrics"],
    }
class BenchmarkPolicyTests(unittest.TestCase):
    def test_full_results_require_enough_samples_for_p95(self) -> None:
        payload = full_result(100.0)
        self.assertEqual(result_errors(payload, label="current"), [])

        payload["metrics"]["route_pack"]["iterations"] = MIN_FULL_SAMPLES - 1
        payload["metrics"]["route_pack"]["samples"] = [100.0] * (
            MIN_FULL_SAMPLES - 1
        )
        errors = result_errors(payload, label="current")
        self.assertTrue(any("at least 20 samples" in error for error in errors))

    def test_full_sample_p95_is_not_a_single_maximum(self) -> None:
        samples = [100.0] * (MIN_FULL_SAMPLES - 1) + [1000.0]
        self.assertEqual(_percentile(samples, 0.95), 100.0)

    def test_metric_summaries_must_match_samples(self) -> None:
        payload = result(100.0)
        payload["metrics"]["route_selection"]["p50"] = 90.0
        payload["metrics"]["route_selection"]["p95"] = 90.0

        errors = result_errors(payload, label="current")

        self.assertTrue(any("p50 must match its samples" in error for error in errors))
        self.assertTrue(any("p95 must match its samples" in error for error in errors))

    def test_summary_validation_allows_serialization_rounding(self) -> None:
        serialized = {
            "unit": "ms",
            "iterations": 2,
            "p50": 0.152,
            "p95": 0.152,
            "max": 0.152,
            "samples": [0.151, 0.152],
        }

        self.assertEqual(metric_errors("rounded", serialized), [])

    def test_falsified_p95_cannot_bypass_regression(self) -> None:
        current = result(170.0)
        current["metrics"]["route_selection"]["p50"] = 100.0
        current["metrics"]["route_selection"]["p95"] = 100.0

        comparison = compare_results(result(100.0), current)

        self.assertFalse(comparison["ok"])
        self.assertTrue(
            any("route_selection p95 must match its samples" in error for error in comparison["errors"])
        )

    def test_smoke_comparison_is_diagnostic_only(self) -> None:
        comparison = compare_results(result(100.0), result(100.0))

        self.assertTrue(comparison["ok"], comparison["errors"])
        self.assertTrue(any("diagnostic only" in warning for warning in comparison["warnings"]))

    def test_source_binding_preserves_initial_dirty_state(self) -> None:
        commit = "a" * 40
        self.assertEqual(
            _source_binding((commit, True), (commit, False)),
            {"source_commit": commit, "source_dirty": True},
        )

    def test_source_binding_rejects_commit_changes(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "source commit changed"):
            _source_binding(("a" * 40, False), ("b" * 40, False))

    def test_small_absolute_variance_does_not_fail(self) -> None:
        comparison = compare_results(result(10.0), result(20.0))
        self.assertTrue(comparison["ok"])

    def test_relative_and_absolute_regression_fails(self) -> None:
        comparison = compare_results(result(100.0), result(170.0))
        self.assertFalse(comparison["ok"])
        self.assertTrue(any(item["regressed"] for item in comparison["comparisons"]))

    def test_different_runner_fails_closed(self) -> None:
        comparison = compare_results(
            result(100.0),
            result(100.0, image="macos-15"),
        )
        self.assertFalse(comparison["ok"])

    def test_kernel_and_image_patch_drift_do_not_fail(self) -> None:
        baseline = result(100.0, platform_name="Linux-kernel-a")
        current = result(100.0, platform_name="Linux-kernel-b")
        current["runner"]["image_version"] = "20260721.9"
        current["runner"]["python"] = "3.13.14"
        comparison = compare_results(baseline, current)
        self.assertTrue(comparison["ok"], comparison["errors"])

    def test_os_arch_and_python_minor_drift_fail_closed(self) -> None:
        cases = (
            {"os_name": "darwin"},
            {"arch": "aarch64"},
            {"python": "3.12.9"},
        )
        for values in cases:
            with self.subTest(values=values):
                comparison = compare_results(result(100.0), result(100.0, **values))
                self.assertFalse(comparison["ok"])

    def test_legacy_v1_baseline_is_read_with_explicit_warning(self) -> None:
        comparison = compare_results(legacy_result(100.0), result(100.0))
        self.assertTrue(comparison["ok"], comparison["errors"])
        self.assertTrue(any("legacy v1" in item for item in comparison["warnings"]))

    def test_v1_migration_requires_explicit_runner_identity(self) -> None:
        migrated = migrate_v1_result(
            legacy_result(100.0),
            runner_image="ubuntu-24.04",
            image_version="20260720.1",
            node_version="24.18.0",
        )
        self.assertEqual(migrated["schema"], SCHEMA)
        self.assertEqual(migrated["runner"]["image"], "ubuntu-24.04")
        self.assertEqual(migrated["migration"]["from_schema"], SCHEMA_V1)
        self.assertEqual(result_errors(migrated, label="migrated"), [])

    def test_missing_schema_fails_closed(self) -> None:
        baseline = result(100.0)
        del baseline["schema"]
        comparison = compare_results(baseline, result(100.0))
        self.assertFalse(comparison["ok"])
        self.assertTrue(any("schema" in error for error in comparison["errors"]))

    def test_metric_set_drift_fails_closed(self) -> None:
        baseline = result(100.0)
        del baseline["metrics"]["incremental_validation_100"]
        comparison = compare_results(baseline, result(100.0))
        self.assertFalse(comparison["ok"])
        self.assertTrue(any("metric set" in error for error in comparison["errors"]))

    def test_non_finite_metric_fails_closed(self) -> None:
        baseline = result(100.0)
        baseline["metrics"]["route_selection"]["p95"] = float("nan")
        comparison = compare_results(baseline, result(100.0))
        self.assertFalse(comparison["ok"])
        self.assertTrue(any("finite" in error for error in comparison["errors"]))

    def test_sample_count_mismatch_fails_closed(self) -> None:
        baseline = result(100.0)
        baseline["metrics"]["route_selection"]["iterations"] = 2
        comparison = compare_results(baseline, result(100.0))
        self.assertFalse(comparison["ok"])
        self.assertTrue(any("sample count" in error for error in comparison["errors"]))

    def test_baseline_and_current_sample_counts_must_match(self) -> None:
        current = result(100.0)
        current["metrics"]["route_selection"]["iterations"] = 2
        current["metrics"]["route_selection"]["samples"] = [100.0, 100.0]
        comparison = compare_results(result(100.0), current)
        self.assertFalse(comparison["ok"])
        self.assertTrue(any("between baseline and current" in error for error in comparison["errors"]))

    def test_cache_capacity_violation_fails_closed(self) -> None:
        baseline = result(100.0)
        baseline["metrics"]["validation_cache_warm"]["max_entries_observed"] = (
            CACHE_CAPACITY + 1
        )
        comparison = compare_results(baseline, result(100.0))
        self.assertFalse(comparison["ok"])
        self.assertTrue(any("cache capacity" in error for error in comparison["errors"]))

    def test_synthetic_cache_scope_cannot_claim_runtime_coverage(self) -> None:
        payload = result(100.0)
        payload["metrics"]["validation_cache_warm"]["fixture_scope"] = (
            "production_runtime_cache"
        )

        errors = result_errors(payload, label="current")

        self.assertTrue(any("synthetic cache scope" in error for error in errors))

    def test_release_bundle_contract_fails_closed(self) -> None:
        baseline = result(100.0)
        baseline["metrics"]["release_bundle_build"]["deterministic"] = False
        comparison = compare_results(baseline, result(100.0))
        self.assertFalse(comparison["ok"])
        self.assertTrue(any("release_bundle_build" in error for error in comparison["errors"]))

    def test_route_pack_requires_portable_fixture(self) -> None:
        baseline = result(100.0)
        del baseline["metrics"]["route_pack"]["fixture_scope"]
        comparison = compare_results(baseline, result(100.0))
        self.assertFalse(comparison["ok"])
        self.assertTrue(any("portable self-check" in error for error in comparison["errors"]))

    def test_portable_validation_requires_real_wall_clock_scope(self) -> None:
        payload = result(100.0)
        payload["metrics"]["portable_validation"]["resource_scope"] = (
            "cpu_and_peak_rss"
        )

        errors = result_errors(payload, label="current")

        self.assertTrue(any("real portable wall-clock" in error for error in errors))

    def test_tree_scan_requires_explicit_synthetic_scope(self) -> None:
        payload = result(100.0)
        del payload["metrics"]["tree_scan_10000"]["fixture_scope"]

        errors = result_errors(payload, label="current")

        self.assertTrue(any("synthetic SHA-256 tree" in error for error in errors))

    def test_synthetic_validation_scope_is_required(self) -> None:
        payload = result(100.0)
        del payload["metrics"]["incremental_validation_10"]["fixture_scope"]
        del payload["metrics"]["validation_cache_warm"]["fixture_scope"]

        errors = result_errors(payload, label="current")

        self.assertTrue(any("synthetic fixture scope" in error for error in errors))
        self.assertTrue(any("synthetic cache scope" in error for error in errors))

    def test_portable_validation_output_contract(self) -> None:
        output = (
            '{"schema":"design-craft.validation-run.v2",'
            '"profile":"portable","status":"passed","gate_count":27}'
        )

        self.assertEqual(_portable_validation_gate_count(output), 27)
        with self.assertRaisesRegex(RuntimeError, "status"):
            _portable_validation_gate_count(output.replace("passed", "failed"))


class IncrementalAndCacheTests(unittest.TestCase):
    def test_incremental_validation_rejects_invalid_python(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-benchmark-test-") as raw:
            root = Path(raw)
            invalid = root / "invalid.py"
            invalid.write_text("def broken(:\n", encoding="utf-8")
            with self.assertRaises(SyntaxError):
                _validate_changed_files(root, [invalid])

    def test_incremental_validation_rejects_duplicate_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-benchmark-test-") as raw:
            root = Path(raw)
            path = root / "valid.json"
            path.write_text('{"ok": true}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                _validate_changed_files(root, [path, path])

    def test_bounded_cache_records_hits_misses_and_invalidation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-benchmark-test-") as raw:
            root = Path(raw)
            paths = []
            for index in range(3):
                path = root / f"fixture-{index}.txt"
                path.write_text(f"value {index}\n", encoding="utf-8")
                paths.append(path)
            cache = _BoundedDigestCache(root, capacity=2)
            first = cache.digest(paths[0])
            self.assertEqual(cache.misses, 1)
            self.assertEqual(cache.digest(paths[0]), first)
            self.assertEqual(cache.hits, 1)
            paths[0].write_text("changed value with a different size\n", encoding="utf-8")
            self.assertNotEqual(cache.digest(paths[0]), first)
            self.assertEqual(cache.misses, 2)
            cache.digest(paths[1])
            cache.digest(paths[2])
            self.assertEqual(cache.entries, 2)
            self.assertLessEqual(cache.max_entries_observed, cache.capacity)
            self.assertGreater(cache.evictions, 0)

    def test_warm_metric_excludes_cache_population_from_counters(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-benchmark-test-") as raw:
            root = Path(raw)
            paths = []
            for index in range(3):
                path = root / f"fixture-{index}.txt"
                path.write_text(f"value {index}\n", encoding="utf-8")
                paths.append(path)

            cold = _measure_cache(root, paths, capacity=3, iterations=2, warm=False)
            warm = _measure_cache(root, paths, capacity=3, iterations=2, warm=True)

            self.assertEqual(cold["cache_hits"], 0)
            self.assertEqual(cold["cache_misses"], 6)
            self.assertEqual(warm["cache_hits"], 6)
            self.assertEqual(warm["cache_misses"], 0)


if __name__ == "__main__":
    unittest.main()
