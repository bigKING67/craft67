from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT


SCRIPT = REPO_ROOT / "skills/design-craft/scripts/design_craft_comp_fidelity.py"
LIB_DIR = REPO_ROOT / "skills/design-craft/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from design_craft.comp_fidelity import PngImage, write_png


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


class CompFidelityCliTests(unittest.TestCase):
    def test_self_check(self) -> None:
        result = run_cli("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_compare_then_strict_validate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = root / "reference.png"
            rendered = root / "rendered.png"
            spec = root / "spec.json"
            output = root / "evidence"
            write_png(reference, PngImage(2, 2, bytes((10, 10, 10, 255)) * 4))
            write_png(rendered, PngImage(2, 2, bytes((12, 12, 12, 255)) * 4))
            spec.write_text(json.dumps({
                "schema": "design-craft.comp-fidelity-spec.v1",
                "case_id": "cli-fixture",
                "coordinate_space": {"width": 2, "height": 2},
                "changed_pixel_delta": 0.005,
                "regions": [{"id": "canvas", "box": [0, 0, 2, 2], "salience": "primary", "dimensions": ["material"], "note": "full canvas"}],
                "advisory_thresholds": {"mean_delta": 0.1},
            }), encoding="utf-8")

            created = run_cli("compare", "--reference", str(reference), "--rendered", str(rendered), "--spec", str(spec), "--output-dir", str(output), "--observed-at", "2026-08-29T00:00:00Z")
            validated = run_cli("validate", "--manifest", str(output / "report.json"), "--reference", str(reference), "--rendered", str(rendered), "--spec", str(spec), "--strict")

            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertEqual(json.loads(created.stdout)["verdict"], "measurement_only")
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertTrue(json.loads(validated.stdout)["ok"])

    def test_cli_fails_closed_without_traceback(self) -> None:
        result = run_cli("validate", "--manifest", "/definitely/missing/report.json")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(json.loads(result.stderr)["ok"])


if __name__ == "__main__":
    unittest.main()
