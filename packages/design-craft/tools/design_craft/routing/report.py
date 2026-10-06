from __future__ import annotations

import json
from pathlib import Path

from .manifest import (
    PackFile,
    ROUTE_PACK_MANIFEST_PATH,
    SCHEMA,
    SUGGESTED_VALIDATION_COMMANDS,
    file_entry,
    load_route_pack_files,
    sha256_file,
    utc_now,
)


def build_manifest(source_root: Path, *, include_semantic: bool = True) -> dict:
    manifest_error = ""
    try:
        route_pack_files, route_pack_manifest = load_route_pack_files(source_root)
        route_pack_manifest["status"] = "ok"
        route_pack_manifest["errors"] = []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        manifest_error = str(exc)
        route_pack_files = [
            PackFile(ROUTE_PACK_MANIFEST_PATH, True, "route-manifest")
        ]
        manifest_path = source_root / ROUTE_PACK_MANIFEST_PATH
        route_pack_manifest = {
            "schema": "unknown",
            "version": None,
            "path": ROUTE_PACK_MANIFEST_PATH,
            "sha256": sha256_file(manifest_path) if manifest_path.is_file() else "",
            "declared_files": 0,
            "selected_files": 0,
            "required_files": 1,
            "snapshot_files": 0,
            "required_snapshot_covered": False,
            "status": "error",
            "errors": [manifest_error],
        }

    files = [file_entry(source_root, spec) for spec in route_pack_files]
    missing_required = [
        item["path"] for item in files if item["required"] and not item["exists"]
    ]
    existing_files = [item for item in files if item["exists"]]
    if include_semantic and not missing_required and not manifest_error:
        from .semantic_audit import semantic_validation

        semantic = semantic_validation(source_root)
    else:
        reason = (
            "semantic validation skipped because the route-pack manifest is invalid"
            if manifest_error
            else "semantic validation skipped because required route-pack files are missing"
            if missing_required
            else "semantic validation disabled for structural self-check"
        )
        semantic = {
            "status": "skipped",
            "issues": [],
            "warnings": [reason],
            "runtime_probes": [],
            "route_modules": [],
            "runtime_profiles": [],
            "model_catalog_source": "unavailable",
        }
    if manifest_error:
        status = "manifest-error"
    elif missing_required:
        status = "missing-required"
    elif semantic["status"] == "error":
        status = "semantic-error"
    else:
        status = "ok"
    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "source_root": str(source_root),
        "status": status,
        "route_pack_manifest": route_pack_manifest,
        "summary": {
            "tracked_files": len(files),
            "existing_files": len(existing_files),
            "required_files": sum(1 for item in files if item["required"]),
            "missing_required": missing_required,
        },
        "files": files,
        "semantic_validation": semantic,
        "validation": {
            "suggested_commands": SUGGESTED_VALIDATION_COMMANDS,
            "screenshot_policy": "Route planner decides screenshot_evidence_level=none|optional|required.",
        },
    }




def emit_human(payload: dict, copied: list[str], manifest_path: Path | None, dry_run: bool) -> None:
    summary = payload["summary"]
    print(f"schema: {payload['schema']}")
    print(f"source_root: {payload['source_root']}")
    print(f"status: {payload['status']}")
    route_pack_manifest = payload.get("route_pack_manifest", {})
    print(
        "route_pack_manifest: "
        f"{route_pack_manifest.get('status', 'unknown')} "
        f"({route_pack_manifest.get('path', ROUTE_PACK_MANIFEST_PATH)})"
    )
    for error in route_pack_manifest.get("errors", []):
        print(f"- manifest_error: {error}")
    print(
        "files: "
        f"{summary['existing_files']}/{summary['tracked_files']} existing, "
        f"{len(summary['missing_required'])} missing required"
    )
    if summary["missing_required"]:
        print("missing_required:")
        for rel_path in summary["missing_required"]:
            print(f"- {rel_path}")
    semantic = payload.get("semantic_validation", {})
    if semantic:
        print(f"semantic_validation: {semantic.get('status', 'unknown')}")
        for issue in semantic.get("issues", []):
            print(f"- semantic_error: {issue}")
        for warning in semantic.get("warnings", []):
            print(f"- semantic_warning: {warning}")
    if copied:
        action = "would_copy" if dry_run else "copied"
        print(f"{action}: {len(copied)} files")
    if manifest_path is not None:
        action = "would_write_manifest" if dry_run else "manifest"
        print(f"{action}: {manifest_path}")
