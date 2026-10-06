from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from .report import build_quality_report


def run_quality(args: Namespace) -> int:
    payload = build_quality_report(
        baseline_path=Path(args.baseline).expanduser().resolve() if args.baseline else None,
        release_level=args.level,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for name, domain in payload["domains"].items():
            print(f"{name}: {domain['status']}")
        print("composite score: intentionally not computed")
    return 0 if payload["ok"] else 1
