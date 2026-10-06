from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from decimal import Decimal, localcontext
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import financial_rigor  # noqa: E402
import financial_reconciliation  # noqa: E402
import report_audit  # noqa: E402


VALID_REPORT = """---
schema: money-craft.report.v1
workflow: research
security: Test Company
thscode: 600519.SH
as_of: 2026-08-23
data_cutoff: 2026-08-23T12:00:00+08:00
base_currency: CNY
provider_status: unavailable
---
# Test Company
## 结论
The evidence is bounded.
## 事实与证据
- 经营现金流同比下降 -1.72% [S01]
- 收入由独立来源复核 [S02]
## 估值与假设
Scenario inputs remain uncertain.
<!-- money-craft-calc: {"id":"C01","operation":"add","inputs":["-1.72","1"],"expected":"-0.72","tolerance":"0.000001"} -->
## 风险与反方证据
The strongest counterargument is retained.
## 证伪条件
Official facts materially change.
## 来源索引
- [S01] https://example.invalid/filing
- [S02] `captures/S02/capture.json`
"""


class ReportAuditTests(unittest.TestCase):
    def test_source_target_cannot_borrow_next_line_or_disappear(self):
        for candidate in (VALID_REPORT.replace('- [S01] https://example.invalid/filing',
                         '- [S01]\nAn unrelated https://example.invalid/unrelated appears here'),
                         VALID_REPORT + '- [S03]\n'):
            result = report_audit.audit_text(candidate)
            self.assertFalse(result["valid"])
            self.assertTrue(any("source target is missing" in error for error in result["errors"]))

    def test_citations_after_source_index_are_checked(self):
        for heading in ("## 来源索引", "##   来源索引", "##\t来源索引"):
            with self.subTest(heading=heading):
                text = VALID_REPORT.replace("## 来源索引", heading) + "\n## 补充说明\n收入依据 [S99]\n"
                result = report_audit.audit_text(text)
                self.assertFalse(result["valid"])
                self.assertIn("unresolved source citation: S99", result["errors"])

    def test_source_definitions_do_not_count_as_citations(self):
        text = VALID_REPORT.replace("## 来源索引", "##\t来源索引")
        text += "- [S03] https://example.invalid/unused\n"
        result = report_audit.audit_text(text)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["citation_count"], 2)
        self.assertIn("unused source definition: S03", result["warnings"])

    def test_as_of_requires_canonical_calendar_date(self):
        for date in ("20260823", "2026-W34-7"):
            with self.subTest(date=date):
                result = report_audit.audit_text(VALID_REPORT.replace("as_of: 2026-08-23", "as_of: " + date))
                self.assertFalse(result["valid"])
                self.assertIn("as_of must be YYYY-MM-DD", result["errors"])

    def test_valid_report_with_negative_number(self) -> None:
        result = report_audit.audit_text(VALID_REPORT)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["source_count"], 2)

    def test_unresolved_source_fails(self) -> None:
        text = VALID_REPORT.replace("[S02]", "[S03]", 1)
        result = report_audit.audit_text(text)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unresolved source citation: S03" in error for error in result["errors"]))

    def test_template_placeholder_fails(self) -> None:
        result = report_audit.audit_text(VALID_REPORT.replace("Test Company", "{{security}}", 1))
        self.assertFalse(result["valid"])
        self.assertTrue(any("unresolved template placeholders" in error for error in result["errors"]))

    def test_data_cutoff_requires_timezone(self) -> None:
        result = report_audit.audit_text(
            VALID_REPORT.replace("2026-08-23T12:00:00+08:00", "2026-08-23T12:00:00")
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("data_cutoff" in error for error in result["errors"]))

    def test_duplicate_source_definition_fails(self) -> None:
        result = report_audit.audit_text(
            VALID_REPORT.replace(
                "- [S02] `captures/S02/capture.json`",
                "- [S01] `captures/S02/capture.json`",
            )
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("duplicate source definitions" in error for error in result["errors"]))


class FinancialAuditTests(unittest.TestCase):
    def test_multiline_receipts_are_evaluated(self):
        receipt = {"id": "C01", "operation": "add", "inputs": ["1", "2"], "expected": "3"}
        result = financial_rigor.audit_text("<!-- money-craft-calc: " + json.dumps(receipt, indent=2) + " -->")
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(len(result["checks"]), 1)
        receipt["expected"] = "9"
        self.assertFalse(financial_rigor.audit_text("<!-- money-craft-calc: " + json.dumps(receipt, indent=2) + " -->")["valid"])

    def test_malformed_receipts_cannot_hide_beside_valid_receipt(self):
        for marker in ("<!-- money-craft-calc: [] -->", "<!-- money-craft-calc: broken -->",
                       '<!-- money-craft-calc: {"id":"C02"}'):
            with self.subTest(marker=marker):
                result = financial_rigor.audit_text(VALID_REPORT + "\n" + marker)
                self.assertFalse(result["valid"])
                self.assertTrue(result["errors"])

    def test_calculation_id_length_contract(self):
        import re
        schema = json.loads((ROOT / 'skills/money-craft/schemas/financial-reconciliation.schema.json').read_text())
        pattern = schema['$defs']['calculation']['properties']['id']['pattern']
        for identifier, expected in [('C01', True), ('C10000', True), ('C9999999', True), ('C10000000', False), ('C1', False)]:
            receipt = dict(id=identifier, operation='add', inputs=['1','2'], expected='3', tolerance='0')
            result = financial_rigor.audit_text('<!-- money-craft-calc: '+json.dumps(receipt)+' -->')
            self.assertEqual(result['valid'], expected, identifier)
            self.assertEqual(bool(re.fullmatch(pattern, identifier)), expected, identifier)
            payload = reconciliation_payload()
            payload['period_basis'][1].update(basis='comparable-estimate', calculation=receipt)
            self.assertEqual(financial_reconciliation.audit_payload(payload)['valid'], expected, identifier)

    def test_calculations_ignore_ambient_decimal_precision(self):
        with localcontext() as context:
            context.prec = 6
            self.assertEqual(financial_rigor.calculate("add", ["1234567.89", "0.01"]), Decimal("1234567.90"))
            expected = financial_rigor.CONTEXT.divide(Decimal("1"), Decimal("1234567.89"))
            self.assertEqual(financial_rigor.relative_error(Decimal("1234568.89"), Decimal("1234567.89")), expected)

    def test_exact_negative_receipt(self) -> None:
        result = financial_rigor.audit_text(VALID_REPORT)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["checks"][0]["actual"], "-0.72")

    def test_wrong_expected_value_fails(self) -> None:
        result = financial_rigor.audit_text(VALID_REPORT.replace('"expected":"-0.72"', '"expected":"0.72"'))
        self.assertFalse(result["valid"])
        self.assertFalse(result["checks"][0]["passed"])

    def test_weighted_average(self) -> None:
        result = financial_rigor.calculate("weighted_average", ["10", "2", "20", "1"])
        self.assertEqual(result, financial_rigor.decimal_value("13.33333333333333333333333333333333"))

    def test_nonfinite_decimal_values_are_rejected(self) -> None:
        for value in ("NaN", "sNaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(financial_rigor.CalculationError, "must be finite"):
                    financial_rigor.decimal_value(value)

    def test_invalid_tolerances_are_audit_failures(self) -> None:
        for tolerance, expected_error in (
            ("-0.01", "tolerance must be between 0 and 0.05"),
            ("NaN", "decimal value must be finite"),
            ("Infinity", "decimal value must be finite"),
            ("-Infinity", "decimal value must be finite"),
        ):
            with self.subTest(tolerance=tolerance):
                receipt = {
                    "id": "C01",
                    "operation": "add",
                    "inputs": ["1", "1"],
                    "expected": "2",
                    "tolerance": tolerance,
                }
                result = financial_rigor.audit_text(
                    f"<!-- money-craft-calc: {json.dumps(receipt)} -->"
                )
                self.assertFalse(result["valid"])
                self.assertEqual(result["checks"], [])
                self.assertIn(expected_error, result["errors"][0])

    def test_nonfinite_expected_value_is_an_audit_failure(self) -> None:
        receipt = {
            "id": "C01",
            "operation": "add",
            "inputs": ["1", "1"],
            "expected": "Infinity",
            "tolerance": "0.01",
        }
        result = financial_rigor.audit_text(f"<!-- money-craft-calc: {json.dumps(receipt)} -->")
        self.assertFalse(result["valid"])
        self.assertEqual(result["checks"], [])
        self.assertIn("decimal value must be finite", result["errors"][0])

    def test_arithmetic_overflow_is_a_visible_failure(self) -> None:
        with self.assertRaisesRegex(financial_rigor.CalculationError, "multiply calculation failed"):
            financial_rigor.calculate("multiply", ["1e999999", "10"])

        receipt = {
            "id": "C01",
            "operation": "multiply",
            "inputs": ["1e999999", "10"],
            "expected": "1",
            "tolerance": "0.01",
        }
        result = financial_rigor.audit_text(f"<!-- money-craft-calc: {json.dumps(receipt)} -->")
        self.assertFalse(result["valid"])
        self.assertEqual(result["checks"], [])
        self.assertIn("multiply calculation failed", result["errors"][0])


def reconciliation_payload() -> dict[str, object]:
    return {
        "schema": "money-craft.financial-reconciliation.v1",
        "security": "Test Company",
        "thscode": "600519.SH",
        "as_of": "2026-08-23",
        "base_currency": "CNY",
        "required_checks": ["balance-sheet-equation", "cash-balance-tie", "quarter-from-ytd"],
        "period_basis": [
            {
                "role": "current",
                "period": "2026-2",
                "basis": "reported",
                "source_ids": ["S11"],
                "notes": "Current period uses the formal filing.",
            },
            {
                "role": "comparison",
                "period": "2025-2",
                "basis": "restated",
                "source_ids": ["S11", "S12"],
                "notes": "Comparison period uses the restated column.",
            },
        ],
        "restatement_assessment": {
            "status": "restated",
            "source_ids": ["S11", "S12"],
            "notes": "The filing retrospectively restates the comparison period.",
        },
        "material_disclosure_assessment": [
            {
                "source_id": "S18",
                "status": "not-triggered",
                "notes": "No decision-critical transaction or capital-structure trigger was identified.",
            },
            {
                "source_id": "S19",
                "status": "not-triggered",
                "notes": "Management Q&A was not required for a decision-critical claim.",
            },
            {
                "source_id": "S20",
                "status": "imported",
                "notes": "A material post-reporting-period financing disclosure was imported.",
            },
        ],
        "checks": [
            {
                "id": "FR01",
                "kind": "balance-sheet-equation",
                "period": "2026-2",
                "unit": "CNY million",
                "inputs": {"assets": "100", "liabilities": "40", "equity": "60"},
                "tolerance": "0.000001",
                "source_ids": ["S11"],
            },
            {
                "id": "FR02",
                "kind": "cash-balance-tie",
                "period": "2026-2",
                "unit": "CNY million",
                "inputs": {"balance_sheet_cash": "25", "cash_flow_ending_cash": "25"},
                "tolerance": "0.000001",
                "source_ids": ["S11"],
            },
            {
                "id": "FR03",
                "kind": "quarter-from-ytd",
                "period": "2026-2",
                "unit": "CNY million",
                "inputs": {"current_ytd": "80", "previous_period_ytd": "30", "reported_quarter": "50"},
                "tolerance": "0.000001",
                "source_ids": ["S11", "S16"],
            },
        ],
        "presentation_to_economics": {
            "status": "items-identified",
            "source_ids": ["S11"],
            "notes": "One non-cash presentation item is material.",
            "items": [
                {
                    "id": "P01",
                    "topic": "Fair-value loss",
                    "accounting_presentation": "Recorded below operating profit.",
                    "operating_interpretation": "Does not represent current-period customer demand.",
                    "cash_effect": "Non-cash in the current period.",
                    "evidence_state": "OBSERVED",
                    "source_ids": ["S11"],
                }
            ],
        },
        "subsequent_events": {
            "status": "identified",
            "source_ids": ["S20"],
            "notes": "A material financing occurred after period end.",
            "items": [
                {
                    "id": "E01",
                    "event": "Convertible financing",
                    "materiality": "May dilute equity holders.",
                    "research_effect": "Update the fully diluted valuation.",
                    "evidence_state": "OBSERVED",
                    "source_ids": ["S20"],
                }
            ],
        },
    }


class FinancialReconciliationTests(unittest.TestCase):
    def test_cash_bridge_preserves_raw_balance_and_requires_all_components(self):
        payload = reconciliation_payload()
        check = payload["checks"][1]
        check["inputs"]["cash_flow_ending_cash"] = "30"
        self.assertFalse(financial_reconciliation.audit_payload(payload)["valid"])
        check["cash_adjustments"] = [
            {"id": "CA01", "amount": "-10", "reason": "Remove restricted deposits, note 4.", "source_ids": ["S11"]},
            {"id": "CA02", "amount": "15", "reason": "Eligible interbank deposits, note 5.", "source_ids": ["S11"]},
        ]
        result = financial_reconciliation.audit_payload(payload)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["checks"][1]["balance_sheet_cash"], "25")
        self.assertEqual(result["checks"][1]["lhs"], "30")
        check["cash_adjustments"].pop()
        self.assertFalse(financial_reconciliation.audit_payload(payload)["valid"])

    def test_cash_bridge_rejects_invalid_or_unbound_adjustments(self):
        for field, value in [("amount", True), ("amount", "NaN"), ("amount", []), ("reason", ""), ("source_ids", []), ("source_ids", ["S99"]), ("id", [])]:
            with self.subTest(field=field, value=value):
                payload = reconciliation_payload()
                adjustment = {"id": "CA01", "amount": "0", "reason": "Disclosed component, note 4.", "source_ids": ["S11"]}
                adjustment[field] = value
                payload["checks"][1]["cash_adjustments"] = [adjustment]
                result = financial_reconciliation.audit_payload(payload, allowed_source_ids={"S11", "S12", "S16", "S20"})
                self.assertFalse(result["valid"])

    def test_cash_bridge_rejects_wrong_kind_duplicate_ids_and_empty_list(self):
        adjustment = {"id": "CA01", "amount": "0", "reason": "Disclosed component, note 4.", "source_ids": ["S11"]}
        for index, values in [(0, [adjustment]), (1, [adjustment, adjustment]), (1, []), (1, None)]:
            payload = reconciliation_payload()
            payload["checks"][index]["cash_adjustments"] = values
            self.assertFalse(financial_reconciliation.audit_payload(payload)["valid"])

    def test_json_numbers_preserve_decimal_difference(self):
        payload = reconciliation_payload()
        payload["checks"][1]["inputs"].update(balance_sheet_cash="1.00000000000000000001", cash_flow_ending_cash="1")
        payload["checks"][1]["tolerance"] = "0"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(payload).replace('"1.00000000000000000001"', '1.00000000000000000001'))
            self.assertFalse(financial_reconciliation.audit_file(path)["valid"])

    def test_malformed_enum_values_are_structured_failures(self):
        for field in ("kind", "required_checks", "role", "basis", "restatement", "presentation"):
            for bad in ([], {}):
                with self.subTest(field=field, bad=bad):
                    payload = reconciliation_payload()
                    if field == "kind": payload["checks"][0]["kind"] = bad
                    elif field == "required_checks": payload[field] = [bad]
                    elif field in ("role", "basis"): payload["period_basis"][0][field] = bad
                    elif field == "restatement": payload["restatement_assessment"]["status"] = bad
                    else: payload["presentation_to_economics"]["status"] = bad
                    with tempfile.TemporaryDirectory() as directory:
                        path = Path(directory) / "input.json"
                        path.write_text(json.dumps(payload))
                        result = financial_reconciliation.audit_file(path, expected_contract=reconciliation_payload())
                    self.assertFalse(result["valid"])
                    self.assertTrue(result["errors"])

    def test_quarter_check_must_use_current_period(self):
        payload = reconciliation_payload()
        payload["checks"][2]["period"] = "2025-2"
        self.assertFalse(financial_reconciliation.audit_payload(payload)["valid"])

    @unittest.skipUnless(hasattr(sys, "get_int_max_str_digits") and 0 < sys.get_int_max_str_digits() < 5000,
                         "requires enabled standard integer parsing limit")
    def test_oversized_integer_is_a_structured_json_error(self):
        giant = "1" * 5000
        result = financial_rigor.audit_text('<!-- money-craft-calc: {"id":"C01","expected":' + giant + '} -->')
        self.assertFalse(result["valid"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text('{"value":' + giant + '}')
            self.assertFalse(financial_reconciliation.audit_file(path)["valid"])

    def test_check_period_must_belong_to_declared_basis(self):
        payload = reconciliation_payload()
        payload["checks"][0]["period"] = "1999-1"
        result = financial_reconciliation.audit_payload(payload)
        self.assertFalse(result["valid"])
        self.assertTrue(any("period_basis" in error for error in result["errors"]))

    def test_statement_overflow_is_a_structured_failure(self):
        payload = reconciliation_payload()
        payload["checks"][0]["inputs"].update(assets="9e999999", liabilities="9e999999", equity="9e999999")
        result = financial_reconciliation.audit_payload(payload)
        self.assertFalse(result["valid"])
        self.assertTrue(any("calculation failed" in error for error in result["errors"]))

    def test_restatement_and_statement_ties_pass(self) -> None:
        result = financial_reconciliation.audit_payload(reconciliation_payload())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual([item["passed"] for item in result["checks"]], [True, True, True])

    def test_mixed_basis_and_failed_cash_tie_are_visible(self) -> None:
        payload = reconciliation_payload()
        payload["period_basis"][1]["basis"] = "unverified"
        payload["checks"][1]["inputs"]["cash_flow_ending_cash"] = "20"
        result = financial_reconciliation.audit_payload(payload)
        self.assertFalse(result["valid"])
        self.assertTrue(any("basis must be resolved" in item for item in result["errors"]))
        self.assertTrue(any("cash-balance-tie does not reconcile" in item for item in result["errors"]))

    def test_research_contract_rejects_unknown_source_and_removed_quarter_check(self) -> None:
        payload = reconciliation_payload()
        payload["checks"][2]["source_ids"] = ["S99"]
        payload["required_checks"] = ["balance-sheet-equation", "cash-balance-tie"]
        contract = {
            "required_checks": ["balance-sheet-equation", "cash-balance-tie", "quarter-from-ytd"],
            "material_disclosure_source_ids": ["S18", "S19", "S20"],
            "period_basis": [
                {"role": "current", "period": "2026-2"},
                {"role": "comparison", "period": "2025-2"},
            ],
        }
        result = financial_reconciliation.audit_payload(
            payload,
            expected_contract=contract,
            allowed_source_ids={"S11", "S12", "S16", "S20"},
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("required_checks must match plan.json" in item for item in result["errors"]))
        self.assertTrue(any("outside available research evidence" in item for item in result["errors"]))

    def test_comparable_estimate_requires_reproducible_calculation(self) -> None:
        payload = reconciliation_payload()
        payload["period_basis"][1]["basis"] = "comparable-estimate"
        missing = financial_reconciliation.audit_payload(payload)
        self.assertFalse(missing["valid"])
        self.assertTrue(any("calculation is required" in item for item in missing["errors"]))
        payload["period_basis"][1]["calculation"] = {
            "id": "C02",
            "operation": "subtract",
            "inputs": ["100", "10"],
            "expected": "90",
            "tolerance": "0.000001",
        }
        valid = financial_reconciliation.audit_payload(payload)
        self.assertTrue(valid["valid"], valid["errors"])
        self.assertEqual(valid["checks"][0]["kind"], "comparable-estimate")

    def test_cli_audits_reconciliation_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "financial-reconciliation.json"
            path.write_text(json.dumps(reconciliation_payload(), ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "money_craft.py"),
                    "audit",
                    "reconciliation",
                    str(path),
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertTrue(json.loads(completed.stdout)["valid"])

    def test_reconciliation_artifact_rejects_secret_like_material(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "financial-reconciliation.json"
            payload = reconciliation_payload()
            payload["restatement_assessment"]["notes"] = "sk-" + "fuyao-" + "abcdefghijklmnop"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = financial_reconciliation.audit_file(path)
        self.assertFalse(result["valid"])
        self.assertTrue(any("secret-like" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
