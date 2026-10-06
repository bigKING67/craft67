from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT

from .contract import HOSTS, validate_definition_root
from .self_check import run_self_check
from .task import validate_observed_task


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate design-craft cross-agent benchmark tasks."
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Run built-in self-checks.")
    modes.add_argument("--root", help="Cross-agent benchmark root.")
    modes.add_argument("--observed-task", help="Validate one task with recorded outputs.")
    modes.add_argument(
        "--history-root",
        help=(
            "Validate immutable historical observed tasks without treating them "
            "as current source."
        ),
    )
    parser.add_argument(
        "--require-host",
        action="append",
        choices=HOSTS,
        default=[],
        help="Require this host to have a real output and score in --observed-task",
    )
    parser.add_argument(
        "--skill-root",
        help="Canonical skill root used only by --observed-task.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.observed_task and (args.require_host or args.skill_root):
        parser.error("--require-host and --skill-root require --observed-task")

    errors: list[str] = []
    if args.check:
        errors.extend(run_self_check())
    elif args.history_root:
        history_root = Path(args.history_root).expanduser().resolve()
        historical_tasks = sorted(
            path for path in history_root.rglob("same-prompt-*") if path.is_dir()
        )
        if not historical_tasks:
            errors.append(f"{history_root}: no historical observed tasks found")
        for task in historical_tasks:
            errors.extend(validate_observed_task(task, historical=True))
    elif args.observed_task:
        errors.extend(
            validate_observed_task(
                Path(args.observed_task),
                tuple(args.require_host),
                skill_root=(
                    Path(args.skill_root).expanduser().resolve()
                    if args.skill_root
                    else REPO_ROOT / "skills/design-craft"
                ),
                require_current_schema=True,
                require_current_source=True,
                require_any_observed=True,
            )
        )
    else:
        errors.extend(
            validate_definition_root(Path(args.root or "evals/cross-agent"))
        )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0
