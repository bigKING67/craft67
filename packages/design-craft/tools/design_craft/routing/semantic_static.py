from __future__ import annotations

import json
import tomllib
from pathlib import Path

from .manifest import load_json
from .semantic_contract import (
    EXPLICIT_REASONING_VOCABULARY,
    REQUIRED_FRAGMENTS,
    STALE_FRAGMENTS,
    SemanticPaths,
)


def load_toml(path: Path) -> dict:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected TOML table: {path}")
    return payload


def validate_routing_config(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        routing = load_json(path)
        if routing.get("version") != 2:
            issues.append("frontend_agent_routing.json must use version 2")
        if routing.get("policy_name") != "frontend-route-v2":
            issues.append(
                "frontend_agent_routing.json missing frontend-route-v2 policy name"
            )
        tier_defaults = routing.get("tier_defaults")
        if not isinstance(tier_defaults, dict):
            issues.append("frontend_agent_routing.json missing tier_defaults")
        else:
            for tier in ["L0", "L1-F", "L1-V", "L2"]:
                route = tier_defaults.get(tier)
                if not isinstance(route, dict):
                    issues.append(f"missing tier route: {tier}")
                    continue
                if route.get("agent_route") != "main_inherit":
                    issues.append(f"{tier} must use agent_route=main_inherit")
                if route.get("agent_model") != "inherit":
                    issues.append(f"{tier} must inherit the runtime model")
                if route.get("execution_mode") != "main_serial":
                    issues.append(
                        f"{tier} default execution_mode must be main_serial"
                    )
                if route.get("subagent_required") is not False:
                    issues.append(f"{tier} must not require a subagent by tier")
        delegation = routing.get("delegation_contract")
        if not isinstance(delegation, dict):
            issues.append("frontend_agent_routing.json missing delegation_contract")
        else:
            if delegation.get("minimum_independent_subtasks") != 2:
                issues.append(
                    "delegation requires exactly the documented minimum of two "
                    "independent subtasks"
                )
            if delegation.get("fallback_when_unavailable") != "continue_main_and_report":
                issues.append(
                    "delegation fallback must continue with the main agent"
                )
        quality_governance = routing.get("quality_governance", {})
        evidence_validation = quality_governance.get("evidence_validation")
        if not isinstance(evidence_validation, dict):
            issues.append(
                "frontend_agent_routing.json missing "
                "quality_governance.evidence_validation"
            )
        else:
            if evidence_validation.get("default_mode") != "none":
                issues.append("frontend evidence default mode must remain none")
            if evidence_validation.get("supported_modes") != [
                "none",
                "comp-fidelity",
                "sealed-rendition",
            ]:
                issues.append("frontend evidence modes must preserve the reviewed order")
            if evidence_validation.get("measurement_is_visual_acceptance") is not False:
                issues.append("frontend evidence measurements must not imply visual acceptance")
            if evidence_validation.get("global_pixel_pass_threshold") is not None:
                issues.append("frontend evidence policy must not define a global pixel PASS threshold")
        platform_validation = quality_governance.get("platform_validation")
        if not isinstance(platform_validation, dict):
            issues.append(
                "frontend_agent_routing.json missing "
                "quality_governance.platform_validation"
            )
        else:
            if platform_validation.get("surface_mobile_is_native_signal") is not False:
                issues.append("surface=mobile must not be a native platform signal")
            if platform_validation.get("static_scan_is_runtime_proof") is not False:
                issues.append("static native scans must not be runtime proof")
        risk_governance = quality_governance.get("risk_governance", {})
        if risk_governance.get("architecture_review_required_intents") != [
            "redesign",
            "new-page",
        ]:
            issues.append(
                "architecture review intent triggers must be declared in routing config"
            )
        if quality_governance.get("performance_review_required_for_surfaces") != [
            "dashboard",
            "app",
        ]:
            issues.append(
                "performance review surface triggers must be declared in routing config"
            )
        reasoning = routing.get("reasoning_overrides")
        required_reasoning = {
            "inherit",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
            "ultra",
        }
        if not isinstance(reasoning, dict) or not required_reasoning.issubset(reasoning):
            issues.append(
                "routing reasoning vocabulary must cover "
                "inherit/low/medium/high/xhigh/max/ultra"
            )
        elif not isinstance(reasoning.get("ultra"), dict):
            issues.append("routing ultra reasoning policy must be an object")
        else:
            ultra = reasoning["ultra"]
            if ultra.get("explicit_override_allowed") is not False:
                issues.append(
                    "ultra must remain runtime-profile-only for controlled "
                    "frontend delegation"
                )
            if ultra.get("runtime_auto_delegation") is not False:
                issues.append(
                    "ultra reasoning alone must not imply automatic delegation"
                )
            if ultra.get("fallback_reasoning_target") != "max":
                issues.append(
                    "ultra must identify max as the explicit main-owned fallback"
                )
        orchestration = routing.get("orchestration_overrides")
        if not isinstance(orchestration, dict) or not {
            "main",
            "parallel",
            "review",
        }.issubset(orchestration):
            issues.append(
                "routing orchestration overrides must cover main/parallel/review"
            )
        if "gpt-5.5" in json.dumps(routing, ensure_ascii=False):
            issues.append("routing config still pins gpt-5.5")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(f"failed to validate routing config: {exc}")
    return issues


def validate_route_modules(paths: SemanticPaths) -> list[str]:
    issues: list[str] = []
    for path in paths.route_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"failed to read {path.name}: {exc}")
            continue
        for fragment in STALE_FRAGMENTS:
            if fragment in text:
                issues.append(
                    f"{path.name} contains stale routing fragment: {fragment}"
                )
        for fragment in REQUIRED_FRAGMENTS.get(path.name, ()):
            if fragment not in text:
                issues.append(
                    f"{path.name} missing V2 routing fragment: {fragment}"
                )

    for path in (paths.route_plan, paths.worker_entry):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if EXPLICIT_REASONING_VOCABULARY not in text:
            issues.append(
                f"{path.name} missing explicit reasoning vocabulary: "
                f"{EXPLICIT_REASONING_VOCABULARY}"
            )
        if EXPLICIT_REASONING_VOCABULARY + "|ultra" in text:
            issues.append(
                f"{path.name} incorrectly exposes ultra as an explicit "
                "frontend override"
            )
    return issues


def validate_platform_detector(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        platform_text = path.read_text(encoding="utf-8")
        for fragment in (
            "design-craft.platform-scan.v1",
            "React Native/Expo dependency",
            "Capacitor/Cordova/WebView shell",
            "product_context",
        ):
            if fragment not in platform_text:
                issues.append(
                    "frontend_platform_detect.py missing platform fragment: "
                    f"{fragment}"
                )
    except OSError as exc:
        issues.append(f"failed to read frontend_platform_detect.py: {exc}")
    return issues


def validate_worker(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        worker = load_toml(path)
        for required in ["name", "description", "developer_instructions"]:
            if not str(worker.get(required, "")).strip():
                issues.append(f"worker.toml missing required field: {required}")
        # Role-specific profiles and inherited profiles are both valid.
        for field in ("model", "model_reasoning_effort"):
            if field in worker and (
                not isinstance(worker[field], str) or not worker[field].strip()
            ):
                issues.append(f"worker.toml {field} must be a non-empty string")
        effort = worker.get("model_reasoning_effort")
        if isinstance(effort, str) and effort not in {
            "low", "medium", "high", "xhigh", "max", "ultra",
        }:
            issues.append("worker.toml has unsupported model_reasoning_effort")
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        issues.append(f"failed to validate worker.toml: {exc}")
    return issues


def static_validation(paths: SemanticPaths) -> list[str]:
    return [
        *validate_routing_config(paths.routing),
        *validate_route_modules(paths),
        *validate_platform_detector(paths.platform_detect),
        *validate_worker(paths.worker_agent),
    ]
