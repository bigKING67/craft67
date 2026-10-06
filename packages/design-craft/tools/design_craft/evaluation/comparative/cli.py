from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .case import validate_case
from .definition import active_cases, validate_definition
from .self_check import run_self_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate comparative ablation definitions, isolated runs, blind "
            "judge, and result."
        )
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--root")
    modes.add_argument("--case-dir")
    modes.add_argument(
        "--history-root",
        help=(
            "Validate archived observed cases without accepting them as "
            "current-source evidence."
        ),
    )
    modes.add_argument("--check", action="store_true")
    parser.add_argument("--require-observed", action="store_true")
    parser.add_argument(
        "--definitions-only",
        action="store_true",
        help=(
            "Validate active case definitions without admitting or rejecting "
            "recorded evidence."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.check and args.require_observed:
        parser.error("--require-observed is not valid with --check")
    if args.definitions_only and (
        args.check or args.history_root or args.require_observed
    ):
        parser.error(
            "--definitions-only is not valid with --check, --history-root, or "
            "--require-observed"
        )
    if args.check:
        errors = run_self_check()
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print("comparative_validator_self_check=ok")
        return 0
    errors: list[str] = []
    history_mode = bool(args.history_root)
    if args.case_dir:
        cases = [Path(args.case_dir).expanduser().resolve()]
    elif history_mode:
        history_root = Path(args.history_root).expanduser().resolve()
        cases = sorted(path.parent for path in history_root.rglob("variants.json"))
    else:
        root = Path(args.root or "evals/comparative").expanduser().resolve()
        cases = active_cases(root)
    if not cases:
        errors.append("at least one comparative case is required")
    for case in cases:
        if args.definitions_only:
            _, _, definition_errors = validate_definition(case)
            errors.extend(definition_errors)
        else:
            errors.extend(
                validate_case(
                    case,
                    require_observed=True if history_mode else args.require_observed,
                    require_current_source=not history_mode,
                )
            )
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0
