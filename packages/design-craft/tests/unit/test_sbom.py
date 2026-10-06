from __future__ import annotations

import hashlib
import io
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.release.sbom import build_spdx
from tools.design_craft.repo import REPO_ROOT


class SbomTests(unittest.TestCase):
    def test_package_digest_and_file_inventory_are_bound(self) -> None:
        commit = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
        with tempfile.TemporaryDirectory() as raw:
            package = Path(raw) / "fixture.tgz"
            with tarfile.open(package, "w:gz") as archive:
                content = b"fixture\n"
                info = tarfile.TarInfo("package/SKILL.md")
                info.size = len(content)
                info.mtime = 0
                archive.addfile(info, io.BytesIO(content))
            payload = build_spdx(package, version="0.5.0", source_commit=commit)
            self.assertEqual(payload["spdxVersion"], "SPDX-2.3")
            self.assertEqual(len(payload["files"]), 1)
            self.assertEqual(
                payload["packages"][0]["checksums"][0]["algorithm"], "SHA256"
            )
            self.assertEqual(
                payload["packages"][0]["checksums"][0]["checksumValue"],
                hashlib.sha256(package.read_bytes()).hexdigest(),
            )

    def test_package_byte_tamper_changes_the_bound_digest(self) -> None:
        commit = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
        with tempfile.TemporaryDirectory() as raw:
            package = Path(raw) / "fixture.tgz"
            with tarfile.open(package, "w:gz") as archive:
                content = b"fixture\n"
                info = tarfile.TarInfo("package/SKILL.md")
                info.size = len(content)
                info.mtime = 0
                archive.addfile(info, io.BytesIO(content))
            before = build_spdx(package, version="0.5.0", source_commit=commit)
            package.write_bytes(package.read_bytes() + b"tampered")
            after = build_spdx(package, version="0.5.0", source_commit=commit)
            before_digest = before["packages"][0]["checksums"][0]["checksumValue"]
            after_digest = after["packages"][0]["checksums"][0]["checksumValue"]
            self.assertNotEqual(before_digest, after_digest)


if __name__ == "__main__":
    unittest.main()
