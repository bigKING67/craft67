from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.validation.profile_contract import profile_contract_errors
from tools.design_craft.validation.registry import load_registry, select_gates


PORTABLE_PARALLEL_GATES = (
    "skill-schema",
    "repository-contracts",
    "tooling-contracts",
    "lint",
    "package-boundary",
    "public-repository",
    "workflow-contract",
    "upstream-review-contract",
    "upstream-absorption-report",
    "taste-absorption",
    "impeccable-absorption",
    "emil-absorption",
    "cross-agent-run-self-check",
    "cross-agent-validator-self-check",
    "comparative-run-self-check",
    "comparative-judge-self-check",
    "comparative-validator-self-check",
    "native-runtime-self-check",
    "github-checks-self-check",
    "github-governance-self-check",
    "install-verifier-self-check",
    "route-pack-self-check",
    "maturity-self-check",
    "source-test-suite",
)

CONTRACT_GATES = (
    "workflow-contract",
    "cross-agent-run-self-check",
    "cross-agent-validator-self-check",
    "comparative-run-self-check",
    "comparative-judge-self-check",
    "comparative-validator-self-check",
    "native-runtime-self-check",
    "github-checks-self-check",
    "github-governance-self-check",
    "source-test-suite",
)


class ValidationRegistryTests(unittest.TestCase):
    def test_repository_registry_selects_portable_gates(self) -> None:
        gates = select_gates(load_registry(), "portable")
        self.assertEqual(
            [gate.gate_id for gate in gates],
            [*PORTABLE_PARALLEL_GATES, "development-maturity"],
        )
        self.assertEqual(gates[-1].depends_on, PORTABLE_PARALLEL_GATES)
        self.assertGreater(
            next(gate.priority for gate in gates if gate.gate_id == "source-test-suite"),
            next(gate.priority for gate in gates if gate.gate_id == "skill-schema"),
        )
        test_suite = next(
            gate for gate in gates if gate.gate_id == "source-test-suite"
        )
        self.assertEqual(
            test_suite.command,
            (
                "python3",
                "scripts/design_craft_parallel_unittest.py",
                "--jobs",
                "8",
                "--include-discover-dir=tests/unit",
                "--include-discover-dir=tests/integration",
                "--include-discover-dir=tests/adversarial",
                "--include-target=tests.contract.test_installer",
            ),
        )
        self.assertEqual(profile_contract_errors(gates, "portable"), [])

    def test_contract_profile_matches_public_contract_target(self) -> None:
        gates = select_gates(load_registry(), "contracts")
        self.assertEqual(tuple(gate.gate_id for gate in gates), CONTRACT_GATES)
        self.assertTrue(all(gate.execution == "parallel" for gate in gates))
        self.assertEqual(profile_contract_errors(gates, "contracts"), [])

    def test_profile_contract_rejects_missing_bootstrap_test_gate(self) -> None:
        for missing_gate_id in ("source-test-suite",):
            with self.subTest(missing_gate_id=missing_gate_id):
                gates = tuple(
                    gate
                    for gate in select_gates(load_registry(), "portable")
                    if gate.gate_id != missing_gate_id
                )
                errors = profile_contract_errors(gates, "portable")
                self.assertTrue(
                    any(missing_gate_id in error for error in errors)
                )

    def test_duplicate_gate_ids_fail(self) -> None:
        payload = {
            "schema": "design-craft.validation-gates.v1",
            "gates": [
                {
                    "id": "duplicate",
                    "command": ["python3", "--version"],
                    "profiles": ["portable"],
                    "timeout_seconds": 10,
                    "execution": "parallel",
                },
                {
                    "id": "duplicate",
                    "command": ["python3", "--version"],
                    "profiles": ["portable"],
                    "timeout_seconds": 10,
                    "execution": "parallel",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gates.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate validation gate id"):
                load_registry(path)

    def test_profile_cannot_omit_dependency(self) -> None:
        payload = {
            "schema": "design-craft.validation-gates.v1",
            "gates": [
                {
                    "id": "base",
                    "command": ["python3", "--version"],
                    "profiles": ["local"],
                    "timeout_seconds": 10,
                    "execution": "parallel",
                },
                {
                    "id": "dependent",
                    "command": ["python3", "--version"],
                    "profiles": ["portable", "local"],
                    "timeout_seconds": 10,
                    "execution": "serial",
                    "depends_on": ["base"],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gates.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "without dependencies"):
                select_gates(load_registry(path), "portable")

    def test_dependency_must_precede_dependent_gate(self) -> None:
        payload = {
            "schema": "design-craft.validation-gates.v1",
            "gates": [
                {
                    "id": "dependent",
                    "command": ["python3", "--version"],
                    "profiles": ["portable"],
                    "timeout_seconds": 10,
                    "execution": "serial",
                    "depends_on": ["later"],
                },
                {
                    "id": "later",
                    "command": ["python3", "--version"],
                    "profiles": ["portable"],
                    "timeout_seconds": 10,
                    "execution": "parallel",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gates.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must reference earlier gates"):
                load_registry(path)

    def test_parallel_gate_cannot_declare_dependencies(self) -> None:
        payload = {
            "schema": "design-craft.validation-gates.v1",
            "gates": [
                {
                    "id": "base",
                    "command": ["python3", "--version"],
                    "profiles": ["portable"],
                    "timeout_seconds": 10,
                    "execution": "parallel",
                },
                {
                    "id": "dependent",
                    "command": ["python3", "--version"],
                    "profiles": ["portable"],
                    "timeout_seconds": 10,
                    "execution": "parallel",
                    "depends_on": ["base"],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gates.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not declare dependencies"):
                load_registry(path)

    def test_priority_must_be_non_negative(self) -> None:
        payload = {
            "schema": "design-craft.validation-gates.v1",
            "gates": [
                {
                    "id": "invalid-priority",
                    "command": ["python3", "--version"],
                    "profiles": ["portable"],
                    "timeout_seconds": 10,
                    "execution": "parallel",
                    "priority": -1,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "gates.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-negative integer"):
                load_registry(path)


if __name__ == "__main__":
    unittest.main()
