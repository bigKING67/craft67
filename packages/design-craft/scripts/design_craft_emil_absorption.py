#!/usr/bin/env python3
"""Validate the five-skill emilkowalski/skills absorption contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from design_craft_absorption_common import (
    LOCK_SCHEMA,
    validate_matrix_vocabulary,
    validate_review_state,
)


SCHEMA = "design-craft.emil-absorption.v1"
ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "upstreams.lock.json"
MATRIX_PATH = ROOT / "docs/emilkowalski-absorption.md"
COMPATIBILITY_PATH = ROOT / "skills/design-craft/COMPATIBILITY.json"
LATEST_RANGE_ENTRYPOINT_DECISIONS = {
    "find-animation-opportunities": "absorbed",
    "pick-ui-library": "intentionally_rejected",
    "prototype": "absorbed",
    "animate-expo": "partial",
    "write-swift": "intentionally_rejected",
    "mobile-native": "partial",
}
LATEST_RANGE_COVERAGE = {
    "paths": [
        "skills/design-craft/references/motion-quality.md",
        "skills/design-craft/references/motion-audit-planning.md",
        "skills/design-craft/references/motion-vocabulary.md",
        "skills/design-craft/references/prototype-workflow.md",
        "skills/design-craft/references/component-primitive-selection.md",
        "skills/design-craft/references/react-native-expo-motion.md",
        "skills/design-craft/references/surface-playbooks.md",
    ],
    "terms": [
        "Motion needs a reason",
        "Frequency decides restraint",
        "Most UI animations should stay under `300ms`",
        "Missed opportunities",
        "Reject duplicates",
        "at most four missed opportunities",
        "one UI piece per run",
        "Default to three variants",
        "isolated prototype surface",
        "Render one variant at a time",
        "ready_for_selection",
        "explicit user selection",
        "keep | adopt | migrate | defer",
        "Base UI is a supported project choice",
        "Primitive-library consistency cannot substitute for visual-system consistency",
        "Base UI-only universal prescription",
        "UI/worklet/native path",
        "release build on every shipped target",
        "adaptive or cross-platform scope requires both iOS and Android",
        "There are no universal duration",
    ],
}


COVERAGE = {
    "emil-design-eng": {
        "status": "absorbed",
        "paths": [
            "skills/design-craft/references/motion-quality.md",
            "skills/design-craft/references/motion-patterns.md",
            "skills/design-craft/references/engineering-quality.md",
            "skills/design-craft/references/design-system-contract.md",
        ],
        "terms": [
            "@starting-style",
            "skip the remaining delay and entrance motion",
            "visibilitychange",
            "font-optical-sizing",
            "scale(0.97)",
        ],
    },
    "apple-design": {
        "status": "absorbed",
        "paths": [
            "skills/design-craft/SKILL.md",
            "skills/design-craft/references/interaction-physics.md",
            "skills/design-craft/references/product-design-principles.md",
            "skills/design-craft/references/design-system-contract.md",
        ],
        "terms": [
            "presentation value",
            "projected endpoint",
            "release animation starts at the finger's measured velocity",
            "Naming a projected endpoint alone never satisfies",
            "rubber-band",
            "font-optical-sizing",
            "causal state change",
        ],
    },
    "review-animations": {
        "status": "absorbed",
        "paths": [
            "skills/design-craft/references/motion-quality.md",
            "skills/design-craft/references/motion-audit-planning.md",
            "skills/design-craft/scripts/design_craft_detect.sh",
        ],
        "terms": [
            "| Before | After | Why |",
            "transition: all",
            "Static source",
            "Block",
        ],
    },
    "improve-animations": {
        "status": "absorbed",
        "paths": [
            "skills/design-craft/references/motion-audit-planning.md",
            "skills/design-craft/templates/motion-plan/plan.md",
            "skills/design-craft/scripts/design_craft_motion_plan.py",
        ],
        "terms": [
            "Phase 1: motion recon",
            "user impact x frequency x confidence / implementation cost",
            "reconcile",
            "design-craft.motion-plan-scaffold.v1",
        ],
    },
    "animation-vocabulary": {
        "status": "absorbed",
        "paths": ["skills/design-craft/references/motion-vocabulary.md"],
        "terms": [
            "Perceptual duration",
            "Idle animation",
            "Anticipation",
            "Follow-through",
            "Squash and stretch",
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
    meta = lock.get("upstreams", {}).get("emilkowalski-skills", {})
    inventory = meta.get("skill_inventory", {})
    latest_decisions = inventory.get("latest_range_entrypoint_decisions", {})
    upstream = ROOT / meta.get("path", "upstreams/emilkowalski-skills")
    state, state_errors = validate_review_state(
        "emilkowalski-skills", meta, upstream
    )
    errors.extend(state_errors)

    expected_skills = inventory.get("skills", [])
    expected_auxiliary = inventory.get("auxiliary_markdown", [])
    observed_skills = sorted(
        path.parent.name
        for path in (upstream / "skills").glob("*/SKILL.md")
        if path.is_file()
    )
    observed_auxiliary = sorted(
        path.relative_to(upstream).as_posix()
        for path in (upstream / "skills").rglob("*.md")
        if path.name != "SKILL.md"
    )
    observed_non_markdown = sorted(
        path.relative_to(upstream).as_posix()
        for path in (upstream / "skills").rglob("*")
        if path.is_file() and path.suffix.lower() != ".md"
    )

    if observed_skills != sorted(expected_skills):
        errors.append(
            "upstream Skill inventory drift: "
            f"expected {sorted(expected_skills)}, observed {observed_skills}"
        )
    if observed_auxiliary != sorted(expected_auxiliary):
        errors.append(
            "upstream auxiliary Markdown inventory drift: "
            f"expected {sorted(expected_auxiliary)}, observed {observed_auxiliary}"
        )
    if observed_non_markdown != sorted(inventory.get("non_markdown_files", [])):
        errors.append(
            "upstream non-Markdown inventory drift: "
            f"observed {observed_non_markdown}"
        )
    if latest_decisions != LATEST_RANGE_ENTRYPOINT_DECISIONS:
        errors.append(
            "latest_range_entrypoint_decisions must explicitly cover the reviewed additions"
        )

    if meta.get("coverage_contract") != SCHEMA:
        errors.append(f"coverage_contract must be {SCHEMA}")
    if meta.get("coverage_matrix") != matrix_relative:
        errors.append(f"coverage_matrix must be {matrix_relative}")

    compatibility = read_json(COMPATIBILITY_PATH)
    contract = compatibility.get("maintenance_contracts", {}).get("emil_absorption")
    if contract != SCHEMA:
        errors.append(f"COMPATIBILITY.json must declare {SCHEMA}")

    matrix_text = MATRIX_PATH.read_text(encoding="utf-8") if MATRIX_PATH.is_file() else ""
    errors.extend(validate_matrix_vocabulary(matrix_text))
    for entrypoint in LATEST_RANGE_ENTRYPOINT_DECISIONS:
        if f"`{entrypoint}`" not in matrix_text:
            errors.append(f"absorption matrix is missing latest entrypoint: {entrypoint}")

    coverage_payload = {}
    for skill, spec in COVERAGE.items():
        if skill not in expected_skills:
            errors.append(f"coverage map contains unexpected Skill: {skill}")
        if f"`{skill}`" not in matrix_text:
            errors.append(f"absorption matrix is missing Skill section: {skill}")
        combined = ""
        missing_paths = []
        for relative in spec["paths"]:
            path = ROOT / relative
            if not path.is_file():
                missing_paths.append(relative)
                continue
            combined += "\n" + path.read_text(encoding="utf-8")
        normalized = combined.casefold()
        missing_terms = [
            term for term in spec["terms"] if term.casefold() not in normalized
        ]
        if missing_paths:
            errors.append(f"{skill}: missing local coverage paths: {missing_paths}")
        if missing_terms:
            errors.append(f"{skill}: missing local coverage terms: {missing_terms}")
        coverage_payload[skill] = {
            "status": spec["status"],
            "paths": spec["paths"],
            "missing_paths": missing_paths,
            "missing_terms": missing_terms,
        }

    if set(COVERAGE) != set(expected_skills):
        errors.append(
            "coverage map must match the five locked Skill entrypoints exactly"
        )

    latest_combined = ""
    latest_missing_paths = []
    for relative in LATEST_RANGE_COVERAGE["paths"]:
        path = ROOT / relative
        if not path.is_file():
            latest_missing_paths.append(relative)
            continue
        latest_combined += "\n" + path.read_text(encoding="utf-8")
    normalized_latest = latest_combined.casefold()
    latest_missing_terms = [
        term
        for term in LATEST_RANGE_COVERAGE["terms"]
        if term.casefold() not in normalized_latest
    ]
    if latest_missing_paths:
        errors.append(f"latest range: missing local coverage paths: {latest_missing_paths}")
    if latest_missing_terms:
        errors.append(f"latest range: missing local coverage terms: {latest_missing_terms}")

    return {
        "schema": SCHEMA,
        "ok": not errors,
        "upstream": {
            **state,
            "commit": state["current_commit"],
            "locked_commit": meta.get("commit"),
            "skill_count": len(observed_skills),
            "skills": observed_skills,
            "auxiliary_markdown_count": len(observed_auxiliary),
            "auxiliary_markdown": observed_auxiliary,
            "non_markdown_file_count": len(observed_non_markdown),
            "non_markdown_files": observed_non_markdown,
        },
        "coverage": coverage_payload,
        "latest_range": {
            "entrypoint_decisions": latest_decisions,
            "coverage_paths": LATEST_RANGE_COVERAGE["paths"],
            "missing_paths": latest_missing_paths,
            "missing_terms": latest_missing_terms,
        },
        "matrix": matrix_relative,
        "errors": errors,
    }


def self_check() -> None:
    if set(COVERAGE) != {
        "emil-design-eng",
        "apple-design",
        "review-animations",
        "improve-animations",
        "animation-vocabulary",
    }:
        raise RuntimeError("internal five-Skill coverage map drifted")
    if LATEST_RANGE_ENTRYPOINT_DECISIONS != {
        "find-animation-opportunities": "absorbed",
        "pick-ui-library": "intentionally_rejected",
        "prototype": "absorbed",
        "animate-expo": "partial",
        "write-swift": "intentionally_rejected",
        "mobile-native": "partial",
    }:
        raise RuntimeError("latest-range entrypoint decisions drifted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Run internal contract checks.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on validation errors.")
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
            "Emil absorption verified: "
            f"skills={upstream['skill_count']} "
            f"auxiliary_markdown={upstream['auxiliary_markdown_count']} "
            f"non_markdown={upstream['non_markdown_file_count']}"
        )
    else:
        print("\n".join(payload["errors"]), file=sys.stderr)
    return 0 if payload["ok"] or not args.strict else 2


if __name__ == "__main__":
    raise SystemExit(main())
