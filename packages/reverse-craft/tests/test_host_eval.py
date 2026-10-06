from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_support import ROOT


SPEC = importlib.util.spec_from_file_location("reverse_craft_host_eval", ROOT / "scripts" / "run_host_eval.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load run_host_eval.py")
HOST_EVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST_EVAL)


class HostEvalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema_bytes = HOST_EVAL.SCHEMA.read_bytes()
        self.response_schema = json.loads(self.schema_bytes)

    def test_profiles_and_response_schema_do_not_expose_expected_values(self) -> None:
        for name, profile in HOST_EVAL.PROFILES.items():
            response_schema = json.loads(HOST_EVAL.response_schema_path(profile).read_bytes())
            self.assertEqual([], HOST_EVAL.semantic_schema_keywords(response_schema))
            self.assertEqual([], HOST_EVAL.unsupported_schema_keywords(response_schema))
            self.assertNotIn("skill_name", response_schema["properties"])
            self.assertNotIn("skill_version", response_schema["properties"])
            self.assertEqual(set(profile["expected"]), set(response_schema["required"]))
            self.assertEqual(set(profile["expected"]), set(response_schema["properties"]))
            for host in ("codex", "pi"):
                with self.subTest(profile=name, host=host):
                    self.assertEqual(
                        [],
                        HOST_EVAL.expectation_exposure_errors(
                            HOST_EVAL.host_prompt(host, profile["prompt"]),
                            HOST_EVAL.private_contract(profile),
                            response_schema,
                        ),
                    )

    def test_exposure_detector_rejects_prompt_and_schema_answers(self) -> None:
        profile = HOST_EVAL.PROFILES["r44"]
        prompt_errors = HOST_EVAL.expectation_exposure_errors(
            HOST_EVAL.host_prompt("codex", profile["prompt"]) + " R44",
            HOST_EVAL.private_contract(profile),
            self.response_schema,
        )
        self.assertIn("prompt exposes expected value: R44", prompt_errors)

        contaminated = copy.deepcopy(self.response_schema)
        contaminated["properties"]["route_id"]["const"] = "R44"
        schema_errors = HOST_EVAL.expectation_exposure_errors(
            profile["prompt"], HOST_EVAL.private_contract(profile), contaminated,
        )
        self.assertIn("response schema exposes expected value: R44", schema_errors)
        self.assertIn(
            "response schema contains answer-bearing constraint: $.properties.route_id.const",
            schema_errors,
        )

        contaminated = copy.deepcopy(self.response_schema)
        contaminated["properties"]["evidence_chain"]["uniqueItems"] = True
        unsupported_errors = HOST_EVAL.expectation_exposure_errors(
            profile["prompt"], HOST_EVAL.private_contract(profile), contaminated,
        )
        self.assertIn(
            "response schema contains unsupported constraint: $.properties.evidence_chain.uniqueItems",
            unsupported_errors,
        )

    def test_validate_payload_normalizes_only_bounded_runtime_aliases(self) -> None:
        profile = HOST_EVAL.PROFILES["r44"]
        expected = profile["expected"]
        self.assertEqual([], HOST_EVAL.validate_payload(copy.deepcopy(expected), profile))
        source_phrase = copy.deepcopy(expected)
        source_phrase["runtime_truth"] = "normal Web search"
        self.assertEqual([], HOST_EVAL.validate_payload(source_phrase, profile))
        self.assertEqual(expected, HOST_EVAL.normalize_payload(source_phrase, profile))
        mutations = {
            "wrong route": lambda value: value.update({"route_id": "R3"}),
            "wrong module": lambda value: value.update({"module_reference": "wrong.md"}),
            "wrong runtime": lambda value: value.update({"runtime_truth": "other"}),
            "mutation allowed": lambda value: value.update({"mutates": True}),
            "wrong chain order": lambda value: value.update({"evidence_chain": list(reversed(value["evidence_chain"]))}),
            "missing field": lambda value: value.pop("route_id"),
            "extra field": lambda value: value.update({"explanation": "not allowed"}),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                value = copy.deepcopy(expected)
                mutate(value)
                self.assertTrue(HOST_EVAL.validate_payload(value, profile))
        for rejected_runtime in ("normal web search", "public Web search", "browser67"):
            with self.subTest(rejected_runtime=rejected_runtime):
                value = copy.deepcopy(expected)
                value["runtime_truth"] = rejected_runtime
                self.assertTrue(HOST_EVAL.validate_payload(value, profile))

    def test_r0_replan_profile_enforces_both_bounded_thresholds(self) -> None:
        profile = HOST_EVAL.PROFILES["r0-replan"]
        expected = profile["expected"]
        self.assertEqual(HOST_EVAL.R0_REPLAN_SCHEMA, HOST_EVAL.response_schema_path(profile))
        self.assertEqual([], HOST_EVAL.validate_payload(copy.deepcopy(expected), profile))
        source_label = copy.deepcopy(expected)
        source_label["progress_record"][0] = "hypothesis"
        self.assertEqual([], HOST_EVAL.validate_payload(source_label, profile))
        self.assertEqual(expected, HOST_EVAL.normalize_payload(source_label, profile))
        mutations = {
            "operation replan starts early": lambda value: value.update({"bounded_operation_replan": [True, True]}),
            "operation threshold missed": lambda value: value.update({"bounded_operation_replan": [False, False]}),
            "phase replan starts early": lambda value: value.update({"phase_move_replan": [True, True]}),
            "phase threshold missed": lambda value: value.update({"phase_move_replan": [False, False]}),
            "primary route changed": lambda value: value.update({"primary_route_unchanged": False}),
            "progress record reordered": lambda value: value.update({"progress_record": list(reversed(value["progress_record"]))}),
            "wrong gate": lambda value: value.update({"replan_gate": "availability"}),
            "no plan change": lambda value: value.update({"change_required": False}),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                value = copy.deepcopy(expected)
                mutate(value)
                self.assertTrue(HOST_EVAL.validate_payload(value, profile))
        for rejected_label in ("working hypothesis", "current theory", "hypotheses"):
            with self.subTest(rejected_label=rejected_label):
                value = copy.deepcopy(expected)
                value["progress_record"][0] = rejected_label
                self.assertTrue(HOST_EVAL.validate_payload(value, profile))

    def test_evaluation_receipt_is_content_bound_and_blind(self) -> None:
        prompt = HOST_EVAL.PROFILES["r3"]["prompt"]
        profile = HOST_EVAL.PROFILES["r3"]
        receipt = HOST_EVAL.evaluation_receipt(prompt, self.schema_bytes, profile)
        self.assertEqual("blind-contract", receipt["evaluation_mode"])
        self.assertFalse(receipt["expectation_exposed"])
        self.assertEqual(
            hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            receipt["evaluation_prompt_sha256"],
        )
        for host in ("codex", "pi"):
            self.assertEqual(
                hashlib.sha256(HOST_EVAL.host_prompt(host, prompt).encode("utf-8")).hexdigest(),
                receipt["host_prompt_sha256"][host],
            )
        self.assertEqual(hashlib.sha256(self.schema_bytes).hexdigest(), receipt["response_schema_sha256"])
        self.assertEqual(HOST_EVAL.expected_contract_sha256(profile), receipt["expected_contract_sha256"])
        self.assertEqual("reverse-craft", receipt["skill"]["name"])
        self.assertEqual("0.2.0", receipt["skill"]["version"])
        self.assertEqual(HOST_EVAL.skill_bundle_sha256(), receipt["skill"]["bundle_sha256"])

        r0_profile = HOST_EVAL.PROFILES["r0-replan"]
        r0_schema_bytes = HOST_EVAL.response_schema_path(r0_profile).read_bytes()
        r0_receipt = HOST_EVAL.evaluation_receipt(r0_profile["prompt"], r0_schema_bytes, r0_profile)
        self.assertEqual(
            hashlib.sha256(r0_schema_bytes).hexdigest(),
            r0_receipt["response_schema_sha256"],
        )
        self.assertNotEqual(receipt["response_schema_sha256"], r0_receipt["response_schema_sha256"])

        changed_aliases = copy.deepcopy(HOST_EVAL.PROFILES["r44"])
        original_hash = HOST_EVAL.expected_contract_sha256(changed_aliases)
        changed_aliases["normalizers"]["runtime_truth"]["public Web search"] = "Web search"
        self.assertNotEqual(original_hash, HOST_EVAL.expected_contract_sha256(changed_aliases))

        r0_aliases = copy.deepcopy(HOST_EVAL.PROFILES["r0-replan"])
        original_hash = HOST_EVAL.expected_contract_sha256(r0_aliases)
        r0_aliases["normalizers"]["progress_record"]["working hypothesis"] = "current hypothesis"
        self.assertNotEqual(original_hash, HOST_EVAL.expected_contract_sha256(r0_aliases))

    def test_hosts_use_explicit_invocation_and_allow_read_only_loading(self) -> None:
        prompt = HOST_EVAL.PROFILES["r3"]["prompt"]
        self.assertTrue(HOST_EVAL.host_prompt("codex", prompt).startswith("Use $reverse-craft"))
        self.assertTrue(HOST_EVAL.host_prompt("pi", prompt).startswith("/skill:reverse-craft "))
        self.assertNotIn("Do not call tools", prompt)
        self.assertIn("inspect only files inside that Skill", prompt)
        self.assertIn("evidence_chain must be a JSON array of strings", prompt)
        self.assertIn("preserve the full reference string without shortening it", prompt)

        r0_prompt = HOST_EVAL.PROFILES["r0-replan"]["prompt"]
        self.assertIn("bounded_operation_replan", r0_prompt)
        self.assertIn("phase_move_replan", r0_prompt)
        self.assertIn("task's checkpoint order", r0_prompt)
        self.assertNotIn("current hypothesis", r0_prompt)
        self.assertNotIn("feasibility gate", r0_prompt)

    def test_profile_tasks_match_the_private_route_contract(self) -> None:
        script = ROOT / "skills" / "reverse-craft" / "scripts" / "reverse_craft.py"
        for name, profile in HOST_EVAL.PROFILES.items():
            with self.subTest(profile=name):
                completed = subprocess.run(
                    ["python3", str(script), "route", "--hint", profile["task"], "--json"],
                    text=True,
                    capture_output=True,
                    check=True,
                )
                route = json.loads(completed.stdout)["primary"]
                self.assertEqual(profile["expected"]["route_id"], route["id"])
                self.assertEqual(profile["expected"]["module_reference"], route["reference"])

    def test_materialized_skill_snapshot_matches_source_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            identity = HOST_EVAL.materialize_skill(Path(raw) / "reverse-craft")
        self.assertEqual(HOST_EVAL.skill_bundle_sha256(), identity["bundle_sha256"])
        self.assertEqual(len(HOST_EVAL.skill_source_files()), identity["source_file_count"])

    def test_regrade_is_content_bound_and_preserves_source_failure(self) -> None:
        profile_name = "r44"
        profile = HOST_EVAL.PROFILES[profile_name]
        current = HOST_EVAL.evaluation_receipt(profile["prompt"], self.schema_bytes, profile)
        source = {
            "schema": "reverse-craft.host-eval.v2",
            "valid": False,
            "profile": profile_name,
            "requested": ["codex", "pi"],
            "results": [],
            "evaluation_mode": current["evaluation_mode"],
            "expectation_exposed": False,
            "evaluation_prompt_sha256": current["evaluation_prompt_sha256"],
            "host_prompt_sha256": current["host_prompt_sha256"],
            "response_schema_sha256": current["response_schema_sha256"],
            "skill": current["skill"],
        }
        for host in source["requested"]:
            source["results"].append({
                "host": host,
                "status": "failed",
                "valid": False,
                "exit_code": 0,
                "version": "test-host",
                "invocation": {"prompt_sha256": current["host_prompt_sha256"][host]},
                "skill_snapshot": current["skill"],
                "payload": copy.deepcopy(profile["expected"]),
                "errors": ["obsolete grader label"],
            })
        source["results"][0]["payload"]["runtime_truth"] = "normal Web search"

        with tempfile.TemporaryDirectory() as raw:
            source_path = Path(raw) / "source.json"
            source_path.write_text(json.dumps(source), encoding="utf-8")
            regraded = HOST_EVAL.regrade_receipt(
                source_path, profile_name, profile, self.schema_bytes,
            )
            self.assertTrue(regraded["valid"])
            self.assertFalse(regraded["source_receipt"]["valid"])
            self.assertEqual("obsolete grader label", regraded["results"][0]["source_errors"][0])
            self.assertEqual("normal Web search", regraded["results"][0]["payload"]["runtime_truth"])
            self.assertEqual("Web search", regraded["results"][0]["normalized_payload"]["runtime_truth"])
            self.assertEqual(
                HOST_EVAL.expected_contract_sha256(profile),
                regraded["expected_contract_sha256"],
            )

            source["host_prompt_sha256"]["pi"] = "tampered"
            source_path.write_text(json.dumps(source), encoding="utf-8")
            rejected = HOST_EVAL.regrade_receipt(
                source_path, profile_name, profile, self.schema_bytes,
            )
            self.assertFalse(rejected["valid"])
            self.assertTrue(any("host prompt hashes" in error for error in rejected["errors"]))

            source["host_prompt_sha256"] = current["host_prompt_sha256"]
            source["results"].append(copy.deepcopy(source["results"][0]))
            source_path.write_text(json.dumps(source), encoding="utf-8")
            rejected = HOST_EVAL.regrade_receipt(
                source_path, profile_name, profile, self.schema_bytes,
            )
            self.assertFalse(rejected["valid"])
            self.assertTrue(any("source result count" in error for error in rejected["errors"]))

    def test_safe_error_tail_redacts_credentials(self) -> None:
        rendered = HOST_EVAL.safe_error_tail(
            "API key provided: secret-value, Authorization: Bearer token.value-123"
        )
        self.assertNotIn("secret-value", rendered)
        self.assertNotIn("token.value-123", rendered)
        self.assertEqual(2, rendered.count("[REDACTED]"))


if __name__ == "__main__":
    unittest.main()
