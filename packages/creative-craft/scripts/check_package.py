#!/usr/bin/env python3
"""Fail closed when the GitHub/Pi package boundary grows or leaks build residue."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from package_smoke import MAX_ARCHIVE_BYTES

ROOT = Path(__file__).resolve().parents[1]
# Re-measured 2026-10-02: 145,745 bytes packed.
MAX_PACKED_BYTES = 165_000
MAX_UNPACKED_BYTES = MAX_ARCHIVE_BYTES


def main() -> int:
    completed = subprocess.run(
        ["npm", "pack", "--dry-run", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        print(completed.stderr, file=sys.stderr)
        return completed.returncode
    try:
        items = json.loads(completed.stdout)
        package = items[0]
        paths = [item["path"] for item in package["files"]]
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid npm pack report: {exc}", file=sys.stderr)
        return 1
    errors: list[str] = []
    if package["size"] > MAX_PACKED_BYTES:
        errors.append(f"packed size {package['size']} exceeds {MAX_PACKED_BYTES}")
    if package["unpackedSize"] > MAX_UNPACKED_BYTES:
        errors.append(
            f"unpacked size {package['unpackedSize']} exceeds {MAX_UNPACKED_BYTES}"
        )
    forbidden = [
        path
        for path in paths
        if "__pycache__" in path or path.endswith((".pyc", ".pyo", ".DS_Store"))
    ]
    if forbidden:
        errors.append("forbidden package files: " + ", ".join(forbidden))
    required = {
        ".codex-plugin/plugin.json",
        "skills/creative-craft/SKILL.md",
        "skills/creative-craft/schemas/brand-binding.schema.json",
        "skills/creative-craft/schemas/brand-pack.schema.json",
        "skills/creative-craft/schemas/copy-sheet.schema.json",
        "skills/creative-craft/schemas/project-manifest-v2.schema.json",
        "skills/creative-craft/schemas/reference-binding.schema.json",
        "skills/creative-craft/schemas/reference-binding-history.schema.json",
        "skills/creative-craft/schemas/reference-pack.schema.json",
        "skills/creative-craft/references/copy-development.md",
        "skills/creative-craft/references/traceable-project.md",
        "skills/creative-craft/scripts/creative_craft.py",
        "skills/creative-craft/scripts/creative_craft_contracts.py",
        "skills/creative-craft/scripts/creative_craft_entrypoint.py",
        "skills/creative-craft/scripts/creative_craft_evaluation.py",
        "skills/creative-craft/scripts/creative_craft_packs.py",
        "skills/creative-craft/scripts/creative_craft_project.py",
        "skills/creative-craft/scripts/creative_craft_project_ops.py",
        "skills/creative-craft/scripts/creative_craft_runtime.py",
        "skills/creative-craft/scripts/creative_craft_video.py",
        "skills/creative-craft/templates/brand-binding.json",
        "skills/creative-craft/templates/brand-pack.json",
        "skills/creative-craft/templates/copy-sheet.json",
        "skills/creative-craft/templates/reference-binding.json",
        "skills/creative-craft/templates/reference-binding-history.json",
        "skills/creative-craft/templates/reference-pack.json",
        "skills/creative-craft/VERSION",
    }
    missing = sorted(required.difference(paths))
    if missing:
        errors.append("missing package files: " + ", ".join(missing))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "valid": True,
                "packed_bytes": package["size"],
                "unpacked_bytes": package["unpackedSize"],
                "entry_count": len(paths),
                "filename": package["filename"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
