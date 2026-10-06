from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

from .execution import gate_result
from .model import MaturityContext, MaturityGateResult
from .process_runner import json_payload, run_command


RUNTIME_SCRIPTS = {
    "design_craft_audit.sh",
    "design_craft_pass.sh",
    "design_craft_detect.sh",
    "design_craft_route.sh",
    "design_craft_seed_design.sh",
    "design_craft_taste_review.sh",
    "design_craft_browser_evidence.py",
    "design_craft_css_smell_scan.py",
    "design_craft_focus_audit.py",
    "design_craft_token_audit.py",
    "design_craft_static_review.py",
    "design_craft_l4_capture.py",
    "design_craft_l4_evidence_manifest.py",
    "design_craft_l4_eval_case.sh",
    "design_craft_l4_case_validate.py",
    "design_craft_platform_scan.py",
    "design_craft_route_runtime.py",
    "design_craft_comp_fidelity.py",
}


def contract_completeness(context: MaturityContext) -> MaturityGateResult:
    result = run_command(
        [
            sys.executable,
            "scripts/design_craft_score.py",
            "--self",
            "--no-smoke",
            "--json",
        ],
        root=context.root,
    )
    payload = json_payload(result)
    passed = (
        result.returncode == 0
        and payload.get("schema") == "design-craft.source-completeness.v1"
        and payload.get("score") == 100
    )
    return gate_result(
        "contract_completeness",
        passed,
        result.duration_ms,
        {"metric": "source_completeness", "score": payload.get("score")},
        result.stderr or "source completeness must be exactly 100",
    )


def portable_runtime_payload(context: MaturityContext) -> MaturityGateResult:
    started = time.perf_counter()
    root = context.root / "skills/design-craft/scripts"
    missing = sorted(name for name in RUNTIME_SCRIPTS if not (root / name).is_file())
    non_executable = sorted(
        name
        for name in RUNTIME_SCRIPTS
        if (root / name).is_file() and not os.access(root / name, os.X_OK)
    )
    return gate_result(
        "portable_runtime_payload",
        not missing and not non_executable,
        (time.perf_counter() - started) * 1_000,
        {"script_count": len(RUNTIME_SCRIPTS)},
        f"missing={missing}, non_executable={non_executable}",
    )


def portable_route_fallback(context: MaturityContext) -> MaturityGateResult:
    with tempfile.TemporaryDirectory(prefix="design-craft-maturity-route-") as raw:
        target = Path(raw)
        (target / "DESIGN.md").write_text(
            "# Design\n\n## Typography System\nSystem type.\n\n"
            "## Color Palette\nSemantic roles.\n\n"
            "## Motion Language\nReduced motion.\n\n"
            "## Component Grammar\nNative states.\n",
            encoding="utf-8",
        )
        (target / "PRODUCT.md").write_text(
            "# Product\n\n## Platform\nadaptive\n", encoding="utf-8"
        )
        result = run_command(
            [
                "bash",
                "skills/design-craft/scripts/design_craft_route.sh",
                "--target",
                str(target),
                "--surface",
                "mobile",
                "--intent",
                "visual-refine",
                "--scope",
                "component",
                "--json-only",
            ],
            root=context.root,
            environment={
                "DESIGN_CRAFT_ROUTE_PLAN": str(target / "missing-route-plan.sh")
            },
        )
    payload = json_payload(result)
    passed = (
        result.returncode == 0
        and payload.get("route_source") == "portable_fallback"
        and payload.get("degraded") is True
        and payload.get("platform") == "adaptive"
        and payload.get("native_validation_required") is True
    )
    return gate_result(
        "portable_route_fallback",
        passed,
        result.duration_ms,
        {
            "route_source": payload.get("route_source"),
            "platform": payload.get("platform"),
        },
        result.stderr or "portable fallback route contract failed",
    )


def detector_degraded_contract(context: MaturityContext) -> MaturityGateResult:
    with tempfile.TemporaryDirectory(
        prefix="design-craft-maturity-detector-"
    ) as raw:
        result = run_command(
            [
                "bash",
                "skills/design-craft/scripts/design_craft_detect.sh",
                "--target",
                "evals/fixtures/css-smells",
                "--full-json",
            ],
            root=context.root,
            environment={
                "HOME": raw,
                "DESIGN_CRAFT_SOURCE_ROOT": str(Path(raw) / "missing-source"),
                "DESIGN_CRAFT_IMPECCABLE_DETECTOR": str(
                    Path(raw) / "missing-detect.mjs"
                ),
            },
        )
    payload = json_payload(result)
    detector = payload.get("upstream_detector")
    passed = (
        result.returncode == 0
        and payload.get("degraded") is True
        and isinstance(detector, dict)
        and detector.get("status") == "unavailable"
    )
    return gate_result(
        "detector_degraded_contract",
        passed,
        result.duration_ms,
        {"degraded": payload.get("degraded")},
        result.stderr
        or "unavailable detector did not fail open with explicit degraded status",
    )


def platform_fixtures(context: MaturityContext) -> MaturityGateResult:
    started = time.perf_counter()
    failures: list[str] = []
    scanner = "skills/design-craft/scripts/design_craft_platform_scan.py"
    for platform in ("ios", "android", "adaptive"):
        valid = run_command(
            [
                sys.executable,
                scanner,
                "--target",
                f"evals/fixtures/platforms/{platform}/valid",
                "--json",
                "--strict",
            ],
            root=context.root,
        )
        invalid = run_command(
            [
                sys.executable,
                scanner,
                "--target",
                f"evals/fixtures/platforms/{platform}/invalid",
                "--json",
                "--strict",
            ],
            root=context.root,
        )
        if valid.returncode != 0:
            failures.append(f"{platform}: valid fixture failed")
        if invalid.returncode == 0:
            failures.append(f"{platform}: invalid fixture passed")
    return gate_result(
        "platform_fixtures",
        not failures,
        (time.perf_counter() - started) * 1_000,
        {"platforms": ["ios", "android", "adaptive"]},
        "; ".join(failures),
    )


def upstream_lock_parity(context: MaturityContext) -> MaturityGateResult:
    started = time.perf_counter()
    errors: list[str] = []
    try:
        payload = json.loads(
            (context.root / "upstreams.lock.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        return gate_result("upstream_lock_parity", False, 0, {}, str(exc))
    if payload.get("schema") != "design-craft.upstreams-lock.v3":
        errors.append("upstream lock schema is invalid")
    upstreams = payload.get("upstreams")
    if not isinstance(upstreams, dict):
        errors.append("upstreams must be an object")
        upstreams = {}
    for name, metadata in upstreams.items():
        if not isinstance(metadata, dict):
            errors.append(f"{name}: metadata is invalid")
            continue
        commit = metadata.get("commit")
        reviewed = metadata.get("reviewed_through_commit")
        if metadata.get("reviewed_commit") != reviewed:
            errors.append(f"{name}: reviewed commit alias is stale")
        if metadata.get("latest_range_head_commit") != reviewed:
            errors.append(f"{name}: latest reviewed range head is stale")
        if metadata.get("absorbed_commit") != metadata.get(
            "behavior_absorbed_through_commit"
        ):
            errors.append(f"{name}: absorbed commit alias is stale")
        if not metadata.get("notes") or not metadata.get("coverage_contract"):
            errors.append(f"{name}: review metadata is incomplete")
        result = run_command(
            ["git", "-C", str(metadata.get("path", "")), "rev-parse", "HEAD"],
            root=context.root,
            timeout=30,
        )
        if result.returncode != 0 or result.stdout.strip() != commit:
            errors.append(f"{name}: submodule HEAD does not match lock")
    return gate_result(
        "upstream_lock_parity",
        not errors,
        (time.perf_counter() - started) * 1_000,
        {"upstream_count": len(upstreams)},
        "; ".join(errors),
    )


def route_pack(context: MaturityContext) -> MaturityGateResult:
    result = run_command(
        [sys.executable, "scripts/design_craft_codex_route_pack.py", "--check"],
        root=context.root,
        timeout=120,
    )
    return gate_result(
        "route_pack",
        result.returncode == 0,
        result.duration_ms,
        {"fixture_scope": "portable_self_check"},
        result.stderr or result.stdout or "portable route-pack self-check failed",
    )


def cross_agent_contracts(context: MaturityContext) -> MaturityGateResult:
    started = time.perf_counter()
    result = run_command(
        [
            sys.executable,
            "scripts/design_craft_cross_agent_validate.py",
            "--root",
            "evals/cross-agent",
        ],
        root=context.root,
        timeout=120,
    )
    failures = [result.stderr or result.stdout] if result.returncode != 0 else []
    return gate_result(
        "cross_agent_contracts",
        not failures,
        (time.perf_counter() - started) * 1_000,
        {"active": "definitions", "history": "separate_history_audit"},
        "; ".join(failures),
    )


def comparative_contracts(context: MaturityContext) -> MaturityGateResult:
    started = time.perf_counter()
    result = run_command(
        [
            sys.executable,
            "scripts/design_craft_comparative_validate.py",
            "--definitions-only",
        ],
        root=context.root,
        timeout=120,
    )
    failures = [result.stderr or result.stdout] if result.returncode != 0 else []
    return gate_result(
        "comparative_contracts",
        not failures,
        (time.perf_counter() - started) * 1_000,
        {"active": "definitions", "history": "separate_history_audit"},
        "; ".join(failures),
    )


def l4_evidence_contract(context: MaturityContext) -> MaturityGateResult:
    started = time.perf_counter()
    failures: list[str] = []
    for case in (
        "evals/product-ui-taste/before-after/generic-review-workbench-local-l4",
        "evals/product-ui-taste/before-after/ops-dashboard-decision-surface-l4",
    ):
        result = run_command(
            [
                sys.executable,
                "skills/design-craft/scripts/design_craft_l4_case_validate.py",
                "--case-dir",
                case,
                "--strict",
            ],
            root=context.root,
        )
        if result.returncode != 0:
            failures.append(result.stderr or result.stdout)
    return gate_result(
        "l4_evidence_contract",
        not failures,
        (time.perf_counter() - started) * 1_000,
        {"case_count": 2, "claim": "manifest_contract_only"},
        "; ".join(failures),
    )
