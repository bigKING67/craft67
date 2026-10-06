from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT
from tools.design_craft.routing.manifest import (
    ROUTE_PACK_MANIFEST_PATH,
    ROUTE_PACK_MANIFEST_SCHEMA,
)


SCRIPT = REPO_ROOT / "scripts/design_craft_codex_route_pack.py"


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def create_source(root: Path, *, version: int = 1) -> None:
    manifest = root / ROUTE_PACK_MANIFEST_PATH
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema": ROUTE_PACK_MANIFEST_SCHEMA,
                "version": version,
                "files": [
                    {
                        "path": ROUTE_PACK_MANIFEST_PATH,
                        "required": True,
                        "route_pack": True,
                        "snapshot": True,
                        "kind": "route-manifest",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )


class RoutePackCliTests(unittest.TestCase):
    def test_builtin_self_check(self) -> None:
        completed = run_cli("--check")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_strict_invalid_manifest_returns_one_with_schema_payload(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "source"
            create_source(source, version=2)

            completed = run_cli("--source-root", str(source), "--strict", "--json")

            self.assertEqual(completed.returncode, 1, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["schema"], "design-craft.codex-route-pack.v2")
            self.assertEqual(payload["status"], "manifest-error")

    def test_invalid_manifest_cannot_be_exported(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temporary = Path(raw)
            source = temporary / "source"
            export = temporary / "export"
            create_source(source, version=2)

            completed = run_cli(
                "--source-root",
                str(source),
                "--export-dir",
                str(export),
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("invalid route-pack manifest", completed.stderr)
            self.assertFalse(export.exists())


if __name__ == "__main__":
    unittest.main()
