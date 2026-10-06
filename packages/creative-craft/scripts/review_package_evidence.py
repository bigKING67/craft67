#!/usr/bin/env python3
"""Build and exercise one exact package outside the repository for Review Craft."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []
    artifact: dict[str, Any] = {
        "path": None,
        "sha256": None,
        "size_bytes": None,
    }
    smoke: dict[str, Any] = {}
    output = Path(tempfile.mkdtemp(prefix="creative-craft-review-package-"))
    packed = subprocess.run(
        ["npm", "pack", "--pack-destination", str(output), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    package: Path | None = None
    if packed.returncode != 0:
        errors.append(packed.stderr.strip() or "npm pack failed without an error message")
    else:
        try:
            report = json.loads(packed.stdout)
            filename = report[0]["filename"]
            package = output / str(filename)
            if not package.is_file():
                raise ValueError(f"npm pack did not create {filename!r}")
        except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid npm pack report: {exc}")

    if package is not None:
        smoke_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/package_smoke.py"),
                "--package",
                str(package),
                "--json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        try:
            decoded = json.loads(smoke_result.stdout)
            if not isinstance(decoded, dict):
                raise TypeError("package smoke JSON must be an object")
            smoke = decoded
        except (TypeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid package smoke report: {exc}")
        if smoke_result.returncode != 0 or smoke.get("valid") is not True:
            errors.extend(str(item) for item in smoke.get("errors", []))
            if not smoke:
                errors.append(smoke_result.stderr.strip() or "package smoke failed")
        artifact = {
            "path": str(package),
            "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
            "size_bytes": package.stat().st_size,
        }

    valid = not errors and package is not None and smoke.get("valid") is True
    payload = {
        "schema_version": "creative-craft.review-package-evidence.v1",
        "valid": valid,
        "claims": {
            "package_safe": valid and "safe-package-extraction" in smoke.get("checks", []),
            "isolated_install": valid and "packaged-runtime-self-test" in smoke.get("checks", []),
            "runtime": valid and "packaged-reference-bind-update-e2e" in smoke.get("checks", []),
        },
        "artifact": artifact,
        "checks": smoke.get("checks", []),
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
