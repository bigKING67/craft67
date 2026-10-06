"""Offline tests for scripts/upstream_drift.py (no network)."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("upstream_drift", ROOT / "scripts/upstream_drift.py")
assert SPEC and SPEC.loader
drift = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drift)

PIN, HEAD = "a" * 40, "b" * 40


def fake_fetch(tree: dict[str, dict[str, object]], *, pin_exists: bool = True):
    """tree maps ref -> {path: file-sha | list-of-children}; absent paths are 404."""

    def fetch(endpoint: str):
        if endpoint == f"repos/o/r/commits/{PIN}":
            if not pin_exists:
                raise drift.NotFound(endpoint)
            return {"sha": PIN}
        if endpoint == "repos/o/r":
            return {"default_branch": "main"}
        if endpoint == "repos/o/r/commits/main":
            return {"sha": HEAD}
        path, ref = endpoint.removeprefix("repos/o/r/contents/").split("?ref=")
        node = tree[ref].get(path)
        if node is None:
            raise drift.NotFound(endpoint)
        if isinstance(node, list):
            return [{"name": name, "sha": sha} for name, sha in node]
        return {"sha": node}

    return fetch


class WatchListTests(unittest.TestCase):
    def test_repository_watch_list_is_valid(self) -> None:
        self.assertEqual([], drift.validate_watch(drift.load_watch()))

    def test_validation_catches_broken_mappings_and_pins(self) -> None:
        data = copy.deepcopy(drift.load_watch())
        first = data["upstreams"][0]
        first["pinned_sha"] = "main"
        first["watch"][0]["maps_to"] = ["integrations/local-production/renamed.mjs"]
        data["upstreams"].append(copy.deepcopy(data["upstreams"][1]))
        errors = drift.validate_watch(data)
        self.assertTrue(any("full 40-hex" in e for e in errors), errors)
        self.assertTrue(any("missing integrations/local-production/renamed.mjs" in e for e in errors), errors)
        self.assertTrue(any("duplicate id" in e for e in errors), errors)


class DriftTests(unittest.TestCase):
    def upstream(self, paths: list[str], npm: dict | None = None) -> dict:
        entry = {
            "id": "x",
            "repo": "o/r",
            "pinned_sha": PIN,
            "status": "implemented",
            "watch": [{"path": p, "why": "w", "maps_to": ["docs"]} for p in paths],
        }
        if npm:
            entry["npm"] = npm
        return entry

    def test_file_and_directory_states(self) -> None:
        tree = {
            PIN: {"same.md": "1", "edit.md": "1", "gone.md": "1", "dir": [("a", "1")]},
            HEAD: {"same.md": "1", "edit.md": "2", "new.md": "9", "dir": [("a", "1"), ("b", "2")]},
        }
        report = drift.check_upstream(
            self.upstream(["same.md", "edit.md", "gone.md", "new.md", "dir", "never.md"]),
            fetch=fake_fetch(tree),
        )
        states = {p["path"]: p["state"] for p in report["paths"]}
        self.assertEqual(
            {"same.md": "unchanged", "edit.md": "changed", "gone.md": "removed",
             "new.md": "added", "dir": "changed", "never.md": "missing"},
            states,
        )
        self.assertTrue(drift.needs_review(report))
        self.assertEqual(HEAD, report["head_sha"])
        # A path present in neither version is a broken watch entry, not drift.
        self.assertIn("never.md exists at neither pin nor head", report["error"])

    def test_unresolvable_pin_is_an_error_not_added_paths(self) -> None:
        report = drift.check_upstream(
            self.upstream(["a.md"]),
            fetch=fake_fetch({PIN: {}, HEAD: {"a.md": "1"}}, pin_exists=False),
        )
        self.assertIn("not resolvable upstream", report["error"])
        self.assertNotIn("paths", report)

    def test_npm_timeout_and_github_errors_are_both_reported(self) -> None:
        def broken(endpoint: str):
            raise RuntimeError("gh api failed: rate limited")

        def slow(_: str) -> str:
            raise TimeoutError("read timed out")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps({"dependencies": {"pkg": "1"}}))
            report = drift.check_upstream(
                self.upstream(["a.md"], {"package": "pkg", "pinned_in": "package.json"}),
                fetch=broken,
                latest=slow,
                root=root,
            )
        self.assertIn("rate limited", report["error"])
        self.assertIn("read timed out", report["error"])

    def test_missing_gh_binary_is_a_clear_error(self) -> None:
        with (
            mock.patch.dict(os.environ, {"PATH": ""}),
            self.assertRaisesRegex(RuntimeError, "gh CLI not found"),
        ):
            drift.gh_api("repos/o/r")

    def test_unchanged_paths_and_current_npm_need_no_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps({"dependencies": {"pkg": "1.2.3"}}))
            report = drift.check_upstream(
                self.upstream(["same.md"], {"package": "pkg", "pinned_in": "package.json"}),
                fetch=fake_fetch({PIN: {"same.md": "1"}, HEAD: {"same.md": "1"}}),
                latest=lambda _: "1.2.3",
                root=root,
            )
            self.assertFalse(drift.needs_review(report))
            report = drift.check_upstream(
                self.upstream(["same.md"], {"package": "pkg", "pinned_in": "package.json"}),
                fetch=fake_fetch({PIN: {"same.md": "1"}, HEAD: {"same.md": "1"}}),
                latest=lambda _: "1.3.0",
                root=root,
            )
            self.assertTrue(drift.needs_review(report))

    def test_upstream_errors_are_reported_not_raised(self) -> None:
        def broken(endpoint: str):
            raise RuntimeError("gh api failed: rate limited")

        report = drift.check_upstream(self.upstream(["a.md"]), fetch=broken)
        self.assertIn("rate limited", report["error"])


if __name__ == "__main__":
    unittest.main()
