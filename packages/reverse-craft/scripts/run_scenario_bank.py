#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "reverse-craft" / "lib"))

from reverse_craft.case_store import (  # noqa: E402
    add_evidence,
    add_finding,
    add_path,
    init_case,
    render_report,
    seal_case,
    validate_case,
)
from reverse_craft.common import ReverseCraftError  # noqa: E402
from reverse_craft.routing import route  # noqa: E402

REQUIRED = {
    "schema", "id", "title", "scope", "hint", "expected_route", "artifact_name",
    "artifact_content", "kind", "finding", "severity", "reproduction", "path",
}


def run_scenario(path: Path, workspace: Path, home: Path) -> dict[str, object]:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - set(scenario))
    if missing or scenario.get("schema") != "reverse-craft.scenario.v1":
        raise ValueError(f"invalid scenario {path.name}: missing={missing}")
    routed = route(scenario["hint"])
    if routed["primary"]["id"] != scenario["expected_route"]:
        raise AssertionError(f"route mismatch: {routed['primary']['id']} != {scenario['expected_route']}")
    artifact = workspace / scenario["artifact_name"]
    artifact.write_text(scenario["artifact_content"], encoding="utf-8")
    initialized = init_case(scenario["title"], scenario["scope"], scenario["expected_route"], str(home))
    case_id = initialized["case"]["id"]
    evidence = add_evidence(case_id, str(artifact), scenario["kind"], home=str(home))["evidence"]
    finding = add_finding(
        case_id, scenario["finding"], scenario["severity"], "confirmed", [evidence["id"]],
        reproduction=scenario["reproduction"], confidence="high", home=str(home),
    )["finding"]
    add_path(
        case_id, scenario["path"], [finding["id"]], status="confirmed",
        validation=scenario["reproduction"], home=str(home),
    )
    report = render_report(case_id, home=str(home))
    before = validate_case(case_id, str(home))
    if not before["valid"]:
        raise AssertionError(f"pre-seal validation failed: {before['errors']}")
    sealed = seal_case(case_id, str(home))
    after = validate_case(case_id, str(home))
    if not sealed["valid"] or not after["valid"]:
        raise AssertionError(f"post-seal validation failed: {after['errors']}")
    mutation_blocked = False
    try:
        add_path(case_id, "must fail", [finding["id"]], home=str(home))
    except ReverseCraftError:
        mutation_blocked = True
    if not mutation_blocked:
        raise AssertionError("sealed case accepted a mutation")
    return {"id": scenario["id"], "route": scenario["expected_route"], "case_id": case_id, "report_sha256": report["sha256"], "sealed": True}


def main() -> int:
    scenario_paths = sorted((ROOT / "tests" / "scenarios").glob("*.json"))
    results: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="reverse-craft-scenarios-") as raw:
        root = Path(raw)
        for path in scenario_paths:
            workspace = root / "fixtures" / path.stem
            workspace.mkdir(parents=True)
            try:
                results.append(run_scenario(path, workspace, root / "home"))
            except Exception as exc:  # scenario runner must report all fixtures
                failures.append({"scenario": path.name, "error": f"{type(exc).__name__}: {exc}"})
    payload = {
        "schema": "reverse-craft.scenario-bank-result.v1",
        "scenarios": len(scenario_paths),
        "passed": len(results),
        "failed": len(failures),
        "results": results,
        "failures": failures,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if failures or len(scenario_paths) < 10 else 0


if __name__ == "__main__":
    raise SystemExit(main())

