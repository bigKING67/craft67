"""Domain-focused Creative Craft regression tests."""

from __future__ import annotations

import contextlib
import io
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
    approve_brand_pack,
    approve_copy_sheet,
    cc,
    init_brand_pack,
    refresh_manifest,
    tree_snapshot,
    write_json,
)


class SeedTests(unittest.TestCase):
    @staticmethod
    def args(
        target: Path, *, force: bool = False, brand_pack: Path | None = None
    ) -> object:
        return type(
            "Args",
            (),
            {
                "target": str(target),
                "force": force,
                "brand_pack": str(brand_pack) if brand_pack else None,
                "brand_source_uri": "https://git.invalid/acme-brand-pack.git"
                if brand_pack
                else None,
                "brand_source_ref": "main" if brand_pack else None,
                "brand_source_commit": "1" * 40 if brand_pack else None,
                "imported_by": "fixture-operator",
                "reason": "Seed fixture",
            },
        )()

    def test_seed_and_refuse_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = type("Args", (), {"target": directory, "force": False})()
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                self.assertEqual(0, cc.cmd_seed(args))
                self.assertTrue((Path(directory) / "BRAND.md").is_file())
                self.assertTrue(
                    (Path(directory) / ".creative-craft/critique.json").is_file()
                )
                self.assertFalse(
                    (
                        Path(directory) / ".creative-craft/execution-receipt.json"
                    ).exists()
                )
                self.assertFalse(
                    (
                        Path(directory) / ".creative-craft/output-inspection.json"
                    ).exists()
                )
                self.assertFalse(
                    (Path(directory) / ".creative-craft/revision-lineage.json").exists()
                )
                self.assertFalse(
                    (Path(directory) / ".creative-craft/brand-pack.json").exists()
                )
                self.assertFalse(
                    (Path(directory) / ".creative-craft/brand-binding.json").exists()
                )
                self.assertFalse(
                    (Path(directory) / ".creative-craft/reference-bindings").exists()
                )
                self.assertFalse(
                    (Path(directory) / ".creative-craft/reference-snapshots").exists()
                )
                graph = cc.validate_project(Path(directory))
                self.assertTrue(graph.result.ok, graph.result.errors)
                self.assertIsNotNone(graph.record("critique", "critique-tbd"))
                self.assertEqual(1, cc.cmd_seed(args))
            self.assertIn("refusing to overwrite", stderr.getvalue())

    def test_seed_rejects_dangling_destination_symlink_without_external_write(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            outside = root / "outside-brand.md"
            (project / "BRAND.md").symlink_to(outside)
            before = tree_snapshot(project)

            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, cc.cmd_seed(self.args(project)))

            self.assertEqual(before, tree_snapshot(project))
            self.assertFalse(outside.exists())

    def test_seed_rejects_symlink_or_file_parent_without_partial_writes(self) -> None:
        for unsafe_parent in ("symlink", "file"):
            with (
                self.subTest(unsafe_parent=unsafe_parent),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                project = root / "project"
                project.mkdir()
                if unsafe_parent == "symlink":
                    outside = root / "outside"
                    outside.mkdir()
                    (project / ".creative-craft").symlink_to(
                        outside, target_is_directory=True
                    )
                else:
                    (project / ".creative-craft").write_text(
                        "collision", encoding="utf-8"
                    )
                before = tree_snapshot(project)

                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(1, cc.cmd_seed(self.args(project)))

                self.assertEqual(before, tree_snapshot(project))

    def test_seed_copy_failure_restores_exact_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            (project / "keep.txt").write_text("unchanged", encoding="utf-8")
            before = tree_snapshot(project)
            real_copy2 = shutil.copy2
            calls = 0

            def fail_second_copy(
                source: Path, target: Path, *args: object, **kwargs: object
            ) -> Path:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected seed copy failure")
                return real_copy2(source, target, *args, **kwargs)

            with (
                mock.patch.object(cc.shutil, "copy2", side_effect=fail_second_copy),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, cc.cmd_seed(self.args(project)))

            self.assertEqual(before, tree_snapshot(project))

    def test_seed_brand_binding_failure_restores_exact_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            (project / "keep.txt").write_text("unchanged", encoding="utf-8")
            brand_pack = init_brand_pack(root)
            approve_brand_pack(brand_pack)
            before = tree_snapshot(project)

            with (
                mock.patch.object(
                    cc.project_ops,
                    "_install_brand_snapshot",
                    side_effect=OSError("injected brand bind failure"),
                ),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(
                    1, cc.cmd_seed(self.args(project, brand_pack=brand_pack))
                )

            self.assertEqual(before, tree_snapshot(project))

    def test_seed_force_preserves_replaced_files_as_transactional_backups(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_seed(self.args(project)))
            old_brand = "# User authority\n"
            (project / "BRAND.md").write_text(old_brand, encoding="utf-8")

            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_seed(self.args(project, force=True)))

            backups = list(project.glob("BRAND.md.bak.*"))
            self.assertEqual(1, len(backups))
            self.assertEqual(old_brand, backups[0].read_text(encoding="utf-8"))

    def test_seed_cli_path_error_is_stable_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            (project / ".creative-craft").write_text("collision", encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, str(CLI_PATH), "seed", "--target", str(project)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(1, completed.returncode)
            self.assertIn("ERROR:", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    def test_project_rejects_critique_with_unknown_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = type("Args", (), {"target": directory, "force": False})()
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_seed(args))
            critique_path = Path(directory) / ".creative-craft/critique.json"
            critique = json.loads(critique_path.read_text(encoding="utf-8"))
            critique["asset_id"] = "missing-asset"
            write_json(critique_path, critique)
            refresh_manifest(Path(directory))

            graph = cc.validate_project(Path(directory))

            self.assertFalse(graph.result.ok)
            self.assertIn(
                "critique critique-tbd references unknown asset 'missing-asset'",
                graph.result.errors,
            )

    def test_project_doctor_detects_unregistered_seed_residue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = type("Args", (), {"target": directory, "force": False})()
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_seed(args))

            doctor_args = type("Args", (), {"root": directory, "json": True})()
            before_doctor = tree_snapshot(Path(directory))
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(0, cc.cmd_doctor_project(doctor_args))
            self.assertTrue(json.loads(stdout.getvalue())["healthy"])
            self.assertEqual(before_doctor, tree_snapshot(Path(directory)))

            project_dir = Path(directory) / ".creative-craft"
            residue_names = {
                "execution-receipt.json",
                "output-inspection.json",
                "revision-lineage.json",
            }
            for name in residue_names:
                shutil.copy2(cc.TEMPLATES_DIR / name, project_dir / name)

            before_doctor = tree_snapshot(Path(directory))
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(1, cc.cmd_doctor_project(doctor_args))
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["valid"])
            self.assertFalse(payload["healthy"])
            self.assertEqual(
                residue_names,
                {Path(item["path"]).name for item in payload["unregistered_artifacts"]},
            )
            self.assertTrue(
                all(
                    item["classification"] == "seed_template_residue"
                    and item["matches_bundled_template"]
                    for item in payload["unregistered_artifacts"]
                )
            )
            self.assertEqual(before_doctor, tree_snapshot(Path(directory)))

    def test_project_doctor_detects_unregistered_critique(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = type("Args", (), {"target": directory, "force": False})()
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_seed(args))
            manifest_path = Path(directory) / ".creative-craft/project-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"] = [
                item
                for item in manifest["artifacts"]
                if item["artifact_type"] != "critique"
            ]
            write_json(manifest_path, manifest)

            doctor_args = type("Args", (), {"root": directory, "json": True})()
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(1, cc.cmd_doctor_project(doctor_args))
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["valid"])
            self.assertEqual(1, len(payload["unregistered_artifacts"]))
            self.assertEqual(
                "critique", payload["unregistered_artifacts"][0]["artifact_type"]
            )


class ProjectGraphTests(unittest.TestCase):
    def copy_example(self, directory: str) -> Path:
        target = Path(directory) / "project"
        shutil.copytree(ROOT / "examples/premium-haircare-launch", target)
        return target

    def test_valid_example_graph(self) -> None:
        graph = cc.validate_project(ROOT / "examples/premium-haircare-launch")
        self.assertTrue(graph.result.ok, graph.result.errors)
        self.assertEqual(
            "ready", graph.job_statuses["northstar-motion-proof-hero-image-v1"]
        )

    def test_missing_brief_reference_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_example(directory)
            job_path = project / "image-job.json"
            job = json.loads(job_path.read_text(encoding="utf-8"))
            job["brief_id"] = "missing-brief"
            write_json(job_path, job)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("missing brief_id" in item for item in graph.result.errors)
            )

    def test_manifest_digest_drift_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_example(directory)
            path = project / "image-job.json"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("sha256 mismatch" in item for item in graph.result.errors)
            )

    def test_manifest_path_traversal_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_example(directory)
            manifest_path = project / "project-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"][0]["path"] = "../creative-brief.json"
            write_json(manifest_path, manifest)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "unsafe project-relative path" in item
                    for item in graph.result.errors
                )
            )

    def test_manifest_symlink_outside_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = self.copy_example(directory)
            manifest_path = project / "project-manifest.json"
            outside_manifest = root / "outside-manifest.json"
            manifest_path.replace(outside_manifest)
            manifest_path.symlink_to(outside_manifest)

            graph = cc.validate_project(project)

            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "manifest" in item and "symlink" in item
                    for item in graph.result.errors
                )
            )

    def test_nested_manifest_symlink_outside_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_seed(SeedTests.args(project)))
            manifest_path = project / ".creative-craft/project-manifest.json"
            outside_manifest = root / "outside-manifest.json"
            manifest_path.replace(outside_manifest)
            manifest_path.symlink_to(outside_manifest)

            graph = cc.validate_project(project)

            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "manifest" in item and "symlink" in item
                    for item in graph.result.errors
                )
            )

    def test_symlink_project_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = self.copy_example(directory)
            project_link = root / "project-link"
            project_link.symlink_to(project, target_is_directory=True)

            graph = cc.validate_project(project_link)

            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "project root must not be a symlink" in item
                    for item in graph.result.errors
                )
            )

    def test_project_doctor_reports_unregistered_symlink_without_following_it(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_seed(SeedTests.args(project)))
            unsafe = project / ".creative-craft/execution-receipt.json"
            unsafe.symlink_to(cc.TEMPLATES_DIR / "execution-receipt.json")
            nested_snapshot = project / ".creative-craft/reference-snapshots/example"
            nested_snapshot.mkdir(parents=True)
            (nested_snapshot / "ignored.json").symlink_to(
                cc.TEMPLATES_DIR / "execution-receipt.json"
            )
            before = tree_snapshot(project)
            args = type("Args", (), {"root": str(project), "json": True})()
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                self.assertEqual(1, cc.cmd_doctor_project(args))

            payload = json.loads(stdout.getvalue())
            self.assertFalse(payload["healthy"])
            unsafe_findings = [
                item
                for item in payload["unregistered_artifacts"]
                if item["classification"] == "unsafe_symlink"
            ]
            self.assertEqual(
                [".creative-craft/execution-receipt.json"],
                [item["path"] for item in unsafe_findings],
            )
            self.assertEqual(before, tree_snapshot(project))

    def test_ready_job_requires_cleared_referenced_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_example(directory)
            ledger_path = project / "asset-ledger.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["assets"][0]["rights_status"] = "UNVERIFIED"
            write_json(ledger_path, ledger)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("has unresolved rights" in item for item in graph.result.errors)
            )

    def test_receipt_and_inspection_project_status_is_derived(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_example(directory)
            output_path = project / "outputs/hero.bin"
            output_path.parent.mkdir()
            output_path.write_bytes(b"synthetic-output")
            job_path = project / "image-job.json"
            receipt = {
                "schema_version": "creative-craft.execution-receipt.v1",
                "receipt_id": "receipt-hero-1",
                "job_id": "northstar-motion-proof-hero-image-v1",
                "job_sha256": cc.sha256_file(job_path),
                "provider_profile": cc.IMAGE_PROFILE_ID,
                "execution_surface": "openai.image_api",
                "model": "gpt-image-2",
                "snapshot": "gpt-image-2-2026-04-21",
                "host": "synthetic-test",
                "operator": "unittest",
                "started_at": "2026-08-04T00:00:00Z",
                "completed_at": "2026-08-04T00:00:01Z",
                "outcome": "succeeded",
                "request_or_prompt_sha256": "1" * 64,
                "parameters": {},
                "provider_execution_id": "synthetic-1",
                "outputs": [
                    {
                        "asset_id": "hero-output-1",
                        "path": "outputs/hero.bin",
                        "sha256": cc.sha256_file(output_path),
                        "mime_type": "application/octet-stream",
                        "bytes": output_path.stat().st_size,
                    }
                ],
                "provider_errors": [],
                "moderation_result": None,
                "limitations": ["Synthetic fixture; not a provider output."],
            }
            receipt_path = project / "execution-receipt.json"
            write_json(receipt_path, receipt)
            manifest = refresh_manifest(project)
            manifest["artifacts"].append(
                {
                    "artifact_type": "execution-receipt",
                    "artifact_id": "receipt-hero-1",
                    "schema_version": "creative-craft.execution-receipt.v1",
                    "path": "execution-receipt.json",
                    "sha256": cc.sha256_file(receipt_path),
                }
            )
            write_json(project / "project-manifest.json", manifest)
            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertEqual(
                "generated", graph.job_statuses["northstar-motion-proof-hero-image-v1"]
            )

            inspection_path = project / "output-inspection.json"
            args = type(
                "Args",
                (),
                {
                    "job": str(job_path),
                    "receipt": str(receipt_path),
                    "file": str(output_path),
                    "output": str(inspection_path),
                    "inspector": "unittest",
                    "force": False,
                },
            )()
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_inspect_output(args))
            inspection = json.loads(inspection_path.read_text(encoding="utf-8"))
            self.assertEqual("deferred", inspection["decision"])
            self.assertIn("not been completed", inspection["remaining_unknowns"][0])
            inspection.update(
                {
                    "inspection_id": "inspection-hero-1",
                    "job_id": receipt["job_id"],
                    "receipt_id": receipt["receipt_id"],
                    "output_asset_id": "hero-output-1",
                    "output_sha256": cc.sha256_file(output_path),
                    "inspector": "unittest",
                    "inspected_at": "2026-08-04T00:01:00Z",
                    "decision": "approved",
                    "invariant_checks": [
                        {
                            "id": "synthetic-invariant",
                            "status": "pass",
                            "observation": "Synthetic fixture invariant passed.",
                            "interpretation": "Lifecycle projection test only.",
                        }
                    ],
                    "rights_checks": [
                        {
                            "id": "synthetic-rights",
                            "status": "pass",
                            "observation": "Synthetic fixture rights passed.",
                            "interpretation": "Lifecycle projection test only.",
                        }
                    ],
                    "approval": {
                        "approved_by": "fixture-owner",
                        "approved_at": "2026-08-04T00:02:00Z",
                        "approval_basis": "Synthetic lifecycle test only.",
                    },
                    "remaining_unknowns": [],
                }
            )
            write_json(inspection_path, inspection)
            manifest["artifacts"].append(
                {
                    "artifact_type": "output-inspection",
                    "artifact_id": "inspection-hero-1",
                    "schema_version": "creative-craft.output-inspection.v1",
                    "path": "output-inspection.json",
                    "sha256": cc.sha256_file(inspection_path),
                }
            )
            write_json(project / "project-manifest.json", manifest)
            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertEqual(
                "approved", graph.job_statuses["northstar-motion-proof-hero-image-v1"]
            )

            delivery_path = project / "delivery-manifest.json"
            delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
            copy_sheet_path = project / "copy-sheet.json"
            copy_sheet = json.loads(copy_sheet_path.read_text(encoding="utf-8"))
            write_json(copy_sheet_path, approve_copy_sheet(copy_sheet))
            delivery.update(
                {
                    "status": "delivered",
                    "receipt_refs": ["cc://execution-receipt/receipt-hero-1#"],
                    "inspection_refs": ["cc://output-inspection/inspection-hero-1#"],
                    "files": [
                        {
                            "asset_id": "hero-output-1",
                            "path": "outputs/hero.bin",
                            "sha256": cc.sha256_file(output_path),
                            "mime_type": "application/octet-stream",
                            "bytes": output_path.stat().st_size,
                            "job_id": receipt["job_id"],
                            "receipt_id": receipt["receipt_id"],
                            "inspection_id": inspection["inspection_id"],
                            "rights_status": "CLEARED",
                            "known_limitations": ["Synthetic lifecycle fixture only."],
                        }
                    ],
                }
            )
            write_json(delivery_path, delivery)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertEqual(
                "delivered", graph.job_statuses["northstar-motion-proof-hero-image-v1"]
            )
            args = type(
                "Args",
                (),
                {
                    "root": str(project),
                    "file": str(delivery_path),
                    "json": True,
                },
            )()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, cc.cmd_verify_delivery(args))
