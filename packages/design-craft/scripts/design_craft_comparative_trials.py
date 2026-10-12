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
    prepare_trial,
    validate_trial_set,
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

    # Validate every trial before touching aggregate.json, so a failed run
    # never removes a previously valid aggregate. A losing mean is recorded
    # as judged; certification is decided by the observed-evidence check.
    aggregate, errors = validate_trial_set(case_dir, require_current_source=True)
    if errors or aggregate is None:
        parser.error("; ".join(errors))
    path = case_dir / AGGREGATE_FILE
    path.write_text(
        json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
