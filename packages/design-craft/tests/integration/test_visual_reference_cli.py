from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT


SCRIPT = REPO_ROOT / "skills/design-craft/scripts/design_craft_reference.py"
FIXTURE_DIR = REPO_ROOT / "evals/fixtures/visual-reference/peekpaper"
CATALOG = REPO_ROOT / "evals/visual-reference/peekpaper-pilot/catalog.json"
GOLDEN = REPO_ROOT / "evals/visual-reference/golden"


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


class VisualReferenceCliTests(unittest.TestCase):
    def test_offline_peekpaper_replay_produces_bounded_candidates(self) -> None:
        completed = run_cli(
            "peekpaper-candidates",
            "--issue",
            "2026-08-10",
            "--issue",
            "2026-08-11",
            "--observed-at",
            "2026-08-17",
            "--fixture-dir",
            str(FIXTURE_DIR),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["schema"], "design-craft.visual-reference-catalog.v1")
        self.assertEqual(len(payload["cards"]), 24)
        self.assertEqual({card["status"] for card in payload["cards"]}, {"candidate"})
        self.assertEqual(payload["hypotheses"], [])

    def test_curated_pilot_catalog_is_valid(self) -> None:
        completed = run_cli("validate", str(CATALOG))

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["cards"]), 24)
        self.assertEqual(
            len([card for card in catalog["cards"] if card["status"] == "reviewed"]),
            8,
        )
        self.assertEqual(len(catalog["hypotheses"]), 3)

    def test_catalog_cli_rejects_double_counted_promotion_evidence(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        hypothesis = next(
            item
            for item in catalog["hypotheses"]
            if item["id"] == "desktop-mobile-priority-reordering"
        )
        hypothesis["comparative_eval_refs"] = [hypothesis["target_validation_refs"][0]]

        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "catalog.json"
            invalid_path.write_text(json.dumps(catalog), encoding="utf-8")
            completed = run_cli("validate", str(invalid_path))

        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["ok"])
        self.assertTrue(
            any(
                "must not reuse evidence" in error
                for result in payload["results"]
                for error in result["errors"]
            ),
            payload,
        )

    def test_reference_transfer_golden_pack(self) -> None:
        completed = run_cli(
            "build-pack",
            "--catalog",
            str(CATALOG),
            "--reference",
            "peekpaper-2026-08-11-design-meetup:structure",
            "--reference",
            "peekpaper-2026-08-11-locket:responsive",
            "--surface-mode",
            "Persuade",
            "--audience",
            "Prospective customer",
            "--primary-job",
            "Understand and evaluate the product offer",
            "--authority-ref",
            "PRODUCT.md",
            "--authority-ref",
            "DESIGN.md",
            "--created-at",
            "2026-08-17T00:00:00Z",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        expected = json.loads(
            (GOLDEN / "reference-transfer/expected.json").read_text(encoding="utf-8")
        )
        self.assertEqual(json.loads(completed.stdout), expected)
        self.assertEqual(expected["status"], "ready")

    def test_beautiful_but_wrong_golden_pack_is_blocked(self) -> None:
        completed = run_cli(
            "build-pack",
            "--catalog",
            str(CATALOG),
            "--reference",
            "peekpaper-2026-08-11-design-meetup:structure",
            "--surface-mode",
            "Operate",
            "--audience",
            "Operations team",
            "--primary-job",
            "Monitor and resolve active incidents",
            "--authority-ref",
            "PRODUCT.md",
            "--authority-ref",
            "DESIGN.md",
            "--created-at",
            "2026-08-17T00:00:00Z",
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        expected = json.loads(
            (GOLDEN / "beautiful-but-wrong/expected.json").read_text(encoding="utf-8")
        )
        self.assertEqual(json.loads(completed.stdout), expected)
        self.assertEqual(expected["status"], "incomplete")
        self.assertTrue(any("blocks surface mode" in item for item in expected["blocking_reasons"]))

    def test_output_write_is_atomic_and_parent_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temporary = Path(raw)
            output = temporary / "catalog.json"
            completed = run_cli(
                "peekpaper-candidates",
                "--issue",
                "2026-08-10",
                "--observed-at",
                "2026-08-17",
                "--fixture-dir",
                str(FIXTURE_DIR),
                "--output",
                str(output),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(output.is_file())
            self.assertEqual(list(temporary.glob(".*.tmp")), [])

            missing = temporary / "missing/catalog.json"
            completed = run_cli(
                "peekpaper-candidates",
                "--issue",
                "2026-08-10",
                "--observed-at",
                "2026-08-17",
                "--fixture-dir",
                str(FIXTURE_DIR),
                "--output",
                str(missing),
            )
            self.assertEqual(completed.returncode, 3)
            self.assertFalse(missing.exists())

    def test_invalid_selection_returns_contract_valid_incomplete_pack(self) -> None:
        completed = run_cli(
            "build-pack",
            "--catalog",
            str(CATALOG),
            "--reference",
            "missing-role",
            "--surface-mode",
            "Persuade",
            "--audience",
            "Prospective customer",
            "--primary-job",
            "Understand the offer",
            "--authority-ref",
            "PRODUCT.md",
            "--created-at",
            "2026-08-17T00:00:00Z",
        )

        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "incomplete")
        self.assertEqual(payload["references"], [])
        self.assertTrue(payload["blocking_reasons"])

    def test_malformed_catalog_fails_closed_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            catalog_path = Path(raw) / "malformed-catalog.json"
            catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
            selected = next(
                card
                for card in catalog["cards"]
                if card["id"] == "peekpaper-2026-08-11-design-meetup"
            )
            selected["classification"] = []
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

            completed = run_cli(
                "build-pack",
                "--catalog",
                str(catalog_path),
                "--reference",
                "peekpaper-2026-08-11-design-meetup:structure",
                "--surface-mode",
                "Persuade",
                "--audience",
                "Prospective customer",
                "--primary-job",
                "Understand the offer",
                "--authority-ref",
                "PRODUCT.md",
                "--created-at",
                "2026-08-17T00:00:00Z",
            )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "incomplete")
        self.assertEqual(payload["references"], [])
        self.assertTrue(
            any(
                reason.startswith("invalid catalog:")
                for reason in payload["blocking_reasons"]
            )
        )
        self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
