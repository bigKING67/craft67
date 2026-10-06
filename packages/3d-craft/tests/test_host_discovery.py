from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "host_discovery.py"


class HostDiscoveryTests(unittest.TestCase):
    @staticmethod
    def make_skill(root: Path) -> Path:
        skill = root / "candidate" / "3d-craft"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: 3d-craft\n---\n", encoding="utf-8")
        (skill / "VERSION").write_text("0.1.0\n", encoding="utf-8")
        return skill

    @staticmethod
    def make_executable(directory: Path, name: str, body: str) -> None:
        path = directory / name
        path.write_text("#!/usr/bin/env python3\n" + textwrap.dedent(body), encoding="utf-8")
        path.chmod(0o755)

    def install_fake_hosts(self, directory: Path, skill_file: Path) -> None:
        quoted = repr(str(skill_file))
        self.make_executable(
            directory,
            "codex",
            f"""
            import json
            import sys
            if sys.argv[1:] == ["--version"]:
                print("codex-cli 9.9.9")
            else:
                skill = {quoted}
                root = str(__import__('pathlib').Path(skill).parents[1])
                text = f"### Skill roots\\n- `r9` = `{{root}}`\\n### Available skills\\n- 3d-craft: fixture (file: r9/3d-craft/SKILL.md)"
                print(json.dumps([{{"type": "text", "text": text}}]))
            """,
        )
        self.make_executable(
            directory,
            "pi",
            f"""
            import json
            import sys
            if sys.argv[1:] == ["--version"]:
                print("0.80.6")
            else:
                sys.stdin.read()
                print(json.dumps({{"type": "response", "commands": [{{
                    "name": "skill:3d-craft",
                    "source": "skill",
                    "sourceInfo": {{"path": {quoted}}}
                }}]}}))
            """,
        )
        self.make_executable(
            directory,
            "grok",
            f"""
            import json
            import sys
            if sys.argv[1:] == ["--version"]:
                print("grok 1.0.5")
            else:
                print(json.dumps({{"skills": [{{
                    "name": "3d-craft",
                    "source": {{"type": "user", "path": {quoted}}}
                }}]}}))
            """,
        )

    def run_script(self, arguments: list[str], path: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PATH"] = path
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )

    def test_all_hosts_discover_exact_candidate_without_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = self.make_skill(root)
            binary_dir = root / "bin"
            binary_dir.mkdir()
            self.install_fake_hosts(binary_dir, skill / "SKILL.md")
            receipt = root / "evidence" / "host-discovery.json"

            result = self.run_script(
                [
                    "--skill-root",
                    str(skill),
                    "--workspace",
                    str(root),
                    "--output",
                    str(receipt),
                    "--json",
                ],
                f"{binary_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload, json.loads(receipt.read_text(encoding="utf-8")))
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual([item["discovery"] for item in payload["hosts"]], ["PASS", "PASS", "PASS"])
            self.assertEqual(payload["security"]["model_invocation"], "NOT_RUN")
            self.assertEqual(payload["security"]["credential_access"], "NOT_REQUESTED")

    def test_different_candidate_path_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = self.make_skill(root)
            other = root / "other" / "3d-craft"
            other.mkdir(parents=True)
            (other / "SKILL.md").write_text("---\nname: 3d-craft\n---\n", encoding="utf-8")
            binary_dir = root / "bin"
            binary_dir.mkdir()
            self.install_fake_hosts(binary_dir, other / "SKILL.md")

            result = self.run_script(
                ["--skill-root", str(expected), "--workspace", str(root), "--host", "codex", "--json"],
                f"{binary_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            )

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(payload["hosts"][0]["discovery"], "FAIL")
            self.assertIn("different candidate path", payload["hosts"][0]["detail"])

    def test_missing_host_is_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = self.make_skill(root)
            empty_path = root / "empty-bin"
            empty_path.mkdir()

            result = self.run_script(
                ["--skill-root", str(skill), "--workspace", str(root), "--host", "grok", "--json"],
                str(empty_path),
            )

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "UNVERIFIED")
            self.assertEqual(payload["hosts"][0]["discovery"], "UNVERIFIED")

    def test_refuses_receipt_inside_source_repository(self) -> None:
        result = self.run_script(
            [
                "--skill-root",
                str(ROOT / "skills" / "3d-craft"),
                "--output",
                str(ROOT / "host-discovery.json"),
                "--json",
            ],
            os.environ.get("PATH", ""),
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("outside the source repository", result.stderr)
        self.assertFalse((ROOT / "host-discovery.json").exists())


if __name__ == "__main__":
    unittest.main()
