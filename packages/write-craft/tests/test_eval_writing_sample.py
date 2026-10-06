from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import eval_writing_sample as sample


class WritingSampleTests(unittest.TestCase):
    def test_refuses_a_case_that_can_revise(self) -> None:
        with patch.object(sample.behavior, "load_cases", return_value=[{"max_revisions": 1}]):
            with self.assertRaises(sample.behavior.ContractError):
                sample.first_draft_cases(Path("unused"))

    def run_sample(self, *, mutate: bool = False, error: bool = False, existing: bool = False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skill"
            skill.mkdir()
            entry = skill / "SKILL.md"
            entry.write_text("original")
            cases_file = root / "cases.json"
            cases_file.write_text("{}")
            output = root / "sample"
            if existing:
                output.mkdir()
                (output / "candidate.md").write_text("preserve me")
            cases = [{"id": str(i), "max_revisions": 0} for i in range(6)]

            def evaluate(**kwargs):
                if mutate:
                    entry.write_text("changed")
                return {"case_id": kwargs["case"]["id"], "status": "ERROR" if error else "PASS"}

            argv = ["sample", "--skill", str(skill), "--cases", str(cases_file),
                    "--output-dir", str(output), "--model", "test", "--judge-model", "test"]
            with patch("sys.argv", argv), patch.object(sample, "first_draft_cases", return_value=cases), \
                 patch.object(sample.behavior, "pi_version", return_value="test"), \
                 patch.object(sample.behavior, "evaluate_case", side_effect=evaluate) as evaluator, \
                 patch.object(sample.behavior, "SKILL_ROOT", skill), patch("builtins.print"):
                if existing:
                    with self.assertRaises(FileExistsError):
                        sample.main()
                    self.assertEqual((output / "candidate.md").read_text(), "preserve me")
                    evaluator.assert_not_called()
                    return
                if mutate:
                    with self.assertRaises(sample.behavior.ContractError):
                        sample.main()
                    self.assertEqual(evaluator.call_count, 1)
                    manifest = json.loads((output / "sample.json").read_text())
                    self.assertNotIn("fact_contract_status", manifest)
                    return
                status = sample.main()
                manifest = json.loads((output / "sample.json").read_text())
                if error:
                    self.assertEqual(status, 1)
                    self.assertEqual(evaluator.call_count, 3)
                    self.assertEqual(manifest["not_run"], ["3", "4", "5"])
                else:
                    self.assertEqual(status, 0)
                    self.assertEqual(manifest["fact_contract_status"], "PASS")
                self.assertEqual(manifest["editorial_acceptance"], "NOT_EVALUATED")
                self.assertEqual(manifest["human_acceptance"], "NOT_RUN")

    def test_preserves_existing_sample_without_a_model_call(self) -> None:
        self.run_sample(existing=True)

    def test_changed_snapshot_cannot_pass(self) -> None:
        self.run_sample(mutate=True)

    def test_stops_after_three_errors_without_retrying(self) -> None:
        self.run_sample(error=True)

    def test_fact_pass_never_claims_writing_or_human_acceptance(self) -> None:
        self.run_sample()


if __name__ == "__main__":
    unittest.main()
