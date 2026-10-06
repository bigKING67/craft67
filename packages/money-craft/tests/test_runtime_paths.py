from __future__ import annotations

import sys
import os
import json
import subprocess
from unittest import mock
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import runtime_paths  # noqa: E402
import money_craft as mc  # noqa: E402


class RuntimePathTests(unittest.TestCase):
    def test_env_file_replacement_between_inspection_and_open_is_rejected(self):
        for symlink in (False, True):
            with self.subTest(symlink=symlink), tempfile.TemporaryDirectory() as directory:
                path, other = Path(directory)/"config.env", Path(directory)/"other.env"
                path.write_text("MONEY_CRAFT_DATA_HOME=/tmp/first-fixture\n")
                other.write_text("MONEY_CRAFT_DATA_HOME=/tmp/second-fixture\n")
                path.chmod(0o600); other.chmod(0o600)
                env = {runtime_paths.ENV_FILE_ENV: str(path)}
                before = dict(env)
                original_open = os.open
                def swap(target, flags, *args, **kwargs):
                    if symlink:
                        path.unlink(); path.symlink_to(other)
                    else:
                        os.replace(other, path)
                    return original_open(target, flags, *args, **kwargs)
                with mock.patch.object(runtime_paths.os, "open", side_effect=swap):
                    with self.assertRaises(runtime_paths.RuntimePathError):
                        runtime_paths.load_explicit_env_file(env)
                self.assertEqual(env, before)

    def test_invalid_encoding_and_oversize_env_leave_no_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"config.env"
            for raw in (b"", b"\xff", b"a"*(runtime_paths.MAX_ENV_FILE_BYTES+1)):
                path.write_bytes(raw); path.chmod(0o600)
                env = {runtime_paths.ENV_FILE_ENV: str(path)}
                before = dict(env)
                with self.assertRaises(runtime_paths.RuntimePathError):
                    runtime_paths.load_explicit_env_file(env)
                self.assertEqual(env, before)

    def test_env_file_failure_is_atomic_and_existing_empty_value_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"config.env"
            path.write_text("MONEY_CRAFT_DATA_HOME=/tmp/example-data\nunsupported line\n")
            path.chmod(0o600)
            env = {runtime_paths.ENV_FILE_ENV: str(path), "FRED_API_KEY": ""}
            before = dict(env)
            with self.assertRaises(runtime_paths.RuntimePathError):
                runtime_paths.load_explicit_env_file(env)
            self.assertEqual(env, before)
            path.write_text("FRED_API_KEY=synthetic-fixture\n")
            runtime_paths.load_explicit_env_file(env)
            self.assertEqual(env["FRED_API_KEY"], "")

    def test_explicit_env_file_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            path, link = Path(directory)/"config.env", Path(directory)/"link.env"
            path.write_text("MONEY_CRAFT_DATA_HOME=/tmp/example-data\n")
            path.chmod(0o600); link.symlink_to(path)
            env = {runtime_paths.ENV_FILE_ENV: str(link)}
            before = dict(env)
            with self.assertRaises(runtime_paths.RuntimePathError):
                runtime_paths.load_explicit_env_file(env)
            self.assertEqual(env, before)

    def test_cli_rejects_symlink_env_before_command_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path, link = Path(directory)/"config.env", Path(directory)/"link.env"
            path.write_text("MONEY_CRAFT_DATA_HOME=/tmp/example-data\n")
            path.chmod(0o600); link.symlink_to(path)
            env = dict(os.environ); env[runtime_paths.ENV_FILE_ENV] = str(link)
            result = subprocess.run([sys.executable, str(SCRIPT_DIR/"money_craft.py"), "self-test"], env=env, text=True, capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("synthetic-fixture", result.stdout+result.stderr)

    def test_default_paths_follow_xdg_categories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            config, config_source = runtime_paths.config_home({}, home=home)
            data, data_source = runtime_paths.data_home({}, home=home)
            cache, cache_source = runtime_paths.cache_home({}, home=home)
        self.assertEqual(config, home / ".config" / "money-craft")
        self.assertEqual(data, home / ".local" / "share" / "money-craft")
        self.assertEqual(cache, home / ".cache" / "money-craft")
        self.assertEqual({config_source, data_source, cache_source}, {"default"})

    def test_xdg_and_app_specific_absolute_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            environment = {
                "XDG_CONFIG_HOME": str(root / "config-base"),
                "XDG_DATA_HOME": str(root / "data-base"),
                "XDG_CACHE_HOME": str(root / "cache-base"),
            }
            self.assertEqual(
                runtime_paths.config_home(environment)[0],
                root / "config-base" / "money-craft",
            )
            self.assertEqual(
                runtime_paths.data_home(environment)[0],
                root / "data-base" / "money-craft",
            )
            self.assertEqual(
                runtime_paths.cache_home(environment)[0],
                root / "cache-base" / "money-craft",
            )
            environment["MONEY_CRAFT_DATA_HOME"] = str(root / "exact-data")
            self.assertEqual(runtime_paths.data_home(environment)[0], root / "exact-data")
        with self.assertRaises(runtime_paths.RuntimePathError):
            runtime_paths.data_home({"MONEY_CRAFT_DATA_HOME": "relative/path"})

    def test_runtime_prefers_new_data_home_and_has_bounded_legacy_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            preferred, source = runtime_paths.preferred_runtime_python("data", {}, home=home)
            self.assertEqual(
                preferred,
                home / ".local" / "share" / "money-craft" / "venvs" / "data" / "bin" / "python",
            )
            self.assertEqual(source, "default")

            legacy = home / ".config" / "money-craft" / "data-venv" / "bin" / "python"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("", encoding="utf-8")
            fallback, fallback_source = runtime_paths.preferred_runtime_python("data", {}, home=home)
            self.assertEqual(fallback, legacy)
            self.assertEqual(fallback_source, "legacy-fallback")

            new_runtime = preferred
            new_runtime.parent.mkdir(parents=True)
            new_runtime.write_text("", encoding="utf-8")
            selected, selected_source = runtime_paths.preferred_runtime_python("data", {}, home=home)
            self.assertEqual(selected, new_runtime)
            self.assertEqual(selected_source, "default")

    def test_explicit_env_file_is_secure_allowlisted_and_process_env_wins(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            env_file = root / ".env.local"
            env_file.write_text(
                "FRED_API_KEY=" + ("a" * 32) + "\nMONEY_CRAFT_DATA_HOME=" + str(root / "data") + "\n",
                encoding="utf-8",
            )
            env_file.chmod(0o600)
            environment = {
                runtime_paths.ENV_FILE_ENV: str(env_file),
                "FRED_API_KEY": "b" * 32,
            }
            loaded = runtime_paths.load_explicit_env_file(environment)
            self.assertEqual(loaded, env_file)
            self.assertEqual(environment["FRED_API_KEY"], "b" * 32)
            self.assertEqual(environment["MONEY_CRAFT_DATA_HOME"], str(root / "data"))
            self.assertEqual(environment[runtime_paths.ENV_FILE_ACTIVE_ENV], str(env_file))

            env_file.chmod(0o644)
            with self.assertRaises(runtime_paths.RuntimePathError):
                runtime_paths.load_explicit_env_file({runtime_paths.ENV_FILE_ENV: str(env_file)})

            env_file.chmod(0o600)
            env_file.write_text("PATH=/tmp\n", encoding="utf-8")
            with self.assertRaises(runtime_paths.RuntimePathError):
                runtime_paths.load_explicit_env_file({runtime_paths.ENV_FILE_ENV: str(env_file)})

    def test_optional_modules_are_probed_in_the_selected_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            python = Path(directory) / "python"
            python.symlink_to(Path(sys.executable))
            commands: list[list[str]] = []

            def runner(command: list[str], **_kwargs: object) -> SimpleNamespace:
                commands.append(command)
                return SimpleNamespace(
                    returncode=0,
                    stdout='{"markdown": true, "weasyprint": true, "pypdf": false}\n',
                )

            availability, error = mc.probe_python_modules(
                python,
                (("markdown", "markdown"), ("weasyprint", "weasyprint"), ("pypdf", "pypdf")),
                runner=runner,
            )
        self.assertEqual(
            availability,
            {"markdown": True, "weasyprint": True, "pypdf": False},
        )
        self.assertIsNone(error)
        self.assertEqual(commands[0][0], str(python))


if __name__ == "__main__":
    unittest.main()
