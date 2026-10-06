"""Domain-focused Creative Craft regression tests."""

from __future__ import annotations

import copy
import unittest

from support import (
    ROOT,
    cc,
    load,
)


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load("examples/premium-haircare-launch/evaluation.json")
        self.graph = cc.validate_project(ROOT / "examples/premium-haircare-launch")

    def test_scored(self) -> None:
        result = cc.score_evaluation(self.data, self.graph)
        self.assertEqual("scored", result["status"])
        self.assertEqual(100.0, result["coverage"])
        self.assertGreater(result["score"], 80)

    def test_blocked_gate(self) -> None:
        ledger = self.graph.record("asset-ledger", "northstar-assets-v1")
        ledger["data"]["assets"][0]["rights_status"] = "UNVERIFIED"
        result = cc.score_evaluation(self.data, self.graph)
        self.assertEqual("blocked", result["status"])
        self.assertIn("rights_clear", result["failed_gates"])

    def test_withheld_for_low_coverage(self) -> None:
        data = copy.deepcopy(self.data)
        for dim in data["dimensions"][2:]:
            dim["evidence_state"] = "UNVERIFIED"
            dim["evidence_refs"] = []
        result = cc.score_evaluation(data, self.graph)
        self.assertEqual("withheld", result["status"])
        self.assertLess(result["coverage"], 80)

    def test_v2_hypotheses_reduce_strength_and_confidence(self) -> None:
        data = load("examples/premium-haircare-launch/evaluation.json")
        graph = cc.validate_project(ROOT / "examples/premium-haircare-launch")
        for dimension in data["dimensions"]:
            dimension["evidence_state"] = "HYPOTHESIZED"
        result = cc.score_evaluation(data, graph)
        self.assertEqual("scored", result["status"])
        self.assertEqual(100.0, result["coverage"])
        self.assertEqual(40.0, result["evidence_strength"])
        self.assertEqual("WEAK", result["confidence"])

    def test_v2_gate_is_derived_from_project_evidence(self) -> None:
        data = load("examples/premium-haircare-launch/evaluation.json")
        graph = cc.validate_project(ROOT / "examples/premium-haircare-launch")
        graph.record("brief", "northstar-airlift-launch-v1")["data"]["status"] = "draft"
        result = cc.score_evaluation(data, graph)
        self.assertEqual("blocked", result["status"])
        self.assertIn("brief_locked", result["failed_gates"])

    @staticmethod
    def add_output_chain(
        graph: cc.ProjectGraph,
        *,
        job_id: str,
        receipt_id: str,
        inspection_id: str,
        asset_id: str,
    ) -> None:
        output_sha = "a" * 64
        graph.records[("execution-receipt", receipt_id)] = {
            "data": {
                "schema_version": "creative-craft.execution-receipt.v1",
                "receipt_id": receipt_id,
                "job_id": job_id,
                "outcome": "succeeded",
                "outputs": [{"asset_id": asset_id, "sha256": output_sha}],
            }
        }
        graph.records[("output-inspection", inspection_id)] = {
            "data": {
                "schema_version": "creative-craft.output-inspection.v1",
                "inspection_id": inspection_id,
                "job_id": job_id,
                "receipt_id": receipt_id,
                "output_asset_id": asset_id,
                "output_sha256": output_sha,
                "decision": "approved",
            }
        }

    def test_output_gate_does_not_borrow_another_jobs_inspection(self) -> None:
        data = copy.deepcopy(self.data)
        data["stage"] = "output"
        data["target_ref"] = "cc://video/northstar-motion-proof-vertical-15s-v1#"
        self.add_output_chain(
            self.graph,
            job_id="northstar-motion-proof-hero-image-v1",
            receipt_id="receipt-unrelated-image",
            inspection_id="inspection-unrelated-image",
            asset_id="output-unrelated-image",
        )

        result = cc.score_evaluation(data, self.graph)

        self.assertEqual("blocked", result["status"])
        self.assertFalse(result["gate_status"]["actual_output_observed"])
        self.assertIn("actual_output_observed", result["failed_gates"])

    def test_output_gate_accepts_only_matching_job_receipt_output_inspection_chain(
        self,
    ) -> None:
        data = copy.deepcopy(self.data)
        data["stage"] = "output"
        data["target_ref"] = "cc://video/northstar-motion-proof-vertical-15s-v1#"
        self.add_output_chain(
            self.graph,
            job_id="northstar-motion-proof-vertical-15s-v1",
            receipt_id="receipt-target-video",
            inspection_id="inspection-target-video",
            asset_id="output-target-video",
        )

        result = cc.score_evaluation(data, self.graph)

        self.assertEqual("scored", result["status"])
        self.assertTrue(result["gate_status"]["target_compatible"])
        self.assertTrue(result["gate_status"]["actual_output_observed"])

    def test_delivery_gate_rejects_job_target_as_incompatible(self) -> None:
        data = copy.deepcopy(self.data)
        data["stage"] = "delivery"
        data["target_ref"] = "cc://video/northstar-motion-proof-vertical-15s-v1#"
        self.add_output_chain(
            self.graph,
            job_id="northstar-motion-proof-vertical-15s-v1",
            receipt_id="receipt-target-video",
            inspection_id="inspection-target-video",
            asset_id="output-target-video",
        )

        result = cc.score_evaluation(data, self.graph)

        self.assertEqual("blocked", result["status"])
        self.assertIn("target_compatible", result["failed_gates"])


class ArtifactSemanticTests(unittest.TestCase):
    def test_legacy_contracts_remain_readable(self) -> None:
        for name in ("image-job-v1", "video-job-v1", "evaluation-v1", "delivery-v1"):
            data = load(f"tests/fixtures/legacy/{name}.json")
            _, result = cc.validate_data(data)
            self.assertTrue(result.ok, f"{name}: {result.errors}")

    def test_approved_inspection_requires_decisive_checks(self) -> None:
        inspection = load("skills/creative-craft/templates/output-inspection.json")
        inspection.update(
            {
                "decision": "approved",
                "inspector": "reviewer",
                "inspected_at": "2026-08-04T00:00:00Z",
                "approval": {
                    "approved_by": "owner",
                    "approved_at": "2026-08-04T00:01:00Z",
                    "approval_basis": "Reviewed output.",
                },
            }
        )
        _, result = cc.validate_data(inspection)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("requires invariant_checks" in item for item in result.errors)
        )

    def test_unique_items_uses_json_deep_equality(self) -> None:
        schema = {
            "type": "array",
            "uniqueItems": True,
        }
        result = cc.Result()
        cc._validate_schema_node(
            [{"nested": [1]}, {"nested": [1.0]}], schema, schema, (), result
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("unique items" in item for item in result.errors))

        distinct = cc.Result()
        cc._validate_schema_node([True, 1], schema, schema, (), distinct)
        self.assertTrue(distinct.ok, distinct.errors)

        reordered_object = cc.Result()
        cc._validate_schema_node(
            [{"a": 1, "b": [2]}, {"b": [2.0], "a": 1.0}],
            schema,
            schema,
            (),
            reordered_object,
        )
        self.assertFalse(reordered_object.ok)

        signed_zero = cc.Result()
        cc._validate_schema_node([0, -0.0], schema, schema, (), signed_zero)
        self.assertFalse(signed_zero.ok)

    def test_reference_binding_duplicate_selection_is_structurally_rejected(
        self,
    ) -> None:
        binding = load("skills/creative-craft/templates/reference-binding.json")
        binding["selected_reference_ids"] = ["reference-tbd", "reference-tbd"]

        _, result = cc.validate_data(binding)

        self.assertFalse(result.ok)
        self.assertTrue(any("unique items" in item for item in result.errors))


class LifecycleSemanticTests(unittest.TestCase):
    def test_receipt_timestamps_require_timezone_and_never_raise_for_mixed_values(
        self,
    ) -> None:
        receipt = load("skills/creative-craft/templates/execution-receipt.json")
        cases = (
            ("2026-08-05T00:00:00Z", "2026-08-05T00:00:01"),
            ("2026-08-05T00:00:00", "2026-08-05T00:00:01Z"),
            ("not-a-time", "2026-08-05T00:00:01Z"),
            ("2026-08-05T00:00:02Z", "2026-08-05T00:00:01Z"),
        )
        for started_at, completed_at in cases:
            with self.subTest(started_at=started_at, completed_at=completed_at):
                specimen = copy.deepcopy(receipt)
                specimen["started_at"] = started_at
                specimen["completed_at"] = completed_at
                _, result = cc.validate_data(specimen)
                self.assertFalse(result.ok)

    def test_timestamp_offsets_are_normalized_to_utc_before_ordering(self) -> None:
        receipt = load("skills/creative-craft/templates/execution-receipt.json")
        receipt["started_at"] = "2026-08-05T08:00:00+08:00"
        receipt["completed_at"] = "2026-08-05T00:00:01Z"

        _, result = cc.validate_data(receipt)

        self.assertTrue(result.ok, result.errors)

    def test_approved_inspection_rejects_naive_or_reverse_approval_timestamp(
        self,
    ) -> None:
        check = {
            "id": "check-1",
            "status": "pass",
            "observation": "Synthetic observation.",
            "interpretation": "Synthetic interpretation.",
        }
        inspection = load("skills/creative-craft/templates/output-inspection.json")
        inspection.update(
            {
                "decision": "approved",
                "inspector": "reviewer",
                "inspected_at": "2026-08-05T00:00:02Z",
                "invariant_checks": [check],
                "technical_checks": [{**check, "id": "check-2"}],
                "rights_checks": [{**check, "id": "check-3"}],
                "approval": {
                    "approved_by": "owner",
                    "approved_at": "2026-08-05T00:00:01",
                    "approval_basis": "Synthetic review.",
                },
            }
        )

        _, naive = cc.validate_data(inspection)
        self.assertFalse(naive.ok)

        inspection["approval"]["approved_at"] = "2026-08-05T00:00:01Z"
        _, reverse = cc.validate_data(inspection)
        self.assertFalse(reverse.ok)
        self.assertTrue(any("at or after" in item for item in reverse.errors))
