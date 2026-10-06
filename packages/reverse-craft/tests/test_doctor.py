from __future__ import annotations

import json
import subprocess
import unittest
from unittest import mock

from test_support import ROOT  # noqa: F401

from reverse_craft.doctor import _mcp_inventory


class DoctorTests(unittest.TestCase):
    @mock.patch("reverse_craft.doctor.subprocess.run")
    @mock.patch("reverse_craft.doctor.shutil.which", return_value="/mock/codex")
    def test_mcp_inventory_never_returns_transport_secrets(self, _which: mock.Mock, run: mock.Mock) -> None:
        canary = "rc-secret-canary"
        payload = [{
            "name": "js-reverse",
            "enabled": True,
            "transport": {
                "type": "stdio",
                "command": "/safe/js-reverse",
                "args": ["--api-key", canary, "--mode=managed"],
                "cwd": "/safe/browser67",
                "env": {"API_TOKEN": canary, "SAFE_MODE": "1"},
                "headers": {"Authorization": f"Bearer {canary}", "X-Mode": "managed"},
                "url": f"https://user:{canary}@example.test/private?token={canary}",
                "unknown_secret_field": canary,
            },
        }]
        run.return_value = subprocess.CompletedProcess([], 0, json.dumps(payload), "")

        result = _mcp_inventory()

        rendered = json.dumps(result, sort_keys=True)
        self.assertNotIn(canary, rendered)
        transport = result["servers"][0]["transport"]
        self.assertEqual(3, transport["args_count"])
        self.assertEqual(["API_TOKEN", "SAFE_MODE"], transport["env_keys"])
        self.assertEqual(["Authorization", "X-Mode"], transport["header_keys"])
        self.assertEqual("https://example.test", transport["url_origin"])
        self.assertNotIn("args", transport)
        self.assertNotIn("env", transport)
        self.assertNotIn("headers", transport)

    @mock.patch("reverse_craft.doctor.subprocess.run")
    @mock.patch("reverse_craft.doctor.shutil.which", return_value="/mock/codex")
    def test_mcp_error_reason_does_not_return_stderr(self, _which: mock.Mock, run: mock.Mock) -> None:
        canary = "rc-secret-canary"
        run.return_value = subprocess.CompletedProcess([], 1, "", f"API_TOKEN={canary}")

        result = _mcp_inventory()

        self.assertFalse(result["checked"])
        self.assertNotIn(canary, result["reason"])
        self.assertEqual("codex_mcp_list_failed", result["reason"])
        self.assertEqual(1, result["exit_code"])

    @mock.patch("reverse_craft.doctor.subprocess.run")
    @mock.patch("reverse_craft.doctor.shutil.which", return_value="/mock/codex")
    def test_mcp_inventory_rejects_malformed_server_collection(self, _which: mock.Mock, run: mock.Mock) -> None:
        run.return_value = subprocess.CompletedProcess([], 0, '{"servers": null}', "")

        result = _mcp_inventory()

        self.assertFalse(result["checked"])
        self.assertEqual("invalid_codex_json", result["reason"])

    @mock.patch("reverse_craft.doctor.subprocess.run")
    @mock.patch("reverse_craft.doctor.shutil.which", return_value="/mock/codex")
    def test_mcp_inventory_ignores_non_string_server_identity(self, _which: mock.Mock, run: mock.Mock) -> None:
        run.return_value = subprocess.CompletedProcess([], 0, '{"servers": [{"name": {}}]}', "")

        result = _mcp_inventory()

        self.assertTrue(result["checked"])
        self.assertEqual([], result["servers"])


if __name__ == "__main__":
    unittest.main()
