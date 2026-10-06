#!/usr/bin/env python3
"""Scaffold a source-stamped, self-contained motion implementation plan."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_ROOT / "templates/motion-plan/plan.md"
SEVERITIES = ("P0", "P1", "P2", "P3")


def git_commit(target: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--short=12", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unversioned"


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:72]


def next_number(plan_dir: Path) -> int:
    numbers = []
    if plan_dir.is_dir():
        for path in plan_dir.glob("[0-9][0-9][0-9]-*.md"):
            try:
                numbers.append(int(path.name[:3]))
            except ValueError:
                continue
    return max(numbers, default=0) + 1


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    staged = Path(raw_path)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def render_plan(
    *,
    number: int,
    title: str,
    commit: str,
    severity: str,
    category: str,
) -> str:
    content = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{NUMBER}}": f"{number:03d}",
        "{{TITLE}}": title,
        "{{COMMIT}}": commit,
        "{{SEVERITY}}": severity,
        "{{CATEGORY}}": category,
    }
    for marker, value in replacements.items():
        content = content.replace(marker, value)
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="Project root that owns the plan.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug", help="ASCII filename slug; inferred from the title when possible.")
    parser.add_argument("--severity", choices=SEVERITIES, required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument(
        "--plan-dir",
        default="plans/motion",
        help="Project-relative plan directory, default plans/motion.",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        parser.error(f"target directory does not exist: {target}")
    relative_plan_dir = Path(args.plan_dir)
    if relative_plan_dir.is_absolute() or ".." in relative_plan_dir.parts:
        parser.error("--plan-dir must stay inside the target project")
    plan_dir = target / relative_plan_dir
    slug = slugify(args.slug or args.title)
    if not slug:
        parser.error("cannot infer an ASCII slug; pass --slug explicitly")
    number = next_number(plan_dir)
    path = plan_dir / f"{number:03d}-{slug}.md"
    if path.exists() and not args.force:
        parser.error(f"plan already exists: {path}")

    commit = git_commit(target)
    content = render_plan(
        number=number,
        title=args.title.strip(),
        commit=commit,
        severity=args.severity,
        category=args.category.strip(),
    )
    payload = {
        "schema": "design-craft.motion-plan-scaffold.v1",
        "target": str(target),
        "plan_dir": relative_plan_dir.as_posix(),
        "path": str(path),
        "commit": commit,
        "severity": args.severity,
        "category": args.category.strip(),
        "dry_run": args.dry_run,
        "index_update_required": True,
    }
    if not args.dry_run:
        atomic_write(path, content)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
