from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.benchmark_runtime import sha256_json
from tests.support import ROOT

BENCHMARK = ROOT / "scripts/benchmark_runtime.py"


class BenchmarkTests(unittest.TestCase):
    def test_malformed_benchmark_document_fails_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result_path = Path(directory) / "result.json"
            result_path.write_text("[]\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(BENCHMARK),
                    "validate",
                    "--result",
                    str(result_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("validation failed", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    def test_small_runtime_benchmark_and_relative_comparison_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result_path = Path(directory) / "result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(BENCHMARK),
                    "run",
                    "--sizes",
                    "20",
                    "--repetitions",
                    "1",
                    "--warmups",
                    "0",
                    "--no-git",
                    "--output",
                    str(result_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["parameters"]["sizes"], [20])
            self.assertEqual(payload["measurements"][0]["fileCount"], 20)
            self.assertEqual(
                set(payload["measurements"][0]["operations"]),
                set(json.loads((ROOT / "benchmarks/specs/runtime.json").read_text())["operations"]),
            )
            self.assertEqual(
                payload["measurements"][0]["operations"]["preflight"]["memoryScope"],
                "NOT_CAPTURED_FOR_SUBPROCESS",
            )
            summary = payload["measurements"][0]["operations"]["inventory"]["summary"]
            self.assertGreater(summary["p50FilesPerSecond"], 0)
            self.assertGreater(
                payload["measurements"][0]["operations"]["inventory"]["samples"][0][
                    "processPeakRssBytes"
                ],
                0,
            )
            validated = subprocess.run(
                [
                    sys.executable,
                    str(BENCHMARK),
                    "validate",
                    "--result",
                    str(result_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)

            compared = subprocess.run(
                [
                    sys.executable,
                    str(BENCHMARK),
                    "compare",
                    "--baseline",
                    str(result_path),
                    "--result",
                    str(result_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(compared.returncode, 0, compared.stderr)
            self.assertTrue(json.loads(compared.stdout)["valid"])

            regressed_path = Path(directory) / "regressed.json"
            regressed = copy.deepcopy(payload)
            regressed["measurements"][0]["operations"]["inventory"]["summary"]["p50WallMs"] *= 2
            regressed["contentSha256"] = sha256_json(
                {key: value for key, value in regressed.items() if key != "contentSha256"}
            )
            regressed_path.write_text(json.dumps(regressed) + "\n", encoding="utf-8")
            failed = subprocess.run(
                [
                    sys.executable,
                    str(BENCHMARK),
                    "compare",
                    "--baseline",
                    str(result_path),
                    "--result",
                    str(regressed_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(failed.returncode, 1, failed.stderr)
            self.assertFalse(json.loads(failed.stdout)["valid"])

    def test_relative_performance_gate_covers_pull_requests_and_main_pushes(self) -> None:
        workflow = (ROOT / ".github/workflows/benchmark.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("pull_request:\n", workflow)
        self.assertIn("push:\n    branches: [main]", workflow)
        self.assertIn("github.event_name == 'push'", workflow)
        self.assertIn("github.event.before || github.sha", workflow)
        self.assertIn("--max-regression-percent 20", workflow)


if __name__ == "__main__":
    unittest.main()
