from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

from .assurance import validate_assurance
from .configuration import validate_config
from .constants import (
    ARTIFACT_PATHS,
    CONTENT_BOUND_SCHEMA_VERSIONS,
    LEGACY_ARTIFACT_PATHS,
    LEGACY_SCHEMA_VERSION,
    SCHEMA_VERSION,
    SUPPORTED_RUN_SCHEMA_VERSIONS,
)
from .contract_core import (
    ContractError,
)
from .contract_core import (
    non_empty as _non_empty,
)
from .contract_core import (
    run_file as _run_file,
)
from .jsonio import read_json, read_jsonl, sha256_bytes, sha256_json
from .repository import (
    fingerprint_inventory,
    inspect_git,
    inventory_for_mode,
    worktree_fingerprint,
)
from .repository_analysis import build_dependency_map, build_module_map
from .review_validation import (
    _validate_candidates,
    _validate_coverage,
    _validate_coverage_inventory,
    _validate_decisions,
    _validate_findings,
    _validate_quality_model,
    _validate_remediation,
    _validate_repository_maps,
    _validate_review_scope,
)
from .run_evidence_validation import (
    _evidence_references,
    _validate_command_receipts,
    _validate_evidence_registry,
)
from .schema_validation import validate_instance, validate_schema_definition
from .score_validation import validate_scorecard
from .source_anchor import SourceProjection

SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"
DOCUMENT_SCHEMAS = {
    "manifest": "review-manifest.schema.json",
    "reviewScope": "review-scope.schema.json",
    "qualityModel": "quality-model.schema.json",
    "coverage": "coverage.schema.json",
    "moduleMap": "module-map.schema.json",
    "dependencyMap": "dependency-map.schema.json",
    "findings": "findings.schema.json",
    "decisions": "decisions.schema.json",
    "scorecard": "scorecard.schema.json",
    "remediationPlan": "remediation-plan.schema.json",
}
CURRENT_DOCUMENT_SCHEMAS = {
    **DOCUMENT_SCHEMAS,
    "evidenceRegistry": "evidence-registry.schema.json",
}


@cache
def _schema(name: str) -> dict[str, Any]:
    value = read_json(SCHEMA_ROOT / name)
    if not isinstance(value, dict):
        raise ValueError(f"schema {name}: expected an object")
    errors = validate_schema_definition(value)
    if errors:
        raise ValueError(f"schema {name}: {'; '.join(errors)}")
    return value


def _artifact_paths(schema_version: str) -> dict[str, str]:
    if schema_version == LEGACY_SCHEMA_VERSION:
        return LEGACY_ARTIFACT_PATHS
    if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
        return ARTIFACT_PATHS
    raise ContractError([f"review-manifest.schemaVersion: unsupported {schema_version!r}"])


def _document_schemas(schema_version: str) -> dict[str, str]:
    if schema_version == LEGACY_SCHEMA_VERSION:
        return DOCUMENT_SCHEMAS
    if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
        return CURRENT_DOCUMENT_SCHEMAS
    raise ContractError([f"review-manifest.schemaVersion: unsupported {schema_version!r}"])


def _artifact(run_dir: Path, artifact_paths: dict[str, str], key: str) -> Path:
    return _run_file(run_dir, artifact_paths[key])


def load_run(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve(strict=True)
    manifest = read_json(_run_file(run_dir, "review-manifest.json"))
    if not isinstance(manifest, dict):
        raise ContractError(["manifest: expected a JSON object"])
    schema_version = manifest.get("schemaVersion")
    if schema_version not in SUPPORTED_RUN_SCHEMA_VERSIONS:
        raise ContractError([f"review-manifest.schemaVersion: unsupported {schema_version!r}"])
    artifact_paths = _artifact_paths(schema_version)
    result = {
        "manifest": manifest,
        "reviewScope": read_json(_artifact(run_dir, artifact_paths, "reviewScope")),
        "qualityModel": read_json(_artifact(run_dir, artifact_paths, "qualityModel")),
        "coverage": read_json(_artifact(run_dir, artifact_paths, "coverage")),
        "moduleMap": read_json(_artifact(run_dir, artifact_paths, "moduleMap")),
        "dependencyMap": read_json(_artifact(run_dir, artifact_paths, "dependencyMap")),
        "candidates": read_jsonl(_artifact(run_dir, artifact_paths, "candidateLedger")),
        "findings": read_json(_artifact(run_dir, artifact_paths, "findings")),
        "decisions": read_json(_artifact(run_dir, artifact_paths, "decisions")),
        "scorecard": read_json(_artifact(run_dir, artifact_paths, "scorecard")),
        "remediationPlan": read_json(_artifact(run_dir, artifact_paths, "remediationPlan")),
        "commands": read_jsonl(_artifact(run_dir, artifact_paths, "commands")),
        "evidenceRegistry": (
            read_json(_artifact(run_dir, artifact_paths, "evidenceRegistry"))
            if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS
            else None
        ),
        "runState": read_json(_run_file(run_dir, "run-state.json")),
    }
    return result


def _validate_document_header(
    name: str,
    document: Any,
    schema_version: str,
    errors: list[str],
) -> None:
    if not isinstance(document, dict):
        errors.append(f"{name}: expected a JSON object")
        return
    if document.get("schemaVersion") != schema_version:
        errors.append(f"{name}.schemaVersion: expected {schema_version}")


def _validate_run_documents(
    data: dict[str, Any], errors: list[str]
) -> tuple[str, dict[str, str], dict[str, str], dict[str, Any]]:
    manifest = data["manifest"]
    schema_version = manifest.get("schemaVersion")
    document_schemas = _document_schemas(schema_version)
    artifact_paths = _artifact_paths(schema_version)
    for name, schema_name in document_schemas.items():
        errors.extend(
            f"{schema_name}: {error}"
            for error in validate_instance(data[name], _schema(schema_name))
        )
    for index, candidate in enumerate(data["candidates"]):
        errors.extend(
            f"candidate.schema.json[{index}]: {error}"
            for error in validate_instance(candidate, _schema("candidate.schema.json"))
        )
    for index, receipt in enumerate(data["commands"]):
        errors.extend(
            f"command-receipt.schema.json[{index}]: {error}"
            for error in validate_instance(receipt, _schema("command-receipt.schema.json"))
        )
    for name in document_schemas:
        _validate_document_header(name, data[name], schema_version, errors)
    if any(not isinstance(data[name], dict) for name in document_schemas):
        raise ContractError(errors)

    manifest_configuration = manifest.get("configuration")
    errors.extend(
        f"config.schema.json: {error}"
        for error in validate_instance(manifest_configuration, _schema("config.schema.json"))
    )
    if not isinstance(manifest_configuration, dict):
        raise ContractError(errors)
    try:
        validate_config(manifest_configuration)
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"review-manifest.configuration: {error}")
    return schema_version, document_schemas, artifact_paths, manifest_configuration


def _validate_manifest_identity(
    manifest: dict[str, Any],
    configuration: dict[str, Any],
    coverage: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    target = manifest.get("target")
    if not isinstance(target, dict):
        target = {}
    if manifest.get("configFingerprint") != sha256_json(configuration):
        errors.append("review-manifest.configFingerprint: does not match configuration")
    if target.get("sourceFingerprint") != coverage.get("inventoryFingerprint"):
        errors.append("review-manifest.target.sourceFingerprint: does not match coverage")
    identity_seed = {
        "remote": target.get("remote"),
        "revision": target.get("revision"),
        "branch": target.get("branch"),
        "sourceFingerprint": target.get("sourceFingerprint"),
    }
    if target.get("identity") != sha256_json(identity_seed):
        errors.append("review-manifest.target.identity: does not match target fields")
    return target


def _current_source_projection(
    target_root: Path,
    configuration: dict[str, Any],
    *,
    schema_version: str = SCHEMA_VERSION,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str, str, str]:
    records, _, current_diff = inventory_for_mode(
        target_root,
        mode=configuration["mode"],
        scopes=configuration["scope"],
        excludes=configuration["exclude"],
        generated=configuration["generated"],
        vendored=configuration["vendored"],
        diff_base=configuration["diffBase"],
        _legacy_identity=schema_version != SCHEMA_VERSION,
    )
    return (
        records,
        current_diff,
        fingerprint_inventory(records),
        worktree_fingerprint(target_root, records=records),
        inspect_git(target_root, _legacy_identity=schema_version != SCHEMA_VERSION).status,
    )


def _validate_live_source(
    data: dict[str, Any],
    configuration: dict[str, Any],
    target: dict[str, Any],
    schema_version: str,
    errors: list[str],
) -> tuple[
    dict[str, Any] | None,
    dict[str, Any] | None,
    SourceProjection | None,
]:
    run_state = data["runState"]
    if not isinstance(run_state, dict) or not _non_empty(run_state.get("targetRoot")):
        errors.append("run-state.targetRoot: required")
        return None, None, None
    try:
        target_root = Path(run_state["targetRoot"]).resolve(strict=True)
        records, current_diff, current_source, current_worktree, current_status = (
            _current_source_projection(target_root, configuration, schema_version=schema_version)
        )
        module_map = build_module_map(records)
        dependency_map = build_dependency_map(target_root, records)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as error:
        errors.append(f"run-state.targetRoot: source verification failed: {error}")
        return None, None, None

    module_map["schemaVersion"] = schema_version
    dependency_map["schemaVersion"] = schema_version
    if current_source != target.get("sourceFingerprint"):
        errors.append("run-state.targetRoot: source fingerprint changed after preflight")
    if configuration.get("mode") == "diff":
        stored_diff = data["reviewScope"].get("diff")
        if (
            not isinstance(current_diff, dict)
            or not isinstance(stored_diff, dict)
            or current_diff.get("changes") != stored_diff.get("changes")
        ):
            errors.append("run-state.targetRoot: diff scope changed after preflight")
    if current_worktree != run_state.get("worktreeFingerprint"):
        errors.append("run-state.targetRoot: worktree changed after preflight")
    current_status_fingerprint = sha256_bytes(
        current_status.encode("utf-8", errors="surrogateescape")
    )
    if current_status_fingerprint != run_state.get("statusFingerprint"):
        errors.append("run-state.targetRoot: Git status changed after preflight")
    return (
        module_map,
        dependency_map,
        SourceProjection(
            target_root=target_root,
            records={row["path"]: row for row in records},
            diff_base=configuration.get("diffBase"),
        ),
    )


def validate_run(run_dir: Path, *, final: bool = True) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve(strict=True)
    data = load_run(run_dir)
    errors: list[str] = []
    manifest = data["manifest"]
    schema_version, document_schemas, artifact_paths, manifest_configuration = (
        _validate_run_documents(data, errors)
    )
    coverage = data["coverage"]
    target = _validate_manifest_identity(manifest, manifest_configuration, coverage, errors)
    rebuilt_module_map, rebuilt_dependency_map, source_projection = _validate_live_source(
        data, manifest_configuration, target, schema_version, errors
    )
    if rebuilt_module_map is not None and data["moduleMap"] != rebuilt_module_map:
        errors.append("module-map: does not match the current inventory")
    if rebuilt_dependency_map is not None and data["dependencyMap"] != rebuilt_dependency_map:
        errors.append("dependency-map: does not match the current source projection")
    _validate_command_receipts(
        run_dir, data["commands"], manifest_configuration["commands"], errors
    )
    if isinstance(manifest, dict):
        artifacts = manifest.get("artifacts")
        if artifacts != artifact_paths:
            errors.append("review-manifest.artifacts: canonical artifact map mismatch")
        if final and manifest.get("status") not in {"draft", "final"}:
            errors.append("review-manifest.status: expected draft or final")
    if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
        _validate_evidence_registry(
            run_dir,
            data["evidenceRegistry"],
            _evidence_references(data),
            errors,
        )
    _validate_quality_model(data["qualityModel"], errors, final)
    coverage_paths = _validate_coverage(data["coverage"], errors, final)
    _validate_coverage_inventory(data["coverage"], schema_version, source_projection, errors)
    _validate_review_scope(data["reviewScope"], manifest_configuration, coverage_paths, errors)
    _validate_repository_maps(data["moduleMap"], data["dependencyMap"], coverage_paths, errors)
    candidates = _validate_candidates(
        data["candidates"],
        coverage_paths,
        errors,
        final,
        schema_version=schema_version,
        source_projection=source_projection,
    )
    findings = _validate_findings(
        data["findings"],
        candidates,
        coverage_paths,
        errors,
        schema_version=schema_version,
        source_projection=source_projection,
    )
    _validate_decisions(data["decisions"], findings, errors)
    validate_scorecard(
        data["scorecard"],
        findings,
        data["candidates"],
        data["coverage"],
        data["commands"],
        errors,
        schema_version=schema_version,
        final=final,
    )
    validate_assurance(data, run_dir, errors, final=final)
    _validate_remediation(data["remediationPlan"], errors, final)
    if errors:
        raise ContractError(errors)
    return data
