from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from ..repo import REPO_ROOT
from .repository_contracts import RELEASE_TARGETS


SCHEMA = "design-craft.tooling-contracts.v1"
MAKE_TARGETS = (
    "validate",
    "validate-portable",
    "lint",
    "contract-tests",
    "release-gate-source",
    "publish-local",
    "sync-status",
    "native-release-bundle-check",
    "codex-route-pack-check",
    "codex-route-pack-host-check",
    *RELEASE_TARGETS,
)


def _run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def validate(root: Path = REPO_ROOT) -> dict[str, object]:
    errors: list[str] = []
    script_roots = (root / "scripts", root / "skills/design-craft/scripts")
    executable_count = 0
    for script_root in script_roots:
        for path in sorted(script_root.iterdir()):
            if not path.is_file() or path.suffix not in {".py", ".sh"}:
                continue
            executable_count += 1
            if not os.access(path, os.X_OK):
                errors.append(f"script must be executable: {path.relative_to(root)}")

    make_result = _run(["make", "-n", *MAKE_TARGETS], root)
    if make_result.returncode != 0:
        errors.append(make_result.stderr.strip() or "Make target topology failed")

    node_result = _run(["node", "--check", ".github/scripts/upstream_review_issue.cjs"], root)
    if node_result.returncode != 0:
        errors.append(node_result.stderr.strip() or "upstream review issue helper syntax failed")

    return {
        "schema": SCHEMA,
        "root": str(root),
        "executable_script_count": executable_count,
        "make_target_count": len(MAKE_TARGETS),
        "ok": not errors,
        "errors": errors,
    }


def self_check() -> None:
    if len(MAKE_TARGETS) != len(set(MAKE_TARGETS)):
        raise RuntimeError("tooling contract Make target list contains duplicates")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.check:
        self_check()
    payload = validate()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif payload["ok"]:
        print(
            "tooling contracts verified: "
            f"{payload['executable_script_count']} scripts, {payload['make_target_count']} Make targets"
        )
    else:
        print("\n".join(payload["errors"]), file=sys.stderr)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
