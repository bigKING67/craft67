from __future__ import annotations

import re
from typing import Any

from .constants import (
    CONTENT_BOUND_SCHEMA_VERSIONS,
    EVIDENCE_LEVELS,
    FINAL_COVERAGE_DISPOSITIONS,
    SCORE_DIMENSIONS,
    SEMANTIC_CLAIM_LEVELS,
)

EVIDENCE_GAP_PATTERN = re.compile(r"evidence-gap:[a-z][a-z0-9_-]{0,63}")


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_non_empty(item) for item in value)


def _validate_deduction(
    deduction: Any,
    *,
    prefix: str,
    findings: dict[str, dict[str, Any]],
    schema_version: str,
    close_references: bool,
    errors: list[str],
) -> int:
    if not isinstance(deduction, dict):
        errors.append(f"{prefix}: expected an object")
        return 0
    points = deduction.get("points")
    valid_points = isinstance(points, int) and not isinstance(points, bool) and points >= 1
    if not valid_points:
        errors.append(f"{prefix}.points: expected a positive integer")
    if not _non_empty(deduction.get("reason")):
        errors.append(f"{prefix}.reason: required")
    references = deduction.get("evidenceRefs")
    if not _string_list(references):
        errors.append(f"{prefix}.evidenceRefs: required")
    elif schema_version in CONTENT_BOUND_SCHEMA_VERSIONS and close_references:
        for index, reference in enumerate(references):
            if reference in findings or EVIDENCE_GAP_PATTERN.fullmatch(reference):
                continue
            errors.append(
                f"{prefix}.evidenceRefs[{index}]: unknown score evidence reference "
                f"{reference!r}; expected an existing finding ID or canonical evidence-gap:<id>"
            )
    return points if valid_points else 0


def _validate_dimensions(
    dimensions: Any,
    *,
    findings: dict[str, dict[str, Any]],
    schema_version: str,
    close_references: bool,
    errors: list[str],
) -> int | None:
    if not isinstance(dimensions, list):
        errors.append("scorecard.dimensions: expected an array")
        return None
    by_id = {row.get("id"): row for row in dimensions if isinstance(row, dict)}
    expected_ids = {item[0] for item in SCORE_DIMENSIONS}
    if set(by_id) != expected_ids:
        errors.append("scorecard.dimensions: expected the canonical eight dimensions")
        return None
    total = 0
    for identifier, _, maximum in SCORE_DIMENSIONS:
        row = by_id[identifier]
        if row.get("maximum") != maximum:
            errors.append(f"scorecard.{identifier}.maximum: expected {maximum}")
        awarded = row.get("awarded")
        if not isinstance(awarded, int) or isinstance(awarded, bool) or not 0 <= awarded <= maximum:
            errors.append(f"scorecard.{identifier}.awarded: expected 0..{maximum}")
            continue
        deductions = row.get("deductions")
        if not isinstance(deductions, list):
            errors.append(f"scorecard.{identifier}.deductions: expected an array")
            continue
        points = sum(
            _validate_deduction(
                deduction,
                prefix=f"scorecard.{identifier}.deductions[{index}]",
                findings=findings,
                schema_version=schema_version,
                close_references=close_references,
                errors=errors,
            )
            for index, deduction in enumerate(deductions)
        )
        if maximum - awarded != points:
            errors.append(
                f"scorecard.{identifier}: deductions {points} do not equal {maximum - awarded}"
            )
        total += awarded
    return total


def _coverage_metrics(coverage: dict[str, Any]) -> tuple[float, float, int]:
    files = coverage.get("files", [])
    accounted = sum(
        1 for row in files if row.get("disposition") in FINAL_COVERAGE_DISPOSITIONS
    )
    reviewed = sum(
        1
        for row in files
        if row.get("disposition") in {"REVIEWED", "COVERED_BY_PARENT"}
    )
    accounted_percent = round(100 * accounted / len(files), 2) if files else 100.0
    reviewed_percent = round(100 * reviewed / len(files), 2) if files else 100.0
    review_gaps = sum(
        row.get("disposition") in {"PENDING", "DEFERRED", "UNREADABLE", "OUT_OF_SCOPE"}
        for row in files
        if isinstance(row, dict)
    )
    return accounted_percent, reviewed_percent, review_gaps


def _validate_coverage_fields(
    scorecard: dict[str, Any],
    coverage: dict[str, Any],
    errors: list[str],
) -> tuple[float, int]:
    accounted_percent, reviewed_percent, review_gaps = _coverage_metrics(coverage)
    explicit = "accountedPercent" in scorecard or "reviewedPercent" in scorecard
    if explicit:
        if scorecard.get("accountedPercent") != accounted_percent:
            errors.append(f"scorecard.accountedPercent: expected {accounted_percent}")
        if scorecard.get("reviewedPercent") != reviewed_percent:
            errors.append(f"scorecard.reviewedPercent: expected {reviewed_percent}")
        if scorecard.get("coveragePercent") != reviewed_percent:
            errors.append(f"scorecard.coveragePercent: expected {reviewed_percent}")
    elif scorecard.get("coveragePercent") != accounted_percent:
        # Historical run.v3 artifacts used coveragePercent for accounting closure.
        errors.append(f"scorecard.coveragePercent: expected {accounted_percent}")
    return accounted_percent, review_gaps


def _successful_receipts(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in commands
        if isinstance(row, dict)
        and row.get("exitCode") == 0
        and row.get("timedOut") is False
        and row.get("repositoryMutationDetected") is False
        and row.get("semanticEvidenceValid") is not False
    ]


def _validate_evidence_level(
    level: Any,
    commands: list[dict[str, Any]],
    errors: list[str],
) -> bool:
    if level not in EVIDENCE_LEVELS:
        errors.append("scorecard.evidenceLevel: expected E0..E4")
        return False
    successful = _successful_receipts(commands)
    if EVIDENCE_LEVELS[level] >= EVIDENCE_LEVELS["E2"] and not successful:
        errors.append(
            "scorecard.evidenceLevel: E2+ requires a successful canonical command receipt"
        )
    semantic_present = any(
        isinstance(row, dict) and "semanticEvidenceValid" in row for row in commands
    )
    if semantic_present and EVIDENCE_LEVELS[level] >= EVIDENCE_LEVELS["E3"]:
        verified_levels = [
            EVIDENCE_LEVELS[SEMANTIC_CLAIM_LEVELS[claim["kind"]]]
            for row in successful
            for claim in row.get("evidenceClaims", [])
            if claim.get("status") == "VERIFIED"
            and claim.get("kind") in SEMANTIC_CLAIM_LEVELS
        ]
        if not verified_levels or max(verified_levels) < EVIDENCE_LEVELS[level]:
            errors.append(
                f"scorecard.evidenceLevel: {level} requires a matching verified semantic claim"
            )
    return True


def _validate_final_state(
    scorecard: dict[str, Any],
    *,
    level: str,
    total: int,
    accounted_percent: float,
    review_gaps: int,
    unresolved: int,
    findings: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if EVIDENCE_LEVELS[level] < 1:
        errors.append("scorecard.evidenceLevel: E1 is required for a numeric final score")
    final_score = scorecard.get("status") == "final"
    if final_score and (accounted_percent != 100.0 or unresolved):
        errors.append("scorecard.status: final requires closed coverage and candidates")
    if final_score and review_gaps:
        errors.append(
            "scorecard.status: final requires no pending, deferred, unreadable, "
            "or out-of-scope review gaps"
        )
    if final_score and any(
        row.get("priority") in {"P0", "P1"}
        and row.get("validationStatus") != "CONFIRMED"
        for row in findings.values()
    ):
        errors.append("scorecard.status: unresolved P0/P1 finding prevents final status")
    if total >= 95 and EVIDENCE_LEVELS[level] < 3:
        errors.append("scorecard: scores >=95 require evidence level E3")
    if total >= 98 and EVIDENCE_LEVELS[level] < 4:
        errors.append("scorecard: scores >=98 require evidence level E4")


def validate_scorecard(
    scorecard: dict[str, Any],
    findings: dict[str, dict[str, Any]],
    candidates: list[dict[str, Any]],
    coverage: dict[str, Any],
    commands: list[dict[str, Any]],
    errors: list[str],
    *,
    schema_version: str,
    final: bool,
) -> None:
    total = _validate_dimensions(
        scorecard.get("dimensions"),
        findings=findings,
        schema_version=schema_version,
        close_references=final,
        errors=errors,
    )
    if total is None:
        return
    if scorecard.get("total") != total:
        errors.append(f"scorecard.total: expected {total}, got {scorecard.get('total')!r}")
    unresolved = sum(
        1
        for row in candidates
        if row.get("validation", {}).get("status") in {"PENDING", "BLOCKED"}
    )
    if scorecard.get("unresolvedCandidates") != unresolved:
        errors.append(f"scorecard.unresolvedCandidates: expected {unresolved}")
    accounted_percent, review_gaps = _validate_coverage_fields(scorecard, coverage, errors)
    level = scorecard.get("evidenceLevel")
    if not _validate_evidence_level(level, commands, errors):
        return
    if final:
        _validate_final_state(
            scorecard,
            level=level,
            total=total,
            accounted_percent=accounted_percent,
            review_gaps=review_gaps,
            unresolved=unresolved,
            findings=findings,
            errors=errors,
        )
