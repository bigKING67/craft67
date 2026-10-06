#!/usr/bin/env python3
"""Run Creative Craft's portable source, artifact, and unit-test gates."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "creative-craft" / "scripts" / "creative_craft.py"


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main() -> int:
    run(str(CLI), "doctor")
    run(str(CLI), "validate-project", "--root", str(ROOT / "examples/premium-haircare-launch"))
    # Exits non-zero on digest drift between production.json and its bound artifacts.
    run(str(CLI), "video-status", "--root", str(ROOT / "examples/talking-head-broll-cut"))

    artifact_dirs = [
        ROOT / "skills" / "creative-craft" / "templates",
        ROOT / "examples",
        ROOT / "tests" / "fixtures",
    ]
    for directory in artifact_dirs:
        for path in sorted(directory.rglob("*.json")):
            # Provider profiles and source locks are repository metadata, not job artifacts.
            if "providers" in path.parts or path.name == "sources.lock.json":
                continue
            if "invalid" in path.parts:
                # Semantic-negative fixtures: schema-valid, but validation must reject them.
                rejected = subprocess.run(
                    [sys.executable, str(CLI), "validate", "--file", str(path)],
                    cwd=ROOT,
                    capture_output=True,
                    check=False,
                ).returncode
                if rejected == 0:
                    raise SystemExit(f"expected validation to reject {path.relative_to(ROOT)}")
                continue
            run(str(CLI), "validate", "--file", str(path))

    run("scripts/benchmark_unique_items.py")
    run("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py")
    print("Creative Craft validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
