from __future__ import annotations

import io
import json
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import patch

from tools.design_craft.validation.cli import run_validate
from tools.design_craft.validation.model import GateResult


def result(
    gate_id: str,
    duration_ms: float,
    *,
    status: str = "passed",
    stdout_summary: str = "",
    stderr_summary: str = "",
) -> GateResult:
    return GateResult(
        gate_id=gate_id,
        status=status,
        exit_code=0 if status == "passed" else 1,
        duration_ms=duration_ms,
        stdout_summary=stdout_summary,
        stderr_summary=stderr_summary,
    )


class ValidationCliTests(unittest.TestCase):
    def test_json_reports_wall_time_separately_from_gate_time_sum(self) -> None:
        args = Namespace(profile="portable", list=False, json=True, jobs=0)
        output = io.StringIO()
        with (
            patch("tools.design_craft.validation.cli.load_registry", return_value=()),
            patch("tools.design_craft.validation.cli.select_gates", return_value=()),
            patch("tools.design_craft.validation.cli.require_profile_contract"),
            patch(
                "tools.design_craft.validation.cli.run_gates",
                return_value=(result("one", 700.0), result("two", 800.0)),
            ),
            patch(
                "tools.design_craft.validation.cli.time.perf_counter",
                side_effect=(10.0, 11.0),
            ),
            redirect_stdout(output),
        ):
            exit_code = run_validate(args)

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema"], "design-craft.validation-run.v2")
        self.assertEqual(payload["duration_ms"], 1000.0)
        self.assertEqual(payload["gate_duration_sum_ms"], 1500.0)

    def test_human_failure_falls_back_to_stdout_diagnostics(self) -> None:
        args = Namespace(profile="contracts", list=False, json=False, jobs=0)
        output = io.StringIO()
        failed = result(
            "stdout-failure",
            10.0,
            status="failed",
            stdout_summary="observable failure",
        )
        with (
            patch("tools.design_craft.validation.cli.load_registry", return_value=()),
            patch("tools.design_craft.validation.cli.select_gates", return_value=()),
            patch("tools.design_craft.validation.cli.require_profile_contract"),
            patch("tools.design_craft.validation.cli.run_gates", return_value=(failed,)),
            patch(
                "tools.design_craft.validation.cli.time.perf_counter",
                side_effect=(10.0, 10.1),
            ),
            redirect_stdout(output),
        ):
            exit_code = run_validate(args)

        self.assertEqual(exit_code, 1)
        self.assertIn("observable failure", output.getvalue())


if __name__ == "__main__":
    unittest.main()
