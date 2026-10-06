"""Regression for a disclosed aggregate that differs from product-level inputs.

Public inputs: 603667 November 2025 inquiry reply, pp. 7-1-21–22.
The audit verifies supplied arithmetic, not PDF extraction or prose semantics.
"""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/money-craft/scripts"))
from financial_rigor import audit_text, calculate


PRODUCTS = [
    ("980000", "500", "318.77"),
    ("2100000", "120", "80.06"),
    ("70000", "2170", "1540.86"),
    ("1000000", "300", "223.37"),
    ("4000000", "70", "50.37"),
]


def reconstructed_margin():
    revenue = calculate("add", [calculate("multiply", [q, p]) for q, p, _ in PRODUCTS])
    cost = calculate("add", [calculate("multiply", [q, c]) for q, _, c in PRODUCTS])
    gross = calculate("subtract", [revenue, cost])
    return calculate("multiply", [calculate("divide", [gross, revenue]), "100"])


def receipt(expected):
    return "<!-- money-craft-calc: " + json.dumps({
        "id": "C01", "operation": "subtract",
        "inputs": [str(reconstructed_margin()), "31.08"],
        "expected": str(expected), "tolerance": "0",
    }) + " -->"


class DisclosureTieTests(unittest.TestCase):
    def test_false_equality_below_one_percent_is_rejected(self):
        margin = reconstructed_margin()
        self.assertEqual(str(margin), "31.25511907185019336454304905353145")
        relative_gap = calculate("divide", [calculate("subtract", [margin, "31.08"]), "31.08"])
        self.assertLess(relative_gap, calculate("divide", ["1", "100"]))
        audit = audit_text(receipt("0"))
        self.assertFalse(audit["valid"])
        self.assertFalse(audit["checks"][0]["passed"])

    def test_honest_residual_is_valid_arithmetic_not_reconciliation(self):
        audit = audit_text(receipt("0.17511907185019336454304905353145"))
        self.assertTrue(audit["valid"], audit["errors"])
        self.assertNotEqual(audit["checks"][0]["actual"], "0")

    def test_exact_equality_control_passes(self):
        report = receipt("0").replace('"31.08"', json.dumps(str(reconstructed_margin())))
        self.assertTrue(audit_text(report)["valid"])

    def test_prose_claim_is_outside_arithmetic_audit(self):
        # Semantic review must reject this unsupported explanation even though
        # its attached residual arithmetic is correct.
        report = "差异已经证明完全来自四舍五入。\n" + receipt("0.17511907185019336454304905353145")
        self.assertTrue(audit_text(report)["valid"])


if __name__ == "__main__":
    unittest.main()
