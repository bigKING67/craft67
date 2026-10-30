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
    runtime = package / "skills" / "workflow-craft"
    (runtime / "scripts").mkdir(parents=True)
    (runtime / "SKILL.md").write_text(
        "---\nname: workflow-craft\ndescription: test fixture\n---\n# Fixture\n", encoding="utf-8"
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
    def legacy_fixture(self, root):
        source = fixture_package(root)
        files = packaging.runtime_files(source)
        files['SKILL.md'] = files['SKILL.md'].replace(b'workflow-craft', b'team-workflow-craft')
        project = root / 'project'
        legacy = project / '.agents/skills/team-workflow-craft'
        legacy.mkdir(parents=True)
        for name, content in files.items():
            path = legacy / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        marker = dict(schema='team-workflow-craft.install.v1', skill='team-workflow-craft', version='0.1.0',
                      files=[dict(path=name, sha256=hashlib.sha256(content).hexdigest(), size=len(content))
                             for name, content in files.items()])
        (legacy / packaging.INSTALL_MARKER).write_bytes(packaging.canonical_json(marker))
        (source / 'VERSION').write_text('0.1.1\n')
        artifact, _, _ = packaging.create_artifact(source, root / 'out')
        return project, legacy, artifact

    def test_legacy_name_migration_is_explicit_and_preserves_project_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project, legacy, artifact = self.legacy_fixture(root)
            target = legacy.with_name('workflow-craft')
            history = project / '.team-workflow/tasks/local-existing/task.json'
            history.parent.mkdir(parents=True)
            history.write_bytes(b'original history')
            before = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob('*') if p.is_file()}
            command = ('--artifact', str(artifact), '--project', str(project), '--host', 'codex')
            rejected = run_install(*command, '--apply')
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('--allow-upgrade', rejected.stderr)
            preview = run_install(*command, '--allow-upgrade')
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(json.loads(preview.stdout)['action'], 'migrate')
            self.assertEqual({p.relative_to(legacy): p.read_bytes() for p in legacy.rglob('*') if p.is_file()}, before)
            self.assertFalse(target.exists())
            applied = run_install(*command, '--allow-upgrade', '--apply')
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(json.loads(applied.stdout)['status'], 'migrate')
            self.assertFalse(legacy.exists())
            self.assertIn('name: workflow-craft', (target / 'SKILL.md').read_text())
            self.assertEqual(history.read_bytes(), b'original history')
            self.assertEqual(json.loads(run_install(*command, '--apply').stdout)['status'], 'already_installed')

    def test_legacy_migration_refuses_drift_unknown_links_and_duplicate_names(self):
        for scenario in ('drift', 'unknown', 'symlink', 'duplicate'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                project, legacy, artifact = self.legacy_fixture(Path(temporary))
                target = legacy.with_name('workflow-craft')
                if scenario == 'drift':
                    (legacy / 'SKILL.md').write_text('local edit')
                elif scenario == 'unknown':
                    (legacy / packaging.INSTALL_MARKER).write_text('{}')
                elif scenario == 'symlink':
                    actual = legacy.with_name('saved')
                    legacy.rename(actual)
                    legacy.symlink_to(actual, target_is_directory=True)
                else:
                    target.mkdir()
                result = run_install('--artifact', str(artifact), '--project', str(project), '--host', 'codex',
                                     '--allow-upgrade', '--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(legacy.exists())
                self.assertEqual(target.exists(), scenario == 'duplicate')

    def test_legacy_migration_rolls_back_if_new_target_cannot_be_written(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, legacy, artifact = self.legacy_fixture(Path(temporary))
            target = legacy.with_name('workflow-craft')
            manifest, files, sha = packaging.read_artifact(artifact, artifact.with_suffix('.zip.manifest.json'))
            old_marker = (legacy / packaging.INSTALL_MARKER).read_bytes()
            replace = installer.os.replace

            def fail_new_target(src, dest):
                if Path(dest) == target:
                    raise OSError('simulated destination failure')
                return replace(src, dest)

            with mock.patch.object(installer.os, 'replace', side_effect=fail_new_target):
                with self.assertRaises(OSError):
                    installer.apply_install(target, files, packaging.install_marker(manifest, sha),
                                            'migrate', old_marker, legacy)
            self.assertEqual((legacy / packaging.INSTALL_MARKER).read_bytes(), old_marker)
            self.assertFalse(target.exists())
            self.assertEqual(list(legacy.parent.glob('.*twc-*')), [])

    def test_legacy_migration_rechecks_files_before_replacing(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, legacy, artifact = self.legacy_fixture(Path(temporary))
            target = legacy.with_name('workflow-craft')
            manifest, files, sha = packaging.read_artifact(artifact, artifact.with_suffix('.zip.manifest.json'))
            old_marker = (legacy / packaging.INSTALL_MARKER).read_bytes()
            (legacy / 'SKILL.md').write_text('concurrent edit')
            with self.assertRaisesRegex(packaging.PackagingError, 'content changed'):
                installer.apply_install(target, files, packaging.install_marker(manifest, sha),
                                        'migrate', old_marker, legacy)
            self.assertEqual((legacy / 'SKILL.md').read_text(), 'concurrent edit')
            self.assertFalse(target.exists())

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
                        "workflow-craft/LICENSE",
                        "workflow-craft/SKILL.md",
                        "workflow-craft/VERSION",
                        "workflow-craft/scripts/twc.py",
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
            target = project / ".agents" / "skills" / "workflow-craft"
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
            artifact = root / "workflow-craft-0.1.0.zip"
            with zipfile.ZipFile(artifact, "w") as archive:
                archive.writestr("workflow-craft/../outside", b"no")
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
            runtime = source / "skills" / "workflow-craft"
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
            linked_target = link / "skills" / "workflow-craft"
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
            target = Path.home() / parent / "workflow-craft"
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
            self.assertEqual(target, (project / ".agents" / "skills" / "workflow-craft").resolve())

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
