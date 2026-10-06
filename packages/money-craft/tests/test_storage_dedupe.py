from __future__ import annotations

import errno
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ROOT / "scripts"))

import storage_check  # noqa: E402
import storage_dedupe  # noqa: E402
import tracking_workflow  # noqa: E402

PAYLOAD = b"evidence" * 20_000  # above the default size floor


def copy_clone(source: Path, destination: Path) -> None:
    shutil.copyfile(source, destination)


def make_writable(root: Path) -> None:
    for directory, dirs, _files in os.walk(root):
        for name in dirs:
            os.chmod(Path(directory) / name, 0o700)


class StorageDedupeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "local"
        self.root.mkdir()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(make_writable, Path(self.directory.name))

    def write(self, relative: str, data: bytes = PAYLOAD, mode: int = 0o644) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        os.chmod(path, mode)
        return path

    def seal(self, directory: Path) -> None:
        for path in directory.rglob("*"):
            os.chmod(path, 0o444 if path.is_file() else 0o555)
        os.chmod(directory, 0o555)

    def run_dedupe(self, **kwargs):
        return storage_dedupe.dedupe(self.root, clone=kwargs.pop("clone", copy_clone), **kwargs)

    def test_dry_run_reports_without_replacing(self) -> None:
        self.write("raw/a.pdf")
        second = self.write("runs/r1/body.bin")
        before = second.stat().st_ino
        result = self.run_dedupe()
        self.assertTrue(result["valid"])
        self.assertEqual(result["clones_planned"], 1)
        self.assertEqual(result["duplicate_bytes"], len(PAYLOAD))
        self.assertEqual(second.stat().st_ino, before)

    def test_apply_keeps_independent_inodes_modes_and_mtimes(self) -> None:
        keeper = self.write("raw/a.pdf")
        private = self.write("runs/r1/body.bin", mode=0o600)
        os.utime(private, ns=(1_000_000_000, 2_000_000_000))
        other = self.write("raw/b.pdf", PAYLOAD + b"!")
        before = private.stat().st_ino
        result = self.run_dedupe(apply=True)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["clones_created"], 1)
        after = private.stat()
        self.assertNotEqual(after.st_ino, before)
        self.assertNotEqual(after.st_ino, keeper.stat().st_ino)
        self.assertEqual(stat.S_IMODE(after.st_mode), 0o600)
        self.assertEqual(after.st_mtime_ns, 2_000_000_000)
        self.assertEqual(private.read_bytes(), PAYLOAD)
        self.assertEqual(other.read_bytes(), PAYLOAD + b"!")
        self.assertEqual(list(self.root.rglob(".*.dedup-*")), [])

    def test_sealed_and_read_only_files_are_sources_not_targets(self) -> None:
        sealed = self.write("archive/revisions/r0001/sources/S01/source-01.pdf")
        self.seal(sealed.parents[2])
        loose = self.write("tracking/revisions/r0002/thesis.pdf", mode=0o444)  # writable root, 0444 file
        copy = self.write("raw/a.pdf")
        seen = []
        result = self.run_dedupe(apply=True, clone=lambda s, d: (seen.append(s), copy_clone(s, d)))
        self.assertEqual(result["clones_created"], 1)
        self.assertEqual(result["non_replaceable_copies"], 1)
        self.assertEqual(len(seen), 1)
        self.assertIn(seen[0], {sealed, loose})
        self.assertEqual(stat.S_IMODE(loose.stat().st_mode), 0o444)
        self.assertEqual(stat.S_IMODE(copy.stat().st_mode), 0o644)

    def test_hard_linked_files_and_mutable_areas_are_left_alone(self) -> None:
        linked = self.write("raw/a.pdf")
        os.link(linked, self.root / "raw/a-link.pdf")
        other = self.write("raw/c.pdf")
        working = self.write("tracking/.working/track-1/body.bin")
        staging = self.write("tracking/.t1.staging.x/body.bin")
        before = linked.stat().st_ino
        result = self.run_dedupe(apply=True)
        self.assertEqual(result["clones_created"], 1)  # only raw/c.pdf; the hard-linked inode is the source
        self.assertEqual(result["mutable_areas_skipped"], 2)
        self.assertEqual(linked.stat().st_ino, before)
        self.assertEqual(linked.stat().st_nlink, 2)
        self.assertEqual(other.read_bytes(), PAYLOAD)
        self.assertEqual(working.stat().st_nlink, 1)
        self.assertTrue(staging.exists())

    def test_keeper_changed_after_hashing_is_rejected(self) -> None:
        self.write("raw/a.pdf")
        target = self.write("runs/r1/body.bin")
        before = target.stat().st_ino

        def mutating_clone(source: Path, destination: Path) -> None:
            destination.write_bytes(b"changed" + source.read_bytes()[7:])

        result = self.run_dedupe(apply=True, clone=mutating_clone)
        self.assertFalse(result["valid"])
        self.assertEqual(result["errors"], [{"path": "runs/r1/body.bin", "kind": "changed_during_scan"}])
        self.assertEqual(target.stat().st_ino, before)
        self.assertEqual(list(self.root.rglob(".*.dedup-*")), [])

    def test_unsupported_filesystem_stops_without_changes(self) -> None:
        self.write("raw/a.pdf")
        target = self.write("runs/r1/body.bin")
        self.write("raw/b.pdf", PAYLOAD * 2)
        other = self.write("runs/r2/body.bin", PAYLOAD * 2)
        before = (target.stat().st_ino, other.stat().st_ino)
        calls = []

        def unsupported(source: Path, _destination: Path) -> None:
            calls.append(source)
            raise OSError(errno.ENOTSUP, "not supported")

        result = self.run_dedupe(apply=True, clone=unsupported)
        self.assertFalse(result["valid"])
        self.assertEqual(result["clones_created"], 0)
        self.assertEqual(result["error_kinds"], {"clone_unsupported": 1})
        self.assertEqual(len(calls), 1)  # later groups are not attempted
        self.assertEqual((target.stat().st_ino, other.stat().st_ino), before)
        with mock.patch.object(storage_dedupe, "platform_clone", return_value=None):
            with self.assertRaises(storage_dedupe.StorageError):
                storage_dedupe.dedupe(self.root, apply=True)

    def test_target_changed_after_hashing_is_left_alone(self) -> None:
        self.write("raw/a.pdf")
        target = self.write("runs/r1/body.bin")
        before = target.stat().st_ino
        original = storage_dedupe.sha256_file

        def touch_after_hash(path: Path) -> str:
            digest = original(path)
            if path == target:
                os.utime(target, ns=(1, 1))
            return digest

        with mock.patch.object(storage_dedupe, "sha256_file", side_effect=touch_after_hash):
            result = self.run_dedupe(apply=True)
        self.assertEqual(result["errors"], [{"path": "runs/r1/body.bin", "kind": "changed_during_scan"}])
        self.assertEqual(target.stat().st_ino, before)

    def test_foreign_owner_and_root_bypass_are_not_replaceable(self) -> None:
        self.write("raw/a.pdf")
        target = self.write("runs/r1/body.bin")
        with mock.patch.object(storage_dedupe.os, "geteuid", return_value=target.stat().st_uid + 1):
            self.assertEqual(self.run_dedupe(apply=True)["clones_created"], 0)
        for sealed in (target.parent, self.root / "raw"):
            os.chmod(sealed, 0o555)  # sealed directories; root would still pass os.access
        with mock.patch.object(storage_dedupe.os, "access", return_value=True):
            result = self.run_dedupe(apply=True)
        self.assertEqual(result["clones_created"], 0)
        self.assertEqual(result["non_replaceable_copies"], 1)

    def test_cleanup_failure_is_recorded_without_aborting(self) -> None:
        self.write("raw/a.pdf")
        self.write("runs/r1/body.bin")
        with mock.patch.object(storage_dedupe.Path, "unlink", side_effect=PermissionError("denied")):
            result = self.run_dedupe(apply=True)
        self.assertEqual(result["clones_created"], 1)
        self.assertEqual(result["error_kinds"], {"cleanup_failed": 1})

    def test_linux_clone_keeps_errno_and_removes_destination(self) -> None:
        import fcntl

        source = self.write("raw/a.pdf")
        destination = self.root / "raw/clone.pdf"
        failure = OSError(errno.EOPNOTSUPP, "Operation not supported")
        with mock.patch.object(fcntl, "ioctl", side_effect=failure):
            with self.assertRaises(OSError) as caught:
                storage_dedupe._linux_clone(source, destination)
            self.assertEqual(caught.exception.errno, errno.EOPNOTSUPP)
            self.assertFalse(destination.exists())
            with mock.patch.object(storage_dedupe.Path, "unlink", side_effect=PermissionError("denied")):
                with self.assertRaises(OSError) as masked:
                    storage_dedupe._linux_clone(source, self.root / "raw/clone2.pdf")
            self.assertEqual(masked.exception.errno, errno.EOPNOTSUPP)
        self.assertIn(errno.EOPNOTSUPP, storage_dedupe.UNSUPPORTED_ERRNOS)
        self.assertIn(errno.ENOSYS, storage_dedupe.UNSUPPORTED_ERRNOS)

    def test_unreadable_file_is_reported_without_aborting(self) -> None:
        self.write("raw/a.pdf")
        self.write("runs/r1/body.bin")
        self.write("runs/r2/body.bin")
        original = storage_dedupe.sha256_file

        def flaky(path: Path) -> str:
            if "r2" in str(path):
                raise FileNotFoundError(str(path))
            return original(path)

        with mock.patch.object(storage_dedupe, "sha256_file", side_effect=flaky):
            result = self.run_dedupe(apply=True)
        self.assertEqual(result["clones_created"], 1)
        self.assertEqual(result["errors"], [{"path": "runs/r2/body.bin", "kind": "local_io_error"}])

    def test_small_files_and_invalid_roots(self) -> None:
        self.write("a.txt", b"x")
        self.write("b.txt", b"x")
        self.assertEqual(self.run_dedupe(apply=True)["clones_created"], 0)
        with self.assertRaises(storage_dedupe.StorageError):
            storage_dedupe.dedupe(self.root / "missing")
        link = Path(self.directory.name) / "link"
        link.symlink_to(self.root)
        with self.assertRaises(storage_dedupe.StorageError):
            storage_dedupe.dedupe(link)

    @unittest.skipUnless(sys.platform == "darwin" or sys.platform.startswith("linux"), "clonefile/FICLONE platforms")
    def test_real_platform_clone(self) -> None:
        keeper = self.write("raw/a.pdf")
        target = self.write("runs/r1/body.bin", mode=0o600)
        before = target.stat().st_ino
        result = storage_dedupe.dedupe(self.root, apply=True)
        if result["error_count"]:
            # Filesystems without reflinks (ext4, tmpfs) must fail closed: nothing replaced, no temp files.
            self.assertFalse(result["valid"])
            self.assertEqual(result["clones_created"], 0)
            self.assertEqual(result["errors"], [])  # clone_unsupported carries no path
            self.assertEqual(target.stat().st_ino, before)
            self.assertEqual(target.read_bytes(), PAYLOAD)
            self.assertEqual(list(self.root.rglob(".*.dedup-*")), [])
            self.skipTest(f"{sys.platform}: clone unsupported here; fail-closed path verified")
        self.assertEqual(result["clones_created"], 1)
        self.assertNotEqual(target.stat().st_ino, keeper.stat().st_ino)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertEqual(target.read_bytes(), PAYLOAD)

    def test_tree_removal_keeps_permissions_of_linked_sealed_file(self) -> None:
        sealed = self.write("archive/r0001/source.pdf")
        workspace = self.root / "workspace"
        workspace.mkdir()
        os.link(sealed, workspace / "source.pdf")
        self.seal(sealed.parent)
        tracking_workflow.remove_mutable_tree(workspace)
        self.assertFalse(workspace.exists())
        self.assertEqual(stat.S_IMODE(sealed.stat().st_mode), 0o444)
        self.assertEqual(sealed.stat().st_nlink, 1)

    def test_storage_inventory_counts_hard_links_once(self) -> None:
        first = self.write("raw/a.pdf")
        single = storage_check.size(self.root)
        os.link(first, self.root / "raw/b.pdf")
        self.assertEqual(storage_check.size(self.root), single)

    def test_cli_dry_run_receipt(self) -> None:
        self.write("raw/a.pdf")
        self.write("runs/r1/body.bin")
        env = {**os.environ, "MONEY_CRAFT_DATA_RUNTIME_ACTIVE": "1"}
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "money_craft.py"), "storage", "dedupe", "--root", str(self.root), "--json"],
            capture_output=True, text=True, env=env, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["schema"], "money-craft.storage-dedupe.v1")
        self.assertEqual(payload["clones_planned"], 1)
        self.assertNotIn(str(self.root), completed.stdout)  # receipt carries no absolute paths


if __name__ == "__main__":
    unittest.main()
