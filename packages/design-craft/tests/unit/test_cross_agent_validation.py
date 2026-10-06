from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.evaluation.cross_agent.cli import main
from tools.design_craft.evaluation.cross_agent.contract import (
    CROSS_AGENT_CONTRACT_FILES,
    HOSTS,
    render_current_comparison,
)
from tools.design_craft.evaluation.cross_agent.output import validate_output
from tools.design_craft.evaluation.cross_agent.task import (
    observed_hosts,
    validate_observed_task,
)
from tools.design_craft.repo import REPO_ROOT


SOURCE_TASK = REPO_ROOT / "evals/cross-agent/same-prompt-dashboard-review"
CONTRACT_MODULES = {
    "tools/design_craft/evaluation/cross_agent/cli.py",
    "tools/design_craft/evaluation/cross_agent/contract.py",
    "tools/design_craft/evaluation/cross_agent/current_source.py",
    "tools/design_craft/evaluation/cross_agent/history.py",
    "tools/design_craft/evaluation/cross_agent/output.py",
    "tools/design_craft/evaluation/cross_agent/run_evidence.py",
    "tools/design_craft/evaluation/cross_agent/score.py",
    "tools/design_craft/evaluation/cross_agent/task.py",
}


def copy_definition_fixture(destination: Path) -> None:
    shutil.copytree(SOURCE_TASK, destination)
    for host in HOSTS:
        for name in (
            f"{host}-output.md",
            f"{host}-unverified.md",
            f"run.{host}.json",
            f"score.{host}.json",
        ):
            (destination / name).unlink(missing_ok=True)
    status_path = destination / "evidence-status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    for host in HOSTS:
        status["hosts"][host] = {
            "status": "pending",
            "reason": "Unit fixture has not admitted observed evidence.",
        }
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    (destination / "comparison.md").write_text(
        render_current_comparison(destination), encoding="utf-8"
    )


class CrossAgentValidationTests(unittest.TestCase):
    def test_localized_output_concepts_are_accepted(self) -> None:
        for boundary_label, move_label in (
            ("未验证", "具体设计改动"),
            ("未确认", "具体设计 moves"),
        ):
            with (
                self.subTest(boundary_label=boundary_label, move_label=move_label),
                tempfile.TemporaryDirectory() as temp_dir,
            ):
                task_dir = Path(temp_dir)
                (task_dir / "codex-output.md").write_text(
                    f"证据、{boundary_label}边界和{move_label}。" * 40,
                    encoding="utf-8",
                )

                errors = validate_output(task_dir, "codex")

            self.assertEqual(errors, [])

    def test_observed_hosts_requires_output_and_score_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_dir = Path(temp_dir)
            (task_dir / "codex-output.md").write_text("output\n", encoding="utf-8")
            self.assertEqual(observed_hosts(task_dir), set())
            (task_dir / "score.codex.json").write_text("{}\n", encoding="utf-8")

            observed = observed_hosts(task_dir)

        self.assertEqual(observed, {"codex"})

    def test_definition_without_observed_artifacts_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_dir = Path(temp_dir) / SOURCE_TASK.name
            copy_definition_fixture(task_dir)

            errors = validate_observed_task(task_dir)

        self.assertEqual(errors, [])

    def test_partial_observed_artifact_pair_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_dir = Path(temp_dir) / SOURCE_TASK.name
            copy_definition_fixture(task_dir)
            (task_dir / "cursor-output.md").write_text(
                "Evidence, unverified boundaries, and design moves. " * 20,
                encoding="utf-8",
            )

            errors = validate_observed_task(task_dir)

        self.assertTrue(any("score.cursor.json" in error for error in errors))

    def test_cli_rejects_observed_only_options_without_task(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as exc:
            main(["--require-host", "codex"])

        self.assertEqual(exc.exception.code, 2)
        self.assertIn("require --observed-task", stderr.getvalue())

    def test_evidence_contract_includes_all_admission_modules(self) -> None:
        self.assertTrue(CONTRACT_MODULES.issubset(CROSS_AGENT_CONTRACT_FILES))


if __name__ == "__main__":
    unittest.main()
