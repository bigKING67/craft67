from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
TEMPLATE_ROOT = ROOT / "skills" / "money-craft" / "templates"
TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(TEST_DIR))

import earnings_update  # noqa: E402
import tracking_workflow as tracking  # noqa: E402
from test_tracking_workflow import INITIAL_UPDATE, thesis_text  # noqa: E402


SECURITY_ID = "CN-SH:600519"
CLI = ROOT / "skills" / "money-craft" / "scripts" / "money_craft.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_ref(source_id: str) -> list[dict[str, str]]:
    return [{"source_id": source_id, "locator": "p. 42, consolidated statement"}]


def snapshot(
    *,
    start: str,
    end: str,
    values: dict[str, str],
    source_id: str,
    basis: str = "reported",
) -> dict[str, object]:
    return {
        "start": start,
        "end": end,
        "kind": "annual",
        "accounting_basis": "PRC GAAP",
        "basis": basis,
        "metrics": {
            metric: {
                "value": value,
                "unit": "shares" if metric == "shares" else "CNY",
                "source_refs": source_ref(source_id),
            }
            for metric, value in values.items()
        },
    }


def scenario(*, factor: str, pe: str, rationale: str) -> dict[str, str]:
    return {"earnings_factor": factor, "pe": pe, "fx": "1", "rationale": rationale}


def example_update(base: Path) -> tuple[dict[str, object], Path]:
    """A source-bound adjacent-year review suitable for schema consumers and tests."""
    base.mkdir(parents=True, exist_ok=True)
    source_specs = {
        "S01": ("previous annual report", "2025-03-20", "prior annual actuals"),
        "S02": ("current annual report", "2026-03-20", "current annual actuals"),
        "S03": ("dated consensus", "2026-02-15", "consensus before disclosure"),
    }
    sources: dict[str, dict[str, str]] = {}
    for source_id, (title, published_on, contents) in source_specs.items():
        path = base / f"{source_id}.txt"
        path.write_text(contents, encoding="utf-8")
        sources[source_id] = {
            "security_id": SECURITY_ID,
            "title": title,
            "url": f"https://issuer.example/{source_id}.pdf",
            "published_on": published_on,
            "local_path": path.name,
            "sha256": sha256(path),
        }

    previous_thesis = base / "audited-previous-thesis.md"
    previous_thesis.write_text(
        thesis_text(
            as_of="2026-08-23",
            cutoff="2026-08-23T12:00:00+08:00",
            hypothesis_state="UNVERIFIED",
            update_rows=[INITIAL_UPDATE],
        ).replace("thscode: 600519.SH", f"security_id: {SECURITY_ID}"),
        encoding="utf-8",
    )
    payload: dict[str, object] = {
        "schema": earnings_update.INPUT_SCHEMA,
        "security_id": SECURITY_ID,
        "currency": "CNY",
        "as_of": "2026-09-01",
        "sources": sources,
        "previous": snapshot(
            start="2024-01-01", end="2024-12-31",
            values={"revenue": "100", "net_income": "20", "operating_cash_flow": "25", "shares": "10"},
            source_id="S01",
        ),
        "current": snapshot(
            start="2025-01-01", end="2025-12-31",
            values={"revenue": "120", "net_income": "30", "operating_cash_flow": "40", "shares": "12"},
            source_id="S02",
        ),
        "comparison_basis": "unchanged",
        "valuation": {
            "method": "earnings_multiple",
            "currency": "CNY",
            "previous": {
                "bear": scenario(factor="0.8", pe="10", rationale="prior downside"),
                "base": scenario(factor="1", pe="15", rationale="prior central case"),
                "bull": scenario(factor="1.2", pe="20", rationale="prior upside"),
            },
            "current": {
                "bear": scenario(factor="0.9", pe="12", rationale="current downside"),
                "base": scenario(factor="1.1", pe="18", rationale="current central case"),
                "bull": scenario(factor="1.3", pe="25", rationale="current upside"),
            },
        },
        "thesis_updates": {
            "hypotheses": {"H01": {"status": "SUPPORTED", "rationale": "profit and cash flow improved", "source_refs": source_ref("S02")}},
            "red_lines": {"R01": {"status": "WATCH", "rationale": "monitor quality despite improvement", "source_refs": source_ref("S02")}},
        },
    }
    return payload, previous_thesis


class EarningsUpdateTests(unittest.TestCase):
    def build(self, base: Path) -> tuple[dict[str, object], Path, dict[str, object]]:
        payload, previous = example_update(base)
        return payload, previous, earnings_update.build_update(payload, base=base, previous_thesis=previous)

    def test_adjacent_year_metrics_and_three_scenario_bridge_close(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload, _, result = self.build(Path(directory))
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["metrics"]["revenue"]["change_pct"], "20.0")
            valuation = result["valuation"]
            self.assertEqual(valuation["driver_order"], ["net_income", "earnings_factor", "pe", "shares", "fx"])
            for scenario_name in ("bear", "base", "bull"):
                bridge = valuation["scenarios"][scenario_name]
                self.assertEqual(len(bridge["bridge"]), 5)
                self.assertEqual(sum(Decimal(item["contribution"]) for item in bridge["bridge"]), Decimal(bridge["change"]))
                self.assertEqual(Decimal(bridge["rounding_residual"]), Decimal(0))
                self.assertNotEqual(bridge["previous_inputs"]["net_income"], bridge["current_inputs"]["net_income"])
                self.assertNotEqual(bridge["previous_inputs"]["shares"], bridge["current_inputs"]["shares"])
            self.assertEqual(payload["valuation"]["currency"], valuation["currency"])

    def test_unverified_comparison_blocks_calculations_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous = example_update(base)
            payload["comparison_basis"] = "unverified"
            result = earnings_update.build_update(payload, base=base, previous_thesis=previous)
            self.assertFalse(result["valid"])
            self.assertEqual(result["metrics"], {})
            self.assertIsNone(result["valuation"])
            self.assertIsNone(result["tracking_handoff"])
            self.assertIn("UNVERIFIED", result["errors"][0])

    def test_restated_comparison_does_not_rewrite_frozen_prior_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous = example_update(base)
            payload["comparison_basis"] = "restated"
            payload["restatement_reason"] = "issuer restated the comparative column"
            comparable = copy.deepcopy(payload["previous"])
            comparable["basis"] = "restated"
            comparable["metrics"]["net_income"]["value"] = "18"
            comparable["metrics"]["revenue"]["value"] = "95"
            payload["comparable_previous"] = comparable
            result = earnings_update.build_update(payload, base=base, previous_thesis=previous)
            self.assertTrue(result["valid"])
            self.assertEqual(result["metrics"]["net_income"]["previous"], "18")
            self.assertEqual(result["restatement"]["adjustments"]["net_income"]["change"], "-2")
            for item in result["valuation"]["scenarios"].values():
                self.assertEqual(item["previous_inputs"]["net_income"], "20")

    def test_future_research_date_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous = example_update(base)
            payload["as_of"] = "2099-01-01"
            with self.assertRaises(earnings_update.EarningsError):
                earnings_update.build_update(payload, base=base, previous_thesis=previous)

    def test_rejects_unbound_or_incomparable_financial_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous = example_update(base)
            cases = {
                "source_hash": lambda p: p["sources"]["S02"].update(sha256="0" * 64),
                "missing_locator": lambda p: p["current"]["metrics"]["revenue"]["source_refs"][0].update(locator=""),
                "currency": lambda p: p["current"]["metrics"]["revenue"].update(unit="USD"),
                "period": lambda p: p["current"].update(start="2025-02-01"),
            }
            for label, mutate in cases.items():
                with self.subTest(label=label):
                    candidate = copy.deepcopy(payload)
                    mutate(candidate)
                    with self.assertRaises(earnings_update.EarningsError):
                        earnings_update.build_update(candidate, base=base, previous_thesis=previous)

    def test_expectations_require_pre_disclosure_evidence_and_are_optional(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous = example_update(base)
            no_expectation = earnings_update.build_update(payload, base=base, previous_thesis=previous)
            self.assertEqual(no_expectation["expectation_status"], "UNAVAILABLE_NO_BEAT_OR_MISS_CLAIM")
            self.assertEqual(no_expectation["expectations"], [])
            payload["expectations"] = [{
                "metric": "revenue", "period_start": "2025-01-01", "period_end": "2025-12-31", "unit": "CNY", "value": "110",
                "kind": payload["current"]["kind"], "accounting_basis": payload["current"]["accounting_basis"],
                "as_of": "2026-03-20", "source_refs": source_ref("S02"),
            }]
            payload["first_actual_disclosure"] = {"date": "2026-03-20", "source_refs": source_ref("S02")}
            with self.assertRaisesRegex(earnings_update.EarningsError, "predate"):
                earnings_update.build_update(payload, base=base, previous_thesis=previous)

    def test_expectation_window_and_first_disclosure_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); payload, previous = example_update(base)
            payload["expectations"] = [{"metric": "revenue", "period_start": "2025-01-01", "period_end": "2025-12-31",
                "unit": "CNY", "value": "110", "kind": payload["current"]["kind"], "accounting_basis": payload["current"]["accounting_basis"],
                "as_of": "2026-02-15", "source_refs": source_ref("S03")}]
            with self.assertRaises(earnings_update.EarningsError):
                earnings_update.build_update(payload, base=base, previous_thesis=previous)
            payload["first_actual_disclosure"] = {"date": "2026-03-20", "source_refs": source_ref("S02")}
            valid = earnings_update.build_update(payload, base=base, previous_thesis=previous)
            self.assertEqual(valid["expectations"][0]["relation"], "above")
            quarter = copy.deepcopy(payload)
            quarter["expectations"][0].update(period_start="2025-10-01", kind="quarter")
            with self.assertRaisesRegex(earnings_update.EarningsError, "fiscal window"):
                earnings_update.build_update(quarter, base=base, previous_thesis=previous)
            early = copy.deepcopy(payload)
            early["sources"]["S04"] = {**early["sources"]["S02"], "published_on": "2026-01-31", "title": "Earlier actual-result disclosure"}
            early["first_actual_disclosure"] = {"date": "2026-01-31", "source_refs": source_ref("S04")}
            with self.assertRaisesRegex(earnings_update.EarningsError, "predate"):
                earnings_update.build_update(early, base=base, previous_thesis=previous)

    def test_proposal_cannot_override_recorded_prior_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); payload, previous = example_update(base)
            payload["thesis_updates"]["hypotheses"]["H01"]["previous"] = "SUPPORTED"
            with self.assertRaisesRegex(earnings_update.EarningsError, "reserved"):
                earnings_update.build_update(payload, base=base, previous_thesis=previous)

    def test_proposal_has_all_ids_and_never_writes_the_previous_thesis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous = example_update(base)
            before = previous.read_bytes()
            result = earnings_update.build_update(payload, base=base, previous_thesis=previous)
            handoff = result["tracking_handoff"]
            self.assertEqual(handoff["status"], "PROPOSED_REQUIRES_REVIEW")
            self.assertEqual(set(handoff["updates"]["hypotheses"]), {"H01"})
            self.assertEqual(set(handoff["updates"]["red_lines"]), {"R01"})
            self.assertEqual(previous.read_bytes(), before)
            incomplete = copy.deepcopy(payload)
            incomplete["thesis_updates"]["hypotheses"] = {}
            with self.assertRaisesRegex(earnings_update.EarningsError, "cover every existing ID"):
                earnings_update.build_update(incomplete, base=base, previous_thesis=previous)

    def test_nonpositive_comparison_base_has_no_misleading_percentage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous = example_update(base)
            payload["previous"]["metrics"]["revenue"]["value"] = "-100"
            result = earnings_update.build_update(payload, base=base, previous_thesis=previous)
            revenue = result["metrics"]["revenue"]
            self.assertIsNone(revenue["change_pct"])
            self.assertEqual(revenue["percentage_basis"], "not_meaningful_for_nonpositive_prior")

    def test_loss_makes_earnings_multiple_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous = example_update(base)
            payload["current"]["metrics"]["net_income"]["value"] = "-1"
            with self.assertRaisesRegex(earnings_update.EarningsError, "not valid for losses"):
                earnings_update.build_update(payload, base=base, previous_thesis=previous)

    def test_cli_success_and_schema_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous = example_update(base)
            input_path = base / "update.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            command = [sys.executable, str(CLI), "earnings", "review", "--input", str(input_path), "--previous-thesis", str(previous), "--json"]
            success = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertTrue(json.loads(success.stdout)["valid"])
            payload["comparison_basis"] = "unverified"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            failed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(json.loads(failed.stdout)["valid"])

    def test_result_plan_can_be_researched_then_sealed_and_verified_in_tracking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload, previous, result = self.build(base)
            root = base / "tracking"
            initialized = tracking.initialize_tracking(
                root, as_of=payload["as_of"], previous=previous, template_root=TEMPLATE_ROOT,
            )
            workspace = Path(initialized["workspace"])
            plan = json.loads((workspace / "update-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan, result["tracking_handoff"]["update_plan"])

            researcher_candidate = thesis_text(
                as_of=payload["as_of"], cutoff="2026-09-01T12:00:00+08:00",
                hypothesis_state="SUPPORTED",
                update_rows=[INITIAL_UPDATE, "| 2026-09-01 | H01 转为 SUPPORTED | 更新估值 | 研究者确认 | [S02] |"],
            ).replace("thscode: 600519.SH", f"security_id: {SECURITY_ID}")
            (workspace / "thesis.md").write_text(researcher_candidate, encoding="utf-8")
            card = (workspace / "card.md").read_text(encoding="utf-8")
            (workspace / "card.md").write_text(re.sub(r"\{\{[^{}]+\}\}", "研究者确认", card), encoding="utf-8")
            state = json.loads((workspace / "state.json").read_text(encoding="utf-8"))
            state.update(as_of=payload["as_of"], data_cutoff="2026-09-01T12:00:00+08:00", hypotheses={"H01": "SUPPORTED"})
            state["health"] = {"score": 10, "maximum": 10, "status": "SUPPORTED", "formula": "10 - 0 adverse states"}
            state["next_mandatory_review"] = {"event": "next annual report", "required_workflow": "earnings-review then track init/check"}
            (workspace / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            sealed = tracking.finalize_tracking(workspace)
            self.assertEqual(sealed["tracking_revision"], "t0001")
            verified = tracking.verify_tracking(root)
            self.assertTrue(verified["valid"], verified["errors"])


if __name__ == "__main__":
    unittest.main()
