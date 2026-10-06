#!/usr/bin/env python3
"""Verify installed skill files match freshly built self-contained bundles."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "skill-pack.json"
BUILDER = ROOT / "tooling/build/build_skill_bundles.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.installation.tree_integrity import (
    TreeIntegrityError,
    lexical_absolute,
    tree_hashes,
    validate_real_directory,
)
from tooling.manifest import ManifestError, load_manifest


def expand_root(value: str) -> Path:
    expanded = Path(os.path.expandvars(os.path.expanduser(value)))
    return lexical_absolute(expanded)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-root")
    parser.add_argument("--skill", action="append", default=[])
    args = parser.parse_args()

    try:
        manifest = load_manifest(MANIFEST)
    except (OSError, ManifestError) as exc:
        print(f"verify_install error: {exc}", file=sys.stderr)
        return 2
    selected = args.skill or [skill["name"] for skill in manifest["skills"]]
    known = {skill["name"] for skill in manifest["skills"]}
    unknown = sorted(set(selected) - known)
    if unknown:
        print(f"verify_install error: unknown skills: {', '.join(unknown)}", file=sys.stderr)
        return 2
    install_root = expand_root(args.install_root or manifest["default_install_root"])
    try:
        validate_real_directory(install_root)
    except TreeIntegrityError as exc:
        print(
            f"verify_install error: install root must be a real directory: {install_root}: {exc}",
            file=sys.stderr,
        )
        return 2

    with tempfile.TemporaryDirectory(prefix="skill-install-verify-") as temp:
        command = [sys.executable, str(BUILDER), "--output", temp]
        for name in selected:
            command.extend(["--skill", name])
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            return result.returncode

        failures = []
        for name in selected:
            built = Path(temp) / name
            installed = install_root / name
            if not os.path.lexists(installed):
                failures.append(f"missing installed skill: {installed}")
                continue
            if installed.is_symlink() or not installed.is_dir():
                failures.append(f"installed skill is not a real directory: {installed}")
                continue
            try:
                if tree_hashes(built) != tree_hashes(installed):
                    failures.append(f"installed content differs: {installed}")
            except (OSError, TreeIntegrityError) as exc:
                failures.append(f"installed content is invalid: {installed}: {exc}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 2
    print(f"installed parity passed: {len(selected)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
