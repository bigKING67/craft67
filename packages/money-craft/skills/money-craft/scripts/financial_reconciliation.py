#!/usr/bin/env python3
"""Audit restatement basis, statement ties, and accounting-to-economics bridges."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from financial_rigor import CalculationError, calculate, decimal_value, relative_error
import report_audit

SCHEMA = "money-craft.financial-reconciliation.v1"
AUDIT_SCHEMA = "money-craft.financial-reconciliation-audit.v1"
SOURCE_ID_RE = re.compile(r"^S\d{2,4}$")
SECRET_RE = re.compile(rb"sk-fuyao-[A-Za-z0-9_-]{12,}")
PERIOD_RE = re.compile(r"^(?:19|20)\d{2}-[1-4]$")
CHECK_ID_RE = re.compile(r"^FR\d{2,4}$")
MANDATORY_CHECKS = {"balance-sheet-equation", "cash-balance-tie"}
CHECK_INPUTS = {
    "balance-sheet-equation": ("assets", "liabilities", "equity"),
    "cash-balance-tie": ("balance_sheet_cash", "cash_flow_ending_cash"),
    "quarter-from-ytd": ("current_ytd", "previous_period_ytd", "reported_quarter"),
}
MAX_BYTES = 5 * 1024 * 1024


class ReconciliationError(ValueError):
    """A reconciliation artifact cannot be parsed or validated."""


def source_ids(
    value: Any,
    label: str,
    errors: list[str],
    *,
    allowed_source_ids: set[str] | None,
) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} must contain at least one source ID")
        return []
    if any(not isinstance(item, str) or not SOURCE_ID_RE.fullmatch(item) for item in value):
        errors.append(f"{label} must contain only Sxx source IDs")
        return []
    if len(set(value)) != len(value):
        errors.append(f"{label} contains duplicate source IDs")
    if allowed_source_ids is not None:
        unknown = sorted(set(value) - allowed_source_ids)
        if unknown:
            errors.append(f"{label} contains source IDs outside available research evidence: {', '.join(unknown)}")
    return list(value)


def nonempty_text(value: Any, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be non-empty text")
        return ""
    if "{{" in value or "}}" in value:
        errors.append(f"{label} contains an unresolved placeholder")
    return value.strip()


def audit_assessment(
    payload: Any,
    *,
    label: str,
    allowed_statuses: set[str],
    empty_status: str,
    identified_status: str,
    item_prefix: str,
    item_fields: tuple[str, ...],
    allowed_source_ids: set[str] | None,
    errors: list[str],
) -> None:
    if not isinstance(payload, dict):
        errors.append(f"{label} must be an object")
        return
    status = payload.get("status")
    if not isinstance(status, str) or status not in allowed_statuses:
        errors.append(f"{label}.status is invalid")
    elif status == "unverified":
        errors.append(f"{label}.status must be resolved before finalization")
    source_ids(payload.get("source_ids"), f"{label}.source_ids", errors, allowed_source_ids=allowed_source_ids)
    nonempty_text(payload.get("notes"), f"{label}.notes", errors)
    items = payload.get("items")
    if not isinstance(items, list):
        errors.append(f"{label}.items must be an array")
        return
    if status == empty_status and items:
        errors.append(f"{label}.items must be empty when status is {empty_status}")
    if status == identified_status and not items:
        errors.append(f"{label}.items is required when status is {identified_status}")
    seen: set[str] = set()
    for index, item in enumerate(items):
        item_label = f"{label}.items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_label} must be an object")
            continue
        item_id = item.get("id")
        if (
            not isinstance(item_id, str)
            or not re.fullmatch(rf"{item_prefix}\d{{2,4}}", item_id)
            or item_id in seen
        ):
            errors.append(f"{item_label}.id must be a unique {item_prefix}xx identifier")
        else:
            seen.add(item_id)
        for field in item_fields:
            nonempty_text(item.get(field), f"{item_label}.{field}", errors)
        evidence_state = item.get("evidence_state")
        if not isinstance(evidence_state, str) or evidence_state not in {"OBSERVED", "INFERRED", "UNVERIFIED"}:
            errors.append(f"{item_label}.evidence_state is invalid")
        elif evidence_state == "UNVERIFIED":
            errors.append(f"{item_label}.evidence_state must be resolved before finalization")
        source_ids(
            item.get("source_ids"),
            f"{item_label}.source_ids",
            errors,
            allowed_source_ids=allowed_source_ids,
        )


def audit_payload(
    payload: dict[str, Any],
    *,
    expected_contract: dict[str, Any] | None = None,
    expected_identity: dict[str, str] | None = None,
    allowed_source_ids: set[str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []
    if payload.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    security = nonempty_text(payload.get("security"), "security", errors)
    identity_metadata = {
        key: value
        for key in ("security_id", "thscode")
        if isinstance((value := payload.get(key)), str)
    }
    try:
        security_id = report_audit.security_id_from_metadata(identity_metadata)
    except ValueError as exc:
        errors.append(str(exc))
        security_id = ""
    as_of = payload.get("as_of")
    try:
        dt.date.fromisoformat(str(as_of))
    except ValueError:
        errors.append("as_of must be YYYY-MM-DD")
    base_currency = payload.get("base_currency")
    if not isinstance(base_currency, str) or not report_audit.CURRENCY_RE.fullmatch(base_currency):
        errors.append("base_currency must be a three-letter uppercase currency code")
    if expected_identity:
        expected = {
            "security": expected_identity.get("security"),
            "security_id": expected_identity.get("security_id"),
            "as_of": expected_identity.get("as_of"),
            "base_currency": expected_identity.get("base_currency"),
        }
        actual = {
            "security": security,
            "security_id": security_id,
            "as_of": as_of,
            "base_currency": base_currency,
        }
        for field, value in expected.items():
            if actual.get(field) != value:
                errors.append(f"{field} must match plan.json")

    required_checks = payload.get("required_checks")
    if not isinstance(required_checks, list) or any(not isinstance(kind, str) or kind not in CHECK_INPUTS for kind in required_checks):
        errors.append("required_checks contains an unsupported reconciliation kind")
        required_checks = []
    elif len(set(required_checks)) != len(required_checks):
        errors.append("required_checks contains duplicate kinds")
    missing_mandatory = sorted(MANDATORY_CHECKS - set(required_checks))
    if missing_mandatory:
        errors.append("required_checks is missing: " + ", ".join(missing_mandatory))
    if expected_contract and required_checks != expected_contract.get("required_checks"):
        errors.append("required_checks must match plan.json")

    basis = payload.get("period_basis")
    expected_basis = expected_contract.get("period_basis") if expected_contract else None
    if not isinstance(basis, list) or len(basis) != 2:
        errors.append("period_basis must contain current and comparison rows")
        basis = []
    seen_roles: set[str] = set()
    seen_calculation_ids: set[str] = set()
    for index, item in enumerate(basis):
        label = f"period_basis[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        role = item.get("role")
        period = item.get("period")
        basis_kind = item.get("basis")
        if not isinstance(role, str) or role not in {"current", "comparison"} or role in seen_roles:
            errors.append(f"{label}.role must be unique current or comparison")
        else:
            seen_roles.add(role)
        if not isinstance(period, str) or not PERIOD_RE.fullmatch(period):
            errors.append(f"{label}.period is invalid")
        if not isinstance(basis_kind, str) or basis_kind not in {"reported", "restated", "comparable-estimate", "unverified"}:
            errors.append(f"{label}.basis is invalid")
        elif basis_kind == "unverified":
            errors.append(f"{label}.basis must be resolved before finalization")
        source_ids(item.get("source_ids"), f"{label}.source_ids", errors, allowed_source_ids=allowed_source_ids)
        nonempty_text(item.get("notes"), f"{label}.notes", errors)
        calculation = item.get("calculation")
        if basis_kind == "comparable-estimate":
            if not isinstance(calculation, dict):
                errors.append(f"{label}.calculation is required for comparable-estimate")
            else:
                calculation_id = calculation.get("id")
                if (
                    not isinstance(calculation_id, str)
                    or not re.fullmatch(r"C\d{2,7}", calculation_id)
                    or calculation_id in seen_calculation_ids
                ):
                    errors.append(f"{label}.calculation.id must be a unique Cxx identifier")
                else:
                    seen_calculation_ids.add(calculation_id)
                try:
                    operation = calculation.get("operation")
                    inputs = calculation.get("inputs")
                    if not isinstance(operation, str) or not isinstance(inputs, list):
                        raise CalculationError("calculation requires operation and inputs")
                    expected_value = decimal_value(calculation.get("expected"))
                    tolerance = decimal_value(calculation.get("tolerance", "0.000001"))
                    if tolerance < 0 or tolerance > Decimal("0.05"):
                        raise CalculationError("tolerance must be between 0 and 0.05")
                    actual_value = calculate(operation, inputs)
                    error = relative_error(actual_value, expected_value)
                    passed = error <= tolerance
                    checks.append(
                        {
                            "id": calculation_id,
                            "kind": "comparable-estimate",
                            "period": period,
                            "lhs": str(actual_value),
                            "rhs": str(expected_value),
                            "relative_error": str(error),
                            "tolerance": str(tolerance),
                            "passed": passed,
                        }
                    )
                    if not passed:
                        errors.append(f"{calculation_id}: comparable estimate differs from expected value")
                except (CalculationError, TypeError) as exc:
                    errors.append(f"{label}.calculation: {exc}")
        elif calculation is not None:
            errors.append(f"{label}.calculation is only allowed for comparable-estimate")
    if seen_roles != {"current", "comparison"}:
        errors.append("period_basis must contain current and comparison roles")
    if isinstance(expected_basis, list):
        actual_roles = {item.get("role"): item.get("period") for item in basis
                        if isinstance(item, dict) and isinstance(item.get("role"), str)}
        expected_roles = {item.get("role"): item.get("period") for item in expected_basis if isinstance(item, dict)}
        if actual_roles != expected_roles:
            errors.append("period_basis roles and periods must match plan.json")

    restatement = payload.get("restatement_assessment")
    if not isinstance(restatement, dict):
        errors.append("restatement_assessment must be an object")
    else:
        status = restatement.get("status")
        if not isinstance(status, str) or status not in {"none-disclosed", "restated", "unverified"}:
            errors.append("restatement_assessment.status is invalid")
        elif status == "unverified":
            errors.append("restatement_assessment.status must be resolved before finalization")
        source_ids(
            restatement.get("source_ids"),
            "restatement_assessment.source_ids",
            errors,
            allowed_source_ids=allowed_source_ids,
        )
        nonempty_text(restatement.get("notes"), "restatement_assessment.notes", errors)
        if status == "restated" and not any(
            isinstance(item, dict) and item.get("basis") in ("restated", "comparable-estimate") for item in basis
        ):
            errors.append("a restated assessment requires a restated or comparable-estimate basis row")

    disclosures = payload.get("material_disclosure_assessment")
    expected_disclosures = (
        expected_contract.get("material_disclosure_source_ids") if expected_contract else ["S18", "S19", "S20"]
    )
    if not isinstance(disclosures, list):
        errors.append("material_disclosure_assessment must be an array")
        disclosures = []
    seen_disclosures: set[str] = set()
    for index, item in enumerate(disclosures):
        label = f"material_disclosure_assessment[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        source_id = item.get("source_id")
        if (
            not isinstance(source_id, str)
            or not SOURCE_ID_RE.fullmatch(source_id)
            or source_id in seen_disclosures
        ):
            errors.append(f"{label}.source_id must be a unique Sxx identifier")
        else:
            seen_disclosures.add(source_id)
        status = item.get("status")
        if not isinstance(status, str) or status not in {"not-triggered", "imported", "unverified"}:
            errors.append(f"{label}.status is invalid")
        elif status == "unverified":
            errors.append(f"{label}.status must be resolved before finalization")
        if allowed_source_ids is not None and isinstance(source_id, str):
            available = source_id in allowed_source_ids
            if status == "imported" and not available:
                errors.append(f"{label} claims imported evidence that is unavailable")
            if status == "not-triggered" and available:
                errors.append(f"{label} marks imported evidence as not-triggered")
        nonempty_text(item.get("notes"), f"{label}.notes", errors)
    actual_disclosures = [item.get("source_id") for item in disclosures if isinstance(item, dict)]
    if actual_disclosures != expected_disclosures:
        errors.append("material_disclosure_assessment must match the plan's conditional source order")

    raw_checks = payload.get("checks")
    if not isinstance(raw_checks, list):
        errors.append("checks must be an array")
        raw_checks = []
    seen_ids: set[str] = set()
    seen_kinds: set[str] = set()
    for index, item in enumerate(raw_checks):
        label = f"checks[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        check_id = item.get("id")
        kind = item.get("kind")
        if not isinstance(check_id, str) or not CHECK_ID_RE.fullmatch(check_id) or check_id in seen_ids:
            errors.append(f"{label}.id must be a unique FRxx identifier")
        else:
            seen_ids.add(check_id)
        if not isinstance(kind, str) or kind not in CHECK_INPUTS:
            errors.append(f"{label}.kind is unsupported")
            continue
        if kind in seen_kinds:
            errors.append(f"duplicate reconciliation kind: {kind}")
        seen_kinds.add(kind)
        period = item.get("period")
        if not isinstance(period, str) or not PERIOD_RE.fullmatch(period):
            errors.append(f"{label}.period is invalid")
        elif period not in [row.get("period") for row in basis if isinstance(row, dict)]:
            errors.append(f"{label}.period must belong to period_basis")
        if kind == "quarter-from-ytd" and period not in [
            row.get("period") for row in basis if isinstance(row, dict) and row.get("role") == "current"
        ]:
            errors.append(f"{label}.period must match current period_basis for quarter-from-ytd")
        nonempty_text(item.get("unit"), f"{label}.unit", errors)
        source_ids(item.get("source_ids"), f"{label}.source_ids", errors, allowed_source_ids=allowed_source_ids)
        adjustments = []
        if "cash_adjustments" in item:
            if kind != "cash-balance-tie":
                errors.append(f"{label}.cash_adjustments is only valid for cash-balance-tie")
            raw_adjustments = item["cash_adjustments"]
            if not isinstance(raw_adjustments, list) or not 1 <= len(raw_adjustments) <= 20:
                errors.append(f"{label}.cash_adjustments must contain 1 to 20 items")
            else:
                adjustment_ids: set[str] = set()
                for adjustment_index, adjustment in enumerate(raw_adjustments):
                    adjustment_label = f"{label}.cash_adjustments[{adjustment_index}]"
                    if not isinstance(adjustment, dict) or set(adjustment) != {"id", "amount", "reason", "source_ids"}:
                        errors.append(f"{adjustment_label} must contain exactly id, amount, reason, source_ids")
                        continue
                    adjustment_id = adjustment["id"]
                    if not isinstance(adjustment_id, str) or not re.fullmatch(r"CA\d{2,4}", adjustment_id) or adjustment_id in adjustment_ids:
                        errors.append(f"{adjustment_label}.id must be a unique CAxx identifier")
                    else:
                        adjustment_ids.add(adjustment_id)
                    reason = nonempty_text(adjustment["reason"], f"{adjustment_label}.reason", errors)
                    sources = source_ids(adjustment["source_ids"], f"{adjustment_label}.source_ids", errors, allowed_source_ids=allowed_source_ids)
                    try:
                        amount = decimal_value(adjustment["amount"])
                    except CalculationError as exc:
                        errors.append(f"{adjustment_label}.amount: {exc}")
                        continue
                    adjustments.append({"id": adjustment_id, "amount": str(amount), "reason": reason, "source_ids": sources})
        inputs = item.get("inputs")
        names = CHECK_INPUTS[kind]
        if not isinstance(inputs, dict) or set(inputs) != set(names):
            errors.append(f"{label}.inputs must contain exactly: {', '.join(names)}")
            continue
        try:
            values = {name: decimal_value(inputs[name]) for name in names}
            tolerance = decimal_value(item.get("tolerance", "0.000001"))
            if tolerance < 0 or tolerance > Decimal("0.05"):
                raise CalculationError("tolerance must be between 0 and 0.05")
            if kind == "balance-sheet-equation":
                lhs = values["assets"]
                rhs = calculate("add", [values["liabilities"], values["equity"]])
            elif kind == "cash-balance-tie":
                lhs = calculate("add", [values["balance_sheet_cash"], *[Decimal(row["amount"]) for row in adjustments]])
                rhs = values["cash_flow_ending_cash"]
            else:
                lhs = calculate("subtract", [values["current_ytd"], values["previous_period_ytd"]])
                rhs = values["reported_quarter"]
            error = relative_error(lhs, rhs)
            passed = error <= tolerance
            checks.append(
                {
                    "id": check_id,
                    "kind": kind,
                    "period": period,
                    "lhs": str(lhs),
                    "rhs": str(rhs),
                    "relative_error": str(error),
                    "tolerance": str(tolerance),
                    "passed": passed,
                }
            )
            if kind == "cash-balance-tie" and "cash_adjustments" in item:
                checks[-1].update(balance_sheet_cash=str(values["balance_sheet_cash"]), cash_adjustments=adjustments)
            if not passed:
                errors.append(f"{check_id}: {kind} does not reconcile")
        except (CalculationError, KeyError, TypeError) as exc:
            errors.append(f"{label}: {exc}")
    missing_checks = [kind for kind in required_checks if kind not in seen_kinds]
    if missing_checks:
        errors.append("checks is missing required kinds: " + ", ".join(missing_checks))
    unexpected_checks = sorted(seen_kinds - set(required_checks))
    if unexpected_checks:
        errors.append("checks contains undeclared kinds: " + ", ".join(unexpected_checks))

    audit_assessment(
        payload.get("presentation_to_economics"),
        label="presentation_to_economics",
        allowed_statuses={"no-material-distortion", "items-identified", "unverified"},
        empty_status="no-material-distortion",
        identified_status="items-identified",
        item_prefix="P",
        item_fields=("topic", "accounting_presentation", "operating_interpretation", "cash_effect"),
        allowed_source_ids=allowed_source_ids,
        errors=errors,
    )
    audit_assessment(
        payload.get("subsequent_events"),
        label="subsequent_events",
        allowed_statuses={"none-disclosed", "identified", "unverified"},
        empty_status="none-disclosed",
        identified_status="identified",
        item_prefix="E",
        item_fields=("event", "materiality", "research_effect"),
        allowed_source_ids=allowed_source_ids,
        errors=errors,
    )
    presentation = payload.get("presentation_to_economics")
    events = payload.get("subsequent_events")
    if not isinstance(presentation, dict) or not presentation.get("items"):
        warnings.append("no material accounting-presentation bridge items were identified")
    if not isinstance(events, dict) or not events.get("items"):
        warnings.append("no material post-reporting-period events were identified")
    return {
        "schema": AUDIT_SCHEMA,
        "valid": not errors,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
    }


def audit_file(
    path: Path,
    *,
    expected_contract: dict[str, Any] | None = None,
    expected_identity: dict[str, str] | None = None,
    allowed_source_ids: set[str] | None = None,
) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        return {
            "schema": AUDIT_SCHEMA,
            "valid": False,
            "checks": [],
            "warnings": [],
            "errors": [f"reconciliation artifact does not exist: {path}"],
        }
    if path.stat().st_size < 2 or path.stat().st_size > MAX_BYTES:
        return {
            "schema": AUDIT_SCHEMA,
            "valid": False,
            "checks": [],
            "warnings": [],
            "errors": ["reconciliation artifact size is invalid"],
        }
    try:
        raw = path.read_bytes()
        if SECRET_RE.search(raw):
            raise ReconciliationError("secret-like material is not allowed")
        payload = json.loads(raw.decode("utf-8"), parse_float=Decimal)
    except ReconciliationError as exc:
        return {"schema": AUDIT_SCHEMA, "valid": False, "checks": [], "warnings": [], "errors": [str(exc)]}
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return {
            "schema": AUDIT_SCHEMA,
            "valid": False,
            "checks": [],
            "warnings": [],
            "errors": [f"invalid reconciliation JSON: {exc}"],
        }
    if not isinstance(payload, dict):
        return {
            "schema": AUDIT_SCHEMA,
            "valid": False,
            "checks": [],
            "warnings": [],
            "errors": ["reconciliation artifact must be a JSON object"],
        }
    return audit_payload(
        payload,
        expected_contract=expected_contract,
        expected_identity=expected_identity,
        allowed_source_ids=allowed_source_ids,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit_file(Path(args.artifact).expanduser().resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
