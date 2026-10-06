#!/usr/bin/env python3
"""Run the stable route contract through one portable Python process."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR.parent / "lib"
sys.dont_write_bytecode = True
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
platform_scan = importlib.import_module("design_craft_platform_scan")
route_contract = importlib.import_module("design_craft.route_contract")
authority = importlib.import_module("design_craft.authority")

# Re-export pure policy seams for focused tests and benchmark profiling.
build_route_payload = route_contract.build_route_payload
fallback_tier = route_contract.fallback_tier
load_route_payload = route_contract.load_route_payload
parse_route_payload = route_contract.parse_route_payload
print_route_payload = route_contract.print_route_payload
recommended_references = route_contract.recommended_references


def resolve_target(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def shell_path(path: Path) -> str:
    raw = str(path)
    cygpath = shutil.which("cygpath")
    if cygpath is None:
        return raw
    result = subprocess.run(
        [cygpath, "-u", raw],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.stdout.strip().replace("\r", "") if result.returncode == 0 else raw


def filesystem_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.exists() or shutil.which("cygpath") is None:
        return path
    result = subprocess.run(
        ["cygpath", "-w", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip().replace("\r", ""))
    return path


def detect_platform(
    *, target: Path, requested: str, product_context_path: Path | None
) -> dict[str, object]:
    product_path, product_path_source = platform_scan.discover_product_context(
        target,
        str(product_context_path) if product_context_path is not None else "",
    )
    platform, source, confidence, signals, contradictions = platform_scan.resolve_platform(
        target,
        requested,
        product_path,
    )
    return {
        "schema": platform_scan.SCHEMA,
        "ok": True,
        "target": str(target),
        "platform": platform,
        "platform_source": source,
        "platform_confidence": confidence,
        "product_context_path": (
            str(product_path) if product_path is not None and product_path.is_file() else ""
        ),
        "product_context_path_source": product_path_source,
        "product_context_status": (
            "present" if product_path is not None and product_path.is_file() else "missing"
        ),
        "signals": signals,
        "contradictions": contradictions,
        "scan_mode": "detect",
        "findings": [],
        "summary": {
            "total": 0,
            "severity_counts": {level: 0 for level in ("P0", "P1", "P2", "P3")},
        },
        **platform_scan.runtime_contract(platform),
    }


def route_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="design_craft_route.sh",
        description=(
            "Resolve the design-craft route through the global planner or a "
            "conservative portable fallback."
        ),
    )
    parser.add_argument("--target", default=".")
    parser.add_argument("--surface", default="auto")
    parser.add_argument("--intent", default="auto")
    parser.add_argument("--scope", default="auto")
    parser.add_argument("--style", default="auto")
    parser.add_argument(
        "--platform",
        default="auto",
        choices=("auto", "web", "ios", "android", "adaptive"),
    )
    parser.add_argument("--product-context-path", default="")
    parser.add_argument("--design-authority-mode", default="auto")
    parser.add_argument("--style-authority-path", default="")
    parser.add_argument("--has-reference-image", default="0")
    parser.add_argument("--needs-generated-reference", default="0")
    parser.add_argument(
        "--evidence-mode",
        default="auto",
        choices=("auto", "none", "comp-fidelity", "sealed-rendition"),
    )
    parser.add_argument("--existing-project", default="1")
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def planner_command(
    *,
    route_plan: str,
    surface: str,
    intent: str,
    scope: str,
    style: str,
    platform: str,
    design_authority_mode: str,
    has_reference_image: str,
    needs_generated_reference: str,
    evidence_mode: str,
    existing_project: str,
    product_context_path: str,
    style_authority_path: str,
) -> list[str]:
    command = [
        "bash",
        route_plan,
        "--surface",
        surface,
        "--intent",
        intent,
        "--scope",
        scope,
        "--style",
        style,
        "--platform",
        platform,
        "--design-authority-mode",
        design_authority_mode,
        "--has-reference-image",
        has_reference_image,
        "--needs-generated-reference",
        needs_generated_reference,
        "--evidence-mode",
        evidence_mode,
        "--existing-project",
        existing_project,
        "--output",
        "json",
    ]
    if product_context_path:
        command.extend(["--product-context-path", product_context_path])
    if style_authority_path:
        command.extend(["--style-authority-path", style_authority_path])
    return command


def run_route(argv: Sequence[str]) -> int:
    args = route_parser().parse_args(list(argv))
    target = resolve_target(args.target)
    scan_target = target.parent if target.is_file() else target
    if not scan_target.is_dir():
        print(f"target is not a directory: {target}", file=sys.stderr)
        return 2

    style_resolution = authority.resolve_project_authority(
        target,
        "DESIGN.md",
        explicit=args.style_authority_path or None,
    )
    product_resolution = authority.resolve_project_authority(
        target,
        "PRODUCT.md",
        explicit=args.product_context_path or None,
    )
    style_authority = style_resolution.path
    product_context = product_resolution.path
    target_shell = shell_path(target)
    style_authority_shell = shell_path(style_authority) if style_authority else ""
    product_context_shell = shell_path(product_context) if product_context else ""
    platform_payload = detect_platform(
        target=scan_target,
        requested=args.platform,
        product_context_path=product_context,
    )
    platform_payload["product_context_path_source"] = product_resolution.source
    platform_payload["product_context_path_reason"] = product_resolution.reason
    route_plan_raw = os.environ.get(
        "DESIGN_CRAFT_ROUTE_PLAN",
        shell_path(Path.home() / ".codex/tools/frontend_route_plan.sh"),
    )
    route_plan_path = filesystem_path(route_plan_raw)
    route_plan = shell_path(route_plan_path) if route_plan_path.exists() else route_plan_raw
    command = planner_command(
        route_plan=route_plan,
        surface=args.surface,
        intent=args.intent,
        scope=args.scope,
        style=args.style,
        platform=args.platform,
        design_authority_mode=args.design_authority_mode,
        has_reference_image=args.has_reference_image,
        needs_generated_reference=args.needs_generated_reference,
        evidence_mode=args.evidence_mode,
        existing_project=args.existing_project,
        product_context_path=product_context_shell,
        style_authority_path=style_authority_shell,
    )
    planner_available = route_plan_path.is_file() and os.access(route_plan_path, os.X_OK)

    try:
        route_contract.validate_evidence_request(
            requested=args.evidence_mode,
            platform=str(platform_payload["platform"]),
            has_reference=args.has_reference_image == "1",
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.dry_run:
        if planner_available:
            print(f"FRONTEND_WORKSPACE_ROOT={shlex.quote(target_shell)} {shlex.join(command)}")
        else:
            print(
                "portable_fallback "
                f"target={shlex.quote(target_shell)} "
                f"platform={shlex.quote(args.platform)} "
                f"product_context={shlex.quote(product_context_shell)} "
                f"style_authority={shlex.quote(style_authority_shell)}"
            )
        return 0

    planner_status = 0
    route_source = "portable_fallback"
    route_payload: dict[str, object] = {}
    if planner_available:
        environment = dict(os.environ)
        environment["FRONTEND_WORKSPACE_ROOT"] = target_shell
        result = subprocess.run(
            command,
            env=environment,
            stdout=subprocess.PIPE,
            text=True,
            check=False,
        )
        planner_status = result.returncode
        route_source = "codex_global"
        try:
            route_payload = parse_route_payload(result.stdout)
        except json.JSONDecodeError:
            route_payload = {}

    route_payload = build_route_payload(
        route_payload=route_payload,
        platform_payload=platform_payload,
        route_source=route_source,
        surface=args.surface,
        intent=args.intent,
        scope=args.scope,
        style=args.style,
        style_authority_path=style_authority_shell,
        design_authority_mode=args.design_authority_mode,
        existing_project=args.existing_project == "1",
        has_reference=args.has_reference_image == "1",
        needs_reference=args.needs_generated_reference == "1",
        evidence_mode=args.evidence_mode,
        style_authority_source=style_resolution.source,
        style_authority_reason=style_resolution.reason,
    )
    print_route_payload(route_payload, intent=args.intent, json_only=args.json_only)
    if route_source == "portable_fallback":
        return 0 if route_payload.get("ok") else 2
    return 0 if planner_status == 0 else 2


def main(argv: Sequence[str] | None = None) -> int:
    return run_route(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
