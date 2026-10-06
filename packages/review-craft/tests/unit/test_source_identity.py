from __future__ import annotations

# tests.support initializes the canonical runtime import path.
# ruff: noqa: I001

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support import git_init, run_cli
from review_craft.configuration import default_config
from review_craft.delivery import collect_delivery_evidence
from review_craft.remediation_contract import changes, current_source, stable_records
from review_craft.repository import (
    fingerprint_inventory,
    inspect_git,
    inventory,
    inventory_for_mode,
    run_git,
)


class SourceIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "target"
        self.root.mkdir()
        git_init(self.root)

    def commit(self, root: Path, *paths: str) -> None:
        run_git(root, "add", "--", *paths, check=True)
        run_git(root, "commit", "-m", "identity fixture", check=True)

    def submodule(self) -> Path:
        origin = Path(self.temporary.name) / "origin"
        origin.mkdir()
        git_init(origin)
        (origin / "logic.py").write_text("VALUE = 1\n")
        self.commit(origin, "logic.py")
        run_git(
            self.root,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            str(origin),
            "dep space",
            check=True,
        )
        self.commit(self.root, ".gitmodules", "dep space")
        child = self.root / "dep space"
        run_git(child, "config", "user.name", "Fixture", check=True)
        run_git(child, "config", "user.email", "fixture@example.invalid", check=True)
        run_git(child, "config", "commit.gpgsign", "false", check=True)
        return child

    def collect(self, expected: str) -> dict:
        local, *_ = collect_delivery_evidence(
            self.root,
            source_configuration=default_config(),
            expected_source_fingerprint=expected,
            verify_push=False,
            github_run=None,
        )
        return local

    @unittest.skipIf(os.name == "nt", "POSIX executable-bit regression")
    def test_mode_only_change_invalidates_source_and_delivery(self) -> None:
        script = self.root / "run.sh"
        script.write_text("#!/bin/sh\nexit 0\n")
        script.chmod(0o755)
        self.commit(self.root, "run.sh")
        self.assertEqual(subprocess.run([str(script)], capture_output=True).returncode, 0)
        before, source = current_source(self.root)
        self.assertEqual(self.collect(source["sourceFingerprint"])["status"], "VERIFIED")
        script.chmod(0o644)
        with self.assertRaises(PermissionError):
            subprocess.run([str(script)], capture_output=True)
        self.commit(self.root, "run.sh")
        after, current = current_source(self.root)
        self.assertEqual(before[0]["sha256"], after[0]["sha256"])
        self.assertNotEqual(source["sourceFingerprint"], current["sourceFingerprint"])
        self.assertEqual(
            changes(stable_records(before), stable_records(after))[0]["status"], "MODIFIED"
        )
        self.assertEqual(self.collect(source["sourceFingerprint"])["status"], "FAILED")

    def test_gitlink_and_checkout_changes_are_bound(self) -> None:
        child = self.submodule()
        before, source = current_source(self.root)
        self.assertEqual(self.collect(source["sourceFingerprint"])["status"], "VERIFIED")
        (child / "logic.py").write_text("VALUE = 2\n")
        self.commit(child, "logic.py")
        # Parent gitlink has not been staged: actual checkout alone must change identity.
        checkout_records, checkout = current_source(self.root)
        self.assertNotEqual(source["sourceFingerprint"], checkout["sourceFingerprint"])
        self.commit(self.root, "dep space")
        after, current = current_source(self.root)
        self.assertEqual(inspect_git(self.root).status, "")
        self.assertNotEqual(checkout["sourceFingerprint"], current["sourceFingerprint"])
        self.assertNotEqual(source["sourceFingerprint"], current["sourceFingerprint"])
        self.assertEqual(self.collect(source["sourceFingerprint"])["status"], "FAILED")
        self.assertEqual(
            changes(stable_records(before), stable_records(after))[0]["path"], "dep space"
        )
        self.assertEqual(
            fingerprint_inventory(stable_records(checkout_records)), checkout["sourceFingerprint"]
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli("preflight", "--target", str(self.root), "--output-root", output)
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = json.loads(created.stdout)["runDir"]
            valid = run_cli("validate", "--run-dir", run_dir, "--allow-draft")
            self.assertEqual(valid.returncode, 0, valid.stderr)

    def test_dirty_submodule_cannot_be_hidden_by_git_configuration(self) -> None:
        child = self.submodule()
        run_git(self.root, "config", "submodule.dep space.ignore", "all", check=True)
        run_git(child, "config", "status.showUntrackedFiles", "no", check=True)
        for name in ("logic.py", "untracked.py"):
            with self.subTest(name=name):
                path = child / name
                path.write_text("VALUE = 9\n")
                if name == "logic.py":
                    self.assertTrue(inspect_git(self.root).status)
                with self.assertRaisesRegex(RuntimeError, "submodule.*dirty"):
                    inventory(self.root)
                with tempfile.TemporaryDirectory() as output:
                    created = run_cli(
                        "preflight", "--target", str(self.root), "--output-root", output
                    )
                    self.assertEqual(created.returncode, 2, created.stderr)
                    self.assertEqual(list(Path(output).iterdir()), [])
                path.unlink()
                run_git(child, "restore", "--", "logic.py", check=True)

    def test_missing_unmerged_gitlink_blocks_selected_inventory(self) -> None:
        (self.root / "app.py").write_text("VALUE = 1\n")
        self.commit(self.root, "app.py")
        oid = run_git(self.root, "rev-parse", "HEAD", check=True).stdout.decode().strip()
        entries = "".join(f"160000 {oid} {stage}\tmissing-submodule\n" for stage in (1, 2, 3))
        subprocess.run(
            ["git", "update-index", "--index-info"],
            cwd=self.root,
            input=entries.encode("ascii"),
            check=True,
            capture_output=True,
        )
        staged = run_git(self.root, "ls-files", "--stage", check=True).stdout
        self.assertEqual(staged.count(b"\tmissing-submodule\n"), 3)
        with self.assertRaisesRegex(RuntimeError, "unmerged index entry"):
            inventory(self.root)
        self.assertEqual(
            [r["path"] for r in inventory(self.root, excludes=["missing-submodule"])[0]], ["app.py"]
        )
        with tempfile.TemporaryDirectory() as output:
            result = run_cli("preflight", "--target", str(self.root), "--output-root", output)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(list(Path(output).iterdir()), [])

    def test_current_coverage_identity_cannot_be_removed_or_forged(self) -> None:
        from tests.support import create_run

        (self.root / "app.py").write_text("VALUE = 1\n")
        with tempfile.TemporaryDirectory() as output:
            run = create_run(self.root, Path(output))
            path = run / "coverage.json"
            original = path.read_text(encoding="utf-8")
            for mutation in ("remove", "forge"):
                value = json.loads(original)
                row = value["files"][0]
                if mutation == "remove":
                    row.pop("sourceIdentity")
                else:
                    row["sourceIdentity"]["executable"] = not row["sourceIdentity"]["executable"]
                path.write_text(json.dumps(value))
                checked = run_cli("validate", "--run-dir", str(run), "--allow-draft")
                self.assertNotEqual(checked.returncode, 0)
                self.assertIn("sourceIdentity", checked.stderr)

    def test_frozen_projection_retains_old_submodule_and_status_semantics(self) -> None:
        from review_craft.contracts import _current_source_projection
        from review_craft.jsonio import sha256_bytes

        child = self.submodule()
        (child / "logic.py").write_text("VALUE = 9\n")
        run_git(self.root, "config", "submodule.dep space.ignore", "all", check=True)
        run_git(self.root, "config", "status.showUntrackedFiles", "no", check=True)
        (self.root / "loose.py").write_text("VALUE = 1\n")
        for schema in ("review-craft.run.v3", "review-craft.run.v4"):
            rows, _, _, _, status = _current_source_projection(
                self.root,
                default_config(),
                schema_version=schema,
            )
            row = next(r for r in rows if r["path"] == "dep space")
            self.assertNotIn("sourceIdentity", row)
            self.assertEqual(row["kind"], "other")
            self.assertEqual(row["sizeBytes"], child.lstat().st_size)
            self.assertEqual(row["sha256"], sha256_bytes(b""))
            self.assertEqual(status, "")
        with self.assertRaisesRegex(RuntimeError, "dirty"):
            _current_source_projection(self.root, default_config())
        run_git(child, "restore", "--", "logic.py", check=True)
        run_git(self.root, "submodule", "deinit", "-f", "--", "dep space", check=True)
        child.rmdir()
        rows, *_ = _current_source_projection(
            self.root, default_config(), schema_version="review-craft.run.v4"
        )
        self.assertNotIn("dep space", [r["path"] for r in rows])

    def test_frozen_run_validates_old_rows_and_rejects_new_identity(self) -> None:
        from tests.support import create_run, populate_valid_run, rewrite_fixture_run_schema

        (self.root / "app.py").write_text("def answer():\n    return 41\n")
        for schema in ("review-craft.run.v3", "review-craft.run.v4"):
            with self.subTest(schema=schema), tempfile.TemporaryDirectory() as output:
                run = create_run(self.root, Path(output))
                populate_valid_run(run)
                rewrite_fixture_run_schema(run, schema)
                valid = run_cli("validate", "--run-dir", str(run))
                self.assertEqual(valid.returncode, 0, valid.stderr)
                path = run / "coverage.json"
                coverage = json.loads(path.read_text(encoding="utf-8"))
                self.assertNotIn("sourceIdentity", coverage["files"][0])
                coverage["files"][0]["sourceIdentity"] = {
                    "executable": False,
                    "gitlink": None,
                    "checkout": None,
                }
                path.write_text(json.dumps(coverage))
                invalid = run_cli("validate", "--run-dir", str(run))
                self.assertNotEqual(invalid.returncode, 0)
                self.assertIn("unsupported by frozen", invalid.stderr)

    def test_legacy_record_fingerprint_stays_readable(self) -> None:
        from review_craft.jsonio import canonical_compact, sha256_bytes

        rows = [{"path": "a.py", "kind": "file", "sha256": "a" * 64, "classification": "source"}]
        self.assertEqual(
            fingerprint_inventory(rows), sha256_bytes(canonical_compact(rows).encode())
        )

    def test_optimized_fingerprint_preserves_canonical_bytes(self) -> None:
        from review_craft.jsonio import canonical_compact, sha256_bytes

        rows = []
        for index, identity in enumerate(
            (
                None,
                {"executable": False, "gitlink": None, "checkout": None},
                {"executable": True, "gitlink": None, "checkout": None},
                {"executable": 1, "gitlink": None, "checkout": None},
                {"executable": False, "gitlink": "a" * 40, "checkout": "b" * 40},
            )
        ):
            row = {
                "path": f'{index}/中文\\quote"\n.py',
                "kind": "file",
                "sha256": "a" * 64,
                "classification": "source",
            }
            if identity is not None:
                row["sourceIdentity"] = identity
            rows.append(row)
            rows.append(
                {
                    **row,
                    "path": row["path"] + ".old",
                    "diffStatus": "RENAMED",
                    "previousPath": "old.py",
                    "untracked": False,
                }
            )
        expected = sha256_bytes(canonical_compact(sorted(rows, key=lambda r: r["path"])).encode())
        self.assertEqual(fingerprint_inventory(list(reversed(rows))), expected)

    @unittest.skipIf(os.name == "nt", "POSIX diff mode selection")
    def test_diff_detects_modes_hidden_by_filemode_configuration(self) -> None:
        path = self.root / "run.sh"
        path.write_text("#!/bin/sh\nexit 0\n")
        path.chmod(0o644)
        self.commit(self.root, "run.sh")
        run_git(self.root, "config", "core.filemode", "false", check=True)
        config = {**default_config(), "mode": "diff", "diffBase": "HEAD"}
        _, before = current_source(self.root, config)
        path.chmod(0o755)
        rows, after = current_source(self.root, config)
        self.assertEqual([row["path"] for row in rows], ["run.sh"])
        self.assertNotEqual(before["sourceFingerprint"], after["sourceFingerprint"])
        local, *_ = collect_delivery_evidence(
            self.root,
            source_configuration=config,
            expected_source_fingerprint=before["sourceFingerprint"],
            verify_push=False,
            github_run=None,
        )
        self.assertEqual(local["status"], "FAILED")
        self.assertFalse(local["clean"])

    def test_hidden_submodule_index_flags_are_rejected_recursively(self) -> None:
        child = self.submodule()
        origin = Path(self.temporary.name) / "origin"
        run_git(
            child,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            str(origin),
            "nested",
            check=True,
        )
        self.commit(child, ".gitmodules", "nested")
        self.commit(self.root, "dep space")
        _, before = current_source(self.root)
        for target in (child, child / "nested"):
            for flag in ("assume-unchanged", "skip-worktree"):
                with self.subTest(target=target.name, flag=flag):
                    run_git(target, "update-index", f"--{flag}", "--", "logic.py", check=True)
                    (target / "logic.py").write_text("VALUE = 9\n")
                    self.assertEqual(run_git(target, "status", "--porcelain").stdout, b"")
                    with self.assertRaisesRegex(RuntimeError, "hidden index flags"):
                        self.collect(before["sourceFingerprint"])
                    run_git(target, "update-index", f"--no-{flag}", "--", "logic.py", check=True)
                    run_git(target, "restore", "--", "logic.py", check=True)
        run_git(child, "submodule", "deinit", "-f", "--", "nested", check=True)
        self.assertNotEqual(
            current_source(self.root)[1]["sourceFingerprint"], before["sourceFingerprint"]
        )

    def test_frozen_diff_preserves_ignored_broken_checkout_semantics(self) -> None:
        from review_craft.contracts import _current_source_projection

        child = self.submodule()
        run_git(self.root, "config", "submodule.dep space.ignore", "all", check=True)
        (child / ".git").unlink()  # Git for Windows marks this fixture file hidden.
        (child / ".git").write_text("gitdir: nonexistent-fixture-directory\n", encoding="utf-8")
        config = {**default_config(), "mode": "diff", "diffBase": "HEAD"}
        for schema in ("review-craft.run.v3", "review-craft.run.v4"):
            rows, diff, *_ = _current_source_projection(self.root, config, schema_version=schema)
            self.assertEqual(rows, [])
            self.assertEqual(diff["changes"], [])
        with self.assertRaisesRegex(RuntimeError, "git status failed"):
            _current_source_projection(self.root, config)

    def test_excluded_broken_submodule_does_not_block_inventory(self) -> None:
        child = self.submodule()
        (child / ".git").unlink()  # Git for Windows marks this fixture file hidden.
        (child / ".git").write_text("gitdir: nonexistent-fixture-directory\n", encoding="utf-8")
        rows, _ = inventory(self.root, excludes=["dep space"])
        self.assertEqual([row["path"] for row in rows], [".gitmodules"])
        with self.assertRaisesRegex(RuntimeError, "submodule.*identity is unknown"):
            inventory(self.root)

    def test_uninitialized_and_deleted_gitlinks_keep_explicit_identity(self) -> None:
        child = self.submodule()
        before = fingerprint_inventory(inventory(self.root)[0])
        oid = run_git(child, "rev-parse", "HEAD", check=True).stdout.decode().strip()
        run_git(self.root, "submodule", "deinit", "-f", "--", "dep space", check=True)
        rows, _ = inventory(self.root)
        record = next(row for row in rows if row["path"] == "dep space")
        self.assertEqual(record["sourceIdentity"]["gitlink"], oid)
        self.assertIsNone(record["sourceIdentity"]["checkout"])
        self.assertNotEqual(fingerprint_inventory(rows), before)
        child.rmdir()
        self.assertEqual(
            fingerprint_inventory(inventory(self.root)[0]), fingerprint_inventory(rows)
        )
        run_git(self.root, "rm", "--", "dep space", check=True)
        deleted, _, _ = inventory_for_mode(self.root, mode="diff", diff_base="HEAD")
        record = next(row for row in deleted if row["path"] == "dep space")
        self.assertEqual(record["kind"], "deleted")
        self.assertEqual(record["sourceIdentity"]["gitlink"], oid)
        self.assertTrue(record["binary"])

    @unittest.skipIf(os.name == "nt", "POSIX mode change and execution semantics")
    def test_modes_ignore_git_filemode_configuration_but_respect_scope(self) -> None:
        child = self.submodule()
        run_git(child, "config", "core.filemode", "false", check=True)
        (child / "logic.py").chmod(0o755)
        self.assertEqual(run_git(child, "status", "--porcelain").stdout, b"")
        with self.assertRaisesRegex(RuntimeError, "submodule.*dirty"):
            inventory(self.root)
        # An excluded submodule must not be opened by source inventory.
        rows, _ = inventory(self.root, excludes=["dep space"])
        self.assertEqual([row["path"] for row in rows], [".gitmodules"])

    @unittest.skipIf(os.name == "nt", "POSIX mode-only end-to-end regression")
    def test_identity_changes_fail_both_delivery_protocols(self) -> None:
        from tests.unit import test_attempt_delivery, test_delivery
        from tests.support import make_target

        for protocol in ("legacy", "attempt"):
            for mutation in ("mode", "gitlink"):
                with self.subTest(protocol=protocol, mutation=mutation):
                    module = test_delivery if protocol == "legacy" else test_attempt_delivery
                    fixture_type = (
                        module.DeliveryTests
                        if protocol == "legacy"
                        else module.AttemptDeliveryTests
                    )
                    fixture = fixture_type()

                    def target_with_submodule(
                        *args,
                        mutation=mutation,
                        protocol=protocol,
                        **kwargs,
                    ):
                        result = make_target(*args, **kwargs)
                        self.root = result[1]
                        if mutation == "gitlink":
                            # Each subcase has an independent local origin.
                            origin = Path(self.temporary.name) / "origin"
                            if origin.exists():
                                origin.rename(origin.with_name(f"origin-{protocol}"))
                            self.submodule()
                        return result

                    with patch.object(module, "make_target", side_effect=target_with_submodule):
                        fixture.setUp()
                    try:
                        if protocol == "legacy":
                            command = ["verify-delivery", "--fix-dir", str(fixture.fix_dir)]
                        else:
                            attempt, _ = fixture._verified_attempt()
                            command = ["verify-attempt-delivery", "--attempt-dir", str(attempt)]
                        baseline = run_cli(*command, "--output-root", fixture.delivery_tmp.name)
                        self.assertEqual(baseline.returncode, 3, baseline.stderr)
                        if mutation == "mode":
                            (self.root / "app.py").chmod(0o755)
                            self.commit(self.root, "app.py")
                        else:
                            child = self.root / "dep space"
                            (child / "logic.py").write_text("VALUE = 2\n")
                            self.commit(child, "logic.py")
                            self.commit(self.root, "dep space")
                        result = run_cli(*command, "--output-root", fixture.delivery_tmp.name)
                        self.assertEqual(result.returncode, 4, result.stderr)
                        delivery_dir = json.loads(result.stdout)["deliveryDir"]
                        receipt = json.loads(
                            (Path(delivery_dir) / "delivery-attestation.json").read_text(
                                encoding="utf-8"
                            )
                        )
                        self.assertTrue(receipt["localSource"]["clean"])
                        self.assertFalse(receipt["localSource"]["sourceMatchesVerification"])
                        validated = run_cli("validate-delivery", "--delivery-dir", delivery_dir)
                        self.assertEqual(validated.returncode, 0, validated.stderr)
                    finally:
                        fixture.tearDown()


if __name__ == "__main__":
    unittest.main()
