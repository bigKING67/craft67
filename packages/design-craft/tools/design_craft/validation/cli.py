from __future__ import annotations

import json
import time
from argparse import Namespace
from dataclasses import asdict

from .profile_contract import require_profile_contract
from .registry import load_registry, select_gates
from .runner import run_gates


OUTPUT_SCHEMA = "design-craft.validation-run.v2"


def run_validate(args: Namespace) -> int:
    gates = select_gates(load_registry(), args.profile)
    require_profile_contract(gates, args.profile)
    if args.list:
        payload = {
            "schema": OUTPUT_SCHEMA,
            "profile": args.profile,
            "status": "listed",
            "gates": [gate.gate_id for gate in gates],
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            for gate in gates:
                print(gate.gate_id)
        return 0

    started = time.perf_counter()
    results = run_gates(gates, jobs=args.jobs)
    wall_duration_ms = (time.perf_counter() - started) * 1_000
    passed = all(result.passed for result in results)
    payload = {
        "schema": OUTPUT_SCHEMA,
        "profile": args.profile,
        "status": "passed" if passed else "failed",
        "gate_count": len(results),
        "duration_ms": round(wall_duration_ms, 3),
        "gate_duration_sum_ms": round(
            sum(result.duration_ms for result in results), 3
        ),
        "results": [asdict(result) for result in results],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for result in results:
            marker = "+" if result.passed else "-"
            print(f"{marker} {result.gate_id}: {result.status} ({result.duration_ms:.3f} ms)")
            if not result.passed:
                detail = result.stderr_summary or result.stdout_summary
                if detail:
                    print(detail)
        print(f"design-craft validation {payload['status']}: {len(results)} gates")
    return 0 if passed else 1
