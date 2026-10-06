from __future__ import annotations

import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.design_craft.validation.maturity.model import MaturityGateResult
from tools.design_craft.validation.maturity.runner import evaluate_maturity


class MaturityRunnerTests(unittest.TestCase):
    def test_performance_gate_runs_after_parallel_gates(self) -> None:
        events: list[str] = []

        def fake_gate_runner(gate_id: str):
            def evaluate(_context):
                events.append(f"{gate_id}:start")
                if gate_id == "parallel":
                    time.sleep(0.01)
                events.append(f"{gate_id}:end")
                return MaturityGateResult(gate_id, "passed", 0.0, {}, "")

            return evaluate

        profile = SimpleNamespace(
            required_gate_ids=("parallel", "performance_regression")
        )
        with (
            patch(
                "tools.design_craft.validation.maturity.runner.load_profile",
                return_value=profile,
            ),
            patch(
                "tools.design_craft.validation.maturity.runner.gate_runner",
                side_effect=fake_gate_runner,
            ),
        ):
            result = evaluate_maturity("operational_95", root=Path.cwd(), jobs=2)

        self.assertTrue(result["ok"])
        self.assertLess(
            events.index("parallel:end"),
            events.index("performance_regression:start"),
        )


if __name__ == "__main__":
    unittest.main()
