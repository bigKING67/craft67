from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.support import RUNTIME_LIB, git_init

sys.path.insert(0, str(RUNTIME_LIB))

import review_craft.repository as repository
from review_craft.repository import (
    fingerprint_inventory,
    inventory,
    safe_remote,
    worktree_fingerprint,
)
from review_craft.repository_analysis import (
    build_dependency_map,
    build_module_map,
    detect_profile,
)


class RepositoryTests(unittest.TestCase):
    def test_safe_remote_strips_credentials_from_supported_remote_forms(self) -> None:
        cases = {
            "https://user:secret@example.invalid/owner/repo.git": (
                "https://example.invalid/owner/repo.git"
            ),
            "ssh://user:secret@example.invalid/owner/repo.git": (
                "ssh://example.invalid/owner/repo.git"
            ),
            "ftp://user:secret@example.invalid/owner/repo.git": (
                "ftp://example.invalid/owner/repo.git"
            ),
            "https://example.invalid/owner/repo.git?access_token=secret#fragment": (
                "https://example.invalid/owner/repo.git"
            ),
            "git@example.invalid:owner/repo.git": "example.invalid:owner/repo.git",
            "git@example.invalid:owner/repo.git?token=secret#fragment": (
                "example.invalid:owner/repo.git"
            ),
        }
        for remote, expected in cases.items():
            with self.subTest(remote=remote):
                self.assertEqual(safe_remote(remote), expected)

    def test_safe_remote_fails_closed_for_malformed_credential_bearing_values(self) -> None:
        remotes = (
            "https:///user:secret@example.invalid/owner/repo.git",
            "https://user:secret@example.invalid:not-a-port/owner/repo.git",
            "user:secret@example.invalid/owner/repo.git",
            "file:///private/repository.git",
        )
        for remote in remotes:
            with self.subTest(remote=remote):
                self.assertIsNone(safe_remote(remote))

    def test_inventory_is_sorted_and_excludes_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "z.py").write_text("z = 1\n", encoding="utf-8")
            (root / "a.py").write_text("a = 1\n", encoding="utf-8")
            (root / "dist").mkdir()
            (root / "dist/out.js").write_text("generated\n", encoding="utf-8")
            records, excluded = inventory(root)
            self.assertEqual([row["path"] for row in records], ["a.py", "z.py"])
            self.assertEqual([row["path"] for row in excluded], ["dist/out.js"])

    def test_inventory_records_symlink_without_following_it(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            target = Path(outside) / "secret.txt"
            target.write_text("outside\n", encoding="utf-8")
            try:
                (root / "link").symlink_to(target)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            records, _ = inventory(root)
            self.assertEqual(records[0]["kind"], "symlink")
            self.assertEqual(records[0]["linkTarget"], os.readlink(root / "link"))

    def test_inventory_accepts_utf8_character_split_at_preview_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "performance.md").write_bytes(
                b"a" * 8191 + "盘".encode() + b"\n"
            )
            records, _ = inventory(root)
            self.assertFalse(records[0]["binary"])

    def test_inventory_rejects_invalid_utf8_nul_and_incomplete_eof(self) -> None:
        cases = {
            "invalid.bin": b"a" * 100 + b"\xff",
            "nul.bin": b"a" * 100 + b"\0",
            "incomplete.bin": b"a" * 8191 + b"\xe7",
        }
        for name, payload in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / name).write_bytes(payload)
                records, _ = inventory(root)
                self.assertTrue(records[0]["binary"])

    def test_deleted_revision_accepts_utf8_split_at_preview_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "performance.md"
            path.write_bytes(b"a" * 8191 + "盘".encode() + b"\n")
            git_init(root)
            repository.run_git(root, "add", "--", path.name, check=True)
            repository.run_git(root, "commit", "-m", "fixture", check=True)
            record = repository._file_record_at_revision(root, "HEAD", path.name)
            self.assertFalse(record["binary"])

    def test_fingerprint_ignores_input_order(self) -> None:
        rows = [
            {"path": "b", "kind": "file", "sha256": "b" * 64, "classification": "source"},
            {"path": "a", "kind": "file", "sha256": "a" * 64, "classification": "source"},
        ]
        self.assertEqual(fingerprint_inventory(rows), fingerprint_inventory(list(reversed(rows))))

    def test_worktree_fingerprint_never_opens_out_of_scope_or_excluded_content(self) -> None:
        for is_git in (False, True):
            with self.subTest(is_git=is_git), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "src").mkdir()
                included = root / "src/app.py"
                excluded = root / "src/private.json"
                out_of_scope = root / "auth.json"
                included.write_text("VALUE = 1\n", encoding="utf-8")
                excluded.write_text('{"token":"private-v1"}\n', encoding="utf-8")
                out_of_scope.write_text('{"token":"outside-v1"}\n', encoding="utf-8")
                if is_git:
                    git_init(root)
                    repository.run_git(root, "add", "--", ".", check=True)
                    repository.run_git(root, "commit", "-m", "fixture", check=True)
                configuration = {
                    "mode": "review",
                    "scope": ["src"],
                    "exclude": ["src/private.json"],
                    "generated": [],
                    "vendored": [],
                    "diffBase": None,
                }

                with mock.patch.object(
                    repository, "_file_record", wraps=repository._file_record
                ) as reader:
                    before = worktree_fingerprint(root, configuration=configuration)
                self.assertEqual([call.args[1] for call in reader.call_args_list], ["src/app.py"])

                excluded.write_text('{"token":"private-v2-longer"}\n', encoding="utf-8")
                out_of_scope.write_text('{"token":"outside-v2-longer"}\n', encoding="utf-8")
                self.assertEqual(
                    worktree_fingerprint(root, configuration=configuration),
                    before,
                )

                included.write_text("VALUE = 2\n", encoding="utf-8")
                self.assertNotEqual(
                    worktree_fingerprint(root, configuration=configuration),
                    before,
                )

    def test_review_fingerprint_is_stable_when_a_deletion_is_committed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            removed = root / "removed.py"
            removed.write_text("REMOVE = True\n", encoding="utf-8")
            git_init(root)
            repository.run_git(root, "add", "--", ".", check=True)
            repository.run_git(root, "commit", "-m", "fixture", check=True)

            removed.unlink()
            diff_records, _, _ = repository.inventory_for_mode(
                root,
                mode="diff",
                diff_base="HEAD",
            )
            self.assertEqual(
                [(row["path"], row["kind"], row["diffStatus"]) for row in diff_records],
                [("removed.py", "deleted", "D")],
            )
            before_commit = worktree_fingerprint(root)

            repository.run_git(root, "add", "--", removed.name, check=True)
            repository.run_git(root, "commit", "-m", "remove fixture", check=True)
            self.assertEqual(worktree_fingerprint(root), before_commit)

    def test_repository_maps_capture_local_python_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src/a.py").write_text("from . import b\n", encoding="utf-8")
            (root / "src/b.py").write_text("VALUE = 1\n", encoding="utf-8")
            records, _ = inventory(root)
            module_map = build_module_map(records)
            dependency_map = build_dependency_map(root, records)
            self.assertEqual(module_map["modules"][0]["fileCount"], 2)
            self.assertEqual(
                dependency_map["edges"],
                [
                    {
                        "from": "src/a.py",
                        "to": "src/b.py",
                        "kind": "python-import",
                        "line": 1,
                    }
                ],
            )

    def test_agent_skill_maps_preserve_runtime_capability_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                "skills/demo/lib/demo/cli.py": "def main():\n    return 0\n",
                "skills/demo/scripts/tool.py": "from demo.cli import main\n",
                "skills/demo/schemas/run.schema.json": "{}\n",
                "skills/demo/references/workflow.md": "# Workflow\n",
            }
            for relative, content in paths.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            records, _ = inventory(root)
            module_map = build_module_map(records)
            dependency_map = build_dependency_map(root, records)
            self.assertEqual(
                {row["id"] for row in module_map["modules"]},
                {
                    "skills/demo/lib",
                    "skills/demo/references",
                    "skills/demo/schemas",
                    "skills/demo/scripts",
                },
            )
            self.assertEqual(
                dependency_map["moduleEdges"],
                [
                    {
                        "from": "skills/demo/scripts",
                        "to": "skills/demo/lib",
                        "count": 1,
                    }
                ],
            )

    def test_auto_profile_uses_repository_signals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(
                '{"dependencies":{"react":"1"}}\n', encoding="utf-8"
            )
            (root / "index.html").write_text("<main></main>\n", encoding="utf-8")
            records, _ = inventory(root)
            profile = detect_profile(root, records, "auto")
            self.assertEqual(profile["resolved"], "frontend")
            self.assertEqual(profile["confidence"], "MEDIUM")


if __name__ == "__main__":
    unittest.main()
