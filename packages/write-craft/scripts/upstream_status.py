#!/usr/bin/env python3
"""Report pinned upstream checkout and optional remote-HEAD status."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, text=True, capture_output=True, check=False
    )


def inspect(remote: bool) -> dict[str, object]:
    lock = json.loads((ROOT / "upstreams.lock.json").read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    local_valid = True
    remote_current = True
    for name, entry in sorted(lock["upstreams"].items()):
        checkout = ROOT / entry["path"]
        row: dict[str, object] = {
            "name": name,
            "path": entry["path"],
            "pinned_commit": entry["commit"],
            "decision": entry["decision"],
        }
        if not checkout.is_dir():
            row.update(local_status="missing", local_commit=None, dirty=None)
            local_valid = False
        else:
            head = run("git", "rev-parse", "HEAD", cwd=checkout)
            dirty = run("git", "status", "--porcelain", cwd=checkout)
            local_commit = head.stdout.strip() if head.returncode == 0 else None
            is_dirty = dirty.returncode != 0 or bool(dirty.stdout.strip())
            matches = local_commit == entry["commit"] and not is_dirty
            row.update(
                local_status="current" if matches else "mismatch",
                local_commit=local_commit,
                dirty=is_dirty,
            )
            local_valid = local_valid and matches
        if remote:
            result = run("git", "ls-remote", entry["repo"], "HEAD")
            remote_head = (
                result.stdout.split()[0]
                if result.returncode == 0 and result.stdout.split()
                else None
            )
            current = remote_head == entry["commit"]
            row.update(
                remote_status=(
                    "current" if current else "advanced" if remote_head else "unavailable"
                ),
                remote_head=remote_head,
            )
            remote_current = remote_current and current
        rows.append(row)
    return {
        "schema": "write-craft.upstream-status.v1",
        "local_valid": local_valid,
        "remote_checked": remote,
        "remote_current": remote_current if remote else None,
        "upstreams": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote", action="store_true", help="compare pins with remote HEAD")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = inspect(args.remote)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for row in payload["upstreams"]:
            suffix = f" remote={row.get('remote_status')}" if args.remote else ""
            print(f"{row['name']}: local={row['local_status']}{suffix}")
    if not payload["local_valid"]:
        return 1
    if args.remote and not payload["remote_current"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
