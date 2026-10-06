from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assurance import ASSURANCE_BUDGETS
from .cli_common import utc_now
from .constants import ARTIFACT_PATHS
from .evidence import run_evidence_command
from .evidence_registry import register_evidence
from .jsonio import read_json, read_jsonl


def command_run_evidence(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve(strict=True)
    manifest = read_json(run_dir / "review-manifest.json")
    existing_receipts = read_jsonl(run_dir / ARTIFACT_PATHS["commands"])
    fast_limit = ASSURANCE_BUDGETS["fast"]["maxEvidenceCommands"]
    if args.all:
        names = sorted(manifest["configuration"]["commands"])
        if not names:
            raise ValueError("no configured evidence commands")
        if (
            manifest["configuration"].get("assuranceLevel") == "fast"
            and fast_limit is not None
            and len(existing_receipts) + len(names) > fast_limit
        ):
            raise ValueError(
                "fast assurance evidence-command budget exceeded: "
                f"{len(existing_receipts) + len(names)} > {fast_limit}"
            )
        receipts = []
        final_code = 0
        for name in names:
            code, receipt = run_evidence_command(args.run_dir, name)
            receipts.append(receipt)
            if code != 0 and final_code == 0:
                final_code = code
            if receipt["repositoryMutationDetected"] and code == 3:
                break
        print(json.dumps({"commands": receipts}, ensure_ascii=False, sort_keys=True))
        return final_code
    if (
        manifest["configuration"].get("assuranceLevel") == "fast"
        and fast_limit is not None
        and len(existing_receipts) + 1 > fast_limit
    ):
        raise ValueError(
            "fast assurance evidence-command budget exceeded: "
            f"{len(existing_receipts) + 1} > {fast_limit}"
        )
    code, receipt = run_evidence_command(args.run_dir, args.command)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return code


def command_register_evidence(args: argparse.Namespace) -> int:
    entry = register_evidence(
        args.run_dir,
        identifier=args.id,
        source_value=args.source,
        kind=args.kind,
        producer=args.producer,
        description=args.description,
        media_type=args.media_type,
        registered_at=utc_now(),
        max_bytes=args.max_bytes,
    )
    print(json.dumps(entry, ensure_ascii=False, sort_keys=True))
    return 0
