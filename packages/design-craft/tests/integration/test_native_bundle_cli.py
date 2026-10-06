from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.design_craft.cli import main
from tools.design_craft.release.github_runs import (
    BENCHMARK_WORKFLOW_NAME,
    BENCHMARK_WORKFLOW_PATH,
    PHYSICAL_WORKFLOW_NAME,
    PHYSICAL_WORKFLOW_PATH,
)
from tools.design_craft.release.integrity import repository_version


HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
VERSION = repository_version()


class NativeBundleCliTests(unittest.TestCase):
    def test_benchmark_run_observation_uses_tag_bound_contract(self) -> None:
        run = {
            "id": 789,
            "attempt": 1,
            "workflow": BENCHMARK_WORKFLOW_PATH,
            "workflow_name": BENCHMARK_WORKFLOW_NAME,
            "event": "workflow_dispatch",
            "head_branch": f"v{VERSION}",
            "head_sha": HEAD,
            "status": "completed",
            "conclusion": "success",
            "url": "https://github.com/example/design-craft/actions/runs/789",
            "repository": "example/design-craft",
        }
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "benchmark.json"
            with patch(
                "tools.design_craft.release.cli.observe_run", return_value=run
            ), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                exit_code = main(
                    [
                        "release",
                        "run-observation",
                        "--kind",
                        "benchmark",
                        "--run-id",
                        "789",
                        "--output",
                        str(output),
                    ]
                )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["kind"], "benchmark")
            self.assertEqual(payload["run"], run)

    def test_run_observation_writes_an_exact_non_overwriting_document(self) -> None:
        run = {
            "id": 456,
            "attempt": 1,
            "workflow": PHYSICAL_WORKFLOW_PATH,
            "workflow_name": PHYSICAL_WORKFLOW_NAME,
            "event": "workflow_dispatch",
            "head_branch": "main",
            "head_sha": HEAD,
            "status": "completed",
            "conclusion": "success",
            "url": "https://github.com/example/design-craft/actions/runs/456",
            "repository": "example/design-craft",
        }
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "physical.json"
            with patch(
                "tools.design_craft.release.cli.observe_run", return_value=run
            ), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                exit_code = main(
                    [
                        "release",
                        "run-observation",
                        "--kind",
                        "physical",
                        "--run-id",
                        "456",
                        "--output",
                        str(output),
                    ]
                )
                second_exit = main(
                    [
                        "release",
                        "run-observation",
                        "--kind",
                        "physical",
                        "--run-id",
                        "456",
                        "--output",
                        str(output),
                    ]
                )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(second_exit, 1)
            self.assertEqual(payload["run"], run)
            self.assertEqual(payload["source_commit"], HEAD)

    def test_missing_bundle_is_a_semantic_failure_with_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "release",
                        "native-bundle",
                        "validate",
                        "--output-dir",
                        str(Path(raw) / "missing"),
                        "--json",
                    ]
                )
            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 1)
            self.assertFalse(payload["ok"])

    def test_build_missing_required_sources_is_a_usage_error(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            main(
                [
                    "release",
                    "native-bundle",
                    "build",
                    "--native-observation",
                    "native.json",
                ]
            )
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("required", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
