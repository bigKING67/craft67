from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT
from tests.unit.test_sealed_rendition import GateFixture


SCRIPT = REPO_ROOT / "skills/design-craft/scripts/design_craft_sealed_rendition_gate.py"
LAB_SCRIPT = REPO_ROOT / "skills/design-craft/scripts/design_craft_shadow_lab.py"
LIB_DIR = REPO_ROOT / "skills/design-craft/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from design_craft.comp_fidelity import PngImage, write_png
from design_craft.sealed_rendition import SPEC_SCHEMA


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    # Exercise the Windows Git Bash code-page boundary on every platform.
    environment["PYTHONIOENCODING"] = "cp1252"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def run(*command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        list(command),
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


class SealedRenditionCliTests(unittest.TestCase):
    def test_self_check(self) -> None:
        result = run_cli("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["visual_decision"], "pending")
        self.assertIsNone(payload["global_pixel_pass_threshold"])

    def test_sealed_manifest_prepare_closeout_and_strict_validate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = GateFixture(Path(raw))
            prepared = run_cli(
                "prepare",
                "--spec",
                str(fixture.gate_spec),
                "--output-root",
                str(fixture.output),
                "--prepared-at",
                "2026-08-29T00:00:00Z",
            )
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            self.assertTrue(prepared.stdout.isascii())
            plan = json.loads(prepared.stdout)
            self.assertEqual(plan["authority"]["root"], str(fixture.sealed.resolve()))
            shutil.copyfile(fixture.reference, Path(plan["captures"][0]["rendered_path"]))

            closed = run_cli(
                "closeout",
                "--plan",
                str(fixture.output / "capture-plan.json"),
                "--visual-decision",
                "pending",
                "--visual-note",
                "CLI fixture remains pending visual review.",
                "--observed-at",
                "2026-08-29T00:00:01Z",
            )
            validated = run_cli(
                "validate",
                "--report",
                str(fixture.output / "gate-report.json"),
                "--strict",
            )

            self.assertEqual(closed.returncode, 0, closed.stderr)
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertTrue(json.loads(validated.stdout)["ok"])

    def test_hash_mismatch_fails_closed_without_creating_capture_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = GateFixture(Path(raw))
            fixture.source.write_bytes(b"not the sealed source")

            result = run_cli(
                "prepare",
                "--spec",
                str(fixture.gate_spec),
                "--output-root",
                str(fixture.output),
            )

            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stderr)["ok"])
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(fixture.output.exists())

    def test_git_commit_authority_uses_real_shadow_lab_verification(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_repo = root / "real project"
            source_repo.mkdir()
            page = source_repo / "page.html"
            reference = source_repo / "reference.png"
            page.write_text("<!doctype html><title>shadow</title>", encoding="utf-8")
            write_png(reference, PngImage(2, 2, bytes((20, 40, 60, 255)) * 4))
            for command in (
                ("git", "init"),
                ("git", "add", "page.html", "reference.png"),
                (
                    "git",
                    "-c",
                    "user.name=Design Craft",
                    "-c",
                    "user.email=design-craft@example.invalid",
                    "commit",
                    "-m",
                    "fixture",
                ),
            ):
                result = run(*command, cwd=source_repo)
                self.assertEqual(result.returncode, 0, result.stderr)

            labs = root / "shadow labs"
            prepared_lab = run(
                sys.executable,
                str(LAB_SCRIPT),
                "prepare",
                "--source",
                str(source_repo),
                "--ref",
                "HEAD",
                "--output-root",
                str(labs),
                cwd=REPO_ROOT,
            )
            self.assertEqual(prepared_lab.returncode, 0, prepared_lab.stderr)
            lab_payload = json.loads(prepared_lab.stdout)
            shadow_manifest = Path(
                lab_payload["manifest"]["isolation"]["manifest_path"]
            )

            comparison_spec = root / "comparison.json"
            comparison_spec.write_text(
                json.dumps(
                    {
                        "schema": "design-craft.comp-fidelity-spec.v1",
                        "case_id": "shadow-gate",
                        "coordinate_space": {"width": 2, "height": 2},
                        "changed_pixel_delta": 0.01,
                        "regions": [
                            {
                                "id": "canvas",
                                "box": [0, 0, 2, 2],
                                "salience": "primary",
                                "dimensions": ["content"],
                                "note": "shadow fixture",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            gate_spec = root / "gate.json"
            gate_spec.write_text(
                json.dumps(
                    {
                        "schema": SPEC_SCHEMA,
                        "gate_id": "shadow-gate",
                        "authority": {
                            "kind": "git_commit",
                            "shadow_lab_manifest": str(shadow_manifest),
                        },
                        "captures": [
                            {
                                "id": "desktop",
                                "kind": "browser_viewport",
                                "source": "page.html",
                                "reference": "reference.png",
                                "comparison_spec": str(comparison_spec),
                                "contract": {
                                    "runtime": "browser67",
                                    "viewport": {"width": 2, "height": 2},
                                    "device_scale_factor": 1,
                                    "theme": "light",
                                    "network": "offline",
                                    "wait_for": "document_complete",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "gate evidence"
            prepared = run_cli(
                "prepare", "--spec", str(gate_spec), "--output-root", str(output)
            )
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            plan = json.loads(prepared.stdout)
            shutil.copyfile(Path(plan["captures"][0]["reference"]["path"]), Path(plan["captures"][0]["rendered_path"]))
            closed = run_cli(
                "closeout",
                "--plan",
                str(output / "capture-plan.json"),
                "--visual-decision",
                "pending",
                "--visual-note",
                "Real Shadow Lab authority fixture remains pending.",
            )
            validated = run_cli(
                "validate", "--report", str(output / "gate-report.json"), "--strict"
            )

            self.assertEqual(closed.returncode, 0, closed.stderr)
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertTrue(json.loads(validated.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
