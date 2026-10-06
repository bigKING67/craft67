from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.design_craft.repo import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from upstream_absorption_report import github_compare, local_compare, build_report, render_markdown_summary


class CompareCompletenessTests(unittest.TestCase):
    def compare(self, files=1, commits=1, total=1):
        payload = {"status": "ahead", "ahead_by": total, "total_commits": total,
                   "commits": [{"sha": "a" * 40, "commit": {"message": "change"}}] * commits,
                   "files": [{"filename": "README.md", "status": "modified"}] * files}
        with patch("upstream_absorption_report.urlopen") as opener:
            opener.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            return github_compare("https://github.com/example/repo", "a" * 40, "b" * 40, "fixture")

    def test_api_limits_are_explicit(self):
        self.assertIsNone(self.compare(files=299)[-1])
        self.assertIn("300-entry", self.compare(files=300)[-1])
        self.assertIn("commit list", self.compare(commits=101, total=101)[-1])
        self.assertIn("commit list", self.compare(commits=2, total=3)[-1])

    def test_local_range_preserves_all_paths_without_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(["git", "-C", directory, *args], text=True).strip()
            git("init", "-q")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.invalid")
            git("commit", "--allow-empty", "-qm", "base")
            base = git("rev-parse", "HEAD")
            names = [f"file-{i}.md" for i in range(301)] + ["中文.md"]
            if sys.platform != "win32":
                names += ["tab\tname.md", "line\nname.md", "carriage\rname.md"]
            for name in names:
                (root / name).write_text("fixture")
            git("add", "--", *names)
            git("commit", "-qm", "head")
            head = git("rev-parse", "HEAD")
            commits, files = local_compare(root, base, head, "fixture")
            self.assertEqual({f.path for f in files}, set(names))
            self.assertEqual([c.sha for c in commits], [head])
            self.assertEqual(git("rev-parse", "HEAD"), head)
            self.assertEqual(git("status", "--short"), "")
            with self.assertRaises(subprocess.CalledProcessError):
                local_compare(root, head, base, "fixture")

    def test_missing_local_objects_cannot_recommend_provenance_only(self):
        result = self.compare(files=300)
        with patch("upstream_absorption_report.remote_head", return_value=("f" * 40, "HEAD", None)), \
             patch("upstream_absorption_report.github_compare", return_value=result), \
             patch("upstream_absorption_report.local_compare", side_effect=ValueError("missing")):
            reports = build_report(REPO_ROOT, check_remote=True, fetch_remote_details=True)
        for report in reports:
            self.assertEqual(report.remote_recommendation, "manual_review")
            self.assertIn("Incomplete", report.remote_detail_error)
        self.assertIn("Incomplete", render_markdown_summary(reports))

    def test_local_recovery_includes_gitlinks_ignored_by_local_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / "upstream"
            upstream.mkdir()

            def git(*args):
                return subprocess.check_output(
                    ["git", "-C", str(upstream), *args], text=True
                ).strip()

            git("init", "-q")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.invalid")
            git("commit", "--allow-empty", "-qm", "dependency one")
            first = git("rev-parse", "HEAD")
            git("commit", "--allow-empty", "-qm", "dependency two")
            second = git("rev-parse", "HEAD")
            (upstream / "README.md").write_text("old\n", encoding="utf-8")
            git("add", "--", "README.md")
            git("update-index", "--add", "--cacheinfo", f"160000,{first},skills/vendor")
            git("commit", "-qm", "base")
            base = git("rev-parse", "HEAD")
            (upstream / "README.md").write_text("new\n", encoding="utf-8")
            git("add", "--", "README.md")
            git("update-index", "--cacheinfo", f"160000,{second},skills/vendor")
            git("commit", "-qm", "update dependency and readme")
            head = git("rev-parse", "HEAD")
            git("config", "diff.ignoreSubmodules", "all")
            before_status = git("status", "--short")

            lock = json.loads((REPO_ROOT / "upstreams.lock.json").read_text())
            name = next(iter(lock["upstreams"]))
            meta = lock["upstreams"][name]
            meta.update(
                path="upstream", commit=head, reviewed_commit=base,
                reviewed_through_commit=base, latest_range_head_commit=base,
            )
            lock["upstreams"] = {name: meta}
            (root / "upstreams.lock.json").write_text(json.dumps(lock), encoding="utf-8")
            with (
                patch("upstream_absorption_report.remote_head", return_value=(head, "HEAD", None)),
                patch("upstream_absorption_report.github_compare", return_value=self.compare(files=300)),
            ):
                report, = build_report(root, check_remote=True, fetch_remote_details=True)

            self.assertEqual(report.remote_detail_source, "local_git")
            self.assertIsNone(report.remote_detail_error)
            self.assertEqual(
                {item.path for item in report.remote_changed_files},
                {"README.md", "skills/vendor"},
            )
            self.assertEqual(report.remote_recommendation, "absorption_review")
            self.assertEqual([item.sha for item in report.remote_commits], [head])
            self.assertEqual(git("config", "--get", "diff.ignoreSubmodules"), "all")
            self.assertEqual(git("rev-parse", "HEAD"), head)
            self.assertEqual(git("status", "--short"), before_status)

    def test_complete_local_recovery_clears_partial_evidence(self):
        result = self.compare(files=300)
        with patch("upstream_absorption_report.remote_head", return_value=("f" * 40, "HEAD", None)), \
             patch("upstream_absorption_report.github_compare", return_value=result), \
             patch("upstream_absorption_report.local_compare", return_value=([], [])):
            reports = build_report(REPO_ROOT, check_remote=True, fetch_remote_details=True)
        for report in reports:
            self.assertEqual(report.remote_detail_source, "local_git")
            self.assertIsNone(report.remote_detail_error)
            self.assertEqual(report.remote_changed_files, [])


if __name__ == "__main__":
    unittest.main()
