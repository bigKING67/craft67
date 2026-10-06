from __future__ import annotations

import sys
import unittest
from unittest import mock

from tools.design_craft.validation.model import GateResult, GateSpec
from tools.design_craft.validation.runner import run_gates


def gate(
    gate_id: str,
    code: str,
    *,
    execution: str = "parallel",
    depends_on: tuple[str, ...] = (),
    priority: int = 0,
) -> GateSpec:
    return GateSpec(
        gate_id=gate_id,
        command=(sys.executable, "-c", code),
        profiles=frozenset({"portable"}),
        timeout_seconds=5,
        execution=execution,
        priority=priority,
        depends_on=depends_on,
    )


class ValidationRunnerTests(unittest.TestCase):
    def test_nonzero_exit_is_observable(self) -> None:
        result = run_gates((gate("failure", "raise SystemExit(7)"),))[0]
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.exit_code, 7)
        self.assertEqual(result.error_code, "NONZERO_EXIT")

    def test_serial_dependency_failure_skips_gate(self) -> None:
        results = run_gates(
            (
                gate("failure", "raise SystemExit(1)"),
                gate(
                    "dependent",
                    "raise SystemExit('must not execute')",
                    execution="serial",
                    depends_on=("failure",),
                ),
            )
        )
        self.assertEqual(results[1].status, "skipped")
        self.assertEqual(results[1].error_code, "DEPENDENCY_FAILED")

    def test_parallel_priority_changes_start_order_not_result_order(self) -> None:
        started: list[str] = []

        def fake_run(spec: GateSpec) -> GateResult:
            started.append(spec.gate_id)
            return GateResult(spec.gate_id, "passed", 0, 0.0, "", "")

        gates = (
            gate("low", "", priority=0),
            gate("high", "", priority=10),
        )
        with mock.patch(
            "tools.design_craft.validation.runner.run_gate", side_effect=fake_run
        ):
            results = run_gates(gates, jobs=1)

        self.assertEqual(started, ["high", "low"])
        self.assertEqual([result.gate_id for result in results], ["low", "high"])


if __name__ == "__main__":
    unittest.main()
