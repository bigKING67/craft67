from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class RoutePackStartupTests(unittest.TestCase):
    def test_direct_check_skips_general_cli_import(self) -> None:
        code = (
            "import runpy, sys; "
            "sys.argv=['scripts/design_craft_codex_route_pack.py', '--check']; "
            "exit_code=0; "
            "\ntry: runpy.run_path(sys.argv[0], run_name='__main__')"
            "\nexcept SystemExit as exc: exit_code=exc.code; "
            "\nprint(exit_code); "
            "print('tools.design_craft.routing.cli' in sys.modules)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["0", "False"])

    def test_cli_import_keeps_semantic_runtime_lazy(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import tools.design_craft.routing.cli; "
                "print('tools.design_craft.routing.semantic_audit' in sys.modules)",
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False")


if __name__ == "__main__":
    unittest.main()
