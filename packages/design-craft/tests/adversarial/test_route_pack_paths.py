from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.design_craft.routing.path_policy import (
    normalize_manifest_path,
    validate_export_destination,
    validate_manifest_source_path,
)


class RoutePackPathPolicyTests(unittest.TestCase):
    def test_unsafe_manifest_paths_are_rejected(self) -> None:
        for value in ("", "/absolute", "../escape", "a/../escape", "a\\windows"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_manifest_path(value)

    def test_source_and_destination_symlinks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            outside = root / "outside"
            outside.mkdir()
            source = root / "source"
            export = root / "export"
            source.mkdir()
            export.mkdir()
            (source / "linked").symlink_to(outside, target_is_directory=True)
            (export / "linked").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                validate_manifest_source_path(source, "linked/file.json")
            with self.assertRaisesRegex(ValueError, "symlink"):
                validate_export_destination(export, "linked/file.json")


if __name__ == "__main__":
    unittest.main()
