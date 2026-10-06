from __future__ import annotations

import unittest
from unittest.mock import patch

from tools.design_craft.quality.report import build_quality_report


def check(check_id: str, status: str) -> dict[str, object]:
    return {"id": check_id, "status": status, "evidence": {}, "error": ""}


class QualityReportTests(unittest.TestCase):
    def test_domains_remain_independent_without_composite_score(self) -> None:
        evidence = {
            "schema": "design-craft.release-evidence.v1",
            "source_commit": "a" * 40,
            "verified_hosts": ["codex", "pi"],
            "verified_native": ["ios_simulator", "android_emulator"],
            "unverified": ["cursor", "claude", "physical_device"],
            "ok": False,
            "checks": [
                check("contract_completeness", "passed"),
                check("operational_maturity", "passed"),
                check("performance_regression", "failed"),
                check("comparative_evaluation", "passed"),
                check("host_codex_current_source", "passed"),
                check("host_pi_current_source", "passed"),
                check("native_ios_simulator_current_source", "passed"),
                check("native_android_emulator_current_source", "passed"),
                check("clean_worktree", "failed"),
                check("install_provenance", "failed"),
                check("upstream_remote_review", "failed"),
            ],
        }
        with patch(
            "tools.design_craft.quality.report.evaluate_release",
            return_value=evidence,
        ):
            report = build_quality_report(
                baseline_path=None,
                release_level="operational_95",
            )

        self.assertEqual(report["schema"], "design-craft.quality-report.v1")
        self.assertEqual(
            report["metric_policy"],
            "independent_domains_no_composite_score",
        )
        self.assertNotIn("score", report)
        self.assertEqual(
            report["domains"]["contract_completeness"]["status"],
            "passed",
        )
        self.assertEqual(
            report["domains"]["performance_regression"]["status"],
            "incomplete",
        )
        self.assertEqual(
            report["domains"]["release_certification"]["status"],
            "incomplete",
        )
        self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
