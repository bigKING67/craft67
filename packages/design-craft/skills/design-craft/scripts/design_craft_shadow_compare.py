#!/usr/bin/env python3
"""Create and validate evidence-bound comparisons from isolated Shadow Labs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
sys.dont_write_bytecode = True

from design_craft_shadow_lab import (  # noqa: E402
    ShadowLabError,
    atomic_write_json,
    is_relative_to,
    json_text,
    load_manifest,
    utc_now,
    verify_lab,
)


SPEC_SCHEMA = "design-craft.shadow-lab-comparison-spec.v1"
COMPARISON_SCHEMA = "design-craft.shadow-lab-comparison.v1"
VALIDATION_SCHEMA = "design-craft.shadow-lab-comparison-validation.v1"
MAX_JSON_BYTES = 1024 * 1024
MAX_ARTIFACT_BYTES = 128 * 1024 * 1024
MAX_ARTIFACTS = 64
MAX_VARIANTS = 5
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
RUNTIME_STATUSES = {"passed", "failed", "unverified"}
DECISION_STATUSES = {
    "ready_for_selection",
    "recommended",
    "selected",
    "rejected",
}


class ShadowComparisonError(RuntimeError):
    """Expected comparison contract or evidence failure."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_object(path_value: Path, *, label: str) -> tuple[Path, dict[str, Any]]:
    path = path_value.expanduser().absolute()
    if path.is_symlink() or not path.is_file():
        raise ShadowComparisonError(f"{label} must be an existing regular file")
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ShadowComparisonError(f"{label} exceeds the maximum supported size")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ShadowComparisonError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ShadowComparisonError(f"{label} must contain a JSON object")
    return path, payload


def exact_keys(
    value: dict[str, Any],
    *,
    required: set[str],
    optional: set[str] | None = None,
    label: str,
) -> None:
    optional = optional or set()
    missing = sorted(required - set(value))
    unsupported = sorted(set(value) - required - optional)
    if missing:
        raise ShadowComparisonError(f"{label} is missing fields: {', '.join(missing)}")
    if unsupported:
        raise ShadowComparisonError(
            f"{label} has unsupported fields: {', '.join(unsupported)}"
        )


def text_value(value: Any, *, label: str, minimum: int = 1) -> str:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ShadowComparisonError(f"{label} must contain at least {minimum} characters")
    return value.strip()


def slug_value(value: Any, *, label: str) -> str:
    slug = text_value(value, label=label)
    if not SLUG_PATTERN.fullmatch(slug):
        raise ShadowComparisonError(f"{label} must be a lowercase slug")
    return slug


def string_list(
    value: Any,
    *,
    label: str,
    minimum: int = 0,
    slugs: bool = False,
) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise ShadowComparisonError(f"{label} must contain at least {minimum} entries")
    result: list[str] = []
    for index, item in enumerate(value):
        parsed = (
            slug_value(item, label=f"{label}[{index}]")
            if slugs
            else text_value(item, label=f"{label}[{index}]", minimum=3)
        )
        result.append(parsed)
    if len(set(result)) != len(result):
        raise ShadowComparisonError(f"{label} must not contain duplicates")
    return result


def resolve_spec_path(spec_path: Path, raw: Any, *, label: str) -> Path:
    value = text_value(raw, label=label)
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = spec_path.parent / path
    return path.absolute()


def artifact_record(
    *,
    spec_path: Path,
    value: Any,
    source: Path,
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ShadowComparisonError(f"{label} must be an object")
    exact_keys(value, required={"id", "role", "path"}, label=label)
    artifact_id = slug_value(value["id"], label=f"{label}.id")
    role = slug_value(value["role"], label=f"{label}.role")
    raw_path = resolve_spec_path(spec_path, value["path"], label=f"{label}.path")
    if raw_path.is_symlink():
        raise ShadowComparisonError(f"{label}.path must not be a symlink")
    try:
        path = raw_path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ShadowComparisonError(f"{label}.path does not exist") from exc
    if not path.is_file():
        raise ShadowComparisonError(f"{label}.path must be a regular file")
    if is_relative_to(path, source):
        raise ShadowComparisonError(f"{label}.path must remain outside the source repo")
    byte_count = path.stat().st_size
    if byte_count > MAX_ARTIFACT_BYTES:
        raise ShadowComparisonError(
            f"{label}.path exceeds {MAX_ARTIFACT_BYTES} bytes"
        )
    return {
        "id": artifact_id,
        "role": role,
        "path": str(path),
        "bytes": byte_count,
        "sha256": sha256_file(path),
    }


def runtime_checks(
    value: Any,
    *,
    required_ids: list[str],
    artifact_ids: set[str],
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ShadowComparisonError(f"{label} must be an array")
    checks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict):
            raise ShadowComparisonError(f"{item_label} must be an object")
        exact_keys(
            item,
            required={"id", "status", "evidence_refs", "note"},
            label=item_label,
        )
        check_id = slug_value(item["id"], label=f"{item_label}.id")
        status = text_value(item["status"], label=f"{item_label}.status")
        if status not in RUNTIME_STATUSES:
            raise ShadowComparisonError(
                f"{item_label}.status must be passed, failed, or unverified"
            )
        refs = string_list(
            item["evidence_refs"],
            label=f"{item_label}.evidence_refs",
            minimum=1 if status == "passed" else 0,
            slugs=True,
        )
        missing_refs = sorted(set(refs) - artifact_ids)
        if missing_refs:
            raise ShadowComparisonError(
                f"{item_label} references unknown artifacts: {', '.join(missing_refs)}"
            )
        checks.append(
            {
                "id": check_id,
                "status": status,
                "evidence_refs": refs,
                "note": text_value(item["note"], label=f"{item_label}.note", minimum=8),
            }
        )
        seen.add(check_id)
    if seen != set(required_ids) or len(checks) != len(required_ids):
        raise ShadowComparisonError(
            f"{label} must cover every required runtime check exactly once"
        )
    return checks


def decision_record(value: Any, *, variant_ids: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ShadowComparisonError("decision must be an object")
    exact_keys(
        value,
        required={
            "status",
            "preferred_variant",
            "approval_source",
            "absorb",
            "adapt",
            "reject",
            "unverified",
            "production_promotion_authorized",
        },
        label="decision",
    )
    status = text_value(value["status"], label="decision.status")
    if status not in DECISION_STATUSES:
        raise ShadowComparisonError("decision.status is unsupported")
    preferred = value["preferred_variant"]
    if preferred is not None:
        preferred = slug_value(preferred, label="decision.preferred_variant")
    approval = text_value(value["approval_source"], label="decision.approval_source")
    expected = {
        "ready_for_selection": (None, "none"),
        "recommended": ("variant", "user_delegated"),
        "selected": ("variant", "user_selected"),
        "rejected": (None, "none"),
    }[status]
    if expected[0] is None and preferred is not None:
        raise ShadowComparisonError(
            f"decision.preferred_variant must be null for {status}"
        )
    if expected[0] == "variant" and preferred not in variant_ids:
        raise ShadowComparisonError(
            f"decision.preferred_variant must name a comparison variant for {status}"
        )
    if approval != expected[1]:
        raise ShadowComparisonError(
            f"decision.approval_source must be {expected[1]} for {status}"
        )
    if value["production_promotion_authorized"] is not False:
        raise ShadowComparisonError(
            "comparison closeout must not authorize production promotion"
        )
    return {
        "status": status,
        "preferred_variant": preferred,
        "approval_source": approval,
        "absorb": string_list(value["absorb"], label="decision.absorb"),
        "adapt": string_list(value["adapt"], label="decision.adapt", minimum=1),
        "reject": string_list(value["reject"], label="decision.reject", minimum=1),
        "unverified": string_list(value["unverified"], label="decision.unverified"),
        "production_promotion_authorized": False,
    }


def build_comparison(spec_path_value: Path) -> dict[str, Any]:
    spec_path, spec = load_json_object(spec_path_value, label="comparison spec")
    exact_keys(
        spec,
        required={"schema", "comparison_id", "target", "variants", "decision"},
        label="comparison spec",
    )
    if spec["schema"] != SPEC_SCHEMA:
        raise ShadowComparisonError(f"comparison spec must use {SPEC_SCHEMA}")
    comparison_id = slug_value(spec["comparison_id"], label="comparison_id")

    target = spec["target"]
    if not isinstance(target, dict):
        raise ShadowComparisonError("target must be an object")
    exact_keys(
        target,
        required={
            "surface",
            "user_job",
            "acceptance_rules",
            "required_evidence_roles",
            "required_runtime_checks",
        },
        label="target",
    )
    target_record = {
        "surface": text_value(target["surface"], label="target.surface", minimum=3),
        "user_job": text_value(target["user_job"], label="target.user_job", minimum=8),
        "acceptance_rules": string_list(
            target["acceptance_rules"], label="target.acceptance_rules", minimum=1
        ),
        "required_evidence_roles": string_list(
            target["required_evidence_roles"],
            label="target.required_evidence_roles",
            minimum=1,
            slugs=True,
        ),
        "required_runtime_checks": string_list(
            target["required_runtime_checks"],
            label="target.required_runtime_checks",
            minimum=1,
            slugs=True,
        ),
    }

    raw_variants = spec["variants"]
    if not isinstance(raw_variants, list) or not 2 <= len(raw_variants) <= MAX_VARIANTS:
        raise ShadowComparisonError(
            f"variants must contain between 2 and {MAX_VARIANTS} entries"
        )
    variants: list[dict[str, Any]] = []
    variant_ids: set[str] = set()
    lab_ids: set[str] = set()
    common_source: tuple[str, str] | None = None
    source_path: Path | None = None
    total_artifacts = 0

    for index, raw_variant in enumerate(raw_variants):
        label = f"variants[{index}]"
        if not isinstance(raw_variant, dict):
            raise ShadowComparisonError(f"{label} must be an object")
        exact_keys(
            raw_variant,
            required={
                "id",
                "manifest",
                "axis",
                "hypothesis",
                "invariants",
                "risks",
                "artifacts",
                "runtime_checks",
            },
            label=label,
        )
        variant_id = slug_value(raw_variant["id"], label=f"{label}.id")
        if variant_id in variant_ids:
            raise ShadowComparisonError(f"duplicate variant id: {variant_id}")
        variant_ids.add(variant_id)
        manifest_path_value = resolve_spec_path(
            spec_path, raw_variant["manifest"], label=f"{label}.manifest"
        )
        verification = verify_lab(manifest_path_value)
        if not verification.get("ok"):
            raise ShadowComparisonError(f"{label} source baseline no longer matches")
        manifest_path, manifest = load_manifest(manifest_path_value)
        lab_id = text_value(manifest.get("lab_id"), label=f"{label}.lab_id")
        if lab_id in lab_ids:
            raise ShadowComparisonError("each variant must use a distinct Shadow Lab")
        lab_ids.add(lab_id)
        observed_source = verification["source"]
        source_identity = (
            text_value(observed_source.get("repo_path"), label=f"{label}.source.repo_path"),
            text_value(observed_source.get("commit"), label=f"{label}.source.commit"),
        )
        if common_source is None:
            common_source = source_identity
            source_path = Path(source_identity[0]).resolve(strict=True)
        elif common_source != source_identity:
            raise ShadowComparisonError(
                "all variants must use the same source repository and fixed commit"
            )
        if source_path is None:
            raise ShadowComparisonError("source path resolution failed")
        if is_relative_to(spec_path.resolve(strict=True), source_path):
            raise ShadowComparisonError("comparison spec must remain outside the source repo")

        raw_artifacts = raw_variant["artifacts"]
        if not isinstance(raw_artifacts, list) or not raw_artifacts:
            raise ShadowComparisonError(f"{label}.artifacts must be non-empty")
        artifacts = [
            artifact_record(
                spec_path=spec_path,
                value=item,
                source=source_path,
                label=f"{label}.artifacts[{artifact_index}]",
            )
            for artifact_index, item in enumerate(raw_artifacts)
        ]
        total_artifacts += len(artifacts)
        if total_artifacts > MAX_ARTIFACTS:
            raise ShadowComparisonError(
                f"comparison exceeds the {MAX_ARTIFACTS}-artifact limit"
            )
        artifact_ids = [item["id"] for item in artifacts]
        if len(set(artifact_ids)) != len(artifact_ids):
            raise ShadowComparisonError(f"{label}.artifacts has duplicate ids")
        roles = {item["role"] for item in artifacts}
        missing_roles = sorted(set(target_record["required_evidence_roles"]) - roles)
        if missing_roles:
            raise ShadowComparisonError(
                f"{label}.artifacts is missing roles: {', '.join(missing_roles)}"
            )
        checks = runtime_checks(
            raw_variant["runtime_checks"],
            required_ids=target_record["required_runtime_checks"],
            artifact_ids=set(artifact_ids),
            label=f"{label}.runtime_checks",
        )
        variants.append(
            {
                "id": variant_id,
                "axis": text_value(raw_variant["axis"], label=f"{label}.axis", minimum=8),
                "hypothesis": text_value(
                    raw_variant["hypothesis"],
                    label=f"{label}.hypothesis",
                    minimum=12,
                ),
                "invariants": string_list(
                    raw_variant["invariants"], label=f"{label}.invariants", minimum=1
                ),
                "risks": string_list(
                    raw_variant["risks"], label=f"{label}.risks", minimum=1
                ),
                "lab": {
                    "lab_id": lab_id,
                    "manifest_path": str(manifest_path),
                    "manifest_sha256": sha256_file(manifest_path),
                    "source_unchanged": True,
                    "verified_at": utc_now(),
                    "worktree_sha256": verification["lab"]["sha256"],
                    "file_count": verification["lab"]["file_count"],
                    "total_bytes": verification["lab"]["total_bytes"],
                    "symlink_count": verification["lab"].get("symlink_count", 0),
                },
                "artifacts": artifacts,
                "runtime_checks": checks,
            }
        )

    if common_source is None:
        raise ShadowComparisonError("comparison has no source identity")
    decision = decision_record(spec["decision"], variant_ids=variant_ids)
    return {
        "schema": COMPARISON_SCHEMA,
        "comparison_id": comparison_id,
        "created_at": utc_now(),
        "state": "validated",
        "source": {"repo_path": common_source[0], "commit": common_source[1]},
        "target": target_record,
        "variants": variants,
        "decision": decision,
        "boundary": {
            "source_writes_allowed": False,
            "network_allowed": False,
            "artifacts_repo_external": True,
            "production_promotion_authorized": False,
        },
    }


def validate_comparison(
    manifest_path_value: Path,
    *,
    require_live_labs: bool,
) -> dict[str, Any]:
    manifest_path, payload = load_json_object(
        manifest_path_value, label="comparison manifest"
    )
    if payload.get("schema") != COMPARISON_SCHEMA:
        raise ShadowComparisonError(
            f"comparison manifest must use {COMPARISON_SCHEMA}"
        )
    exact_keys(
        payload,
        required={
            "schema",
            "comparison_id",
            "created_at",
            "state",
            "source",
            "target",
            "variants",
            "decision",
            "boundary",
        },
        label="comparison manifest",
    )
    slug_value(payload["comparison_id"], label="comparison_id")
    if payload["state"] != "validated":
        raise ShadowComparisonError("comparison state must be validated")
    source = payload["source"]
    if not isinstance(source, dict):
        raise ShadowComparisonError("source must be an object")
    exact_keys(source, required={"repo_path", "commit"}, label="source")
    source_path = Path(text_value(source["repo_path"], label="source.repo_path")).resolve(
        strict=True
    )
    commit = text_value(source["commit"], label="source.commit")
    if not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        raise ShadowComparisonError("source.commit must be a full Git object id")
    boundary = payload["boundary"]
    expected_boundary = {
        "source_writes_allowed": False,
        "network_allowed": False,
        "artifacts_repo_external": True,
        "production_promotion_authorized": False,
    }
    if boundary != expected_boundary:
        raise ShadowComparisonError("comparison boundary does not match the zero-write contract")
    if is_relative_to(manifest_path.resolve(strict=True), source_path):
        raise ShadowComparisonError("comparison manifest must remain outside the source repo")

    target = payload["target"]
    if not isinstance(target, dict):
        raise ShadowComparisonError("target must be an object")
    exact_keys(
        target,
        required={
            "surface",
            "user_job",
            "acceptance_rules",
            "required_evidence_roles",
            "required_runtime_checks",
        },
        label="target",
    )
    required_roles = string_list(
        target["required_evidence_roles"],
        label="target.required_evidence_roles",
        minimum=1,
        slugs=True,
    )
    required_checks = string_list(
        target["required_runtime_checks"],
        label="target.required_runtime_checks",
        minimum=1,
        slugs=True,
    )
    text_value(target["surface"], label="target.surface", minimum=3)
    text_value(target["user_job"], label="target.user_job", minimum=8)
    string_list(
        target["acceptance_rules"],
        label="target.acceptance_rules",
        minimum=1,
    )
    variants = payload["variants"]
    if not isinstance(variants, list) or not 2 <= len(variants) <= MAX_VARIANTS:
        raise ShadowComparisonError("comparison must contain two to five variants")
    variant_ids: set[str] = set()
    lab_ids: set[str] = set()
    artifact_count = 0
    live_verified = 0
    for index, variant in enumerate(variants):
        label = f"variants[{index}]"
        if not isinstance(variant, dict):
            raise ShadowComparisonError(f"{label} must be an object")
        exact_keys(
            variant,
            required={
                "id",
                "axis",
                "hypothesis",
                "invariants",
                "risks",
                "lab",
                "artifacts",
                "runtime_checks",
            },
            label=label,
        )
        variant_id = slug_value(variant["id"], label=f"{label}.id")
        if variant_id in variant_ids:
            raise ShadowComparisonError(f"duplicate variant id: {variant_id}")
        variant_ids.add(variant_id)
        text_value(variant["axis"], label=f"{label}.axis", minimum=8)
        text_value(
            variant["hypothesis"],
            label=f"{label}.hypothesis",
            minimum=12,
        )
        string_list(
            variant["invariants"],
            label=f"{label}.invariants",
            minimum=1,
        )
        string_list(variant["risks"], label=f"{label}.risks", minimum=1)
        lab = variant["lab"]
        if not isinstance(lab, dict):
            raise ShadowComparisonError(f"{label}.lab must be an object")
        exact_keys(
            lab,
            required={
                "lab_id",
                "manifest_path",
                "manifest_sha256",
                "source_unchanged",
                "verified_at",
                "worktree_sha256",
                "file_count",
                "total_bytes",
                "symlink_count",
            },
            label=f"{label}.lab",
        )
        lab_id = text_value(lab["lab_id"], label=f"{label}.lab.lab_id")
        if lab_id in lab_ids:
            raise ShadowComparisonError("each variant must use a distinct Shadow Lab")
        lab_ids.add(lab_id)
        if lab["source_unchanged"] is not True:
            raise ShadowComparisonError(f"{label}.lab must record source_unchanged=true")
        if not SHA256_PATTERN.fullmatch(str(lab["manifest_sha256"])):
            raise ShadowComparisonError(f"{label}.lab.manifest_sha256 is invalid")
        if not SHA256_PATTERN.fullmatch(str(lab["worktree_sha256"])):
            raise ShadowComparisonError(f"{label}.lab.worktree_sha256 is invalid")
        for field in ("file_count", "total_bytes", "symlink_count"):
            value = lab[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ShadowComparisonError(f"{label}.lab.{field} must be non-negative")
        if require_live_labs:
            live_manifest_path = Path(
                text_value(lab["manifest_path"], label=f"{label}.lab.manifest_path")
            )
            live_manifest_path, _ = load_manifest(live_manifest_path)
            if sha256_file(live_manifest_path) != lab["manifest_sha256"]:
                raise ShadowComparisonError(f"{label}.lab manifest hash changed")
            verification = verify_lab(live_manifest_path)
            if not verification.get("ok"):
                raise ShadowComparisonError(f"{label}.lab source baseline no longer matches")
            if verification["source"]["repo_path"] != str(source_path):
                raise ShadowComparisonError(f"{label}.lab source repo does not match")
            if verification["source"]["commit"] != commit:
                raise ShadowComparisonError(f"{label}.lab source commit does not match")
            observed_lab = verification["lab"]
            expected_fields = {
                "sha256": "worktree_sha256",
                "file_count": "file_count",
                "total_bytes": "total_bytes",
                "symlink_count": "symlink_count",
            }
            for observed_field, stored_field in expected_fields.items():
                if observed_lab.get(observed_field, 0) != lab[stored_field]:
                    raise ShadowComparisonError(
                        f"{label}.lab {stored_field} changed after closeout"
                    )
            live_verified += 1

        artifacts = variant["artifacts"]
        if not isinstance(artifacts, list) or not artifacts:
            raise ShadowComparisonError(f"{label}.artifacts must be non-empty")
        artifact_ids: set[str] = set()
        roles: set[str] = set()
        for artifact_index, artifact in enumerate(artifacts):
            artifact_label = f"{label}.artifacts[{artifact_index}]"
            if not isinstance(artifact, dict):
                raise ShadowComparisonError(f"{artifact_label} must be an object")
            exact_keys(
                artifact,
                required={"id", "role", "path", "bytes", "sha256"},
                label=artifact_label,
            )
            artifact_id = slug_value(artifact["id"], label=f"{artifact_label}.id")
            if artifact_id in artifact_ids:
                raise ShadowComparisonError(f"{label}.artifacts has duplicate ids")
            artifact_ids.add(artifact_id)
            roles.add(slug_value(artifact["role"], label=f"{artifact_label}.role"))
            path = Path(text_value(artifact["path"], label=f"{artifact_label}.path"))
            if path.is_symlink() or not path.is_file():
                raise ShadowComparisonError(f"{artifact_label}.path must be a regular file")
            path = path.resolve(strict=True)
            if is_relative_to(path, source_path):
                raise ShadowComparisonError(
                    f"{artifact_label}.path must remain outside the source repo"
                )
            byte_count = artifact["bytes"]
            if (
                not isinstance(byte_count, int)
                or isinstance(byte_count, bool)
                or not 0 <= byte_count <= MAX_ARTIFACT_BYTES
            ):
                raise ShadowComparisonError(
                    f"{artifact_label}.bytes must be 0..{MAX_ARTIFACT_BYTES}"
                )
            if not SHA256_PATTERN.fullmatch(str(artifact["sha256"])):
                raise ShadowComparisonError(f"{artifact_label}.sha256 is invalid")
            if path.stat().st_size != byte_count:
                raise ShadowComparisonError(f"{artifact_label}.bytes does not match")
            if sha256_file(path) != artifact["sha256"]:
                raise ShadowComparisonError(f"{artifact_label}.sha256 does not match")
        missing_roles = sorted(set(required_roles) - roles)
        if missing_roles:
            raise ShadowComparisonError(
                f"{label}.artifacts is missing roles: {', '.join(missing_roles)}"
            )
        artifact_count += len(artifacts)
        runtime_checks(
            variant["runtime_checks"],
            required_ids=required_checks,
            artifact_ids=artifact_ids,
            label=f"{label}.runtime_checks",
        )
    if artifact_count > MAX_ARTIFACTS:
        raise ShadowComparisonError(
            f"comparison exceeds the {MAX_ARTIFACTS}-artifact limit"
        )
    decision_record(payload["decision"], variant_ids=variant_ids)
    return {
        "schema": VALIDATION_SCHEMA,
        "ok": True,
        "action": "validate",
        "comparison_id": payload["comparison_id"],
        "variant_count": len(variants),
        "artifact_count": artifact_count,
        "live_labs_required": require_live_labs,
        "live_labs_verified": live_verified,
        "source": {"repo_path": str(source_path), "commit": commit},
        "boundary": expected_boundary,
    }


def output_path(value: Path) -> Path:
    path = value.expanduser().absolute()
    if path.exists() and path.is_symlink():
        raise ShadowComparisonError("output must not be a symlink")
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise ShadowComparisonError("output parent must be an existing real directory")
    return path


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Create and validate evidence-bound Shadow Lab comparisons."
    )
    subcommands = command.add_subparsers(dest="action", required=True)
    create = subcommands.add_parser("create")
    create.add_argument("--spec", required=True, type=Path)
    create.add_argument("--output", required=True, type=Path)
    create.add_argument("--force", action="store_true")
    validate = subcommands.add_parser("validate")
    validate.add_argument("--manifest", required=True, type=Path)
    validate.add_argument("--require-live-labs", action="store_true")
    return command


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        if arguments.action == "create":
            target = output_path(arguments.output)
            if target.exists() and not arguments.force:
                raise ShadowComparisonError(f"refusing to overwrite output: {target}")
            payload = build_comparison(arguments.spec)
            source = Path(payload["source"]["repo_path"]).resolve(strict=True)
            if is_relative_to(target.resolve(strict=False), source):
                raise ShadowComparisonError("comparison output must remain outside the source repo")
            atomic_write_json(target, payload)
            os.chmod(target, 0o600)
            result = {
                "schema": VALIDATION_SCHEMA,
                "ok": True,
                "action": "create",
                "manifest_path": str(target),
                "manifest_sha256": sha256_file(target),
                "comparison": payload,
            }
        else:
            result = validate_comparison(
                arguments.manifest,
                require_live_labs=arguments.require_live_labs,
            )
        sys.stdout.write(json_text(result))
        return 0
    except (
        ShadowComparisonError,
        ShadowLabError,
        json.JSONDecodeError,
        OSError,
        ValueError,
    ) as exc:
        sys.stdout.write(
            json_text(
                {
                    "ok": False,
                    "action": getattr(arguments, "action", "unknown"),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
