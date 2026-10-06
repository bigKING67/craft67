from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

from tools.design_craft.release.policy import load_policy
from tools.design_craft.repo import repo_path


class ReleasePolicyTests(unittest.TestCase):
    def load_mutated(
        self, mutate: Callable[[dict[str, Any]], None]
    ) -> object:
        payload = json.loads(
            repo_path("contracts/release/policy.json").read_text(encoding="utf-8")
        )
        mutate(payload)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "policy.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_policy(path)

    def test_asset_sets_are_exact_and_tiered(self) -> None:
        policy = load_policy()
        operational = policy["operational_95"].assets("0.5.0")
        certified = policy["certified_100"].assets("0.5.0")
        self.assertEqual(len(operational), 4)
        self.assertEqual(len(certified), 7)
        self.assertTrue(set(operational).issubset(certified))
        self.assertIn("design-craft-v0.5.0.spdx.json", operational)

    def test_certified_requirements_extend_operational(self) -> None:
        policy = load_policy()
        operational = policy["operational_95"]
        certified = policy["certified_100"]
        self.assertTrue(set(operational.required_hosts).issubset(certified.required_hosts))
        self.assertTrue(set(operational.required_native).issubset(certified.required_native))
        self.assertFalse(operational.permanent_native_bundle)
        self.assertTrue(certified.permanent_native_bundle)

    def test_operational_missing_required_domain_is_rejected(self) -> None:
        def mutate(payload: dict[str, Any]) -> None:
            domains = payload["levels"]["operational_95"]["required_domains"]
            domains.remove("performance_regression")

        with self.assertRaisesRegex(ValueError, "operational_95.required_domains"):
            self.load_mutated(mutate)

    def test_certified_missing_physical_evidence_requirement_is_rejected(self) -> None:
        def mutate(payload: dict[str, Any]) -> None:
            required = payload["levels"]["certified_100"]["required_native"]
            required.remove("physical_device")

        with self.assertRaisesRegex(ValueError, "certified_100.required_native"):
            self.load_mutated(mutate)

    def test_operational_policy_cannot_replace_sbom_with_native_asset(self) -> None:
        def mutate(payload: dict[str, Any]) -> None:
            assets = payload["levels"]["operational_95"]["assets"]
            assets[-1] = "design-craft-v{version}-native-runtime.tgz"

        with self.assertRaisesRegex(ValueError, "operational_95.assets"):
            self.load_mutated(mutate)


if __name__ == "__main__":
    unittest.main()
