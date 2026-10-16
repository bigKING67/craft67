from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PureWindowsPath
from unittest import mock


PACKAGE = Path(__file__).resolve().parents[1]
SCRIPTS = PACKAGE / "scripts"
sys.path.insert(0, str(SCRIPTS))
import packaging  # noqa: E402
import install as installer  # noqa: E402


def fixture_package(root: Path) -> Path:
    package = root / "source"
    runtime = package / "skills" / "team-workflow-craft"
    (runtime / "scripts").mkdir(parents=True)
    (runtime / "SKILL.md").write_text(
        "---\nname: team-workflow-craft\ndescription: test fixture\n---\n# Fixture\n", encoding="utf-8"
    )
    (runtime / "scripts" / "twc.py").write_text(
        "import argparse\nparser = argparse.ArgumentParser()\nparser.parse_args()\n", encoding="utf-8"
    )
    (package / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (package / "LICENSE").write_text("fixture license\n", encoding="utf-8")
    return package


def run_install(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "install.py"), *arguments], text=True, capture_output=True, check=False
    )


class PackagingTests(unittest.TestCase):
    def build_fixture(self, directory: Path) -> tuple[Path, Path, dict]:
        package = fixture_package(directory)
        return packaging.create_artifact(package, directory / "out")

    def test_build_is_reproducible_and_runtime_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = fixture_package(root)
            one, one_manifest, _ = packaging.create_artifact(source, root / "one")
            two, two_manifest, _ = packaging.create_artifact(source, root / "two")
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertEqual(one_manifest.read_bytes(), two_manifest.read_bytes())
            with zipfile.ZipFile(one) as archive:
                self.assertEqual(
                    sorted(archive.namelist()),
                    [
                        "team-workflow-craft/LICENSE",
                        "team-workflow-craft/SKILL.md",
                        "team-workflow-craft/VERSION",
                        "team-workflow-craft/scripts/twc.py",
                    ],
                )

    def test_dry_run_then_apply_and_same_version_idempotency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, manifest, _ = self.build_fixture(root)
            project = root / "project"
            project.mkdir()
            command = ("--artifact", str(artifact), "--manifest", str(manifest), "--project", str(project), "--host", "codex")
            preview = run_install(*command)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            target = project / ".agents" / "skills" / "team-workflow-craft"
            self.assertFalse(target.exists())
            applied = run_install(*command, "--apply")
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(json.loads(applied.stdout)["status"], "install")
            repeat = run_install(*command, "--apply")
            self.assertEqual(repeat.returncode, 0, repeat.stderr)
            self.assertEqual(json.loads(repeat.stdout)["status"], "already_installed")
            self.assertTrue((target / ".twc-install.json").is_file())

    def test_bad_artifact_hash_is_rejected_before_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, manifest, _ = self.build_fixture(root)
            artifact.write_bytes(artifact.read_bytes() + b"changed")
            result = run_install("--artifact", str(artifact), "--manifest", str(manifest), "--target", str(root / "target"), "--apply")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SHA-256", result.stderr)
            self.assertFalse((root / "target").exists())

    def test_zip_path_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "team-workflow-craft-0.1.0.zip"
            with zipfile.ZipFile(artifact, "w") as archive:
                archive.writestr("team-workflow-craft/../outside", b"no")
            contents = artifact.read_bytes()
            manifest = {
                "schema": packaging.ARCHIVE_SCHEMA,
                "artifact": artifact.name,
                "artifact_sha256": hashlib.sha256(contents).hexdigest(),
                "archive_prefix": packaging.SKILL_NAME,
                "version": "0.1.0",
                "files": [{"path": "../outside", "sha256": hashlib.sha256(b"no").hexdigest(), "size": 2}],
            }
            manifest_path = artifact.with_suffix(".zip.manifest.json")
            manifest_path.write_bytes(packaging.canonical_json(manifest))
            result = run_install("--artifact", str(artifact), "--manifest", str(manifest_path), "--target", str(root / "target"), "--apply")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe artifact path", result.stderr)
            self.assertFalse((root / "outside").exists())

    def test_portable_artifact_paths_reject_windows_and_normalization_escapes(self) -> None:
        for unsafe in ("../outside", "folder/../outside", "folder/./file", "folder//file", r"folder\\file", "C:relative", "C:/absolute"):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(packaging.PackagingError):
                    packaging._safe_relative(unsafe)

    def test_source_marker_and_invalid_semver_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = fixture_package(root)
            runtime = source / "skills" / "team-workflow-craft"
            (runtime / ".twc-install.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(packaging.PackagingError):
                packaging.create_artifact(source, root / "out")
            (runtime / ".twc-install.json").unlink()
            (source / "VERSION").write_text("0.1.0/unsafe\n", encoding="utf-8")
            with self.assertRaises(packaging.PackagingError):
                packaging.create_artifact(source, root / "out")

    def test_unknown_existing_target_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, manifest, _ = self.build_fixture(root)
            target = root / "target"
            target.mkdir()
            sentinel = target / "user-file.txt"
            sentinel.write_text("keep", encoding="utf-8")
            result = run_install("--artifact", str(artifact), "--manifest", str(manifest), "--target", str(target), "--apply")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_known_unchanged_installation_requires_explicit_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = fixture_package(root)
            old_artifact, old_manifest, _ = packaging.create_artifact(source, root / "old")
            target = root / "target"
            installed = run_install("--artifact", str(old_artifact), "--manifest", str(old_manifest), "--target", str(target), "--apply")
            self.assertEqual(installed.returncode, 0, installed.stderr)
            (source / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            new_artifact, new_manifest, _ = packaging.create_artifact(source, root / "new")
            rejected = run_install("--artifact", str(new_artifact), "--manifest", str(new_manifest), "--target", str(target), "--apply")
            self.assertNotEqual(rejected.returncode, 0)
            upgraded = run_install(
                "--artifact", str(new_artifact), "--manifest", str(new_manifest), "--target", str(target), "--allow-upgrade", "--apply"
            )
            self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
            self.assertEqual(json.loads(upgraded.stdout)["status"], "upgrade")
            self.assertEqual((target / "VERSION").read_text(encoding="utf-8"), "0.2.0\n")

    def test_target_parent_symlink_and_dotdot_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, manifest, _ = self.build_fixture(root)
            outside = root / "outside"
            outside.mkdir()
            link = root / "link"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")
            linked_target = link / "skills" / "team-workflow-craft"
            linked = run_install("--artifact", str(artifact), "--manifest", str(manifest), "--target", str(linked_target), "--apply")
            self.assertNotEqual(linked.returncode, 0)
            self.assertIn("non-platform symlink", linked.stderr)
            dotdot_target = root / "ordinary" / ".." / "target"
            escaped = run_install("--artifact", str(artifact), "--manifest", str(manifest), "--target", str(dotdot_target), "--apply")
            self.assertNotEqual(escaped.returncode, 0)
            self.assertIn("must not contain", escaped.stderr)
            self.assertFalse((outside / "skills").exists())

    def test_global_skill_destinations_are_rejected_after_canonicalization(self) -> None:
        for parent in (".agents/skills", ".codex/skills", ".claude/skills", ".pi/agent/skills"):
            target = Path.home() / parent / "team-workflow-craft"
            arguments = argparse.Namespace(target=target, project=None, host=None)
            with self.subTest(target=target):
                with self.assertRaises(packaging.PackagingError):
                    installer.resolve_target(arguments)

    def test_unrelated_global_symlink_does_not_block_project_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_home = root / "home"
            fake_home.mkdir()
            external = root / "external-codex"
            external.mkdir()
            try:
                (fake_home / ".codex").symlink_to(external, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")
            project = root / "project"
            project.mkdir()
            arguments = argparse.Namespace(target=None, project=project, host="codex")
            with mock.patch.object(installer.Path, "home", return_value=fake_home):
                target = installer.resolve_target(arguments)
            self.assertEqual(target, (project / ".agents" / "skills" / "team-workflow-craft").resolve())

    def test_windows_paths_are_not_rejected_by_posix_only_guard(self) -> None:
        installer._validate_explicit_path_syntax(
            PureWindowsPath(r"C:\work\project\skill"), "--target", is_windows=True
        )

    def test_installed_runtime_works_after_source_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, manifest, _ = self.build_fixture(root)
            target = root / "target"
            result = run_install("--artifact", str(artifact), "--manifest", str(manifest), "--target", str(target), "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
            shutil.rmtree(root / "source")
            runtime = subprocess.run(
                [sys.executable, str(target / "scripts" / "twc.py"), "--help"], text=True, capture_output=True, check=False
            )
            self.assertEqual(runtime.returncode, 0, runtime.stderr)


if __name__ == "__main__":
    unittest.main()
