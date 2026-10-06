from __future__ import annotations

import argparse
import json

from .attempt_delivery import verify_attempt_delivery
from .delivery import verify_delivery
from .delivery_validation import validate_delivery


def command_verify_delivery(args: argparse.Namespace) -> int:
    delivery_dir, attestation = verify_delivery(
        args.fix_dir,
        verify_push=args.verify_push,
        github_run=args.github_run,
        output_root=args.output_root,
    )
    print(
        json.dumps(
            {
                "deliveryId": attestation["deliveryId"],
                "deliveryDir": str(delivery_dir),
                "status": attestation["status"],
                "commit": attestation["localSource"]["revision"],
                "push": attestation["push"]["status"],
                "githubActions": attestation["githubActions"]["status"],
                "githubRelease": attestation["githubRelease"]["status"],
                "npmPackage": attestation["npmPackage"]["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return {"VERIFIED": 0, "PARTIAL": 3, "FAILED": 4}[attestation["status"]]


def command_verify_attempt_delivery(args: argparse.Namespace) -> int:
    delivery_dir, attestation = verify_attempt_delivery(
        args.attempt_dir,
        verify_push=args.verify_push,
        github_run=args.github_run,
        output_root=args.output_root,
    )
    print(
        json.dumps(
            {
                "deliveryId": attestation["deliveryId"],
                "deliveryDir": str(delivery_dir),
                "status": attestation["status"],
                "fixId": attestation["fix"]["fixId"],
                "attemptId": attestation["fix"]["attemptId"],
                "lineageStatus": attestation["fix"]["lineageStatus"],
                "commit": attestation["localSource"]["revision"],
                "push": attestation["push"]["status"],
                "githubActions": attestation["githubActions"]["status"],
                "githubRelease": attestation["githubRelease"]["status"],
                "npmPackage": attestation["npmPackage"]["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return {"VERIFIED": 0, "PARTIAL": 3, "FAILED": 4}[attestation["status"]]


def command_validate_delivery(args: argparse.Namespace) -> int:
    attestation = validate_delivery(args.delivery_dir)["attestation"]
    payload = {
        "valid": True,
        "schemaVersion": attestation["schemaVersion"],
        "deliveryId": attestation["deliveryId"],
        "status": attestation["status"],
        "fixId": attestation["fix"]["fixId"],
    }
    if "attemptId" in attestation["fix"]:
        payload["attemptId"] = attestation["fix"]["attemptId"]
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0
