from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.evaluation.cross_agent.contract import (
    HOSTS,
    render_current_comparison,
)
from tools.design_craft.repo import REPO_ROOT


def run_script(script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script, *arguments],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


class EvaluationCliTests(unittest.TestCase):
    def test_cross_agent_recorder_help_loads_current_validation_modules(self) -> None:
        result = run_script("scripts/design_craft_cross_agent_record.py", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Record a cryptographically bound cross-agent score", result.stdout)

    def test_active_cross_agent_comparisons_match_evidence_status(self) -> None:
        result = run_script(
            "scripts/design_craft_cross_agent_validate.py",
            "--root",
            "evals/cross-agent",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cross_agent_comparison_drift_is_rejected(self) -> None:
        source = REPO_ROOT / "evals/cross-agent/same-prompt-dashboard-review"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "cross-agent"
            task = root / source.name
            shutil.copytree(source, task)
            (task / "comparison.md").write_text("# drift\n", encoding="utf-8")

            result = run_script(
                "scripts/design_craft_cross_agent_validate.py",
                "--root",
                str(root),
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "must be generated exactly from evidence-status.json", result.stderr
        )

    def test_observed_task_requires_an_observed_host(self) -> None:
        source = REPO_ROOT / "evals/cross-agent/same-prompt-dashboard-review"
        with tempfile.TemporaryDirectory() as temp_dir:
            task = Path(temp_dir) / source.name
            shutil.copytree(source, task)
            for host in HOSTS:
                for name in (
                    f"{host}-output.md",
                    f"run.{host}.json",
                    f"score.{host}.json",
                ):
                    (task / name).unlink(missing_ok=True)
            status_path = task / "evidence-status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            for host in HOSTS:
                status["hosts"][host] = {
                    "status": "pending",
                    "reason": "Temporary fixture has not admitted current observed evidence.",
                }
            status_path.write_text(
                json.dumps(status, indent=2) + "\n", encoding="utf-8"
            )
            (task / "comparison.md").write_text(
                render_current_comparison(task), encoding="utf-8"
            )

            result = run_script(
                "scripts/design_craft_cross_agent_validate.py",
                "--observed-task",
                str(task),
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("at least one observed host", result.stderr)

    def test_cross_agent_modes_are_mutually_exclusive(self) -> None:
        result = run_script(
            "scripts/design_craft_cross_agent_validate.py",
            "--check",
            "--observed-task",
            "/definitely/missing",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with argument", result.stderr)

    def test_comparative_semantic_failure_uses_exit_one(self) -> None:
        result = run_script(
            "scripts/design_craft_comparative_validate.py",
            "--root",
            "/definitely/missing",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("at least one comparative case", result.stderr)

    def test_comparative_check_does_not_swallow_another_mode(self) -> None:
        result = run_script(
            "scripts/design_craft_comparative_validate.py",
            "--check",
            "--case-dir",
            "/definitely/missing",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with argument", result.stderr)

    def test_comparative_definitions_only_ignores_stale_observed_artifacts(self) -> None:
        source = REPO_ROOT / "evals/comparative/emil-motion-ablation"
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir) / source.name
            shutil.copytree(source, case_dir)
            run_path = case_dir / "run.baseline.json"
            run = json.loads(run_path.read_text(encoding="utf-8"))
            run["schema"] = "design-craft.comparative-run.stale"
            run_path.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")

            definitions = run_script(
                "scripts/design_craft_comparative_validate.py",
                "--case-dir",
                str(case_dir),
                "--definitions-only",
            )
            observed = run_script(
                "scripts/design_craft_comparative_validate.py",
                "--case-dir",
                str(case_dir),
                "--require-observed",
            )

        self.assertEqual(definitions.returncode, 0, definitions.stderr)
        self.assertEqual(observed.returncode, 1)
        self.assertIn("current evidence must use", observed.stderr)

    def test_comparative_definitions_only_rejects_observed_mode(self) -> None:
        result = run_script(
            "scripts/design_craft_comparative_validate.py",
            "--definitions-only",
            "--require-observed",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--definitions-only is not valid", result.stderr)

    def test_comparative_blind_rejects_stale_scorecard_before_outputs(self) -> None:
        source = REPO_ROOT / "evals/comparative/emil-motion-ablation"
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir) / source.name
            shutil.copytree(source, case_dir)
            for name in ("blind-packet.md", "blind-map.json"):
                (case_dir / name).unlink(missing_ok=True)
            (case_dir / "scorecard.md").write_text("# drift\n", encoding="utf-8")

            result = run_script(
                "scripts/design_craft_comparative_blind.py",
                "--case-dir",
                str(case_dir),
                "--seed",
                "fixture",
            )

            self.assertFalse((case_dir / "blind-packet.md").exists())
            self.assertFalse((case_dir / "blind-map.json").exists())

        self.assertEqual(result.returncode, 2)
        self.assertIn(
            "scorecard.md must be generated exactly from scorecard.json",
            result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
