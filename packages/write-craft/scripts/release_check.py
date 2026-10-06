#!/usr/bin/env python3
"""Fail closed unless behavior evidence matches the current release candidate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate import validate_release_evidence


def main() -> int:
    errors = validate_release_evidence()
    if not errors:
        package_check = subprocess.run(
            [sys.executable, "scripts/package_check.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if package_check.returncode != 0:
            errors.append(
                "package boundary check failed: "
                + (package_check.stdout.strip() or package_check.stderr.strip())
            )
    if errors:
        print("FAIL Write Craft release evidence")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1
    print("PASS Write Craft release evidence")
    print("  PASS: current Skill digest matches the versioned baseline")
    print("  PASS: every regression case has bound PASS evidence")
    print("  PASS: exploration results or NOT_RUN are disclosed")
    print("  PASS: judge calibration and human acceptance are bound")
    print("  PASS: deterministic delivery limits match recorded candidates")
    print("  PASS: package boundary check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
