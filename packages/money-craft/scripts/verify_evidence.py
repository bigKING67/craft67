#!/usr/bin/env python3
"""Validate public evidence metadata and optionally verify private files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_KINDS = {"provider-response", "official-document", "official-index", "official-material"}


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evidence manifest must be a JSON object")
    return payload


def validate_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != "money-craft.public-evidence-manifest.v1":
        errors.append("unexpected evidence manifest schema")
    distribution = payload.get("distribution")
    if not isinstance(distribution, dict) or distribution.get("mode") != "metadata-only":
        errors.append("distribution.mode must be metadata-only")
    elif distribution.get("provider_payloads_distributed") is not False:
        errors.append("provider payload distribution must be false")
    elif distribution.get("downloaded_documents_distributed") is not False:
        errors.append("downloaded document distribution must be false")

    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        return errors + ["sources must be a non-empty array"]
    if payload.get("source_count") != len(sources):
        errors.append("source_count does not match sources")

    seen_ids: set[str] = set()
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not re.fullmatch(r"S[0-9]{2,}", source_id):
            errors.append(f"{label}.id is invalid")
        elif source_id in seen_ids:
            errors.append(f"duplicate source id: {source_id}")
        else:
            seen_ids.add(source_id)
        if source.get("kind") not in ALLOWED_KINDS:
            errors.append(f"{label}.kind is invalid")
        if not isinstance(source.get("title"), str) or not source["title"].strip():
            errors.append(f"{label}.title is required")
        if source.get("distribution") != "private-not-distributed":
            errors.append(f"{label}.distribution must be private-not-distributed")
        if source.get("kind") == "provider-response":
            if source.get("provider") != "fuyao" or not isinstance(source.get("operation"), str):
                errors.append(f"{label} has invalid provider metadata")
        else:
            url = source.get("url")
            if not isinstance(url, str) or not url.startswith("https://"):
                errors.append(f"{label}.url must be HTTPS")

        files = source.get("files")
        if not isinstance(files, list) or not files:
            errors.append(f"{label}.files must be a non-empty array")
            continue
        for file_index, item in enumerate(files):
            file_label = f"{label}.files[{file_index}]"
            if not isinstance(item, dict):
                errors.append(f"{file_label} must be an object")
                continue
            relative = item.get("path")
            if not isinstance(relative, str) or not relative:
                errors.append(f"{file_label}.path is required")
            else:
                path = Path(relative)
                if path.is_absolute() or ".." in path.parts:
                    errors.append(f"{file_label}.path must stay inside the evidence root")
            if not SHA256_RE.fullmatch(str(item.get("sha256", ""))):
                errors.append(f"{file_label}.sha256 is invalid")
            if not isinstance(item.get("role"), str) or not item["role"]:
                errors.append(f"{file_label}.role is required")
    return errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_private_files(payload: dict[str, Any], evidence_root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    verified = 0
    for source in payload.get("sources", []):
        if not isinstance(source, dict):
            continue
        for item in source.get("files", []):
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                continue
            path = evidence_root / item["path"]
            if not path.is_file():
                errors.append(f"missing private evidence: {item['path']}")
                continue
            actual = sha256_file(path)
            if actual != item.get("sha256"):
                errors.append(f"SHA-256 mismatch: {item['path']}")
                continue
            verified += 1
    return errors, verified


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--metadata-only", action="store_true")
    mode.add_argument("--require-private", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest_path = args.manifest.resolve()
    try:
        payload = load_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        return 1

    errors = validate_manifest(payload)
    warnings: list[str] = []
    verified_files = 0
    local_tested = False
    default_root = payload.get("local_evidence", {}).get("default_root")
    evidence_root = args.evidence_root
    if evidence_root is None and isinstance(default_root, str):
        evidence_root = ROOT / default_root
    if not args.metadata_only:
        if evidence_root is not None and evidence_root.is_dir():
            local_tested = True
            file_errors, verified_files = verify_private_files(payload, evidence_root)
            errors.extend(file_errors)
        elif args.require_private:
            errors.append(f"private evidence root is unavailable: {evidence_root}")
        else:
            warnings.append("private evidence unavailable; metadata-only validation completed")

    result = {
        "schema": "money-craft.evidence-verification.v1",
        "valid": not errors,
        "manifest": str(manifest_path.relative_to(ROOT)) if manifest_path.is_relative_to(ROOT) else str(manifest_path),
        "source_count": len(payload.get("sources", [])),
        "local_evidence_tested": local_tested,
        "verified_file_count": verified_files,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
