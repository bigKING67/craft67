"""Tests for optional host discovery checks."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from support import ROOT

HOST_SMOKE_PATH = ROOT / "scripts" / "host_smoke.py"
SPEC = importlib.util.spec_from_file_location(
    "creative_craft_host_smoke", HOST_SMOKE_PATH
)
assert SPEC and SPEC.loader
host_smoke = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = host_smoke
SPEC.loader.exec_module(host_smoke)


class GrokDiscoveryTests(unittest.TestCase):
    def test_accepts_exact_user_invocable_skill_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_file = Path(directory) / "creative-craft" / "SKILL.md"
            skill_file.parent.mkdir()
            skill_file.write_text("fixture\n", encoding="utf-8")
            payload = {
                "skills": [
                    {
                        "name": "creative-craft",
                        "source": {"type": "project", "path": str(skill_file)},
                        "userInvocable": True,
                    }
                ]
            }

            self.assertEqual(
                [], host_smoke.grok_discovery_errors(payload, skill_file)
            )

    def test_rejects_same_name_from_the_wrong_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = root / "expected" / "SKILL.md"
            other = root / "other" / "SKILL.md"
            payload = {
                "skills": [
                    {
                        "name": "creative-craft",
                        "source": {"type": "user", "path": str(other)},
                        "userInvocable": True,
                    }
                ]
            }

            errors = host_smoke.grok_discovery_errors(payload, expected)

            self.assertEqual(1, len(errors))
            self.assertIn("did not discover Creative Craft", errors[0])

    def test_rejects_non_invocable_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_file = Path(directory) / "creative-craft" / "SKILL.md"
            payload = {
                "skills": [
                    {
                        "name": "creative-craft",
                        "source": {"type": "project", "path": str(skill_file)},
                        "userInvocable": False,
                    }
                ]
            }

            errors = host_smoke.grok_discovery_errors(payload, skill_file)

            self.assertEqual(
                ["Grok discovered Creative Craft but did not mark it user-invocable"],
                errors,
            )


if __name__ == "__main__":
    unittest.main()
