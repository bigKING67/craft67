from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT


LIB_DIR = REPO_ROOT / "skills/design-craft/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from design_craft import reference_contract  # noqa: E402


def card(card_id: str, *, status: str = "reviewed", origin: str | None = None) -> dict:
    origin_url = origin or f"https://{card_id}.example/"
    reviewed = status in {
        "reviewed",
        "exemplar_only",
        "rejected",
        "stale",
        "project_validated",
    }
    return {
        "schema": reference_contract.CARD_SCHEMA,
        "id": card_id,
        "status": status,
        "source": {
            "provider": "fixture",
            "issue_date": "2026-08-10",
            "post_url": f"https://reference.example/2026/08/10/{card_id}",
            "observed_at": "2026-08-17",
            "source_sha256": "a" * 64,
        },
        "origin": {
            "url": origin_url,
            "domain": origin_url.split("//", 1)[1].rstrip("/"),
            "title": card_id,
            "source_description": "Synthetic reference fixture.",
        },
        "classification": {
            "source_surface": "marketing-site" if reviewed else "unclassified",
            "product_archetype": "synthetic" if reviewed else "unclassified",
            "reference_roles": ["structure"] if reviewed else [],
            "recommended_surface_modes": ["Persuade"] if reviewed else [],
            "blocked_surface_modes": ["Operate"] if reviewed else [],
        },
        "evidence": {
            "desktop": {
                "status": "observed",
                "evidence_refs": ["https://reference.example/desktop"],
                "notes": "Desktop fixture.",
            },
            "mobile": {
                "status": "observed",
                "evidence_refs": ["https://reference.example/mobile"],
                "notes": "Mobile fixture.",
            },
            "origin_live": {
                "status": "unverified",
                "evidence_refs": [],
                "notes": "Not audited.",
            },
            "interaction": {
                "status": "unverified",
                "evidence_refs": [],
                "notes": "Not audited.",
            },
            "accessibility": {
                "status": "unverified",
                "evidence_refs": [],
                "notes": "Not audited.",
            },
            "performance": {
                "status": "unverified",
                "evidence_refs": [],
                "notes": "Not audited.",
            },
        },
        "observations": ["A focused hierarchy is visible."] if reviewed else [],
        "transferable_mechanisms": (
            ["Place the primary promise before supporting detail."]
            if reviewed and status != "rejected"
            else []
        ),
        "do_not_copy": ["Do not copy brand assets."] if reviewed else [],
        "not_suitable_when": ["Do not use for dense operations."] if reviewed else [],
        "project_validation_refs": (
            ["artifact://fixture/project-validation"]
            if status == "project_validated"
            else []
        ),
        "rights": {
            "mode": "reference-only",
            "ai_training": False,
            "assets_redistributed": False,
            "policy_url": "https://reference.example/policy",
            "policy_observed_at": "2026-08-17",
        },
        "lifecycle": {
            "reviewed_at": "2026-08-17" if reviewed else None,
            "review_after": "2026-11-15" if reviewed else None,
        },
    }


def catalog(cards: list[dict], hypotheses: list[dict] | None = None) -> dict:
    return {
        "schema": reference_contract.CATALOG_SCHEMA,
        "id": "fixture-catalog",
        "title": "Visual reference fixture",
        "observed_at": "2026-08-17",
        "source_policy": {
            "policy_url": "https://reference.example/policy",
            "policy_observed_at": "2026-08-17",
            "mode": "reference-only",
            "ai_training": False,
            "assets_redistributed": False,
        },
        "cards": cards,
        "hypotheses": hypotheses or [],
    }


class VisualReferenceContractTests(unittest.TestCase):
    def test_runtime_unavailable_visual_baseline_remains_degraded(self) -> None:
        reference = (
            REPO_ROOT / "skills/design-craft/references/reference-workflow.md"
        ).read_text(encoding="utf-8")
        validation = (
            REPO_ROOT / "skills/design-craft/references/validation-contract.md"
        ).read_text(encoding="utf-8")
        contract = " ".join(f"{reference}\n{validation}".split())

        for fragment in (
            "Runtime-unavailable visual baseline",
            "committed visual-regression golden or screenshot fixture",
            "exact tracked target, repository revision, viewport, theme, and variant",
            "current tokens, CSS, components, assets",
            "runtime-unavailable fallback",
            "the task remains `incomplete`",
            "no browser/native success may be claimed",
        ):
            self.assertIn(fragment, contract)

    def test_candidate_and_reviewed_cards_are_strictly_distinct(self) -> None:
        candidate_errors, _ = reference_contract.validate_card(
            card("candidate-card", status="candidate")
        )
        self.assertEqual(candidate_errors, [])

        invalid = card("invalid-reviewed")
        invalid["transferable_mechanisms"] = []
        errors, _ = reference_contract.validate_card(invalid)
        self.assertIn(
            "reviewed non-rejected card must contain transferable_mechanisms",
            errors,
        )

    def test_expired_review_warns_without_rewriting_status(self) -> None:
        expired = card("expired-card")
        expired["lifecycle"]["review_after"] = "2026-08-18"
        errors, warnings = reference_contract.validate_card(
            expired, today=date(2026, 8, 19)
        )
        self.assertEqual(errors, [])
        self.assertTrue(any("should be stale" in warning for warning in warnings))

    def test_hypothesis_requires_three_reviewed_unique_origins(self) -> None:
        cards = [card(f"card-{index}") for index in range(3)]
        hypothesis = {
            "id": "focused-proof-sequence",
            "mechanism": "Lead with one promise and follow with concrete proof.",
            "supporting_card_ids": [item["id"] for item in cards],
            "unique_origin_urls": sorted(item["origin"]["url"] for item in cards),
            "disconfirming_evidence": [],
            "origin_audit_refs": [],
            "target_validation_refs": [],
            "comparative_eval_refs": [],
            "status": "proposed",
        }
        errors, _ = reference_contract.validate_catalog(catalog(cards, [hypothesis]))
        self.assertEqual(errors, [])

        hypothesis["supporting_card_ids"] = hypothesis["supporting_card_ids"][:2]
        hypothesis["unique_origin_urls"] = hypothesis["unique_origin_urls"][:2]
        errors, _ = reference_contract.validate_catalog(catalog(cards, [hypothesis]))
        self.assertTrue(any("three unique origins" in error for error in errors))

    def test_hypothesis_cannot_reuse_one_artifact_for_two_promotion_rungs(self) -> None:
        cards = [card(f"card-{index}") for index in range(3)]
        shared_ref = "artifact://visual-reference/shared-result"
        hypothesis = {
            "id": "proof-priority",
            "mechanism": "Move concrete proof ahead of supporting explanation.",
            "supporting_card_ids": [item["id"] for item in cards],
            "unique_origin_urls": sorted(item["origin"]["url"] for item in cards),
            "disconfirming_evidence": [],
            "origin_audit_refs": [],
            "target_validation_refs": [shared_ref],
            "comparative_eval_refs": [shared_ref],
            "status": "comparative_validated",
        }

        errors, _ = reference_contract.validate_catalog(catalog(cards, [hypothesis]))
        self.assertTrue(
            any("must not reuse evidence" in error for error in errors),
            errors,
        )

        hypothesis["comparative_eval_refs"] = [
            "artifact://visual-reference/distinct-comparative-result"
        ]
        errors, _ = reference_contract.validate_catalog(catalog(cards, [hypothesis]))
        self.assertEqual(errors, [])

    def test_pack_builder_blocks_beautiful_but_wrong_surface(self) -> None:
        reviewed = card("persuade-only")
        pack = reference_contract.build_reference_pack(
            catalog([reviewed]),
            [(reviewed["id"], "structure")],
            surface_mode="Operate",
            audience="Operations team",
            primary_job="Monitor and resolve incidents",
            authority_refs=["PRODUCT.md", "DESIGN.md"],
            created_at="2026-08-17T00:00:00Z",
        )
        self.assertEqual(pack["status"], "incomplete")
        self.assertTrue(any("explicitly blocks" in item for item in pack["blocking_reasons"]))

    def test_pack_builder_projects_reviewed_boundaries(self) -> None:
        reviewed = card("persuade-ready")
        pack = reference_contract.build_reference_pack(
            catalog([reviewed]),
            [(reviewed["id"], "structure")],
            surface_mode="Persuade",
            audience="Prospective customer",
            primary_job="Understand and evaluate the offer",
            authority_refs=["PRODUCT.md", "DESIGN.md"],
            created_at="2026-08-17T00:00:00Z",
        )
        self.assertEqual(pack["status"], "ready")
        self.assertEqual(pack["references"][0]["adapt"], reviewed["transferable_mechanisms"])
        self.assertIn("Do not copy brand assets.", pack["references"][0]["reject"])
        errors, _ = reference_contract.validate_pack(pack)
        self.assertEqual(errors, [])

    def test_pack_builder_requires_declared_role(self) -> None:
        reviewed = card("structure-only")
        pack = reference_contract.build_reference_pack(
            catalog([reviewed]),
            [(reviewed["id"], "tone")],
            surface_mode="Persuade",
            audience="Prospective customer",
            primary_job="Understand the offer",
            authority_refs=["PRODUCT.md", "DESIGN.md"],
            created_at="2026-08-17T00:00:00Z",
        )
        self.assertEqual(pack["status"], "incomplete")
        self.assertIn(
            "structure-only does not declare reference role tone",
            pack["blocking_reasons"],
        )

    def test_empty_incomplete_pack_remains_contract_valid(self) -> None:
        pack = reference_contract.build_reference_pack(
            catalog([]),
            [],
            surface_mode="Persuade",
            audience="Prospective customer",
            primary_job="Understand the offer",
            authority_refs=["PRODUCT.md", "DESIGN.md"],
            created_at="2026-08-17T00:00:00Z",
        )
        self.assertEqual(pack["status"], "incomplete")
        self.assertEqual(pack["references"], [])
        errors, _ = reference_contract.validate_pack(pack)
        self.assertEqual(errors, [])

    def test_invalid_catalog_fails_closed_without_projecting_malformed_cards(self) -> None:
        malformed = card("malformed-card")
        malformed["classification"] = []

        pack = reference_contract.build_reference_pack(
            catalog([malformed]),
            [(malformed["id"], "structure")],
            surface_mode="Persuade",
            audience="Prospective customer",
            primary_job="Understand the offer",
            authority_refs=["PRODUCT.md", "DESIGN.md"],
            created_at="2026-08-17T00:00:00Z",
        )

        self.assertEqual(pack["status"], "incomplete")
        self.assertEqual(pack["references"], [])
        self.assertTrue(
            any(reason.startswith("invalid catalog:") for reason in pack["blocking_reasons"])
        )
        errors, _ = reference_contract.validate_pack(pack)
        self.assertEqual(errors, [])

    def test_interaction_role_requires_observed_origin_and_interaction(self) -> None:
        reviewed = card("interaction-card")
        reviewed["classification"]["reference_roles"] = ["interaction"]
        incomplete = reference_contract.build_reference_pack(
            catalog([reviewed]),
            [(reviewed["id"], "interaction")],
            surface_mode="Persuade",
            audience="Prospective customer",
            primary_job="Understand the interaction model",
            authority_refs=["PRODUCT.md", "DESIGN.md"],
            created_at="2026-08-17T00:00:00Z",
        )
        self.assertEqual(incomplete["status"], "incomplete")
        self.assertTrue(
            any("observed origin_live" in item for item in incomplete["blocking_reasons"])
        )
        self.assertTrue(
            any("observed interaction" in item for item in incomplete["blocking_reasons"])
        )

        for facet in ("origin_live", "interaction"):
            reviewed["evidence"][facet] = {
                "status": "observed",
                "evidence_refs": [f"artifact://fixture/{facet}"],
                "notes": "Observed fixture evidence.",
            }
        ready = reference_contract.build_reference_pack(
            catalog([reviewed]),
            [(reviewed["id"], "interaction")],
            surface_mode="Persuade",
            audience="Prospective customer",
            primary_job="Understand the interaction model",
            authority_refs=["PRODUCT.md", "DESIGN.md"],
            created_at="2026-08-17T00:00:00Z",
        )
        self.assertEqual(ready["status"], "ready")

    def test_json_schemas_match_runtime_enums_and_required_keys(self) -> None:
        errors = reference_contract.schema_contract_errors(
            REPO_ROOT / "skills/design-craft/contracts"
        )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
