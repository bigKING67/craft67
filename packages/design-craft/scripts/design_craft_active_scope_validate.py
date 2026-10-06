#!/usr/bin/env python3
"""Validate that active design-craft surfaces stay project-neutral."""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ACTIVE_FILES = [
    "README.md",
    "Makefile",
    "adapters/codex/README.md",
    "adapters/codex/route-pack/README.md",
    "docs/maintenance.md",
    "scripts/design_craft_codex_route_pack.py",
    "scripts/design_craft_doctor.sh",
    "scripts/design_craft_score.py",
    "scripts/validate.sh",
    "skills/design-craft/scripts/design_craft_l4_capture.py",
    "scripts/design_craft_cross_agent_validate.py",
    "skills/design-craft/SKILL.md",
    "skills/design-craft/references/report-quality.md",
    "skills/design-craft/references/surface-playbooks.md",
    "skills/design-craft/references/source-map.md",
    "skills/design-craft/references/validation-contract.md",
    "evals/golden-tasks/generic-review-workbench.md",
    "evals/product-ui-taste/before-after/README.md",
    "evals/cross-agent/README.md",
]
CROSS_AGENT_ACTIVE_FILES = (
    "prompt.md",
    "expected-findings.md",
    "scorecard.json",
    "evidence-status.json",
)


MARKER_FRAGMENTS = [
    ("data", "hub"),
    ("gro", "land"),
    ("live", "-center"),
    ("content", "-assets"),
]


@dataclass(frozen=True)
class Finding:
    path: Path
    marker: str


def markers() -> list[str]:
    return ["".join(parts).lower() for parts in MARKER_FRAGMENTS]


def find_markers(path: Path, text: str) -> list[Finding]:
    lowered = text.lower()
    return [Finding(path=path, marker=marker) for marker in markers() if marker in lowered]


def validate_paths(root: Path, rel_paths: list[str]) -> list[str]:
    errors: list[str] = []
    for rel_path in rel_paths:
        path = root / rel_path
        if not path.is_file():
            errors.append(f"{rel_path}: missing active scope file")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{rel_path}: unable to read as UTF-8: {exc}")
            continue
        for finding in find_markers(Path(rel_path), text):
            errors.append(
                f"{finding.path}: active generic surface mentions project-specific marker "
                f"{finding.marker!r}"
            )
    return errors


def active_paths(root: Path) -> list[str]:
    task_files: list[str] = []
    for task in sorted((root / "evals/cross-agent").glob("same-prompt-*")):
        if task.is_dir():
            task_files.extend(
                str((task / name).relative_to(root))
                for name in CROSS_AGENT_ACTIVE_FILES
            )
    return [*ACTIVE_FILES, *task_files]


def self_check() -> int:
    with tempfile.TemporaryDirectory(prefix="design-craft-active-scope.") as tmp:
        root = Path(tmp)
        generic = root / "generic.md"
        blocked = root / "blocked.md"
        generic.write_text(
            "Dashboard exports, formal reports, and evidence-heavy UI surfaces.\n",
            encoding="utf-8",
        )
        blocked.write_text("This generic active file mentions " + "".join(("data", "hub")) + ".\n", encoding="utf-8")

        generic_errors = validate_paths(root, ["generic.md"])
        if generic_errors:
            print("Generic self-check unexpectedly failed:", file=sys.stderr)
            print("\n".join(generic_errors), file=sys.stderr)
            return 1

        blocked_errors = validate_paths(root, ["blocked.md"])
        if not blocked_errors:
            print("Blocked self-check unexpectedly passed.", file=sys.stderr)
            return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate active design-craft docs and gates are project-neutral."
    )
    parser.add_argument("--root", default=".", help="design-craft repository root.")
    parser.add_argument("--check", action="store_true", help="Run built-in self-check fixtures.")
    args = parser.parse_args()

    if args.check:
        return self_check()

    root = Path(args.root).expanduser().resolve()
    paths = active_paths(root)
    errors = validate_paths(root, paths)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"active scope validation passed: {len(paths)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
