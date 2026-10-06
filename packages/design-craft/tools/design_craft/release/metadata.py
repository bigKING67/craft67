from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ..repo import REPO_ROOT


SCHEMA = "design-craft.release-metadata.v1"


def _git(*args: str, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=60,
    )


def _release_header(changelog: str, version: str) -> str:
    match = re.search(rf"^## {re.escape(version)} - ([^\n]+)$", changelog, re.M)
    return match.group(1).strip() if match else ""


def validate_release_metadata(
    *,
    phase: str,
    root: Path = REPO_ROOT,
) -> dict[str, object]:
    if phase not in {"candidate", "final"}:
        raise ValueError("release metadata phase must be candidate or final")
    errors: list[str] = []
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        errors.append("VERSION must contain a stable semantic version")
    try:
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
        compatibility = json.loads(
            (root / "skills/design-craft/COMPATIBILITY.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        package = {}
        lock = {}
        compatibility = {}
        errors.append(f"release JSON metadata is invalid: {exc}")
    if package.get("version") != version:
        errors.append("package.json version must match VERSION")
    if lock.get("version") != version or lock.get("packages", {}).get("", {}).get("version") != version:
        errors.append("package-lock.json versions must match VERSION")
    if (root / "skills/design-craft/VERSION").read_text(encoding="utf-8").strip() != version:
        errors.append("skills/design-craft/VERSION must match VERSION")

    evidence_contracts = compatibility.get("evidence_contracts", {})
    maintenance_contracts = compatibility.get("maintenance_contracts", {})
    expected_evidence = {
        "cross_agent": "design-craft.cross-agent-score.v5",
        "native_runtime": "design-craft.native-runtime-evidence.v3",
        "release_verification": "design-craft.release-evidence.v1",
        "github_checks": "design-craft.github-checks.v2",
        "github_governance": "design-craft.github-governance.v2",
        "github_artifact_observation": "design-craft.github-artifact-observation.v1",
        "runtime_evidence": "design-craft.runtime-evidence.v1",
    }
    expected_maintenance = {
        "release_assets": "design-craft.release-assets.v2",
        "release_certification": "design-craft.release-certification.v1",
        "benchmark_result": "design-craft.benchmark-result.v2",
        "maturity": "design-craft.maturity.v2",
        "release_policy": "design-craft.release-policy.v1",
        "evidence_graph": "design-craft.evidence-graph.v2",
    }
    for key, expected in expected_evidence.items():
        if evidence_contracts.get(key) != expected:
            errors.append(f"COMPATIBILITY.json evidence_contracts.{key} must be {expected}")
    for key, expected in expected_maintenance.items():
        if maintenance_contracts.get(key) != expected:
            errors.append(f"COMPATIBILITY.json maintenance_contracts.{key} must be {expected}")

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    header = _release_header(changelog, version)
    if not header:
        errors.append(f"CHANGELOG.md must contain a {version} section")
    elif phase == "candidate" and header != "Unreleased" and not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}", header
    ):
        errors.append("candidate changelog header must be Unreleased or a release date")
    elif phase == "final" and not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", header):
        errors.append("final release requires a dated changelog section")

    head_result = _git("rev-parse", "HEAD", root=root)
    head = head_result.stdout.strip() if head_result.returncode == 0 else ""
    tag = f"v{version}"
    if phase == "final":
        tag_target = _git("rev-list", "-n", "1", tag, root=root)
        tag_type = _git("cat-file", "-t", tag, root=root)
        if tag_target.returncode != 0 or tag_target.stdout.strip() != head:
            errors.append(f"annotated tag {tag} must point to current HEAD")
        if tag_type.returncode != 0 or tag_type.stdout.strip() != "tag":
            errors.append(f"tag {tag} must be an annotated tag object")
        remote = _git("remote", "get-url", "origin", root=root)
        if remote.returncode != 0:
            errors.append("origin remote is required for final release verification")
        else:
            main = _git("ls-remote", "origin", "refs/heads/main", root=root)
            main_sha = main.stdout.split()[0] if main.returncode == 0 and main.stdout.split() else ""
            if main_sha != head:
                errors.append("live origin/main must point to current HEAD")
            remote_tag = _git(
                "ls-remote",
                "--tags",
                "origin",
                f"refs/tags/{tag}^{{}}",
                root=root,
            )
            tag_sha = (
                remote_tag.stdout.split()[0]
                if remote_tag.returncode == 0 and remote_tag.stdout.split()
                else ""
            )
            if tag_sha != head:
                errors.append(f"live origin annotated tag {tag} must resolve to current HEAD")
    return {
        "schema": SCHEMA,
        "phase": phase,
        "version": version,
        "tag": tag,
        "head": head,
        "changelog_state": header,
        "ok": not errors,
        "errors": errors,
    }
