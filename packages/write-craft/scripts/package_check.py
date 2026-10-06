#!/usr/bin/env python3
"""Verify the npm/Pi package boundary without creating an archive."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_FILES = {
    "package.json",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
}
ALLOWED_PREFIXES = ("LICENSES/", "skills/write-craft/")
REQUIRED_PATHS = {
    "package.json",
    "README.md",
    "LICENSE",
    "LICENSES/agent-skills-MIT.txt",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
    "skills/write-craft/SKILL.md",
    "skills/write-craft/VERSION",
    "skills/write-craft/agents/openai.yaml",
    "skills/write-craft/references/clear-chinese.md",
    "skills/write-craft/references/decision-documents.md",
    "skills/write-craft/references/document-presentation.md",
    "skills/write-craft/references/reader-testing.md",
    "skills/write-craft/references/source-integrity.md",
    "skills/write-craft/references/source-map.md",
}
FORBIDDEN_PARTS = {"__pycache__"}
MAX_ENTRIES = 24
MAX_UNPACKED_BYTES = 250_000


def validate_pack(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        return ["npm pack --dry-run must return one package result"]
    result = payload[0]
    files = result.get("files")
    if not isinstance(files, list):
        return ["npm pack result is missing a files array"]
    paths = {
        item.get("path")
        for item in files
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    if len(paths) > MAX_ENTRIES:
        errors.append(f"package entry count must be <= {MAX_ENTRIES}")
    unpacked = result.get("unpackedSize")
    if not isinstance(unpacked, int) or unpacked > MAX_UNPACKED_BYTES:
        errors.append(f"unpacked package must be <= {MAX_UNPACKED_BYTES} bytes")
    missing = REQUIRED_PATHS - paths
    if missing:
        errors.append(f"package is missing required paths: {sorted(missing)}")
    for raw_path in sorted(paths):
        path = PurePosixPath(raw_path)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            errors.append(f"unsafe package path: {raw_path}")
            continue
        if any(part in FORBIDDEN_PARTS for part in path.parts) or path.suffix in {".pyc", ".pyo"}:
            errors.append(f"generated cache leaked into package: {raw_path}")
        if raw_path not in ALLOWED_ROOT_FILES and not raw_path.startswith(ALLOWED_PREFIXES):
            errors.append(f"path is outside the public package boundary: {raw_path}")
    return errors


def main() -> int:
    completed = subprocess.run(
        ["npm", "pack", "--dry-run", "--json", "--ignore-scripts"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        print("FAIL Write Craft package boundary")
        print("  ERROR: " + (completed.stderr.strip() or completed.stdout.strip()))
        return 1
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        print("FAIL Write Craft package boundary")
        print(f"  ERROR: invalid npm JSON: {exc}")
        return 1
    errors = validate_pack(payload)
    if errors:
        print("FAIL Write Craft package boundary")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1
    result = payload[0]
    print("PASS Write Craft package boundary")
    print(f"  PASS: {len(result['files'])} entries")
    print(f"  PASS: {result['unpackedSize']} unpacked bytes")
    print("  PASS: upstream, development, test, and evaluation files excluded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
