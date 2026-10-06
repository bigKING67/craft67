from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.design_craft.repo import REPO_ROOT


SCRIPT = REPO_ROOT / "skills/design-craft/scripts/design_craft_shadow_lab.py"
SCHEMA = REPO_ROOT / "skills/design-craft/contracts/shadow-lab-manifest.schema.json"
SPEC = importlib.util.spec_from_file_location("design_craft_shadow_lab", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
shadow_lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shadow_lab)


def git(repo: Path, *arguments: str) -> str:
    environment = dict(os.environ)
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    completed = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", *arguments],
        cwd=repo,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return completed.stdout


def create_repo(parent: Path) -> Path:
    repo = parent / "source"
    repo.mkdir()
    git(repo, "init", "--quiet")
    git(repo, "config", "user.name", "Design Craft Tests")
    git(repo, "config", "user.email", "design-craft-tests@example.invalid")
    (repo / "app.txt").write_text("committed\n", encoding="utf-8")
    git(repo, "add", "app.txt")
    git(repo, "commit", "--quiet", "-m", "fixture")
    return repo


class ShadowLabTests(unittest.TestCase):
    def test_successful_retry_preserves_failure_and_source_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            prepared = shadow_lab.prepare_lab(
                source_path=repo,
                requested_ref="HEAD",
                output_root_path=parent / "labs",
                network_policy="allowed",
            )
            manifest_path = Path(prepared["manifest"]["isolation"]["manifest_path"])
            failed = shadow_lab.execute_in_lab(
                manifest_path=manifest_path, evidence_id="test-first",
                phase="test", network_mode="allowed",
                command=[sys.executable, "-c", "raise SystemExit(1)"],
                timeout_seconds=10,
            )
            receipt_path = Path(failed["receipt_path"])
            original_receipt = receipt_path.read_bytes()
            succeeded = shadow_lab.execute_in_lab(
                manifest_path=manifest_path, evidence_id="test-retry",
                phase="test", network_mode="allowed",
                command=[sys.executable, "-c", "print('retry completed')"],
                timeout_seconds=10,
            )
            self.assertFalse(failed["ok"])
            self.assertTrue(succeeded["ok"])
            self.assertEqual(receipt_path.read_bytes(), original_receipt)
            verified = shadow_lab.verify_lab(manifest_path)
            self.assertFalse(verified["ok"])
            self.assertTrue(verified["source"]["source_unchanged"])
            self.assertEqual(verified["source"]["difference_fields"], [])
            network = verified["boundary"]["network"]
            self.assertEqual(network["evidence_status"], "failed")
            self.assertEqual(
                {r["id"]: r["status"] for r in network["receipts"]},
                {"test-first": "fail", "test-retry": "pass"},
            )

    def test_output_root_permissions_are_posix_only(self) -> None:
        root_info = SimpleNamespace(st_uid=1000, st_mode=stat.S_IFDIR | 0o777)

        shadow_lab.validate_output_root_permissions(
            root_info,
            platform_name="nt",
            current_uid=2000,
        )
        with self.assertRaisesRegex(shadow_lab.ShadowLabError, "owned"):
            shadow_lab.validate_output_root_permissions(
                root_info,
                platform_name="posix",
                current_uid=2000,
            )
        with self.assertRaisesRegex(shadow_lab.ShadowLabError, "permissions"):
            shadow_lab.validate_output_root_permissions(
                root_info,
                platform_name="posix",
                current_uid=1000,
            )

    def test_manifest_schema_declares_the_zero_write_contract(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(
            schema["properties"]["schema"]["const"],
            "design-craft.shadow-lab-manifest.v1",
        )
        isolation = schema["properties"]["isolation"]["properties"]
        self.assertEqual(isolation["source_writes_allowed"], {"const": False})
        self.assertEqual(isolation["network_allowed"], {"const": False})
        self.assertEqual(isolation["untracked_content_included"], {"const": False})
        self.assertIn(
            "network_boundary",
            schema["properties"]["isolation"]["required"],
        )
        network = isolation["network_boundary"]["properties"]
        self.assertEqual(
            network["policy"]["enum"],
            ["denied", "install_only", "allowed"],
        )
        self.assertEqual(network["enforcement"], {"const": "phase_receipts_required"})

    def test_prepare_uses_fixed_commit_and_excludes_worktree_wip(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            (repo / "app.txt").write_text("dirty user edit\n", encoding="utf-8")
            (repo / "private-wip.txt").write_text("must stay local\n", encoding="utf-8")

            payload = shadow_lab.prepare_lab(
                source_path=repo,
                requested_ref="HEAD",
                output_root_path=parent / "labs",
            )
            manifest = payload["manifest"]
            worktree = Path(manifest["isolation"]["worktree"])
            manifest_path = Path(manifest["isolation"]["manifest_path"])

            self.assertEqual((worktree / "app.txt").read_text(), "committed\n")
            self.assertFalse((worktree / "private-wip.txt").exists())
            self.assertEqual(manifest["source"]["baseline"]["dirty_entry_count"], 2)
            self.assertFalse(
                manifest["source"]["baseline"]["untracked_content_read"]
            )
            self.assertFalse(manifest["isolation"]["untracked_content_included"])
            self.assertFalse((worktree / ".git").exists())
            self.assertEqual(
                manifest["isolation"]["network_boundary"],
                {
                    "policy": "denied",
                    "authorization": "shadow_lab_default",
                    "enforcement": "phase_receipts_required",
                    "observation": "phase_receipts",
                    "evidence_status": "pending",
                },
            )

            verification = shadow_lab.verify_lab(manifest_path)
            self.assertTrue(verification["ok"])
            self.assertTrue(verification["source"]["source_unchanged"])
            self.assertEqual(
                verification["boundary"]["network"]["evidence_status"],
                "unverified",
            )

            cleanup = shadow_lab.cleanup_lab(manifest_path, confirm=True)
            self.assertTrue(cleanup["ok"])
            self.assertFalse(manifest_path.parent.exists())
            self.assertEqual((repo / "app.txt").read_text(), "dirty user edit\n")
            self.assertEqual(
                (repo / "private-wip.txt").read_text(), "must stay local\n"
            )

    def test_verify_reports_source_drift_and_cleanup_stays_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            payload = shadow_lab.prepare_lab(
                source_path=repo,
                requested_ref="HEAD",
                output_root_path=parent / "labs",
            )
            manifest_path = Path(payload["manifest"]["isolation"]["manifest_path"])
            (repo / "app.txt").write_text("changed after prepare\n", encoding="utf-8")

            verification = shadow_lab.verify_lab(manifest_path)
            self.assertFalse(verification["ok"])
            self.assertIn(
                "tracked_diff_sha256",
                verification["source"]["difference_fields"],
            )

            cleanup = shadow_lab.cleanup_lab(manifest_path, confirm=True)
            self.assertFalse(cleanup["ok"])
            self.assertTrue(cleanup["lab_removed"])
            self.assertEqual((repo / "app.txt").read_text(), "changed after prepare\n")

    def test_rejects_output_root_inside_or_above_source(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            for output_root in (repo / ".labs", parent):
                with self.subTest(output_root=output_root), self.assertRaisesRegex(
                    shadow_lab.ShadowLabError, "source repository|contain"
                ):
                    shadow_lab.prepare_lab(
                        source_path=repo,
                        requested_ref="HEAD",
                        output_root_path=output_root,
                    )

    def test_rejects_a_tracked_symlink(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            (repo / "linked.txt").symlink_to("app.txt")
            git(repo, "add", "linked.txt")
            git(repo, "commit", "--quiet", "-m", "add symlink")

            with self.assertRaisesRegex(shadow_lab.ShadowLabError, "symlinks"):
                shadow_lab.prepare_lab(
                    source_path=repo,
                    requested_ref="HEAD",
                    output_root_path=parent / "labs",
                )

    def test_verify_allows_generated_internal_symlinks_without_following_them(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            payload = shadow_lab.prepare_lab(
                source_path=repo,
                requested_ref="HEAD",
                output_root_path=parent / "labs",
            )
            manifest_path = Path(payload["manifest"]["isolation"]["manifest_path"])
            worktree = Path(payload["manifest"]["isolation"]["worktree"])
            package = worktree / "node_modules" / ".store" / "package"
            package.mkdir(parents=True)
            (package / "index.js").write_text("export default true;\n")
            (worktree / "node_modules" / "package").symlink_to(
                ".store/package",
                target_is_directory=True,
            )

            verification = shadow_lab.verify_lab(manifest_path)

            self.assertTrue(verification["ok"])
            self.assertEqual(verification["lab"]["symlink_count"], 1)
            self.assertTrue(verification["source"]["source_unchanged"])

    def test_rejects_a_symlinked_output_root(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            real_root = parent / "real-labs"
            real_root.mkdir(mode=0o700)
            linked_root = parent / "linked-labs"
            linked_root.symlink_to(real_root, target_is_directory=True)

            with self.assertRaisesRegex(shadow_lab.ShadowLabError, "symlink"):
                shadow_lab.prepare_lab(
                    source_path=repo,
                    requested_ref="HEAD",
                    output_root_path=linked_root,
                )

    def test_cleanup_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            payload = shadow_lab.prepare_lab(
                source_path=repo,
                requested_ref="HEAD",
                output_root_path=parent / "labs",
            )
            manifest_path = Path(payload["manifest"]["isolation"]["manifest_path"])

            with self.assertRaisesRegex(shadow_lab.ShadowLabError, "--confirm"):
                shadow_lab.cleanup_lab(manifest_path, confirm=False)
            self.assertTrue(manifest_path.is_file())
            shadow_lab.cleanup_lab(manifest_path, confirm=True)

    def test_network_denied_command_is_explicit_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            sandbox = Path(raw) / "sandbox-exec"
            sandbox.write_text("fixture", encoding="utf-8")

            wrapped, enforcement = shadow_lab._network_denied_command(
                ["tool", "arg"],
                platform_name="darwin",
                sandbox_path=sandbox,
            )

            self.assertEqual(enforcement, "macos_sandbox_exec_egress")
            self.assertEqual(
                wrapped[:3],
                [
                    str(sandbox),
                    "-p",
                    "(version 1)(allow default)(deny network-outbound)",
                ],
            )
            self.assertEqual(wrapped[3:], ["tool", "arg"])
            with self.assertRaisesRegex(shadow_lab.ShadowLabError, "unavailable"):
                shadow_lab._network_denied_command(
                    ["tool"],
                    platform_name="linux",
                    sandbox_path=sandbox,
                )


if __name__ == "__main__":
    unittest.main()
