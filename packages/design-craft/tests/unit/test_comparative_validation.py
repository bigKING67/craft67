from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.design_craft_comparative_common import CONTRACT_FILES
from tools.design_craft.evaluation.comparative.case import validate_case
from tools.design_craft.evaluation.comparative.cli import main
from tools.design_craft.evaluation.comparative.contract import (
    REQUIRED_DEFINITION_FILES,
)
from tools.design_craft.evaluation.comparative.definition import (
    active_cases,
    validate_definition,
)
from tools.design_craft.repo import REPO_ROOT


SOURCE_CASE = REPO_ROOT / "evals/comparative/emil-motion-ablation"
CONTRACT_MODULES = {
    "tools/design_craft/evaluation/comparative/case.py",
    "tools/design_craft/evaluation/comparative/cli.py",
    "tools/design_craft/evaluation/comparative/contract.py",
    "tools/design_craft/evaluation/comparative/definition.py",
    "tools/design_craft/evaluation/comparative/judge_evidence.py",
    "tools/design_craft/evaluation/comparative/result.py",
    "tools/design_craft/evaluation/comparative/run_evidence.py",
}


def copy_definition(destination: Path) -> None:
    destination.mkdir(parents=True)
    for name in REQUIRED_DEFINITION_FILES:
        shutil.copy2(SOURCE_CASE / name, destination / name)


class ComparativeValidationTests(unittest.TestCase):
    def test_valid_definition_is_accepted(self) -> None:
        _, _, errors = validate_definition(SOURCE_CASE)

        self.assertEqual(errors, [])

    def test_empty_variant_set_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir) / "case"
            copy_definition(case_dir)
            variants_path = case_dir / "variants.json"
            variants = json.loads(variants_path.read_text(encoding="utf-8"))
            variants["variants"] = []
            variants_path.write_text(
                json.dumps(variants, indent=2) + "\n", encoding="utf-8"
            )

            _, _, errors = validate_definition(case_dir)

        self.assertTrue(any("variants must be" in error for error in errors))

    def test_scorecard_markdown_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir) / "case"
            copy_definition(case_dir)
            (case_dir / "scorecard.md").write_text("# drift\n", encoding="utf-8")

            _, _, errors = validate_definition(case_dir)

        self.assertTrue(
            any("must be generated exactly" in error for error in errors)
        )

    def test_definition_only_case_does_not_require_observed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir) / "case"
            copy_definition(case_dir)

            errors = validate_case(case_dir, require_observed=False)

        self.assertEqual(errors, [])

    def test_active_cases_excludes_templates_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in ("b-case", "_template", "history", "a-case"):
                (root / name).mkdir()

            cases = active_cases(root)

        self.assertEqual([case.name for case in cases], ["a-case", "b-case"])

    def test_cli_rejects_incompatible_modes_with_argparse_exit(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as exc:
            main(["--definitions-only", "--require-observed"])

        self.assertEqual(exc.exception.code, 2)
        self.assertIn("--definitions-only is not valid", stderr.getvalue())

    def test_evidence_contract_includes_all_admission_modules(self) -> None:
        self.assertTrue(CONTRACT_MODULES.issubset(CONTRACT_FILES))


if __name__ == "__main__":
    unittest.main()
