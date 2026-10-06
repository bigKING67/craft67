from __future__ import annotations

import unittest
import tempfile
import json
from concurrent.futures import Future
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from tools.design_craft.routing.semantic_audit import _semantic_validation
from tools.design_craft.routing.semantic_contract import REQUIRED_FRAGMENTS, semantic_paths
from tools.design_craft.routing.semantic_runtime import (
    RuntimeValidation,
    _validate_route_probes,
    _validate_model_profiles,
    route_probe_requests,
)


from tools.design_craft.routing.semantic_static import validate_worker, validate_routing_config


class SemanticAuditTests(unittest.TestCase):
    def test_worker_accepts_inherited_and_explicit_role_profiles(self) -> None:
        base = 'name = "worker"\ndescription = "Bounded worker"\ndeveloper_instructions = "Follow host authority"\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "worker.toml"
            for profile in ("", 'model = "gpt-5.6-sol"\nmodel_reasoning_effort = "high"\n'):
                path.write_text(base + profile)
                self.assertEqual(validate_worker(path), [])
            for profile in ('model = ""', 'model = 42',
                            'model_reasoning_effort = "unknown"',
                            'model_reasoning_effort = false'):
                with self.subTest(profile=profile):
                    path.write_text(base + profile)
                    self.assertTrue(validate_worker(path))

    def test_explicit_worker_profile_is_checked_against_host_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.toml"
            worker = root / "worker.toml"
            config.write_text("")
            catalog = Future()
            catalog.set_result(({
                "gpt-5.6-sol": {"supported_reasoning_levels": [{"effort": "high"}]},
            }, None))
            paths = SimpleNamespace(config=config, worker_agent=worker)
            batch = SimpleNamespace(model_catalog=catalog)
            for model, effort, expected in (
                ("gpt-5.6-sol", "high", ""),
                ("unknown-model", "high", "unknown model"),
                ("gpt-5.6-sol", "unsupported", "unsupported reasoning"),
            ):
                with self.subTest(model=model, effort=effort):
                    worker.write_text(
                        f'model = "{model}"\nmodel_reasoning_effort = "{effort}"\n'
                    )
                    profiles, issues, warnings, _ = _validate_model_profiles(paths, batch)
                    self.assertEqual(profiles[0]["role"], "worker.toml")
                    self.assertEqual(warnings, [])
                    if expected:
                        self.assertTrue(any(expected in issue for issue in issues))
                    else:
                        self.assertEqual(issues, [])

    def test_ultra_does_not_imply_automatic_delegation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "routing.json"
            for value in (False, True, None):
                reasoning = {level: {} for level in (
                    "inherit", "low", "medium", "high", "xhigh", "max", "ultra"
                )}
                reasoning["ultra"] = {
                    "explicit_override_allowed": False,
                    "runtime_auto_delegation": value,
                    "fallback_reasoning_target": "max",
                }
                path.write_text(json.dumps({"reasoning_overrides": reasoning}))
                issues = validate_routing_config(path)
                self.assertEqual(
                    any("reasoning alone" in issue for issue in issues),
                    value is not False,
                )

    def test_static_work_runs_before_waiting_for_runtime_results(self) -> None:
        events: list[str] = []
        batch = object()

        def submit(*_args: object, **_kwargs: object) -> object:
            events.append("submit")
            return batch

        def static(*_args: object, **_kwargs: object) -> list[str]:
            events.append("static")
            return ["static issue"]

        def schema(observed: object) -> list[str]:
            self.assertIs(observed, batch)
            events.append("schema")
            return ["schema issue"]

        def runtime(*_args: object, **_kwargs: object) -> RuntimeValidation:
            events.append("runtime")
            return RuntimeValidation(
                issues=["runtime issue"],
                warnings=[],
                probes=[],
                profiles=[],
                model_catalog_source="not-run",
            )

        with (
            patch(
                "tools.design_craft.routing.semantic_audit.submit_runtime_probe_batch",
                side_effect=submit,
            ),
            patch(
                "tools.design_craft.routing.semantic_audit.static_validation",
                side_effect=static,
            ),
            patch(
                "tools.design_craft.routing.semantic_audit.validate_schema_probe",
                side_effect=schema,
            ),
            patch(
                "tools.design_craft.routing.semantic_audit.runtime_validation",
                side_effect=runtime,
            ),
        ):
            result = _semantic_validation(Path("/route-pack"), object())

        self.assertEqual(events, ["submit", "static", "schema", "runtime"])
        self.assertEqual(
            result["issues"],
            ["schema issue", "static issue", "runtime issue"],
        )
        self.assertEqual(result["status"], "error")

    def test_route_module_inventory_preserves_stable_order(self) -> None:
        names = [path.name for path in semantic_paths(Path("/pack")).route_files]

        self.assertEqual(names[0], "frontend_route_plan.sh")
        self.assertEqual(names[-1], "frontend_worker_payload_core.py")
        self.assertIn("frontend_route_evidence.py", names)
        self.assertIn("frontend_route_visual_review.py", names)
        self.assertEqual(len(names), 19)
        self.assertEqual(len(names), len(set(names)))

    def test_browser_lifecycle_static_contract_requires_v2_schemas(self) -> None:
        fragments = REQUIRED_FRAGMENTS["frontend_route_browser_contract.py"]

        self.assertIn(
            'RECEIPT_SCHEMA = "frontend-route.browser-lifecycle-receipt.v2"',
            fragments,
        )
        self.assertIn(
            'OBSERVATIONS_SCHEMA = "frontend-route.browser-lifecycle-observations.v2"',
            fragments,
        )
        self.assertFalse(
            any("browser-lifecycle-receipt.v1" in item for item in fragments)
        )
        self.assertFalse(
            any("browser-lifecycle-observations.v1" in item for item in fragments)
        )

    def test_runtime_probe_contract_keeps_seven_bounded_routes(self) -> None:
        requests = route_probe_requests()

        self.assertEqual(len(requests), 7)
        self.assertIn("parallel", requests[6][0])
        self.assertEqual(requests[6][0][-2:], ["--delegation-authorization", "none"])
        self.assertEqual(requests[0][0][-1], "external")
        self.assertEqual(requests[3][0][-2:], ["--browser-context", "local"])
        self.assertEqual(requests[4][2], "ultra")
        self.assertIn("comp-fidelity", requests[5][0])

    def test_local_and_compact_route_probes_require_browser67_lifecycle(self) -> None:
        browser_lifecycle = {"applicable": True, "managed_runtime": "browser67"}

        def browser_payload() -> dict:
            return {
                "preferred_browser_tool": "tmwd_browser",
                "preferred_runtime_tool": "tmwd_browser",
                "planned_browser_lifecycle": browser_lifecycle,
                "browser_lifecycle": browser_lifecycle,
                "actual_browser_lifecycle_state": {
                    "state": "not_started",
                    "finalize_result": "not_started",
                    "delivery_summary_observed": False,
                },
                "style_authority_applicability": "not_applicable",
                "visual_contract_required": False,
            }

        compact = {
            "schema": "frontend-route.compact.v1",
            "route": {"frontend_tier": "L1-F"},
            "runtime_profile": {"verified": True},
            "validation": {"preflight_code": "OK"},
            "planned_browser_lifecycle": browser_lifecycle,
            "browser_lifecycle": browser_lifecycle,
            "actual_browser_lifecycle_state": {
                "state": "not_started",
                "finalize_result": "not_started",
            },
        }
        results = [
            (0, browser_payload(), ""),
            (0, browser_payload(), ""),
            (
                0,
                {
                    "runtime_profile_source": "environment",
                    "runtime_profile_verified": True,
                    "effective_model": "gpt-5.6-sol",
                    "effective_reasoning": "max",
                    "reasoning_application_status": "runtime_verified",
                    "runtime_profile_evidence": {
                        "kind": "explicit_environment",
                        "contains_prompt_data": False,
                    },
                },
                "",
            ),
            (0, compact, ""),
            (
                0,
                {
                    "route_status": "ok",
                    "route_error_code": "",
                    "gate_decision": "allow",
                    "runtime_profile_verified": True,
                    "effective_model": "gpt-5.6-sol",
                    "effective_reasoning": "ultra",
                    "delegation_authorized": False,
                    "delegation_authorization_missing": False,
                    "planned_execution_mode": "main_serial",
                    "actual_subagent_state": "not_started",
                    "subagent_required": False,
                    "runtime_auto_delegation_risk": False,
                },
                "",
            ),
            (
                0,
                {
                    "evidence_mode": "comp-fidelity",
                    "runtime_validation_required": False,
                    "browser_validation_required": False,
                    "browser_screenshot_required": False,
                    "visual_contract_required": False,
                    "visual_review_required": False,
                    "candidate_skills": ["design-craft"],
                    "evidence_contract": {
                        "delivery_state": "measurement_only",
                        "measurement_is_visual_acceptance": False,
                        "global_pixel_pass_threshold": None,
                    },
                },
                "",
            ),
        ]

        results.append((0, {
            **results[4][1],
            "route_status": "warning",
            "delegation_authorization_missing": True,
        }, ""))
        probes, issues = _validate_route_probes(results)

        self.assertEqual(issues, [])
        self.assertTrue(all(probe["ok"] for probe in probes))

        # An allow decision must never hide delegation or a real route error.
        for index in (4, 6):
            original = results[index]
            for field, invalid in (
                ("delegation_authorized", True),
                ("planned_execution_mode", "main_orchestrated"),
                ("actual_subagent_state", "started"),
                ("subagent_required", True),
                ("runtime_auto_delegation_risk", True),
                ("runtime_profile_verified", False),
                ("gate_decision", "deny"),
                ("route_status", "error"),
                ("route_error_code", "RUNTIME_PROFILE_CONFLICT"),
                ("delegation_authorization_missing", index != 6),
            ):
                with self.subTest(index=index, field=field):
                    results[index] = (0, {**original[1], field: invalid}, "")
                    self.assertTrue(_validate_route_probes(results)[1])
            results[index] = (2, original[1], "preflight failed")
            self.assertTrue(_validate_route_probes(results)[1])
            results[index] = (0, {}, "")
            self.assertTrue(_validate_route_probes(results)[1])
            results[index] = original

        legacy_local = browser_payload()
        legacy_local["preferred_browser_tool"] = "in_app_browser"
        legacy_local["preferred_runtime_tool"] = "in_app_browser"
        legacy_local["actual_browser_lifecycle_state"] = {
            "state": "not_applicable",
            "finalize_result": "not_applicable",
            "delivery_summary_observed": False,
        }
        results[1] = (0, legacy_local, "")

        probes, issues = _validate_route_probes(results)

        local_probe = next(
            probe for probe in probes if probe["name"] == "browser_context_local"
        )
        self.assertFalse(local_probe["ok"])
        self.assertTrue(
            any("expected browser/runtime tool tmwd_browser" in issue for issue in issues)
        )


if __name__ == "__main__":
    unittest.main()
