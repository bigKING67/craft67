from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.design_craft_comparative_common import CONTRACT_FILES
from tools.design_craft.evaluation.comparative import trials
from tools.design_craft.evaluation.comparative.cli import main
from tools.design_craft.evaluation.comparative.contract import (
    REQUIRED_DEFINITION_FILES,
)
from tools.design_craft.repo import REPO_ROOT


SOURCE_CASE = REPO_ROOT / "evals/comparative/emil-motion-ablation"


def make_case(root: Path) -> Path:
    case = root / SOURCE_CASE.name
    case.mkdir()
    for name in REQUIRED_DEFINITION_FILES:
        shutil.copy2(SOURCE_CASE / name, case / name)
    return case


def add_trial(case: Path, number: int, scores: dict[str, int], seed: str) -> None:
    path = trials.prepare_trial(case, number)
    winner = max(scores, key=scores.get)
    (path / "comparison.json").write_text(
        json.dumps(
            {
                "case_id": case.name,
                "results": {k: {"score": v} for k, v in scores.items()},
                "winner": winner,
            }
        ),
        encoding="utf-8",
    )
    (path / "blind-map.json").write_text(
        json.dumps({"seed_sha256": seed}), encoding="utf-8"
    )


def write_aggregate(case: Path) -> None:
    (case / trials.AGGREGATE_FILE).write_text(
        json.dumps(trials.build_aggregate(case)), encoding="utf-8"
    )


WIN = {"baseline": 85, "emil": 92, "design-craft": 95}
LOSE = {"baseline": 85, "emil": 95, "design-craft": 90}


class ComparativeTrialsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.case = make_case(self.root)
        # Single-trial evidence is covered elsewhere; isolate the aggregate rules.
        self.single = patch(
            "tools.design_craft.evaluation.comparative.case.validate_case",
            return_value=[],
        )
        self.single.start()

    def tearDown(self) -> None:
        self.single.stop()
        self.temp.cleanup()

    def validate(self, *, current: bool = True) -> list[str]:
        return trials.validate_trials(self.case, require_current_source=current)

    def test_three_winning_trials_pass(self) -> None:
        for number in (1, 2, 3):
            add_trial(self.case, number, WIN, f"seed-{number}")
        write_aggregate(self.case)

        self.assertEqual(self.validate(), [])
        aggregate = trials.build_aggregate(self.case)
        self.assertEqual(aggregate["mean_winner"], "design-craft")
        self.assertEqual(aggregate["mean_scores"]["design-craft"], 95)

    def test_fewer_than_minimum_trials_fail(self) -> None:
        for number in (1, 2):
            add_trial(self.case, number, WIN, f"seed-{number}")
        write_aggregate(self.case)

        self.assertTrue(any("at least 3 trials" in e for e in self.validate()))

    def test_mean_decides_even_when_one_trial_loses(self) -> None:
        add_trial(self.case, 1, WIN, "seed-1")
        add_trial(self.case, 2, WIN, "seed-2")
        add_trial(self.case, 3, {"baseline": 85, "emil": 96, "design-craft": 94}, "seed-3")
        write_aggregate(self.case)

        self.assertEqual(self.validate(), [])

    def test_losing_mean_fails_current_but_not_history(self) -> None:
        for number in (1, 2, 3):
            add_trial(self.case, number, LOSE, f"seed-{number}")
        write_aggregate(self.case)

        self.assertTrue(any("highest mean" in e for e in self.validate()))
        self.assertEqual(self.validate(current=False), [])

    def test_reused_seed_fails(self) -> None:
        for number in (1, 2, 3):
            add_trial(self.case, number, WIN, "same-seed")
        write_aggregate(self.case)

        self.assertTrue(any("own blind seed" in e for e in self.validate()))

    def test_definition_drift_fails(self) -> None:
        for number in (1, 2, 3):
            add_trial(self.case, number, WIN, f"seed-{number}")
        write_aggregate(self.case)
        drifted = trials.trial_dir(self.case, 2) / "prompt.md"
        drifted.write_text(drifted.read_text(encoding="utf-8") + "\nextra\n", encoding="utf-8")

        self.assertTrue(any("must match the parent" in e for e in self.validate()))

    def test_tampered_aggregate_fails(self) -> None:
        for number in (1, 2, 3):
            add_trial(self.case, number, LOSE, f"seed-{number}")
        aggregate = trials.build_aggregate(self.case)
        aggregate["mean_scores"]["design-craft"] = 99
        aggregate["mean_winner"] = "design-craft"
        (self.case / trials.AGGREGATE_FILE).write_text(json.dumps(aggregate), encoding="utf-8")

        self.assertTrue(any("must match the recorded" in e for e in self.validate()))

    def test_trial_numbering_must_be_contiguous(self) -> None:
        for number in (1, 2, 3):
            add_trial(self.case, number, WIN, f"seed-{number}")
        (self.case / "trials" / "3").rename(self.case / "trials" / "4")
        write_aggregate(self.case)

        self.assertTrue(any("without gaps" in e for e in self.validate()))

    def test_renamed_trial_is_reported_not_skipped(self) -> None:
        for number in (1, 2, 3):
            add_trial(self.case, number, WIN, f"seed-{number}")
        add_trial(self.case, 4, LOSE, "seed-4")
        (self.case / "trials" / "4").rename(self.case / "trials" / "4-old")
        write_aggregate(self.case)

        self.assertTrue(any("unexpected entry" in e for e in self.validate()))

    def test_prepare_requires_the_next_trial_number(self) -> None:
        trials.prepare_trial(self.case, 1)
        with self.assertRaises(ValueError):
            trials.prepare_trial(self.case, 1)
        with self.assertRaises(ValueError):
            trials.prepare_trial(self.case, 3)

    def test_prepare_leaves_nothing_when_definitions_are_missing(self) -> None:
        (self.case / "judgment.schema.json").unlink()
        with self.assertRaises(ValueError):
            trials.prepare_trial(self.case, 1)
        self.assertFalse((self.case / "trials" / "1").exists())

    def test_missing_parent_definition_is_an_error_not_a_crash(self) -> None:
        for number in (1, 2, 3):
            add_trial(self.case, number, WIN, f"seed-{number}")
        write_aggregate(self.case)
        (self.case / "expected-findings.md").unlink()

        self.assertTrue(any("missing definition" in e for e in self.validate()))

    def test_incomplete_trial_reports_instead_of_raising(self) -> None:
        for number in (1, 2, 3):
            add_trial(self.case, number, WIN, f"seed-{number}")
        (trials.trial_dir(self.case, 3) / "comparison.json").unlink()

        aggregate, errors = trials.validate_trial_set(
            self.case, require_current_source=True
        )
        self.assertIsNone(aggregate)
        self.assertTrue(any("cannot build aggregate" in e for e in errors))

    def test_aggregate_command_keeps_existing_file_on_failure(self) -> None:
        from scripts.design_craft_comparative_trials import main as trials_main

        for number in (1, 2, 3):
            add_trial(self.case, number, WIN, f"seed-{number}")
        write_aggregate(self.case)
        before = (self.case / trials.AGGREGATE_FILE).read_bytes()
        add_trial(self.case, 4, WIN, "seed-1")  # reused seed makes the set invalid

        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            trials_main(["aggregate", "--case-dir", str(self.case)])

        self.assertEqual((self.case / trials.AGGREGATE_FILE).read_bytes(), before)


class ComparativeTrialsCliTests(unittest.TestCase):
    def test_current_observed_check_requires_trials(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            make_case(Path(raw))
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["--root", raw, "--require-observed"])

        self.assertEqual(code, 1)
        self.assertIn("requires repeated trials", stderr.getvalue())

    def test_routine_validation_ignores_trials_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            case = make_case(Path(raw))
            trials.prepare_trial(case, 1)
            with contextlib.redirect_stderr(io.StringIO()):
                code = main(["--root", raw])

        self.assertEqual(code, 0)

    def test_losing_trial_validated_directly_is_not_a_certification_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw, patch(
            "tools.design_craft.evaluation.comparative.cli.validate_case",
            return_value=[],
        ) as single:
            case = make_case(Path(raw))
            add_trial(case, 1, LOSE, "seed-1")
            code = main(["--case-dir", str(trials.trial_dir(case, 1))])

        self.assertEqual(code, 0)
        self.assertFalse(single.call_args.kwargs["require_win"])

    def test_trial_modules_are_part_of_the_contract(self) -> None:
        self.assertIn("tools/design_craft/evaluation/comparative/trials.py", CONTRACT_FILES)
        self.assertIn("scripts/design_craft_comparative_trials.py", CONTRACT_FILES)


if __name__ == "__main__":
    unittest.main()
