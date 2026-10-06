#!/usr/bin/env python3
"""Validate the pbakaus/impeccable fusion and runtime boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from design_craft_absorption_common import (
    LOCK_SCHEMA,
    MATRIX_STATUS_LABELS,
    validate_matrix_vocabulary,
    validate_review_state,
)


SCHEMA = "design-craft.impeccable-absorption.v1"
ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "upstreams.lock.json"
MATRIX_PATH = ROOT / "docs/impeccable-absorption.md"
COMPATIBILITY_PATH = ROOT / "skills/design-craft/COMPATIBILITY.json"
DECISION_STATUSES = {
    "absorbed",
    "partial",
    "missing_high_value",
    "intentionally_rejected",
    "provenance_only",
}


COVERAGE = {
    "workflow_modes": {
        "paths": ["skills/design-craft/references/impeccable-workflow.md"],
        "terms": [
            "`shape`",
            "`craft`",
            "`critique`",
            "`audit`",
            "`polish`",
            "`harden`",
            "`adapt`",
            "`optimize`",
            "`extract`",
            "`document`",
            "`live`",
        ],
    },
    "hardening_and_performance": {
        "paths": [
            "skills/design-craft/references/impeccable-workflow.md",
            "skills/design-craft/references/engineering-quality.md",
            "skills/design-craft/references/performance-quality.md",
        ],
        "terms": [
            "Use realistic hostile data",
            "4xx/5xx/network timeout",
            "Measure or establish a baseline first",
            "Loading, empty, error",
        ],
    },
    "lifecycle_ownership": {
        "paths": [
            "skills/design-craft/references/engineering-quality.md",
            "skills/design-craft/references/validation-contract.md",
        ],
        "terms": [
            "Every route into the same state",
            "generation token, or epoch",
            "same captured instance set",
            "Static source or source-shape tests can prove these guards",
        ],
    },
    "production_audit_discipline": {
        "paths": [
            "skills/design-craft/SKILL.md",
            "skills/design-craft/references/performance-quality.md",
            "skills/design-craft/references/validation-contract.md",
        ],
        "terms": [
            "baseline before selecting or claiming performance fixes",
            "Contextual static signals",
            "explicit line, word, section, or item limit",
            "count newline-delimited lines",
            "at most eight ledger entries",
            "Do not assign P0 solely",
            "at most two batched verification passes",
            "44 CSS pixels",
            "provisional numeric thresholds",
        ],
    },
    "detector_and_evidence": {
        "paths": [
            "skills/design-craft/references/impeccable-workflow.md",
            "skills/design-craft/scripts/design_craft_detect.sh",
        ],
        "terms": [
            "upstreams/impeccable/skill/scripts/detect.mjs",
            "signals, not law",
            "DEGRADED: single-context",
            "Do not claim dual-agent",
            "available_regex_fallback",
            "optional static HTML/CSS parser dependencies unavailable",
        ],
    },
    "detector_correctness": {
        "paths": [
            "skills/design-craft/references/impeccable-workflow.md",
            "tests/unit/test_impeccable_detector_contract.py",
            "skills/design-craft/lib/design_craft/authority.py",
            "skills/design-craft/lib/design_craft/detector_policy.py",
        ],
        "terms": [
            "style carriers",
            "comment-safe broken-image",
            "query strings and fragments",
            "rounded-none",
            "single-font rule remains retired",
            "YAML scalar escapes",
            "Blade compound suffixes",
            "kicker-above-heading",
            "contextual signal",
            "evals/fixtures/impeccable-detector",
            "function-level",
            "workspace_owns",
            "redact_url_userinfo",
            "linked_stylesheet_files",
        ],
    },
    "reference_fidelity_and_verdict": {
        "paths": [
            "skills/design-craft/references/system-review.md",
            "skills/design-craft/references/comp-fidelity.md",
            "skills/design-craft/references/reference-workflow.md",
            "skills/design-craft/references/validation-contract.md",
            "skills/design-craft/lib/design_craft/comp_fidelity.py",
        ],
        "terms": [
            "before reading the implementation summary",
            "acceptable_adaptation",
            "added_without_approval",
            "resolved",
            "partial",
            "unresolved",
            "Browser defaults are not automatically defects",
            "measurement_only",
            "exact_coordinates_no_registration_or_resize",
            "Human region review remains required",
            "committed visual-regression golden",
            "runtime-unavailable fallback",
            "the task remains `incomplete`",
        ],
    },
    "platform_quality": {
        "paths": [
            "skills/design-craft/references/ios-quality.md",
            "skills/design-craft/references/android-quality.md",
            "skills/design-craft/references/adaptive-quality.md",
            "skills/design-craft/scripts/design_craft_platform_scan.py",
        ],
        "terms": [
            "size classes",
            "predictive Back",
            "Shared versus platform-specific",
            "WebView/Capacitor/Cordova shells remain `web`",
        ],
    },
    "design_system_corrections": {
        "paths": [
            "skills/design-craft/references/design-system-contract.md",
            "skills/design-craft/references/foundational-visual-principles.md",
        ],
        "terms": [
            "component state matrix",
            "focus-visible",
            "Proximity",
            "Alignment",
        ],
    },
    "latest_judgment": {
        "paths": [
            "skills/design-craft/references/visual-judgment.md",
            "skills/design-craft/references/surface-playbooks.md",
            "skills/design-craft/references/impeccable-workflow.md",
        ],
        "terms": [
            "The brief wins",
            "Refinement preserves",
            "Visual authority is observed evidence",
            "`Persuade`",
            "`Operate`",
            "`Read`",
            "`Experience`",
            "craft floor",
            "score / applicable maximum",
        ],
    },
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> dict:
    errors: list[str] = []
    matrix_relative = MATRIX_PATH.relative_to(ROOT).as_posix()
    lock = read_json(LOCK_PATH)
    if lock.get("schema") != LOCK_SCHEMA:
        errors.append(f"upstream lock schema must be {LOCK_SCHEMA}")
    meta = lock.get("upstreams", {}).get("impeccable", {})
    upstream = ROOT / meta.get("path", "upstreams/impeccable")
    inventory = meta.get("skill_inventory", {})
    state, state_errors = validate_review_state("impeccable", meta, upstream)
    errors.extend(state_errors)

    main_skill = str(inventory.get("main_skill", ""))
    command_metadata_path = str(inventory.get("command_metadata", ""))
    expected_commands = inventory.get("commands", [])
    detector_path = str(inventory.get("detector", ""))
    platform_references = inventory.get("platform_references", [])
    rejected_paths = inventory.get("intentionally_rejected_paths", [])
    command_decisions = inventory.get("command_decisions", {})

    if not main_skill or not (upstream / main_skill).is_file():
        errors.append(f"impeccable main Skill is missing: {main_skill or 'unavailable'}")
    command_metadata = {}
    if not command_metadata_path or not (upstream / command_metadata_path).is_file():
        errors.append(
            "impeccable command metadata is missing: "
            f"{command_metadata_path or 'unavailable'}"
        )
    else:
        try:
            command_metadata = read_json(upstream / command_metadata_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"impeccable command metadata is invalid: {exc}")
    observed_commands = sorted([*command_metadata, "impeccable"])
    if observed_commands != sorted(expected_commands):
        errors.append(
            "impeccable command inventory drift: "
            f"expected {sorted(expected_commands)}, observed {observed_commands}"
        )
    if set(command_decisions) != set(expected_commands):
        errors.append("command_decisions must cover every impeccable command exactly once")
    for command in expected_commands:
        if command == "impeccable":
            continue
        reference = upstream / f"skill/reference/{command}.md"
        if not reference.is_file():
            errors.append(f"impeccable command reference is missing: /{command}")
    for command, decision in command_decisions.items():
        if decision not in DECISION_STATUSES:
            errors.append(f"/{command}: invalid absorption decision {decision!r}")
        if decision == "missing_high_value":
            errors.append(f"/{command}: missing_high_value blocks absorption completeness")

    for label, relative in (
        ("detector", detector_path),
        *(("platform reference", str(path)) for path in platform_references),
        *(("rejected runtime/package boundary", str(path)) for path in rejected_paths),
    ):
        if not relative or not (upstream / relative).is_file():
            errors.append(f"impeccable {label} path is missing: {relative or 'unavailable'}")

    if meta.get("coverage_contract") != SCHEMA:
        errors.append(f"coverage_contract must be {SCHEMA}")
    if meta.get("coverage_matrix") != matrix_relative:
        errors.append(f"coverage_matrix must be {matrix_relative}")
    compatibility = read_json(COMPATIBILITY_PATH)
    contract = compatibility.get("maintenance_contracts", {}).get(
        "impeccable_absorption"
    )
    if contract != SCHEMA:
        errors.append(f"COMPATIBILITY.json must declare {SCHEMA}")

    matrix_text = MATRIX_PATH.read_text(encoding="utf-8") if MATRIX_PATH.is_file() else ""
    errors.extend(validate_matrix_vocabulary(matrix_text))
    for command in expected_commands:
        if f"`/{command}`" not in matrix_text:
            errors.append(f"absorption matrix is missing command: /{command}")
    for term in (
        "live-server",
        "manual-edit",
        "provider",
        "package",
        "GitHub sheriff",
        "browser67",
    ):
        if term.casefold() not in matrix_text.casefold():
            errors.append(f"absorption matrix is missing runtime boundary term: {term}")
    for label, sha in (
        ("reviewed boundary", state["reviewed_through_commit"]),
        ("selected behavior boundary", state["behavior_absorbed_through_commit"]),
    ):
        if sha not in matrix_text:
            errors.append(f"absorption matrix is missing {label}: {sha}")

    coverage_payload = {}
    for capability, spec in COVERAGE.items():
        combined = ""
        missing_paths = []
        for relative in spec["paths"]:
            path = ROOT / relative
            if not path.is_file():
                missing_paths.append(relative)
                continue
            combined += "\n" + path.read_text(encoding="utf-8")
        normalized = " ".join(combined.casefold().split())
        missing_terms = [
            term
            for term in spec["terms"]
            if " ".join(term.casefold().split()) not in normalized
        ]
        if missing_paths:
            errors.append(f"{capability}: missing local coverage paths: {missing_paths}")
        if missing_terms:
            errors.append(f"{capability}: missing local coverage terms: {missing_terms}")
        coverage_payload[capability] = {
            "paths": spec["paths"],
            "missing_paths": missing_paths,
            "missing_terms": missing_terms,
        }

    detector_wrapper = ROOT / "skills/design-craft/scripts/design_craft_detect.sh"
    detector_text = detector_wrapper.read_text(encoding="utf-8") if detector_wrapper.is_file() else ""
    if detector_path not in detector_text:
        errors.append("design_craft_detect.sh must retain the locked upstream detector path")

    return {
        "schema": SCHEMA,
        "ok": not errors,
        "upstream": {
            **state,
            "main_skill": main_skill,
            "command_metadata": command_metadata_path,
            "command_count": len(observed_commands),
            "commands": observed_commands,
            "detector": detector_path,
            "platform_references": platform_references,
            "intentionally_rejected_paths": rejected_paths,
        },
        "coverage": coverage_payload,
        "matrix": matrix_relative,
        "status_vocabulary": list(MATRIX_STATUS_LABELS),
        "errors": errors,
    }


def self_check() -> None:
    if set(COVERAGE) != {
        "workflow_modes",
        "hardening_and_performance",
        "lifecycle_ownership",
        "production_audit_discipline",
        "detector_and_evidence",
        "detector_correctness",
        "reference_fidelity_and_verdict",
        "platform_quality",
        "design_system_corrections",
        "latest_judgment",
    }:
        raise RuntimeError("internal impeccable coverage map drifted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.check:
        self_check()
    payload = validate()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif payload["ok"]:
        upstream = payload["upstream"]
        print(
            "impeccable absorption verified: "
            f"commands={upstream['command_count']} "
            f"cumulative={upstream['cumulative_status']} "
            f"latest={upstream['latest_range_status']}"
        )
    else:
        print("\n".join(payload["errors"]), file=sys.stderr)
    return 0 if payload["ok"] or not args.strict else 2


if __name__ == "__main__":
    raise SystemExit(main())
