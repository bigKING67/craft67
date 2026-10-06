from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_SOURCE = ROOT / "skills/review-craft"


class InstallationContractTests(unittest.TestCase):
    def test_readme_distinguishes_pinned_host_installation_paths(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        required_fragments = (
            "## Install for Codex CLI",
            "--repo bigKING67/review-craft",
            "--path skills/review-craft",
            "--ref <release-tag>",
            '--dest "$HOME/.agents/skills"',
            "$review-craft perform a bounded",
            "## Install for Claude Code",
            '"$HOME/.claude/skills/review-craft"',
            "/review-craft perform a bounded",
            "## Install for Pi",
            "pi install npm:@bigking67/review-craft",
            "pi --skill ./skills/review-craft",
            "/skill:review-craft perform a bounded",
            "## Install for Grok",
            "Grok discovers the shared `~/.agents/skills` root",
            "grok inspect",
            "/review-craft perform a bounded",
            ".codex-plugin/plugin.json",
            '{"ready": true',
            f'"version": "{version}"',
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, readme)

    def test_complete_skill_directory_runs_doctor_from_fresh_home(self) -> None:
        with tempfile.TemporaryDirectory(prefix="review-craft-install-") as temporary:
            home = Path(temporary)
            installed = home / ".agents/skills/review-craft"
            shutil.copytree(
                SKILL_SOURCE,
                installed,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )

            for relative in (
                "SKILL.md",
                "VERSION",
                "agents",
                "lib",
                "references",
                "schemas",
                "scripts",
                "templates",
            ):
                with self.subTest(relative=relative):
                    self.assertTrue((installed / relative).exists())

            environment = dict(os.environ)
            environment["HOME"] = str(home)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(installed / "scripts/review_craft.py"),
                    "doctor",
                    "--json",
                ],
                cwd=home,
                env=environment,
                text=True,
                capture_output=True,
                timeout=30,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertTrue(payload["ready"])
            self.assertEqual(
                payload["version"],
                (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
            )
            self.assertFalse(any(installed.rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main()
