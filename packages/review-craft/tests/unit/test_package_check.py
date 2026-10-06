from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from scripts.package_check import PackageCheckError, _resolve_command


class PackageCheckCommandTests(unittest.TestCase):
    def test_resolves_windows_command_shim_before_subprocess_launch(self) -> None:
        with patch(
            "scripts.package_check.shutil.which",
            return_value=r"C:\hostedtoolcache\node\npm.CMD",
        ) as which:
            command = _resolve_command(["npm", "install", "fixture.tgz"])

        self.assertEqual(
            command,
            [r"C:\hostedtoolcache\node\npm.CMD", "install", "fixture.tgz"],
        )
        which.assert_called_once_with("npm")

    def test_preserves_absolute_executable(self) -> None:
        with patch("scripts.package_check.shutil.which") as which:
            command = _resolve_command([sys.executable, "--version"])

        self.assertEqual(command, [sys.executable, "--version"])
        which.assert_not_called()

    def test_missing_command_has_explicit_error(self) -> None:
        with (
            patch("scripts.package_check.shutil.which", return_value=None),
            self.assertRaisesRegex(PackageCheckError, "command not found: npm"),
        ):
            _resolve_command(["npm", "install"])


if __name__ == "__main__":
    unittest.main()
