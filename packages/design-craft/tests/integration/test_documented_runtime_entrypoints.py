"""Loaded-Skill commands must work without a source-repository cwd."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools.design_craft.repo import REPO_ROOT


class RuntimeEntrypointTests(unittest.TestCase):
    def test_helpers_from_repo_target_and_standalone_skill(self) -> None:
        source_skill = REPO_ROOT / "skills/design-craft"
        with tempfile.TemporaryDirectory(prefix="design-craft-entrypoints-") as raw:
            root = Path(raw)
            target = root / "target with spaces"
            target.mkdir()
            standalone = root / "loaded skill"
            shutil.copytree(source_skill, standalone)
            for skill, cwd in (
                (source_skill, REPO_ROOT),
                (source_skill, target),
                (standalone, target),
            ):
                for helper in (
                    "design_craft_shadow_lab.py",
                    "design_craft_shadow_compare.py",
                    "design_craft_platform_scan.py",
                ):
                    with self.subTest(skill=skill, cwd=cwd, helper=helper):
                        result = subprocess.run(
                            [sys.executable, str(skill / "scripts" / helper), "--help"],
                            cwd=cwd,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                            capture_output=True, text=True, timeout=15,
                            check=False,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertIn("usage:", result.stdout.lower())
            self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
