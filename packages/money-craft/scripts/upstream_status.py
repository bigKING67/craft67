#!/usr/bin/env python3
"""Report pinned, absorbed, classified-review, local, and remote upstream commits."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from upstream_sources import make_snapshot, source_status, utc_now, validate_tracking

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstreams" / "ai-berkshire"
LOCK_PATH = ROOT / "sources.lock.json"


def git(*args: str, check: bool = True, strip: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=UPSTREAM,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip() if strip else completed.stdout


def changed_paths(from_commit: str, through_commit: str) -> list[str]:
    if from_commit == through_commit:
        return []
    raw = git(
        "-c",
        "core.quotePath=false",
        "diff",
        "--name-only",
        "-z",
        f"{from_commit}..{through_commit}",
        strip=False,
    )
    return [path for path in raw.split("\0") if path]


def category(path: str) -> str:
    if path.startswith(("skills/", "codex-skills/", "codex-prompts/")):
        return "skills"
    if path.startswith("tools/") or path.startswith("scripts/"):
        return "tools"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith(("reports/", "data/", "assets/", "实盘记录/")):
        return "excluded-content"
    if path.endswith(".md"):
        return "documentation"
    return "other"


def build_status(fetch: bool) -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    entry = next(item for item in lock["upstreams"] if item["id"] == "ai-berkshire")
    if not (UPSTREAM / ".git").exists() and not UPSTREAM.is_dir():
        raise ValueError("AI Berkshire submodule is not initialized")
    if fetch:
        git("fetch", "--quiet", "origin", "main")
    local = git("rev-parse", "HEAD")
    remote = git("rev-parse", "origin/main")
    reviewed = entry["reviewed_commit"]
    reviews = entry.get("reviews", [])
    review_baseline = reviews[-1]["through_commit"] if reviews else reviewed
    changed_files = changed_paths(review_baseline, remote)
    categories: dict[str, int] = {}
    for path in changed_files:
        key = category(path)
        categories[key] = categories.get(key, 0) + 1
    if local != entry["pinned_commit"]:
        state = "submodule_mismatch"
    elif remote != review_baseline:
        state = "review_required"
    else:
        state = "current"
    return {
        "schema": "money-craft.upstream-status.v1",
        "state": state,
        "fetched": fetch,
        "pinned_commit": entry["pinned_commit"],
        "reviewed_commit": reviewed,
        "review_baseline_commit": review_baseline,
        "absorbed_commit": entry["absorbed_commit"],
        "local_commit": local,
        "remote_commit": remote,
        "changed_file_count": len(changed_files),
        "changed_categories": categories,
        "changed_files": changed_files,
        "automatic_merge": False,
    }


def build_all_status(fetch: bool, snapshots: list[dict[str, Any]] | None = None,
                     source_ids: list[str] | None = None) -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    errors = validate_tracking(lock, ROOT)
    if errors:
        raise ValueError("; ".join(errors))
    sources = {source["id"]: source for source in lock.get("reference_tracking", {}).get("sources", [])}
    available = {"ai-berkshire", *sources}
    selected = set(source_ids) if source_ids else available
    if not selected.issubset(available):
        raise ValueError("unknown source id")
    captures = {}
    capture_errors = []
    for index, capture in enumerate(snapshots or []):
        if not isinstance(capture, dict) or not isinstance(capture.get("source_id"), str):
            capture_errors.append({"index": index, "reason": "capture is not an object with a source_id; other sources continue"})
            continue
        sid = capture["source_id"]
        if sid not in selected:
            capture_errors.append({"index": index, "reason": "capture source is not selected; other sources continue"})
            continue
        if sid == "ai-berkshire" or sources[sid]["kind"] != "docs":
            capture_errors.append({"index": index, "reason": "capture source must be a documentation source"})
            continue
        if sid in captures:
            captures[sid] = {}  # Reject ambiguity; never silently select one capture.
            capture_errors.append({"index": index, "reason": "duplicate source captures are ambiguous"})
            continue
        captures[sid] = capture
    results = []
    for sid in sorted(selected):
        try:
            if sid == "ai-berkshire":
                result = build_status(fetch)
                result.update(id=sid, kind="git", role="existing-method-source",
                              evidence="live" if fetch else "cached", checked_at=utc_now() if fetch else None)
                if result["state"] == "current" and not fetch:
                    result["state"] = "cached"
            else:
                result = source_status(sources[sid], fetch, captures.get(sid))
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            # Network exceptions may include URLs or response content. Do not echo them.
            result = {"id": sid, "state": "unavailable", "evidence": "failed",
                      "error_type": type(exc).__name__,
                      "reason": str(exc) if isinstance(exc, ValueError) else "source observation failed; no review state advanced"}
        results.append(result)
    states = {item["state"] for item in results}
    if capture_errors:
        state = "partial"
    elif states.intersection({"unavailable", "error", "submodule_mismatch"}):
        state = "unavailable" if states == {"unavailable"} else "partial"
    elif "review_required" in states:
        state = "review_required"
    elif states == {"current"}:
        state = "current"
    else:
        state = "stale" if "stale" in states else "cached"
    return {"schema": "money-craft.upstream-status.v2", "state": state, "sources": results,
            "source_count": len(results), "capture_errors": capture_errors,
            "automatic_merge": False, "review_state_mutated": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true", help="check all registered reference sources and AI Berkshire")
    parser.add_argument("--source", action="append", help="select a source (repeatable); uses v2 output")
    parser.add_argument("--snapshot", type=Path, action="append", default=[], help="import a complete public browser capture")
    parser.add_argument("--snapshot-only", type=Path, help="validate a capture and emit metadata-only snapshot; does not update lock")
    args = parser.parse_args()
    try:
        if args.snapshot_only:
            if args.fetch or args.all or args.source or args.snapshot:
                raise ValueError("--snapshot-only cannot be combined with check options")
            capture = json.loads(args.snapshot_only.read_text(encoding="utf-8"))
            lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
            source = next(s for s in lock["reference_tracking"]["sources"] if s["id"] == capture["source_id"] and s["kind"] == "docs")
            print(json.dumps(make_snapshot(capture, source), ensure_ascii=False, indent=2))
            return 0
        captures = []
        for path in args.snapshot:
            try:
                captures.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                # An unidentifiable capture is reported in v2 capture_errors;
                # it does not suppress independent Git observations.
                captures.append(None)
        payload = build_all_status(args.fetch, captures, args.source) if args.all or args.source or args.snapshot else build_status(args.fetch)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, StopIteration) as exc:
        payload = {"schema": "money-craft.upstream-status.v2" if args.all or args.source or args.snapshot or args.snapshot_only else "money-craft.upstream-status.v1",
                   "state": "error", "error_type": type(exc).__name__,
                   "error": str(exc) if isinstance(exc, ValueError) else "invalid source registry or capture input"}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["state"] in {"partial", "unavailable", "error"}:
        return 1
    return 0 if payload["state"] == "current" else 2


if __name__ == "__main__":
    raise SystemExit(main())
