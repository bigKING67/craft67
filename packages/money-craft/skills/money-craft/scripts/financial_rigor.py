#!/usr/bin/env python3
"""Exact financial calculations and embedded calculation-receipt audit.

Adapted from AI Berkshire's financial_rigor.py at the commit recorded in
sources.lock.json. Money Craft narrows the interface to deterministic Decimal
operations that can be embedded in portable Markdown reports.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Sequence

CONTEXT = Context(prec=34, rounding=ROUND_HALF_EVEN)
CALC_MARKER_RE = re.compile(r"<!--\s*money-craft-calc:")
CALC_RE = re.compile(r"<!--\s*money-craft-calc:\s*(.*?)-->", re.DOTALL)
SUPPORTED_OPERATIONS = {
    "add",
    "subtract",
    "multiply",
    "divide",
    "cagr",
    "weighted_average",
}


class CalculationError(ValueError):
    """A calculation receipt is invalid or cannot be evaluated."""


def decimal_value(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise CalculationError(f"not a decimal value: {value!r}")
    try:
        result = value if isinstance(value, Decimal) else CONTEXT.create_decimal(str(value).strip())
    except (DecimalException, ValueError) as exc:
        raise CalculationError(f"invalid decimal value: {value!r}") from exc
    if not result.is_finite():
        raise CalculationError(f"decimal value must be finite: {value!r}")
    return result


def calculate(operation: str, inputs: Sequence[Any]) -> Decimal:
    values = [decimal_value(value) for value in inputs]
    if operation not in SUPPORTED_OPERATIONS:
        raise CalculationError(f"unsupported operation: {operation}")
    try:
        if operation == "add":
            if not values:
                raise CalculationError("add requires at least one input")
            result = Decimal(0)
            for value in values:
                result = CONTEXT.add(result, value)
            return result
        if operation == "subtract":
            if len(values) != 2:
                raise CalculationError("subtract requires exactly two inputs")
            return CONTEXT.subtract(values[0], values[1])
        if operation == "multiply":
            if not values:
                raise CalculationError("multiply requires at least one input")
            result = Decimal(1)
            for value in values:
                result = CONTEXT.multiply(result, value)
            return result
        if operation == "divide":
            if len(values) != 2:
                raise CalculationError("divide requires exactly two inputs")
            if values[1] == 0:
                raise CalculationError("division by zero")
            return CONTEXT.divide(values[0], values[1])
        if operation == "cagr":
            if len(values) != 3:
                raise CalculationError("cagr requires start, end, and years")
            start, end, years = values
            if start <= 0 or end < 0 or years <= 0:
                raise CalculationError("cagr requires start > 0, end >= 0, years > 0")
            exponent = CONTEXT.divide(Decimal(1), years)
            return CONTEXT.subtract(CONTEXT.power(CONTEXT.divide(end, start), exponent), Decimal(1))
        if len(values) < 2 or len(values) % 2:
            raise CalculationError("weighted_average requires value/weight pairs")
        numerator = Decimal(0)
        denominator = Decimal(0)
        for index in range(0, len(values), 2):
            numerator = CONTEXT.add(numerator, CONTEXT.multiply(values[index], values[index + 1]))
            denominator = CONTEXT.add(denominator, values[index + 1])
        if denominator == 0:
            raise CalculationError("weighted_average weights sum to zero")
        return CONTEXT.divide(numerator, denominator)
    except DecimalException as exc:
        raise CalculationError(f"{operation} calculation failed: {exc}") from exc


def relative_error(actual: Decimal, expected: Decimal) -> Decimal:
    if not actual.is_finite() or not expected.is_finite():
        raise CalculationError("relative_error requires finite values")
    try:
        difference = CONTEXT.subtract(actual, expected).copy_abs()
        if expected == 0:
            return Decimal(0) if actual == 0 else Decimal("Infinity")
        return CONTEXT.divide(difference, expected.copy_abs())
    except DecimalException as exc:
        raise CalculationError(f"relative_error calculation failed: {exc}") from exc


def audit_text(text: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    matched_starts: set[int] = set()
    for match in CALC_RE.finditer(text):
        matched_starts.add(match.start())
        try:
            receipt = json.loads(match.group(1), parse_float=Decimal)
            if not isinstance(receipt, dict):
                raise CalculationError("receipt must be a JSON object")
            receipt_id = receipt.get("id")
            if not isinstance(receipt_id, str) or not re.fullmatch(r"C\d{2,7}", receipt_id):
                raise CalculationError("receipt id must be C followed by 2..7 digits")
            if receipt_id in seen_ids:
                raise CalculationError(f"duplicate receipt id: {receipt_id}")
            seen_ids.add(receipt_id)
            operation = receipt.get("operation")
            inputs = receipt.get("inputs")
            if not isinstance(operation, str) or not isinstance(inputs, list):
                raise CalculationError("receipt requires operation and inputs")
            expected = decimal_value(receipt.get("expected"))
            tolerance = decimal_value(receipt.get("tolerance", "0.000001"))
            if tolerance < 0 or tolerance > Decimal("0.05"):
                raise CalculationError("tolerance must be between 0 and 0.05")
            actual = calculate(operation, inputs)
            error = relative_error(actual, expected)
            passed = error <= tolerance
            checks.append(
                {
                    "id": receipt_id,
                    "operation": operation,
                    "actual": str(actual),
                    "expected": str(expected),
                    "relative_error": str(error),
                    "tolerance": str(tolerance),
                    "passed": passed,
                }
            )
            if not passed:
                errors.append(f"{receipt_id}: calculation differs from expected value")
        except (CalculationError, DecimalException, ValueError, TypeError) as exc:
            errors.append(f"calculation receipt at byte {match.start()}: {exc}")
    for marker in CALC_MARKER_RE.finditer(text):
        if marker.start() not in matched_starts:
            errors.append(f"calculation receipt at character {marker.start()}: unterminated or nested marker")
    if not checks and not errors:
        warnings.append("no money-craft-calc receipts found")
    return {
        "schema": "money-craft.financial-audit.v1",
        "valid": not errors,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
    }


def audit_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "schema": "money-craft.financial-audit.v1",
            "valid": False,
            "checks": [],
            "warnings": [],
            "errors": [f"report does not exist: {path}"],
        }
    return audit_text(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit")
    audit.add_argument("--report", required=True)
    audit.add_argument("--json", action="store_true")
    calc = subparsers.add_parser("calculate")
    calc.add_argument("--operation", choices=sorted(SUPPORTED_OPERATIONS), required=True)
    calc.add_argument("--inputs", nargs="+", required=True)
    calc.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.command == "audit":
        result = audit_file(Path(args.report).expanduser().resolve())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 1
    try:
        value = calculate(args.operation, args.inputs)
    except CalculationError as exc:
        payload = {"ok": False, "error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    payload = {"ok": True, "operation": args.operation, "result": str(value)}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
