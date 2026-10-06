from __future__ import annotations

import gzip
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.release.native_archive import (
    inspect_archive,
    regular_tar_info,
    safe_relative,
    write_deterministic_tar,
)


def write_archive(
    output: Path,
    entries: list[tuple[tarfile.TarInfo, bytes]],
    *,
    archive_format: int = tarfile.USTAR_FORMAT,
) -> None:
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(
                fileobj=zipped, mode="w", format=archive_format
            ) as archive:
                for info, content in entries:
                    archive.addfile(info, io.BytesIO(content) if info.isfile() else None)


class NativeArchiveTests(unittest.TestCase):
    def test_relative_path_policy_rejects_cross_platform_escape_forms(self) -> None:
        for value in (
            "",
            "/absolute",
            "../escape",
            "a/../escape",
            "a//b",
            "a/./b",
            "C:/escape",
            "C:\\escape",
            "\\\\server\\share",
            "directory/",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_relative(value)

    def test_deterministic_writer_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            files = {"b.txt": b"b", "a.txt": b"a"}
            first = root / "first.tgz"
            second = root / "second.tgz"
            write_deterministic_tar(files, first)
            write_deterministic_tar(files, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            entries, errors = inspect_archive(first)
            self.assertEqual(errors, [])
            self.assertEqual(entries, files)

    def test_links_devices_duplicates_and_traversal_are_rejected(self) -> None:
        base = regular_tar_info("valid.txt", 5)
        mutations: list[tuple[str, list[tuple[tarfile.TarInfo, bytes]], str]] = []
        duplicate = regular_tar_info("valid.txt", 5)
        mutations.append(
            ("duplicate", [(base, b"valid"), (duplicate, b"again")], "duplicate")
        )
        traversal = tarfile.TarInfo("../escape.txt")
        traversal.size = 1
        traversal.mode = 0o644
        mutations.append(("traversal", [(traversal, b"x")], "unsafe"))
        for label, member_type in (
            ("symlink", tarfile.SYMTYPE),
            ("hardlink", tarfile.LNKTYPE),
            ("device", tarfile.CHRTYPE),
        ):
            special = regular_tar_info(f"{label}.entry", 0)
            special.type = member_type
            special.linkname = "valid.txt" if label != "device" else ""
            mutations.append((label, [(special, b"")], "regular file"))
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for label, entries, expected in mutations:
                with self.subTest(label=label):
                    output = root / f"{label}.tgz"
                    write_archive(output, entries)
                    _, errors = inspect_archive(output)
                    self.assertTrue(any(expected in error for error in errors), errors)

    def test_non_normalized_metadata_is_rejected(self) -> None:
        mutations = {
            "mode": ("mode", 0o600),
            "mtime": ("mtime", 1),
            "uid": ("uid", 1),
            "gid": ("gid", 1),
            "uname": ("uname", "owner"),
            "gname": ("gname", "group"),
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for label, (field, value) in mutations.items():
                with self.subTest(label=label):
                    info = regular_tar_info("file.txt", 1)
                    setattr(info, field, value)
                    output = root / f"{label}.tgz"
                    write_archive(output, [(info, b"x")])
                    _, errors = inspect_archive(output)
                    self.assertTrue(errors)

    def test_pax_headers_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "pax.tgz"
            info = regular_tar_info("file.txt", 1)
            info.pax_headers = {"comment": "not-normalized"}
            write_archive(output, [(info, b"x")], archive_format=tarfile.PAX_FORMAT)
            _, errors = inspect_archive(output)
            self.assertTrue(any("PAX" in error for error in errors), errors)

    def test_archive_resource_limits_are_enforced_before_unbounded_reads(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            archive = root / "limits.tgz"
            entries = [
                (regular_tar_info(f"{index}.txt", 4), b"data")
                for index in range(3)
            ]
            write_archive(archive, entries)
            _, count_errors = inspect_archive(archive, max_entries=2)
            _, member_errors = inspect_archive(archive, max_member_bytes=3)
            _, total_errors = inspect_archive(archive, max_total_bytes=7)
            _, compressed_errors = inspect_archive(archive, max_archive_bytes=1)
            self.assertTrue(any("too many" in error for error in count_errors))
            self.assertTrue(any("member is too large" in error for error in member_errors))
            self.assertTrue(any("content is too large" in error for error in total_errors))
            self.assertTrue(any("compressed archive" in error for error in compressed_errors))

    def test_truncated_and_corrupt_archives_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            corrupt = root / "corrupt.tgz"
            corrupt.write_bytes(b"not a gzip archive")
            _, corrupt_errors = inspect_archive(corrupt)
            self.assertTrue(any("cannot read" in error for error in corrupt_errors))
            valid = root / "valid.tgz"
            write_deterministic_tar({"file.txt": b"data"}, valid)
            truncated = root / "truncated.tgz"
            truncated.write_bytes(valid.read_bytes()[:20])
            _, truncated_errors = inspect_archive(truncated)
            self.assertTrue(any("cannot read" in error for error in truncated_errors))


if __name__ == "__main__":
    unittest.main()
