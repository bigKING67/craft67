from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from tests.bash_support import bash_command


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills/design-craft"
AUDIT_SCRIPT = SKILL_ROOT / "scripts/design_craft_audit.sh"
PASS_SCRIPT = SKILL_ROOT / "scripts/design_craft_pass.sh"


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class SystemReviewContractTests(unittest.TestCase):
    def test_visible_change_gate_consumes_staged_visual_review(self) -> None:
        skill = read("skills/design-craft/SKILL.md")
        validation = read("skills/design-craft/references/validation-contract.md")

        self.assertIn("lightweight system-consistency", skill)
        self.assertIn("semantic-family exemplars", skill)
        self.assertIn("sibling same-state consistency", skill)
        self.assertIn("Screenshot attachment is not visual review", validation)
        for field in (
            "visual_review_mode",
            "baseline_visual_review_required",
            "final_visual_review_required",
            "visual_review_contract",
            "visual_review_blocks_delivery",
        ):
            self.assertIn(field, validation)

    def test_full_review_defines_inventories_matrix_ledger_and_signoff(self) -> None:
        contract = read("skills/design-craft/references/system-review.md")

        for required_fragment in (
            "Build a surface inventory",
            "Build a semantic component-family inventory",
            "Build an interaction-pattern inventory",
            "Visual system",
            "Visual language",
            "Interaction system",
            "Motion system",
            "State and theme matrix",
            "Finding ledger",
            "Same-state comparison",
            "`pass`",
            "`blocked`",
            "`incomplete`",
        ):
            self.assertIn(required_fragment, contract)

        self.assertIn("A checkbox and a primary action do not need identical", contract)
        self.assertIn("Do not create a second numeric score", contract)

    def test_reference_first_fidelity_and_post_fix_verdict_are_bounded(self) -> None:
        contract = read("skills/design-craft/references/system-review.md")

        self.assertIn("before reading the implementation summary", contract)
        for classification in (
            "`match`",
            "`acceptable_adaptation`",
            "`missing`",
            "`contradicted`",
            "`added_without_approval`",
        ):
            self.assertIn(classification, contract)
        for verdict in ("`resolved`", "`partial`", "`unresolved`"):
            self.assertIn(verdict, contract)
        self.assertIn("does not restart an unbounded review", contract)

    def test_browser_native_surfaces_are_conditional_not_universal_bans(self) -> None:
        contract = read("skills/design-craft/references/system-review.md")

        for surface in (
            "focus ring",
            "text selection",
            "editable-text caret",
            "underline thickness and offset",
            "tabular numerals",
            "scrollbars",
        ):
            self.assertIn(surface, contract)
        self.assertIn("Browser defaults are not automatically defects", contract)
        self.assertIn("does not require universal custom", contract)

    def test_cli_accepts_system_review_mode(self) -> None:
        result = subprocess.run(
            bash_command(
                PASS_SCRIPT,
                "--target",
                str(SKILL_ROOT),
                "--mode",
                "system-review",
                "--skip-route",
                "--skip-detector",
                "--skip-score",
            ),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("== design-craft system-review ==", result.stdout)
        self.assertIn("surface/route inventory", result.stdout)
        self.assertIn("component-family x state x theme matrix", result.stdout)
        self.assertIn("pass, blocked, or incomplete", result.stdout)

        help_result = subprocess.run(
            bash_command(PASS_SCRIPT, "--help"),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("system-review", help_result.stdout)

    def test_cli_still_rejects_unknown_mode(self) -> None:
        result = subprocess.run(
            bash_command(AUDIT_SCRIPT, "--mode", "system-review-unknown"),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown mode: system-review-unknown", result.stderr)

    def test_golden_case_blocks_confirmed_same_family_drift(self) -> None:
        fixture = read("evals/product-ui-taste/system-consistency-toolbar/input.md")
        expected = read(
            "evals/product-ui-taste/system-consistency-toolbar/review.expected.md"
        )

        self.assertIn("project-neutral textual fixture", fixture)
        self.assertIn("selection checkbox is a separate semantic", fixture)
        self.assertIn("compact utility action", fixture)
        self.assertIn("Target-size and default border/background", fixture)
        self.assertIn("F-01", expected)
        self.assertIn("F-02", expected)
        self.assertGreaterEqual(expected.count("P1"), 2)
        self.assertIn("`blocked`", expected)
        self.assertIn("Missing Dark-theme evidence", expected)

    def test_governance_registers_reference_fixture_test_and_smoke(self) -> None:
        required = json.loads(
            read("contracts/validation/required-files.json")
        )["files"]
        for path in (
            "skills/design-craft/references/system-review.md",
            "evals/product-ui-taste/system-consistency-toolbar/input.md",
            "evals/product-ui-taste/system-consistency-toolbar/review.expected.md",
            "tests/unit/test_system_review_contract.py",
        ):
            self.assertIn(path, required)

        makefile = read("Makefile")
        score = read("scripts/design_craft_score.py")
        source_map = read("skills/design-craft/references/source-map.md")
        self.assertIn("system-review:", makefile)
        self.assertIn("release-gate-source:", makefile)
        self.assertIn("critique prototype system-review motion", makefile)
        self.assertIn("system_review_smoke", score)
        self.assertIn("system-consistency-toolbar", source_map)


if __name__ == "__main__":
    unittest.main()
