from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from design_craft_github_governance import (  # noqa: E402
    ACTIONS_PERMISSIONS,
    REVIEWED_TRANSITIVE_ACTIONS,
    SELECTED_ACTIONS,
    _api_failure,
    desired_rulesets,
    reviewed_action_patterns,
    validate_actions_permissions,
    validate_ruleset,
)


class GitHubGovernanceContractTests(unittest.TestCase):
    def test_administration_denial_has_machine_readable_classification(self) -> None:
        result = subprocess.CompletedProcess(
            ["gh", "api"],
            1,
            stdout="",
            stderr="HTTP 403: Resource not accessible by integration",
        )
        error = _api_failure(result, "repos/example/design-craft/actions/permissions")
        self.assertEqual(error.code, "insufficient_permissions")
        self.assertIn("actions/permissions", error.endpoint)

    def test_desired_rulesets_validate_without_bypass(self) -> None:
        for payload in desired_rulesets().values():
            self.assertEqual(validate_ruleset(payload, payload), [])

    def test_main_ruleset_allows_normal_direct_pushes(self) -> None:
        main = desired_rulesets()["design-craft-main"]
        rule_types = {rule["type"] for rule in main["rules"]}
        self.assertEqual(rule_types, {"deletion", "non_fast_forward"})

    def test_ruleset_bypass_is_rejected(self) -> None:
        expected = desired_rulesets()["design-craft-main"]
        observed = {**expected, "bypass_actors": [{"actor_type": "RepositoryRole"}]}
        errors = validate_ruleset(observed, expected)
        self.assertTrue(any("bypass_actors" in error for error in errors))

    def test_actions_permission_drift_is_rejected(self) -> None:
        observed = {**ACTIONS_PERMISSIONS, "sha_pinning_required": False}
        errors = validate_actions_permissions(observed, SELECTED_ACTIONS)
        self.assertTrue(any("sha_pinning_required" in error for error in errors))

    def test_selected_actions_include_reviewed_transitive_dependencies(self) -> None:
        self.assertEqual(
            REVIEWED_TRANSITIVE_ACTIONS,
            {
                "actions/attest-build-provenance@*": frozenset(
                    {
                        "actions/attest-build-provenance/predicate@*",
                        "actions/attest@*",
                    }
                )
            },
        )
        self.assertEqual(
            set(SELECTED_ACTIONS["patterns_allowed"]),
            reviewed_action_patterns(),
        )

    def test_selected_actions_reject_missing_transitive_dependency(self) -> None:
        for dependency in REVIEWED_TRANSITIVE_ACTIONS[
            "actions/attest-build-provenance@*"
        ]:
            with self.subTest(dependency=dependency):
                selected = {
                    **SELECTED_ACTIONS,
                    "patterns_allowed": [
                        pattern
                        for pattern in SELECTED_ACTIONS["patterns_allowed"]
                        if pattern != dependency
                    ],
                }
                errors = validate_actions_permissions(ACTIONS_PERMISSIONS, selected)
                self.assertTrue(any("patterns" in error for error in errors))

    def test_reviewed_transitive_parent_must_be_used_by_workflow(self) -> None:
        with patch.dict(
            REVIEWED_TRANSITIVE_ACTIONS,
            {"example/unused@*": frozenset({"example/dependency@*"})},
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "not used by a workflow"):
                reviewed_action_patterns()

    def test_selected_actions_do_not_allow_repository_wildcards(self) -> None:
        for pattern in SELECTED_ACTIONS["patterns_allowed"]:
            repository, separator, revision = pattern.partition("@")
            self.assertEqual(separator, "@")
            self.assertEqual(revision, "*")
            self.assertNotIn("*", repository)


if __name__ == "__main__":
    unittest.main()
