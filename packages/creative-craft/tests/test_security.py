"""Domain-focused Creative Craft regression tests."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import (
    CLI_PATH,
    ROOT,
    add_reference_entity,
    approve_brand_pack,
    bind_brand_pack,
    bind_reference_pack,
    cc,
    init_brand_pack,
    init_reference_pack,
    load,
    tree_snapshot,
    write_json,
)


class WriteBoundaryTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_compile_image_rejects_precreated_temporary_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside.md"
            outside.write_text("preserve outside bytes\n", encoding="utf-8")
            output = root / "compiled.md"
            legacy_tmp = output.with_name(output.name + ".tmp")
            legacy_tmp.symlink_to(outside)

            completed = self.run_cli(
                "compile-image",
                "--file",
                str(ROOT / "examples/premium-haircare-launch/image-job.json"),
                "--output",
                str(output),
            )

            self.assertEqual(1, completed.returncode, completed.stdout)
            self.assertIn("temporary path must not be a symlink", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertEqual(
                "preserve outside bytes\n", outside.read_text(encoding="utf-8")
            )
            self.assertFalse(output.exists())
            self.assertTrue(legacy_tmp.is_symlink())

    def test_compile_image_atomic_write_preserves_output_and_cleans_temp_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "compiled.md"

            completed = self.run_cli(
                "compile-image",
                "--file",
                str(ROOT / "examples/premium-haircare-launch/image-job.json"),
                "--output",
                str(output),
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                cc.compile_image_markdown(
                    load("examples/premium-haircare-launch/image-job.json")
                ),
                output.read_text(encoding="utf-8"),
            )
            self.assertEqual([], list(root.glob(f".{output.name}.*.tmp")))

    def test_atomic_replace_failure_preserves_destination_and_cleans_temp_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "compiled.md"
            output.write_text("before\n", encoding="utf-8")

            with (
                mock.patch.object(
                    cc.contracts.os,
                    "replace",
                    side_effect=OSError("injected replace failure"),
                ),
                self.assertRaises(OSError),
            ):
                cc.write_atomic(output, "after\n")

            self.assertEqual("before\n", output.read_text(encoding="utf-8"))
            self.assertEqual([], list(root.glob(f".{output.name}.*.tmp")))

    def test_public_pack_writes_reject_symlink_project_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            reference = init_reference_pack(root / "reference")
            add_reference_entity(reference, "reference-a", with_asset=True)
            reference_project = root / "reference-project"
            shutil.copytree(
                ROOT / "examples/premium-haircare-launch", reference_project
            )
            reference_link = root / "reference-project-link"
            reference_link.symlink_to(reference_project, target_is_directory=True)
            before_reference_bind = tree_snapshot(reference_project)
            completed = self.run_cli(
                "bind-reference-pack",
                "--target",
                str(reference_link),
                "--reference-pack",
                str(reference),
            )
            self.assertEqual(1, completed.returncode, completed.stdout)
            self.assertIn("project root must not be a symlink", completed.stderr)
            self.assertEqual(before_reference_bind, tree_snapshot(reference_project))

            bind_reference_pack(reference_project, reference)
            updated_reference = root / "updated-reference"
            shutil.copytree(reference, updated_reference)
            reference_manifest_path = updated_reference / "reference-pack.json"
            reference_manifest = json.loads(
                reference_manifest_path.read_text(encoding="utf-8")
            )
            reference_manifest["version"] = "0.2.0"
            write_json(reference_manifest_path, reference_manifest)
            before_reference_update = tree_snapshot(reference_project)
            completed = self.run_cli(
                "update-reference-snapshot",
                "--target",
                str(reference_link),
                "--reference-pack",
                str(updated_reference),
                "--reason",
                "Reject symlink project root",
            )
            self.assertEqual(1, completed.returncode, completed.stdout)
            self.assertIn("project root must not be a symlink", completed.stderr)
            self.assertEqual(before_reference_update, tree_snapshot(reference_project))

            brand = init_brand_pack(root / "brand")
            approve_brand_pack(brand)
            brand_seed_project = root / "brand-seed-project"
            brand_seed_project.mkdir()
            brand_seed_link = root / "brand-seed-project-link"
            brand_seed_link.symlink_to(brand_seed_project, target_is_directory=True)
            before_brand_bind = tree_snapshot(brand_seed_project)
            completed = self.run_cli(
                "seed",
                "--target",
                str(brand_seed_link),
                "--brand-pack",
                str(brand),
                "--brand-source-uri",
                "https://git.invalid/acme-brand-pack.git",
                "--brand-source-ref",
                "main",
                "--brand-source-commit",
                "1" * 40,
                "--imported-by",
                "fixture-operator",
            )
            self.assertEqual(1, completed.returncode, completed.stdout)
            self.assertIn("symlink", completed.stderr)
            self.assertEqual(before_brand_bind, tree_snapshot(brand_seed_project))

            brand_project = root / "brand-project"
            shutil.copytree(ROOT / "examples/premium-haircare-launch", brand_project)
            bind_brand_pack(brand_project, brand)
            approve_brand_pack(brand, version="0.2.0")
            brand_link = root / "brand-project-link"
            brand_link.symlink_to(brand_project, target_is_directory=True)
            before_brand_update = tree_snapshot(brand_project)
            completed = self.run_cli(
                "update-brand-snapshot",
                "--target",
                str(brand_link),
                "--brand-pack",
                str(brand),
                "--reason",
                "Reject symlink project root",
            )
            self.assertEqual(1, completed.returncode, completed.stdout)
            self.assertIn("project root must not be a symlink", completed.stderr)
            self.assertEqual(before_brand_update, tree_snapshot(brand_project))
