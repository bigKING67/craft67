from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upstream_diff.py"


class UpstreamDiffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.checkout = self.root / "checkout"
        self.checkout.mkdir()
        self.git("init", "--quiet")
        self.git("config", "user.name", "3D-Craft Test")
        self.git("config", "user.email", "test@3d-craft.invalid")
        self.git("remote", "add", "origin", "https://github.com/example/upstream.git")
        for name, content in {
            "README.md": "v1\n",
            "SKILL.md": "workflow v1\n",
            "LICENSE": "MIT\n",
        }.items():
            (self.checkout / name).write_text(content, encoding="utf-8")
        self.git("add", "README.md", "SKILL.md", "LICENSE")
        self.git("commit", "--quiet", "-m", "reviewed")
        self.locked_commit = self.git("rev-parse", "HEAD")
        self.lock_file = self.root / "upstreams.lock.json"
        self.lock_file.write_text(
            json.dumps(
                {
                    "schema": "3d-craft.upstreams.v1",
                    "reviewed_at": "2026-09-02",
                    "upstreams": [
                        {
                            "repo": "example/upstream",
                            "commit": self.locked_commit,
                            "license": "MIT",
                            "relationship": "absorbed_reference",
                            "freshness": {"strategy": "target-path-git-blob"},
                            "source_paths": ["README.md", "SKILL.md", "LICENSE"],
                            "absorbed_concepts": ["fixture"],
                            "copied_files": [],
                            "local_destinations": ["fixture"],
                            "validation_cases": ["fixture"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(self.checkout), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def audit(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--repo",
                "example/upstream",
                "--checkout",
                str(self.checkout),
                "--lock-file",
                str(self.lock_file),
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_classifies_current_and_head_only_change(self) -> None:
        current = self.audit()
        self.assertEqual(current.returncode, 0, current.stderr)
        self.assertEqual(json.loads(current.stdout)["status"], "CURRENT")

        (self.checkout / "unrelated.txt").write_text("noise\n", encoding="utf-8")
        self.git("add", "unrelated.txt")
        self.git("commit", "--quiet", "-m", "unrelated")
        head_only = self.audit()
        self.assertEqual(head_only.returncode, 0, head_only.stderr)
        self.assertEqual(json.loads(head_only.stdout)["status"], "HEAD_ONLY_CHANGED")
        self.assertTrue(all(item["status"] == "SAME" for item in json.loads(head_only.stdout)["paths"]))

    def test_relevant_path_change_requires_review(self) -> None:
        (self.checkout / "README.md").write_text("v2\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "--quiet", "-m", "relevant")
        changed = self.audit()
        payload = json.loads(changed.stdout)
        self.assertEqual(changed.returncode, 3, changed.stderr)
        self.assertEqual(payload["status"], "TARGET_PATH_CHANGED")
        states = {item["path"]: item["status"] for item in payload["paths"]}
        self.assertEqual(states["README.md"], "CHANGED")
        self.assertEqual(states["SKILL.md"], "SAME")

    def test_origin_mismatch_fails_closed(self) -> None:
        self.git("remote", "set-url", "origin", "https://github.com/other/repo.git")
        result = self.audit()
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(payload["status"], "UNVERIFIED")
        self.assertIn("origin mismatch", payload["error"])

    def test_maintainer_guide_retains_the_research_watchlist(self) -> None:
        guide = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
        expected = {
            "ifBars/blender-agent-studio",
            "RobLe3/cc-blender-skill",
            "EnzeD/r3f-skills",
            "img2threejs/img2threejs",
            "KhronosGroup/glTF-Validator",
            "ra100/blender-claude-plugin",
            "arjun988/blender-skills",
            "TMHSDigital/Blender-Developer-Tools",
            "DmitriyGolub/threejs-devtools-mcp",
            "ahujasid/blender-mcp",
            "greensock/gsap-skills",
            "majidmanzarpour/threejs-game-skills",
            "MengTo/Skills",
        }
        for repo in expected:
            self.assertIn(repo, guide)


if __name__ == "__main__":
    unittest.main()
