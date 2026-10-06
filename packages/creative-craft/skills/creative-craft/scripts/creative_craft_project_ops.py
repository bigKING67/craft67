"""Project seed, diagnostics, inspection, revision, and delivery CLI operations."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from creative_craft_contracts import (
    ARTIFACT_ID_FIELDS,
    ARTIFACT_REGISTRY,
    PROJECT_MANIFEST_SEED_SCHEMA_VERSIONS,
    PROJECT_SEED_SCHEMA_VERSIONS,
    TEMPLATES_DIR,
    load_json,
    sha256_file,
    validate_data,
    write_atomic,
)
from creative_craft_evaluation import render_result
from creative_craft_packs import _install_brand_snapshot
from creative_craft_project import (
    ProjectGraph,
    _safe_relative_path,
    validate_brand_pack,
    validate_project,
)


def _seed_copy_sources(bind_brand_pack: bool) -> dict[str, Path]:
    copies = {
        "CREATIVE.md": TEMPLATES_DIR / "CREATIVE.md",
        "DELIVERABLES.md": TEMPLATES_DIR / "DELIVERABLES.md",
    }
    if not bind_brand_pack:
        copies["BRAND.md"] = TEMPLATES_DIR / "BRAND.md"
    for schema_version, entry in ARTIFACT_REGISTRY.items():
        template = entry.get("template")
        if template and schema_version in PROJECT_SEED_SCHEMA_VERSIONS:
            copies[f".creative-craft/{template}"] = TEMPLATES_DIR / str(template)
    return copies


def _seed_parent_directory(parent: Path) -> list[Path]:
    missing: list[Path] = []
    current = parent
    while not current.exists() and not current.is_symlink():
        missing.append(current)
        if current == current.parent:
            break
        current = current.parent
    if current.is_symlink():
        raise ValueError(f"seed target parent must not be a symlink: {current}")
    if not current.is_dir():
        raise ValueError(f"seed target parent is not a directory: {current}")
    created: list[Path] = []
    try:
        for path in reversed(missing):
            path.mkdir()
            created.append(path)
    except Exception:
        for path in reversed(created):
            path.rmdir()
        raise
    return created


def _validate_seed_destination(root: Path, relative: str) -> Path:
    path, error = _safe_relative_path(root, relative, label="seed destination")
    if error or path is None:
        raise ValueError(error or f"invalid seed destination: {relative!r}")
    current = root
    for part in Path(relative).parts[:-1]:
        current = current / part
        if current.exists() and not current.is_dir():
            raise ValueError(f"seed destination parent is not a directory: {current}")
    if path.exists() and not path.is_file():
        raise ValueError(f"seed destination is not a regular file: {path}")
    return path


def _write_seed_manifest(target: Path) -> None:
    manifest_entries: list[dict[str, Any]] = []
    fallback_ids = {
        "asset-ledger": "asset-ledger-tbd",
        "concept-routes": "routes-tbd",
    }
    for schema_version, entry in ARTIFACT_REGISTRY.items():
        template = entry.get("template")
        artifact_type = str(entry["kind"])
        if not template or schema_version not in PROJECT_MANIFEST_SEED_SCHEMA_VERSIONS:
            continue
        path = target / ".creative-craft" / str(template)
        data = load_json(path)
        id_field = ARTIFACT_ID_FIELDS.get(artifact_type)
        artifact_id = (
            str(data.get(id_field)) if id_field else fallback_ids[artifact_type]
        )
        manifest_entries.append(
            {
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,
                "schema_version": schema_version,
                "path": path.relative_to(target).as_posix(),
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "schema_version": "creative-craft.project-manifest.v2",
        "project_id": "project-tbd",
        "manifest_id": "manifest-tbd",
        "contract_version": "0.3",
        "copy_policy": "required",
        "artifacts": manifest_entries,
    }
    write_atomic(
        target / ".creative-craft" / "project-manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )


def _seed_project(args: argparse.Namespace) -> tuple[Path, list[str], list[str]]:
    requested_target = Path(args.target).expanduser().absolute()
    if requested_target.is_symlink():
        raise ValueError(f"seed target must not be a symlink: {requested_target}")
    if requested_target.exists() and not requested_target.is_dir():
        raise ValueError(f"seed target is not a directory: {requested_target}")

    brand_pack_value = getattr(args, "brand_pack", None)
    brand_pack = Path(str(brand_pack_value)).expanduser() if brand_pack_value else None
    if brand_pack is not None:
        source = validate_brand_pack(brand_pack)
        if not source.result.ok:
            raise ValueError(
                "Brand Pack is invalid: " + "; ".join(source.result.errors)
            )
        if source.manifest.get("status") == "revoked":
            raise ValueError("cannot bind a revoked Brand Pack")
        if getattr(args, "brand_source_commit", None) and not getattr(
            args, "brand_source_uri", None
        ):
            raise ValueError("--brand-source-commit requires --brand-source-uri")

    created_parents = _seed_parent_directory(requested_target.parent)
    transaction: Path | None = None
    committed = False
    try:
        target = requested_target.resolve()
        copies = _seed_copy_sources(brand_pack is not None)
        destinations = {
            relative: _validate_seed_destination(target, relative)
            for relative in copies
        }
        if brand_pack is not None:
            for relative in (
                "BRAND.md",
                ".creative-craft/asset-ledger.json",
                ".creative-craft/project-manifest.json",
                ".creative-craft/brand-binding.json",
                ".creative-craft/brand-snapshot",
            ):
                _validate_seed_destination(target, relative)
        conflicts = [
            path
            for path in destinations.values()
            if path.exists() and not bool(args.force)
        ]
        if conflicts:
            formatted = "; ".join(str(path) for path in conflicts)
            raise ValueError(
                "refusing to overwrite existing files: "
                f"{formatted}; use --force only after reviewing the existing authority"
            )

        transaction = Path(
            tempfile.mkdtemp(
                prefix=f".{requested_target.name}.seed-", dir=requested_target.parent
            )
        )
        staged = transaction / "staged"
        target_existed = target.is_dir()
        if target_existed:
            shutil.copytree(target, staged, symlinks=True, copy_function=shutil.copy2)
        else:
            staged.mkdir()

        backup_suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_relatives: list[str] = []
        for relative, source_path in copies.items():
            destination = staged / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and bool(args.force):
                backup = destination.with_name(
                    f"{destination.name}.bak.{backup_suffix}"
                )
                if backup.exists() or backup.is_symlink():
                    raise ValueError(
                        f"seed backup destination already exists: {backup}"
                    )
                shutil.copy2(destination, backup)
                backup_relatives.append(backup.relative_to(staged).as_posix())
            shutil.copy2(source_path, destination)

        _write_seed_manifest(staged)
        if brand_pack is not None:
            _install_brand_snapshot(
                staged,
                brand_pack,
                args,
                require_existing_binding=False,
                retain_backup=False,
            )
        validated = validate_project(staged)
        if not validated.result.ok:
            raise ValueError(
                "staged seed project is invalid: " + "; ".join(validated.result.errors)
            )

        original = transaction / "original"
        if target_existed:
            target.rename(original)
        try:
            staged.rename(target)
        except Exception:
            if target_existed and original.exists() and not target.exists():
                original.rename(target)
            raise
        committed = True
        return target, list(copies), backup_relatives
    finally:
        if transaction is not None:
            shutil.rmtree(transaction, ignore_errors=True)
        if not committed:
            for path in reversed(created_parents):
                if path.is_dir() and not any(path.iterdir()):
                    path.rmdir()


def cmd_seed(args: argparse.Namespace) -> int:
    try:
        target, copied_relatives, backup_relatives = _seed_project(args)
    except (OSError, ValueError) as exc:
        print(f"ERROR: failed to seed project: {exc}", file=sys.stderr)
        return 1
    for relative in backup_relatives:
        print(target / relative)
    for relative in copied_relatives:
        print(target / relative)
    return 0


def cmd_update_brand_snapshot(args: argparse.Namespace) -> int:
    try:
        backup = _install_brand_snapshot(
            Path(args.target).expanduser(),
            Path(args.brand_pack).expanduser(),
            args,
            require_existing_binding=True,
            retain_backup=True,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: failed to update Brand Pack snapshot: {exc}", file=sys.stderr)
        return 1
    print(f"Backup: {backup}")
    print(
        Path(args.target).expanduser().resolve()
        / ".creative-craft"
        / "brand-binding.json"
    )
    return 0


def _write_json_artifact(path: Path, data: dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise ValueError(
            f"refusing to overwrite existing file: {path}; use --force after review"
        )
    if path.exists():
        suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = path.with_name(f"{path.name}.bak.{suffix}")
        shutil.copy2(path, backup)
        print(f"Backup: {backup}")
    write_atomic(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _project_payload(graph: ProjectGraph) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for artifact_type, _ in graph.records:
        counts[artifact_type] = counts.get(artifact_type, 0) + 1
    return {
        "root": str(graph.root),
        "manifest": str(graph.manifest_path),
        "project_id": graph.manifest.get("project_id"),
        "valid": graph.result.ok,
        "artifact_counts": counts,
        "job_statuses": graph.job_statuses,
        "errors": graph.result.errors,
        "warnings": graph.result.warnings,
    }


def _unregistered_project_artifacts(graph: ProjectGraph) -> list[dict[str, Any]]:
    registered_paths = {
        Path(record["path"]).absolute() for record in graph.records.values()
    }
    findings: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()

    def unsafe_symlink_finding(path: Path, artifact_type: str) -> dict[str, Any]:
        return {
            "path": path.relative_to(graph.root).as_posix(),
            "schema_version": None,
            "artifact_type": artifact_type,
            "artifact_id": None,
            "sha256": None,
            "structurally_valid": False,
            "matches_bundled_template": False,
            "classification": "unsafe_symlink",
        }

    template_types = {
        str(entry["template"]): str(entry["kind"])
        for entry in ARTIFACT_REGISTRY.values()
        if entry.get("template")
    }
    scan_roots = (graph.root, graph.root / ".creative-craft")
    for scan_root in scan_roots:
        if scan_root in seen_paths:
            continue
        seen_paths.add(scan_root)
        if scan_root.is_symlink():
            findings.append(unsafe_symlink_finding(scan_root, "project-directory"))
            continue
        if not scan_root.is_dir():
            continue
        for path in sorted(scan_root.glob("*.json"), key=lambda item: item.name):
            absolute_path = path.absolute()
            if absolute_path in seen_paths:
                continue
            seen_paths.add(absolute_path)
            if path.is_symlink():
                artifact_type = (
                    "project-manifest"
                    if path.name == "project-manifest.json"
                    else template_types.get(path.name, "unknown")
                )
                findings.append(unsafe_symlink_finding(path, artifact_type))
                continue
            if not path.is_file() or absolute_path in registered_paths:
                continue
            try:
                data = load_json(path)
            except ValueError:
                continue
            schema_version = str(data.get("schema_version"))
            entry = ARTIFACT_REGISTRY.get(schema_version)
            if entry is None or entry["kind"] == "project-manifest":
                continue

            artifact_type = str(entry["kind"])
            id_field = ARTIFACT_ID_FIELDS.get(artifact_type)
            _, result = validate_data(data, artifact_type)
            template_name = entry.get("template")
            template_path = (
                TEMPLATES_DIR / str(template_name) if template_name else None
            )
            digest = sha256_file(path)
            matches_template = bool(
                template_path
                and template_path.is_file()
                and sha256_file(template_path) == digest
            )
            findings.append(
                {
                    "path": path.relative_to(graph.root).as_posix(),
                    "schema_version": schema_version,
                    "artifact_type": artifact_type,
                    "artifact_id": data.get(id_field) if id_field else None,
                    "sha256": digest,
                    "structurally_valid": result.ok,
                    "matches_bundled_template": matches_template,
                    "classification": (
                        "seed_template_residue"
                        if matches_template
                        else "unregistered_artifact"
                    ),
                }
            )
    return findings


def cmd_validate_project(args: argparse.Namespace) -> int:
    graph = validate_project(Path(args.root))
    payload = _project_payload(graph)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{'PASS' if graph.result.ok else 'FAIL'} project: {graph.root}")
        print(f"  Manifest: {graph.manifest_path}")
        print(f"  Artifacts: {sum(payload['artifact_counts'].values())}")
        for job_id, status in sorted(graph.job_statuses.items()):
            print(f"  Job {job_id}: {status}")
        for message in graph.result.errors:
            print(f"  ERROR: {message}")
        for message in graph.result.warnings:
            print(f"  WARN:  {message}")
    return 0 if graph.result.ok else 1


def cmd_doctor_project(args: argparse.Namespace) -> int:
    graph = validate_project(Path(args.root))
    payload = _project_payload(graph)
    unregistered = _unregistered_project_artifacts(graph)
    payload["unregistered_artifacts"] = unregistered
    payload["healthy"] = graph.result.ok and not unregistered
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"{'PASS' if payload['healthy'] else 'FAIL'} project doctor: {graph.root}"
        )
        print(f"  Project graph: {'valid' if graph.result.ok else 'invalid'}")
        print(f"  Unregistered artifacts: {len(unregistered)}")
        for item in unregistered:
            print(
                f"  UNREGISTERED {item['artifact_type']}: {item['path']} "
                f"({item['classification']})"
            )
        for message in graph.result.errors:
            print(f"  ERROR: {message}")
        for message in graph.result.warnings:
            print(f"  WARN:  {message}")
    return 0 if payload["healthy"] else 1


def cmd_project_status(args: argparse.Namespace) -> int:
    graph = validate_project(Path(args.root))
    payload = _project_payload(graph)
    payload["status"] = "valid" if graph.result.ok else "invalid"
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Project status: {payload['status']}")
        print(f"Project ID: {payload['project_id']}")
        for artifact_type, count in sorted(payload["artifact_counts"].items()):
            print(f"  {artifact_type}: {count}")
        for job_id, status in sorted(graph.job_statuses.items()):
            print(f"  {job_id}: {status}")
        for message in graph.result.errors:
            print(f"ERROR: {message}")
    return 0 if graph.result.ok else 1


def cmd_inspect_output(args: argparse.Namespace) -> int:
    job_path = Path(args.job).resolve()
    receipt_path = Path(args.receipt).resolve()
    file_path = Path(args.file).resolve()
    output_path = Path(args.output).resolve()
    try:
        job = load_json(job_path)
        receipt = load_json(receipt_path)
        _, job_result = validate_data(job, "auto")
        _, receipt_result = validate_data(receipt, "execution-receipt")
        if not job_result.ok or not receipt_result.ok:
            raise ValueError("job or receipt is structurally invalid")
        if receipt.get("job_id") != job.get("job_id"):
            raise ValueError("receipt.job_id does not match job.job_id")
        if receipt.get("job_sha256") != sha256_file(job_path):
            raise ValueError("receipt.job_sha256 does not match the job file")
        if not file_path.is_file():
            raise ValueError(f"output file not found: {file_path}")
        digest = sha256_file(file_path)
        matches = [
            item
            for item in receipt.get("outputs", [])
            if isinstance(item, dict) and item.get("sha256") == digest
        ]
        if not matches:
            raise ValueError(
                "output file digest is not present in the execution receipt"
            )
        receipt_output = matches[0]
        now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        inspection = {
            "schema_version": "creative-craft.output-inspection.v1",
            "inspection_id": f"inspection-{receipt_output['asset_id']}",
            "job_id": str(job["job_id"]),
            "receipt_id": str(receipt["receipt_id"]),
            "output_asset_id": str(receipt_output["asset_id"]),
            "output_sha256": digest,
            "inspector": args.inspector,
            "inspected_at": now,
            "findings": [],
            "invariant_checks": [],
            "copy_checks": [],
            "technical_checks": [
                {
                    "id": "file-digest",
                    "status": "pass",
                    "observation": "The inspected file exists and its SHA-256 matches the execution receipt.",
                    "interpretation": "File identity is bound; creative quality has not been inspected.",
                }
            ],
            "rights_checks": [],
            "decision": "deferred",
            "approval": {
                "approved_by": None,
                "approved_at": None,
                "approval_basis": "",
            },
            "remaining_unknowns": [
                "Visual or audiovisual inspection has not been completed.",
                "Invariants, exact copy, technical quality, and rights still require explicit checks.",
            ],
        }
        _write_json_artifact(output_path, inspection, args.force)
    except (KeyError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(output_path)
    return 0


def cmd_start_revision(args: argparse.Namespace) -> int:
    inspection_path = Path(args.inspection).resolve()
    output_path = Path(args.output).resolve()
    try:
        inspection = load_json(inspection_path)
        _, result = validate_data(inspection, "output-inspection")
        if not result.ok:
            raise ValueError(
                "inspection artifact is invalid: " + "; ".join(result.errors)
            )
        revision = {
            "schema_version": "creative-craft.revision-lineage.v1",
            "revision_id": f"revision-{inspection['inspection_id']}",
            "parent_output_ref": (
                f"cc://output-inspection/{inspection['inspection_id']}#/output_asset_id"
            ),
            "parent_inspection_ref": f"cc://output-inspection/{inspection['inspection_id']}#",
            "primary_variable": args.primary_variable,
            "reason": args.reason,
            "change": [],
            "preserve": [],
            "integration_changes": [],
            "new_job_ref": None,
            "new_receipt_ref": None,
            "new_output_ref": None,
            "observed_result": None,
            "comparison": None,
            "decision": "draft",
            "next_action": "Create one new job that changes the primary variable and preserves all locked invariants.",
        }
        _write_json_artifact(output_path, revision, args.force)
    except (KeyError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(output_path)
    return 0


def cmd_verify_delivery(args: argparse.Namespace) -> int:
    graph = validate_project(Path(args.root))
    delivery_path = Path(args.file).resolve()
    delivery_record = next(
        (
            record
            for (artifact_type, _), record in graph.records.items()
            if artifact_type == "delivery" and record["path"] == delivery_path
        ),
        None,
    )
    if delivery_record is None:
        graph.result.errors.append(
            "delivery file is not registered in project-manifest.json"
        )
    elif delivery_record["data"].get("schema_version") != "creative-craft.delivery.v2":
        graph.result.errors.append(
            "verify-delivery requires creative-craft.delivery.v2"
        )
    elif delivery_record["data"].get("status") != "delivered":
        graph.result.errors.append("delivery status is not delivered")
    return render_result(delivery_path, "delivery", graph.result, args.json)
