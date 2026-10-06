from __future__ import annotations

import json
import subprocess
import tomllib
from concurrent.futures import Future
from dataclasses import dataclass

from .probes import runtime_profiles
from .runtime_batch import RouteProbeRequest, RuntimeProbeBatch
from .semantic_contract import SemanticPaths
from .semantic_static import load_toml


@dataclass(frozen=True)
class RuntimeValidation:
    issues: list[str]
    warnings: list[str]
    probes: list[dict]
    profiles: list[dict[str, str]]
    model_catalog_source: str


def route_probe_requests() -> list[RouteProbeRequest]:
    probe_base = [
        "--surface",
        "dashboard",
        "--intent",
        "functional",
        "--scope",
        "component",
        "--visual-contract",
        "not-applicable",
        "--output",
        "json",
    ]
    compact_arguments = [
        *probe_base[:-1],
        "compact-json",
        "--browser-context",
        "local",
    ]
    evidence_arguments = [
        "--surface",
        "landing",
        "--intent",
        "reference-only",
        "--scope",
        "page",
        "--has-reference-image",
        "1",
        "--evidence-mode",
        "comp-fidelity",
        "--output",
        "json",
    ]
    return [
        ([*probe_base, "--browser-context", "external"], None, None),
        ([*probe_base, "--browser-context", "local"], None, None),
        ([*probe_base, "--browser-context", "local"], "gpt-5.6-sol", "max"),
        (compact_arguments, "gpt-5.6-sol", "max"),
        ([*probe_base, "--browser-context", "local"], "gpt-5.6-sol", "ultra"),
        (evidence_arguments, "gpt-5.6-sol", "max"),
        (
            [*probe_base, "--browser-context", "local",
             "--orchestration", "parallel", "--delegation-authorization", "none"],
            "gpt-5.6-sol", "ultra",
        ),
    ]


def validate_schema_probe(batch: RuntimeProbeBatch) -> list[str]:
    try:
        completed = batch.schema.result()
        payload = json.loads(completed.stdout)
        if completed.returncode == 0 and payload.get("ok") is True:
            return []
        schema_errors = payload.get("errors")
        detail = (
            "; ".join(schema_errors)
            if isinstance(schema_errors, list)
            else completed.stderr.strip()
        )
        return [
            f"frontend routing JSON Schema validation failed: {detail[:500]}"
        ]
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return [f"failed to run frontend routing JSON Schema validation: {exc}"]


def _completed_contract_probe(
    future: Future[subprocess.CompletedProcess[str]],
    *,
    name: str,
    failure_prefix: str,
) -> tuple[dict, str | None]:
    try:
        completed = future.result()
        ok = completed.returncode == 0
        detail = (completed.stderr or completed.stdout).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        ok = False
        detail = str(exc)
    probe = {"name": name, "ok": ok}
    return probe, None if ok else f"{failure_prefix}: {detail[:240]}"


def _validate_route_probes(
    probe_results: list[tuple[int, dict, str]],
) -> tuple[list[dict], list[str]]:
    probes: list[dict] = []
    issues: list[str] = []
    for (browser_context, expected_tool), (
        returncode,
        payload,
        detail,
    ) in zip(
        [
            ("external", "tmwd_browser"),
            ("local", "tmwd_browser"),
        ],
        probe_results[:2],
    ):
        expected_lifecycle_state = (
            "not_started" if expected_tool == "tmwd_browser" else "not_applicable"
        )
        actual_lifecycle = payload.get("actual_browser_lifecycle_state")
        probe_ok = (
            returncode == 0
            and payload.get("preferred_browser_tool") == expected_tool
            and payload.get("preferred_runtime_tool") == expected_tool
            and payload.get("planned_browser_lifecycle")
            == payload.get("browser_lifecycle")
            and isinstance(actual_lifecycle, dict)
            and actual_lifecycle.get("state") == expected_lifecycle_state
            and actual_lifecycle.get("finalize_result")
            == expected_lifecycle_state
            and actual_lifecycle.get("delivery_summary_observed") is False
            and payload.get("style_authority_applicability") == "not_applicable"
            and payload.get("visual_contract_required") is False
        )
        probes.append(
            {
                "name": f"browser_context_{browser_context}",
                "ok": probe_ok,
                "returncode": returncode,
                "preferred_browser_tool": payload.get("preferred_browser_tool"),
                "preferred_runtime_tool": payload.get("preferred_runtime_tool"),
                "actual_browser_lifecycle_state": (
                    actual_lifecycle.get("state")
                    if isinstance(actual_lifecycle, dict)
                    else None
                ),
            }
        )
        if not probe_ok:
            issues.append(
                f"browser context {browser_context} route probe failed: "
                f"expected browser/runtime tool {expected_tool}; {detail[:240]}"
            )

    returncode, payload, detail = probe_results[2]
    runtime_evidence = payload.get("runtime_profile_evidence")
    runtime_truth_probe_ok = (
        returncode == 0
        and payload.get("runtime_profile_source") == "environment"
        and payload.get("runtime_profile_verified") is True
        and payload.get("effective_model") == "gpt-5.6-sol"
        and payload.get("effective_reasoning") == "max"
        and payload.get("reasoning_application_status") == "runtime_verified"
        and isinstance(runtime_evidence, dict)
        and runtime_evidence.get("kind") == "explicit_environment"
        and runtime_evidence.get("contains_prompt_data") is False
    )
    probes.append(
        {
            "name": "verified_environment_runtime_profile",
            "ok": runtime_truth_probe_ok,
            "returncode": returncode,
            "runtime_profile_source": payload.get("runtime_profile_source"),
            "runtime_profile_verified": payload.get("runtime_profile_verified"),
            "effective_model": payload.get("effective_model"),
            "effective_reasoning": payload.get("effective_reasoning"),
        }
    )
    if not runtime_truth_probe_ok:
        issues.append(
            f"verified environment runtime-profile probe failed: {detail[:240]}"
        )

    returncode, payload, detail = probe_results[3]
    compact_probe_ok = (
        returncode == 0
        and payload.get("schema") == "frontend-route.compact.v1"
        and "delivery_contract" not in payload
        and payload.get("route", {}).get("frontend_tier") == "L1-F"
        and payload.get("runtime_profile", {}).get("verified") is True
        and payload.get("validation", {}).get("preflight_code") == "OK"
        and payload.get("planned_browser_lifecycle")
        == payload.get("browser_lifecycle")
        and payload.get("actual_browser_lifecycle_state", {}).get("state")
        == "not_started"
        and payload.get("actual_browser_lifecycle_state", {}).get(
            "finalize_result"
        )
        == "not_started"
    )
    probes.append(
        {
            "name": "compact_route_output",
            "ok": compact_probe_ok,
            "returncode": returncode,
            "schema": payload.get("schema"),
        }
    )
    if not compact_probe_ok:
        issues.append(f"compact route output probe failed: {detail[:240]}")

    # Allowing a main-owned route is not authorization to spawn an agent.
    for index, name, expected_status, authorization_missing in (
        (4, "ultra_main_serial", "ok", False),
        (6, "unauthorized_parallel_main_serial", "warning", True),
    ):
        returncode, payload, detail = probe_results[index]
        probe_ok = (
            returncode == 0
            and payload.get("route_status") == expected_status
            and payload.get("route_error_code") == ""
            and payload.get("gate_decision") == "allow"
            and payload.get("runtime_profile_verified") is True
            and payload.get("effective_model") == "gpt-5.6-sol"
            and payload.get("effective_reasoning") == "ultra"
            and payload.get("delegation_authorized") is False
            and payload.get("delegation_authorization_missing") is authorization_missing
            and payload.get("planned_execution_mode") == "main_serial"
            and payload.get("actual_subagent_state") == "not_started"
            and payload.get("subagent_required") is False
            and payload.get("runtime_auto_delegation_risk") is False
        )
        probes.append({
            "name": name,
            "ok": probe_ok,
            "returncode": returncode,
            "route_error_code": payload.get("route_error_code"),
            "gate_decision": payload.get("gate_decision"),
            "planned_execution_mode": payload.get("planned_execution_mode"),
            "actual_subagent_state": payload.get("actual_subagent_state"),
            "delegation_authorized": payload.get("delegation_authorized"),
        })
        if not probe_ok:
            issues.append(f"{name} route probe failed: {detail[:240]}")

    returncode, payload, detail = probe_results[5]
    evidence_contract = payload.get("evidence_contract")
    evidence_probe_ok = (
        returncode == 0
        and payload.get("evidence_mode") == "comp-fidelity"
        and payload.get("runtime_validation_required") is False
        and payload.get("browser_validation_required") is False
        and payload.get("browser_screenshot_required") is False
        and payload.get("visual_contract_required") is False
        and payload.get("visual_review_required") is False
        and payload.get("candidate_skills") == ["design-craft"]
        and isinstance(evidence_contract, dict)
        and evidence_contract.get("delivery_state") == "measurement_only"
        and evidence_contract.get("measurement_is_visual_acceptance") is False
        and evidence_contract.get("global_pixel_pass_threshold") is None
    )
    probes.append(
        {
            "name": "comp_fidelity_evidence_mode",
            "ok": evidence_probe_ok,
            "returncode": returncode,
            "evidence_mode": payload.get("evidence_mode"),
            "runtime_validation_required": payload.get(
                "runtime_validation_required"
            ),
        }
    )
    if not evidence_probe_ok:
        issues.append(f"comp-fidelity evidence route probe failed: {detail[:240]}")
    return probes, issues


def _validate_model_profiles(
    paths: SemanticPaths,
    batch: RuntimeProbeBatch,
) -> tuple[list[dict[str, str]], list[str], list[str], str]:
    profiles: list[dict[str, str]] = []
    issues: list[str] = []
    warnings: list[str] = []
    model_catalog_source = "not-run"
    if paths.config.is_file():
        try:
            config = load_toml(paths.config)
            profiles = runtime_profiles(config)
            worker = load_toml(paths.worker_agent)
            worker_model = worker.get("model")
            if isinstance(worker_model, str) and worker_model.strip():
                profiles.append({
                    "role": "worker.toml",
                    "model": worker_model.strip(),
                    "reasoning": str(worker.get("model_reasoning_effort", "")).strip(),
                })
            catalog, catalog_warning = batch.model_catalog.result()
            if catalog_warning:
                warnings.append(catalog_warning)
            if catalog:
                model_catalog_source = "codex debug models --bundled"
                for profile in profiles:
                    model = catalog.get(profile["model"])
                    if not model:
                        issues.append(
                            f"runtime profile {profile['role']} references "
                            f"unknown model {profile['model']}"
                        )
                        continue
                    reasoning = profile["reasoning"]
                    if reasoning:
                        supported = {
                            str(item.get("effort", ""))
                            for item in model.get(
                                "supported_reasoning_levels", []
                            )
                            if isinstance(item, dict)
                        }
                        if reasoning not in supported:
                            issues.append(
                                f"runtime profile {profile['role']} uses "
                                f"unsupported reasoning {reasoning} for "
                                f"{profile['model']}"
                            )
        except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
            issues.append(f"failed to validate config.toml model profiles: {exc}")
    else:
        warnings.append(
            "config.toml not present in route pack source; runtime profiles "
            "were not checked"
        )
    return profiles, issues, warnings, model_catalog_source


def runtime_validation(
    paths: SemanticPaths,
    batch: RuntimeProbeBatch,
) -> RuntimeValidation:
    issues: list[str] = []
    probes: list[dict] = []
    for future, name, failure_prefix in (
        (
            batch.telemetry,
            "route_telemetry_self_check",
            "frontend route telemetry self-check failed",
        ),
        (
            batch.browser_capture,
            "browser_lifecycle_capture_contract_tests",
            "frontend browser lifecycle capture tests failed",
        ),
        (
            batch.browser_receipt,
            "browser_lifecycle_receipt_contract_tests",
            "frontend browser lifecycle receipt contract tests failed",
        ),
    ):
        probe, issue = _completed_contract_probe(
            future,
            name=name,
            failure_prefix=failure_prefix,
        )
        probes.append(probe)
        if issue:
            issues.append(issue)

    route_probes, route_issues = _validate_route_probes(
        [future.result() for future in batch.routes]
    )
    probes.extend(route_probes)
    issues.extend(route_issues)
    profiles, profile_issues, warnings, model_catalog_source = (
        _validate_model_profiles(paths, batch)
    )
    issues.extend(profile_issues)
    return RuntimeValidation(
        issues=issues,
        warnings=warnings,
        probes=probes,
        profiles=profiles,
        model_catalog_source=model_catalog_source,
    )
