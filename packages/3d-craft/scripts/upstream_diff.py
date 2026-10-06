#!/usr/bin/env python3
"""Compare reviewed upstream paths with a candidate Git revision.

The script is deliberately offline: callers provide an existing checkout that
contains both the locked commit and candidate revision. It never fetches,
installs, authenticates, or mutates the checkout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA = "3d-craft.upstream-diff.v1"


class AuditError(RuntimeError):
    """Raised when the requested comparison cannot be proven."""


def git(checkout: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise AuditError(f"git {' '.join(args)}: {detail}")
    return completed.stdout.strip()


def normalize_github_remote(value: str) -> str:
    normalized = value.strip().removesuffix(".git").rstrip("/")
    if normalized.startswith("git@github.com:"):
        normalized = "https://github.com/" + normalized.removeprefix("git@github.com:")
    elif normalized.startswith("ssh://git@github.com/"):
        normalized = "https://github.com/" + normalized.removeprefix("ssh://git@github.com/")
    return normalized.lower()


def expected_remote(repo: str) -> str:
    return f"https://github.com/{repo}".lower()


def resolve_commit(checkout: Path, revision: str) -> str:
    commit = git(checkout, "rev-parse", "--verify", f"{revision}^{{commit}}")
    if len(commit) != 40:
        raise AuditError(f"revision did not resolve to a full commit: {revision}")
    return commit


def blob_id(checkout: Path, commit: str, path: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "--verify", f"{commit}:{path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def load_entry(lock_file: Path, repo: str) -> dict[str, Any]:
    try:
        lock = json.loads(lock_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AuditError(f"cannot read lock file {lock_file}: {error}") from error
    matches = [item for item in lock.get("upstreams", []) if item.get("repo") == repo]
    if len(matches) != 1:
        raise AuditError(f"expected exactly one lock entry for {repo}, found {len(matches)}")
    entry = matches[0]
    strategy = entry.get("freshness", {}).get("strategy")
    if strategy != "target-path-git-blob":
        raise AuditError(f"{repo} uses unsupported offline Git freshness strategy: {strategy!r}")
    if not entry.get("source_paths"):
        raise AuditError(f"{repo} has no tracked source_paths")
    return entry


def compare(lock_file: Path, repo: str, checkout: Path, revision: str) -> dict[str, Any]:
    if not checkout.is_dir():
        raise AuditError(f"checkout directory does not exist: {checkout}")
    if git(checkout, "rev-parse", "--is-inside-work-tree") != "true":
        raise AuditError(f"not a Git worktree: {checkout}")

    origin = git(checkout, "remote", "get-url", "origin")
    if normalize_github_remote(origin) != expected_remote(repo):
        raise AuditError(f"origin mismatch for {repo}: {origin}")

    entry = load_entry(lock_file, repo)
    locked_commit = resolve_commit(checkout, entry["commit"])
    candidate_commit = resolve_commit(checkout, revision)
    paths: list[dict[str, Any]] = []
    relevant_change = False

    for source_path in entry["source_paths"]:
        locked_blob = blob_id(checkout, locked_commit, source_path)
        candidate_blob = blob_id(checkout, candidate_commit, source_path)
        if locked_blob is None:
            raise AuditError(f"locked source path cannot be resolved: {source_path}")
        if candidate_blob is None:
            state = "REMOVED"
            relevant_change = True
        elif locked_blob == candidate_blob:
            state = "SAME"
        else:
            state = "CHANGED"
            relevant_change = True
        paths.append(
            {
                "path": source_path,
                "status": state,
                "locked_blob": locked_blob,
                "candidate_blob": candidate_blob,
            }
        )

    if candidate_commit == locked_commit:
        status = "CURRENT"
    elif relevant_change:
        status = "TARGET_PATH_CHANGED"
    else:
        status = "HEAD_ONLY_CHANGED"

    return {
        "schema": SCHEMA,
        "status": status,
        "repo": repo,
        "checkout": str(checkout.resolve()),
        "origin": origin,
        "lock_file": str(lock_file.resolve()),
        "locked_commit": locked_commit,
        "candidate_revision": revision,
        "candidate_commit": candidate_commit,
        "paths": paths,
    }


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"{payload['status']}: {payload['repo']}",
        f"locked:    {payload.get('locked_commit', 'UNVERIFIED')}",
        f"candidate: {payload.get('candidate_commit', 'UNVERIFIED')}",
    ]
    for item in payload.get("paths", []):
        lines.append(f"{item['status']:>7}  {item['path']}")
    if payload.get("error"):
        lines.append(f"error: {payload['error']}")
    return "\n".join(lines)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Compare locked upstream source-path blobs with an existing checkout revision."
    )
    parser.add_argument("--repo", required=True, help="GitHub owner/repository from upstreams.lock.json")
    parser.add_argument("--checkout", required=True, help="Existing offline Git checkout")
    parser.add_argument("--revision", default="HEAD", help="Candidate revision in the checkout (default: HEAD)")
    parser.add_argument("--lock-file", default=str(root / "upstreams.lock.json"), help="Upstream lock JSON")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    try:
        payload = compare(
            Path(args.lock_file).expanduser().resolve(),
            args.repo,
            Path(args.checkout).expanduser().resolve(),
            args.revision,
        )
    except AuditError as error:
        payload = {
            "schema": SCHEMA,
            "status": "UNVERIFIED",
            "repo": args.repo,
            "checkout": str(Path(args.checkout).expanduser().resolve()),
            "lock_file": str(Path(args.lock_file).expanduser().resolve()),
            "candidate_revision": args.revision,
            "error": str(error),
            "paths": [],
        }

    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else render_text(payload))
    if payload["status"] in {"CURRENT", "HEAD_ONLY_CHANGED"}:
        return 0
    if payload["status"] == "TARGET_PATH_CHANGED":
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
