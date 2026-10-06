#!/usr/bin/env python3
"""Report upstream drift for the paths listed in docs/upstream-watch.json.

Read-only. For every watched path, compares the pinned research SHA with the
upstream default branch at file level (git blob / directory listing), so it
also works when upstream history was rewritten. Changes are prompts for a human
review recorded in docs/upstream-absorption.md; nothing is pulled or copied.

Uses the authenticated `gh` CLI for GitHub and the public npm registry for
package versions. `--offline` only validates the watch list against this
repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WATCH_FILE = ROOT / "docs" / "upstream-watch.json"
STATUSES = {"reference", "candidate", "implemented", "verified", "deferred"}

Fetch = Callable[[str], Any]


class NotFound(Exception):
    """Upstream object does not exist at the requested ref."""


def gh_api(endpoint: str) -> Any:
    try:
        proc = subprocess.run(
            ["gh", "api", endpoint], capture_output=True, text=True, check=False
        )
    except FileNotFoundError as exc:
        raise RuntimeError("gh CLI not found; install and authenticate gh") from exc
    if proc.returncode != 0:
        if "HTTP 404" in proc.stderr or "Not Found" in proc.stderr:
            raise NotFound(endpoint)
        raise RuntimeError(f"gh api {endpoint} failed: {proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gh api {endpoint} returned non-JSON output") from exc


def npm_latest(package: str) -> str:
    url = f"https://registry.npmjs.org/{urllib.parse.quote(package, safe='@')}/latest"
    with urllib.request.urlopen(url, timeout=20) as response:
        return str(json.load(response)["version"])


def load_watch(path: Path = WATCH_FILE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_watch(data: dict[str, Any], root: Path = ROOT) -> list[str]:
    """Offline checks: identities, pins and that every mapping points at a real local file."""
    errors: list[str] = []
    seen: set[str] = set()
    for upstream in data.get("upstreams", []):
        uid = upstream.get("id", "?")
        if uid in seen:
            errors.append(f"{uid}: duplicate id")
        seen.add(uid)
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", str(upstream.get("repo", ""))):
            errors.append(f"{uid}: repo must be owner/name")
        if not re.fullmatch(r"[0-9a-f]{40}", str(upstream.get("pinned_sha", ""))):
            errors.append(f"{uid}: pinned_sha must be a full 40-hex commit")
        if upstream.get("status") not in STATUSES:
            errors.append(f"{uid}: status must be one of {sorted(STATUSES)}")
        npm = upstream.get("npm")
        if npm and not (root / npm["pinned_in"]).is_file():
            errors.append(f"{uid}: npm.pinned_in {npm['pinned_in']} does not exist")
        if not upstream.get("watch"):
            errors.append(f"{uid}: watch list is empty")
        for entry in upstream.get("watch", []):
            if not entry.get("path") or not entry.get("why"):
                errors.append(f"{uid}: watch entries need path and why")
            for target in entry.get("maps_to", []):
                local = target.split("#", 1)[0]
                if not (root / local).exists():
                    errors.append(f"{uid}: {entry.get('path')} maps to missing {local}")
    return errors


def fingerprint(fetch: Fetch, repo: str, path: str, ref: str) -> str | None:
    """Stable content identity of a file or directory at ref; None if absent."""
    try:
        content = fetch(f"repos/{repo}/contents/{urllib.parse.quote(path)}?ref={ref}")
    except NotFound:
        return None
    if isinstance(content, list):
        listing = "\n".join(sorted(f"{item['name']}:{item['sha']}" for item in content))
        return "dir:" + hashlib.sha256(listing.encode()).hexdigest()
    return "file:" + str(content["sha"])


def classify(pinned: str | None, head: str | None) -> str:
    if pinned is None and head is None:
        return "missing"
    if pinned is None:
        return "added"
    if head is None:
        return "removed"
    return "unchanged" if pinned == head else "changed"


def check_upstream(
    upstream: dict[str, Any],
    fetch: Fetch = gh_api,
    latest: Callable[[str], str] = npm_latest,
    root: Path = ROOT,
) -> dict[str, Any]:
    repo = upstream["repo"]
    report: dict[str, Any] = {"id": upstream["id"], "repo": repo, "status": upstream["status"]}
    errors: list[str] = []
    try:
        try:
            fetch(f"repos/{repo}/commits/{upstream['pinned_sha']}")
        except NotFound as exc:
            raise RuntimeError(
                f"pinned_sha {upstream['pinned_sha'][:12]} is not resolvable upstream; re-pin after review"
            ) from exc
        branch = fetch(f"repos/{repo}")["default_branch"]
        head = fetch(f"repos/{repo}/commits/{branch}")["sha"]
        report.update(branch=branch, head_sha=head, pinned_sha=upstream["pinned_sha"])
        paths = []
        for entry in upstream["watch"]:
            state = classify(
                fingerprint(fetch, repo, entry["path"], upstream["pinned_sha"]),
                fingerprint(fetch, repo, entry["path"], head),
            )
            paths.append({"path": entry["path"], "state": state, "maps_to": entry["maps_to"]})
        report["paths"] = paths
        for item in paths:
            if item["state"] == "missing":
                errors.append(f"watch path {item['path']} exists at neither pin nor head")
    except (NotFound, RuntimeError, KeyError) as exc:
        errors.append(str(exc))
    npm = upstream.get("npm")
    if npm:
        manifest = json.loads((root / npm["pinned_in"]).read_text(encoding="utf-8"))
        pinned = manifest.get("dependencies", {}).get(npm["package"])
        try:
            newest = latest(npm["package"])
        except (OSError, KeyError, ValueError) as exc:  # URLError and timeouts are OSError
            newest = None
            errors.append(f"npm lookup failed: {exc}")
        report["npm"] = {"package": npm["package"], "pinned": pinned, "latest": newest}
    if errors:
        report["error"] = "; ".join(errors)
    return report


def needs_review(report: dict[str, Any]) -> bool:
    changed = any(
        p["state"] in {"changed", "added", "removed"} for p in report.get("paths", [])
    )
    npm = report.get("npm")
    return changed or bool(npm and npm["latest"] and npm["latest"] != npm["pinned"])


def render_text(reports: list[dict[str, Any]]) -> str:
    lines = []
    for report in reports:
        head = report.get("head_sha", "?")[:12]
        flag = "REVIEW" if needs_review(report) else "ok"
        if "error" in report:
            flag = "ERROR"
        lines.append(f"[{flag}] {report['id']} ({report['status']}) pinned {report.get('pinned_sha', '?')[:12]} -> {report.get('branch', '?')} {head}")
        for item in report.get("paths", []):
            if item["state"] != "unchanged":
                lines.append(f"    {item['state']:9} {item['path']}  ->  {', '.join(item['maps_to'])}")
        npm = report.get("npm")
        if npm:
            lines.append(f"    npm {npm['package']}: pinned {npm['pinned']}, latest {npm['latest']}")
        if "error" in report:
            lines.append(f"    error: {report['error']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true", help="only validate the watch list")
    parser.add_argument("--only", action="append", help="limit to these upstream ids")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-change", action="store_true", help="exit 1 when review is needed")
    args = parser.parse_args(argv)

    data = load_watch()
    errors = validate_watch(data)
    if errors:
        print("upstream-watch.json is invalid:", *errors, sep="\n  ", file=sys.stderr)
        return 2
    if args.offline:
        print(f"upstream-watch.json valid: {len(data['upstreams'])} upstreams")
        return 0
    known = {u["id"] for u in data["upstreams"]}
    unknown = sorted(set(args.only or []) - known)
    if unknown:
        print(f"unknown upstream id(s): {', '.join(unknown)}", file=sys.stderr)
        return 2
    selected = [u for u in data["upstreams"] if not args.only or u["id"] in args.only]
    reports = [check_upstream(upstream) for upstream in selected]
    print(json.dumps(reports, indent=2) if args.json else render_text(reports))
    if any("error" in r for r in reports):
        return 2
    return 1 if args.fail_on_change and any(needs_review(r) for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
