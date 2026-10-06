from __future__ import annotations

import json
import os
import stat
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import ROOT  # noqa: F401

from reverse_craft.common import ReverseCraftError
from reverse_craft.provenance import audit_references
from reverse_craft.setup_ops import _plan_digest, _redact_output, apply_plan, create_plan, setup_status


class SetupAndProvenanceTests(unittest.TestCase):
    def test_setup_output_redacts_prefixed_secret_names(self) -> None:
        canary = "rc-secret-canary"
        output = _redact_output(f"API_TOKEN={canary}\nAuthorization: Bearer {canary}")
        self.assertNotIn(canary, output)
        self.assertEqual(2, output.count("[REDACTED]"))

    def test_reference_audit(self) -> None:
        result = audit_references()
        self.assertTrue(result["valid"])
        manifest = json.loads(
            (ROOT / "skills/reverse-craft/references/provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [entry["path"] for entry in manifest["paths"]],
            [check["path"] for check in result["checks"]],
        )

    def test_reference_audit_in_standalone_skill(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "reverse-craft"
            shutil.copytree(ROOT / "skills" / "reverse-craft", target)
            completed = subprocess.run(
                [sys.executable, str(target / "scripts/reverse_craft.py"), "references", "audit", "--json"],
                text=True, capture_output=True, timeout=20, check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertTrue(result["valid"])
            self.assertFalse(result["source_checkout"])
            self.assertEqual(2, sum(1 for item in result["checks"] if item.get("skipped")))

    def test_empty_setup_plan_requires_hash_and_is_single_use(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "home"
            plan_path = root / "plan.json"
            receipt = create_plan("ios", str(plan_path), str(home))
            self.assertEqual(0, receipt["actions"])
            with self.assertRaises(ReverseCraftError):
                apply_plan(str(plan_path), "0" * 64, True, str(home))
            result = apply_plan(str(plan_path), receipt["sha256"], True, str(home))
            self.assertEqual("complete", result["status"])
            self.assertEqual(1, len(setup_status(str(home))["transactions"]))
            if os.name != "nt":
                self.assertEqual(0o700, stat.S_IMODE((home / "setup").stat().st_mode))
                self.assertEqual(0o700, stat.S_IMODE((home / "setup" / "transactions").stat().st_mode))
                self.assertEqual(0o600, stat.S_IMODE(Path(result["journal"]).stat().st_mode))
            with self.assertRaises(ReverseCraftError):
                apply_plan(str(plan_path), receipt["sha256"], True, str(home))

    def test_setup_plan_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "home"
            path = root / "plan.json"
            receipt = create_plan("ios", str(path), str(home))
            plan = json.loads(path.read_text(encoding="utf-8"))
            plan["profile"] = "all"
            path.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaises(ReverseCraftError):
                apply_plan(str(path), receipt["sha256"], True, str(home))

    def test_setup_plan_id_cannot_escape_transaction_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "home"
            path = root / "plan.json"
            create_plan("ios", str(path), str(home))
            plan = json.loads(path.read_text(encoding="utf-8"))
            plan["id"] = "../../escape"
            plan["plan_sha256"] = _plan_digest(plan)
            path.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaises(ReverseCraftError):
                apply_plan(str(path), plan["plan_sha256"], True, str(home))
            self.assertFalse((root / "escape.json").exists())

    def test_setup_requires_yes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "home"
            path = root / "plan.json"
            receipt = create_plan("ios", str(path), str(home))
            with self.assertRaises(ReverseCraftError):
                apply_plan(str(path), receipt["sha256"], False, str(home))

    @mock.patch("reverse_craft.setup_ops.shutil.which")
    def test_non_privileged_apt_is_plan_only(self, which: mock.Mock) -> None:
        values = {"brew": None, "apt-get": "/usr/bin/apt-get", "winget": None, "jq": None}
        which.side_effect = lambda name: values.get(name)
        with tempfile.TemporaryDirectory() as raw, mock.patch("reverse_craft.setup_ops._has_root_privileges", return_value=False):
            receipt = create_plan("core", str(Path(raw) / "plan.json"), str(Path(raw) / "home"))
            self.assertEqual(0, receipt["actions"])
            self.assertIn("jq", {item["tool"] for item in receipt["unavailable"]})


if __name__ == "__main__":
    unittest.main()
