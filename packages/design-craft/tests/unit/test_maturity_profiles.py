from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.design_craft.repo import REPO_ROOT
from tools.design_craft.release.integrity import repository_head
from tools.design_craft.validation.maturity.gates import performance_regression, route_pack
from tools.design_craft.validation.maturity.model import MaturityContext
from tools.design_craft.validation.maturity.profiles import (
    check_profile_invariants,
    load_profile,
)


class MaturityProfileTests(unittest.TestCase):
    def test_development_route_pack_is_portable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-missing-codex-") as raw:
            missing_codex_home = Path(raw) / "missing"
            with mock.patch.dict(
                os.environ,
                {"CODEX_HOME": str(missing_codex_home)},
                clear=False,
            ):
                result = route_pack(
                    MaturityContext(
                        root=REPO_ROOT,
                        profile="development",
                        phase="candidate",
                        baseline_path=None,
                    )
                )
        self.assertTrue(result.passed, result.error)
        self.assertEqual(result.evidence["fixture_scope"], "portable_self_check")

    def test_release_performance_rejects_smoke_baseline(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-maturity-test-") as raw:
            baseline = Path(raw) / "baseline.json"
            baseline.write_text(json.dumps({"scale": "smoke"}), encoding="utf-8")
            result = performance_regression(
                MaturityContext(
                    root=Path(raw),
                    profile="operational_95",
                    phase="candidate",
                    baseline_path=baseline,
                )
            )
        self.assertFalse(result.passed)
        self.assertIn("full suite", result.error)

    def test_final_performance_requires_precomputed_result(self) -> None:
        baseline = (
            REPO_ROOT / "benchmarks/baselines/v0.5.1-linux-x86_64-python3.13.json"
        )
        result = performance_regression(
            MaturityContext(
                root=REPO_ROOT,
                profile="operational_95",
                phase="final",
                baseline_path=baseline,
            )
        )
        self.assertFalse(result.passed)
        self.assertIn("precomputed benchmark result", result.error)

    def test_precomputed_performance_rejects_wrong_source_or_dirty_result(self) -> None:
        baseline = (
            REPO_ROOT / "benchmarks/baselines/v0.5.1-linux-x86_64-python3.13.json"
        )
        with tempfile.TemporaryDirectory(prefix="design-craft-benchmark-result-") as raw:
            result_path = Path(raw) / "result.json"
            payload = json.loads(baseline.read_text(encoding="utf-8"))
            payload["source_commit"] = "0" * 40
            payload["source_dirty"] = False
            result_path.write_text(json.dumps(payload), encoding="utf-8")
            wrong_source = performance_regression(
                MaturityContext(
                    root=REPO_ROOT,
                    profile="operational_95",
                    phase="candidate",
                    baseline_path=baseline,
                    benchmark_result_path=result_path,
                )
            )
            self.assertFalse(wrong_source.passed)
            self.assertIn("match current HEAD", wrong_source.error)

            payload["source_commit"] = repository_head()
            payload["source_dirty"] = True
            result_path.write_text(json.dumps(payload), encoding="utf-8")
            dirty = performance_regression(
                MaturityContext(
                    root=REPO_ROOT,
                    profile="operational_95",
                    phase="candidate",
                    baseline_path=baseline,
                    benchmark_result_path=result_path,
                )
            )
            self.assertFalse(dirty.passed)
            self.assertIn("clean source", dirty.error)

    def test_profile_invariants(self) -> None:
        self.assertEqual(check_profile_invariants(), [])

    def test_installer_contract_is_deduplicated_only_for_development(self) -> None:
        development = load_profile("development", "candidate")
        operational = load_profile("operational_95", "candidate")

        self.assertNotIn("installer_contract", development.required_gate_ids)
        self.assertIn("installer_contract", operational.required_gate_ids)

    def test_operational_is_not_a_missing_evidence_cap(self) -> None:
        profile = load_profile("operational_95", "candidate")
        self.assertIn("host_codex_current_source", profile.required_gate_ids)
        self.assertIn("host_pi_current_source", profile.required_gate_ids)
        self.assertIn("native_ios_simulator_current_source", profile.required_gate_ids)
        self.assertIn("native_android_emulator_current_source", profile.required_gate_ids)
        self.assertIn("performance_regression", profile.required_gate_ids)

    def test_final_phase_binds_main_without_admin_only_governance(self) -> None:
        candidate = load_profile("operational_95", "candidate")
        final = load_profile("operational_95", "final")
        self.assertNotIn("main_ruleset", candidate.required_gate_ids)
        self.assertIn("main_branch", final.required_gate_ids)
        self.assertNotIn("main_ruleset", final.required_gate_ids)

    def test_final_phase_uses_committed_upstream_snapshot(self) -> None:
        candidate = load_profile("operational_95", "candidate")
        final = load_profile("operational_95", "final")
        self.assertIn("upstream_remote_review", candidate.required_gate_ids)
        self.assertNotIn("upstream_remote_review", final.required_gate_ids)
        self.assertIn("upstream_lock_parity", final.required_gate_ids)


if __name__ == "__main__":
    unittest.main()
