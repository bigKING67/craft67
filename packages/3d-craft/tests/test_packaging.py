from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package_skill.py"


class PackagingTests(unittest.TestCase):
    @staticmethod
    def write_glb(path: Path, value: dict) -> None:
        document = json.dumps(value, separators=(",", ":")).encode()
        document += b" " * ((4 - len(document) % 4) % 4)
        total_length = 12 + 8 + len(document)
        path.write_bytes(
            struct.pack("<III", 0x46546C67, 2, total_length)
            + struct.pack("<II", len(document), 0x4E4F534A)
            + document
        )

    def test_package_is_reproducible_and_contains_only_the_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packages = [root / "first.zip", root / "second.zip"]
            payloads = []
            for package in packages:
                result = subprocess.run(
                    ["python3", str(PACKAGER), "--output", str(package), "--json"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                payloads.append(json.loads(result.stdout))

            digests = [hashlib.sha256(path.read_bytes()).hexdigest() for path in packages]
            self.assertEqual(digests[0], digests[1])
            self.assertEqual(payloads[0]["sha256"], digests[0])
            extracted = root / "extracted"
            with zipfile.ZipFile(packages[0]) as archive:
                names = archive.namelist()
                archive.extractall(extracted)
            self.assertIn("3d-craft/SKILL.md", names)
            self.assertIn("3d-craft/vendor/gltf-validator/gltf_validator.dart.js", names)
            self.assertIn("3d-craft/vendor/gltf-validator/LICENSE", names)
            self.assertTrue(all(name.startswith("3d-craft/") for name in names))
            self.assertFalse(any("node_modules" in name or "/dist/" in name for name in names))

            glb = root / "minimal.glb"
            report = root / "gltf-report.json"
            self.write_glb(
                glb,
                {"asset": {"version": "2.0", "generator": "3d-craft-test"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"name": "Root"}]},
            )
            runtime = subprocess.run(
                [
                    "node",
                    str(extracted / "3d-craft" / "scripts" / "gltf_validate.mjs"),
                    str(glb),
                    "--output",
                    str(report),
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(runtime.returncode, 0, runtime.stderr or runtime.stdout)
            self.assertEqual(json.loads(report.read_text())["status"], "PASS")
            second_report = root / "gltf-report-second.json"
            second_runtime = subprocess.run(
                [
                    "node",
                    str(extracted / "3d-craft" / "scripts" / "gltf_validate.mjs"),
                    str(glb),
                    "--output",
                    str(second_report),
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second_runtime.returncode, 0, second_runtime.stderr or second_runtime.stdout)
            self.assertEqual(report.read_bytes(), second_report.read_bytes())

    def test_validator_reports_a_cyclic_scene_without_recursion_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            glb = root / "cyclic.glb"
            report = root / "cyclic-report.json"
            self.write_glb(
                glb,
                {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"children": [0]}]},
            )
            result = subprocess.run(
                ["node", str(ROOT / "skills" / "3d-craft" / "scripts" / "gltf_validate.mjs"), str(glb), "--output", str(report)],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Maximum call stack", result.stderr)
            self.assertEqual(json.loads(report.read_text())["status"], "FAIL")

    def test_validator_refuses_to_overwrite_the_input_glb(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            glb = Path(directory) / "asset.glb"
            self.write_glb(glb, {"asset": {"version": "2.0"}})
            before = glb.read_bytes()
            result = subprocess.run(
                ["node", str(ROOT / "skills" / "3d-craft" / "scripts" / "gltf_validate.mjs"), str(glb), "--output", str(glb)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("must not overwrite", result.stderr)
            self.assertEqual(glb.read_bytes(), before)

    def test_validator_refuses_to_overwrite_existing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            glb = root / "asset.glb"
            report = root / "report.json"
            self.write_glb(glb, {"asset": {"version": "2.0"}})
            report.write_text("preserve", encoding="utf-8")
            result = subprocess.run(
                ["node", str(ROOT / "skills" / "3d-craft" / "scripts" / "gltf_validate.mjs"), str(glb), "--output", str(report)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(report.read_text(), "preserve")

    def test_package_requires_an_absolute_output_path(self) -> None:
        result = subprocess.run(
            ["python3", str(PACKAGER), "--output", "candidate.zip", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("absolute path", result.stderr)

    def test_blender_inspector_has_no_fixture_specific_asset_prefix(self) -> None:
        inspector = (ROOT / "skills" / "3d-craft" / "scripts" / "blend_inspect.py").read_text(encoding="utf-8")
        renderer = (ROOT / "skills" / "3d-craft" / "scripts" / "render_evidence.py").read_text(encoding="utf-8")
        self.assertNotIn("GRINDER_", inspector)
        self.assertIn("inspection output already exists", inspector)
        self.assertIn("render evidence already exists", renderer)

    def test_package_and_release_outputs_must_remain_outside_source(self) -> None:
        package_output = ROOT / "candidate.zip"
        package = subprocess.run(
            ["python3", str(PACKAGER), "--output", str(package_output), "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(package.returncode, 2)
        self.assertIn("outside the source repository", package.stderr)
        self.assertFalse(package_output.exists())

        release_output = ROOT / "release-candidate"
        release = subprocess.run(
            ["python3", str(ROOT / "scripts" / "release_gate.py"), "--output-dir", str(release_output), "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(release.returncode, 2)
        self.assertIn("outside the source repository", release.stderr)
        self.assertFalse(release_output.exists())


if __name__ == "__main__":
    unittest.main()
