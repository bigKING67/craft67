from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT


SCRIPT = REPO_ROOT / "skills/design-craft/scripts/design_craft_shadow_lab.py"
SPEC = importlib.util.spec_from_file_location("design_craft_shadow_lab_adversarial", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
shadow_lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shadow_lab)


def git(repo: Path, *arguments: str) -> None:
    completed = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", *arguments],
        cwd=repo,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_OPTIONAL_LOCKS": "0"},
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)


class ShadowLabBoundaryTests(unittest.TestCase):
    def test_cleanup_does_not_follow_a_nested_lab_symlink(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = parent / "source"
            repo.mkdir()
            git(repo, "init", "--quiet")
            git(repo, "config", "user.name", "Design Craft Tests")
            git(repo, "config", "user.email", "design-craft-tests@example.invalid")
            (repo / "app.txt").write_text("fixture\n")
            git(repo, "add", "app.txt")
            git(repo, "commit", "--quiet", "-m", "fixture")
            victim = parent / "must-survive.txt"
            victim.write_text("preserve\n")

            payload = shadow_lab.prepare_lab(
                source_path=repo,
                requested_ref="HEAD",
                output_root_path=parent / "labs",
            )
            manifest_path = Path(payload["manifest"]["isolation"]["manifest_path"])
            worktree = Path(payload["manifest"]["isolation"]["worktree"])
            (worktree / "hostile-link").symlink_to(victim)

            with self.assertRaisesRegex(shadow_lab.ShadowLabError, "symlink"):
                shadow_lab.verify_lab(manifest_path)

            cleanup = shadow_lab.cleanup_lab(manifest_path, confirm=True)
            self.assertTrue(cleanup["lab_removed"])
            self.assertEqual(victim.read_text(), "preserve\n")

    def test_manifest_cannot_retarget_cleanup_outside_the_owned_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = parent / "source"
            repo.mkdir()
            git(repo, "init", "--quiet")
            git(repo, "config", "user.name", "Design Craft Tests")
            git(repo, "config", "user.email", "design-craft-tests@example.invalid")
            (repo / "app.txt").write_text("fixture\n")
            git(repo, "add", "app.txt")
            git(repo, "commit", "--quiet", "-m", "fixture")
            payload = shadow_lab.prepare_lab(
                source_path=repo,
                requested_ref="HEAD",
                output_root_path=parent / "labs",
            )
            manifest_path = Path(payload["manifest"]["isolation"]["manifest_path"])
            victim = parent / "victim"
            victim.mkdir()
            (victim / "keep.txt").write_text("preserve\n")
            manifest = payload["manifest"]
            manifest["isolation"]["lab_dir"] = str(victim)
            manifest["isolation"]["worktree"] = str(victim / "source")
            manifest_path.write_text(shadow_lab.json_text(manifest), encoding="utf-8")

            with self.assertRaisesRegex(shadow_lab.ShadowLabError, "direct child"):
                shadow_lab.cleanup_lab(manifest_path, confirm=True)
            self.assertEqual((victim / "keep.txt").read_text(), "preserve\n")


if __name__ == "__main__":
    unittest.main()
