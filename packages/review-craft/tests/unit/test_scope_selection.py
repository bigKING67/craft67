from __future__ import annotations

# tests.support initializes the canonical runtime import path.
# ruff: noqa: I001

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.support import git_init, run_cli

from review_craft.configuration import default_config, validate_config
from review_craft.repository import inventory


class ScopeSelectionTests(unittest.TestCase):
    def _fixture(self, *, git: bool = False) -> Path:
        temporary = tempfile.TemporaryDirectory(prefix="review-craft-scope-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "src").mkdir()
        (root / "src/main.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "README.md").write_text("Scope fixture\n", encoding="utf-8")
        if git:
            git_init(root)
        return root

    def test_equivalent_scope_spellings_preserve_inventory(self) -> None:
        for git in (False, True):
            root = self._fixture(git=git)
            for canonical, aliases in (
                (".", (".", "./", "././", "./././", "././.")),
                ("src", ("src", "src/", "./src", "././src", "././src/")),
                ("src/main.py", ("src/main.py", "././src/main.py")),
            ):
                expected = inventory(root, scopes=[canonical])
                self.assertTrue(expected[0])
                for alias in aliases:
                    with self.subTest(git=git, scope=alias):
                        config = default_config()
                        config["scope"] = [alias]
                        validate_config(config)
                        self.assertEqual(inventory(root, scopes=config["scope"]), expected)

    def test_root_selector_widens_narrower_selection_in_either_order(self) -> None:
        root = self._fixture(git=True)
        expected = inventory(root)
        for alias in (".", "./", "./././"):
            for scopes in (["src", alias], [alias, "src"]):
                with self.subTest(scopes=scopes):
                    self.assertEqual(inventory(root, scopes=scopes), expected)

    @unittest.skipIf(os.name == "nt", "POSIX whitespace and backslash filename identity")
    def test_normalization_preserves_literal_filename_characters(self) -> None:
        root = self._fixture(git=True)
        for directory in (" src ", "back\\slash", "back/slash"):
            (root / directory).mkdir(parents=True)
            (root / directory / "main.py").write_text("VALUE = 2\n", encoding="utf-8")
        for directory in (" src ", "back\\slash"):
            with self.subTest(directory=directory):
                records, _ = inventory(root, scopes=[f"././{directory}"])
                self.assertEqual([row["path"] for row in records], [f"{directory}/main.py"])

    def test_frozen_protocol_inventory_retains_original_scope_semantics(self) -> None:
        root = self._fixture(git=True)
        for scope in ("././src", "./././"):
            with self.subTest(scope=scope):
                records, excluded = inventory(root, scopes=[scope], _legacy_identity=True)
                self.assertEqual(records, [])
                self.assertEqual(len(excluded), 2)
        records, _ = inventory(root, scopes=["./src"], _legacy_identity=True)
        self.assertEqual([row["path"] for row in records], ["src/main.py"])
        self.assertNotIn("sourceIdentity", records[0])

    def test_preflight_binds_repeated_prefix_scope_to_selected_source(self) -> None:
        root = self._fixture(git=True)
        with tempfile.TemporaryDirectory(prefix="review-craft-scope-output-") as directory:
            output = Path(directory)
            config = default_config()
            config["scope"] = ["././src"]
            config_path = output / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = run_cli(
                "preflight",
                "--target",
                str(root),
                "--config",
                str(config_path),
                "--output-root",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = Path(json.loads(result.stdout)["runDir"])
            coverage = json.loads((run_dir / "coverage.json").read_text(encoding="utf-8"))
            self.assertEqual([row["path"] for row in coverage["files"]], ["src/main.py"])
            result = run_cli("validate", "--run-dir", str(run_dir), "--allow-draft")
            self.assertEqual(result.returncode, 0, result.stderr)
