from __future__ import annotations

import json
import subprocess
import sys
import unittest
from copy import deepcopy

from scripts.complexity_budget import evaluate_budget
from tests.support import ROOT


class ComplexityBudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = {
            "schema": "review-craft.complexity-budget.v2",
            "runtimeRoots": ["runtime"],
            "defaultMaximum": 15,
            "ceilings": [
                {"path": "runtime/a.py", "function": "strict", "maximum": 8}
            ],
            "debtExceptions": [
                {
                    "path": "runtime/b.py",
                    "function": "legacy",
                    "observed": 18,
                    "targetMaximum": 15,
                    "removeByVersion": "v0.7.0",
                }
            ],
        }
        self.measured = {
            ("runtime/a.py", "strict"): 8,
            ("runtime/b.py", "legacy"): 18,
        }

    def test_complexity_budget_is_enforced_for_core_functions(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/complexity_budget.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["valid"])
        self.assertGreaterEqual(len(payload["functions"]), 9)
        self.assertGreater(payload["scannedFunctions"], len(payload["functions"]))

    def test_unlisted_global_regression_fails(self) -> None:
        measured = {**self.measured, ("runtime/new.py", "complex"): 16}
        errors, _ = evaluate_budget(self.contract, measured)
        self.assertTrue(any("exceeds global maximum" in error for error in errors))

    def test_debt_growth_and_stale_improvement_both_fail(self) -> None:
        for actual, fragment in ((19, "exceeds debt ceiling"), (17, "stale debt exception")):
            with self.subTest(actual=actual):
                measured = {**self.measured, ("runtime/b.py", "legacy"): actual}
                errors, _ = evaluate_budget(self.contract, measured)
                self.assertTrue(any(fragment in error for error in errors))

    def test_debt_exception_must_be_removed_at_global_limit(self) -> None:
        measured = {**self.measured, ("runtime/b.py", "legacy"): 15}
        errors, _ = evaluate_budget(self.contract, measured)
        self.assertTrue(any("stale debt exception" in error for error in errors))

    def test_duplicate_and_missing_entries_fail(self) -> None:
        contract = deepcopy(self.contract)
        contract["debtExceptions"].append(
            {
                "path": "runtime/a.py",
                "function": "strict",
                "observed": 18,
                "targetMaximum": 15,
                "removeByVersion": "v0.7.0",
            }
        )
        contract["ceilings"].append(
            {"path": "runtime/missing.py", "function": "missing", "maximum": 8}
        )
        errors, _ = evaluate_budget(contract, self.measured)
        self.assertTrue(any("duplicate complexity entry" in error for error in errors))
        self.assertTrue(any("function was not measured" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
