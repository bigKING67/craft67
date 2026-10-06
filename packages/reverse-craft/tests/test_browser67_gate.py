from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

from test_support import ROOT


SPEC = importlib.util.spec_from_file_location(
    "reverse_craft_browser67_gate",
    ROOT / "scripts" / "check_browser67_mcp.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load check_browser67_mcp.py")
BROWSER67_GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BROWSER67_GATE)


class Browser67GateTests(unittest.TestCase):
    def test_surface_only_never_calls_orphan_cleanup(self) -> None:
        home = Path("/tmp/browser67-test-home")
        client = object()
        with mock.patch.object(BROWSER67_GATE, "cleanup_fixture_orphans") as cleanup:
            result = BROWSER67_GATE.maybe_cleanup_fixture_orphans(True, home, client, 30)

        cleanup.assert_not_called()
        self.assertEqual({
            "status": "not_requested",
            "reason": "surface_only",
            "closed_count": 0,
        }, result)

    def test_full_live_gate_executes_bounded_orphan_cleanup(self) -> None:
        home = Path("/tmp/browser67-test-home")
        client = object()
        with mock.patch.object(BROWSER67_GATE, "cleanup_fixture_orphans", return_value=2) as cleanup:
            result = BROWSER67_GATE.maybe_cleanup_fixture_orphans(False, home, client, 30)

        cleanup.assert_called_once_with(home, client, 30)
        self.assertEqual({
            "status": "executed",
            "reason": "full_live_gate",
            "closed_count": 2,
        }, result)


if __name__ == "__main__":
    unittest.main()
