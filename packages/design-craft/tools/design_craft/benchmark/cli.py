from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from .contract import compare_results, migrate_v1_result
from .runner import run_suite


def run_benchmark(args: Namespace) -> int:
    if args.migrate_v1:
        required = {
            "--output": args.output,
            "--runner-image": args.runner_image,
            "--image-version": args.image_version,
            "--node-version": args.node_version,
        }
        missing = [flag for flag, value in required.items() if not value]
        if missing:
            raise ValueError("v1 benchmark migration requires " + ", ".join(missing))
        source = Path(args.migrate_v1).expanduser().resolve()
        output = Path(args.output).expanduser().resolve()
        if output.exists() or output.is_symlink():
            raise ValueError(f"benchmark migration output already exists: {output}")
        migrated = migrate_v1_result(
            json.loads(source.read_text(encoding="utf-8")),
            runner_image=args.runner_image,
            image_version=args.image_version,
            node_version=args.node_version,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(migrated, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if args.json:
            print(json.dumps(migrated, indent=2, sort_keys=True))
        else:
            print(f"benchmark baseline migrated explicitly: {source} -> {output}")
        return 0
    current = run_suite(args.scale)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload: dict[str, object] = current
    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        payload = compare_results(baseline, current)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if args.baseline:
            print(f"benchmark regression: {'pass' if payload['ok'] else 'fail'}")
            for warning in payload.get("warnings", []):
                print(f"- warning: {warning}")
            for error in payload.get("errors", []):
                print(f"- {error}")
        else:
            print(f"benchmark suite completed: {len(current['metrics'])} metrics")
    return 0 if payload.get("ok", True) else 1
