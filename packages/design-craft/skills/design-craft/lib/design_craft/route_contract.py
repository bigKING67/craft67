"""Pure route policy and rendering for the portable design-craft runtime."""

from __future__ import annotations

import json
from pathlib import Path


VISUAL_INTENTS = frozenset(
    {
        "visual-refine",
        "redesign",
        "new-page",
        "high-motion",
        "brand",
        "mobile-flow",
        "reference-only",
    }
)
LARGE_SCOPE_INTENTS = frozenset(
    {"redesign", "new-page", "brand", "mobile-flow", "high-motion"}
)
DEVELOPER_PRODUCT_SURFACES = frozenset(
    {"auto", "dashboard", "app", "admin", "data-app"}
)
NON_SEED_INTENTS = frozenset(
    {"brand", "high-motion", "mobile-flow", "reference-only"}
)
EVIDENCE_MODES = frozenset(
    {"auto", "none", "comp-fidelity", "sealed-rendition"}
)


def resolve_evidence_mode(requested: str) -> str:
    mode = requested.strip().lower() or "auto"
    if mode not in EVIDENCE_MODES:
        raise ValueError(f"unsupported evidence mode: {requested}")
    return "none" if mode == "auto" else mode


def validate_evidence_request(
    *, requested: str, platform: str, has_reference: bool
) -> str:
    mode = resolve_evidence_mode(requested)
    if mode != "none" and not has_reference:
        raise ValueError(f"evidence mode {mode} requires --has-reference-image 1")
    if mode == "sealed-rendition" and platform != "web":
        raise ValueError("sealed-rendition evidence currently supports platform=web")
    return mode


def evidence_workflow_contract(requested: str) -> dict[str, object]:
    mode = resolve_evidence_mode(requested)
    required = mode != "none"
    if mode == "comp-fidelity":
        contract = "design-craft.comp-fidelity-report.v1"
        capture_plan_required = False
        runtime_owner = "existing_capture_path"
        delivery_state = "measurement_only"
    elif mode == "sealed-rendition":
        contract = "design-craft.sealed-rendition-gate-report.v1"
        capture_plan_required = True
        runtime_owner = "sealed_capture_plan"
        delivery_state = "explicit_visual_decision"
    else:
        contract = "not_applicable"
        capture_plan_required = False
        runtime_owner = "not_applicable"
        delivery_state = "not_applicable"
    return {
        "required": required,
        "mode": mode,
        "contract": contract,
        "reference": "references/comp-fidelity.md" if required else "",
        "capture_plan_required": capture_plan_required,
        "capture_runtime_owner": runtime_owner,
        "comparison_is_measurement_only": required,
        "measurement_is_visual_acceptance": False,
        "human_visual_decision_required_for_pass": required,
        "global_pixel_pass_threshold": None,
        "delivery_state": delivery_state,
    }


def load_route_payload(path: Path) -> dict[str, object]:
    try:
        return parse_route_payload(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def parse_route_payload(raw: str) -> dict[str, object]:
    payload = json.loads(raw)
    return payload if isinstance(payload, dict) else {}


def fallback_tier(
    *,
    intent: str,
    scope: str,
    style: str,
    design_authority_mode: str,
    has_reference: bool,
    needs_reference: bool,
    evidence_mode: str = "none",
) -> str:
    resolved_evidence_mode = resolve_evidence_mode(evidence_mode)
    visual = (
        intent in VISUAL_INTENTS
        or has_reference
        or needs_reference
        or resolved_evidence_mode != "none"
    )
    large_scope = scope in {"page", "multi-page"} or intent in LARGE_SCOPE_INTENTS
    micro_visual_safe = (
        scope == "micro"
        and intent in {"auto", "functional", "visual-refine"}
        and not has_reference
        and not needs_reference
        and resolved_evidence_mode == "none"
        and style in {"auto", "none"}
        and design_authority_mode != "evolve"
    )
    if micro_visual_safe:
        return "L0"
    if not visual and intent in {"auto", "functional"}:
        return "L1-F"
    if large_scope:
        return "L2"
    return "L1-V"


def portable_fallback_payload(
    *,
    tier: str,
    platform: str,
    surface: str,
    intent: str,
    scope: str,
    style: str,
    style_authority_path: str,
    design_authority_mode: str,
    existing_project: bool,
    has_reference: bool,
    needs_reference: bool,
    style_authority_source: str = "none",
    style_authority_reason: str = "",
    evidence_mode: str = "none",
) -> dict[str, object]:
    resolved_evidence_mode = validate_evidence_request(
        requested=evidence_mode,
        platform=platform,
        has_reference=has_reference,
    )
    evidence_contract = evidence_workflow_contract(resolved_evidence_mode)
    implementation_expected = intent != "reference-only"
    sealed_capture_required = resolved_evidence_mode == "sealed-rendition"
    measurement_only_route = (
        resolved_evidence_mode == "comp-fidelity" and not implementation_expected
    )
    execution_required = implementation_expected or sealed_capture_required
    authority_required = tier != "L0" and execution_required
    authority_ok = bool(style_authority_path) or not authority_required
    visual = (
        intent in VISUAL_INTENTS
        or has_reference
        or needs_reference
        or resolved_evidence_mode != "none"
    )
    browser_required = platform == "web" and tier != "L0" and execution_required
    screenshot_required = (
        platform == "web"
        and execution_required
        and (
            sealed_capture_required
            or tier == "L2"
            or has_reference
            or needs_reference
            or intent in LARGE_SCOPE_INTENTS
            or (visual and scope in {"section", "page", "multi-page"})
        )
    )
    return {
        "ok": authority_ok,
        "frontend_tier": tier,
        "design_tier": tier,
        "candidate_skills": ["design-craft"],
        "skills": ["design-craft"],
        "execution_mode": "main_serial",
        "subagent_required": False,
        "subagent_recommended": False,
        "style_authority_path": style_authority_path,
        "style_authority_source": style_authority_source,
        "style_authority_reason": style_authority_reason,
        "style_authority_mode": (
            "evolve" if design_authority_mode == "evolve" else "enforce"
        ),
        "style_authority_applicability": (
            "not_applicable"
            if measurement_only_route
            else "required"
            if authority_required
            else "not_applicable"
        ),
        "visual_contract_required": authority_required,
        "preflight_status": "pass" if authority_ok else "fail",
        "preflight_code": "OK" if authority_ok else "STYLE_AUTHORITY_MISSING",
        "gate_decision": "allow" if authority_ok else "deny",
        "browser_validation_required": browser_required,
        "preferred_browser_tool": "tmwd_browser",
        "browser_screenshot_required": screenshot_required,
        "screenshot_evidence_level": "required" if screenshot_required else "none",
        "screenshot_required_reason": (
            "portable fallback visual-risk policy"
            if screenshot_required
            else "not required by portable fallback"
        ),
        "preferred_screenshot_tool": "tmwd_browser.browser_screenshot_ops",
        "evidence_mode": resolved_evidence_mode,
        "evidence_contract": evidence_contract,
        "directory_governance_required": tier != "L0" and implementation_expected,
        "performance_review_required": (
            tier in {"L1-V", "L2"} and implementation_expected
        ),
        "quality_tradeoff": (
            "Global Codex route planner unavailable; conservative portable fallback used."
        ),
        "inputs": {
            "surface": surface,
            "intent": intent,
            "scope": scope,
            "style": style,
            "existing_project": existing_project,
            "evidence_mode": resolved_evidence_mode,
        },
    }


def seed_applicability(
    *,
    route_payload: dict[str, object],
    platform: str,
    surface: str,
    intent: str,
    existing_project: bool,
    evidence_mode: str = "none",
) -> tuple[bool, str]:
    has_style_authority = bool(route_payload.get("style_authority_path"))
    applicable = (
        platform == "web"
        and not has_style_authority
        and surface in DEVELOPER_PRODUCT_SURFACES
        and intent not in NON_SEED_INTENTS
        and resolve_evidence_mode(evidence_mode) == "none"
    )
    if applicable:
        reason = (
            "existing developer-product surface has no resolved style authority; "
            "use the original developer-product seed only if runtime/project style is weak"
            if existing_project
            else "new developer-product surface has no resolved style authority"
        )
    elif platform != "web":
        reason = "native/adaptive platforms require platform-specific design authority"
    elif has_style_authority:
        reason = "stronger style authority was resolved"
    elif surface not in DEVELOPER_PRODUCT_SURFACES:
        reason = "surface is not a default developer-product seed case"
    else:
        reason = "intent or evidence workflow calls for another authority path"
    return applicable, reason


def build_route_payload(
    *,
    route_payload: dict[str, object],
    platform_payload: dict[str, object],
    route_source: str,
    surface: str,
    intent: str,
    scope: str,
    style: str,
    style_authority_path: str,
    design_authority_mode: str,
    existing_project: bool,
    has_reference: bool,
    needs_reference: bool,
    style_authority_source: str = "none",
    style_authority_reason: str = "",
    evidence_mode: str = "auto",
) -> dict[str, object]:
    resolved_evidence_mode = validate_evidence_request(
        requested=evidence_mode,
        platform=str(platform_payload["platform"]),
        has_reference=has_reference,
    )
    effective_style_authority_source = style_authority_source
    if style_authority_path and style_authority_source == "none":
        effective_style_authority_source = "explicit_or_discovered"
    resolved_fallback_tier = fallback_tier(
        intent=intent,
        scope=scope,
        style=style,
        design_authority_mode=design_authority_mode,
        has_reference=has_reference,
        needs_reference=needs_reference,
        evidence_mode=resolved_evidence_mode,
    )
    platform = str(platform_payload["platform"])
    native = bool(platform_payload["native_validation_required"])

    if route_source == "portable_fallback":
        route_payload = portable_fallback_payload(
            tier=resolved_fallback_tier,
            platform=platform,
            surface=surface,
            intent=intent,
            scope=scope,
            style=style,
            style_authority_path=style_authority_path,
            design_authority_mode=design_authority_mode,
            existing_project=existing_project,
            has_reference=has_reference,
            needs_reference=needs_reference,
            style_authority_source=effective_style_authority_source,
            style_authority_reason=style_authority_reason,
            evidence_mode=resolved_evidence_mode,
        )

    tier = route_payload.get("frontend_tier") or resolved_fallback_tier
    implementation_expected = intent != "reference-only"
    runtime_required = (
        tier != "L0"
        and (
            implementation_expected
            or resolved_evidence_mode == "sealed-rendition"
        )
    )
    evidence_contract = evidence_workflow_contract(resolved_evidence_mode)
    route_payload.update(
        {
            "design_tier": tier,
            "frontend_tier": tier,
            "route_source": route_source,
            "degraded": route_source == "portable_fallback"
            or bool(route_payload.get("degraded", False)),
            "platform": platform,
            "platform_source": platform_payload["platform_source"],
            "platform_confidence": platform_payload["platform_confidence"],
            "platform_signals": platform_payload.get("signals", []),
            "platform_contradictions": platform_payload.get("contradictions", []),
            "product_context_path": platform_payload.get("product_context_path", ""),
            "product_context_path_source": platform_payload.get("product_context_path_source", "none"),
            "product_context_path_reason": platform_payload.get("product_context_path_reason", ""),
            "style_authority_path": style_authority_path,
            "style_authority_source": effective_style_authority_source,
            "style_authority_reason": style_authority_reason,
            "runtime_validation_required": runtime_required,
            "runtime_validation_kind": platform_payload["runtime_validation_kind"],
            "native_validation_required": native and runtime_required,
            "preferred_runtime_tool": platform_payload["preferred_runtime_tool"],
            "evidence_mode": resolved_evidence_mode,
            "evidence_contract": evidence_contract,
        }
    )
    inputs = route_payload.setdefault("inputs", {})
    if not isinstance(inputs, dict):
        inputs = {}
        route_payload["inputs"] = inputs
    inputs.update(
        {
            "platform": platform,
            "requested_platform": (
                platform_payload.get("platform")
                if platform_payload.get("platform_source") == "explicit"
                else "auto"
            ),
            "product_context_path": platform_payload.get("product_context_path", ""),
            "has_reference_image": has_reference,
            "needs_generated_reference": needs_reference,
            "evidence_mode": resolved_evidence_mode,
        }
    )

    seed_applicable, seed_reason = seed_applicability(
        route_payload=route_payload,
        platform=platform,
        surface=surface,
        intent=intent,
        existing_project=existing_project,
        evidence_mode=resolved_evidence_mode,
    )
    triggers = reference_workflow_triggers(
        intent=intent,
        has_reference=has_reference,
        needs_reference=needs_reference,
    )
    platform_signals = platform_payload.get("signals", [])
    react_native_expo = platform != "web" and isinstance(platform_signals, list) and any(
        signal == "React Native/Expo dependency" for signal in platform_signals
    )
    references = recommended_references(
        platform=platform,
        intent=intent,
        style=style,
        surface=surface,
        developer_product_seed_applicable=seed_applicable,
        has_reference=has_reference,
        needs_reference=needs_reference,
        react_native_expo=react_native_expo,
        evidence_mode=resolved_evidence_mode,
    )
    conditional = route_payload.get("design_craft_conditional_references", [])
    allowed_conditional = {
        "references/image-reference-implementation.md",
        "references/web-image-direction.md",
        "references/visual-judgment.md",
        "references/motion-quality.md",
    }
    if isinstance(conditional, list):
        references = sorted(set(references) | {
            reference for reference in conditional
            if isinstance(reference, str) and reference in allowed_conditional
        })
    route_payload.update(
        {
            "developer_product_seed_applicable": seed_applicable,
            "developer_product_seed_reason": seed_reason,
            # Compatibility fields for existing route consumers.
            "vercel_geist_seed_applicable": seed_applicable,
            "vercel_geist_seed_reason": seed_reason,
            "reference_workflow": {
                "required": bool(triggers),
                "triggers": triggers,
                "contract": reference_workflow_contract(
                    platform=platform, surface=surface, intent=intent,
                    has_reference=has_reference, needs_reference=needs_reference,
                    evidence_mode=resolved_evidence_mode,
                ),
            },
            "evidence_workflow": evidence_contract,
            "react_native_expo_motion_applicable": react_native_expo,
            "recommended_design_craft_references": references,
        }
    )
    return route_payload


def reference_workflow_triggers(
    *, intent: str, has_reference: bool, needs_reference: bool
) -> list[str]:
    triggers: list[str] = []
    if intent == "reference-only":
        triggers.append("reference-only")
    if has_reference:
        triggers.append("has-reference-image")
    if needs_reference:
        triggers.append("needs-generated-reference")
    return triggers


def reference_workflow_contract(
    *, platform: str, surface: str, intent: str,
    has_reference: bool, needs_reference: bool, evidence_mode: str,
) -> str:
    if resolve_evidence_mode(evidence_mode) != "none":
        return "references/comp-fidelity.md"
    if needs_reference and platform == "web" and surface not in {"mobile", "brand"} and intent not in {
        "mobile-flow", "brand"
    }:
        return "references/web-image-direction.md"
    if has_reference and intent != "reference-only":
        return "references/image-reference-implementation.md"
    return "references/reference-workflow.md"


def recommended_references(
    *,
    platform: str,
    intent: str,
    developer_product_seed_applicable: bool,
    has_reference: bool = False,
    needs_reference: bool = False,
    react_native_expo: bool = False,
    evidence_mode: str = "none",
    style: str = "auto",
    surface: str = "auto",
) -> list[str]:
    references = {"references/validation-contract.md", "references/product-context.md"}
    if platform == "ios":
        references.add("references/ios-quality.md")
    elif platform == "android":
        references.add("references/android-quality.md")
    elif platform == "adaptive":
        references.update(
            {
                "references/ios-quality.md",
                "references/android-quality.md",
                "references/adaptive-quality.md",
            }
        )
    if intent == "high-motion" or platform != "web":
        references.add("references/interaction-physics.md")
    if react_native_expo and platform != "web":
        references.add("references/react-native-expo-motion.md")
    if developer_product_seed_applicable:
        references.update(
            {
                "templates/developer-product/design.md",
                "templates/developer-product/design.dark.md",
            }
        )
    if reference_workflow_triggers(intent=intent, has_reference=has_reference, needs_reference=needs_reference):
        references.add(reference_workflow_contract(
            platform=platform, surface=surface, intent=intent,
            has_reference=has_reference, needs_reference=needs_reference,
            evidence_mode=evidence_mode,
        ))
    if platform == "web":
        if needs_reference and surface not in {"mobile", "brand"} and intent not in {
            "mobile-flow", "brand"
        }:
            references.add("references/web-image-direction.md")
        if (has_reference or needs_reference) and intent != "reference-only" and evidence_mode == "none":
            references.add("references/image-reference-implementation.md")
        if style in {"high-end", "gpt-taste"} or intent in {"high-motion", "brand"}:
            references.add("references/visual-judgment.md")
        if style == "gpt-taste" or intent == "high-motion":
            references.add("references/motion-quality.md")
    if resolve_evidence_mode(evidence_mode) != "none":
        references.add("references/comp-fidelity.md")
    return sorted(references)


def print_route_payload(
    route_payload: dict[str, object], *, intent: str, json_only: bool
) -> None:
    if json_only:
        print(json.dumps(route_payload, ensure_ascii=False, indent=2, sort_keys=True))
        return

    print("design-craft route summary:")
    for key in [
        "ok",
        "frontend_tier",
        "design_tier",
        "platform",
        "platform_source",
        "platform_confidence",
        "product_context_path",
        "route_source",
        "degraded",
        "candidate_skills",
        "execution_mode",
        "subagent_required",
        "style_authority_path",
        "preflight_status",
        "preflight_code",
        "runtime_validation_required",
        "runtime_validation_kind",
        "native_validation_required",
        "preferred_runtime_tool",
        "browser_validation_required",
        "browser_screenshot_required",
        "evidence_mode",
        "evidence_workflow",
        "developer_product_seed_applicable",
        "developer_product_seed_reason",
        "reference_workflow",
    ]:
        print(f"- {key}: {route_payload.get(key)}")
    print("- recommended_design_craft_references:")
    references = route_payload.get("recommended_design_craft_references", [])
    if not isinstance(references, list):
        references = []
    for reference in references:
        print(f"  - {reference}")
    print("\nraw_json:")
    print(json.dumps(route_payload, ensure_ascii=False, indent=2, sort_keys=True))
