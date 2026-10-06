#!/usr/bin/env python3
"""Validate the complete Leonxlnx/taste-skill absorption boundary."""

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


SCHEMA = "design-craft.taste-absorption.v1"
ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "upstreams.lock.json"
MATRIX_PATH = ROOT / "docs/taste-skill-absorption.md"
COMPATIBILITY_PATH = ROOT / "skills/design-craft/COMPATIBILITY.json"
DECISION_STATUSES = {
    "absorbed",
    "partial",
    "missing_high_value",
    "intentionally_rejected",
    "provenance_only",
}


COVERAGE = {
    "taste-skill": {
        "paths": [
            "skills/design-craft/references/visual-judgment.md",
            "skills/design-craft/references/foundational-visual-principles.md",
            "skills/design-craft/references/product-ui-taste-review.md",
            "skills/design-craft/references/design-move-library.md",
        ],
        "terms": [
            "anti-slop",
            "Infer before styling",
            "Cards are a tool",
            "Acceptance Criteria",
        ],
    },
    "redesign-skill": {
        "paths": [
            "skills/design-craft/references/product-ui-taste-review.md",
            "skills/design-craft/references/design-move-library.md",
        ],
        "terms": [
            "Dashboard card soup",
            "Loading, empty, error",
            "Acceptance criteria",
        ],
    },
    "minimalist-skill": {
        "paths": [
            "skills/design-craft/references/visual-judgment.md",
            "skills/design-craft/references/design-system-contract.md",
        ],
        "terms": [
            "Use shadows only where elevation",
            "Typography roles",
            "Token layers",
        ],
    },
    "gpt-tasteskill": {
        "paths": [
            "skills/design-craft/references/visual-judgment.md",
            "skills/design-craft/references/motion-quality.md",
        ],
        "terms": [
            "DESIGN_VARIANCE",
            "MOTION_INTENSITY",
            "Do not default to Inter",
            "Motion must clarify",
        ],
    },
    "image-to-code-skill": {
        "paths": [
            "skills/design-craft/references/image-reference-implementation.md",
            "skills/design-craft/references/comp-fidelity.md",
        ],
        "terms": ["selected image", "label estimates", "not visual acceptance"],
    },
    "imagegen-frontend-web": {
        "paths": ["skills/design-craft/references/web-image-direction.md"],
        "terms": ["generation optional", "agreed scope and budget", "failed/missing"],
    },
    "stitch-skill": {
        "paths": [
            "skills/design-craft/references/design-system-contract.md",
            "skills/design-craft/templates/developer-product/design.md",
            "skills/design-craft/templates/developer-product/design.dark.md",
        ],
        "terms": [
            "machine-readable",
            "default seed",
            "component state matrix",
        ],
    },
    "soft-skill": {
        "paths": [
            "skills/design-craft/references/visual-judgment.md",
            "skills/design-craft/references/product-ui-taste-review.md",
        ],
        "terms": [
            "premium",
            "restrained",
            "not generic",
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
    meta = lock.get("upstreams", {}).get("taste-skill", {})
    upstream = ROOT / meta.get("path", "upstreams/taste-skill")
    inventory = meta.get("skill_inventory", {})

    state, state_errors = validate_review_state("taste-skill", meta, upstream)
    errors.extend(state_errors)
    expected_skills = inventory.get("skills", [])
    expected_auxiliary = inventory.get("auxiliary_files", [])
    observed_skills = sorted(
        path.parent.name
        for path in (upstream / "skills").glob("*/SKILL.md")
        if path.is_file()
    )
    observed_auxiliary = sorted(
        path.relative_to(upstream).as_posix()
        for path in (upstream / "skills").rglob("*")
        if path.is_file() and path.name != "SKILL.md"
    )
    if observed_skills != sorted(expected_skills):
        errors.append(
            "taste Skill inventory drift: "
            f"expected {sorted(expected_skills)}, observed {observed_skills}"
        )
    if observed_auxiliary != sorted(expected_auxiliary):
        errors.append(
            "taste auxiliary inventory drift: "
            f"expected {sorted(expected_auxiliary)}, observed {observed_auxiliary}"
        )

    decisions = inventory.get("entrypoint_decisions", {})
    auxiliary_decisions = inventory.get("auxiliary_decisions", {})
    if set(decisions) != set(expected_skills):
        errors.append("entrypoint_decisions must cover every taste Skill exactly once")
    if set(auxiliary_decisions) != set(expected_auxiliary):
        errors.append("auxiliary_decisions must cover every taste auxiliary file")
    for label, decision in {**decisions, **auxiliary_decisions}.items():
        if decision not in DECISION_STATUSES:
            errors.append(f"{label}: invalid absorption decision {decision!r}")
        if decision == "missing_high_value":
            errors.append(f"{label}: missing_high_value blocks absorption completeness")

    if meta.get("coverage_contract") != SCHEMA:
        errors.append(f"coverage_contract must be {SCHEMA}")
    if meta.get("coverage_matrix") != matrix_relative:
        errors.append(f"coverage_matrix must be {matrix_relative}")
    compatibility = read_json(COMPATIBILITY_PATH)
    contract = compatibility.get("maintenance_contracts", {}).get(
        "taste_absorption"
    )
    if contract != SCHEMA:
        errors.append(f"COMPATIBILITY.json must declare {SCHEMA}")

    matrix_text = MATRIX_PATH.read_text(encoding="utf-8") if MATRIX_PATH.is_file() else ""
    errors.extend(validate_matrix_vocabulary(matrix_text))
    for skill in expected_skills:
        if f"`{skill}`" not in matrix_text:
            errors.append(f"absorption matrix is missing Skill entry: {skill}")
    for relative in expected_auxiliary:
        if f"`{relative}`" not in matrix_text:
            errors.append(f"absorption matrix is missing auxiliary entry: {relative}")

    coverage_payload = {}
    expected_covered = {
        skill for skill, decision in decisions.items() if decision in {"absorbed", "partial"}
    }
    if set(COVERAGE) != expected_covered:
        errors.append(
            "coverage map must match every absorbed/partial taste entrypoint exactly"
        )
    for skill, spec in COVERAGE.items():
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
            "decision": decisions.get(skill),
            "paths": spec["paths"],
            "missing_paths": missing_paths,
            "missing_terms": missing_terms,
        }

    return {
        "schema": SCHEMA,
        "ok": not errors,
        "upstream": {
            **state,
            "skill_count": len(observed_skills),
            "skills": observed_skills,
            "auxiliary_file_count": len(observed_auxiliary),
            "auxiliary_files": observed_auxiliary,
        },
        "coverage": coverage_payload,
        "matrix": matrix_relative,
        "status_vocabulary": list(MATRIX_STATUS_LABELS),
        "errors": errors,
    }


def self_check() -> None:
    if "taste-skill" not in COVERAGE or "redesign-skill" not in COVERAGE:
        raise RuntimeError("internal taste coverage map lost its primary entrypoints")


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
            "taste-skill absorption verified: "
            f"skills={upstream['skill_count']} "
            f"auxiliary={upstream['auxiliary_file_count']} "
            f"cumulative={upstream['cumulative_status']} "
            f"latest={upstream['latest_range_status']}"
        )
    else:
        print("\n".join(payload["errors"]), file=sys.stderr)
    return 0 if payload["ok"] or not args.strict else 2


if __name__ == "__main__":
    raise SystemExit(main())
