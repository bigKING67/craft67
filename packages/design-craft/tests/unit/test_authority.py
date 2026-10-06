from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.design_craft.repo import REPO_ROOT

import sys


LIB_DIR = REPO_ROOT / "skills/design-craft/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import design_craft.authority as authority_module
from design_craft.authority import asset_root_for, resolve_project_authority, workspace_owns


class AuthorityResolutionTests(unittest.TestCase):
    def test_nearest_nested_authority_wins_inside_git_project(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-authority-") as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            (root / "DESIGN.md").write_text("root", encoding="utf-8")
            target = root / "packages/app/src"
            target.mkdir(parents=True)
            nested = root / "packages/app/DESIGN.md"
            nested.write_text("nested", encoding="utf-8")

            resolution = resolve_project_authority(target, "DESIGN.md")

            self.assertEqual(resolution.path, nested.resolve())
            self.assertEqual(resolution.source, "nearest_project")

    def test_workspace_root_authority_only_applies_to_owned_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-workspace-") as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            (root / "DESIGN.md").write_text("root", encoding="utf-8")
            (root / "package.json").write_text(
                json.dumps({"workspaces": ["packages/*"]}), encoding="utf-8"
            )
            owned = root / "packages/app/src"
            unowned = root / "scratch/demo"
            owned.mkdir(parents=True)
            unowned.mkdir(parents=True)

            self.assertEqual(
                resolve_project_authority(owned, "DESIGN.md").path,
                (root / "DESIGN.md").resolve(),
            )
            rejected = resolve_project_authority(unowned, "DESIGN.md")
            self.assertIsNone(rejected.path)
            self.assertIn("does not own", rejected.reason)

    def test_pnpm_inline_comments_do_not_break_workspace_ownership(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-pnpm-") as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            (root / "PRODUCT.md").write_text("product", encoding="utf-8")
            (root / "pnpm-workspace.yaml").write_text(
                "packages:\n  - 'apps/*' # shipped apps\n", encoding="utf-8"
            )
            target = root / "apps/mobile/src"
            target.mkdir(parents=True)

            resolution = resolve_project_authority(target, "PRODUCT.md")

            self.assertEqual(resolution.path, (root / "PRODUCT.md").resolve())
            self.assertEqual(resolution.source, "workspace_root")

    def test_unrelated_parent_authority_is_not_inherited_without_project_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-unowned-") as raw:
            parent = Path(raw)
            (parent / "DESIGN.md").write_text("unrelated", encoding="utf-8")
            target = parent / "loose/files"
            target.mkdir(parents=True)

            resolution = resolve_project_authority(target, "DESIGN.md")

            self.assertIsNone(resolution.path)
            self.assertEqual(resolution.source, "none")

    def test_target_local_authority_needs_no_project_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-local-") as raw:
            target = Path(raw) / "prototype"
            target.mkdir()
            local = target / "DESIGN.md"
            local.write_text("local", encoding="utf-8")

            resolution = resolve_project_authority(target, "DESIGN.md")

            self.assertEqual(resolution.path, local.resolve())
            self.assertEqual(resolution.source, "target_local")

    def test_home_authority_is_not_implicitly_target_local(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-home-") as raw:
            fake_home = Path(raw)
            (fake_home / "DESIGN.md").write_text("home", encoding="utf-8")

            with patch.object(authority_module.Path, "home", return_value=fake_home):
                resolution = resolve_project_authority(fake_home, "DESIGN.md")

            self.assertIsNone(resolution.path)
            self.assertEqual(resolution.source, "none")

    def test_single_file_target_uses_sibling_authority_without_project_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-file-") as raw:
            root = Path(raw)
            target = root / "index.html"
            target.write_text("<main></main>", encoding="utf-8")
            product = root / "PRODUCT.md"
            product.write_text("Platform: adaptive", encoding="utf-8")

            resolution = resolve_project_authority(target, "PRODUCT.md")

            self.assertEqual(resolution.path, product.resolve())
            self.assertEqual(resolution.source, "target_local")

    def test_non_git_project_root_can_own_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-project-") as raw:
            root = Path(raw)
            (root / "package.json").write_text("{}", encoding="utf-8")
            authority = root / "DESIGN.md"
            authority.write_text("project", encoding="utf-8")
            target = root / "src/components"
            target.mkdir(parents=True)

            resolution = resolve_project_authority(target, "DESIGN.md")

            self.assertEqual(resolution.path, authority.resolve())
            self.assertEqual(resolution.source, "project_root")

    def test_explicit_authority_is_allowed_outside_project(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-explicit-") as raw:
            root = Path(raw)
            target = root / "project"
            target.mkdir()
            explicit = root / "shared.md"
            explicit.write_text("explicit", encoding="utf-8")

            resolution = resolve_project_authority(
                target, "DESIGN.md", explicit=explicit
            )

            self.assertEqual(resolution.path, explicit.resolve())
            self.assertEqual(resolution.source, "explicit")

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlinks unsupported")
    def test_implicit_authority_rejects_symlinks_at_every_discovery_level(self) -> None:
        for level in ("root", "nested", "target"):
            with self.subTest(level=level), tempfile.TemporaryDirectory(prefix="design-craft-authority-link-") as raw:
                parent = Path(raw)
                outside = parent / "outside.md"
                outside.write_text("outside", encoding="utf-8")
                root = parent / "repo"
                (root / ".git").mkdir(parents=True)
                target = root / "packages/app/src"
                target.mkdir(parents=True)
                location = {
                    "root": root,
                    "nested": root / "packages/app",
                    "target": target,
                }[level]
                (location / "DESIGN.md").symlink_to(outside)

                resolution = resolve_project_authority(target, "DESIGN.md")

                self.assertIsNone(resolution.path)
                self.assertEqual(resolution.source, "unsafe")

    def test_workspace_negation_applies_before_positive_ancestry_match(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-workspace-negation-") as raw:
            root = Path(raw)
            (root / "package.json").write_text(
                json.dumps({"workspaces": ["packages/*", "!packages/private/**"]}),
                encoding="utf-8",
            )
            private = root / "packages/private/src"
            public = root / "packages/public/src"
            private.mkdir(parents=True)
            public.mkdir(parents=True)

            self.assertFalse(workspace_owns(root, private))
            self.assertTrue(workspace_owns(root, public))

    def test_pnpm_flow_sequence_is_supported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-pnpm-flow-") as raw:
            root = Path(raw)
            (root / "pnpm-workspace.yaml").write_text(
                "packages: ['apps/*']\n", encoding="utf-8"
            )
            target = root / "apps/mobile/src"
            target.mkdir(parents=True)

            self.assertTrue(workspace_owns(root, target))

    def test_invalid_or_negative_only_workspace_configuration_fails_closed(self) -> None:
        fixtures = (
            ("package.json", "{invalid"),
            ("pnpm-workspace.yaml", "packages: not-a-sequence\n"),
            ("package.json", json.dumps({"workspaces": ["!private/**"]})),
        )
        for name, content in fixtures:
            with self.subTest(name=name, content=content), tempfile.TemporaryDirectory(prefix="design-craft-workspace-invalid-") as raw:
                root = Path(raw)
                (root / name).write_text(content, encoding="utf-8")
                target = root / "apps/mobile/src"
                target.mkdir(parents=True)

                self.assertFalse(workspace_owns(root, target))

    def test_invalid_nearest_project_boundary_blocks_outer_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-invalid-boundary-") as raw:
            outer = Path(raw)
            (outer / "package.json").write_text("{}", encoding="utf-8")
            (outer / "DESIGN.md").write_text("outer", encoding="utf-8")
            inner = outer / "broken"
            target = inner / "src"
            target.mkdir(parents=True)
            (inner / "package.json").write_text("{invalid", encoding="utf-8")

            resolution = resolve_project_authority(target, "DESIGN.md")

            self.assertIsNone(resolution.path)
            self.assertEqual(resolution.search_root, inner.resolve())
            self.assertIn("metadata is invalid", resolution.reason)

    def test_monorepo_asset_root_is_nearest_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-asset-root-") as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            (root / "package.json").write_text(
                json.dumps({"workspaces": ["apps/*"]}), encoding="utf-8"
            )
            package = root / "apps/web"
            package.mkdir(parents=True)
            (package / "package.json").write_text("{}", encoding="utf-8")
            page = package / "index.html"
            page.write_text("<main></main>", encoding="utf-8")

            self.assertEqual(asset_root_for(page), package.resolve())

    def test_monorepo_without_leaf_package_has_ambiguous_asset_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-asset-ambiguous-") as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            (root / "package.json").write_text(
                json.dumps({"workspaces": ["apps/*"]}), encoding="utf-8"
            )
            page = root / "apps/web/index.html"
            page.parent.mkdir(parents=True)
            page.write_text("<main></main>", encoding="utf-8")

            self.assertIsNone(asset_root_for(page))


if __name__ == "__main__":
    unittest.main()
