from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from test_support import ROOT

from reverse_craft.cli import _print, main

CLI = ROOT / "skills" / "reverse-craft" / "scripts" / "reverse_craft.py"


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(CLI), *args], text=True, capture_output=True, timeout=20, check=False)

    def test_version(self) -> None:
        completed = self.run_cli("--version")
        self.assertEqual(0, completed.returncode)
        self.assertEqual("0.2.0", completed.stdout.strip())

    def test_route_json(self) -> None:
        completed = self.run_cli("route", "--hint", "JS reverse request signature", "--json")
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("R3", json.loads(completed.stdout)["primary"]["id"])

    def test_json_output_falls_back_to_ascii_on_legacy_console(self) -> None:
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1252")
        _print({"message": "中文"}, stream=stream)
        stream.flush()
        rendered = raw.getvalue().decode("cp1252")
        self.assertEqual({"message": "中文"}, json.loads(rendered))

    def test_route_json_on_legacy_console_encoding(self) -> None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "cp1252"
        completed = subprocess.run(
            [sys.executable, str(CLI), "route", "--hint", "JS reverse request signature", "--json"],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
            env=env,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("R3", json.loads(completed.stdout)["primary"]["id"])

    def test_invalid_case_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            completed = self.run_cli("case", "status", "--case", "../escape", "--home", raw)
        self.assertEqual(2, completed.returncode)
        self.assertEqual(
            {"schema": "reverse-craft.error.v1", "error": "invalid case id: '../escape'"},
            json.loads(completed.stderr),
        )

    def test_unexpected_exception_returns_redacted_crash_diagnostic(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        secret = "token=must-not-escape /private/case/path"

        with (
            mock.patch("reverse_craft.cli.run", side_effect=RuntimeError(secret)),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            return_code = main(["route", "--hint", "offline fixture", "--json"])

        self.assertEqual(3, return_code)
        self.assertEqual("", stdout.getvalue())
        self.assertEqual(
            {
                "schema": "reverse-craft.crash.v1",
                "error": "unexpected internal error",
                "exception_type": "RuntimeError",
            },
            json.loads(stderr.getvalue()),
        )
        self.assertNotIn(secret, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
