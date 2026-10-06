"""Domain-focused Creative Craft regression tests."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import (
    ROOT,
    add_reference_entity,
    approve_brand_pack,
    bind_brand_pack,
    bind_reference_pack,
    bind_reference_source_snapshot,
    cc,
    init_brand_pack,
    init_reference_pack,
    load,
    refresh_manifest,
    tree_snapshot,
    write_json,
)


class BrandPackTests(unittest.TestCase):
    def copy_example(self, directory: str) -> Path:
        target = Path(directory) / "project"
        shutil.copytree(ROOT / "examples/premium-haircare-launch", target)
        return target

    def test_init_brand_pack_is_draft_unverified_and_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            graph = cc.validate_brand_pack(skill_root)
            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertEqual("draft", graph.manifest["status"])
            self.assertEqual("internal", graph.manifest["classification"])
            self.assertEqual([], graph.ledger["assets"])
            self.assertIn(
                "UNVERIFIED", (skill_root / "references/claims.md").read_text()
            )
            self.assertNotIn(
                "creative-craft.brand-pack.v1", (skill_root / "SKILL.md").read_text()
            )

    def test_brand_pack_path_traversal_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            manifest_path = skill_root / "brand-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["authority_files"][0]["path"] = "../outside.md"
            write_json(manifest_path, manifest)
            graph = cc.validate_brand_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("unsafe root-relative" in item for item in graph.result.errors)
            )

    def test_brand_pack_symlink_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            brand_path = skill_root / "references/brand.md"
            content = brand_path.read_text(encoding="utf-8")
            real_path = skill_root / "references/brand-real.md"
            real_path.write_text(content, encoding="utf-8")
            brand_path.unlink()
            brand_path.symlink_to(real_path.name)
            graph = cc.validate_brand_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("must not use a symlink" in item for item in graph.result.errors)
            )

    def test_authority_digest_drift_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            with (skill_root / "references/brand.md").open(
                "a", encoding="utf-8"
            ) as handle:
                handle.write("\nDrift.\n")
            graph = cc.validate_brand_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("sha256 mismatch" in item for item in graph.result.errors)
            )

    def test_approved_pack_requires_approval_and_reviewed_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            manifest_path = skill_root / "brand-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["status"] = "approved"
            write_json(manifest_path, manifest)
            graph = cc.validate_brand_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("requires approved_at" in item for item in graph.result.errors)
            )
            self.assertTrue(
                any(
                    "requires at least one source" in item
                    for item in graph.result.errors
                )
            )

    def test_approved_pack_rejects_placeholder_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            manifest_path = skill_root / "brand-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update(
                {
                    "status": "approved",
                    "approved_at": "2026-08-04T00:00:00Z",
                    "source_references": [
                        {
                            "source_id": "fixture",
                            "uri": "https://brand.invalid/authority",
                            "version": "0.1.0",
                            "reviewed_at": "2026-08-04T00:00:00Z",
                            "notes": "Synthetic fixture.",
                        }
                    ],
                }
            )
            write_json(manifest_path, manifest)
            graph = cc.validate_brand_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("still contains TBD" in item for item in graph.result.errors)
            )

    def test_approved_pack_rejects_unresolved_asset_rights(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            ledger_path = skill_root / "asset-ledger.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["assets"].append(
                {
                    "asset_id": "acme-dam-001",
                    "path_or_uri": "dam://acme/asset-001",
                    "mime_type": "image/png",
                    "sha256": "1" * 64,
                    "creator": "fixture",
                    "owner": "fixture",
                    "rights_status": "UNVERIFIED",
                    "consent_status": "NOT_APPLICABLE",
                    "allowed_use": [],
                    "expires_at": None,
                    "reference_roles": ["brand"],
                    "parent_assets": [],
                    "notes": "Synthetic fixture.",
                }
            )
            write_json(ledger_path, ledger)
            manifest_path = skill_root / "brand-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["asset_ledger"]["sha256"] = cc.sha256_file(ledger_path)
            write_json(manifest_path, manifest)
            approve_brand_pack(skill_root, require_valid=False)
            graph = cc.validate_brand_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("unresolved rights" in item for item in graph.result.errors)
            )

    def test_seed_creates_content_bound_snapshot_without_live_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_brand_pack(root)
            project = root / "project"
            args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "force": False,
                    "brand_pack": str(skill_root),
                    "brand_source_uri": "https://git.invalid/acme.git",
                    "brand_source_ref": "main",
                    "brand_source_commit": "1" * 40,
                    "imported_by": "fixture",
                },
            )()
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_seed(args))
            snapshot_brand = (
                project / ".creative-craft/brand-snapshot/references/brand.md"
            )
            before = snapshot_brand.read_bytes()
            source_brand = skill_root / "references/brand.md"
            source_brand.write_text("Source changed after binding.\n", encoding="utf-8")
            self.assertEqual(before, snapshot_brand.read_bytes())
            self.assertFalse(snapshot_brand.is_symlink())
            self.assertTrue(cc.validate_project(project).result.ok)

    def test_draft_brand_pack_blocks_ready_job(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_brand_pack(root)
            project = root / "project"
            args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "force": False,
                    "brand_pack": str(skill_root),
                    "brand_source_uri": None,
                    "brand_source_ref": None,
                    "brand_source_commit": None,
                    "imported_by": "fixture",
                },
            )()
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_seed(args))
            job_path = project / ".creative-craft/image-job.json"
            job = json.loads(job_path.read_text(encoding="utf-8"))
            job["declared_status"] = "ready"
            write_json(job_path, job)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "requires an approved bound brand pack" in item
                    for item in graph.result.errors
                )
            )

    def test_approved_brand_pack_allows_existing_ready_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            approve_brand_pack(skill_root)
            project = self.copy_example(directory)
            bind_brand_pack(project, skill_root)
            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)

    def test_binding_identity_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            approve_brand_pack(skill_root)
            project = self.copy_example(directory)
            bind_brand_pack(project, skill_root)
            binding_path = project / ".creative-craft/brand-binding.json"
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            binding["pack_version"] = "9.9.9"
            write_json(binding_path, binding)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("pack_version differs" in item for item in graph.result.errors)
            )

    def test_binding_source_digest_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            approve_brand_pack(skill_root)
            project = self.copy_example(directory)
            bind_brand_pack(project, skill_root)
            binding_path = project / ".creative-craft/brand-binding.json"
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            binding["source"]["pack_sha256"] = "f" * 64
            write_json(binding_path, binding)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "source.pack_sha256 differs" in item for item in graph.result.errors
                )
            )

    def test_snapshot_tree_digest_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            approve_brand_pack(skill_root)
            project = self.copy_example(directory)
            bind_brand_pack(project, skill_root)
            path = project / ".creative-craft/brand-snapshot/references/brand.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8"
            )
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("tree_sha256 mismatch" in item for item in graph.result.errors)
            )

    def test_project_brand_digest_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_brand_pack(Path(directory))
            approve_brand_pack(skill_root)
            project = self.copy_example(directory)
            bind_brand_pack(project, skill_root)
            (project / "BRAND.md").write_text("Drift.\n", encoding="utf-8")
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "project_brand.sha256 mismatch" in item
                    for item in graph.result.errors
                )
            )

    def test_update_brand_snapshot_creates_backup_and_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = init_brand_pack(root / "first")
            approve_brand_pack(first)
            project = self.copy_example(directory)
            bind_brand_pack(project, first)
            old_binding = json.loads(
                (project / ".creative-craft/brand-binding.json").read_text(
                    encoding="utf-8"
                )
            )
            second = root / "second/acme-brand"
            shutil.copytree(first, second)
            brand_path = second / "references/brand.md"
            brand_path.write_text(
                brand_path.read_text(encoding="utf-8") + "\nVersion 0.2.0.\n",
                encoding="utf-8",
            )
            manifest_path = second / "brand-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "0.2.0"
            for item in manifest["authority_files"]:
                if item["role"] == "brand":
                    item["sha256"] = cc.sha256_file(brand_path)
            write_json(manifest_path, manifest)
            args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "brand_pack": str(second),
                    "reason": "Adopt approved authority 0.2.0",
                    "brand_source_uri": "https://git.invalid/acme.git",
                    "brand_source_ref": "v0.2.0",
                    "brand_source_commit": "2" * 40,
                    "imported_by": "fixture",
                },
            )()
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_update_brand_snapshot(args))
            binding = json.loads(
                (project / ".creative-craft/brand-binding.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(old_binding["binding_id"], binding["previous_binding_id"])
            self.assertEqual("0.2.0", binding["pack_version"])
            backups = list((project / ".creative-craft/brand-backups").iterdir())
            self.assertEqual(1, len(backups))
            self.assertTrue(cc.validate_project(project).result.ok)

    def test_update_failure_rolls_back_project_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = init_brand_pack(root / "first")
            approve_brand_pack(first)
            project = self.copy_example(directory)
            bind_brand_pack(project, first)
            second = root / "second/acme-brand"
            shutil.copytree(first, second)
            manifest_path = second / "brand-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "0.2.0"
            write_json(manifest_path, manifest)
            binding_path = project / ".creative-craft/brand-binding.json"
            before_binding = binding_path.read_bytes()
            before_brand = (project / "BRAND.md").read_bytes()
            before_tree = tree_snapshot(project)
            original_validate = cc.validate_project
            calls = 0

            def fail_final_validation(root_path: Path) -> cc.ProjectGraph:
                nonlocal calls
                calls += 1
                if calls == 1:
                    return original_validate(root_path)
                graph = original_validate(root_path)
                graph.result.errors.append("synthetic post-write failure")
                return graph

            args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "brand_pack": str(second),
                    "reason": "Synthetic rollback test",
                    "brand_source_uri": "https://git.invalid/acme.git",
                    "brand_source_ref": "v0.2.0",
                    "brand_source_commit": "2" * 40,
                    "imported_by": "fixture",
                },
            )()
            with (
                mock.patch.object(
                    cc.packs, "validate_project", side_effect=fail_final_validation
                ),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, cc.cmd_update_brand_snapshot(args))
            self.assertEqual(before_binding, binding_path.read_bytes())
            self.assertEqual(before_brand, (project / "BRAND.md").read_bytes())
            self.assertEqual(before_tree, tree_snapshot(project))
            self.assertTrue(original_validate(project).result.ok)

    def test_brand_backup_destination_symlink_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = init_brand_pack(root / "first")
            approve_brand_pack(first)
            project = self.copy_example(directory)
            bind_brand_pack(project, first)
            second = root / "second/acme-brand"
            shutil.copytree(first, second)
            manifest_path = second / "brand-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "0.2.0"
            write_json(manifest_path, manifest)
            outside = root / "outside-brand-backups"
            outside.mkdir()
            backup_link = project / ".creative-craft/brand-backups"
            backup_link.symlink_to(outside, target_is_directory=True)
            args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "brand_pack": str(second),
                    "reason": "Reject destination symlink",
                    "brand_source_uri": None,
                    "brand_source_ref": None,
                    "brand_source_commit": None,
                    "imported_by": "fixture",
                },
            )()
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(1, cc.cmd_update_brand_snapshot(args))
            self.assertIn("must not use a symlink", stderr.getvalue())
            self.assertEqual([], list(outside.iterdir()))
            self.assertTrue(cc.validate_project(project).result.ok)


class ReferencePackTests(unittest.TestCase):
    def copy_example(self, directory: str) -> Path:
        target = Path(directory) / "project"
        shutil.copytree(ROOT / "examples/premium-haircare-launch", target)
        return target

    def test_binding_content_digest_is_key_order_independent(self) -> None:
        binding = load("skills/creative-craft/templates/reference-binding.json")
        reordered = dict(reversed(list(binding.items())))
        self.assertEqual(
            cc.json_content_sha256(binding),
            cc.json_content_sha256(reordered),
        )

    def test_reference_staging_collision_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root / "source")
            add_reference_entity(skill_root, "reference-a")
            source = cc.validate_reference_pack(skill_root)
            staging = root / "existing-staging"
            staging.mkdir()
            marker = staging / "owner-data.txt"
            marker.write_text("preserve\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "staging path already exists"):
                cc._copy_reference_snapshot_files(source, staging)
            self.assertEqual("preserve\n", marker.read_text(encoding="utf-8"))

    def test_failed_backup_copy_removes_only_operation_residue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            tracked = root / "tracked.json"
            tracked.write_text("{}\n", encoding="utf-8")
            before = tree_snapshot(root)
            with (
                mock.patch.object(
                    cc.shutil, "copy2", side_effect=OSError("copy failed")
                ),
                self.assertRaisesRegex(OSError, "copy failed"),
            ):
                cc._backup_project_state(
                    root,
                    ".creative-craft/reference-backups/reference-a/fixed",
                    [tracked],
                    label="reference backup path",
                )
            self.assertEqual(before, tree_snapshot(root))

    def test_init_reference_pack_is_empty_draft_and_non_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_reference_pack(Path(directory))
            graph = cc.validate_reference_pack(skill_root)
            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertEqual("draft", graph.manifest["status"])
            self.assertEqual("internal", graph.manifest["classification"])
            self.assertEqual([], graph.manifest["entities"])
            self.assertEqual([], graph.ledger["assets"])
            skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("non-authoritative", skill_text)
            self.assertIn("Never override", skill_text)

    def test_reference_pack_path_traversal_and_digest_drift_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_reference_pack(Path(directory))
            add_reference_entity(skill_root, "reference-a", with_asset=True)
            ledger_path = skill_root / "asset-ledger.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["assets"][0]["path_or_uri"] = "../outside.bin"
            write_json(ledger_path, ledger)
            manifest_path = skill_root / "reference-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["asset_ledger"]["sha256"] = cc.sha256_file(ledger_path)
            write_json(manifest_path, manifest)
            graph = cc.validate_reference_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("unsafe root-relative" in item for item in graph.result.errors)
            )

            ledger["assets"][0]["path_or_uri"] = "assets/approved/reference-a.bin"
            ledger["assets"][0]["sha256"] = "f" * 64
            write_json(ledger_path, ledger)
            manifest["asset_ledger"]["sha256"] = cc.sha256_file(ledger_path)
            write_json(manifest_path, manifest)
            graph = cc.validate_reference_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("sha256 mismatch" in item for item in graph.result.errors)
            )

    def test_reference_pack_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_reference_pack(Path(directory))
            add_reference_entity(skill_root, "reference-a", with_asset=True)
            asset_path = skill_root / "assets/approved/reference-a.bin"
            real_path = skill_root / "assets/approved/reference-a-real.bin"
            real_path.write_bytes(asset_path.read_bytes())
            asset_path.unlink()
            asset_path.symlink_to(real_path.name)
            graph = cc.validate_reference_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("must not use a symlink" in item for item in graph.result.errors)
            )

    def test_reference_evidence_and_authority_semantics_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_reference_pack(Path(directory))
            manifest = add_reference_entity(skill_root, "reference-a")
            manifest["entities"][0]["observations"][0]["evidence_refs"] = []
            _, result = cc.validate_data(manifest, "reference-pack")
            self.assertFalse(result.ok)
            self.assertTrue(
                any("requires evidence_refs" in item for item in result.errors)
            )

            manifest = add_reference_entity(skill_root, "reference-b")
            manifest["entities"][0]["may_override_primary_brand"] = True
            _, result = cc.validate_data(manifest, "reference-pack")
            self.assertFalse(result.ok)
            self.assertTrue(any("must equal False" in item for item in result.errors))

    def test_reviewed_pack_requires_review_evidence_and_no_unverified_observation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_reference_pack(Path(directory))
            manifest = add_reference_entity(skill_root, "reference-a")
            manifest["status"] = "reviewed"
            manifest["reviewed_at"] = None
            observation = manifest["entities"][0]["observations"][0]
            observation["evidence_state"] = "UNVERIFIED"
            observation["evidence_refs"] = []
            write_json(skill_root / "reference-pack.json", manifest)
            graph = cc.validate_reference_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("requires reviewed_at" in item for item in graph.result.errors)
            )
            self.assertTrue(
                any("cannot contain UNVERIFIED" in item for item in graph.result.errors)
            )

    def test_reviewed_pack_requires_content_bound_source_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_reference_pack(Path(directory))
            manifest = add_reference_entity(skill_root, "reference-a")
            manifest.update(
                {
                    "status": "reviewed",
                    "reviewed_at": "2026-08-04T00:00:00Z",
                    "review_after": "2027-08-04T00:00:00Z",
                }
            )
            manifest["source_references"][0]["uri"] = "TBD"
            write_json(skill_root / "reference-pack.json", manifest)
            graph = cc.validate_reference_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("must not be a placeholder" in item for item in graph.result.errors)
            )
            self.assertTrue(
                any(
                    "requires a content SHA-256" in item for item in graph.result.errors
                )
            )
            self.assertTrue(
                any("requires snapshot_path" in item for item in graph.result.errors)
            )

            manifest["source_references"][0]["uri"] = (
                "urn:creative-craft:reference-a-source"
            )
            bind_reference_source_snapshot(skill_root, manifest)
            graph = cc.validate_reference_pack(skill_root)
            self.assertTrue(graph.result.ok, graph.result.errors)
            snapshot_path = (
                skill_root / manifest["source_references"][0]["snapshot_path"]
            )
            snapshot_path.write_text("drifted source evidence\n", encoding="utf-8")
            graph = cc.validate_reference_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("snapshot sha256 mismatch" in item for item in graph.result.errors)
            )

    def test_approved_reference_input_requires_resolved_rights(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = init_reference_pack(Path(directory))
            manifest = add_reference_entity(
                skill_root,
                "reference-a",
                with_asset=True,
                rights_status="UNVERIFIED",
                rights_policy="research_only",
            )
            manifest["entities"][0]["rights_policy"] = "approved_reference_input"
            write_json(skill_root / "reference-pack.json", manifest)
            graph = cc.validate_reference_pack(skill_root)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("unresolved rights" in item for item in graph.result.errors)
            )

    def test_draft_reference_pack_does_not_block_ready_job_and_snapshot_does_not_drift(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root)
            add_reference_entity(skill_root, "reference-a")
            project = self.copy_example(directory)
            bind_reference_pack(project, skill_root)
            snapshot_path = (
                project
                / ".creative-craft/reference-snapshots/reference-fixture/reference-pack.json"
            )
            before = snapshot_path.read_bytes()
            source_path = skill_root / "reference-pack.json"
            source_path.write_text(
                source_path.read_text(encoding="utf-8") + "\n", encoding="utf-8"
            )
            self.assertEqual(before, snapshot_path.read_bytes())
            self.assertFalse(snapshot_path.is_symlink())
            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertEqual(
                "ready", graph.job_statuses["northstar-motion-proof-hero-image-v1"]
            )
            self.assertTrue(
                any("exploratory evidence" in item for item in graph.result.warnings)
            )

    def test_multiple_reference_packs_can_coexist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = init_reference_pack(
                root / "first", "reference-one", "Reference One"
            )
            second = init_reference_pack(
                root / "second", "reference-two", "Reference Two"
            )
            add_reference_entity(first, "reference-a")
            add_reference_entity(second, "reference-b")
            project = self.copy_example(directory)
            bind_reference_pack(project, first)
            bind_reference_pack(project, second)
            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertEqual(
                2,
                sum(1 for kind, _ in graph.records if kind == "reference-pack"),
            )
            self.assertEqual(
                2,
                sum(1 for kind, _ in graph.records if kind == "reference-binding"),
            )

    def test_binding_merges_only_selected_entity_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root)
            add_reference_entity(skill_root, "reference-a", with_asset=True)
            add_reference_entity(skill_root, "reference-b", with_asset=True)
            project = self.copy_example(directory)
            bind_reference_pack(project, skill_root, ["reference-a"])
            ledger = json.loads(
                (project / "asset-ledger.json").read_text(encoding="utf-8")
            )
            assets = {asset["asset_id"]: asset for asset in ledger["assets"]}
            self.assertIn("asset-reference-a", assets)
            self.assertNotIn("asset-reference-b", assets)
            self.assertEqual(
                ".creative-craft/reference-snapshots/reference-fixture/"
                "assets/approved/reference-a.bin",
                assets["asset-reference-a"]["path_or_uri"],
            )
            self.assertTrue(cc.validate_project(project).result.ok)

    def test_unknown_selection_and_revoked_pack_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root)
            manifest = add_reference_entity(skill_root, "reference-a")
            project = self.copy_example(directory)
            with self.assertRaisesRegex(ValueError, "does not exist"):
                bind_reference_pack(project, skill_root, ["missing-reference"])
            bind_reference_pack(project, skill_root)

            manifest["status"] = "revoked"
            write_json(skill_root / "reference-pack.json", manifest)
            with self.assertRaisesRegex(ValueError, "revoked"):
                bind_reference_pack(project, skill_root)

            manifest["status"] = "superseded"
            write_json(skill_root / "reference-pack.json", manifest)
            with self.assertRaisesRegex(ValueError, "superseded"):
                bind_reference_pack(project, skill_root)
            update_args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "reference_pack": str(skill_root),
                    "reason": "Reject superseded update source",
                    "reference_source_uri": None,
                    "reference_source_ref": None,
                    "reference_source_commit": None,
                    "imported_by": "fixture-operator",
                    "select": ["reference-a"],
                },
            )()
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(1, cc.cmd_update_reference_snapshot(update_args))
            self.assertIn("superseded", stderr.getvalue())
            self.assertTrue(cc.validate_project(project).result.ok)

    def test_already_bound_superseded_snapshot_remains_historical_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root)
            add_reference_entity(skill_root, "reference-a")
            project = self.copy_example(directory)
            bind_reference_pack(project, skill_root)

            snapshot_root = (
                project / ".creative-craft/reference-snapshots/reference-fixture"
            )
            snapshot_manifest_path = snapshot_root / "reference-pack.json"
            snapshot_manifest = json.loads(
                snapshot_manifest_path.read_text(encoding="utf-8")
            )
            snapshot_manifest["status"] = "superseded"
            write_json(snapshot_manifest_path, snapshot_manifest)

            binding_path = (
                project / ".creative-craft/reference-bindings/reference-fixture.json"
            )
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            binding["source"]["pack_sha256"] = cc.sha256_file(snapshot_manifest_path)
            binding["snapshot"]["tree_sha256"] = cc.tree_sha256(snapshot_root)
            write_json(binding_path, binding)
            refresh_manifest(project)

            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertTrue(
                any(
                    "historical evidence" in warning
                    for warning in graph.result.warnings
                )
            )

    def test_snapshot_and_binding_digest_drift_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root)
            add_reference_entity(skill_root, "reference-a")
            project = self.copy_example(directory)
            bind_reference_pack(project, skill_root)
            binding_path = (
                project / ".creative-craft/reference-bindings/reference-fixture.json"
            )
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            original_selection = binding["selected_reference_ids"]
            binding["selected_reference_ids"] = ["missing-reference"]
            write_json(binding_path, binding)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("selects unknown reference" in item for item in graph.result.errors)
            )

            binding["selected_reference_ids"] = original_selection
            binding["source"]["pack_sha256"] = "f" * 64
            write_json(binding_path, binding)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "source.pack_sha256 differs" in item for item in graph.result.errors
                )
            )

            binding["source"]["pack_sha256"] = cc.sha256_file(
                project
                / ".creative-craft/reference-snapshots/reference-fixture/reference-pack.json"
            )
            binding["snapshot"]["tree_sha256"] = "e" * 64
            write_json(binding_path, binding)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any("tree_sha256 mismatch" in item for item in graph.result.errors)
            )

    def test_reference_binding_predecessor_must_resolve_to_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root)
            add_reference_entity(skill_root, "reference-a")
            project = self.copy_example(directory)
            bind_reference_pack(project, skill_root)
            binding_path = (
                project / ".creative-craft/reference-bindings/reference-fixture.json"
            )
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            binding["previous_binding_id"] = "reference-binding-does-not-exist"
            write_json(binding_path, binding)
            refresh_manifest(project)
            graph = cc.validate_project(project)
            self.assertFalse(graph.result.ok)
            self.assertTrue(
                any(
                    "has unresolved predecessor" in item for item in graph.result.errors
                )
            )

    def test_multiple_reference_updates_extend_one_resolvable_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = init_reference_pack(root / "v1")
            add_reference_entity(source, "reference-a")
            project = self.copy_example(directory)
            bind_reference_pack(project, source)
            expected_history_ids: list[str] = []

            for version in ("0.2.0", "0.3.0"):
                current_binding_path = (
                    project
                    / ".creative-craft/reference-bindings/reference-fixture.json"
                )
                current_binding = json.loads(
                    current_binding_path.read_text(encoding="utf-8")
                )
                expected_history_ids.append(current_binding["binding_id"])
                updated = root / f"v{version}/reference-fixture"
                updated.parent.mkdir()
                shutil.copytree(source, updated)
                manifest_path = updated / "reference-pack.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["version"] = version
                write_json(manifest_path, manifest)
                args = type(
                    "Args",
                    (),
                    {
                        "target": str(project),
                        "reference_pack": str(updated),
                        "reason": f"Adopt {version}",
                        "reference_source_uri": None,
                        "reference_source_ref": None,
                        "reference_source_commit": None,
                        "imported_by": "fixture-operator",
                        "select": ["reference-a"],
                    },
                )()
                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(0, cc.cmd_update_reference_snapshot(args))
                source = updated

            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)
            histories = {
                artifact_id
                for artifact_type, artifact_id in graph.records
                if artifact_type == "reference-binding-history"
            }
            self.assertEqual(set(expected_history_ids), histories)
            current_binding = json.loads(
                (
                    project
                    / ".creative-craft/reference-bindings/reference-fixture.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                expected_history_ids[-1], current_binding["previous_binding_id"]
            )

    def test_update_one_reference_pack_preserves_other_pack_and_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = init_reference_pack(
                root / "first", "reference-one", "Reference One"
            )
            second = init_reference_pack(
                root / "second", "reference-two", "Reference Two"
            )
            add_reference_entity(first, "reference-a", with_asset=True)
            add_reference_entity(second, "reference-b", with_asset=True)
            project = self.copy_example(directory)
            bind_reference_pack(project, first)
            bind_reference_pack(project, second)
            old_binding = json.loads(
                (
                    project / ".creative-craft/reference-bindings/reference-one.json"
                ).read_text(encoding="utf-8")
            )
            second_snapshot_digest = cc.tree_sha256(
                project / ".creative-craft/reference-snapshots/reference-two"
            )

            updated = root / "updated/reference-one"
            updated.parent.mkdir()
            shutil.copytree(first, updated)
            add_reference_entity(updated, "reference-c", with_asset=True)
            updated_manifest_path = updated / "reference-pack.json"
            updated_manifest = json.loads(
                updated_manifest_path.read_text(encoding="utf-8")
            )
            updated_manifest["version"] = "0.2.0"
            write_json(updated_manifest_path, updated_manifest)
            args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "reference_pack": str(updated),
                    "reason": "Adopt synthetic reference revision",
                    "reference_source_uri": "https://git.invalid/reference-one.git",
                    "reference_source_ref": "v0.2.0",
                    "reference_source_commit": "4" * 40,
                    "imported_by": "fixture-operator",
                    "select": ["reference-c"],
                },
            )()
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, cc.cmd_update_reference_snapshot(args))
            binding = json.loads(
                (
                    project / ".creative-craft/reference-bindings/reference-one.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(old_binding["binding_id"], binding["previous_binding_id"])
            history_path = (
                project
                / ".creative-craft/reference-lineage/reference-one"
                / cc.reference_history_filename(old_binding["binding_id"])
            )
            history = json.loads(history_path.read_text(encoding="utf-8"))
            self.assertEqual(old_binding["binding_id"], history["history_id"])
            self.assertEqual(old_binding, history["binding"])
            self.assertEqual(
                cc.json_content_sha256(old_binding), history["binding_sha256"]
            )
            self.assertEqual("0.2.0", binding["pack_version"])
            self.assertEqual(
                second_snapshot_digest,
                cc.tree_sha256(
                    project / ".creative-craft/reference-snapshots/reference-two"
                ),
            )
            ledger = json.loads(
                (project / "asset-ledger.json").read_text(encoding="utf-8")
            )
            asset_ids = {asset["asset_id"] for asset in ledger["assets"]}
            self.assertNotIn("asset-reference-a", asset_ids)
            self.assertIn("asset-reference-b", asset_ids)
            self.assertIn("asset-reference-c", asset_ids)
            backups = list(
                (project / ".creative-craft/reference-backups/reference-one").iterdir()
            )
            self.assertEqual(1, len(backups))
            self.assertTrue(cc.validate_project(project).result.ok)

    def test_update_failure_rolls_back_only_target_reference_pack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root / "first")
            add_reference_entity(skill_root, "reference-a", with_asset=True)
            project = self.copy_example(directory)
            bind_reference_pack(project, skill_root)
            updated = root / "updated/reference-fixture"
            updated.parent.mkdir()
            shutil.copytree(skill_root, updated)
            manifest_path = updated / "reference-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "0.2.0"
            write_json(manifest_path, manifest)
            binding_path = (
                project / ".creative-craft/reference-bindings/reference-fixture.json"
            )
            before_binding = binding_path.read_bytes()
            before_ledger = (project / "asset-ledger.json").read_bytes()
            before_snapshot = cc.tree_sha256(
                project / ".creative-craft/reference-snapshots/reference-fixture"
            )
            before_tree = tree_snapshot(project)
            original_validate = cc.validate_project
            calls = 0

            def fail_final_validation(root_path: Path) -> cc.ProjectGraph:
                nonlocal calls
                calls += 1
                graph = original_validate(root_path)
                if calls > 1:
                    graph.result.errors.append("synthetic post-write failure")
                return graph

            args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "reference_pack": str(updated),
                    "reason": "Synthetic rollback test",
                    "reference_source_uri": None,
                    "reference_source_ref": None,
                    "reference_source_commit": None,
                    "imported_by": "fixture-operator",
                    "select": ["reference-a"],
                },
            )()
            with (
                mock.patch.object(
                    cc.packs, "validate_project", side_effect=fail_final_validation
                ),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, cc.cmd_update_reference_snapshot(args))
            self.assertEqual(before_binding, binding_path.read_bytes())
            self.assertEqual(
                before_ledger, (project / "asset-ledger.json").read_bytes()
            )
            self.assertEqual(
                before_snapshot,
                cc.tree_sha256(
                    project / ".creative-craft/reference-snapshots/reference-fixture"
                ),
            )
            self.assertEqual(before_tree, tree_snapshot(project))
            self.assertTrue(original_validate(project).result.ok)

    def test_reference_backup_destination_symlink_is_rejected_before_write(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root / "first")
            add_reference_entity(skill_root, "reference-a", with_asset=True)
            project = self.copy_example(directory)
            bind_reference_pack(project, skill_root)
            updated = root / "updated/reference-fixture"
            updated.parent.mkdir()
            shutil.copytree(skill_root, updated)
            manifest_path = updated / "reference-pack.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "0.2.0"
            write_json(manifest_path, manifest)

            outside = root / "outside-backups"
            outside.mkdir()
            backup_link = project / ".creative-craft/reference-backups"
            backup_link.symlink_to(outside, target_is_directory=True)
            before = cc.tree_sha256(
                project / ".creative-craft/reference-snapshots/reference-fixture"
            )
            args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "reference_pack": str(updated),
                    "reason": "Reject destination symlink",
                    "reference_source_uri": None,
                    "reference_source_ref": None,
                    "reference_source_commit": None,
                    "imported_by": "fixture-operator",
                    "select": ["reference-a"],
                },
            )()
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(1, cc.cmd_update_reference_snapshot(args))
            self.assertIn("must not use a symlink", stderr.getvalue())
            self.assertEqual([], list(outside.iterdir()))
            self.assertEqual(
                before,
                cc.tree_sha256(
                    project / ".creative-craft/reference-snapshots/reference-fixture"
                ),
            )
            self.assertTrue(cc.validate_project(project).result.ok)

    def test_failed_initial_reference_bind_restores_exact_project_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = init_reference_pack(root)
            add_reference_entity(skill_root, "reference-a", with_asset=True)
            project = self.copy_example(directory)
            before_tree = tree_snapshot(project)
            original_validate = cc.validate_project
            calls = 0

            def fail_final_validation(root_path: Path) -> cc.ProjectGraph:
                nonlocal calls
                calls += 1
                graph = original_validate(root_path)
                if calls > 1:
                    graph.result.errors.append("synthetic post-write failure")
                return graph

            args = type(
                "Args",
                (),
                {
                    "target": str(project),
                    "reference_pack": str(skill_root),
                    "reason": "Synthetic failed initial binding",
                    "reference_source_uri": None,
                    "reference_source_ref": None,
                    "reference_source_commit": None,
                    "imported_by": "fixture-operator",
                    "select": ["reference-a"],
                },
            )()
            with (
                mock.patch.object(
                    cc.packs, "validate_project", side_effect=fail_final_validation
                ),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, cc.cmd_bind_reference_pack(args))
            self.assertEqual(before_tree, tree_snapshot(project))
            self.assertTrue(original_validate(project).result.ok)

    def test_reference_pack_cannot_replace_primary_brand_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            brand = init_brand_pack(root / "brand")
            approve_brand_pack(brand)
            reference = init_reference_pack(root / "reference")
            add_reference_entity(reference, "reference-a")
            project = self.copy_example(directory)
            bind_brand_pack(project, brand)
            before_brand = (project / "BRAND.md").read_bytes()
            bind_reference_pack(project, reference)
            self.assertEqual(before_brand, (project / "BRAND.md").read_bytes())
            graph = cc.validate_project(project)
            self.assertTrue(graph.result.ok, graph.result.errors)
            self.assertEqual(
                1,
                sum(1 for kind, _ in graph.records if kind == "brand-pack"),
            )
