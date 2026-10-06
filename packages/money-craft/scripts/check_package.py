#!/usr/bin/env python3
"""Check npm package allowlist, size limits, and extracted runtime behavior."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAX_COMPRESSED_BYTES = 1 * 1024 * 1024
MAX_UNPACKED_BYTES = 2 * 1024 * 1024
MAX_FILES = 100
ALLOWED_PREFIXES = (
    ".env.example",
    ".codex-plugin/",
    ".claude-plugin/",
    ".grok-plugin/",
    "skills/money-craft/",
    "adapters/",
    "scripts/install_skill.py",
    "README.md",
    "LICENSE",
    "LICENSES/",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
    "sources.lock.json",
    "package.json",
)


def npm_dry_run() -> dict[str, Any]:
    completed = subprocess.run(
        ["npm", "pack", "--dry-run", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or "npm pack --dry-run failed")
    payload = json.loads(completed.stdout)
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        raise ValueError("unexpected npm pack --dry-run response")
    return payload[0]


def allowed(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def main() -> int:
    checks: list[str] = []
    errors: list[str] = []
    try:
        metadata = npm_dry_run()
        files = metadata.get("files")
        if not isinstance(files, list):
            raise ValueError("npm dry-run file inventory is missing")
        paths = [item.get("path") for item in files if isinstance(item, dict)]
        invalid = [path for path in paths if not isinstance(path, str) or not allowed(path)]
        if invalid:
            errors.append(f"package contains non-allowlisted paths: {invalid[:10]}")
        if len(paths) > MAX_FILES:
            errors.append(f"package has {len(paths)} files; limit is {MAX_FILES}")
        if int(metadata.get("size", 0)) > MAX_COMPRESSED_BYTES:
            errors.append("compressed package exceeds 1 MiB")
        if int(metadata.get("unpackedSize", 0)) > MAX_UNPACKED_BYTES:
            errors.append("unpacked package exceeds 2 MiB")
        if not errors:
            checks.append("npm-pack-allowlist-and-size")
        completed = subprocess.run(
            [sys.executable, "scripts/package_smoke.py", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        try:
            smoke = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"package smoke returned invalid JSON: {exc}") from exc
        if completed.returncode != 0 or smoke.get("valid") is not True:
            errors.extend(str(item) for item in smoke.get("errors", ["package smoke failed"]))
        else:
            checks.extend(smoke.get("checks", []))
    except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
        errors.append(str(exc))
    payload = {
        "schema": "money-craft.package-check.v1",
        "valid": not errors,
        "checks": checks,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
