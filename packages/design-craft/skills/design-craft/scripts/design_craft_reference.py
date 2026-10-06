#!/usr/bin/env python3
"""Build and validate bounded design-craft visual-reference artifacts."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR.parent / "lib"
sys.dont_write_bytecode = True
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

peekpaper = importlib.import_module("design_craft.peekpaper")
contract = importlib.import_module("design_craft.reference_contract")

MAX_ISSUES = 8


def _write_payload(payload: dict[str, object], output: str) -> None:
    rendered = contract.json_text(payload)
    if not output:
        sys.stdout.write(rendered)
        return
    path = Path(output).expanduser()
    if not path.parent.is_dir():
        raise OSError(f"output parent does not exist: {path.parent}")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(rendered)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _candidate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "peekpaper-candidates",
        help="Normalize one to eight Peekpaper issues into a candidate catalog.",
    )
    parser.add_argument("--issue", action="append", required=True)
    parser.add_argument("--observed-at", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fixture-dir")
    source.add_argument("--allow-network", action="store_true")
    parser.add_argument("--output", default="")


def _validate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "validate", help="Validate card, catalog, or pack JSON artifacts."
    )
    parser.add_argument("paths", nargs="+")


def _pack_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "build-pack", help="Build a bounded Reference Pack from reviewed cards."
    )
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--reference", action="append", required=True)
    parser.add_argument("--surface-mode", choices=contract.SURFACE_MODES, required=True)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--primary-job", required=True)
    parser.add_argument("--authority-ref", action="append", required=True)
    parser.add_argument("--created-at", default="")
    parser.add_argument("--output", default="")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)
    _candidate_parser(subparsers)
    _validate_parser(subparsers)
    _pack_parser(subparsers)
    return root


def _run_candidates(args: argparse.Namespace) -> int:
    issues = list(dict.fromkeys(args.issue))
    if len(issues) != len(args.issue):
        print("Peekpaper issue dates must not repeat", file=sys.stderr)
        return 2
    if not 1 <= len(issues) <= MAX_ISSUES:
        print(f"select between one and {MAX_ISSUES} Peekpaper issues", file=sys.stderr)
        return 2
    try:
        sources = (
            [peekpaper.fetch_issue(issue) for issue in issues]
            if args.allow_network
            else [
                peekpaper.load_issue_fixture(Path(args.fixture_dir), issue)
                for issue in issues
            ]
        )
        catalog = peekpaper.build_catalog(sources, observed_at=args.observed_at)
        errors, warnings = contract.validate_catalog(catalog)
        if errors:
            raise peekpaper.PeekpaperError(
                "normalized catalog failed validation: " + "; ".join(errors)
            )
        if warnings:
            print("\n".join(warnings), file=sys.stderr)
        _write_payload(catalog, args.output)
    except (peekpaper.PeekpaperError, peekpaper.PeekpaperFetchError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 3
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    results: list[dict[str, object]] = []
    ok = True
    for raw_path in args.paths:
        path = Path(raw_path).expanduser()
        try:
            payload = contract.load_json(path)
            schema, errors, warnings = contract.validate_document(
                payload, today=date.today()
            )
        except (OSError, ValueError) as exc:
            schema = "unknown"
            errors = [str(exc)]
            warnings = []
        item_ok = not errors
        ok = ok and item_ok
        results.append(
            {
                "path": str(path),
                "schema": schema,
                "ok": item_ok,
                "errors": errors,
                "warnings": warnings,
            }
        )
    _write_payload(
        {
            "schema": "design-craft.visual-reference-validation.v1",
            "ok": ok,
            "results": results,
        },
        "",
    )
    return 0 if ok else 2


def _parse_selections(values: Sequence[str]) -> tuple[list[tuple[str, str]], list[str]]:
    selections: list[tuple[str, str]] = []
    errors: list[str] = []
    for value in values:
        if ":" not in value:
            errors.append(f"reference must use <card-id>:<role>: {value!r}")
            continue
        card_id, role = value.rsplit(":", 1)
        if not card_id or role not in contract.REFERENCE_ROLES:
            errors.append(f"invalid reference selection: {value!r}")
            continue
        selections.append((card_id, role))
    return selections, errors


def _run_build_pack(args: argparse.Namespace) -> int:
    selections, selection_errors = _parse_selections(args.reference)
    try:
        catalog = contract.load_json(Path(args.catalog).expanduser())
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    pack = contract.build_reference_pack(
        catalog,
        selections,
        surface_mode=args.surface_mode,
        audience=args.audience,
        primary_job=args.primary_job,
        authority_refs=args.authority_ref,
        created_at=args.created_at or None,
    )
    if selection_errors:
        pack["status"] = "incomplete"
        pack["blocking_reasons"] = list(
            dict.fromkeys([*selection_errors, *pack["blocking_reasons"]])
        )
    errors, _ = contract.validate_pack(pack)
    if errors:
        pack["status"] = "incomplete"
        pack["blocking_reasons"] = list(
            dict.fromkeys([*pack["blocking_reasons"], *errors])
        )
    try:
        _write_payload(pack, args.output)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0 if pack["status"] == "ready" else 2


def run(argv: Sequence[str]) -> int:
    args = parser().parse_args(list(argv))
    if args.command == "peekpaper-candidates":
        return _run_candidates(args)
    if args.command == "validate":
        return _run_validate(args)
    if args.command == "build-pack":
        return _run_build_pack(args)
    raise AssertionError(f"unhandled command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    return run(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
