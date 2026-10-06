#!/usr/bin/env python3
"""Dependency-free fallback validator for skill bundles in CI environments."""

from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate(root: Path) -> None:
    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        raise ValueError("SKILL.md is required")
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not NAME_RE.fullmatch(name):
        raise ValueError(f"invalid skill name: {name!r}")
    if root.name != name:
        raise ValueError(f"folder/name mismatch: {root.name!r} != {name!r}")
    if not description:
        raise ValueError("description is required")
    if len(description) > 500:
        raise ValueError("description exceeds 500 characters")
    if not (root / "agents/openai.yaml").is_file():
        raise ValueError("agents/openai.yaml is required")
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("skill bundle must not contain symlinks")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: quick_validate_skill.py <skill-dir>", file=sys.stderr)
        return 2
    try:
        validate(Path(sys.argv[1]).resolve())
        print("Skill is valid!")
        return 0
    except (OSError, ValueError) as exc:
        print(f"skill validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
