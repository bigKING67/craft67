#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/complexity-budget.json"
MESSAGE_PATTERN = re.compile(r"`(?P<function>[^`]+)` is too complex \((?P<value>\d+) > 0\)")
VERSION_PATTERN = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")


def _load_contract(path: Path = CONTRACT) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "review-craft.complexity-budget.v2":
        raise ValueError("unsupported complexity budget schema")
    roots = payload.get("runtimeRoots")
    if not isinstance(roots, list) or not roots or not all(isinstance(row, str) for row in roots):
        raise ValueError("complexity budget must contain runtimeRoots")
    maximum = payload.get("defaultMaximum")
    if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 1:
        raise ValueError("complexity budget defaultMaximum must be a positive integer")
    for collection in ("ceilings", "debtExceptions"):
        if not isinstance(payload.get(collection), list):
            raise ValueError(f"complexity budget {collection} must be an array")
    return payload


class _FunctionIndex(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.by_line: dict[int, str] = {}

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified = ".".join([*self.stack, node.name])
        self.by_line[node.lineno] = qualified
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()


def _function_index(path: Path) -> dict[int, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    visitor = _FunctionIndex()
    visitor.visit(tree)
    return visitor.by_line


def _ruff_complexities(paths: list[str]) -> dict[tuple[str, str], int]:
    completed = subprocess.run(
        [
            "ruff",
            "check",
            "--select",
            "C901",
            "--output-format",
            "json",
            "--config",
            "lint.mccabe.max-complexity=0",
            *paths,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError(completed.stderr.strip() or "ruff C901 audit failed")
    indexes: dict[str, dict[int, str]] = {}
    result: dict[tuple[str, str], int] = {}
    for row in json.loads(completed.stdout):
        match = MESSAGE_PATTERN.fullmatch(row.get("message", ""))
        if match is None:
            continue
        path = Path(row["filename"]).resolve().relative_to(ROOT).as_posix()
        if path not in indexes:
            indexes[path] = _function_index(ROOT / path)
        line = row["location"]["row"]
        function = indexes[path].get(line, match.group("function"))
        key = (path, function)
        if key in result:
            raise RuntimeError(f"duplicate Ruff complexity result: {path}:{function}")
        result[key] = int(match.group("value"))
    return result


def _entry_key(row: dict[str, Any]) -> tuple[str, str]:
    path = row.get("path")
    function = row.get("function")
    if not isinstance(path, str) or not isinstance(function, str) or not path or not function:
        raise ValueError("complexity entries require path and function")
    return path, function


def evaluate_budget(
    contract: dict[str, Any], measured: dict[tuple[str, str], int]
) -> tuple[list[str], list[dict[str, Any]]]:
    default = contract["defaultMaximum"]
    errors: list[str] = []
    results: list[dict[str, Any]] = []
    entries: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
    for kind, collection in (
        ("ceiling", contract["ceilings"]),
        ("debt", contract["debtExceptions"]),
    ):
        for row in collection:
            key = _entry_key(row)
            if key in entries:
                errors.append(f"{key[0]}:{key[1]}: duplicate complexity entry")
            entries[key] = (kind, row)
    for key, (kind, row) in entries.items():
        actual = measured.get(key)
        if actual is None:
            errors.append(f"{key[0]}:{key[1]}: function was not measured")
            continue
        if kind == "ceiling":
            maximum = row.get("maximum")
            if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum > default:
                errors.append(f"{key[0]}:{key[1]}: invalid strict ceiling")
            elif actual > maximum:
                errors.append(f"{key[0]}:{key[1]}: complexity {actual} exceeds ceiling {maximum}")
        else:
            observed = row.get("observed")
            target = row.get("targetMaximum")
            remove_by = row.get("removeByVersion")
            if (
                target != default
                or not isinstance(remove_by, str)
                or not VERSION_PATTERN.fullmatch(remove_by)
            ):
                errors.append(f"{key[0]}:{key[1]}: invalid debt retirement contract")
            if isinstance(observed, bool) or not isinstance(observed, int) or observed <= default:
                errors.append(f"{key[0]}:{key[1]}: invalid debt observed complexity")
            elif actual > observed:
                errors.append(
                    f"{key[0]}:{key[1]}: complexity {actual} exceeds debt ceiling {observed}"
                )
            elif actual < observed:
                errors.append(
                    f"{key[0]}:{key[1]}: complexity improved to {actual}; "
                    "tighten or remove the stale debt exception"
                )
        results.append({"path": key[0], "function": key[1], "actual": actual, "kind": kind})
    for key, actual in measured.items():
        if actual > default and key not in entries:
            errors.append(
                f"{key[0]}:{key[1]}: complexity {actual} exceeds global maximum {default}"
            )
    return errors, sorted(results, key=lambda row: (row["path"], row["function"]))


def main() -> int:
    try:
        contract = _load_contract()
        measured = _ruff_complexities(contract["runtimeRoots"])
        errors, results = evaluate_budget(contract, measured)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, json.JSONDecodeError) as error:
        print(f"review-craft complexity budget: {error}", file=sys.stderr)
        return 2
    if errors:
        print("review-craft complexity budget failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "schema": "review-craft.complexity-budget-result.v2",
                "valid": True,
                "defaultMaximum": contract["defaultMaximum"],
                "scannedFunctions": len(measured),
                "functions": results,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
