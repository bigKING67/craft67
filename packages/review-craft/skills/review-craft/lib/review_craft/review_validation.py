from __future__ import annotations

import re
from typing import Any

from .constants import (
    DECISIONS,
    FINAL_COVERAGE_DISPOSITIONS,
    PERFORMANCE_CLASSES,
    PRIORITIES,
    PROFILES,
    REMEDIATION_PHASES,
    REVIEW_MODES,
    SCHEMA_VERSION,
    SCORE_DIMENSIONS,
    SEVERITIES,
    VALIDATION_STATUSES,
)
from .contract_core import (
    non_empty as _non_empty,
)
from .contract_core import (
    safe_relative as _safe_relative,
)
from .contract_core import (
    string_list as _string_list,
)
from .source_anchor import SourceProjection, build_source_anchor

_COVERAGE_INVENTORY_FIELDS = (
    "path",
    "kind",
    "sizeBytes",
    "sha256",
    "binary",
    "classification",
    "linkTarget",
    "readError",
    "diffStatus",
    "previousPath",
    "untracked",
    "sourceIdentity",
)


def _validate_quality_model(model: dict[str, Any], errors: list[str], final: bool) -> None:
    for field in ("purpose", "audience"):
        if final and not _non_empty(model.get(field)):
            errors.append(f"quality-model.{field}: required for finalization")
    for field in (
        "criticalPaths",
        "invariants",
        "nonGoals",
        "compatibility",
        "performanceBudgets",
        "reliabilityRequirements",
        "authoritySources",
        "assumptions",
        "unknowns",
    ):
        value = model.get(field)
        if not isinstance(value, list) or not all(_non_empty(item) for item in value):
            errors.append(f"quality-model.{field}: expected an array of strings")
        elif final and field in {"criticalPaths", "invariants", "authoritySources"} and not value:
            errors.append(f"quality-model.{field}: must not be empty for finalization")


def _validate_review_scope(
    review_scope: dict[str, Any],
    configuration: dict[str, Any],
    coverage_paths: set[str],
    errors: list[str],
) -> None:
    mode = review_scope.get("mode")
    _validate_review_mode(mode, configuration, errors)
    _validate_review_dimensions(review_scope.get("dimensions"), configuration, errors)
    _validate_review_profile(review_scope.get("profile"), configuration, errors)
    _validate_diff_scope(mode, review_scope.get("diff"), configuration, coverage_paths, errors)


def _validate_review_mode(mode: Any, configuration: dict[str, Any], errors: list[str]) -> None:
    if mode not in REVIEW_MODES or mode != configuration.get("mode"):
        errors.append("review-scope.mode: must match the canonical configuration")
    focus_dimensions = configuration.get("focusDimensions")
    diff_base = configuration.get("diffBase")
    if mode == "review" and focus_dimensions:
        errors.append("review-scope.mode: review mode cannot declare focus dimensions")
    if mode == "focus" and not focus_dimensions:
        errors.append("review-scope.mode: focus mode requires focus dimensions")
    if mode == "diff" and not _non_empty(diff_base):
        errors.append("review-scope.mode: diff mode requires an immutable diff base")
    if mode != "diff" and diff_base is not None:
        errors.append("review-scope.mode: diffBase is only valid in diff mode")


def _validate_review_dimensions(
    dimensions: Any, configuration: dict[str, Any], errors: list[str]
) -> None:
    canonical_dimensions = [row[0] for row in SCORE_DIMENSIONS]
    if (
        not isinstance(dimensions, list)
        or not dimensions
        or len(dimensions) != len(set(dimensions))
    ):
        errors.append("review-scope.dimensions: expected unique canonical dimensions")
    elif any(item not in canonical_dimensions for item in dimensions):
        errors.append("review-scope.dimensions: contains an unsupported dimension")
    expected_dimensions = configuration.get("focusDimensions") or canonical_dimensions
    if dimensions != expected_dimensions:
        errors.append("review-scope.dimensions: must match configuration focusDimensions")


def _validate_review_profile(
    profile: Any, configuration: dict[str, Any], errors: list[str]
) -> None:
    if not isinstance(profile, dict):
        errors.append("review-scope.profile: expected an object")
        return
    if profile.get("requested") != configuration.get("profile"):
        errors.append("review-scope.profile.requested: must match configuration profile")
    if profile.get("resolved") not in PROFILES - {"auto"}:
        errors.append("review-scope.profile.resolved: unsupported profile")


def _validate_diff_scope(
    mode: Any,
    diff: Any,
    configuration: dict[str, Any],
    coverage_paths: set[str],
    errors: list[str],
) -> None:
    if mode != "diff":
        if diff is not None:
            errors.append("review-scope.diff: must be null outside diff mode")
        return
    if not isinstance(diff, dict):
        errors.append("review-scope.diff: required in diff mode")
        return
    if diff.get("baseRevision") != configuration.get("diffBase"):
        errors.append("review-scope.diff.baseRevision: must match configuration diffBase")
    changes = diff.get("changes")
    if not isinstance(changes, list):
        errors.append("review-scope.diff.changes: expected an array")
        return
    _validate_diff_changes(changes, coverage_paths, errors)


def _validate_diff_changes(changes: list[Any], coverage_paths: set[str], errors: list[str]) -> None:
    seen: set[str] = set()
    for index, change in enumerate(changes):
        prefix = f"review-scope.diff.changes[{index}]"
        if not isinstance(change, dict):
            errors.append(f"{prefix}: expected an object")
            continue
        path = change.get("path")
        if not _safe_relative(path) or path in seen:
            errors.append(f"{prefix}.path: expected a unique safe relative path")
            continue
        seen.add(path)
        if change.get("inScope") is True and path not in coverage_paths:
            errors.append(f"{prefix}.inScope: path is missing from coverage")
        if change.get("inScope") is False and path in coverage_paths:
            errors.append(f"{prefix}.inScope: excluded path appears in coverage")


def _validate_repository_maps(
    module_map: dict[str, Any],
    dependency_map: dict[str, Any],
    coverage_paths: set[str],
    errors: list[str],
) -> None:
    module_ids = _validate_modules(module_map.get("modules"), coverage_paths, errors)
    _validate_dependency_paths(dependency_map, coverage_paths, module_ids, errors)


def _validate_modules(modules: Any, coverage_paths: set[str], errors: list[str]) -> set[str]:
    module_ids: set[str] = set()
    declared_files = 0
    if not isinstance(modules, list):
        errors.append("module-map.modules: expected an array")
        return module_ids
    for index, module in enumerate(modules):
        if not isinstance(module, dict):
            errors.append(f"module-map.modules[{index}]: expected an object")
            continue
        declared_files += _validate_module(module, index, coverage_paths, module_ids, errors)
    if declared_files != len(coverage_paths):
        errors.append(
            "module-map.modules: file counts total "
            f"{declared_files}, expected {len(coverage_paths)}"
        )
    return module_ids


def _validate_module(
    module: dict[str, Any],
    index: int,
    coverage_paths: set[str],
    module_ids: set[str],
    errors: list[str],
) -> int:
    prefix = f"module-map.modules[{index}]"
    identifier = module.get("id")
    if not _non_empty(identifier) or identifier in module_ids:
        errors.append(f"{prefix}.id: expected a unique module ID")
    else:
        module_ids.add(identifier)
    for entry in module.get("entryPoints", []):
        if entry not in coverage_paths:
            errors.append(f"{prefix}.entryPoints: {entry!r} is not in coverage")
    file_count = module.get("fileCount")
    return file_count if isinstance(file_count, int) and not isinstance(file_count, bool) else 0


def _validate_dependency_paths(
    dependency_map: dict[str, Any],
    coverage_paths: set[str],
    module_ids: set[str],
    errors: list[str],
) -> None:
    for index, edge in enumerate(dependency_map.get("edges", [])):
        if not isinstance(edge, dict):
            continue
        for field in ("from", "to"):
            if edge.get(field) not in coverage_paths:
                errors.append(f"dependency-map.edges[{index}].{field}: path is not in coverage")
    for index, skipped in enumerate(dependency_map.get("filesSkipped", [])):
        if isinstance(skipped, dict) and skipped.get("path") not in coverage_paths:
            errors.append(f"dependency-map.filesSkipped[{index}].path: path is not in coverage")
    for index, edge in enumerate(dependency_map.get("moduleEdges", [])):
        if not isinstance(edge, dict):
            continue
        for field in ("from", "to"):
            if edge.get(field) not in module_ids:
                errors.append(f"dependency-map.moduleEdges[{index}].{field}: unknown module")


def _validate_coverage(coverage: dict[str, Any], errors: list[str], final: bool) -> set[str]:
    files = coverage.get("files")
    if not isinstance(files, list):
        errors.append("coverage.files: expected an array")
        return set()
    paths: set[str] = set()
    for index, row in enumerate(files):
        prefix = f"coverage.files[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: expected an object")
            continue
        path = row.get("path")
        if not _safe_relative(path):
            errors.append(f"{prefix}.path: expected a safe repository-relative POSIX path")
        elif path in paths:
            errors.append(f"{prefix}.path: duplicate {path}")
        else:
            paths.add(path)
        disposition = row.get("disposition")
        if final and disposition not in FINAL_COVERAGE_DISPOSITIONS:
            errors.append(f"{prefix}.disposition: unresolved disposition {disposition!r}")
        if disposition == "COVERED_BY_PARENT" and not _safe_relative(row.get("coveredBy")):
            errors.append(f"{prefix}.coveredBy: required for COVERED_BY_PARENT")
        if disposition in {"DEFERRED", "UNREADABLE", "OUT_OF_SCOPE"} and not _non_empty(
            row.get("reason")
        ):
            errors.append(f"{prefix}.reason: required for {disposition}")
        evidence = row.get("evidenceRefs", [])
        if not isinstance(evidence, list) or not all(_non_empty(item) for item in evidence):
            errors.append(f"{prefix}.evidenceRefs: expected an array of strings")
    summary = coverage.get("summary")
    declared = summary.get("total") if isinstance(summary, dict) else None
    if declared != len(files):
        errors.append(f"coverage.summary.total: expected {len(files)}, got {declared!r}")
    if isinstance(summary, dict):
        reviewed = sum(
            row.get("disposition") in {"REVIEWED", "COVERED_BY_PARENT"}
            for row in files
            if isinstance(row, dict)
        )
        deferred = sum(
            row.get("disposition") in {"PENDING", "DEFERRED", "UNREADABLE"}
            for row in files
            if isinstance(row, dict)
        )
        if summary.get("reviewed") != reviewed:
            errors.append(f"coverage.summary.reviewed: expected {reviewed}")
        if summary.get("deferred") != deferred:
            errors.append(f"coverage.summary.deferred: expected {deferred}")
    return paths


def _validate_coverage_inventory(
    coverage: dict[str, Any],
    schema_version: str,
    source_projection: SourceProjection | None,
    errors: list[str],
) -> None:
    if schema_version != SCHEMA_VERSION:
        if any(
            "sourceIdentity" in row for row in coverage.get("files", []) if isinstance(row, dict)
        ):
            errors.append("coverage.sourceIdentity: unsupported by frozen review protocol")
        return
    if source_projection is None:
        return
    files = coverage.get("files")
    if not isinstance(files, list):
        return
    rows_by_path = {
        row.get("path"): (index, row)
        for index, row in enumerate(files)
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    expected_paths = set(source_projection.records)
    actual_paths = set(rows_by_path)
    for path in sorted(expected_paths - actual_paths):
        errors.append(f"coverage.files: missing canonical inventory path {path!r}")
    for path in sorted(actual_paths - expected_paths):
        errors.append(f"coverage.files: unexpected canonical inventory path {path!r}")
    for path in sorted(expected_paths & actual_paths):
        index, row = rows_by_path[path]
        expected = source_projection.records[path]
        for field in _COVERAGE_INVENTORY_FIELDS:
            if (field in row) != (field in expected) or row.get(field) != expected.get(field):
                errors.append(
                    f"coverage.files[{index}].{field}: does not match the canonical inventory"
                )


def _validate_location(
    location: Any,
    prefix: str,
    coverage_paths: set[str],
    errors: list[str],
    *,
    schema_version: str,
    source_projection: SourceProjection | None,
) -> None:
    if not isinstance(location, dict):
        errors.append(f"{prefix}: expected an object")
        return
    path = location.get("path")
    if not _safe_relative(path):
        errors.append(f"{prefix}.path: expected a safe relative path")
    elif path not in coverage_paths:
        errors.append(f"{prefix}.path: {path} is not in coverage")
    start = location.get("lineStart")
    end = location.get("lineEnd", start)
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        errors.append(f"{prefix}.lineStart: expected a positive integer")
    if (
        not isinstance(end, int)
        or isinstance(end, bool)
        or not isinstance(start, int)
        or end < start
    ):
        errors.append(f"{prefix}.lineEnd: expected an integer >= lineStart")
    if schema_version != SCHEMA_VERSION:
        if "anchor" in location:
            errors.append(f"{prefix}.anchor: unsupported by frozen {schema_version}")
        return
    anchor = location.get("anchor")
    if not isinstance(anchor, dict):
        errors.append(f"{prefix}.anchor: required for {SCHEMA_VERSION}")
        return
    if (
        source_projection is None
        or not isinstance(path, str)
        or path not in coverage_paths
        or not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
        or start < 1
        or end < start
    ):
        return
    try:
        expected = build_source_anchor(
            source_projection,
            path=path,
            line_start=start,
            line_end=end,
        )
    except (OSError, ValueError, RuntimeError) as error:
        errors.append(f"{prefix}.anchor: source validation failed: {error}")
        return
    for field, value in expected.items():
        if anchor.get(field) != value:
            errors.append(f"{prefix}.anchor.{field}: does not match canonical source")


def _validate_candidates(
    candidates: list[dict[str, Any]],
    coverage_paths: set[str],
    errors: list[str],
    final: bool,
    *,
    schema_version: str,
    source_projection: SourceProjection | None,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(candidates):
        prefix = f"candidate-ledger[{index}]"
        candidate_id = row.get("id")
        if not _non_empty(candidate_id) or not re.fullmatch(r"RC-[A-Z]+-[0-9]{3,}", candidate_id):
            errors.append(f"{prefix}.id: expected RC-CATEGORY-NNN")
        elif candidate_id in result:
            errors.append(f"{prefix}.id: duplicate {candidate_id}")
        else:
            result[candidate_id] = row
        for field in ("category", "type", "title", "confidence"):
            if not _non_empty(row.get(field)):
                errors.append(f"{prefix}.{field}: required")
        locations = row.get("locations")
        if not isinstance(locations, list) or not locations:
            errors.append(f"{prefix}.locations: expected a non-empty array")
        else:
            for location_index, location in enumerate(locations):
                _validate_location(
                    location,
                    f"{prefix}.locations[{location_index}]",
                    coverage_paths,
                    errors,
                    schema_version=schema_version,
                    source_projection=source_projection,
                )
        validation = row.get("validation")
        if not isinstance(validation, dict):
            errors.append(f"{prefix}.validation: expected an object")
            continue
        status = validation.get("status")
        if status not in VALIDATION_STATUSES:
            errors.append(f"{prefix}.validation.status: unsupported {status!r}")
        if final and status == "PENDING":
            errors.append(f"{prefix}.validation.status: unresolved candidate")
        if status not in {"PENDING", "BLOCKED"} and not _non_empty(validation.get("method")):
            errors.append(f"{prefix}.validation.method: required for {status}")
    return result


def _validate_findings(
    document: dict[str, Any],
    candidates: dict[str, dict[str, Any]],
    coverage_paths: set[str],
    errors: list[str],
    *,
    schema_version: str,
    source_projection: SourceProjection | None,
) -> dict[str, dict[str, Any]]:
    rows = document.get("findings")
    if not isinstance(rows, list):
        errors.append("findings.findings: expected an array")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        prefix = f"findings.findings[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: expected an object")
            continue
        _validate_finding_row(
            row,
            prefix,
            candidates,
            coverage_paths,
            result,
            errors,
            schema_version=schema_version,
            source_projection=source_projection,
        )
    return result


def _validate_finding_row(
    row: dict[str, Any],
    prefix: str,
    candidates: dict[str, dict[str, Any]],
    coverage_paths: set[str],
    result: dict[str, dict[str, Any]],
    errors: list[str],
    *,
    schema_version: str,
    source_projection: SourceProjection | None,
) -> None:
    finding_id = row.get("id")
    if not _non_empty(finding_id) or finding_id in result:
        errors.append(f"{prefix}.id: expected a unique string")
    else:
        result[finding_id] = row
    _validate_finding_candidate(row, prefix, candidates, errors, schema_version=schema_version)
    _validate_finding_fields(row, prefix, errors)
    _validate_finding_locations(
        row,
        prefix,
        coverage_paths,
        errors,
        schema_version=schema_version,
        source_projection=source_projection,
    )


def _validate_finding_candidate(
    row: dict[str, Any],
    prefix: str,
    candidates: dict[str, dict[str, Any]],
    errors: list[str],
    *,
    schema_version: str,
) -> None:
    candidate_id = row.get("candidateId")
    if candidate_id not in candidates:
        errors.append(f"{prefix}.candidateId: unknown candidate {candidate_id!r}")
        return
    candidate = candidates[candidate_id]
    candidate_status = candidate.get("validation", {}).get("status")
    if candidate_status not in {"CONFIRMED", "LIKELY"}:
        errors.append(f"{prefix}.candidateId: candidate is not reportable")
    if row.get("validationStatus") != candidate_status:
        errors.append(f"{prefix}.validationStatus: must match the candidate")
    if row.get("category") != candidate.get("category"):
        errors.append(f"{prefix}.category: must match the candidate")
    if schema_version == SCHEMA_VERSION and row.get("locations") != candidate.get("locations"):
        errors.append(f"{prefix}.locations: must exactly match the run.v5 candidate anchors")


def _validate_finding_fields(row: dict[str, Any], prefix: str, errors: list[str]) -> None:
    required = (
        "title",
        "category",
        "rootCause",
        "currentImpact",
        "longTermRisk",
        "recommendation",
        "modificationCost",
        "modificationRisk",
        "decisionId",
    )
    for field in required:
        if not _non_empty(row.get(field)):
            errors.append(f"{prefix}.{field}: required")
    if row.get("validationStatus") not in {"CONFIRMED", "LIKELY"}:
        errors.append(f"{prefix}.validationStatus: expected CONFIRMED or LIKELY")
    if row.get("severity") not in SEVERITIES:
        errors.append(f"{prefix}.severity: unsupported")
    if row.get("priority") not in PRIORITIES:
        errors.append(f"{prefix}.priority: unsupported")
    performance = row.get("performanceClass")
    if performance is not None and performance not in PERFORMANCE_CLASSES:
        errors.append(f"{prefix}.performanceClass: unsupported")
    if performance in {"LIKELY_HOT_PATH", "UNVERIFIED_SUSPICION"}:
        errors.append(f"{prefix}.performanceClass: unmeasured suspicion must not be a finding")
    if not _string_list(row.get("evidenceRefs")):
        errors.append(f"{prefix}.evidenceRefs: expected a non-empty string array")
    if not _string_list(row.get("verification")):
        errors.append(f"{prefix}.verification: expected a non-empty string array")


def _validate_finding_locations(
    row: dict[str, Any],
    prefix: str,
    coverage_paths: set[str],
    errors: list[str],
    *,
    schema_version: str,
    source_projection: SourceProjection | None,
) -> None:
    locations = row.get("locations")
    if not isinstance(locations, list) or not locations:
        errors.append(f"{prefix}.locations: expected a non-empty array")
        return
    for location_index, location in enumerate(locations):
        _validate_location(
            location,
            f"{prefix}.locations[{location_index}]",
            coverage_paths,
            errors,
            schema_version=schema_version,
            source_projection=source_projection,
        )


def _validate_decisions(
    document: dict[str, Any], findings: dict[str, dict[str, Any]], errors: list[str]
) -> dict[str, dict[str, Any]]:
    rows = document.get("decisions")
    if not isinstance(rows, list):
        errors.append("decisions.decisions: expected an array")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        prefix = f"decisions.decisions[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: expected an object")
            continue
        _validate_decision_row(row, prefix, findings, result, errors)
    _validate_finding_decision_links(findings, result, errors)
    return result


def _validate_decision_row(
    row: dict[str, Any],
    prefix: str,
    findings: dict[str, dict[str, Any]],
    result: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    decision_id = row.get("id")
    if not _non_empty(decision_id) or decision_id in result:
        errors.append(f"{prefix}.id: expected a unique string")
    else:
        result[decision_id] = row
    if row.get("decision") not in DECISIONS:
        errors.append(f"{prefix}.decision: unsupported")
    for field in ("subject", "rationale"):
        if not _non_empty(row.get(field)):
            errors.append(f"{prefix}.{field}: required")
    finding_refs = row.get("findingRefs", [])
    if not isinstance(finding_refs, list) or not all(item in findings for item in finding_refs):
        errors.append(f"{prefix}.findingRefs: contains an unknown finding")
    if not _string_list(row.get("verification")):
        errors.append(f"{prefix}.verification: expected a non-empty string array")
    _validate_destructive_decision(row, prefix, finding_refs, errors)


def _validate_destructive_decision(
    row: dict[str, Any], prefix: str, finding_refs: Any, errors: list[str]
) -> None:
    if row.get("decision") not in {"DELETE", "REWRITE"}:
        return
    for field in ("migration", "rollback"):
        if not _non_empty(row.get(field)):
            errors.append(f"{prefix}.{field}: required for {row.get('decision')}")
    for field in ("compatibilityRisks", "alternatives"):
        if not _string_list(row.get(field)):
            errors.append(f"{prefix}.{field}: required for {row.get('decision')}")
    if not finding_refs:
        errors.append(f"{prefix}.findingRefs: required for {row.get('decision')}")


def _validate_finding_decision_links(
    findings: dict[str, dict[str, Any]],
    decisions: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for finding_id, finding in findings.items():
        decision_id = finding.get("decisionId")
        if decision_id not in decisions:
            errors.append(f"findings {finding_id}: unknown decisionId {decision_id!r}")
        elif finding_id not in decisions[decision_id].get("findingRefs", []):
            errors.append(f"decisions {decision_id}: does not reference finding {finding_id}")


def _validate_remediation(plan: dict[str, Any], errors: list[str], final: bool) -> None:
    if final and plan.get("changeClass") not in {
        "LOCAL_OPTIMIZATION",
        "MODULE_REFACTOR",
        "ARCHITECTURE_ADJUSTMENT",
    }:
        errors.append("remediation-plan.changeClass: unsupported")
    target = plan.get("targetArchitecture")
    if not isinstance(target, dict):
        errors.append("remediation-plan.targetArchitecture: expected an object")
    else:
        for field in (
            "overview",
            "moduleBoundaries",
            "dependencyDirection",
            "coreDataFlow",
            "stateAndErrors",
            "directoryStructure",
            "testingStructure",
            "deliveryFlow",
        ):
            value = target.get(field)
            if final and not (_non_empty(value) or _string_list(value)):
                errors.append(f"remediation-plan.targetArchitecture.{field}: required")
    phases = plan.get("phases")
    if not isinstance(phases, list):
        errors.append("remediation-plan.phases: expected an array")
        return
    expected = [item[0] for item in REMEDIATION_PHASES]
    actual = [row.get("id") for row in phases if isinstance(row, dict)]
    if actual != expected:
        errors.append(f"remediation-plan.phases: expected {expected}")
    for index, row in enumerate(phases):
        if not isinstance(row, dict):
            continue
        prefix = f"remediation-plan.phases[{index}]"
        for field in (
            "modificationScope",
            "prerequisites",
            "expectedBenefits",
            "risks",
            "acceptanceCriteria",
        ):
            value = row.get(field)
            if not isinstance(value, list) or not all(_non_empty(item) for item in value):
                errors.append(f"{prefix}.{field}: expected an array of strings")
            elif final and not value:
                errors.append(f"{prefix}.{field}: must not be empty for finalization")
