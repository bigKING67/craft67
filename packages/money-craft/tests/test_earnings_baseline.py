from __future__ import annotations
import copy
import datetime as dt
from unittest.mock import patch
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from test_earnings_update import example_update, CLI
import earnings_baseline as baseline
import earnings_update as eu


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        update, _ = example_update(self.root)
        expectation = {"metric": "revenue", "origin": "analyst", "rationale": "Synthetic test forecast",
                       "period_start": update["current"]["start"], "period_end": update["current"]["end"],
                       "kind": "annual", "accounting_basis": "PRC GAAP", "unit": "CNY", "value": "100",
                       "as_of": "2026-02-15", "source_refs": [{"source_id": "S03", "locator": "test fixture"}]}
        self.preview = {"schema": "money-craft.earnings-preview.v1", "security_id": update["security_id"],
                        "currency": "CNY", "as_of": "2026-02-15", "sources": {"S03": update["sources"]["S03"]},
                        "expectations": [expectation], "catalysts": [{"id": "C01", "window_start": "2026-03-01",
                        "window_end": "2026-03-31", "impact_path": "sales -> earnings", "confirmation_condition": "sales improve",
                        "invalidation_condition": "sales weaken", "next_evidence": "segment actuals", "decision_condition": "review H01 if margin weakens",
                        "source_refs": expectation["source_refs"]}]}
        self.outcome = {"schema": "money-craft.earnings-outcome.v1", "security_id": update["security_id"], "currency": "CNY",
                        "as_of": "2026-04-01", "sources": update["sources"], "actual": update["current"],
                        "first_actual_disclosure": {"date": "2026-03-20", "source_refs": [{"source_id": "S02", "locator": "test disclosure"}]},
                        "catalyst_observations": {}}
        self.input = self.root / "preview.json"
        self.sealed = self.root / "sealed.json"
        self.actual = self.root / "outcome.json"

    def seal(self):
        self.input.write_text(json.dumps(self.preview))
        return baseline.seal(self.input, self.sealed)

    def replay(self):
        self.actual.write_text(json.dumps(self.outcome))
        return baseline.replay(self.sealed, self.actual)

    def test_reconstructed_history_preserves_original_and_emits_tasks(self):
        self.seal()
        original = self.sealed.read_bytes()
        result = self.replay()
        self.assertEqual(result["timing"], "RECONSTRUCTED_AFTER_DISCLOSURE")
        self.assertEqual(result["catalysts"][0]["state"], "OVERDUE_UNVERIFIED")
        self.assertEqual(result["research_tasks"][0]["status"], "OPEN_REQUIRES_REVIEW")
        self.assertEqual(original, self.sealed.read_bytes())

    def test_cannot_overwrite_seal(self):
        self.seal()
        with self.assertRaises(eu.EarningsError): self.seal()

    def test_baseline_tampering_rejected(self):
        self.seal()
        data = json.loads(self.sealed.read_text())
        data["preview"]["expectations"][0]["value"] = "900"
        self.sealed.write_text(json.dumps(data))
        with self.assertRaises(eu.EarningsError): self.replay()

    def test_changed_evidence_rejected(self):
        self.seal()
        (self.root / "S03.txt").write_text("rewritten forecast")
        with self.assertRaises(eu.EarningsError): self.replay()

    def test_future_source_rejected(self):
        self.preview["expectations"][0]["as_of"] = "2026-02-14"
        with self.assertRaises(eu.EarningsError): self.seal()

    def test_origins_preserved_separately(self):
        extra = copy.deepcopy(self.preview["expectations"][0])
        extra.update(origin="management", value="110")
        self.preview["expectations"].append(extra)
        self.seal()
        self.assertEqual(len(self.replay()["comparisons"]), 2)

    def test_invalid_expectation_window_rejected_before_seal(self):
        for kind, start, end in (("annual", "2025-01-01", "2025-01-01"),
                                 ("quarter", "2025-01-01", "2025-12-31"),
                                 ("ytd", "2024-01-01", "2025-12-31")):
            with self.subTest(kind=kind):
                self.sealed = self.root / (kind + "-sealed.json")
                self.preview["expectations"][0].update(kind=kind, period_start=start, period_end=end)
                with self.assertRaises(eu.EarningsError):
                    self.seal()
                self.assertFalse(self.sealed.exists())

    def test_mixed_period_rejected(self):
        self.seal()
        self.outcome["actual"]["kind"] = "ytd"
        with self.assertRaises(eu.EarningsError): self.replay()

    def test_event_does_not_confirm_thesis(self):
        self.seal()
        self.outcome["catalyst_observations"]["C01"] = {"state": "OCCURRED", "observed_on": "2026-03-20",
                "source_refs": [{"source_id": "S02", "locator": "disclosure"}], "rationale": "filing appeared"}
        result = self.replay()
        self.assertEqual(result["catalysts"][0]["state"], "OCCURRED")
        self.assertEqual(result["catalysts"][0]["thesis_support"], "UNVERIFIED")

    def test_observation_future_source_rejected(self):
        self.seal()
        self.outcome["catalyst_observations"]["C01"] = {"state": "OCCURRED", "observed_on": "2026-03-19",
                "source_refs": [{"source_id": "S02", "locator": "disclosure"}], "rationale": "filing appeared"}
        with self.assertRaises(eu.EarningsError): self.replay()

    def test_late_preview_rejected(self):
        self.preview["as_of"] = "2026-03-20"
        self.seal()
        with self.assertRaises(eu.EarningsError): self.replay()

    def test_locally_sealed_before_disclosure(self):
        class PreviewClock(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 3, 1, tzinfo=dt.timezone.utc)
        with patch.object(baseline.dt, "datetime", PreviewClock):
            self.seal()
        self.assertEqual(self.replay()["timing"], "LOCAL_SEALED_BEFORE_DISCLOSURE")

    def test_cancellation_needs_evidence(self):
        self.seal()
        self.outcome["catalyst_observations"]["C01"] = {"state": "CANCELLED", "observed_on": "2026-03-20",
                "source_refs": [], "rationale": "cancelled"}
        with self.assertRaises(eu.EarningsError): self.replay()
        self.outcome["catalyst_observations"]["C01"]["source_refs"] = [{"source_id": "S02", "locator": "cancellation fixture"}]
        self.assertEqual(self.replay()["catalysts"][0]["state"], "CANCELLED")

    def test_false_first_disclosure_date_rejected(self):
        self.seal()
        self.outcome["first_actual_disclosure"]["date"] = "2026-03-21"
        with self.assertRaises(eu.EarningsError): self.replay()

    def test_restatement_requires_reconciliation(self):
        self.seal()
        self.outcome["actual"]["basis"] = "restated"
        with self.assertRaises(eu.EarningsError): self.replay()

    def test_local_civil_date_can_be_ahead_of_utc(self):
        class ChinaClock(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                instant = cls(2026, 9, 14, 16, 30, tzinfo=dt.timezone.utc)
                return instant.astimezone(tz or dt.timezone(dt.timedelta(hours=8)))
            def astimezone(self, tz=None):
                return super().astimezone(tz or dt.timezone(dt.timedelta(hours=8)))
        self.preview["as_of"] = "2026-09-15"
        with patch.object(baseline.dt, "datetime", ChinaClock):
            self.assertEqual(baseline.calendar_today().isoformat(), "2026-09-15")
            self.seal()

    def test_inspect_without_actuals(self):
        self.seal()
        result = baseline.inspect_baseline(self.sealed)
        self.assertEqual(result["actual_disclosure_status"], "UNVERIFIED_NO_OUTCOME_PROVIDED")
        self.assertEqual(result["research_tasks"][0]["state"], "OVERDUE_UNVERIFIED")
        (self.root / "S03.txt").write_text("changed")
        with self.assertRaises(eu.EarningsError): baseline.inspect_baseline(self.sealed)

    def test_local_disclosure_day_is_not_prior_day_forecast(self):
        class DisclosureClock(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                instant = cls(2026, 3, 19, 16, 30, tzinfo=dt.timezone.utc)
                return instant.astimezone(tz or dt.timezone(dt.timedelta(hours=8)))
            def astimezone(self, tz=None):
                return super().astimezone(tz or dt.timezone(dt.timedelta(hours=8)))
        with patch.object(baseline.dt, "datetime", DisclosureClock):
            self.seal()
        self.assertEqual(self.replay()["timing"], "RECONSTRUCTED_AFTER_DISCLOSURE")

    def test_missing_linked_model_fails_before_publish(self):
        self.preview["linked_model_hashes"] = {"model-input.json": "0" * 64}
        with self.assertRaises(eu.EarningsError): self.seal()
        self.assertFalse(self.sealed.exists())

    def test_publish_failure_leaves_no_partial_baseline(self):
        with patch.object(baseline.os, "link", side_effect=OSError("synthetic publish failure")):
            with self.assertRaises(eu.EarningsError): self.seal()
        self.assertFalse(self.sealed.exists())
        self.assertEqual(list(self.root.glob(".preview-*")), [])
        self.seal()
        self.assertTrue(baseline.inspect_baseline(self.sealed)["valid"])

    def test_cli(self):
        self.input.write_text(json.dumps(self.preview))
        self.actual.write_text(json.dumps(self.outcome))
        import sys
        for args in (["seal-preview", "--input", str(self.input), "--output", str(self.sealed)],
                     ["replay-preview", "--input", str(self.actual), "--baseline", str(self.sealed)],
                     ["inspect-preview", "--baseline", str(self.sealed)]):
            result = subprocess.run([sys.executable, str(CLI), "earnings", *args, "--json"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)["valid"])

if __name__ == "__main__": unittest.main()
