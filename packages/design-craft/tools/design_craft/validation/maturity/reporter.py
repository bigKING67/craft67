from __future__ import annotations

from dataclasses import asdict


SCHEMA = "design-craft.maturity.v2"


def build_report(evaluation: dict[str, object], *, phase: str, root: str) -> dict[str, object]:
    profile = evaluation["profile"]
    results = evaluation["results"]
    failed = evaluation["failed_gate_ids"]
    unverified = {
        target: "explicitly_unverified"
        for target in profile.allowed_unverified
    }
    return {
        "schema": SCHEMA,
        "profile": profile.name,
        "scope": profile.scope,
        "phase": phase,
        "root": root,
        "release_level_score": profile.release_level_score,
        "metric_policy": "all_required_gates_no_partial_composite_score",
        "status": "passed" if evaluation["ok"] else "failed",
        "ok": evaluation["ok"],
        "required_gate_count": len(results),
        "passed_gate_count": len(results) - len(failed),
        "failed_gate_ids": failed,
        "unverified": unverified,
        "gates": [asdict(result) for result in results],
    }
