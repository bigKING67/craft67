#!/usr/bin/env python3
"""Validate deterministic compatibility hints, not Codex runtime selection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.manifest import ManifestError, load_manifest


def route_key(value: str) -> str:
    return value.casefold().replace(" ", "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(ROOT / "skill-pack.json"))
    parser.add_argument("--cases", default=str(ROOT / "eval/routing/cases.json"))
    args = parser.parse_args()

    try:
        manifest = load_manifest(Path(args.manifest))
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))["cases"]
        routes = {
            skill["name"]: [route_key(term) for term in skill.get("routing_terms", [])]
            for skill in manifest["skills"]
        }
        if not isinstance(cases, list) or not cases:
            raise ValueError("routing cases must be a non-empty list")
        case_ids: set[str] = set()
        for case in cases:
            if not isinstance(case, dict):
                raise ValueError("each routing case must be an object")
            case_id = case.get("id")
            prompt = case.get("prompt")
            expected = case.get("expected")
            if not isinstance(case_id, str) or not case_id or case_id in case_ids:
                raise ValueError(f"invalid or duplicate routing case id: {case_id!r}")
            case_ids.add(case_id)
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError(f"routing prompt is missing: {case_id}")
            if not isinstance(expected, list) or any(name not in routes for name in expected):
                raise ValueError(f"routing expected Skills are invalid: {case_id}")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, ManifestError) as exc:
        print(f"check_routing error: {exc}", file=sys.stderr)
        return 2

    failures = []
    for case in cases:
        prompt = route_key(case["prompt"])
        matched = sorted(
            name
            for name, terms in routes.items()
            if any(term and term in prompt for term in terms)
        )
        expected = sorted(case["expected"])
        if matched != expected:
            failures.append({"id": case["id"], "expected": expected, "matched": matched})

    if failures:
        print(json.dumps({"passed": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 2
    print(f"routing validation passed: {len(cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
