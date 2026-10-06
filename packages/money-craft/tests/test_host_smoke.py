from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import host_smoke  # noqa: E402
import install_skill  # noqa: E402


def install_fixture(destination: Path) -> None:
    shutil.copytree(ROOT / "skills" / "money-craft", destination)
    provenance = {
        "schema": "money-craft.install-provenance.v1",
        "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "source_skill_sha256": install_skill.tree_sha256(ROOT / "skills" / "money-craft"),
    }
    (destination / "INSTALL_PROVENANCE.json").write_text(
        json.dumps(provenance),
        encoding="utf-8",
    )


class HostDiscoveryParserTests(unittest.TestCase):
    def test_codex_model_visible_catalog(self) -> None:
        output = json.dumps(
            [
                {
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "- `r1` = `/tmp/.agents/skills`\n"
                                "- money-craft: research (file: r1/money-craft/SKILL.md)"
                            ),
                        }
                    ]
                }
            ]
        )
        self.assertTrue(host_smoke.parse_codex_discovery(output))
        self.assertFalse(host_smoke.parse_codex_discovery("[]"))
        decoy = output.replace("/tmp/.agents/skills", "/tmp/.codex/skills")
        self.assertFalse(host_smoke.parse_codex_discovery(decoy))

    def test_pi_rpc_commands(self) -> None:
        output = json.dumps(
            {
                "type": "response",
                "command": "get_commands",
                "success": True,
                "data": {
                    "commands": [
                        {
                            "name": "skill:money-craft",
                            "sourceInfo": {"path": "/tmp/.agents/skills/money-craft/SKILL.md"},
                        }
                    ]
                },
            }
        )
        self.assertTrue(host_smoke.parse_pi_discovery(output))
        self.assertFalse(host_smoke.parse_pi_discovery('{"type":"response","command":"other"}'))

    def test_pi_rpc_ignores_discovery_root_backup(self) -> None:
        output = json.dumps(
            {
                "type": "response",
                "command": "get_commands",
                "success": True,
                "data": {
                    "commands": [
                        {
                            "name": "skill:money-craft",
                            "sourceInfo": {
                                "path": "/tmp/.agents/skills/.money-craft.backup/SKILL.md"
                            },
                        },
                        {
                            "name": "skill:money-craft",
                            "sourceInfo": {"path": "/tmp/.agents/skills/money-craft/SKILL.md"},
                        },
                    ]
                },
            }
        )
        self.assertTrue(host_smoke.parse_pi_discovery(output))

    def test_grok_inspect(self) -> None:
        output = json.dumps(
            {
                "skills": [
                    {
                        "name": "money-craft",
                        "source": {"path": "/tmp/.agents/skills/money-craft/SKILL.md"},
                    }
                ]
            }
        )
        self.assertTrue(host_smoke.parse_grok_discovery(output))
        self.assertFalse(host_smoke.parse_grok_discovery('{"skills":[]}'))

    def test_grok_inspect_ignores_discovery_root_backup(self) -> None:
        output = json.dumps(
            {
                "skills": [
                    {
                        "name": "money-craft",
                        "source": {"path": "/tmp/.agents/skills/.money-craft.backup/SKILL.md"},
                    },
                    {
                        "name": "money-craft",
                        "source": {"path": "/tmp/.agents/skills/money-craft/SKILL.md"},
                    },
                ]
            }
        )
        self.assertTrue(host_smoke.parse_grok_discovery(output))


class HostDiscoveryGateTests(unittest.TestCase):
    def test_model_free_discovery_gate(self) -> None:
        codex_output = json.dumps(
            [
                {
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "- `r1` = `/tmp/.agents/skills`\n"
                                "- money-craft: research (file: r1/money-craft/SKILL.md)"
                            ),
                        }
                    ]
                }
            ]
        )
        pi_output = json.dumps(
            {
                "type": "response",
                "command": "get_commands",
                "success": True,
                "data": {
                    "commands": [
                        {
                            "name": "skill:money-craft",
                            "sourceInfo": {"path": "/tmp/.agents/skills/money-craft/SKILL.md"},
                        }
                    ]
                },
            }
        )
        grok_output = json.dumps(
            {
                "skills": [
                    {
                        "name": "money-craft",
                        "source": {"path": "/tmp/.agents/skills/money-craft/SKILL.md"},
                    }
                ]
            }
        )

        def fake_runner(
            command: list[str],
            *,
            input_text: str | None = None,
            max_output_chars: int = 1000,
        ) -> tuple[int, str]:
            del max_output_chars
            if command[:3] == ["codex", "debug", "prompt-input"]:
                return 0, codex_output
            if command[0] == "pi":
                self.assertIn("get_commands", input_text or "")
                return 0, pi_output
            if command[:3] == ["grok", "inspect", "--json"]:
                return 0, grok_output
            if command[0] == sys.executable:
                return 0, json.dumps({"runtime_valid": True})
            raise AssertionError(f"unexpected command: {command}")

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            install_fixture(home / ".agents" / "skills" / "money-craft")
            install_fixture(home / ".claude" / "skills" / "money-craft")
            with mock.patch.object(host_smoke.shutil, "which", return_value="/fixture/bin/host"):
                result = host_smoke.validate(
                    False,
                    True,
                    home=home,
                    runner=fake_runner,
                )

        self.assertTrue(result["valid"])
        self.assertTrue(result["discovery_tested"])
        self.assertEqual(result["discovery"]["shared_agents"]["status"], "passed")
        self.assertEqual(result["discovery"]["codex"]["status"], "passed")
        self.assertEqual(result["discovery"]["pi"]["status"], "passed")
        self.assertEqual(result["discovery"]["grok"]["status"], "passed")
        self.assertEqual(result["discovery"]["claude"]["status"], "partial")
        self.assertFalse(result["fresh_session_tested"])

    def test_shared_agents_compatibility_fails_closed_on_installed_drift(self) -> None:
        def fake_runner(
            command: list[str],
            *,
            input_text: str | None = None,
            max_output_chars: int = 1000,
        ) -> tuple[int, str]:
            del command, input_text, max_output_chars
            return 0, json.dumps({"runtime_valid": True})

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            installed = home / ".agents" / "skills" / "money-craft"
            install_fixture(installed)
            with (installed / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\ninstalled drift\n")
            checks: list[str] = []
            errors: list[str] = []
            discovery: dict[str, dict[str, object]] = {}
            host_smoke.validate_shared_agents_compatibility(
                home=home,
                checks=checks,
                errors=errors,
                discovery=discovery,
                runner=fake_runner,
            )

        self.assertEqual(
            errors,
            ["Shared Agent Skills installation does not match the canonical Skill"],
        )
        self.assertEqual(discovery["shared_agents"]["status"], "failed")

    def test_claude_compatibility_fails_closed_on_installed_drift(self) -> None:
        def fake_runner(
            command: list[str],
            *,
            input_text: str | None = None,
            max_output_chars: int = 1000,
        ) -> tuple[int, str]:
            del command, input_text, max_output_chars
            return 0, json.dumps({"runtime_valid": True})

        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            installed = home / ".claude" / "skills" / "money-craft"
            install_fixture(installed)
            with (installed / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\ninstalled drift\n")
            checks: list[str] = []
            errors: list[str] = []
            warnings: list[str] = []
            discovery: dict[str, dict[str, object]] = {}
            host_smoke.validate_claude_compatibility(
                home=home,
                checks=checks,
                errors=errors,
                warnings=warnings,
                discovery=discovery,
                runner=fake_runner,
            )

        self.assertEqual(
            errors,
            ["Claude compatibility installation does not match the canonical Skill"],
        )
        self.assertEqual(discovery["claude"]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
