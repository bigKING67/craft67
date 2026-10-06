#!/usr/bin/env python3
"""Validate Money Craft source, provenance, versions, and runtime contracts."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from acceptance_case import AcceptanceError, load_case
from upstream_sources import validate_tracking

ROOT = Path(__file__).resolve().parents[1]
OWNED_DIRS = [
    ROOT / "skills" / "money-craft",
    ROOT / "scripts",
    ROOT / "adapters",
    ROOT / ".codex-plugin",
    ROOT / ".claude-plugin",
    ROOT / ".grok-plugin",
    ROOT / "LICENSES",
    ROOT / ".github",
    ROOT / "tests",
    ROOT / "artifacts",
    ROOT / "acceptance",
    ROOT / "docs",
    ROOT / "openspec",
]
SECRET_PATTERNS = [
    re.compile(rb"sk-fuyao-[A-Za-z0-9_-]{12,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
FORBIDDEN_PUBLIC_EVIDENCE_SUFFIXES = (".normalized.json", ".pdf", ".html")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def owned_files() -> list[Path]:
    files = [
        ROOT / ".env.example",
        ROOT / ".gitignore",
        ROOT / "LICENSE",
        ROOT / "README.md",
        ROOT / "THIRD_PARTY_NOTICES.md",
        ROOT / "VERSION",
        ROOT / "package.json",
        ROOT / "sources.lock.json",
    ]
    for directory in OWNED_DIRS:
        if directory.exists():
            files.extend(
                path
                for path in directory.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
            )
    return sorted(set(files))


def run(command: list[str], *, cwd: Path = ROOT) -> tuple[int, str]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    output = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode, output


def validate() -> dict[str, Any]:
    checks: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    try:
        package = load_json(ROOT / "package.json")
        codex = load_json(ROOT / ".codex-plugin" / "plugin.json")
        claude = load_json(ROOT / ".claude-plugin" / "plugin.json")
        grok = load_json(ROOT / ".grok-plugin" / "plugin.json")
        leaf_version = (ROOT / "skills" / "money-craft" / "VERSION").read_text(encoding="utf-8").strip()
        values = {version, leaf_version, package.get("version"), codex.get("version"), claude.get("version"), grok.get("version")}
        if values != {version}:
            errors.append(f"version mismatch: {sorted(str(value) for value in values)}")
        else:
            checks.append("version-parity")
        if package.get("private") is not True or package.get("moneyCraft", {}).get("distribution") != "github-only":
            errors.append("package must remain private and GitHub-only")
        if package.get("pi", {}).get("skills") != ["skills/money-craft"]:
            errors.append("package pi.skills must point to canonical skill")
        if codex.get("skills") != "./skills/":
            errors.append("Codex manifest must point to ./skills/")
        checks.append("host-manifests")
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"manifest validation failed: {exc}")

    for path in (ROOT / "skills" / "money-craft" / "schemas").glob("*.json"):
        try:
            payload = load_json(path)
            if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                errors.append(f"{path.name}: unexpected JSON Schema dialect")
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            errors.append(f"{path.name}: invalid schema: {exc}")
    if not errors:
        checks.append("schema-json")

    skill = ROOT / "skills" / "money-craft" / "SKILL.md"
    skill_text = skill.read_text(encoding="utf-8")
    if not skill_text.startswith("---\n") or "\nname: money-craft\n" not in skill_text[:500] or "\ndescription:" not in skill_text[:700]:
        errors.append("SKILL.md frontmatter is invalid")
    else:
        checks.append("skill-frontmatter")

    try:
        lock = load_json(ROOT / "sources.lock.json")
        errors.extend(validate_tracking(lock, ROOT))
        upstream = next(item for item in lock["upstreams"] if item["id"] == "ai-berkshire")
        if not (ROOT / upstream["license_file"]).is_file():
            errors.append("AI Berkshire license file is missing")
        code, local_commit = run(["git", "rev-parse", "HEAD"], cwd=ROOT / "upstreams" / "ai-berkshire")
        if code or local_commit != upstream["pinned_commit"]:
            errors.append("AI Berkshire submodule does not match pinned_commit")
        for mapping in upstream["mappings"]:
            source = ROOT / "upstreams" / "ai-berkshire" / mapping["source"]
            if not source.is_file():
                errors.append(f"missing upstream source: {mapping['source']}")
            for target in mapping["targets"]:
                if not (ROOT / target).is_file():
                    errors.append(f"missing absorbed target: {target}")
        previous_review_commit = upstream["reviewed_commit"]
        for review in upstream.get("reviews", []):
            if not isinstance(review, dict) or not all(
                isinstance(review.get(key), str) and re.fullmatch(r"[0-9a-f]{40}", review[key])
                for key in ("from_commit", "through_commit")
            ):
                errors.append("upstream review range must use fixed 40-character commits")
                continue
            if review["from_commit"] != previous_review_commit:
                errors.append("upstream review ranges must be contiguous and ordered")
            previous_review_commit = review["through_commit"]
            disposition = review.get("disposition")
            if disposition not in {
                "pin-retained-report-only",
                "pin-retained-selective-reimplementation",
            }:
                errors.append("unsupported upstream review disposition")
            if disposition == "pin-retained-report-only" and (
                review.get("changed_scope") != ["reports/"] or review.get("mapped_source_changes") != 0
            ):
                errors.append("report-only upstream review scope is inconsistent")
            if disposition == "pin-retained-selective-reimplementation":
                coverage = review.get("coverage")
                if not isinstance(coverage, dict):
                    errors.append("selective upstream review must record coverage")
                else:
                    counts = [
                        coverage.get("changed_files"),
                        coverage.get("reviewed_files"),
                        coverage.get("accounted_excluded_files"),
                        coverage.get("pending_files"),
                    ]
                    categories = coverage.get("categories")
                    if any(not isinstance(value, int) or value < 0 for value in counts):
                        errors.append("selective upstream review coverage counts must be non-negative integers")
                    elif counts[0] != counts[1] + counts[2] + counts[3]:
                        errors.append("selective upstream review coverage does not close")
                    if (
                        not isinstance(categories, dict)
                        or set(categories) != set(review.get("changed_scope", []))
                        or any(not isinstance(value, int) or value < 0 for value in categories.values())
                        or sum(categories.values()) != coverage.get("changed_files")
                    ):
                        errors.append("selective upstream review category coverage is inconsistent")
                    elif (
                        categories.get("excluded-content", 0) != coverage.get("accounted_excluded_files")
                        or sum(value for key, value in categories.items() if key != "excluded-content")
                        != coverage.get("reviewed_files")
                    ):
                        errors.append("selective upstream review accounted and reviewed coverage is inconsistent")
                    if coverage.get("pending_files") != 0:
                        errors.append("selective upstream review has pending files")
                decisions = review.get("non_absorbed_decisions")
                if not isinstance(decisions, list) or not decisions:
                    errors.append("selective upstream review must record non-absorbed decisions")
                else:
                    excluded_decision_files = 0
                    for decision in decisions:
                        sources = decision.get("sources") if isinstance(decision, dict) else None
                        if (
                            not isinstance(sources, list)
                            or not sources
                            or any(not isinstance(path, str) or path.startswith(("/", "../")) for path in sources)
                            or decision.get("disposition")
                            not in {"provenance-only", "content-excluded", "scope-rejected"}
                            or not isinstance(decision.get("reason"), str)
                            or not decision["reason"]
                        ):
                            errors.append("selective upstream non-absorbed decision is invalid")
                        elif decision["disposition"] == "content-excluded":
                            file_count = decision.get("file_count")
                            if not isinstance(file_count, int) or file_count <= 0:
                                errors.append("content-excluded upstream decision must record a positive file count")
                            else:
                                excluded_decision_files += file_count
                    if isinstance(coverage, dict) and excluded_decision_files != coverage.get(
                        "accounted_excluded_files"
                    ):
                        errors.append("content-excluded upstream decisions do not match coverage")
            observations = review.get("mechanism_observations")
            if not isinstance(observations, list) or not observations:
                errors.append("upstream review must record mechanism observations")
                continue
            for observation in observations:
                if not isinstance(observation, dict):
                    errors.append("upstream mechanism observation must be an object")
                    continue
                if observation.get("classification") != "reimplemented":
                    errors.append("upstream report mechanisms must be reimplemented, not copied")
                sources = observation.get("sources")
                allowed_source_prefixes = ("reports/",) if disposition == "pin-retained-report-only" else ("reports/", "skills/")
                if not isinstance(sources, list) or not sources or any(
                    not isinstance(path, str) or not path.startswith(allowed_source_prefixes) for path in sources
                ):
                    errors.append("upstream mechanism source is outside the reviewed source scope")
                targets = observation.get("targets")
                if not isinstance(targets, list) or not targets or any(not (ROOT / path).is_file() for path in targets):
                    errors.append("upstream mechanism observation target is missing")
        if not errors:
            checks.append("source-provenance")
    except (OSError, json.JSONDecodeError, KeyError, StopIteration, TypeError) as exc:
        errors.append(f"source lock validation failed: {exc}")

    for directory in OWNED_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_symlink():
                errors.append(f"symlink is not allowed: {path.relative_to(ROOT)}")
    for path in owned_files():
        relative = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        for pattern in SECRET_PATTERNS:
            if pattern.search(raw):
                errors.append(f"secret-like material found in {relative}")
        local_home_marker = b"/Users/" + b"gaoqian"
        windows_home_marker = b"C:\\" + b"Users\\"
        if local_home_marker in raw or windows_home_marker in raw:
            errors.append(f"user-specific absolute path found in {relative}")
        if path.suffix in {".py", ".md", ".json", ".yaml", ".yml"}:
            for line_number, line in enumerate(raw.splitlines(), start=1):
                if line.endswith((b" ", b"\t")):
                    errors.append(f"trailing whitespace: {relative}:{line_number}")
                    break
    checks.extend(["secret-scan", "path-scan", "no-symlinks", "whitespace"])

    artifact_root = ROOT / "artifacts"
    forbidden_evidence: list[str] = []
    if artifact_root.is_dir():
        for path in artifact_root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative.endswith(FORBIDDEN_PUBLIC_EVIDENCE_SUFFIXES):
                forbidden_evidence.append(relative)
            if "/captures/" in relative or "/host-smoke/" in relative:
                forbidden_evidence.append(relative)
    if forbidden_evidence:
        errors.append(
            "private evidence found in public artifacts: " + ", ".join(sorted(set(forbidden_evidence)))
        )
    else:
        checks.append("public-data-boundary")

    case_files = sorted((ROOT / "acceptance" / "cases").glob("*.json"))
    if not case_files:
        errors.append("at least one acceptance case contract is required")
    for case_file in case_files:
        try:
            load_case(case_file)
        except (AcceptanceError, OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"invalid acceptance case {case_file.name}: {exc}")
    if case_files and not any("invalid acceptance case" in item for item in errors):
        checks.append("acceptance-case-contracts")

    evidence_manifests = sorted((ROOT / "artifacts" / "acceptance").glob("*/evidence-manifest.json"))
    if not evidence_manifests:
        errors.append("at least one public evidence manifest is required")
    for evidence_manifest in evidence_manifests:
        case_id = evidence_manifest.parent.name
        code, output = run(
            [sys.executable, "scripts/verify_evidence.py", str(evidence_manifest), "--metadata-only"]
        )
        if code:
            errors.append(f"{case_id} public evidence manifest validation failed: {output}")
            continue
        local_evidence = ROOT / "local" / "evidence" / case_id
        if local_evidence.is_dir():
            code, output = run(
                [sys.executable, "scripts/verify_evidence.py", str(evidence_manifest), "--require-private"]
            )
            if code:
                errors.append(f"{case_id} private evidence integrity failed: {output}")
    if evidence_manifests and not any("evidence manifest validation failed" in item for item in errors):
        checks.append("public-evidence-manifests")
    if evidence_manifests and not any("private evidence integrity failed" in item for item in errors):
        checks.append("private-evidence-integrity")

    ignored_code, ignored_output = run(["git", "check-ignore", ".codex/config.toml"])
    if ignored_code != 0 or ignored_output != ".codex/config.toml":
        errors.append("local .codex/config.toml must remain ignored")
    else:
        checks.append("local-config-boundary")
    ignored_code, ignored_output = run(["git", "check-ignore", "local/evidence/600519/example.json"])
    if ignored_code != 0 or ignored_output != "local/evidence/600519/example.json":
        errors.append("local evidence root must remain ignored")
    else:
        checks.append("local-evidence-boundary")
    ignored_code, ignored_output = run(["git", "check-ignore", "local/research/000333/example.json"])
    if ignored_code != 0 or ignored_output != "local/research/000333/example.json":
        errors.append("local research workspaces must remain ignored")
    else:
        checks.append("local-research-boundary")

    python_files = [str(path.relative_to(ROOT)) for path in owned_files() if path.suffix == ".py"]
    code, output = run([sys.executable, "-m", "py_compile", *python_files])
    if code:
        errors.append(f"Python compile failed: {output}")
    else:
        checks.append("python-compile")
    code, output = run([sys.executable, "skills/money-craft/scripts/money_craft.py", "self-test", "--json"])
    if code:
        errors.append(f"runtime self-test failed: {output}")
    else:
        checks.append("runtime-self-test")

    quick_validate = Path.home() / ".codex" / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
    if quick_validate.is_file():
        code, output = run([sys.executable, str(quick_validate), "skills/money-craft"])
        if code and "ModuleNotFoundError" in output:
            # Optional host tool with missing host dependencies; built-in frontmatter checks still ran.
            warnings.append("Codex quick_validate.py dependencies are unavailable; built-in frontmatter checks ran")
        elif code:
            errors.append(f"skill quick_validate failed: {output}")
        else:
            checks.append("skill-quick-validate")
    else:
        warnings.append("Codex quick_validate.py is unavailable; built-in frontmatter checks ran")

    return {
        "schema": "money-craft.source-validation.v1",
        "valid": not errors,
        "version": version,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    payload = validate()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
