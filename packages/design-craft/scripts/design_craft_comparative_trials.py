#!/usr/bin/env python3
"""Prepare repeated comparative trials and record their hash-bound aggregate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.design_craft.evaluation.comparative.trials import (  # noqa: E402
    AGGREGATE_FILE,
    build_aggregate,
    prepare_trial,
    validate_trials,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser(
        "prepare", help="Copy the case definition into trials/<n>/<case-id>/."
    )
    prepare.add_argument("--case-dir", required=True)
    prepare.add_argument("--trial", type=int, required=True)
    aggregate = commands.add_parser(
        "aggregate", help="Validate every trial and write aggregate.json."
    )
    aggregate.add_argument("--case-dir", required=True)
    args = parser.parse_args(argv)
    case_dir = Path(args.case_dir).expanduser().resolve()

    if args.command == "prepare":
        try:
            print(prepare_trial(case_dir, args.trial))
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        return 0

    # Write first so validation compares the file against a fresh rebuild.
    path = case_dir / AGGREGATE_FILE
    path.write_text(
        json.dumps(build_aggregate(case_dir), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    errors = [
        error
        for error in validate_trials(case_dir, require_current_source=True)
        if "certification requires" not in error
    ]
    if errors:
        path.unlink()
        parser.error("; ".join(errors))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
