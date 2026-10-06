from __future__ import annotations

import argparse
import json
from argparse import Namespace
from pathlib import Path

from ...repo import REPO_ROOT
from .profiles import PHASES, PROFILE_NAMES, check_profile_invariants
from .reporter import build_report
from .runner import evaluate_maturity


def run_maturity(args: Namespace, parser: argparse.ArgumentParser | None = None) -> int:
    if args.jobs < 0:
        if parser:
            parser.error("--jobs must be non-negative")
        raise ValueError("--jobs must be non-negative")
    if args.check:
        errors = check_profile_invariants()
        if errors:
            print("\n".join(errors))
            return 1
        return 0

    evaluation = evaluate_maturity(
        args.profile,
        phase=args.phase,
        baseline_path=args.baseline.expanduser().resolve() if args.baseline else None,
        benchmark_result_path=(
            args.benchmark_result.expanduser().resolve()
            if args.benchmark_result
            else None
        ),
        benchmark_observation_path=(
            args.benchmark_observation.expanduser().resolve()
            if args.benchmark_observation
            else None
        ),
        jobs=args.jobs,
    )
    report = build_report(evaluation, phase=args.phase, root=str(REPO_ROOT))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"design-craft maturity {args.profile}: {report['status']}")
        if report["release_level_score"] is not None:
            print(f"release level target: {report['release_level_score']}")
        for gate in report["gates"]:
            marker = "+" if gate["status"] == "passed" else "-"
            print(f"{marker} {gate['gate_id']}: {gate['status']} ({gate['duration_ms']:.3f} ms)")
            if gate["status"] != "passed" and gate["error"]:
                print(gate["error"])
    return 0 if report["ok"] else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate explicit development or release maturity contracts."
    )
    parser.add_argument("--profile", choices=PROFILE_NAMES, default="development")
    parser.add_argument("--phase", choices=PHASES, default="candidate")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--benchmark-result", type=Path)
    parser.add_argument("--benchmark-observation", type=Path)
    parser.add_argument("--jobs", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    return run_maturity(parser.parse_args(argv), parser)


if __name__ == "__main__":
    raise SystemExit(main())
