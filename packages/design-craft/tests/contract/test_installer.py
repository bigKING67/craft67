from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT


class InstallerContractTests(unittest.TestCase):
    def _bash_executable(self, environment: dict[str, str]) -> str:
        configured = environment.get("DESIGN_CRAFT_BASH", "").strip()
        executable = shutil.which(configured or "bash")
        if executable is None:
            self.fail(
                "Git Bash is required; set DESIGN_CRAFT_BASH to Git for Windows bash.exe"
            )
        normalized = executable.replace("\\", "/").lower()
        if os.name == "nt" and normalized.endswith("/windows/system32/bash.exe"):
            self.fail("DESIGN_CRAFT_BASH resolved to WSL bash instead of Git Bash")
        return executable

    def _bash_paths(self, bash: str, *paths: Path) -> tuple[str, ...]:
        if os.name != "nt":
            return tuple(str(path) for path in paths)
        result = subprocess.run(
            [
                bash,
                "--noprofile",
                "--norc",
                "-c",
                'for value in "$@"; do cygpath -u "$value"; done',
                "design-craft-paths",
                *(str(path) for path in paths),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        converted = tuple(line for line in result.stdout.splitlines() if line)
        if result.returncode != 0 or len(converted) != len(paths):
            self.fail(
                "Git Bash path conversion failed\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        return converted

    @staticmethod
    def _result_details(result: subprocess.CompletedProcess[str]) -> str:
        command = result.args if isinstance(result.args, list) else [str(result.args)]
        return (
            f"command: {shlex.join(str(part) for part in command)}\n"
            f"returncode: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    def _run_installer(
        self,
        install_root: Path,
        backup_root: Path,
        *args: str,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        bash = self._bash_executable(environment)
        script, bash_install_root, bash_backup_root = self._bash_paths(
            bash,
            REPO_ROOT / "scripts/install_local.sh",
            install_root,
            backup_root,
        )
        environment.update(
            {
                "DESIGN_CRAFT_SKILL_ROOT": bash_install_root,
                "DESIGN_CRAFT_BACKUP_ROOT": bash_backup_root,
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        if extra_env:
            environment.update(extra_env)
        return subprocess.run(
            [bash, script, *args],
            cwd=REPO_ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def _snapshot(self, root: Path) -> list[tuple[str, str, bytes]]:
        if not root.exists():
            return []
        snapshot: list[tuple[str, str, bytes]] = []
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                snapshot.append((relative, "symlink", os.readlink(path).encode()))
            elif path.is_dir():
                snapshot.append((relative, "directory", b""))
            else:
                snapshot.append((relative, "file", path.read_bytes()))
        return snapshot

    def test_install_writes_verified_canonical_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            install_root = root / "skills"
            backup_root = root / "backups"

            result = self._run_installer(install_root, backup_root)

            self.assertEqual(result.returncode, 0, self._result_details(result))
            installed = install_root / "design-craft"
            self.assertTrue((installed / "SKILL.md").is_file())
            metadata = json.loads(
                (installed / ".design-craft-install.json").read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["schema"], "design-craft.install.v2")
            self.assertEqual(metadata["skill_name"], "design-craft")
            self.assertEqual(metadata["version"], (REPO_ROOT / "VERSION").read_text().strip())
            self.assertTrue(metadata["source_tree_sha256"])

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            before = self._snapshot(root)

            result = self._run_installer(root / "skills", root / "backups", "--dry-run")

            self.assertEqual(result.returncode, 0, self._result_details(result))
            self.assertIn(
                "dry_run: no files changed",
                result.stdout,
                self._result_details(result),
            )
            self.assertEqual(self._snapshot(root), before)

    def test_backup_failpoint_restores_previous_target(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            install_root = root / "skills"
            target = install_root / "design-craft"
            target.mkdir(parents=True)
            (target / "user-file.txt").write_text("preserve\n", encoding="utf-8")

            result = self._run_installer(
                install_root,
                root / "backups",
                extra_env={"DESIGN_CRAFT_INSTALL_TEST_FAIL_AFTER_BACKUP": "1"},
            )

            self.assertEqual(result.returncode, 97, self._result_details(result))
            self.assertEqual((target / "user-file.txt").read_text(), "preserve\n")
            self.assertFalse((target / "SKILL.md").exists())

    def test_post_switch_failpoint_restores_previous_target(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            install_root = root / "skills"
            target = install_root / "design-craft"
            target.mkdir(parents=True)
            (target / "user-file.txt").write_text("preserve\n", encoding="utf-8")

            result = self._run_installer(
                install_root,
                root / "backups",
                extra_env={"DESIGN_CRAFT_INSTALL_TEST_FAIL_AFTER_SWITCH": "1"},
            )

            self.assertNotEqual(result.returncode, 0, self._result_details(result))
            self.assertEqual((target / "user-file.txt").read_text(), "preserve\n")
            self.assertFalse((target / "SKILL.md").exists())

    def test_live_and_stale_install_locks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            install_root = root / "skills"
            backup_root = root / "backups"
            lock = install_root / ".design-craft-install.lock"
            lock.mkdir(parents=True)
            bash = self._bash_executable(os.environ.copy())
            owner = subprocess.Popen(
                [bash, "--noprofile", "--norc", "-c", 'printf "%s\\n" "$$"; exec sleep 60'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertIsNotNone(owner.stdout)
                owner_pid = owner.stdout.readline().strip()
                self.assertRegex(owner_pid, r"^[0-9]+$")
                (lock / "pid").write_text(f"{owner_pid}\n", encoding="utf-8")

                blocked = self._run_installer(
                    install_root, backup_root, "--lock-timeout", "0"
                )
            finally:
                owner.terminate()
                owner.wait(timeout=10)
                if owner.stdout is not None:
                    owner.stdout.close()
                if owner.stderr is not None:
                    owner.stderr.close()
            self.assertNotEqual(
                blocked.returncode,
                0,
                self._result_details(blocked),
            )
            self.assertIn(
                "Timed out waiting for install lock",
                blocked.stderr,
                self._result_details(blocked),
            )
            self.assertFalse((install_root / "design-craft").exists())

            shutil.rmtree(lock)
            lock.mkdir()
            (lock / "pid").write_text("999999999\n", encoding="utf-8")
            recovered = self._run_installer(install_root, backup_root)
            self.assertEqual(
                recovered.returncode,
                0,
                self._result_details(recovered),
            )
            self.assertTrue((install_root / "design-craft/SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
