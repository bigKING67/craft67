#!/usr/bin/env python3
"""Validate the publishable Pi/npm package boundary and size budget."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA = "design-craft.package-verification.v1"
ROOT = Path(__file__).resolve().parents[1]
MAX_PACKED_BYTES = 1_000_000
MAX_UNPACKED_BYTES = 2_000_000
# Two conditional image references replace independent design Skill installs.
# Byte limits and payload allowlists remain unchanged.
MAX_ENTRIES = 102

EXPECTED_PACKAGE_FILES = {
    "skills/design-craft",
    "LICENSE",
    "LICENSES",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
}

REQUIRED_PACKED_PATHS = {
    "package.json",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
    "LICENSES/Apache-2.0.txt",
    "LICENSES/MIT-upstreams.txt",
    "LICENSES/NOTICE-impeccable.md",
    "LICENSES/VERCEL-DESIGN-NOTICE.md",
    "skills/design-craft/SKILL.md",
    "skills/design-craft/VERSION",
    "skills/design-craft/COMPATIBILITY.json",
    "skills/design-craft/lib/design_craft/__init__.py",
    "skills/design-craft/lib/design_craft/authority.py",
    "skills/design-craft/lib/design_craft/comp_fidelity.py",
    "skills/design-craft/lib/design_craft/sealed_rendition.py",
    "skills/design-craft/lib/design_craft/detector_policy.py",
    "skills/design-craft/lib/design_craft/peekpaper.py",
    "skills/design-craft/lib/design_craft/reference_contract.py",
    "skills/design-craft/lib/design_craft/route_contract.py",
    "skills/design-craft/contracts/visual-reference-card.schema.json",
    "skills/design-craft/contracts/visual-reference-catalog.schema.json",
    "skills/design-craft/contracts/visual-reference-pack.schema.json",
    "skills/design-craft/contracts/shadow-lab-comparison.schema.json",
    "skills/design-craft/contracts/shadow-lab-manifest.schema.json",
    "skills/design-craft/contracts/comp-fidelity-spec.schema.json",
    "skills/design-craft/contracts/comp-fidelity-report.schema.json",
    "skills/design-craft/contracts/runtime-evidence.schema.json",
    "skills/design-craft/contracts/sealed-rendition-gate-spec.schema.json",
    "skills/design-craft/contracts/sealed-rendition-capture-plan.schema.json",
    "skills/design-craft/contracts/sealed-rendition-gate-report.schema.json",
    "skills/design-craft/references/comp-fidelity.md",
    "skills/design-craft/references/react-native-expo-motion.md",
    "skills/design-craft/references/reference-workflow.md",
    "skills/design-craft/references/image-reference-implementation.md",
    "skills/design-craft/references/web-image-direction.md",
    "skills/design-craft/scripts/design_craft_reference.py",
    "skills/design-craft/scripts/design_craft_shadow_compare.py",
    "skills/design-craft/scripts/design_craft_shadow_lab.py",
    "skills/design-craft/scripts/design_craft_route.sh",
    "skills/design-craft/scripts/design_craft_route_runtime.py",
    "skills/design-craft/scripts/design_craft_comp_fidelity.py",
    "skills/design-craft/scripts/design_craft_sealed_rendition_gate.py",
    "skills/design-craft/templates/developer-product/design.md",
    "skills/design-craft/templates/developer-product/design.dark.md",
}

ALLOWED_PATHS = {
    "package.json",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
}
ALLOWED_PREFIXES = ("LICENSES/", "skills/design-craft/")
FORBIDDEN_PREFIXES = (
    ".github/",
    "adapters/",
    "docs/",
    "evals/",
    "scripts/",
    "skills/frontend-craft/",
    "upstreams/",
)
FORBIDDEN_PACKED_PARTS = {"__pycache__"}
FORBIDDEN_PACKED_SUFFIXES = {".pyc", ".pyo"}
PUBLIC_HOME_PATTERN = re.compile(
    r"(?:/Users/[^/\s]+|/home/[^/\s]+|[A-Za-z]:\\Users\\[^\\\s]+)"
)
TEXT_SUFFIXES = {
    "",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".swift",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def package_errors(
    package: dict[str, Any],
    lock: dict[str, Any] | None = None,
    compatibility: dict[str, Any] | None = None,
    version: str | None = None,
) -> list[str]:
    errors: list[str] = []
    configured = package.get("files")
    if not isinstance(configured, list) or any(not isinstance(item, str) for item in configured):
        errors.append("package.json files must be a string array")
    elif set(configured) != EXPECTED_PACKAGE_FILES:
        errors.append(
            "package.json files must expose only the canonical skill and required legal metadata"
        )

    pi_skills = package.get("pi", {}).get("skills") if isinstance(package.get("pi"), dict) else None
    if pi_skills != ["skills/design-craft"]:
        errors.append("package.json pi.skills must expose only skills/design-craft")

    if version is not None and package.get("version") != version:
        errors.append("package.json version must match VERSION")
    if not isinstance(package.get("keywords"), list) or "pi-package" not in package["keywords"]:
        errors.append("package.json keywords must include pi-package")

    if lock is not None and version is not None:
        if lock.get("name") != package.get("name") or lock.get("version") != version:
            errors.append("package-lock.json root name/version must match package.json and VERSION")
        root_package = lock.get("packages", {}).get("") if isinstance(lock.get("packages"), dict) else None
        if not isinstance(root_package, dict) or root_package.get("version") != version:
            errors.append("package-lock.json packages root version must match VERSION")

    if compatibility is not None:
        route = compatibility.get("codex_route_pack", {})
        evidence = compatibility.get("evidence_contracts", {})
        maintenance = compatibility.get("maintenance_contracts", {})
        expected = {
            "schema": "design-craft.codex-route-pack.v2",
            "manifest_schema": "codex.frontend-route-pack.manifest.v1",
            "snapshot_schema": "codex.global_agents.snapshot.v2",
            "routing_version": 2,
        }
        if compatibility.get("schema") != "design-craft.compatibility.v1" or any(
            route.get(key) != value for key, value in expected.items()
        ):
            errors.append("COMPATIBILITY.json must pin the route-pack v2 contracts")
        expected_evidence = {
            "cross_agent": "design-craft.cross-agent-score.v5",
            "native_runtime": "design-craft.native-runtime-evidence.v3",
            "release_verification": "design-craft.release-evidence.v1",
            "github_checks": "design-craft.github-checks.v2",
            "visual_reference_card": "design-craft.visual-reference-card.v1",
            "visual_reference_catalog": "design-craft.visual-reference-catalog.v1",
            "visual_reference_pack": "design-craft.visual-reference-pack.v1",
            "comp_fidelity_spec": "design-craft.comp-fidelity-spec.v1",
            "comp_fidelity_report": "design-craft.comp-fidelity-report.v1",
            "runtime_evidence": "design-craft.runtime-evidence.v1",
            "sealed_rendition_gate_spec": "design-craft.sealed-rendition-gate-spec.v1",
            "sealed_rendition_capture_plan": "design-craft.sealed-rendition-capture-plan.v1",
            "sealed_rendition_gate_report": "design-craft.sealed-rendition-gate-report.v1",
        }
        if any(evidence.get(key) != value for key, value in expected_evidence.items()):
            errors.append("COMPATIBILITY.json must pin the release evidence contracts")
        expected_maintenance = {
            "install": "design-craft.install.v2",
            "sync_status": "design-craft.sync-status.v2",
            "release_assets": "design-craft.release-assets.v2",
            "maturity": "design-craft.maturity.v2",
            "release_policy": "design-craft.release-policy.v1",
            "native_release_bundle": "design-craft.native-release-bundle.v2",
            "upstream_absorption_state": "design-craft.upstream-absorption-state.v2",
            "taste_absorption": "design-craft.taste-absorption.v1",
            "impeccable_absorption": "design-craft.impeccable-absorption.v1",
            "emil_absorption": "design-craft.emil-absorption.v1",
            "evidence_graph": "design-craft.evidence-graph.v2",
            "cross_agent_run": "design-craft.cross-agent-run.v3",
            "comparative_variants": "design-craft.comparative-variants.v2",
            "comparative_run": "design-craft.comparative-run.v4",
            "comparative_blind_map": "design-craft.comparative-blind-map.v3",
            "comparative_judge_run": "design-craft.comparative-judge-run.v1",
            "comparative_result": "design-craft.comparative-result.v4",
        }
        if any(maintenance.get(key) != value for key, value in expected_maintenance.items()):
            errors.append("COMPATIBILITY.json must pin the maintenance contracts")
    return errors


def pack_errors(pack: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    packed_size = pack.get("size")
    unpacked_size = pack.get("unpackedSize")
    entry_count = pack.get("entryCount")
    files = pack.get("files")
    if not isinstance(packed_size, int) or packed_size > MAX_PACKED_BYTES:
        errors.append(f"packed package must be <= {MAX_PACKED_BYTES} bytes")
    if not isinstance(unpacked_size, int) or unpacked_size > MAX_UNPACKED_BYTES:
        errors.append(f"unpacked package must be <= {MAX_UNPACKED_BYTES} bytes")
    if not isinstance(entry_count, int) or entry_count > MAX_ENTRIES:
        errors.append(f"package entry count must be <= {MAX_ENTRIES}")
    if not isinstance(files, list):
        return [*errors, "npm pack result must contain a files array"]

    paths = {
        item.get("path")
        for item in files
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    missing = sorted(REQUIRED_PACKED_PATHS - paths)
    if missing:
        errors.append("package is missing required paths: " + ", ".join(missing))

    for path in sorted(paths):
        packed_path = PurePosixPath(path)
        if (
            FORBIDDEN_PACKED_PARTS.intersection(packed_path.parts)
            or packed_path.suffix.lower() in FORBIDDEN_PACKED_SUFFIXES
        ):
            errors.append(f"package contains generated Python cache: {path}")
        elif path.startswith(FORBIDDEN_PREFIXES):
            errors.append(f"package contains forbidden path: {path}")
        elif path not in ALLOWED_PATHS and not path.startswith(ALLOWED_PREFIXES):
            errors.append(f"package contains undeclared path: {path}")
    return errors


def public_path_errors(paths: set[str]) -> list[str]:
    errors: list[str] = []
    for relative in sorted(paths):
        path = ROOT / relative
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        match = PUBLIC_HOME_PATTERN.search(text)
        if match:
            errors.append(f"packed text exposes a user-home path: {relative}: {match.group(0)}")
    return errors


def npm_pack() -> tuple[dict[str, Any], list[str]]:
    npm = shutil.which("npm")
    if npm is None:
        return {}, ["npm is required to validate the publishable package"]
    completed = subprocess.run(
        [npm, "pack", "--dry-run", "--json", "--ignore-scripts"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown npm pack error"
        return {}, [f"npm pack --dry-run failed: {detail}"]
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {}, [f"npm pack returned invalid JSON: {exc}"]
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        return {}, ["npm pack must return exactly one package object"]
    return payload[0], []


def validate() -> dict[str, Any]:
    errors: list[str] = []
    try:
        package = read_json(ROOT / "package.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        package = {}
        errors.append(f"package.json is invalid: {exc}")
    try:
        lock = read_json(ROOT / "package-lock.json")
        compatibility = read_json(ROOT / "skills/design-craft/COMPATIBILITY.json")
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        lock = {}
        compatibility = {}
        version = ""
        errors.append(f"package compatibility metadata is invalid: {exc}")
    errors.extend(package_errors(package, lock, compatibility, version))

    pack, npm_errors = npm_pack()
    errors.extend(npm_errors)
    if pack:
        errors.extend(pack_errors(pack))
        paths = {
            item["path"]
            for item in pack.get("files", [])
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
        errors.extend(public_path_errors(paths))

    return {
        "schema": SCHEMA,
        "root": str(ROOT),
        "package": package.get("name"),
        "version": package.get("version"),
        "packed_bytes": pack.get("size"),
        "unpacked_bytes": pack.get("unpackedSize"),
        "entry_count": pack.get("entryCount"),
        "max_packed_bytes": MAX_PACKED_BYTES,
        "max_unpacked_bytes": MAX_UNPACKED_BYTES,
        "max_entries": MAX_ENTRIES,
        "ok": not errors,
        "errors": errors,
    }


def self_check() -> list[str]:
    errors: list[str] = []
    valid_package = {
        "name": "design-craft",
        "version": "0.5.0",
        "files": sorted(EXPECTED_PACKAGE_FILES),
        "keywords": ["pi-package"],
        "pi": {"skills": ["skills/design-craft"]},
    }
    valid_lock = {
        "name": "design-craft",
        "version": "0.5.0",
        "packages": {"": {"version": "0.5.0"}},
    }
    valid_compatibility = {
        "schema": "design-craft.compatibility.v1",
        "codex_route_pack": {
            "schema": "design-craft.codex-route-pack.v2",
            "manifest_schema": "codex.frontend-route-pack.manifest.v1",
            "snapshot_schema": "codex.global_agents.snapshot.v2",
            "routing_version": 2,
        },
        "evidence_contracts": {
            "cross_agent": "design-craft.cross-agent-score.v5",
            "native_runtime": "design-craft.native-runtime-evidence.v3",
            "release_verification": "design-craft.release-evidence.v1",
            "github_checks": "design-craft.github-checks.v2",
            "visual_reference_card": "design-craft.visual-reference-card.v1",
            "visual_reference_catalog": "design-craft.visual-reference-catalog.v1",
            "visual_reference_pack": "design-craft.visual-reference-pack.v1",
            "comp_fidelity_spec": "design-craft.comp-fidelity-spec.v1",
            "comp_fidelity_report": "design-craft.comp-fidelity-report.v1",
            "runtime_evidence": "design-craft.runtime-evidence.v1",
            "sealed_rendition_gate_spec": "design-craft.sealed-rendition-gate-spec.v1",
            "sealed_rendition_capture_plan": "design-craft.sealed-rendition-capture-plan.v1",
            "sealed_rendition_gate_report": "design-craft.sealed-rendition-gate-report.v1",
        },
        "maintenance_contracts": {
            "install": "design-craft.install.v2",
            "sync_status": "design-craft.sync-status.v2",
            "release_assets": "design-craft.release-assets.v2",
            "maturity": "design-craft.maturity.v2",
            "release_policy": "design-craft.release-policy.v1",
            "native_release_bundle": "design-craft.native-release-bundle.v2",
            "upstream_absorption_state": "design-craft.upstream-absorption-state.v2",
            "taste_absorption": "design-craft.taste-absorption.v1",
            "impeccable_absorption": "design-craft.impeccable-absorption.v1",
            "emil_absorption": "design-craft.emil-absorption.v1",
            "evidence_graph": "design-craft.evidence-graph.v2",
            "cross_agent_run": "design-craft.cross-agent-run.v3",
            "comparative_variants": "design-craft.comparative-variants.v2",
            "comparative_run": "design-craft.comparative-run.v4",
            "comparative_blind_map": "design-craft.comparative-blind-map.v3",
            "comparative_judge_run": "design-craft.comparative-judge-run.v1",
            "comparative_result": "design-craft.comparative-result.v4",
        },
    }
    if package_errors(valid_package, valid_lock, valid_compatibility, "0.5.0"):
        errors.append("package validator rejected the valid package boundary fixture")

    valid_pack = {
        "size": 100,
        "unpackedSize": 200,
        "entryCount": len(REQUIRED_PACKED_PATHS),
        "files": [{"path": path} for path in sorted(REQUIRED_PACKED_PATHS)],
    }
    if pack_errors(valid_pack):
        errors.append("package validator rejected the valid npm pack fixture")

    oversized = dict(valid_pack, size=MAX_PACKED_BYTES + 1)
    if not any("packed package" in item for item in pack_errors(oversized)):
        errors.append("package validator did not reject an oversized package")

    too_many = dict(valid_pack, entryCount=MAX_ENTRIES + 1)
    if not any("entry count" in item for item in pack_errors(too_many)):
        errors.append("package validator did not reject an excessive file count")

    forbidden = dict(
        valid_pack,
        entryCount=len(REQUIRED_PACKED_PATHS) + 1,
        files=[*valid_pack["files"], {"path": "upstreams/example/LICENSE"}],
    )
    if not any("forbidden path" in item for item in pack_errors(forbidden)):
        errors.append("package validator did not reject an upstream payload")

    bytecode = dict(
        valid_pack,
        entryCount=len(REQUIRED_PACKED_PATHS) + 1,
        files=[
            *valid_pack["files"],
            {
                "path": (
                    "skills/design-craft/scripts/__pycache__/"
                    "design_craft_route_runtime.cpython-313.pyc"
                )
            },
        ],
    )
    if not any("generated Python cache" in item for item in pack_errors(bytecode)):
        errors.append("package validator did not reject generated Python bytecode")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Run offline validator invariants.")
    parser.add_argument("--validate", action="store_true", help="Run npm pack and validate the package.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.check and not args.validate:
        args.validate = True

    errors: list[str] = []
    if args.check:
        errors.extend(self_check())
    payload = validate() if args.validate else {
        "schema": SCHEMA,
        "root": str(ROOT),
        "ok": True,
        "errors": [],
    }
    errors.extend(payload["errors"])
    payload["errors"] = errors
    payload["ok"] = not errors

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif payload["ok"]:
        print(
            "package verified: "
            f"{payload.get('packed_bytes', 'n/a')} packed bytes, "
            f"{payload.get('unpacked_bytes', 'n/a')} unpacked bytes, "
            f"{payload.get('entry_count', 'n/a')} files"
        )
    else:
        print("\n".join(errors), file=sys.stderr)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
