"""Domain-focused Creative Craft regression tests."""

from __future__ import annotations

import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import (
    ROOT,
    build_release,
    installer,
    package_smoke,
)


class ReleaseReceiptTests(unittest.TestCase):
    def test_release_receipt_argv_redacts_local_absolute_paths(self) -> None:
        outside = Path.home() / "private-workspace" / "artifact.tgz"
        normalized = build_release.normalize_receipt_argv(
            [
                sys.executable,
                str(ROOT / "scripts/validate.py"),
                str(outside),
                "--json",
            ]
        )
        self.assertEqual("<python>", normalized[0])
        self.assertEqual("<repo>/scripts/validate.py", normalized[1])
        self.assertEqual("<absolute>/artifact.tgz", normalized[2])
        self.assertEqual("--json", normalized[3])
        serialized = json.dumps(normalized)
        self.assertNotIn(str(Path.home()), serialized)
        self.assertNotIn(str(ROOT), serialized)


class PackageSmokeTests(unittest.TestCase):
    @staticmethod
    def write_tar_member(
        archive: tarfile.TarFile,
        name: str,
        payload: bytes = b"fixture\n",
        *,
        member_type: bytes = tarfile.REGTYPE,
        linkname: str = "",
    ) -> None:
        member = tarfile.TarInfo(name)
        member.type = member_type
        member.linkname = linkname
        if member_type == tarfile.REGTYPE:
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
        else:
            archive.addfile(member)

    def test_safe_extract_package_accepts_regular_package_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "fixture.tgz"
            with tarfile.open(package, "w:gz") as archive:
                self.write_tar_member(
                    archive,
                    "package/skills/creative-craft/SKILL.md",
                )
            destination = root / "extracted"
            package_smoke.safe_extract_package(package, destination)
            self.assertEqual(
                b"fixture\n",
                (destination / "package/skills/creative-craft/SKILL.md").read_bytes(),
            )

    def test_safe_extract_package_rejects_escape_and_link_members(self) -> None:
        cases = (
            ("../escape", tarfile.REGTYPE, ""),
            ("/absolute", tarfile.REGTYPE, ""),
            ("package/link", tarfile.SYMTYPE, "../../escape"),
            ("package/hardlink", tarfile.LNKTYPE, "package/target"),
        )
        for name, member_type, linkname in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                package = root / "unsafe.tgz"
                with tarfile.open(package, "w:gz") as archive:
                    self.write_tar_member(
                        archive,
                        name,
                        member_type=member_type,
                        linkname=linkname,
                    )
                with self.assertRaisesRegex(ValueError, "unsafe|links are not allowed"):
                    package_smoke.safe_extract_package(package, root / "extracted")
                self.assertFalse((root / "escape").exists())

    def test_safe_extract_package_enforces_total_bytes_before_writing(self) -> None:
        limit = package_smoke.MAX_ARCHIVE_BYTES
        # Two highly compressible members exercise cumulative expanded bytes,
        # including the exact boundary and a one-byte overrun in the last file.
        for extra in (0, 1):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                package = root / "size-boundary.tgz"
                first = b"a" * (limit // 2)
                second = b"b" * (limit - len(first) + extra)
                with tarfile.open(package, "w:gz") as archive:
                    self.write_tar_member(archive, "package/first", first)
                    self.write_tar_member(archive, "package/second", second)
                self.assertLess(package.stat().st_size, limit // 10)
                destination = root / "extracted"
                if extra:
                    with self.assertRaisesRegex(ValueError, "archive expands beyond"):
                        package_smoke.safe_extract_package(package, destination)
                    self.assertEqual([], list(destination.iterdir()))
                else:
                    package_smoke.safe_extract_package(package, destination)
                    self.assertEqual(first, (destination / "package/first").read_bytes())
                    self.assertEqual(second, (destination / "package/second").read_bytes())

    def test_safe_extract_package_enforces_member_count_before_writing(self) -> None:
        for extra in (0, 1):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                package = root / "member-boundary.tgz"
                count = package_smoke.MAX_ARCHIVE_MEMBERS + extra
                with tarfile.open(package, "w:gz") as archive:
                    for index in range(count):
                        self.write_tar_member(archive, f"package/{index}", b"")
                destination = root / "extracted"
                if extra:
                    with self.assertRaisesRegex(ValueError, "members; limit is"):
                        package_smoke.safe_extract_package(package, destination)
                    self.assertEqual([], list(destination.iterdir()))
                else:
                    package_smoke.safe_extract_package(package, destination)
                    self.assertEqual(count, len(list((destination / "package").iterdir())))


class InstallerTests(unittest.TestCase):
    def test_atomic_install_writes_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination, backup = installer.install(Path(directory), False)
            self.assertIsNone(backup)
            self.assertTrue((destination / "SKILL.md").is_file())
            provenance = json.loads((destination / "INSTALL_PROVENANCE.json").read_text())
            self.assertEqual(provenance["source_repository"], "https://github.com/bigKING67/craft67")
            self.assertEqual(provenance["source_subdirectory"], "packages/creative-craft/skills/creative-craft")

    def test_failed_force_install_preserves_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "creative-craft"
            destination.mkdir()
            marker = destination / "marker.txt"
            marker.write_text("preserve", encoding="utf-8")
            with (
                mock.patch.object(
                    installer, "validate_staging", side_effect=RuntimeError("boom")
                ),
                self.assertRaises(RuntimeError),
            ):
                installer.install(Path(directory), True)
            self.assertEqual("preserve", marker.read_text(encoding="utf-8"))
