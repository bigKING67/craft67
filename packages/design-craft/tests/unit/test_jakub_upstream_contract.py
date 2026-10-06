from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.design_craft.repo import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from design_craft_absorption_common import validate_review_state  # noqa: E402
from upstream_absorption_report import build_report, categorize_changed_file  # noqa: E402


NAME = "jakubkrehel-skills"


class JakubUpstreamContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.meta = json.loads((REPO_ROOT / "upstreams.lock.json").read_text())["upstreams"][NAME]
        self.upstream = REPO_ROOT / self.meta["path"]

    def test_registered_snapshot_and_review_state(self) -> None:
        _state, errors = validate_review_state(NAME, self.meta, self.upstream)
        self.assertEqual(errors, [])
        self.assertEqual(self.meta["coverage_contract"], "design-craft.jakub-absorption.v1")
        self.assertTrue((REPO_ROOT / self.meta["coverage_matrix"]).is_file())
        result = subprocess.run(
            ["git", "config", "--file", str(REPO_ROOT / ".gitmodules"),
             "--get", f"submodule.{self.meta['path']}.url"],
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(result.stdout.strip(), self.meta["repo"])

    def test_inventory_and_selected_source_integrity(self) -> None:
        inventory = self.meta["skill_inventory"]
        actual = sorted(p.parent.name for p in (self.upstream / "skills").glob("*/SKILL.md"))
        self.assertTrue(actual)
        self.assertEqual(inventory["skills"], actual)
        decisions = inventory["entrypoint_decisions"]
        self.assertEqual(set(decisions), set(actual))
        selected = {name for name, status in decisions.items() if status == "partial"}
        self.assertEqual(selected, {"better-writing", "break"})
        self.assertEqual(set(decisions.values()), {"partial", "deferred"})
        self.assertEqual(self.meta["cumulative_status"], "selective_absorbed")
        self.assertEqual(set(inventory["local_coverage"]), selected)
        for path in inventory["local_coverage"].values():
            self.assertTrue(path.startswith("skills/design-craft/references/"))
            self.assertTrue((REPO_ROOT / path).is_file())
        hashes = inventory["reviewed_source_sha256"]
        self.assertEqual(set(hashes), {
            "skills/better-writing/SKILL.md", "skills/break/SKILL.md",
            "skills/break/scenarios.md", "LICENSE",
        })
        for path, expected in hashes.items():
            self.assertEqual(hashlib.sha256((self.upstream / path).read_bytes()).hexdigest(), expected)

    def test_report_detects_unreviewed_remote_without_advancing_lock(self) -> None:
        lock = REPO_ROOT / "upstreams.lock.json"
        before = lock.read_bytes()
        for remote, expected_drift in ((self.meta["reviewed_commit"], False), ("f" * 40, True)):
            with self.subTest(remote=remote), patch(
                "upstream_absorption_report.remote_head", return_value=(remote, "HEAD", None)
            ):
                report = next(r for r in build_report(REPO_ROOT, check_remote=True) if r.name == NAME)
                self.assertEqual(report.reviewed_remote_drift, expected_drift)
                self.assertFalse(report.drift)
                self.assertFalse(report.dirty)
                self.assertEqual(report.absorbed_commit, self.meta["absorbed_commit"])
        self.assertEqual(lock.read_bytes(), before)

    def test_changed_instruction_is_candidate_not_automatic_adoption(self) -> None:
        self.assertEqual(categorize_changed_file(NAME, "skills/break/scenarios.md"), "candidate_absorb")
        self.assertEqual(categorize_changed_file(NAME, "README.md"), "provenance_only")

    def test_sync_accepts_jakub_and_changes_only_pin(self) -> None:
        with tempfile.TemporaryDirectory(prefix="jakub-sync-") as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "bin").mkdir()
            shutil.copy2(REPO_ROOT / "scripts/sync_upstreams.sh", root / "scripts")
            payload = json.loads((REPO_ROOT / "upstreams.lock.json").read_text())
            (root / "upstreams.lock.json").write_text(json.dumps(payload))
            fake_git = root / "bin/git"
            fake_git.write_text("#!/bin/sh\nexit 0\n")
            fake_git.chmod(0o755)
            env = dict(os.environ, PATH=str(root / "bin") + os.pathsep + os.environ["PATH"])
            target = "a" * 40
            result = subprocess.run(
                [os.environ.get("DESIGN_CRAFT_BASH", "bash"), str(root / "scripts/sync_upstreams.sh"),
                 "--name", NAME, "--commit", target],
                env=env, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload["upstreams"][NAME]["commit"] = target
            self.assertEqual(json.loads((root / "upstreams.lock.json").read_text()), payload)


if __name__ == "__main__":
    unittest.main()
