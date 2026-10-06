"""Project graphs, Pack validation, path safety, and cross-artifact invariants."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from creative_craft_contracts import (
    ARTIFACT_ID_FIELDS,
    ARTIFACT_REGISTRY,
    Result,
    ValidationContext,
    load_json,
    nonempty,
    reference_history_filename,
    sha256_file,
    validate_data,
)


@dataclass
class ProjectGraph:
    root: Path
    manifest_path: Path
    manifest: dict[str, Any]
    records: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    result: Result = field(default_factory=Result)
    job_statuses: dict[str, str] = field(default_factory=dict)

    def record(self, artifact_type: str, artifact_id: str) -> dict[str, Any] | None:
        return self.records.get((artifact_type, artifact_id))


def _project_manifest_path(root: Path) -> Path:
    nested = root / ".creative-craft" / "project-manifest.json"
    direct = root / "project-manifest.json"
    if nested.exists() or nested.is_symlink() or nested.parent.is_symlink():
        return nested
    return direct


def _safe_relative_path(
    root: Path, value: Any, *, label: str = "path"
) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, f"{label} must be a non-empty string"
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None, f"unsafe root-relative {label}: {value!r}"
    candidate = root / relative
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return None, f"{label} must not use a symlink: {value!r}"
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None, f"{label} escapes root: {value!r}"
    return candidate, None


def _safe_project_path(root: Path, value: Any) -> tuple[Path | None, str | None]:
    path, error = _safe_relative_path(root, value, label="project-relative path")
    if error and error.startswith("unsafe root-relative"):
        return path, error.replace(
            "unsafe root-relative project-relative path",
            "unsafe project-relative path",
            1,
        )
    return path, error


def _require_safe_project_write_path(root: Path, value: str, *, label: str) -> Path:
    path, error = _safe_relative_path(root, value, label=label)
    if error or path is None:
        raise ValueError(error or f"{label} is invalid")
    return path


def tree_sha256(root: Path) -> str:
    if not root.is_dir():
        raise ValueError(f"tree root is not a directory: {root}")
    files: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValueError(f"tree contains a symlink: {relative}")
        if path.is_file():
            files.append(path)
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _is_external_asset_uri(value: str) -> bool:
    match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*)://", value)
    return bool(match and match.group(1).lower() != "file")


@dataclass
class BrandPackGraph:
    root: Path
    manifest_path: Path
    manifest: dict[str, Any]
    ledger_path: Path | None = None
    ledger: dict[str, Any] = field(default_factory=dict)
    authority_paths: dict[str, Path] = field(default_factory=dict)
    result: Result = field(default_factory=Result)


def validate_brand_pack(
    root: Path, context: ValidationContext | None = None
) -> BrandPackGraph:
    source_root = Path(root).expanduser()
    root_is_symlink = source_root.is_symlink()
    resolved_root = source_root.resolve()
    manifest_path = resolved_root / "brand-pack.json"
    graph = BrandPackGraph(resolved_root, manifest_path, {})
    graph.result.require(not root_is_symlink, "brand pack root must not be a symlink")
    graph.result.require(
        resolved_root.is_dir(), f"brand pack root is not a directory: {resolved_root}"
    )
    if not resolved_root.is_dir():
        return graph
    if manifest_path.is_symlink():
        graph.result.errors.append("brand-pack.json must not be a symlink")
        return graph
    try:
        manifest = load_json(manifest_path)
    except ValueError as exc:
        graph.result.errors.append(str(exc))
        return graph
    graph.manifest = manifest
    _, manifest_result = validate_data(manifest, "brand-pack", context)
    graph.result.extend(manifest_result)
    if not manifest_result.ok:
        return graph

    for index, item in enumerate(manifest.get("authority_files", [])):
        if not isinstance(item, dict):
            continue
        path, error = _safe_relative_path(
            resolved_root, item.get("path"), label=f"authority_files[{index}].path"
        )
        if error:
            graph.result.errors.append(error)
            continue
        if path is None or not path.is_file():
            graph.result.errors.append(
                f"authority_files[{index}] file does not exist: {item.get('path')!r}"
            )
            continue
        graph.result.require(
            sha256_file(path) == item.get("sha256"),
            f"authority_files[{index}] sha256 mismatch: {item.get('path')}",
        )
        graph.authority_paths[str(item.get("role"))] = path
        if manifest.get("status") == "approved":
            try:
                authority_text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                graph.result.errors.append(
                    f"approved authority file must be UTF-8 text: {item.get('path')}"
                )
            else:
                graph.result.require(
                    not re.search(r"\bTBD\b", authority_text),
                    f"approved authority file still contains TBD: {item.get('path')}",
                )
                graph.result.require(
                    not re.search(
                        r"(?im)^\s*Status:\s*`?UNVERIFIED`?\s*$", authority_text
                    ),
                    f"approved authority file still declares UNVERIFIED: {item.get('path')}",
                )

    ledger_ref = manifest.get("asset_ledger", {})
    if isinstance(ledger_ref, dict):
        ledger_path, error = _safe_relative_path(
            resolved_root, ledger_ref.get("path"), label="asset_ledger.path"
        )
        if error:
            graph.result.errors.append(error)
        elif ledger_path is None or not ledger_path.is_file():
            graph.result.errors.append(
                f"asset ledger file does not exist: {ledger_ref.get('path')!r}"
            )
        else:
            graph.ledger_path = ledger_path
            graph.result.require(
                sha256_file(ledger_path) == ledger_ref.get("sha256"),
                f"asset ledger sha256 mismatch: {ledger_ref.get('path')}",
            )
            try:
                graph.ledger = load_json(ledger_path)
            except ValueError as exc:
                graph.result.errors.append(str(exc))
            else:
                _, ledger_result = validate_data(graph.ledger, "asset-ledger", context)
                graph.result.errors.extend(
                    f"asset ledger: {message}" for message in ledger_result.errors
                )
                graph.result.warnings.extend(
                    f"asset ledger: {message}" for message in ledger_result.warnings
                )
                expected_project_id = f"brand:{manifest.get('brand_id')}"
                graph.result.require(
                    graph.ledger.get("project_id") == expected_project_id,
                    f"asset ledger project_id must be {expected_project_id!r}",
                )
                for index, asset in enumerate(graph.ledger.get("assets", [])):
                    if not isinstance(asset, dict):
                        continue
                    path_or_uri = str(asset.get("path_or_uri", ""))
                    digest = asset.get("sha256")
                    graph.result.require(
                        isinstance(digest, str)
                        and bool(re.fullmatch(r"[0-9a-f]{64}", digest)),
                        f"asset ledger assets[{index}] requires a lowercase SHA-256 digest",
                    )
                    if not _is_external_asset_uri(path_or_uri):
                        asset_path, asset_error = _safe_relative_path(
                            resolved_root,
                            path_or_uri,
                            label=f"asset ledger assets[{index}].path_or_uri",
                        )
                        if asset_error:
                            graph.result.errors.append(asset_error)
                        elif asset_path is None or not asset_path.is_file():
                            graph.result.errors.append(
                                f"asset ledger assets[{index}] local file does not exist: {path_or_uri!r}"
                            )
                        elif isinstance(digest, str):
                            graph.result.require(
                                sha256_file(asset_path) == digest,
                                f"asset ledger assets[{index}] sha256 mismatch: {path_or_uri}",
                            )
                    if manifest.get("status") == "approved":
                        graph.result.require(
                            asset.get("rights_status") in {"CLEARED", "LIMITED"},
                            f"approved brand pack asset {asset.get('asset_id')!r} has unresolved rights",
                        )
                        graph.result.require(
                            asset.get("consent_status")
                            in {"CLEARED", "LIMITED", "NOT_APPLICABLE"},
                            f"approved brand pack asset {asset.get('asset_id')!r} has unresolved consent",
                        )
    return graph


@dataclass
class ReferencePackGraph:
    root: Path
    manifest_path: Path
    manifest: dict[str, Any]
    ledger_path: Path | None = None
    ledger: dict[str, Any] = field(default_factory=dict)
    result: Result = field(default_factory=Result)


def validate_reference_pack(
    root: Path, context: ValidationContext | None = None
) -> ReferencePackGraph:
    source_root = Path(root).expanduser()
    root_is_symlink = source_root.is_symlink()
    resolved_root = source_root.resolve()
    manifest_path = resolved_root / "reference-pack.json"
    graph = ReferencePackGraph(resolved_root, manifest_path, {})
    graph.result.require(
        not root_is_symlink, "reference pack root must not be a symlink"
    )
    graph.result.require(
        resolved_root.is_dir(),
        f"reference pack root is not a directory: {resolved_root}",
    )
    if not resolved_root.is_dir():
        return graph
    if manifest_path.is_symlink():
        graph.result.errors.append("reference-pack.json must not be a symlink")
        return graph
    try:
        manifest = load_json(manifest_path)
    except ValueError as exc:
        graph.result.errors.append(str(exc))
        return graph
    graph.manifest = manifest
    _, manifest_result = validate_data(manifest, "reference-pack", context)
    graph.result.extend(manifest_result)
    if not manifest_result.ok:
        return graph

    ledger_ref = manifest.get("asset_ledger", {})
    if not isinstance(ledger_ref, dict):
        return graph
    ledger_path, error = _safe_relative_path(
        resolved_root, ledger_ref.get("path"), label="asset_ledger.path"
    )
    if error:
        graph.result.errors.append(error)
        return graph
    if ledger_path is None or not ledger_path.is_file():
        graph.result.errors.append(
            f"asset ledger file does not exist: {ledger_ref.get('path')!r}"
        )
        return graph
    graph.ledger_path = ledger_path
    graph.result.require(
        sha256_file(ledger_path) == ledger_ref.get("sha256"),
        f"asset ledger sha256 mismatch: {ledger_ref.get('path')}",
    )
    try:
        graph.ledger = load_json(ledger_path)
    except ValueError as exc:
        graph.result.errors.append(str(exc))
        return graph
    _, ledger_result = validate_data(graph.ledger, "asset-ledger", context)
    graph.result.errors.extend(
        f"asset ledger: {message}" for message in ledger_result.errors
    )
    graph.result.warnings.extend(
        f"asset ledger: {message}" for message in ledger_result.warnings
    )
    expected_project_id = f"reference:{manifest.get('reference_pack_id')}"
    graph.result.require(
        graph.ledger.get("project_id") == expected_project_id,
        f"asset ledger project_id must be {expected_project_id!r}",
    )

    for index, source in enumerate(manifest.get("source_references", [])):
        if not isinstance(source, dict) or source.get("snapshot_path") is None:
            continue
        snapshot_path, snapshot_error = _safe_relative_path(
            resolved_root,
            source.get("snapshot_path"),
            label=f"source_references[{index}].snapshot_path",
        )
        if snapshot_error:
            graph.result.errors.append(snapshot_error)
        elif snapshot_path is None or not snapshot_path.is_file():
            graph.result.errors.append(
                f"source_references[{index}] snapshot file does not exist: "
                f"{source.get('snapshot_path')!r}"
            )
        elif isinstance(source.get("sha256"), str):
            graph.result.require(
                sha256_file(snapshot_path) == source.get("sha256"),
                f"source_references[{index}] snapshot sha256 mismatch: "
                f"{source.get('snapshot_path')}",
            )

    assets: dict[str, dict[str, Any]] = {}
    for index, asset in enumerate(graph.ledger.get("assets", [])):
        if not isinstance(asset, dict):
            continue
        asset_id = str(asset.get("asset_id"))
        graph.result.require(
            asset_id not in assets,
            f"asset ledger assets[{index}] duplicates asset_id {asset_id!r}",
        )
        assets[asset_id] = asset
        path_or_uri = str(asset.get("path_or_uri", ""))
        digest = asset.get("sha256")
        graph.result.require(
            isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", digest)),
            f"asset ledger assets[{index}] requires a lowercase SHA-256 digest",
        )
        if not _is_external_asset_uri(path_or_uri):
            asset_path, asset_error = _safe_relative_path(
                resolved_root,
                path_or_uri,
                label=f"asset ledger assets[{index}].path_or_uri",
            )
            if asset_error:
                graph.result.errors.append(asset_error)
            elif asset_path is None or not asset_path.is_file():
                graph.result.errors.append(
                    f"asset ledger assets[{index}] local file does not exist: {path_or_uri!r}"
                )
            elif isinstance(digest, str):
                graph.result.require(
                    sha256_file(asset_path) == digest,
                    f"asset ledger assets[{index}] sha256 mismatch: {path_or_uri}",
                )

    source_ids = {
        str(source.get("source_id"))
        for source in manifest.get("source_references", [])
        if isinstance(source, dict)
    }
    for entity_index, entity in enumerate(manifest.get("entities", [])):
        if not isinstance(entity, dict):
            continue
        entity_assets: list[dict[str, Any]] = []
        for asset_id in entity.get("asset_refs", []):
            graph.result.require(
                asset_id in assets,
                f"entities[{entity_index}] references unknown asset {asset_id!r}",
            )
            if asset_id in assets:
                entity_assets.append(assets[str(asset_id)])
        for observation in entity.get("observations", []):
            if not isinstance(observation, dict):
                continue
            for evidence_ref in observation.get("evidence_refs", []):
                graph.result.require(
                    evidence_ref in source_ids or evidence_ref in assets,
                    f"observation {observation.get('observation_id')!r} references unknown evidence {evidence_ref!r}",
                )
        if entity.get("rights_policy") == "approved_reference_input":
            graph.result.require(
                bool(entity_assets),
                f"entities[{entity_index}] approved_reference_input requires asset_refs",
            )
            for asset in entity_assets:
                graph.result.require(
                    asset.get("rights_status") in {"CLEARED", "LIMITED"},
                    f"approved reference input {asset.get('asset_id')!r} has unresolved rights",
                )
                graph.result.require(
                    asset.get("consent_status")
                    in {"CLEARED", "LIMITED", "NOT_APPLICABLE"},
                    f"approved reference input {asset.get('asset_id')!r} has unresolved consent",
                )
    return graph


def _json_pointer(value: Any, pointer: str) -> tuple[bool, Any]:
    if pointer in {"", "/"}:
        return True, value
    if not pointer.startswith("/"):
        return False, None
    current = value
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return False, None
    return True, current


CC_REF_PATTERN = re.compile(r"^cc://([a-z0-9-]+)/([^#]+)#(.*)$")


def resolve_evidence_ref(graph: ProjectGraph, reference: Any) -> tuple[bool, Any, str]:
    if not isinstance(reference, str):
        return False, None, "reference must be a string"
    match = CC_REF_PATTERN.fullmatch(reference)
    if not match:
        return False, None, f"invalid Creative Craft reference: {reference!r}"
    artifact_type, artifact_id, pointer = match.groups()
    record = graph.record(artifact_type, artifact_id)
    if record is None:
        return False, None, f"reference target does not exist: {reference!r}"
    found, value = _json_pointer(record["data"], pointer)
    if not found:
        return False, None, f"reference JSON pointer does not exist: {reference!r}"
    return True, value, ""


def _require_record(
    graph: ProjectGraph, artifact_type: str, artifact_id: Any, message: str
) -> dict[str, Any] | None:
    record = graph.record(artifact_type, str(artifact_id))
    graph.result.require(record is not None, message)
    return record


def _project_brand_cross_checks(graph: ProjectGraph) -> None:
    packs = [
        record for (kind, _), record in graph.records.items() if kind == "brand-pack"
    ]
    bindings = [
        record for (kind, _), record in graph.records.items() if kind == "brand-binding"
    ]
    if not packs and not bindings:
        return
    graph.result.require(
        len(packs) == 1, "project must register exactly one brand-pack artifact"
    )
    graph.result.require(
        len(bindings) == 1, "project must register exactly one brand-binding artifact"
    )
    if len(packs) != 1 or len(bindings) != 1:
        return
    pack_record = packs[0]
    binding_record = bindings[0]
    pack = pack_record["data"]
    binding = binding_record["data"]
    graph.result.require(
        binding_record["path"] == graph.root / ".creative-craft" / "brand-binding.json",
        "brand-binding artifact must use .creative-craft/brand-binding.json",
    )
    graph.result.require(
        binding.get("project_id") == graph.manifest.get("project_id"),
        "brand binding project_id differs from project manifest",
    )
    graph.result.require(
        binding.get("brand_id") == pack.get("brand_id"),
        "brand binding brand_id differs from brand pack",
    )
    graph.result.require(
        binding.get("pack_id") == pack.get("pack_id"),
        "brand binding pack_id differs from brand pack",
    )
    graph.result.require(
        binding.get("pack_version") == pack.get("version"),
        "brand binding pack_version differs from brand pack",
    )
    graph.result.require(
        pack.get("status") != "revoked", "project must not bind a revoked brand pack"
    )

    snapshot = binding.get("snapshot", {})
    snapshot_value = snapshot.get("path") if isinstance(snapshot, dict) else None
    graph.result.require(
        snapshot_value == ".creative-craft/brand-snapshot",
        "brand binding snapshot.path must be .creative-craft/brand-snapshot",
    )
    snapshot_path, snapshot_error = _safe_project_path(graph.root, snapshot_value)
    graph.result.require(
        snapshot_error is None, f"brand binding snapshot: {snapshot_error}"
    )
    if snapshot_path is None or not snapshot_path.is_dir():
        graph.result.errors.append("brand binding snapshot directory does not exist")
        return
    expected_pack_path = snapshot_path / "brand-pack.json"
    graph.result.require(
        pack_record["path"] == expected_pack_path,
        "registered brand-pack artifact is not the bound snapshot manifest",
    )
    snapshot_graph = validate_brand_pack(snapshot_path)
    graph.result.errors.extend(
        f"brand snapshot: {message}" for message in snapshot_graph.result.errors
    )
    graph.result.warnings.extend(
        f"brand snapshot: {message}" for message in snapshot_graph.result.warnings
    )
    try:
        actual_tree_sha = tree_sha256(snapshot_path)
    except ValueError as exc:
        graph.result.errors.append(str(exc))
    else:
        graph.result.require(
            actual_tree_sha == snapshot.get("tree_sha256"),
            "brand binding snapshot tree_sha256 mismatch",
        )
    source = binding.get("source", {})
    graph.result.require(
        isinstance(source, dict) and source.get("pack_sha256") == pack_record["sha256"],
        "brand binding source.pack_sha256 differs from snapshot brand-pack.json",
    )

    project_brand = binding.get("project_brand", {})
    project_brand_value = (
        project_brand.get("path") if isinstance(project_brand, dict) else None
    )
    graph.result.require(
        project_brand_value == "BRAND.md",
        "brand binding project_brand.path must be BRAND.md",
    )
    brand_path, brand_error = _safe_project_path(graph.root, project_brand_value)
    graph.result.require(
        brand_error is None, f"brand binding project_brand: {brand_error}"
    )
    if brand_path is None or not brand_path.is_file():
        graph.result.errors.append("bound project BRAND.md does not exist")
        return
    brand_digest = sha256_file(brand_path)
    graph.result.require(
        brand_digest == project_brand.get("sha256"),
        "brand binding project_brand.sha256 mismatch",
    )
    brand_authority = next(
        (
            item
            for item in pack.get("authority_files", [])
            if isinstance(item, dict) and item.get("role") == "brand"
        ),
        None,
    )
    if isinstance(brand_authority, dict):
        graph.result.require(
            brand_digest == brand_authority.get("sha256"),
            "project BRAND.md differs from snapshot brand authority",
        )


def _project_reference_cross_checks(graph: ProjectGraph) -> None:
    pack_records = [
        record
        for (kind, _), record in graph.records.items()
        if kind == "reference-pack"
    ]
    binding_records = [
        record
        for (kind, _), record in graph.records.items()
        if kind == "reference-binding"
    ]
    history_records = [
        record
        for (kind, _), record in graph.records.items()
        if kind == "reference-binding-history"
    ]
    if not pack_records and not binding_records and not history_records:
        return

    packs: dict[str, dict[str, Any]] = {}
    for record in pack_records:
        pack_id = str(record["data"].get("reference_pack_id"))
        graph.result.require(
            pack_id not in packs, f"duplicate reference-pack artifact for {pack_id!r}"
        )
        packs[pack_id] = record
    bindings: dict[str, dict[str, Any]] = {}
    for record in binding_records:
        pack_id = str(record["data"].get("reference_pack_id"))
        graph.result.require(
            pack_id not in bindings, f"duplicate reference binding for {pack_id!r}"
        )
        bindings[pack_id] = record
    graph.result.require(
        set(packs) == set(bindings),
        "every reference pack must have exactly one matching reference binding",
    )

    histories: dict[str, dict[str, dict[str, Any]]] = {}
    for record in history_records:
        history = record["data"]
        archived_binding = history.get("binding", {})
        if not isinstance(archived_binding, dict):
            continue
        pack_id = str(archived_binding.get("reference_pack_id"))
        history_id = str(history.get("history_id"))
        pack_histories = histories.setdefault(pack_id, {})
        graph.result.require(
            history_id not in pack_histories,
            f"duplicate reference binding history {history_id!r}",
        )
        pack_histories[history_id] = record
        expected_history_path = (
            graph.root
            / ".creative-craft"
            / "reference-lineage"
            / pack_id
            / reference_history_filename(history_id)
        )
        graph.result.require(
            record["path"] == expected_history_path,
            f"reference binding history {history_id!r} uses a non-canonical path",
        )
        graph.result.require(
            archived_binding.get("project_id") == graph.manifest.get("project_id"),
            f"reference binding history {history_id!r} project_id differs from project manifest",
        )
        graph.result.require(
            pack_id in packs,
            f"reference binding history {history_id!r} has no current Reference Pack",
        )

    project_ledgers = [
        record for (kind, _), record in graph.records.items() if kind == "asset-ledger"
    ]
    project_assets = {
        str(asset.get("asset_id")): asset
        for record in project_ledgers
        for asset in record["data"].get("assets", [])
        if isinstance(asset, dict)
    }
    for pack_id in sorted(set(packs).intersection(bindings)):
        pack_record = packs[pack_id]
        binding_record = bindings[pack_id]
        pack = pack_record["data"]
        binding = binding_record["data"]
        expected_binding_path = (
            graph.root / ".creative-craft" / "reference-bindings" / f"{pack_id}.json"
        )
        graph.result.require(
            binding_record["path"] == expected_binding_path,
            f"reference binding {pack_id!r} uses a non-canonical path",
        )
        graph.result.require(
            binding.get("project_id") == graph.manifest.get("project_id"),
            f"reference binding {pack_id!r} project_id differs from project manifest",
        )
        graph.result.require(
            binding.get("pack_version") == pack.get("version"),
            f"reference binding {pack_id!r} pack_version differs from reference pack",
        )
        graph.result.require(
            pack.get("status") != "revoked",
            f"project must not bind revoked reference pack {pack_id!r}",
        )
        if pack.get("status") == "draft":
            graph.result.warnings.append(
                f"reference pack {pack_id!r} is draft; treat its contents as exploratory evidence"
            )
        elif pack.get("status") == "superseded":
            graph.result.warnings.append(
                f"reference pack {pack_id!r} is superseded; preserve it only as historical evidence"
            )

        pack_histories = histories.get(pack_id, {})
        current_binding_id = str(binding.get("binding_id"))
        graph.result.require(
            current_binding_id not in pack_histories,
            f"current reference binding {current_binding_id!r} must not also be archived",
        )
        visited: set[str] = set()
        predecessor = binding.get("previous_binding_id")
        while predecessor is not None:
            predecessor_id = str(predecessor)
            if predecessor_id in visited:
                graph.result.errors.append(
                    f"reference binding lineage for {pack_id!r} contains a cycle at {predecessor_id!r}"
                )
                break
            visited.add(predecessor_id)
            history_record = pack_histories.get(predecessor_id)
            if history_record is None:
                graph.result.errors.append(
                    f"reference binding {current_binding_id!r} has unresolved predecessor "
                    f"{predecessor_id!r}"
                )
                break
            archived_binding = history_record["data"].get("binding", {})
            if not isinstance(archived_binding, dict):
                break
            graph.result.require(
                archived_binding.get("project_id") == binding.get("project_id"),
                f"reference binding predecessor {predecessor_id!r} belongs to another project",
            )
            graph.result.require(
                archived_binding.get("reference_pack_id") == pack_id,
                f"reference binding predecessor {predecessor_id!r} belongs to another pack",
            )
            predecessor = archived_binding.get("previous_binding_id")
        graph.result.require(
            visited == set(pack_histories),
            f"reference binding lineage for {pack_id!r} contains orphan history records",
        )

        snapshot = binding.get("snapshot", {})
        snapshot_value = snapshot.get("path") if isinstance(snapshot, dict) else None
        expected_snapshot_value = f".creative-craft/reference-snapshots/{pack_id}"
        graph.result.require(
            snapshot_value == expected_snapshot_value,
            f"reference binding {pack_id!r} snapshot.path must be {expected_snapshot_value}",
        )
        snapshot_path, snapshot_error = _safe_project_path(graph.root, snapshot_value)
        graph.result.require(
            snapshot_error is None,
            f"reference binding {pack_id!r} snapshot: {snapshot_error}",
        )
        if snapshot_path is None or not snapshot_path.is_dir():
            graph.result.errors.append(
                f"reference binding {pack_id!r} snapshot directory does not exist"
            )
            continue
        graph.result.require(
            pack_record["path"] == snapshot_path / "reference-pack.json",
            f"registered reference pack {pack_id!r} is not the bound snapshot manifest",
        )
        snapshot_graph = validate_reference_pack(snapshot_path)
        graph.result.errors.extend(
            f"reference snapshot {pack_id!r}: {message}"
            for message in snapshot_graph.result.errors
        )
        graph.result.warnings.extend(
            f"reference snapshot {pack_id!r}: {message}"
            for message in snapshot_graph.result.warnings
        )
        try:
            actual_tree_sha = tree_sha256(snapshot_path)
        except ValueError as exc:
            graph.result.errors.append(str(exc))
        else:
            graph.result.require(
                actual_tree_sha == snapshot.get("tree_sha256"),
                f"reference binding {pack_id!r} snapshot tree_sha256 mismatch",
            )
        source = binding.get("source", {})
        graph.result.require(
            isinstance(source, dict)
            and source.get("pack_sha256") == pack_record["sha256"],
            f"reference binding {pack_id!r} source.pack_sha256 differs from snapshot",
        )

        entities = {
            str(entity.get("reference_id")): entity
            for entity in pack.get("entities", [])
            if isinstance(entity, dict)
        }
        selected_ids = binding.get("selected_reference_ids", [])
        for reference_id in selected_ids:
            graph.result.require(
                reference_id in entities,
                f"reference binding {pack_id!r} selects unknown reference {reference_id!r}",
            )
            entity = entities.get(str(reference_id), {})
            for asset_id in entity.get("asset_refs", []):
                graph.result.require(
                    asset_id in project_assets,
                    f"reference binding {pack_id!r} selected asset {asset_id!r} is absent from project ledger",
                )
                source_asset = next(
                    (
                        asset
                        for asset in snapshot_graph.ledger.get("assets", [])
                        if isinstance(asset, dict) and asset.get("asset_id") == asset_id
                    ),
                    None,
                )
                project_asset = project_assets.get(str(asset_id))
                if source_asset and project_asset:
                    source_value = str(source_asset.get("path_or_uri"))
                    expected_value = (
                        source_value
                        if _is_external_asset_uri(source_value)
                        else f"{expected_snapshot_value}/{Path(source_value).as_posix()}"
                    )
                    graph.result.require(
                        project_asset.get("path_or_uri") == expected_value,
                        f"reference binding {pack_id!r} asset {asset_id!r} path differs from snapshot",
                    )
                    graph.result.require(
                        project_asset.get("sha256") == source_asset.get("sha256"),
                        f"reference binding {pack_id!r} asset {asset_id!r} digest differs from snapshot",
                    )


def _project_cross_checks(graph: ProjectGraph) -> None:
    _project_brand_cross_checks(graph)
    _project_reference_cross_checks(graph)
    copy_required = (
        graph.manifest.get("schema_version") == "creative-craft.project-manifest.v2"
        and graph.manifest.get("copy_policy") == "required"
    )
    bound_brand_packs = [
        record["data"]
        for (kind, _), record in graph.records.items()
        if kind == "brand-pack"
    ]
    has_brand_binding = any(kind == "brand-binding" for kind, _ in graph.records)
    assets: dict[str, dict[str, Any]] = {}
    for (artifact_type, _), record in graph.records.items():
        if artifact_type == "asset-ledger":
            for asset in record["data"].get("assets", []):
                if isinstance(asset, dict) and isinstance(asset.get("asset_id"), str):
                    asset_id = asset["asset_id"]
                    graph.result.require(
                        asset_id not in assets,
                        f"duplicate asset_id across ledgers: {asset_id}",
                    )
                    assets[asset_id] = asset

    routes_by_brief: dict[str, dict[str, dict[str, Any]]] = {}
    for (artifact_type, _), record in graph.records.items():
        data = record["data"]
        if artifact_type == "asset-ledger":
            graph.result.require(
                data.get("project_id") == graph.manifest.get("project_id"),
                "asset ledger project_id differs from project manifest",
            )
        if artifact_type == "concept-routes":
            brief_id = data.get("brief_id")
            _require_record(
                graph,
                "brief",
                brief_id,
                f"concept routes references missing brief_id {brief_id!r}",
            )
            route_map = routes_by_brief.setdefault(str(brief_id), {})
            for route in data.get("routes", []):
                if isinstance(route, dict) and isinstance(route.get("route_id"), str):
                    graph.result.require(
                        route["route_id"] not in route_map,
                        f"duplicate route_id across route artifacts: {route['route_id']}",
                    )
                    route_map[route["route_id"]] = route

    for (artifact_type, artifact_id), record in graph.records.items():
        data = record["data"]
        if artifact_type == "creative-direction":
            brief_id = data.get("brief_id")
            route_id = data.get("selected_route_id")
            _require_record(
                graph,
                "brief",
                brief_id,
                f"direction {artifact_id} references missing brief_id {brief_id!r}",
            )
            graph.result.require(
                route_id in routes_by_brief.get(str(brief_id), {}),
                f"direction {artifact_id} selected_route_id does not belong to its brief",
            )
            selected_route = routes_by_brief.get(str(brief_id), {}).get(str(route_id))
            if selected_route:
                graph.result.require(
                    selected_route.get("decision") in {"SELECT", "SELECT_FOR_TEST"},
                    f"direction {artifact_id} selected route is not selected for production",
                )
            for ref in data.get("reference_roles", []):
                if isinstance(ref, dict):
                    graph.result.require(
                        ref.get("asset_id") in assets,
                        f"direction {artifact_id} references unknown asset {ref.get('asset_id')!r}",
                    )

        if artifact_type == "copy-sheet":
            brief_id = data.get("brief_id")
            direction = _require_record(
                graph,
                "creative-direction",
                data.get("direction_id"),
                f"copy sheet {artifact_id} references missing direction_id {data.get('direction_id')!r}",
            )
            _require_record(
                graph,
                "brief",
                brief_id,
                f"copy sheet {artifact_id} references missing brief_id {brief_id!r}",
            )
            if direction:
                graph.result.require(
                    direction["data"].get("brief_id") == brief_id,
                    f"copy sheet {artifact_id} brief_id differs from direction",
                )
                graph.result.require(
                    direction["data"].get("selected_route_id")
                    == data.get("selected_route_id"),
                    f"copy sheet {artifact_id} selected_route_id differs from direction",
                )
            evidence_groups = [data.get("strategy", {})]
            evidence_groups.extend(data.get("proof_hierarchy", []))
            evidence_groups.extend(data.get("copy_routes", []))
            evidence_groups.extend(data.get("copy_units", []))
            for evidence_item in evidence_groups:
                if not isinstance(evidence_item, dict):
                    continue
                for reference in evidence_item.get("evidence_refs", []):
                    ok, _, message = resolve_evidence_ref(graph, reference)
                    graph.result.require(
                        ok,
                        f"copy sheet {artifact_id} evidence_ref is invalid: {message}",
                    )

        if artifact_type == "critique":
            graph.result.require(
                data.get("asset_id") in assets,
                f"critique {artifact_id} references unknown asset {data.get('asset_id')!r}",
            )

        if artifact_type in {"image", "video"} and data.get(
            "schema_version", ""
        ).endswith(".v2"):
            brief_id = data.get("brief_id")
            direction = _require_record(
                graph,
                "creative-direction",
                data.get("direction_id"),
                f"job {artifact_id} references missing direction_id {data.get('direction_id')!r}",
            )
            brief = _require_record(
                graph,
                "brief",
                brief_id,
                f"job {artifact_id} references missing brief_id {brief_id!r}",
            )
            if direction:
                graph.result.require(
                    direction["data"].get("brief_id") == brief_id,
                    f"job {artifact_id} brief_id differs from direction",
                )
                graph.result.require(
                    direction["data"].get("selected_route_id")
                    == data.get("selected_route_id"),
                    f"job {artifact_id} selected_route_id differs from direction",
                )
            if copy_required:
                copy_sheet_id = data.get("copy_sheet_id")
                graph.result.require(
                    nonempty(copy_sheet_id),
                    f"copy-bound job {artifact_id} requires copy_sheet_id",
                )
                graph.result.require(
                    isinstance(data.get("copy_unit_refs"), list),
                    f"copy-bound job {artifact_id} requires copy_unit_refs",
                )
                copy_sheet = _require_record(
                    graph,
                    "copy-sheet",
                    copy_sheet_id,
                    f"job {artifact_id} references missing copy_sheet_id {copy_sheet_id!r}",
                )
                if copy_sheet:
                    sheet_data = copy_sheet["data"]
                    graph.result.require(
                        sheet_data.get("brief_id") == brief_id,
                        f"job {artifact_id} brief_id differs from copy sheet",
                    )
                    graph.result.require(
                        sheet_data.get("direction_id") == data.get("direction_id"),
                        f"job {artifact_id} direction_id differs from copy sheet",
                    )
                    graph.result.require(
                        sheet_data.get("selected_route_id")
                        == data.get("selected_route_id"),
                        f"job {artifact_id} selected_route_id differs from copy sheet",
                    )
                    unit_ids = {
                        str(item.get("unit_id"))
                        for item in sheet_data.get("copy_units", [])
                        if isinstance(item, dict)
                    }
                    for unit_id in data.get("copy_unit_refs", []):
                        graph.result.require(
                            unit_id in unit_ids,
                            f"job {artifact_id} references unknown copy unit {unit_id!r}",
                        )
                    if data.get("declared_status") == "ready":
                        graph.result.require(
                            sheet_data.get("status") in {"reviewed", "approved"},
                            f"ready job {artifact_id} requires a reviewed or approved copy sheet",
                        )
                        if sheet_data.get("use_scope") == "public":
                            approval = sheet_data.get("approval", {})
                            graph.result.require(
                                sheet_data.get("status") == "approved"
                                and approval.get("status") == "approved"
                                and nonempty(approval.get("approved_by")),
                                f"public ready job {artifact_id} requires named owner approval",
                            )
            referenced_assets = set(data.get("asset_refs", []))
            if artifact_type == "image":
                referenced_assets.update(
                    ref.get("asset_id")
                    for ref in data.get("prompt", {}).get("references", [])
                    if isinstance(ref, dict)
                )
            else:
                referenced_assets.update(
                    ref.get("asset_id")
                    for ref in data.get("references", [])
                    if isinstance(ref, dict)
                )
            for asset_id_ref in referenced_assets:
                graph.result.require(
                    asset_id_ref in assets,
                    f"job {artifact_id} references unknown asset {asset_id_ref!r}",
                )
            if data.get("declared_status") == "ready":
                if has_brand_binding:
                    graph.result.require(
                        len(bound_brand_packs) == 1
                        and bound_brand_packs[0].get("status") == "approved",
                        f"ready job {artifact_id} requires an approved bound brand pack",
                    )
                graph.result.require(
                    bool(brief and brief["data"].get("status") == "locked"),
                    f"ready job {artifact_id} requires a locked brief",
                )
                graph.result.require(
                    bool(
                        direction
                        and direction["data"].get("status") in {"locked", "approved"}
                    ),
                    f"ready job {artifact_id} requires a locked or approved direction",
                )
                graph.result.require(
                    data.get("rights", {}).get("status") in {"CLEARED", "LIMITED"},
                    f"ready job {artifact_id} has unresolved rights",
                )
                for asset_id_ref in referenced_assets:
                    asset = assets.get(str(asset_id_ref), {})
                    graph.result.require(
                        asset.get("rights_status") in {"CLEARED", "LIMITED"},
                        f"ready job {artifact_id} asset {asset_id_ref!r} has unresolved rights",
                    )
                    graph.result.require(
                        asset.get("consent_status")
                        in {"CLEARED", "LIMITED", "NOT_APPLICABLE"},
                        f"ready job {artifact_id} asset {asset_id_ref!r} has unresolved consent",
                    )

        if artifact_type == "execution-receipt":
            job = graph.record("image", str(data.get("job_id"))) or graph.record(
                "video", str(data.get("job_id"))
            )
            graph.result.require(
                job is not None,
                f"receipt {artifact_id} references missing job_id {data.get('job_id')!r}",
            )
            if job:
                graph.result.require(
                    job["data"].get("schema_version")
                    in {"creative-craft.image-job.v2", "creative-craft.video-job.v2"},
                    f"receipt {artifact_id} requires a v2 job",
                )
                graph.result.require(
                    data.get("job_sha256") == job["sha256"],
                    f"receipt {artifact_id} job_sha256 does not match job artifact",
                )
                graph.result.require(
                    data.get("provider_profile") == job["data"].get("provider_profile"),
                    f"receipt {artifact_id} provider_profile differs from job",
                )
                graph.result.require(
                    data.get("execution_surface")
                    == job["data"].get("execution_surface"),
                    f"receipt {artifact_id} execution_surface differs from job",
                )
            for output in data.get("outputs", []):
                if not isinstance(output, dict):
                    continue
                output_path, error = _safe_project_path(graph.root, output.get("path"))
                graph.result.require(error is None, f"receipt {artifact_id}: {error}")
                if output_path and output_path.is_file():
                    graph.result.require(
                        sha256_file(output_path) == output.get("sha256"),
                        f"receipt {artifact_id} output digest mismatch: {output.get('path')}",
                    )
                    graph.result.require(
                        output_path.stat().st_size == output.get("bytes"),
                        f"receipt {artifact_id} output byte size mismatch: {output.get('path')}",
                    )
                else:
                    graph.result.errors.append(
                        f"receipt {artifact_id} output file does not exist: {output.get('path')!r}"
                    )

        if artifact_type == "output-inspection":
            receipt = _require_record(
                graph,
                "execution-receipt",
                data.get("receipt_id"),
                f"inspection {artifact_id} references missing receipt_id {data.get('receipt_id')!r}",
            )
            if receipt:
                graph.result.require(
                    receipt["data"].get("job_id") == data.get("job_id"),
                    f"inspection {artifact_id} job_id differs from receipt",
                )
                matching = [
                    output
                    for output in receipt["data"].get("outputs", [])
                    if isinstance(output, dict)
                    and output.get("asset_id") == data.get("output_asset_id")
                ]
                graph.result.require(
                    bool(matching),
                    f"inspection {artifact_id} output_asset_id is absent from receipt",
                )
                if matching:
                    graph.result.require(
                        matching[0].get("sha256") == data.get("output_sha256"),
                        f"inspection {artifact_id} output_sha256 differs from receipt",
                    )

        if artifact_type == "revision-lineage":
            for key in ("parent_output_ref", "parent_inspection_ref"):
                ok, _, message = resolve_evidence_ref(graph, data.get(key))
                graph.result.require(ok, f"revision {artifact_id}: {message}")
            for key in ("new_job_ref", "new_receipt_ref", "new_output_ref"):
                reference = data.get(key)
                if reference:
                    ok, _, message = resolve_evidence_ref(graph, reference)
                    graph.result.require(ok, f"revision {artifact_id}: {message}")

        if (
            artifact_type == "evaluation"
            and data.get("schema_version") == "creative-craft.evaluation.v2"
        ):
            ok, _, message = resolve_evidence_ref(graph, data.get("target_ref"))
            graph.result.require(ok, f"evaluation {artifact_id}: {message}")
            _require_record(
                graph,
                "brief",
                data.get("brief_id"),
                f"evaluation {artifact_id} references missing brief_id",
            )
            for dimension in data.get("dimensions", []):
                if isinstance(dimension, dict):
                    for reference in dimension.get("evidence_refs", []):
                        ok, _, message = resolve_evidence_ref(graph, reference)
                        graph.result.require(ok, f"evaluation {artifact_id}: {message}")

        if (
            artifact_type == "delivery"
            and data.get("schema_version") == "creative-craft.delivery.v2"
        ):
            graph.result.require(
                data.get("project_id") == graph.manifest.get("project_id"),
                f"delivery {artifact_id} project_id differs from manifest",
            )
            direction = _require_record(
                graph,
                "creative-direction",
                data.get("direction_id"),
                f"delivery {artifact_id} references missing direction_id",
            )
            if direction:
                graph.result.require(
                    direction["data"].get("brief_id") == data.get("brief_id"),
                    f"delivery {artifact_id} brief_id differs from direction",
                )
                graph.result.require(
                    direction["data"].get("selected_route_id")
                    == data.get("selected_route_id"),
                    f"delivery {artifact_id} selected_route_id differs from direction",
                )
            for ref_key in (
                "job_refs",
                "receipt_refs",
                "inspection_refs",
                "revision_refs",
                "evaluation_refs",
            ):
                for reference in data.get(ref_key, []):
                    ok, _, message = resolve_evidence_ref(graph, reference)
                    graph.result.require(ok, f"delivery {artifact_id}: {message}")
            if copy_required and data.get("status") in {"ready", "delivered"}:
                for reference in data.get("job_refs", []):
                    match = CC_REF_PATTERN.fullmatch(str(reference))
                    if not match:
                        continue
                    job_type, job_id, _ = match.groups()
                    if job_type not in {"image", "video"}:
                        continue
                    job = graph.record(job_type, job_id)
                    if not job:
                        continue
                    copy_sheet = graph.record(
                        "copy-sheet", str(job["data"].get("copy_sheet_id"))
                    )
                    graph.result.require(
                        copy_sheet is not None,
                        f"public delivery {artifact_id} job {job_id!r} lacks a copy sheet",
                    )
                    if copy_sheet:
                        sheet_data = copy_sheet["data"]
                        approval = sheet_data.get("approval", {})
                        graph.result.require(
                            sheet_data.get("status") == "approved"
                            and sheet_data.get("use_scope") == "public"
                            and approval.get("status") == "approved"
                            and nonempty(approval.get("approved_by")),
                            f"public delivery {artifact_id} job {job_id!r} requires an approved Copy Sheet with named owner",
                        )
            for index, item in enumerate(data.get("files", [])):
                if not isinstance(item, dict):
                    continue
                job = graph.record("image", str(item.get("job_id"))) or graph.record(
                    "video", str(item.get("job_id"))
                )
                receipt = graph.record("execution-receipt", str(item.get("receipt_id")))
                graph.result.require(
                    job is not None,
                    f"delivery {artifact_id} files[{index}] job does not exist",
                )
                graph.result.require(
                    receipt is not None,
                    f"delivery {artifact_id} files[{index}] receipt does not exist",
                )
                if job:
                    job_type = str(job["entry"].get("artifact_type"))
                    graph.result.require(
                        f"cc://{job_type}/{item.get('job_id')}#"
                        in data.get("job_refs", []),
                        f"delivery {artifact_id} files[{index}] job is absent from job_refs",
                    )
                graph.result.require(
                    f"cc://execution-receipt/{item.get('receipt_id')}#"
                    in data.get("receipt_refs", []),
                    f"delivery {artifact_id} files[{index}] receipt is absent from receipt_refs",
                )
                graph.result.require(
                    f"cc://output-inspection/{item.get('inspection_id')}#"
                    in data.get("inspection_refs", []),
                    f"delivery {artifact_id} files[{index}] inspection is absent from inspection_refs",
                )
                if receipt:
                    graph.result.require(
                        receipt["data"].get("job_id") == item.get("job_id"),
                        f"delivery {artifact_id} files[{index}] receipt/job mismatch",
                    )
                    matching_output = next(
                        (
                            output
                            for output in receipt["data"].get("outputs", [])
                            if isinstance(output, dict)
                            and output.get("asset_id") == item.get("asset_id")
                        ),
                        None,
                    )
                    graph.result.require(
                        matching_output is not None,
                        f"delivery {artifact_id} files[{index}] asset is absent from receipt",
                    )
                    if matching_output:
                        graph.result.require(
                            matching_output.get("sha256") == item.get("sha256"),
                            f"delivery {artifact_id} files[{index}] digest differs from receipt",
                        )
                output_path, error = _safe_project_path(graph.root, item.get("path"))
                graph.result.require(error is None, f"delivery {artifact_id}: {error}")
                if output_path and output_path.is_file():
                    graph.result.require(
                        sha256_file(output_path) == item.get("sha256"),
                        f"delivery {artifact_id} files[{index}] digest mismatch",
                    )
                    graph.result.require(
                        output_path.stat().st_size == item.get("bytes"),
                        f"delivery {artifact_id} files[{index}] byte size mismatch",
                    )
                elif data.get("status") == "delivered":
                    graph.result.errors.append(
                        f"delivery {artifact_id} file does not exist: {item.get('path')!r}"
                    )
                inspection = graph.record(
                    "output-inspection", str(item.get("inspection_id"))
                )
                graph.result.require(
                    inspection is not None,
                    f"delivery {artifact_id} files[{index}] inspection does not exist",
                )
                if inspection:
                    graph.result.require(
                        inspection["data"].get("job_id") == item.get("job_id"),
                        f"delivery {artifact_id} files[{index}] inspection/job mismatch",
                    )
                    graph.result.require(
                        inspection["data"].get("receipt_id") == item.get("receipt_id"),
                        f"delivery {artifact_id} files[{index}] inspection/receipt mismatch",
                    )
                    graph.result.require(
                        inspection["data"].get("output_asset_id")
                        == item.get("asset_id"),
                        f"delivery {artifact_id} files[{index}] inspection/asset mismatch",
                    )
                    graph.result.require(
                        inspection["data"].get("decision") == "approved",
                        f"delivery {artifact_id} files[{index}] inspection is not approved",
                    )
                    graph.result.require(
                        inspection["data"].get("output_sha256") == item.get("sha256"),
                        f"delivery {artifact_id} files[{index}] digest differs from inspection",
                    )


def _project_job_statuses(graph: ProjectGraph) -> None:
    receipts_by_job: dict[str, list[dict[str, Any]]] = {}
    inspections_by_job: dict[str, list[dict[str, Any]]] = {}
    delivered_jobs: set[str] = set()
    for (artifact_type, _), record in graph.records.items():
        if artifact_type == "execution-receipt":
            receipts_by_job.setdefault(str(record["data"].get("job_id")), []).append(
                record
            )
        elif artifact_type == "output-inspection":
            inspections_by_job.setdefault(str(record["data"].get("job_id")), []).append(
                record
            )
        elif (
            artifact_type == "delivery" and record["data"].get("status") == "delivered"
        ):
            delivered_jobs.update(
                str(item.get("job_id"))
                for item in record["data"].get("files", [])
                if isinstance(item, dict)
            )
    for (artifact_type, job_id), record in graph.records.items():
        if artifact_type not in {"image", "video"}:
            continue
        declared = record["data"].get(
            "declared_status", record["data"].get("status", "draft")
        )
        status = str(declared)
        if status == "superseded":
            graph.job_statuses[job_id] = status
            continue
        successful_receipts = [
            receipt
            for receipt in receipts_by_job.get(job_id, [])
            if receipt["data"].get("outcome") in {"succeeded", "partial"}
            and receipt["data"].get("outputs")
        ]
        if successful_receipts:
            status = "generated"
        inspections = inspections_by_job.get(job_id, [])
        if inspections:
            decisions = {item["data"].get("decision") for item in inspections}
            if "approved" in decisions:
                status = "approved"
            elif "needs_revision" in decisions:
                status = "revision_required"
            else:
                status = "inspected"
        if job_id in delivered_jobs:
            status = "delivered"
        graph.job_statuses[job_id] = status


def validate_project(
    root: Path, context: ValidationContext | None = None
) -> ProjectGraph:
    requested_root = root.expanduser().absolute()
    if requested_root.is_symlink():
        manifest_path = _project_manifest_path(requested_root)
        return ProjectGraph(
            requested_root,
            manifest_path,
            {},
            result=Result(
                errors=[f"project root must not be a symlink: {requested_root}"]
            ),
        )
    root = requested_root.resolve()
    context = context or ValidationContext()
    manifest_path = _project_manifest_path(root)
    try:
        manifest_relative = manifest_path.relative_to(root).as_posix()
    except ValueError:
        return ProjectGraph(
            root,
            manifest_path,
            {},
            result=Result(
                errors=[f"project manifest escapes project root: {manifest_path}"]
            ),
        )
    safe_manifest_path, manifest_error = _safe_relative_path(
        root, manifest_relative, label="project manifest path"
    )
    if manifest_error or safe_manifest_path is None:
        return ProjectGraph(
            root,
            manifest_path,
            {},
            result=Result(
                errors=[manifest_error or "project manifest path is invalid"]
            ),
        )
    manifest_path = safe_manifest_path
    try:
        manifest = load_json(manifest_path)
    except ValueError as exc:
        return ProjectGraph(root, manifest_path, {}, result=Result(errors=[str(exc)]))
    graph = ProjectGraph(root, manifest_path, manifest)
    _, manifest_result = validate_data(manifest, "project-manifest", context)
    graph.result.extend(manifest_result)
    if not manifest_result.ok:
        return graph
    for index, entry in enumerate(manifest.get("artifacts", [])):
        if not isinstance(entry, dict):
            continue
        artifact_path, error = _safe_project_path(root, entry.get("path"))
        if error:
            graph.result.errors.append(f"artifacts[{index}]: {error}")
            continue
        if artifact_path is None or not artifact_path.is_file():
            graph.result.errors.append(
                f"artifacts[{index}] file does not exist: {entry.get('path')!r}"
            )
            continue
        actual_sha = sha256_file(artifact_path)
        graph.result.require(
            actual_sha == entry.get("sha256"),
            f"artifacts[{index}] sha256 mismatch: {entry.get('path')}",
        )
        try:
            data = load_json(artifact_path)
        except ValueError as exc:
            graph.result.errors.append(str(exc))
            continue
        schema_version = str(data.get("schema_version"))
        graph.result.require(
            schema_version == entry.get("schema_version"),
            f"artifacts[{index}] schema_version differs from file",
        )
        registry_entry = ARTIFACT_REGISTRY.get(schema_version)
        if registry_entry is None:
            graph.result.errors.append(
                f"artifacts[{index}] has unsupported schema_version"
            )
            continue
        expected_type = str(registry_entry["kind"])
        graph.result.require(
            entry.get("artifact_type") == expected_type,
            f"artifacts[{index}] artifact_type must be {expected_type!r}",
        )
        _, artifact_result = validate_data(data, expected_type, context)
        graph.result.errors.extend(
            f"{entry.get('path')}: {message}" for message in artifact_result.errors
        )
        graph.result.warnings.extend(
            f"{entry.get('path')}: {message}" for message in artifact_result.warnings
        )
        artifact_id = str(entry.get("artifact_id"))
        id_field = ARTIFACT_ID_FIELDS.get(expected_type)
        if id_field:
            graph.result.require(
                data.get(id_field) == artifact_id,
                f"artifacts[{index}] artifact_id differs from file {id_field}",
            )
        key = (expected_type, artifact_id)
        graph.result.require(
            key not in graph.records,
            f"artifacts[{index}] duplicates artifact identity {key}",
        )
        graph.records[key] = {
            "data": data,
            "path": artifact_path,
            "sha256": actual_sha,
            "entry": entry,
        }
    _project_cross_checks(graph)
    _project_job_statuses(graph)
    return graph
