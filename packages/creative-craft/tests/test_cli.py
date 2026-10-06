"""Domain-focused Creative Craft regression tests."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import (
    ROOT,
    cc,
    load,
    write_json,
)


class DoctorTests(unittest.TestCase):
    def test_doctor_passes(self) -> None:
        result = cc.doctor(ROOT)
        self.assertEqual([], result.errors, result.errors)

    def test_package_self_test_passes(self) -> None:
        args = type("Args", (), {"root": str(ROOT), "json": False})()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(0, cc.cmd_self_test(args))
        self.assertIn("PASS package self-test", stdout.getvalue())

    def test_checkout_self_test_can_force_leaf_runtime_scope(self) -> None:
        args = type(
            "Args",
            (),
            {
                "root": str(ROOT / "skills/creative-craft"),
                "scope": "runtime",
                "json": True,
            },
        )()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(0, cc.cmd_self_test(args))
        payload = json.loads(stdout.getvalue())
        self.assertEqual("runtime", payload["scope"])
        self.assertIsNone(payload["repository_valid"])
        self.assertTrue(payload["runtime_valid"])

    def test_leaf_install_self_test_uses_runtime_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory) / "skills" / "creative-craft"
            shutil.copytree(
                ROOT / "skills/creative-craft",
                installed,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(installed / "scripts/creative_craft.py"),
                    "self-test",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                0, completed.returncode, completed.stderr or completed.stdout
            )
            payload = json.loads(completed.stdout)
            self.assertTrue(payload["valid"])
            self.assertEqual("runtime", payload["scope"])
            self.assertIsNone(payload["repository_valid"])
            self.assertTrue(payload["runtime_valid"])

    def test_doctor_uses_profiles_from_requested_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "repo"
            shutil.copytree(
                ROOT,
                copied,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            profile_path = (
                copied / "skills/creative-craft/providers/openai-gpt-image-2.json"
            )
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["profile_id"] = "copied-root.invalid-profile"
            write_json(profile_path, profile)
            result = cc.doctor(copied)
            self.assertFalse(result.ok)
            self.assertTrue(any(cc.IMAGE_PROFILE_ID in item for item in result.errors))

    def test_doctor_rejects_stale_tier_one_adapter_install_tags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "repo"
            shutil.copytree(
                ROOT,
                copied,
                ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.pyc"),
            )
            adapter = copied / "adapters/pi/README.md"
            adapter.write_text(
                adapter.read_text(encoding="utf-8").replace("v0.3.0", "v0.2.1"),
                encoding="utf-8",
            )

            result = cc.doctor(copied)

            self.assertFalse(result.ok)
            self.assertTrue(
                any("adapters/pi/README.md" in item for item in result.errors)
            )

    def test_doctor_rejects_released_metadata_with_a_different_version_tag(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "repo"
            shutil.copytree(
                ROOT,
                copied,
                ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.pyc"),
            )
            package_path = copied / "package.json"
            package = json.loads(package_path.read_text(encoding="utf-8"))
            package["creativeCraft"]["releaseStatus"] = "released"
            package["creativeCraft"]["publishedInstallTag"] = "v0.2.6"
            write_json(package_path, package)

            result = cc.doctor(copied)

            self.assertFalse(result.ok)
            self.assertTrue(
                any(
                    "released package metadata must publish the tag matching VERSION"
                    in item
                    for item in result.errors
                )
            )

    def test_python_minimum_is_synchronized_across_metadata_and_ci(self) -> None:
        package = load("package.json")
        plugin = load(".codex-plugin/plugin.json")
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertEqual(">=3.10", package["creativeCraft"]["python"])
        self.assertEqual(
            package["creativeCraft"]["python"], plugin["runtime"]["python"]
        )
        self.assertIn('python: ["3.10", "3.11", "3.13"]', workflow)


class ImageJobTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load("examples/premium-haircare-launch/image-job.json")

    def test_valid_image_job(self) -> None:
        result = cc.validate_image_job(self.data)
        self.assertTrue(result.ok, result.errors)

    def test_public_validation_rejects_additional_property(self) -> None:
        data = copy.deepcopy(self.data)
        data["unexpected_field"] = True
        _, result = cc.validate_data(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("not allowed" in item for item in result.errors))

    def test_transparent_background_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["canvas"]["background"] = "transparent"
        result = cc.validate_image_job(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("background" in item for item in result.errors))

    def test_invalid_size_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["canvas"]["size"] = "1000x1000"
        result = cc.validate_image_job(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("multiples" in item for item in result.errors))

    def test_png_compression_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["canvas"]["compression"] = 50
        result = cc.validate_image_job(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("only for jpeg or webp" in item for item in result.errors))

    def test_webp_compression_accepted(self) -> None:
        data = copy.deepcopy(self.data)
        data["canvas"]["format"] = "webp"
        data["canvas"]["compression"] = 50
        result = cc.validate_image_job(data)
        self.assertTrue(result.ok, result.errors)

    def test_compiler_contains_reference_and_preserve(self) -> None:
        text = cc.compile_image_markdown(self.data)
        self.assertIn("REFERENCE MAP", text)
        self.assertIn("@product-pack-001", text)
        self.assertIn("PRESERVE EXACTLY", text)
        self.assertIn("declared status `ready`", text)


class VideoJobTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load("examples/premium-haircare-launch/video-job.json")

    def test_valid_video_job(self) -> None:
        result = cc.validate_video_job(self.data)
        self.assertTrue(result.ok, result.errors)

    def test_overlap_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["timeline"][1]["start"] = 2
        result = cc.validate_video_job(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("overlaps" in item for item in result.errors))

    def test_reference_limit_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["references"] = [
            {"asset_id": f"image-{i}", "kind": "image", "role": "test"}
            for i in range(31)
        ]
        result = cc.validate_video_job(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("reference count" in item for item in result.errors))

    def test_unavailable_execution_surface_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["execution_surface"] = "byteplus.modelark_api"
        result = cc.validate_video_job(data)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("not currently available" in item for item in result.errors)
        )

    def test_compiler_contains_timeline_and_audio(self) -> None:
        text = cc.compile_video_markdown(self.data)
        self.assertIn("TIMESTAMPED BEATS", text)
        self.assertIn("0–3s", text)
        self.assertIn("DIALOGUE / VOICE", text)
        self.assertIn("declared status `ready`", text)
