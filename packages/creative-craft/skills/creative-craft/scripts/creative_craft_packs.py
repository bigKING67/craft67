"""Brand and Reference Pack lifecycle transactions and CLI adapters."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import re
import shutil
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from creative_craft_contracts import (
    json_content_sha256,
    load_json,
    nonempty,
    reference_history_filename,
    sha256_file,
    write_atomic,
)
from creative_craft_project import (
    BrandPackGraph,
    ProjectGraph,
    ReferencePackGraph,
    _is_external_asset_uri,
    _require_safe_project_write_path,
    _safe_relative_path,
    tree_sha256,
    validate_brand_pack,
    validate_project,
    validate_reference_pack,
)


def _json_text(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _brand_authority_documents(brand_name: str) -> list[tuple[str, str, str]]:
    return [
        (
            "brand",
            "references/brand.md",
            f"""# {brand_name} Brand Authority

Status: `UNVERIFIED`

This draft contains no approved brand facts. Replace every `TBD` only from a reviewed source.

## Identity

- Working brand name: {brand_name}
- Legal entity: TBD
- Purpose: TBD
- Positioning: TBD
- Audience: TBD

## Non-negotiables

- TBD

## Source boundary

- Approved source references: none
""",
        ),
        (
            "products",
            "references/products.md",
            f"""# {brand_name} Product Authority

Status: `UNVERIFIED`

No product fact, SKU specification, ingredient, performance statement, price, or availability is approved in this draft.

## Approved products

- TBD

## Source boundary

- Approved source references: none
""",
        ),
        (
            "claims",
            "references/claims.md",
            f"""# {brand_name} Claims Authority

Status: `UNVERIFIED`

No marketing, efficacy, comparative, sustainability, certification, safety, or compliance claim is approved in this draft.

## Approved claims

- None

## Prohibited until approved

- Any claim without a source, owner, scope, market, and approval record
""",
        ),
        (
            "visual",
            "references/visual-system.md",
            f"""# {brand_name} Visual System

Status: `UNVERIFIED`

## Approved marks and lockups

- TBD

## Color, typography, composition, and image rules

- TBD

## Prohibited treatments

- TBD
""",
        ),
        (
            "verbal",
            "references/verbal-system.md",
            f"""# {brand_name} Verbal System

Status: `UNVERIFIED`

## Voice and tone

- TBD

## Exact terminology

- TBD

## Prohibited language

- TBD
""",
        ),
        (
            "channels",
            "references/channels.md",
            f"""# {brand_name} Channel Rules

Status: `UNVERIFIED`

## Markets and channels

- TBD

## Format and adaptation rules

- TBD

## Required disclosures

- TBD
""",
        ),
        (
            "rights",
            "references/rights-and-approvals.md",
            f"""# {brand_name} Rights and Approvals

Status: `UNVERIFIED`

No asset, person, music, font, claim, or market use is approved by this draft.

## Approval owners

- Brand: TBD
- Legal or compliance: TBD
- Asset rights: TBD

## Approved exceptions

- None
""",
        ),
    ]


def _brand_skill_text(brand_id: str, brand_name: str) -> str:
    description = (
        f"Private {brand_name} brand authority router. Use only when the user or active project "
        f"explicitly identifies brand_id '{brand_id}'. Load reviewed brand references and then "
        "apply the generic creative-craft workflow."
    )
    return f"""---
name: {brand_id}-brand
description: {json.dumps(description, ensure_ascii=False)}
---

# {brand_name} Brand Authority Router

Use this skill only when the request or bound project explicitly identifies `{brand_id}`.

1. Read `brand-pack.json` and reject `revoked` authority.
2. Read only the authority files needed for the task.
3. Treat `TBD` and `UNVERIFIED` as unknown; never turn them into facts or approvals.
4. Resolve assets through `asset-ledger.json`; do not infer rights from file possession.
5. Use the generic `creative-craft` skill for briefs, routes, direction, jobs, inspection, revision, evaluation, and delivery.
6. For project work, use the project's immutable Brand Pack snapshot instead of this live checkout.

This skill contains brand authority only. It does not replace or duplicate Creative Craft schemas, provider profiles, or production methods.
"""


def cmd_init_brand_pack(args: argparse.Namespace) -> int:
    requested_target = Path(args.target).expanduser()
    if requested_target.is_symlink():
        print("ERROR: Brand Pack target must not be a symlink", file=sys.stderr)
        return 1
    target = requested_target.resolve()
    brand_id = str(args.brand_id).strip()
    brand_name = str(args.brand_name).strip()
    owner = str(args.owner).strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", brand_id):
        print("ERROR: --brand-id must be a lowercase slug", file=sys.stderr)
        return 1
    if not brand_name or not owner:
        print("ERROR: --brand-name and --owner must be non-empty", file=sys.stderr)
        return 1
    known_paths = [
        target / "SKILL.md",
        target / "VERSION",
        target / "brand-pack.json",
        target / "asset-ledger.json",
        *(target / path for _, path, _ in _brand_authority_documents(brand_name)),
    ]
    conflicts = [path for path in known_paths if path.exists()]
    if conflicts and not args.force:
        print(
            "ERROR: refusing to overwrite existing Brand Pack files:", file=sys.stderr
        )
        for path in conflicts:
            print(f"  {path}", file=sys.stderr)
        print(
            "Use --force only after reviewing the existing authority.", file=sys.stderr
        )
        return 1
    if target.exists() and any(target.iterdir()) and args.force:
        suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = target.with_name(f"{target.name}.bak.{suffix}")
        shutil.copytree(target, backup, symlinks=True)
        print(f"Backup: {backup}")
    try:
        target.mkdir(parents=True, exist_ok=True)
        documents = _brand_authority_documents(brand_name)
        for _, relative, content in documents:
            write_atomic(target / relative, content)
        ledger = {
            "schema_version": "creative-craft.asset-ledger.v1",
            "project_id": f"brand:{brand_id}",
            "assets": [],
        }
        ledger_path = target / "asset-ledger.json"
        write_atomic(ledger_path, _json_text(ledger))
        manifest = {
            "schema_version": "creative-craft.brand-pack.v1",
            "brand_id": brand_id,
            "brand_name": brand_name,
            "pack_id": f"{brand_id}-brand-pack",
            "version": "0.1.0",
            "status": "draft",
            "classification": "internal",
            "owner": owner,
            "approved_at": None,
            "review_after": None,
            "supersedes": None,
            "authority_files": [
                {
                    "role": role,
                    "path": relative,
                    "sha256": sha256_file(target / relative),
                }
                for role, relative, _ in documents
            ],
            "asset_ledger": {
                "path": "asset-ledger.json",
                "sha256": sha256_file(ledger_path),
            },
            "source_references": [],
        }
        write_atomic(target / "brand-pack.json", _json_text(manifest))
        write_atomic(target / "SKILL.md", _brand_skill_text(brand_id, brand_name))
        write_atomic(target / "VERSION", "0.1.0\n")
        approved_dir = target / "assets" / "approved"
        approved_dir.mkdir(parents=True, exist_ok=True)
        write_atomic(approved_dir / ".gitkeep", "")
        graph = validate_brand_pack(target)
        if not graph.result.ok:
            raise ValueError("; ".join(graph.result.errors))
    except (OSError, ValueError) as exc:
        print(f"ERROR: failed to initialize Brand Pack: {exc}", file=sys.stderr)
        return 1
    print(target)
    return 0


def cmd_validate_brand_pack(args: argparse.Namespace) -> int:
    graph = validate_brand_pack(Path(args.root))
    payload = {
        "root": str(graph.root),
        "manifest": str(graph.manifest_path),
        "brand_id": graph.manifest.get("brand_id"),
        "pack_id": graph.manifest.get("pack_id"),
        "version": graph.manifest.get("version"),
        "status": graph.manifest.get("status"),
        "classification": graph.manifest.get("classification"),
        "valid": graph.result.ok,
        "authority_roles": sorted(graph.authority_paths),
        "asset_count": len(graph.ledger.get("assets", [])),
        "errors": graph.result.errors,
        "warnings": graph.result.warnings,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{'PASS' if graph.result.ok else 'FAIL'} brand pack: {graph.root}")
        print(f"  Brand: {payload['brand_id']}")
        print(
            f"  Pack: {payload['pack_id']}@{payload['version']} ({payload['status']})"
        )
        print(f"  Authority files: {len(payload['authority_roles'])}")
        print(f"  Assets: {payload['asset_count']}")
        for message in graph.result.errors:
            print(f"  ERROR: {message}")
        for message in graph.result.warnings:
            print(f"  WARN:  {message}")
    return 0 if graph.result.ok else 1


def _reference_skill_text(reference_pack_id: str, name: str) -> str:
    description = (
        f"Private {name} creative reference router. Use only when the user or active project "
        f"explicitly needs reference_pack_id '{reference_pack_id}'. Load relevant observations "
        "and transferable principles, then apply the generic creative-craft workflow."
    )
    return f"""---
name: {reference_pack_id}
description: {json.dumps(description, ensure_ascii=False)}
---

# {name} Reference Router

Use this skill only when the request or bound project explicitly needs `{reference_pack_id}`.

1. Read `reference-pack.json`; reject `revoked`, and do not create a new binding from `superseded`.
2. Load only the selected reference entities needed for the task.
3. Keep `OBSERVED`, `INFERRED`, `HYPOTHESIZED`, and `UNVERIFIED` distinct.
4. Treat references as research, not as brand authority or permission to imitate.
5. Never override the project's Primary Brand Pack, Brief, exact copy, rights, claims, or product invariants.
6. Require every `reviewed` source to resolve to a local, symlink-free snapshot with matching SHA-256.
7. Resolve assets through `asset-ledger.json`; public visibility does not grant generation-input rights.
8. Use the generic `creative-craft` skill for briefs, routes, direction, jobs, inspection, revision, evaluation, and delivery.
9. For project work, use the immutable project snapshot instead of this live checkout.

This skill contains non-authoritative creative reference intelligence only. It does not replace or duplicate Creative Craft schemas, provider profiles, production methods, or a Primary Brand Pack.
"""


def cmd_init_reference_pack(args: argparse.Namespace) -> int:
    requested_target = Path(args.target).expanduser()
    if requested_target.is_symlink():
        print("ERROR: Reference Pack target must not be a symlink", file=sys.stderr)
        return 1
    target = requested_target.resolve()
    reference_pack_id = str(args.pack_id).strip()
    name = str(args.name).strip()
    owner = str(args.owner).strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", reference_pack_id):
        print("ERROR: --pack-id must be a lowercase slug", file=sys.stderr)
        return 1
    if not name or not owner:
        print("ERROR: --name and --owner must be non-empty", file=sys.stderr)
        return 1
    known_paths = [
        target / "SKILL.md",
        target / "VERSION",
        target / "reference-pack.json",
        target / "asset-ledger.json",
    ]
    conflicts = [path for path in known_paths if path.exists()]
    if conflicts and not args.force:
        print(
            "ERROR: refusing to overwrite existing Reference Pack files:",
            file=sys.stderr,
        )
        for path in conflicts:
            print(f"  {path}", file=sys.stderr)
        print(
            "Use --force only after reviewing the existing research library.",
            file=sys.stderr,
        )
        return 1
    if target.exists() and any(target.iterdir()) and args.force:
        suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = target.with_name(f"{target.name}.bak.{suffix}")
        shutil.copytree(target, backup, symlinks=True)
        print(f"Backup: {backup}")
    try:
        target.mkdir(parents=True, exist_ok=True)
        ledger = {
            "schema_version": "creative-craft.asset-ledger.v1",
            "project_id": f"reference:{reference_pack_id}",
            "assets": [],
        }
        ledger_path = target / "asset-ledger.json"
        write_atomic(ledger_path, _json_text(ledger))
        manifest = {
            "schema_version": "creative-craft.reference-pack.v1",
            "reference_pack_id": reference_pack_id,
            "name": name,
            "version": "0.1.0",
            "status": "draft",
            "classification": "internal",
            "owner": owner,
            "purpose": "TBD",
            "reviewed_at": None,
            "review_after": None,
            "supersedes": None,
            "entities": [],
            "asset_ledger": {
                "path": "asset-ledger.json",
                "sha256": sha256_file(ledger_path),
            },
            "source_references": [],
        }
        write_atomic(target / "reference-pack.json", _json_text(manifest))
        write_atomic(
            target / "SKILL.md", _reference_skill_text(reference_pack_id, name)
        )
        write_atomic(target / "VERSION", "0.1.0\n")
        approved_dir = target / "assets" / "approved"
        approved_dir.mkdir(parents=True, exist_ok=True)
        write_atomic(approved_dir / ".gitkeep", "")
        sources_dir = target / "sources"
        sources_dir.mkdir(parents=True, exist_ok=True)
        write_atomic(sources_dir / ".gitkeep", "")
        graph = validate_reference_pack(target)
        if not graph.result.ok:
            raise ValueError("; ".join(graph.result.errors))
    except (OSError, ValueError) as exc:
        print(f"ERROR: failed to initialize Reference Pack: {exc}", file=sys.stderr)
        return 1
    print(target)
    return 0


def cmd_validate_reference_pack(args: argparse.Namespace) -> int:
    graph = validate_reference_pack(Path(args.root))
    payload = {
        "root": str(graph.root),
        "manifest": str(graph.manifest_path),
        "reference_pack_id": graph.manifest.get("reference_pack_id"),
        "name": graph.manifest.get("name"),
        "version": graph.manifest.get("version"),
        "status": graph.manifest.get("status"),
        "classification": graph.manifest.get("classification"),
        "valid": graph.result.ok,
        "entity_count": len(graph.manifest.get("entities", [])),
        "asset_count": len(graph.ledger.get("assets", [])),
        "errors": graph.result.errors,
        "warnings": graph.result.warnings,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{'PASS' if graph.result.ok else 'FAIL'} reference pack: {graph.root}")
        print(
            f"  Pack: {payload['reference_pack_id']}@{payload['version']} ({payload['status']})"
        )
        print(f"  Entities: {payload['entity_count']}")
        print(f"  Assets: {payload['asset_count']}")
        for message in graph.result.errors:
            print(f"  ERROR: {message}")
        for message in graph.result.warnings:
            print(f"  WARN:  {message}")
    return 0 if graph.result.ok else 1


def _copy_snapshot_files(source: BrandPackGraph, target: Path) -> None:
    try:
        target.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(f"brand staging path already exists: {target}") from exc
    relative_files: set[str] = {"brand-pack.json"}
    relative_files.update(
        str(item["path"])
        for item in source.manifest.get("authority_files", [])
        if isinstance(item, dict)
    )
    ledger_relative = str(source.manifest.get("asset_ledger", {}).get("path"))
    relative_files.add(ledger_relative)
    for asset in source.ledger.get("assets", []):
        if not isinstance(asset, dict):
            continue
        value = str(asset.get("path_or_uri", ""))
        if not _is_external_asset_uri(value):
            relative_files.add(value)
    try:
        for relative in sorted(relative_files):
            source_path, error = _safe_relative_path(
                source.root, relative, label="snapshot source path"
            )
            if error or source_path is None or not source_path.is_file():
                raise ValueError(
                    error or f"snapshot source file does not exist: {relative!r}"
                )
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination)
    except Exception:
        _remove_path(target)
        raise


def _project_ledger_record(graph: ProjectGraph) -> dict[str, Any]:
    records = [
        record for (kind, _), record in graph.records.items() if kind == "asset-ledger"
    ]
    if len(records) != 1:
        raise ValueError("project must register exactly one project asset ledger")
    return records[0]


def _snapshot_asset_ids(snapshot_path: Path | None) -> set[str]:
    if snapshot_path is None or not snapshot_path.is_dir():
        return set()
    graph = validate_brand_pack(snapshot_path)
    if not graph.result.ok:
        raise ValueError(
            "existing brand snapshot is invalid: " + "; ".join(graph.result.errors)
        )
    return {
        str(item.get("asset_id"))
        for item in graph.ledger.get("assets", [])
        if isinstance(item, dict)
    }


def _merged_project_ledger(
    project_ledger: dict[str, Any], source: BrandPackGraph, old_asset_ids: set[str]
) -> dict[str, Any]:
    merged = copy.deepcopy(project_ledger)
    existing = [
        item
        for item in merged.get("assets", [])
        if isinstance(item, dict) and str(item.get("asset_id")) not in old_asset_ids
    ]
    ids = {str(item.get("asset_id")) for item in existing}
    for source_asset in source.ledger.get("assets", []):
        if not isinstance(source_asset, dict):
            continue
        asset = copy.deepcopy(source_asset)
        asset_id = str(asset.get("asset_id"))
        if asset_id in ids:
            raise ValueError(
                f"brand asset_id collides with a project asset: {asset_id}"
            )
        ids.add(asset_id)
        value = str(asset.get("path_or_uri", ""))
        if not _is_external_asset_uri(value):
            asset["path_or_uri"] = (
                f".creative-craft/brand-snapshot/{Path(value).as_posix()}"
            )
        existing.append(asset)
    merged["assets"] = existing
    return merged


def _backup_project_state(
    root: Path,
    backup_relative: str,
    paths: list[Path],
    *,
    label: str,
) -> tuple[Path, dict[Path, bool]]:
    backup = _require_safe_project_write_path(root, backup_relative, label=label)
    tracked: list[tuple[Path, Path]] = []
    for path in paths:
        try:
            relative = path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"{label} tracked path escapes project: {path}") from exc
        safe_path = _require_safe_project_write_path(
            root,
            relative.as_posix(),
            label=f"{label} tracked path",
        )
        tracked.append((safe_path, relative))
    try:
        backup.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(f"{label} already exists: {backup}") from exc
    existed: dict[Path, bool] = {}
    try:
        for safe_path, relative in tracked:
            present = safe_path.exists()
            existed[safe_path] = present
            if not present:
                continue
            destination = backup / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if safe_path.is_dir():
                shutil.copytree(safe_path, destination)
            else:
                shutil.copy2(safe_path, destination)
    except Exception:
        _remove_path(backup)
        _prune_empty_parents(backup.parent, root)
        raise
    return backup, existed


def _backup_brand_state(root: Path, paths: list[Path]) -> tuple[Path, dict[Path, bool]]:
    suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return _backup_project_state(
        root,
        f".creative-craft/brand-backups/{suffix}",
        paths,
        label="brand backup path",
    )


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def _prune_empty_parents(start: Path, stop: Path) -> None:
    current = start
    while current != stop and current.is_dir() and not current.is_symlink():
        if any(current.iterdir()):
            break
        current.rmdir()
        current = current.parent


def _restore_brand_state(root: Path, backup: Path, existed: dict[Path, bool]) -> None:
    for path, was_present in existed.items():
        _remove_path(path)
        if not was_present:
            continue
        source = backup / path.relative_to(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, path)
        else:
            shutil.copy2(source, path)


def _discard_operation_backup(root: Path, backup: Path) -> None:
    _remove_path(backup)
    _prune_empty_parents(backup.parent, root)


def _cleanup_rolled_back_operation(
    root: Path, backup: Path, existed: dict[Path, bool]
) -> None:
    _discard_operation_backup(root, backup)
    for path, was_present in existed.items():
        if not was_present:
            _prune_empty_parents(path.parent, root)


def _brand_source_value(args: argparse.Namespace, name: str) -> Any:
    return getattr(args, name, None)


def _validated_requested_project_root(project_root: Path) -> Path:
    requested_root = project_root.expanduser().absolute()
    if requested_root.is_symlink():
        raise ValueError(f"project root must not be a symlink: {requested_root}")
    return requested_root.resolve()


def _install_brand_snapshot(
    project_root: Path,
    source_root: Path,
    args: argparse.Namespace,
    *,
    require_existing_binding: bool,
    retain_backup: bool,
) -> Path:
    project_root = _validated_requested_project_root(project_root)
    graph = validate_project(project_root)
    if not graph.result.ok:
        raise ValueError(
            "project is invalid before Brand Pack update: "
            + "; ".join(graph.result.errors)
        )
    existing_binding_records = [
        record for (kind, _), record in graph.records.items() if kind == "brand-binding"
    ]
    if require_existing_binding and len(existing_binding_records) != 1:
        raise ValueError(
            "update-brand-snapshot requires exactly one existing brand binding"
        )
    if not require_existing_binding and existing_binding_records:
        raise ValueError(
            "project already has a brand binding; use update-brand-snapshot"
        )

    source = validate_brand_pack(source_root)
    if not source.result.ok:
        raise ValueError("Brand Pack is invalid: " + "; ".join(source.result.errors))
    if source.manifest.get("status") == "revoked":
        raise ValueError("cannot bind a revoked Brand Pack")
    source_uri = _brand_source_value(args, "brand_source_uri")
    source_commit = _brand_source_value(args, "brand_source_commit")
    if source_commit and not source_uri:
        raise ValueError("--brand-source-commit requires --brand-source-uri")
    reason = str(
        _brand_source_value(args, "reason") or "Initial Brand Pack import"
    ).strip()
    imported_by = str(_brand_source_value(args, "imported_by") or "TBD").strip()
    if not reason or not imported_by:
        raise ValueError("reason and imported_by must be non-empty")

    suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    staging = _require_safe_project_write_path(
        project_root,
        f".creative-craft/.brand-snapshot.staging-{suffix}",
        label="brand staging path",
    )
    snapshot_path = _require_safe_project_write_path(
        project_root,
        ".creative-craft/brand-snapshot",
        label="brand snapshot path",
    )
    binding_path = _require_safe_project_write_path(
        project_root,
        ".creative-craft/brand-binding.json",
        label="brand binding path",
    )
    project_brand_path = _require_safe_project_write_path(
        project_root,
        "BRAND.md",
        label="project brand path",
    )
    manifest_path = graph.manifest_path
    ledger_record = _project_ledger_record(graph)
    ledger_path = Path(ledger_record["path"])
    old_snapshot = snapshot_path if existing_binding_records else None
    old_asset_ids = _snapshot_asset_ids(old_snapshot)
    previous_binding_id = (
        str(existing_binding_records[0]["data"].get("binding_id"))
        if existing_binding_records
        else None
    )

    staging_owned = False
    try:
        _copy_snapshot_files(source, staging)
        staging_owned = True
        staged_validation = validate_brand_pack(staging)
        if not staged_validation.result.ok:
            raise ValueError(
                "staged Brand Pack is invalid: "
                + "; ".join(staged_validation.result.errors)
            )
        staged_tree_sha = tree_sha256(staging)
        merged_ledger = _merged_project_ledger(
            ledger_record["data"], source, old_asset_ids
        )
        brand_authority = source.authority_paths.get("brand")
        if brand_authority is None:
            raise ValueError("Brand Pack has no brand authority file")
        tracked_paths = [
            snapshot_path,
            binding_path,
            project_brand_path,
            ledger_path,
            manifest_path,
        ]
        backup, existed = _backup_brand_state(project_root, tracked_paths)
    except Exception:
        if staging_owned:
            _remove_path(staging)
        raise
    try:
        _remove_path(snapshot_path)
        staging.replace(snapshot_path)
        shutil.copy2(
            snapshot_path / brand_authority.relative_to(source.root), project_brand_path
        )
        write_atomic(ledger_path, _json_text(merged_ledger))
        imported_at = (
            dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        )
        binding = {
            "schema_version": "creative-craft.brand-binding.v1",
            "binding_id": (
                f"binding-{graph.manifest.get('project_id')}-{source.manifest.get('brand_id')}-"
                f"{suffix}"
            ),
            "project_id": str(graph.manifest.get("project_id")),
            "brand_id": str(source.manifest.get("brand_id")),
            "pack_id": str(source.manifest.get("pack_id")),
            "pack_version": str(source.manifest.get("version")),
            "source": {
                "repository_or_uri": source_uri,
                "ref": _brand_source_value(args, "brand_source_ref"),
                "commit": source_commit,
                "pack_sha256": sha256_file(snapshot_path / "brand-pack.json"),
            },
            "snapshot": {
                "path": ".creative-craft/brand-snapshot",
                "tree_sha256": staged_tree_sha,
            },
            "project_brand": {
                "path": "BRAND.md",
                "sha256": sha256_file(project_brand_path),
            },
            "imported_at": imported_at,
            "imported_by": imported_by,
            "previous_binding_id": previous_binding_id,
            "reason": reason,
        }
        write_atomic(binding_path, _json_text(binding))

        manifest = copy.deepcopy(graph.manifest)
        manifest["artifacts"] = [
            item
            for item in manifest.get("artifacts", [])
            if isinstance(item, dict)
            and item.get("artifact_type") not in {"brand-pack", "brand-binding"}
        ]
        for item in manifest["artifacts"]:
            if item.get("artifact_type") == "asset-ledger" and Path(
                str(item.get("path"))
            ) == ledger_path.relative_to(project_root):
                item["sha256"] = sha256_file(ledger_path)
        manifest["artifacts"].extend(
            [
                {
                    "artifact_type": "brand-pack",
                    "artifact_id": str(source.manifest.get("pack_id")),
                    "schema_version": "creative-craft.brand-pack.v1",
                    "path": ".creative-craft/brand-snapshot/brand-pack.json",
                    "sha256": sha256_file(snapshot_path / "brand-pack.json"),
                },
                {
                    "artifact_type": "brand-binding",
                    "artifact_id": str(binding["binding_id"]),
                    "schema_version": "creative-craft.brand-binding.v1",
                    "path": ".creative-craft/brand-binding.json",
                    "sha256": sha256_file(binding_path),
                },
            ]
        )
        write_atomic(manifest_path, _json_text(manifest))
        validated = validate_project(project_root)
        if not validated.result.ok:
            raise ValueError(
                "updated project is invalid: " + "; ".join(validated.result.errors)
            )
    except Exception:
        _remove_path(staging)
        _restore_brand_state(project_root, backup, existed)
        _cleanup_rolled_back_operation(project_root, backup, existed)
        raise
    if not retain_backup:
        _discard_operation_backup(project_root, backup)
    return backup


def _copy_reference_snapshot_files(source: ReferencePackGraph, target: Path) -> None:
    try:
        target.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(f"reference staging path already exists: {target}") from exc
    relative_files: set[str] = {"reference-pack.json"}
    ledger_relative = str(source.manifest.get("asset_ledger", {}).get("path"))
    relative_files.add(ledger_relative)
    for source_reference in source.manifest.get("source_references", []):
        if not isinstance(source_reference, dict):
            continue
        snapshot_path = source_reference.get("snapshot_path")
        if nonempty(snapshot_path):
            relative_files.add(str(snapshot_path))
    for asset in source.ledger.get("assets", []):
        if not isinstance(asset, dict):
            continue
        value = str(asset.get("path_or_uri", ""))
        if not _is_external_asset_uri(value):
            relative_files.add(value)
    try:
        for relative in sorted(relative_files):
            source_path, error = _safe_relative_path(
                source.root, relative, label="reference snapshot source path"
            )
            if error or source_path is None or not source_path.is_file():
                raise ValueError(
                    error
                    or f"reference snapshot source file does not exist: {relative!r}"
                )
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination)
    except Exception:
        _remove_path(target)
        raise


def _selected_reference_ids(source: ReferencePackGraph, requested: Any) -> list[str]:
    available = {
        str(entity.get("reference_id"))
        for entity in source.manifest.get("entities", [])
        if isinstance(entity, dict)
    }
    selected = (
        [str(item).strip() for item in requested]
        if isinstance(requested, list) and requested
        else sorted(available)
    )
    if not selected:
        raise ValueError(
            "Reference Pack binding requires at least one reference entity"
        )
    if any(not item for item in selected):
        raise ValueError("--select values must be non-empty")
    if len(selected) != len(set(selected)):
        raise ValueError("--select must not repeat a reference_id")
    unknown = sorted(set(selected).difference(available))
    if unknown:
        raise ValueError("selected reference_id does not exist: " + ", ".join(unknown))
    return selected


def _reference_asset_ids(
    source: ReferencePackGraph, selected_reference_ids: Iterable[str]
) -> set[str]:
    selected = set(selected_reference_ids)
    asset_ids: set[str] = set()
    for entity in source.manifest.get("entities", []):
        if not isinstance(entity, dict) or entity.get("reference_id") not in selected:
            continue
        asset_ids.update(str(item) for item in entity.get("asset_refs", []))
    return asset_ids


def _merged_reference_project_ledger(
    project_ledger: dict[str, Any],
    source: ReferencePackGraph,
    selected_asset_ids: set[str],
    old_asset_ids: set[str],
) -> dict[str, Any]:
    merged = copy.deepcopy(project_ledger)
    existing = [
        item
        for item in merged.get("assets", [])
        if isinstance(item, dict) and str(item.get("asset_id")) not in old_asset_ids
    ]
    ids = {str(item.get("asset_id")) for item in existing}
    pack_id = str(source.manifest.get("reference_pack_id"))
    source_assets = {
        str(item.get("asset_id")): item
        for item in source.ledger.get("assets", [])
        if isinstance(item, dict)
    }
    for asset_id in sorted(selected_asset_ids):
        source_asset = source_assets.get(asset_id)
        if source_asset is None:
            raise ValueError(f"selected reference asset does not exist: {asset_id}")
        if asset_id in ids:
            raise ValueError(
                f"reference asset_id collides with a project or another pack asset: {asset_id}"
            )
        ids.add(asset_id)
        asset = copy.deepcopy(source_asset)
        value = str(asset.get("path_or_uri", ""))
        if not _is_external_asset_uri(value):
            asset["path_or_uri"] = (
                f".creative-craft/reference-snapshots/{pack_id}/{Path(value).as_posix()}"
            )
        existing.append(asset)
    merged["assets"] = existing
    return merged


def _backup_reference_state(
    root: Path, reference_pack_id: str, paths: list[Path]
) -> tuple[Path, dict[Path, bool]]:
    suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return _backup_project_state(
        root,
        f".creative-craft/reference-backups/{reference_pack_id}/{suffix}",
        paths,
        label="reference backup path",
    )


def _existing_reference_binding(
    graph: ProjectGraph, reference_pack_id: str
) -> dict[str, Any] | None:
    matches = [
        record
        for (kind, _), record in graph.records.items()
        if kind == "reference-binding"
        and record["data"].get("reference_pack_id") == reference_pack_id
    ]
    if len(matches) > 1:
        raise ValueError(
            f"project has multiple bindings for Reference Pack {reference_pack_id!r}"
        )
    return matches[0] if matches else None


def _install_reference_snapshot(
    project_root: Path,
    source_root: Path,
    args: argparse.Namespace,
    *,
    require_existing_binding: bool,
    retain_backup: bool,
) -> Path:
    project_root = _validated_requested_project_root(project_root)
    graph = validate_project(project_root)
    if not graph.result.ok:
        raise ValueError(
            "project is invalid before Reference Pack update: "
            + "; ".join(graph.result.errors)
        )
    source = validate_reference_pack(source_root)
    if not source.result.ok:
        raise ValueError(
            "Reference Pack is invalid: " + "; ".join(source.result.errors)
        )
    if source.manifest.get("status") == "revoked":
        raise ValueError("cannot bind a revoked Reference Pack")
    if source.manifest.get("status") == "superseded":
        raise ValueError("cannot create a new binding from a superseded Reference Pack")

    reference_pack_id = str(source.manifest.get("reference_pack_id"))
    existing_binding = _existing_reference_binding(graph, reference_pack_id)
    if require_existing_binding and existing_binding is None:
        raise ValueError(
            "update-reference-snapshot requires an existing binding for "
            f"{reference_pack_id!r}"
        )
    if not require_existing_binding and existing_binding is not None:
        raise ValueError(
            f"project already binds {reference_pack_id!r}; use update-reference-snapshot"
        )

    source_uri = getattr(args, "reference_source_uri", None)
    source_commit = getattr(args, "reference_source_commit", None)
    if source_commit and not source_uri:
        raise ValueError("--reference-source-commit requires --reference-source-uri")
    reason = str(
        getattr(args, "reason", None) or "Initial Reference Pack import"
    ).strip()
    imported_by = str(getattr(args, "imported_by", None) or "TBD").strip()
    if not reason or not imported_by:
        raise ValueError("reason and imported_by must be non-empty")
    selected_ids = _selected_reference_ids(source, getattr(args, "select", None))
    selected_asset_ids = _reference_asset_ids(source, selected_ids)

    suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    staging = _require_safe_project_write_path(
        project_root,
        f".creative-craft/reference-snapshots/.{reference_pack_id}.staging-{suffix}",
        label="reference staging path",
    )
    snapshot_path = _require_safe_project_write_path(
        project_root,
        f".creative-craft/reference-snapshots/{reference_pack_id}",
        label="reference snapshot path",
    )
    binding_path = _require_safe_project_write_path(
        project_root,
        f".creative-craft/reference-bindings/{reference_pack_id}.json",
        label="reference binding path",
    )
    manifest_path = graph.manifest_path
    ledger_record = _project_ledger_record(graph)
    ledger_path = Path(ledger_record["path"])
    old_asset_ids: set[str] = set()
    previous_binding_id: str | None = None
    history_path: Path | None = None
    if existing_binding is not None:
        previous_binding_id = str(existing_binding["data"].get("binding_id"))
        history_path = _require_safe_project_write_path(
            project_root,
            f".creative-craft/reference-lineage/{reference_pack_id}/"
            f"{reference_history_filename(previous_binding_id)}",
            label="reference binding history path",
        )
        if history_path.exists():
            raise ValueError(
                f"reference binding history already exists: {history_path.relative_to(project_root)}"
            )
        old_snapshot = validate_reference_pack(snapshot_path)
        if not old_snapshot.result.ok:
            raise ValueError(
                "existing Reference Pack snapshot is invalid: "
                + "; ".join(old_snapshot.result.errors)
            )
        old_asset_ids = _reference_asset_ids(
            old_snapshot, existing_binding["data"].get("selected_reference_ids", [])
        )

    staging_owned = False
    try:
        _copy_reference_snapshot_files(source, staging)
        staging_owned = True
        staged_validation = validate_reference_pack(staging)
        if not staged_validation.result.ok:
            raise ValueError(
                "staged Reference Pack is invalid: "
                + "; ".join(staged_validation.result.errors)
            )
        staged_tree_sha = tree_sha256(staging)
        merged_ledger = _merged_reference_project_ledger(
            ledger_record["data"], source, selected_asset_ids, old_asset_ids
        )
        tracked_paths = [snapshot_path, binding_path, ledger_path, manifest_path]
        if history_path is not None:
            tracked_paths.append(history_path)
        backup, existed = _backup_reference_state(
            project_root, reference_pack_id, tracked_paths
        )
    except Exception:
        if staging_owned:
            _remove_path(staging)
        raise

    try:
        _remove_path(snapshot_path)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        staging.replace(snapshot_path)
        write_atomic(ledger_path, _json_text(merged_ledger))
        imported_at = (
            dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        )
        history: dict[str, Any] | None = None
        if existing_binding is not None and history_path is not None:
            archived_binding = copy.deepcopy(existing_binding["data"])
            history = {
                "schema_version": "creative-craft.reference-binding-history.v1",
                "history_id": previous_binding_id,
                "archived_at": imported_at,
                "binding_sha256": json_content_sha256(archived_binding),
                "binding": archived_binding,
            }
            write_atomic(history_path, _json_text(history))
        binding = {
            "schema_version": "creative-craft.reference-binding.v1",
            "binding_id": (
                f"reference-binding-{graph.manifest.get('project_id')}-"
                f"{reference_pack_id}-{suffix}"
            ),
            "project_id": str(graph.manifest.get("project_id")),
            "reference_pack_id": reference_pack_id,
            "pack_version": str(source.manifest.get("version")),
            "source": {
                "repository_or_uri": source_uri,
                "ref": getattr(args, "reference_source_ref", None),
                "commit": source_commit,
                "pack_sha256": sha256_file(snapshot_path / "reference-pack.json"),
            },
            "snapshot": {
                "path": f".creative-craft/reference-snapshots/{reference_pack_id}",
                "tree_sha256": staged_tree_sha,
            },
            "selected_reference_ids": selected_ids,
            "imported_at": imported_at,
            "imported_by": imported_by,
            "previous_binding_id": previous_binding_id,
            "reason": reason,
        }
        write_atomic(binding_path, _json_text(binding))

        relative_binding_path = binding_path.relative_to(project_root).as_posix()
        manifest = copy.deepcopy(graph.manifest)
        manifest["artifacts"] = [
            item
            for item in manifest.get("artifacts", [])
            if isinstance(item, dict)
            and not (
                item.get("artifact_type") == "reference-pack"
                and item.get("artifact_id") == reference_pack_id
            )
            and not (
                item.get("artifact_type") == "reference-binding"
                and (
                    item.get("artifact_id") == previous_binding_id
                    or item.get("path") == relative_binding_path
                )
            )
        ]
        for item in manifest["artifacts"]:
            if item.get("artifact_type") == "asset-ledger" and Path(
                str(item.get("path"))
            ) == ledger_path.relative_to(project_root):
                item["sha256"] = sha256_file(ledger_path)
        if history is not None and history_path is not None:
            manifest["artifacts"].append(
                {
                    "artifact_type": "reference-binding-history",
                    "artifact_id": str(history["history_id"]),
                    "schema_version": "creative-craft.reference-binding-history.v1",
                    "path": history_path.relative_to(project_root).as_posix(),
                    "sha256": sha256_file(history_path),
                }
            )
        manifest["artifacts"].extend(
            [
                {
                    "artifact_type": "reference-pack",
                    "artifact_id": reference_pack_id,
                    "schema_version": "creative-craft.reference-pack.v1",
                    "path": (
                        f".creative-craft/reference-snapshots/{reference_pack_id}/"
                        "reference-pack.json"
                    ),
                    "sha256": sha256_file(snapshot_path / "reference-pack.json"),
                },
                {
                    "artifact_type": "reference-binding",
                    "artifact_id": str(binding["binding_id"]),
                    "schema_version": "creative-craft.reference-binding.v1",
                    "path": relative_binding_path,
                    "sha256": sha256_file(binding_path),
                },
            ]
        )
        write_atomic(manifest_path, _json_text(manifest))
        validated = validate_project(project_root)
        if not validated.result.ok:
            raise ValueError(
                "updated project is invalid: " + "; ".join(validated.result.errors)
            )
    except Exception:
        _remove_path(staging)
        _restore_brand_state(project_root, backup, existed)
        _cleanup_rolled_back_operation(project_root, backup, existed)
        raise

    if not retain_backup:
        _discard_operation_backup(project_root, backup)
    return backup


def cmd_bind_reference_pack(args: argparse.Namespace) -> int:
    try:
        _install_reference_snapshot(
            Path(args.target).expanduser(),
            Path(args.reference_pack).expanduser(),
            args,
            require_existing_binding=False,
            retain_backup=False,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: failed to bind Reference Pack: {exc}", file=sys.stderr)
        return 1
    reference_pack_id = load_json(
        Path(args.reference_pack).expanduser().resolve() / "reference-pack.json"
    )["reference_pack_id"]
    print(
        Path(args.target).expanduser().resolve()
        / ".creative-craft"
        / "reference-bindings"
        / f"{reference_pack_id}.json"
    )
    return 0


def cmd_update_reference_snapshot(args: argparse.Namespace) -> int:
    try:
        backup = _install_reference_snapshot(
            Path(args.target).expanduser(),
            Path(args.reference_pack).expanduser(),
            args,
            require_existing_binding=True,
            retain_backup=True,
        )
    except (OSError, ValueError) as exc:
        print(
            f"ERROR: failed to update Reference Pack snapshot: {exc}", file=sys.stderr
        )
        return 1
    reference_pack_id = load_json(
        Path(args.reference_pack).expanduser().resolve() / "reference-pack.json"
    )["reference_pack_id"]
    print(f"Backup: {backup}")
    print(
        Path(args.target).expanduser().resolve()
        / ".creative-craft"
        / "reference-bindings"
        / f"{reference_pack_id}.json"
    )
    return 0
