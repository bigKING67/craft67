"""Domain-focused Creative Craft regression tests."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from support import (
    ROOT,
    approve_copy_sheet,
    cc,
    load,
    refresh_manifest,
    write_json,
)


class CopySheetTests(unittest.TestCase):
    def copy_example(self, directory: str) -> Path:
        target = Path(directory) / "project"
        shutil.copytree(ROOT / "examples/premium-haircare-launch", target)
        return target

    @staticmethod
    def approve(copy_sheet: dict) -> dict:
        return approve_copy_sheet(copy_sheet)

    def test_copy_sheet_status_and_named_owner_contract(self) -> None:
        reviewed = load("examples/premium-haircare-launch/copy-sheet.json")
        _, result = cc.validate_data(reviewed)
        self.assertTrue(result.ok, result.errors)

        approved = self.approve(reviewed)
        _, result = cc.validate_data(approved)
        self.assertTrue(result.ok, result.errors)

        approved["approval"]["approved_by"] = None
        _, result = cc.validate_data(approved)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("named approval.approved_by" in item for item in result.errors)
        )

    def test_v1_project_without_copy_sheet_remains_readable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_example(directory)
            manifest_path = project / "project-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update(
                {
                    "schema_version": "creative-craft.project-manifest.v1",
                    "manifest_id": "legacy-copy-unbound-manifest-v1",
                }
            )
            manifest.pop("contract_version")
            manifest.pop("copy_policy")
            manifest["artifacts"] = [
                item
                for item in manifest["artifacts"]
                if item["artifact_type"] != "copy-sheet"
            ]
            write_json(manifest_path, manifest)
            (project / "copy-sheet.json").unlink()
            for name in ("image-job.json", "video-job.json"):
                path = project / name
                job = json.loads(path.read_text(encoding="utf-8"))
                job.pop("copy_sheet_id")
                job.pop("copy_unit_refs")
                write_json(path, job)
            refresh_manifest(project)

            graph = cc.validate_project(project)

            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertFalse(any(kind == "copy-sheet" for kind, _ in graph.records))

    def test_copy_bound_project_gates_ready_jobs_and_public_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.copy_example(directory)
            copy_sheet_path = project / "copy-sheet.json"
            copy_sheet = json.loads(copy_sheet_path.read_text(encoding="utf-8"))
            copy_sheet.update({"status": "draft", "use_scope": "exploration"})
            copy_sheet["approval"].update(
                {
                    "status": "pending",
                    "reviewed_by": None,
                    "reviewed_at": None,
                }
            )
            write_json(copy_sheet_path, copy_sheet)
            refresh_manifest(project)

            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "requires a reviewed or approved copy sheet" in item
                    for item in graph.result.errors
                )
            )

            copy_sheet = load("examples/premium-haircare-launch/copy-sheet.json")
            write_json(copy_sheet_path, copy_sheet)
            delivery_path = project / "delivery-manifest.json"
            delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
            delivery["status"] = "ready"
            write_json(delivery_path, delivery)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "requires an approved Copy Sheet with named owner" in item
                    for item in graph.result.errors
                )
            )

            write_json(copy_sheet_path, self.approve(copy_sheet))
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)
