from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from tests.bash_support import bash_command


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills/design-craft"
PASS_SCRIPT = SKILL_ROOT / "scripts/design_craft_pass.sh"


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class PrototypeContractTests(unittest.TestCase):
    def test_workflow_separates_exploration_selection_and_promotion(self) -> None:
        contract = read("skills/design-craft/references/prototype-workflow.md")

        for fragment in (
            "one UI piece per run",
            "Default to three variants",
            "Color swaps",
            "must not edit production behavior",
            "Render one variant at a time",
            "realistic content",
            "ready_for_selection",
            "explicit user selection",
            "Delete the prototype surface",
        ):
            self.assertIn(fragment, contract)
        self.assertIn("Do not copy a fixed", contract)
        self.assertIn("system-consistency closeout", contract)

    def test_cli_accepts_prototype_mode(self) -> None:
        result = subprocess.run(
            bash_command(
                PASS_SCRIPT,
                "--target",
                str(SKILL_ROOT),
                "--mode",
                "prototype",
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
        self.assertIn("== design-craft prototype ==", result.stdout)
        self.assertIn("isolated prototype surface", result.stdout)
        self.assertIn("ready_for_selection", result.stdout)
        self.assertIn("selection or delegated selection", result.stdout)

        help_result = subprocess.run(
            bash_command(PASS_SCRIPT, "--help"),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("prototype", help_result.stdout)

    def test_golden_plan_has_three_real_axes_and_no_promotion(self) -> None:
        fixture = read("evals/product-ui-taste/prototype-divergence/input.md")
        expected = read(
            "evals/product-ui-taste/prototype-divergence/plan.expected.md"
        )

        self.assertIn("project-neutral textual fixture", fixture)
        self.assertIn("Color-only, copy-only", fixture)
        for direction in ("Triage Queue", "Change Ledger", "Guided Decision"):
            self.assertIn(direction, expected)
        for axis in (
            "interaction model",
            "information architecture",
            "disclosure strategy",
        ):
            self.assertIn(axis, expected)
        self.assertIn("one direction at full usable size", expected)
        self.assertIn("stops before implementation", expected)
        self.assertIn("cannot start before explicit user selection", expected)

    def test_governance_registers_reference_fixture_test_and_smoke(self) -> None:
        required = json.loads(
            read("contracts/validation/required-files.json")
        )["files"]
        for path in (
            "skills/design-craft/references/prototype-workflow.md",
            "evals/product-ui-taste/prototype-divergence/input.md",
            "evals/product-ui-taste/prototype-divergence/plan.expected.md",
            "tests/unit/test_prototype_contract.py",
        ):
            self.assertIn(path, required)

        makefile = read("Makefile")
        score = read("scripts/design_craft_score.py")
        source_map = read("skills/design-craft/references/source-map.md")
        self.assertIn("prototype:", makefile)
        self.assertIn("prototype_smoke", score)
        self.assertIn("prototype-divergence", source_map)


if __name__ == "__main__":
    unittest.main()
