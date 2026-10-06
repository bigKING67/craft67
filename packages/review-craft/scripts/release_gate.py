#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BASE_COMMANDS = (
    (
        "complexity budget",
        ["uv", "run", "--locked", "python", "scripts/complexity_budget.py"],
    ),
    (
        "tests",
        [
            "uv",
            "run",
            "--locked",
            "python",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_*.py",
        ],
    ),
    ("source validation", ["uv", "run", "--locked", "python", "scripts/validate.py"]),
    ("lint", ["uv", "run", "--locked", "ruff", "check", "."]),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Review Craft release contract")
    parser.add_argument("--package-output", help="Preserve the exact validated npm tarball")
    parser.add_argument("--package-receipt", help="Write the exact package validation receipt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    package_command = [sys.executable, "scripts/package_check.py"]
    if args.package_output:
        package_command.extend(["--output-tarball", args.package_output])
    if args.package_receipt:
        package_command.extend(["--receipt", args.package_receipt])
    commands = (*BASE_COMMANDS, ("exact installed package", package_command))
    for name, command in commands:
        print(f"==> {name}", flush=True)
        completed = subprocess.run(command, cwd=ROOT, env=environment)
        if completed.returncode != 0:
            print(f"release gate failed at {name}", file=sys.stderr)
            return completed.returncode
    print("review-craft release gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
