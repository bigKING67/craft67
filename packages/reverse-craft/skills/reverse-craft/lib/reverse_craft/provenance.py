from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .common import load_json, sha256_file, utc_now


def audit_references(remote: bool = False) -> dict[str, Any]:
    skill_root = Path(__file__).resolve().parents[2]
    repo_root = skill_root.parents[1]
    package_path = repo_root / "package.json"
    source_checkout = False
    if package_path.is_file():
        try:
            source_checkout = load_json(package_path).get("name") == "@bigking67/reverse-craft"
        except Exception:
            source_checkout = False
    provenance_path = skill_root / "references" / "provenance.json"
    manifest = load_json(provenance_path)
    checks: list[dict[str, Any]] = []
    for entry in manifest["paths"]:
        if entry.get("scope") == "source" and not source_checkout:
            checks.append({
                "path": entry["path"], "classification": entry["classification"],
                "exists": False, "ok": True, "skipped": True, "reason": "source-only path is not shipped in a standalone Skill install",
            })
            continue
        prefix = "skills/reverse-craft/"
        path = skill_root / entry["path"][len(prefix):] if entry["path"].startswith(prefix) else repo_root / entry["path"]
        check: dict[str, Any] = {"path": entry["path"], "classification": entry["classification"], "exists": path.exists(), "ok": path.exists()}
        if path.is_file() and entry.get("sha256"):
            check["expected_sha256"] = entry["sha256"]
            check["actual_sha256"] = sha256_file(path)
            check["ok"] = check["actual_sha256"] == check["expected_sha256"]
        checks.append(check)
    upstreams: list[dict[str, Any]] = []
    if remote:
        for source in manifest["sources"]:
            try:
                completed = subprocess.run(
                    ["git", "ls-remote", source["url"], "refs/heads/main"],
                    text=True, capture_output=True, timeout=20, check=False,
                )
                head = completed.stdout.split()[0] if completed.returncode == 0 and completed.stdout.strip() else None
                upstreams.append({"id": source["id"], "reviewed_commit": source["commit"], "remote_main": head, "moved": bool(head and head != source["commit"]), "error": completed.stderr.strip() or None})
            except (OSError, subprocess.TimeoutExpired) as exc:
                upstreams.append({"id": source["id"], "reviewed_commit": source["commit"], "remote_main": None, "moved": None, "error": type(exc).__name__})
    return {
        "schema": "reverse-craft.reference-audit.v1",
        "checked_at": utc_now(),
        "valid": all(item["ok"] for item in checks),
        "source_checkout": source_checkout,
        "checks": checks,
        "remote_checked": remote,
        "upstreams": upstreams,
    }
