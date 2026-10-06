from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class ComponentPrimitiveContractTests(unittest.TestCase):
    def test_base_ui_support_is_conditional_not_exclusive(self) -> None:
        contract = read(
            "skills/design-craft/references/component-primitive-selection.md"
        )

        self.assertIn("Base UI is a supported project choice", contract)
        self.assertIn("conditionally applicable", contract)
        self.assertIn("Base UI-only universal prescription", contract)
        self.assertIn("intentionally rejected", contract)

    def test_decision_record_covers_authority_evidence_and_rollback(self) -> None:
        contract = read(
            "skills/design-craft/references/component-primitive-selection.md"
        )

        for fragment in (
            "keep | adopt | migrate | defer",
            "authority_source",
            "accessibility",
            "keyboard_focus",
            "overlay_portal",
            "forms",
            "ssr_hydration",
            "animation_hooks",
            "bundle_performance",
            "maintenance",
            "migration_cost",
            "rollback",
            "visual_system_impact",
        ):
            self.assertIn(fragment, contract)

    def test_existing_radix_case_repairs_the_system_before_migration(self) -> None:
        fixture = read(
            "evals/product-ui-taste/component-primitive-selection/input.md"
        )
        expected = read(
            "evals/product-ui-taste/component-primitive-selection/decision.expected.md"
        )

        self.assertIn("existing Radix project", fixture)
        self.assertIn("`decision`: `keep`", expected)
        self.assertIn("shared compact-action component", expected)
        self.assertIn("no primitive-level blocker is confirmed", expected)

    def test_new_project_allows_evidence_backed_base_ui_adoption(self) -> None:
        fixture = read(
            "evals/product-ui-taste/component-primitive-selection/input.md"
        )
        expected = read(
            "evals/product-ui-taste/component-primitive-selection/decision.expected.md"
        )

        self.assertIn("new project without authority", fixture)
        self.assertIn("`decision`: `defer`", expected)
        self.assertIn("Base UI is an allowed `adopt` result", expected)
        self.assertIn("it is not the predetermined answer", expected)

    def test_existing_base_ui_case_uses_real_project_contract(self) -> None:
        fixture = read(
            "evals/product-ui-taste/component-primitive-selection/input.md"
        )
        expected = read(
            "evals/product-ui-taste/component-primitive-selection/decision.expected.md"
        )

        self.assertIn("existing Base UI project", fixture)
        self.assertIn("installed Base UI version's real origin/positioning", expected)
        self.assertIn("focus, dismissal, keyboard, Reduced Motion", expected)
        self.assertIn("copied demo CSS", expected)

    def test_system_review_rejects_library_choice_as_visual_acceptance(self) -> None:
        system_review = read("skills/design-craft/references/system-review.md")

        self.assertIn(
            "Primitive-library consistency cannot substitute for visual-system consistency",
            system_review,
        )
        self.assertIn("component-primitive-selection.md", system_review)
        self.assertIn("not visual acceptance", system_review)

    def test_governance_registers_reference_fixture_test_and_route(self) -> None:
        required = json.loads(
            read("contracts/validation/required-files.json")
        )["files"]
        for path in (
            "skills/design-craft/references/component-primitive-selection.md",
            "evals/product-ui-taste/component-primitive-selection/input.md",
            "evals/product-ui-taste/component-primitive-selection/decision.expected.md",
            "tests/unit/test_component_primitive_contract.py",
        ):
            self.assertIn(path, required)

        skill = read("skills/design-craft/SKILL.md")
        intent = read("skills/design-craft/references/intent-map.md")
        matrix = read("docs/emilkowalski-absorption.md")
        self.assertIn("component-primitive-selection.md", skill)
        self.assertIn("component-primitive-selection.md", intent)
        self.assertIn("Base UI primitive-specific application", matrix)


if __name__ == "__main__":
    unittest.main()
