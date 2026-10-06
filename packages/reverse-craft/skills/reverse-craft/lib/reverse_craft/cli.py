from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence, TextIO

from . import __version__
from .case_store import (
    add_evidence,
    add_finding,
    add_path,
    case_status,
    init_case,
    render_report,
    seal_case,
    validate_case,
)
from .common import ReverseCraftError
from .doctor import doctor
from .provenance import audit_references
from .routing import route
from .setup_ops import apply_plan, create_plan, setup_status


def _write_text(value: str, stream: TextIO) -> None:
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        value.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        value = value.encode("unicode_escape").decode("ascii")
    stream.write(value + "\n")


def _print(value: Any, as_json: bool = True, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) if as_json else str(value)
    if as_json:
        encoding = getattr(target, "encoding", None) or "utf-8"
        try:
            rendered.encode(encoding)
        except (LookupError, UnicodeEncodeError):
            rendered = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True)
    _write_text(rendered, target)


def _add_common_home(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--home", help="override REVERSE_CRAFT_HOME")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reverse-craft", description="Evidence-first reverse engineering workbench")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    doctor_parser = sub.add_parser("doctor", help="read-only environment and integration diagnostics")
    doctor_parser.add_argument("--deep", action="store_true", help="run bounded version probes")
    doctor_parser.add_argument("--json", action="store_true")
    _add_common_home(doctor_parser)

    route_parser = sub.add_parser("route", help="select the primary specialist route")
    route_parser.add_argument("--hint", required=True)
    route_parser.add_argument("--artifact")
    route_parser.add_argument("--json", action="store_true")

    case_parser = sub.add_parser("case", help="manage case lifecycle")
    case_sub = case_parser.add_subparsers(dest="case_command", required=True)
    case_init = case_sub.add_parser("init")
    case_init.add_argument("--title", required=True)
    case_init.add_argument("--scope", required=True)
    case_init.add_argument("--route")
    _add_common_home(case_init)
    case_show = case_sub.add_parser("status")
    case_show.add_argument("--case", required=True)
    _add_common_home(case_show)
    case_validate = case_sub.add_parser("validate")
    case_validate.add_argument("--case", required=True)
    case_validate.add_argument("--json", action="store_true")
    _add_common_home(case_validate)
    case_seal = case_sub.add_parser("seal")
    case_seal.add_argument("--case", required=True)
    _add_common_home(case_seal)

    evidence_parser = sub.add_parser("evidence", help="add preserved evidence")
    evidence_sub = evidence_parser.add_subparsers(dest="evidence_command", required=True)
    evidence_add = evidence_sub.add_parser("add")
    evidence_add.add_argument("--case", required=True)
    evidence_add.add_argument("--file", required=True)
    evidence_add.add_argument("--kind", required=True)
    evidence_add.add_argument("--note")
    evidence_add.add_argument("--source")
    evidence_add.add_argument("--external", action="store_true")
    _add_common_home(evidence_add)

    finding_parser = sub.add_parser("finding", help="record evidence-linked findings")
    finding_sub = finding_parser.add_subparsers(dest="finding_command", required=True)
    finding_add = finding_sub.add_parser("add")
    finding_add.add_argument("--case", required=True)
    finding_add.add_argument("--title", required=True)
    finding_add.add_argument("--statement")
    finding_add.add_argument("--severity", choices=["info", "low", "medium", "high", "critical"], required=True)
    finding_add.add_argument("--status", choices=["hypothesis", "supported", "confirmed", "refuted"], required=True)
    finding_add.add_argument("--confidence", choices=["low", "medium", "high"], default="medium")
    finding_add.add_argument("--evidence", action="append", default=[])
    finding_add.add_argument("--reproduction")
    _add_common_home(finding_add)

    path_parser = sub.add_parser("path", help="record ordered finding paths")
    path_sub = path_parser.add_subparsers(dest="path_command", required=True)
    path_add = path_sub.add_parser("add")
    path_add.add_argument("--case", required=True)
    path_add.add_argument("--title", required=True)
    path_add.add_argument("--finding", action="append", required=True)
    path_add.add_argument("--status", choices=["hypothesis", "supported", "confirmed", "refuted"], default="supported")
    path_add.add_argument("--preconditions")
    path_add.add_argument("--impact")
    path_add.add_argument("--validation")
    _add_common_home(path_add)

    report_parser = sub.add_parser("report", help="render deterministic case reports")
    report_sub = report_parser.add_subparsers(dest="report_command", required=True)
    report_render = report_sub.add_parser("render")
    report_render.add_argument("--case", required=True)
    report_render.add_argument("--output")
    _add_common_home(report_render)

    setup_parser = sub.add_parser("setup", help="plan or explicitly apply tool bootstrap")
    setup_sub = setup_parser.add_subparsers(dest="setup_command", required=True)
    setup_plan = setup_sub.add_parser("plan")
    setup_plan.add_argument("--profile", choices=["core", "binary", "android", "ios", "web", "forensics", "firmware", "wireless", "all"], required=True)
    setup_plan.add_argument("--output", required=True)
    _add_common_home(setup_plan)
    setup_apply = setup_sub.add_parser("apply")
    setup_apply.add_argument("--plan", required=True)
    setup_apply.add_argument("--sha256", required=True)
    setup_apply.add_argument("--yes", action="store_true")
    _add_common_home(setup_apply)
    setup_show = setup_sub.add_parser("status")
    _add_common_home(setup_show)

    refs = sub.add_parser("references", help="audit source provenance")
    refs_sub = refs.add_subparsers(dest="references_command", required=True)
    refs_audit = refs_sub.add_parser("audit")
    refs_audit.add_argument("--remote", action="store_true")
    refs_audit.add_argument("--json", action="store_true")
    return parser


def run(args: argparse.Namespace) -> Any:
    if args.command == "doctor":
        return doctor(args.deep, args.home)
    if args.command == "route":
        return route(args.hint, args.artifact)
    if args.command == "case":
        if args.case_command == "init":
            return init_case(args.title, args.scope, args.route, args.home)
        if args.case_command == "status":
            return case_status(args.case, args.home)
        if args.case_command == "validate":
            return validate_case(args.case, args.home)
        if args.case_command == "seal":
            return seal_case(args.case, args.home)
    if args.command == "evidence" and args.evidence_command == "add":
        return add_evidence(args.case, args.file, args.kind, args.note, args.external, args.source, args.home)
    if args.command == "finding" and args.finding_command == "add":
        return add_finding(args.case, args.title, args.severity, args.status, args.evidence, args.statement, args.reproduction, args.confidence, args.home)
    if args.command == "path" and args.path_command == "add":
        return add_path(args.case, args.title, args.finding, args.status, args.preconditions, args.impact, args.validation, args.home)
    if args.command == "report" and args.report_command == "render":
        return render_report(args.case, args.output, args.home)
    if args.command == "setup":
        if args.setup_command == "plan":
            return create_plan(args.profile, args.output, args.home)
        if args.setup_command == "apply":
            return apply_plan(args.plan, args.sha256, args.yes, args.home)
        if args.setup_command == "status":
            return setup_status(args.home)
    if args.command == "references" and args.references_command == "audit":
        return audit_references(args.remote)
    raise ReverseCraftError("unsupported command")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        result = run(args)
        _print(result)
        if isinstance(result, dict) and result.get("valid") is False:
            return 1
        return 0
    except ReverseCraftError as exc:
        _print({"schema": "reverse-craft.error.v1", "error": str(exc)}, stream=sys.stderr)
        return 2
    except Exception as exc:
        _print(
            {
                "schema": "reverse-craft.crash.v1",
                "error": "unexpected internal error",
                "exception_type": type(exc).__name__,
            },
            stream=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
