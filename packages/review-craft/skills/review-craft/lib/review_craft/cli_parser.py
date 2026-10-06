from __future__ import annotations

import argparse

from . import __version__
from .assurance import ASSURANCE_LEVELS
from .cli_delivery import (
    command_validate_delivery,
    command_verify_attempt_delivery,
    command_verify_delivery,
)
from .cli_doctor import command_doctor
from .cli_evidence import command_register_evidence, command_run_evidence
from .cli_remediation import (
    command_capture_fix_attempt,
    command_finalize_fix_attempt,
    command_list_fix_attempts,
    command_prepare_fix,
    command_validate_fix,
    command_validate_fix_attempt,
    command_verify_fix,
)
from .cli_review import (
    command_anchor_location,
    command_finalize,
    command_preflight,
    command_validate,
    command_verification_input,
)
from .constants import (
    REGISTERED_EVIDENCE_KINDS,
    REGISTERED_EVIDENCE_MAX_BYTES,
    REVIEW_MODES,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review Craft deterministic runtime")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check runtime prerequisites")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(handler=command_doctor)

    preflight = subparsers.add_parser("preflight", help="Create a review run")
    preflight.add_argument("--target", required=True)
    preflight.add_argument("--config")
    preflight.add_argument("--output-root")
    preflight.add_argument("--mode", choices=sorted(REVIEW_MODES))
    preflight.add_argument("--assurance", choices=sorted(ASSURANCE_LEVELS))
    preflight.add_argument("--base", help="Git base revision for diff mode")
    preflight.add_argument(
        "--focus",
        action="append",
        help="Comma-separated canonical dimensions; can be repeated",
    )
    preflight.set_defaults(handler=command_preflight)

    anchor = subparsers.add_parser(
        "anchor-location",
        help="Create a source-bound run.v5 candidate or finding location",
    )
    anchor.add_argument("--run-dir", required=True)
    anchor.add_argument("--path", required=True)
    anchor.add_argument("--line-start", type=int, required=True)
    anchor.add_argument("--line-end", type=int)
    anchor.add_argument("--role", required=True)
    anchor.set_defaults(handler=command_anchor_location)

    verification = subparsers.add_parser(
        "verification-input", help="Read the exact findings and digest for independent review"
    )
    verification.add_argument("--run-dir", required=True)
    verification.set_defaults(handler=command_verification_input)

    evidence = subparsers.add_parser("run-evidence", help="Run an allowlisted evidence command")
    evidence.add_argument("--run-dir", required=True)
    evidence_selection = evidence.add_mutually_exclusive_group(required=True)
    evidence_selection.add_argument("--command")
    evidence_selection.add_argument("--all", action="store_true")
    evidence.set_defaults(handler=command_run_evidence)

    register = subparsers.add_parser(
        "register-evidence",
        help="Copy and content-bind a manual evidence artifact into a draft review",
    )
    register.add_argument("--run-dir", required=True)
    register.add_argument("--id", required=True)
    register.add_argument("--source", required=True)
    register.add_argument("--kind", choices=sorted(REGISTERED_EVIDENCE_KINDS), required=True)
    register.add_argument("--producer", required=True)
    register.add_argument("--description", required=True)
    register.add_argument("--media-type", default="application/octet-stream")
    register.add_argument("--max-bytes", type=int, default=REGISTERED_EVIDENCE_MAX_BYTES)
    register.set_defaults(handler=command_register_evidence)

    validate = subparsers.add_parser("validate", help="Validate canonical artifacts")
    validate.add_argument("--run-dir", required=True)
    validate.add_argument("--allow-draft", action="store_true")
    validate.set_defaults(handler=command_validate)

    finalize = subparsers.add_parser("finalize", help="Generate report.md")
    finalize.add_argument("--run-dir", required=True)
    finalize.set_defaults(handler=command_finalize)

    prepare = subparsers.add_parser(
        "prepare-fix", help="Bind selected findings before an explicitly authorized fix"
    )
    prepare.add_argument("--run-dir", required=True)
    prepare.add_argument("--output-root")
    selection = prepare.add_mutually_exclusive_group(required=True)
    selection.add_argument("--finding", action="append")
    selection.add_argument("--all-actionable", action="store_true")
    verification_commands = prepare.add_mutually_exclusive_group()
    verification_commands.add_argument("--command", action="append")
    verification_commands.add_argument("--all-commands", action="store_true")
    prepare.set_defaults(handler=command_prepare_fix)

    verify = subparsers.add_parser(
        "verify-fix", help="Capture post-fix changes, command evidence, and assessment"
    )
    verify.add_argument("--fix-dir", required=True)
    verify.add_argument("--assessment", required=True)
    verify.set_defaults(handler=command_verify_fix)

    validate_remediation = subparsers.add_parser(
        "validate-fix", help="Validate a prepared or completed fix session"
    )
    validate_remediation.add_argument("--fix-dir", required=True)
    validate_remediation.add_argument("--allow-prepared", action="store_true")
    validate_remediation.set_defaults(handler=command_validate_fix)

    capture_attempt = subparsers.add_parser(
        "capture-fix-attempt",
        help="Run commands into a new immutable fix attempt before assessment",
    )
    capture_attempt.add_argument("--fix-dir", required=True)
    capture_attempt.set_defaults(handler=command_capture_fix_attempt)

    finalize_attempt = subparsers.add_parser(
        "finalize-fix-attempt",
        help="Bind a post-command assessment to a captured fix attempt",
    )
    finalize_attempt.add_argument("--attempt-dir", required=True)
    finalize_attempt.add_argument("--assessment", required=True)
    finalize_attempt.set_defaults(handler=command_finalize_fix_attempt)

    validate_attempt = subparsers.add_parser(
        "validate-fix-attempt",
        help="Validate a finalized fix attempt and optionally its live target",
    )
    validate_attempt.add_argument("--attempt-dir", required=True)
    validate_attempt.add_argument("--snapshot-only", action="store_true")
    validate_attempt.set_defaults(handler=command_validate_fix_attempt)

    list_attempts = subparsers.add_parser(
        "list-fix-attempts",
        help="Validate and project the immutable attempt lineage for a fix",
    )
    list_attempts.add_argument("--fix-dir", required=True)
    list_attempts.set_defaults(handler=command_list_fix_attempts)

    delivery = subparsers.add_parser(
        "verify-delivery",
        help="Create a content-bound post-commit, push, and CI delivery attestation",
    )
    delivery.add_argument("--fix-dir", required=True)
    delivery.add_argument("--output-root")
    delivery.add_argument(
        "--verify-push",
        action="store_true",
        help="Run read-only git ls-remote verification for the current branch",
    )
    delivery.add_argument(
        "--github-run",
        type=int,
        help="Run read-only gh verification for a GitHub Actions run id",
    )
    delivery.set_defaults(handler=command_verify_delivery)

    attempt_delivery = subparsers.add_parser(
        "verify-attempt-delivery",
        help="Create a portable delivery attestation for the latest verified fix attempt",
    )
    attempt_delivery.add_argument("--attempt-dir", required=True)
    attempt_delivery.add_argument("--output-root")
    attempt_delivery.add_argument(
        "--verify-push",
        action="store_true",
        help="Run read-only git ls-remote verification for the current branch",
    )
    attempt_delivery.add_argument(
        "--github-run",
        type=int,
        help="Run read-only gh verification for a GitHub Actions run id",
    )
    attempt_delivery.set_defaults(handler=command_verify_attempt_delivery)

    validate_delivery_parser = subparsers.add_parser(
        "validate-delivery",
        help="Validate a portable delivery attestation without the original fix directory",
    )
    validate_delivery_parser.add_argument("--delivery-dir", required=True)
    validate_delivery_parser.set_defaults(handler=command_validate_delivery)
    return parser
