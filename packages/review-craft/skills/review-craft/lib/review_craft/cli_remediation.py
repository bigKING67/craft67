from __future__ import annotations

import argparse
import json

from .jsonio import sha256_json
from .remediation import prepare_fix, verify_fix
from .remediation_attempt_validation import (
    validate_fix_attempt,
    validate_fix_lineage,
)
from .remediation_attempts import capture_fix_attempt, finalize_fix_attempt
from .remediation_validation import validate_fix


def command_prepare_fix(args: argparse.Namespace) -> int:
    fix_dir, plan = prepare_fix(
        args.run_dir,
        finding_ids=args.finding or [],
        all_actionable=args.all_actionable,
        command_names=args.command or [],
        all_commands=args.all_commands,
        output_root=args.output_root,
    )
    print(
        json.dumps(
            {
                "fixId": plan["fixId"],
                "fixDir": str(fix_dir),
                "findings": [row["findingId"] for row in plan["selections"]],
                "commands": plan["verification"]["commands"],
                "sourceMutation": plan["authorization"]["sourceMutation"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def command_verify_fix(args: argparse.Namespace) -> int:
    result = verify_fix(args.fix_dir, assessment_path=args.assessment)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return {"VERIFIED": 0, "PARTIAL": 3, "FAILED": 4, "NO_CHANGES": 5}[
        result["status"]
    ]


def command_validate_fix(args: argparse.Namespace) -> int:
    data = validate_fix(args.fix_dir, require_verification=not args.allow_prepared)
    verification = data["verification"]
    print(
        json.dumps(
            {
                "valid": True,
                "fixId": data["plan"]["fixId"],
                "status": verification["status"] if verification is not None else "PREPARED",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def command_capture_fix_attempt(args: argparse.Namespace) -> int:
    attempt_dir, evidence = capture_fix_attempt(args.fix_dir)
    print(
        json.dumps(
            {
                "attemptId": evidence["attemptId"],
                "attemptDir": str(attempt_dir),
                "captureStatus": evidence["captureStatus"],
                "completedAt": evidence["completedAt"],
                "evidenceSha256": sha256_json(evidence),
                "commands": evidence["commands"],
                "skippedCommands": evidence["skippedCommands"],
                "failureReasons": evidence["failureReasons"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return {"PASSED": 0, "FAILED": 4, "NO_CHANGES": 5}[evidence["captureStatus"]]


def command_finalize_fix_attempt(args: argparse.Namespace) -> int:
    result = finalize_fix_attempt(
        args.attempt_dir,
        assessment_path=args.assessment,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return {"VERIFIED": 0, "PARTIAL": 3, "FAILED": 4, "NO_CHANGES": 5}[
        result["status"]
    ]


def command_validate_fix_attempt(args: argparse.Namespace) -> int:
    data = validate_fix_attempt(
        args.attempt_dir,
        compare_live=not args.snapshot_only,
    )
    verification = data["verification"]
    print(
        json.dumps(
            {
                "valid": True,
                "fixId": data["plan"]["fixId"],
                "attemptId": data["manifest"]["attemptId"],
                "status": verification["status"],
                "snapshotOnly": args.snapshot_only,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def command_list_fix_attempts(args: argparse.Namespace) -> int:
    lineage = validate_fix_lineage(args.fix_dir)["lineage"]
    print(json.dumps(lineage, ensure_ascii=False, sort_keys=True))
    return 0
