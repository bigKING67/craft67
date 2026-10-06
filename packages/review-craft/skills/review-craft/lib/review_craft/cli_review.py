from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .assurance import (
    ASSURANCE_BUDGETS,
    draft_assurance_state,
    eligible_file_count,
    verification_input,
)
from .cli_common import utc_now
from .configuration import effective_preflight_config, load_config
from .constants import (
    ARTIFACT_PATHS,
    REMEDIATION_PHASES,
    SCHEMA_VERSION,
    SCORE_DIMENSIONS,
)
from .contracts import validate_run
from .jsonio import (
    canonical_compact,
    sha256_bytes,
    sha256_json,
    write_json,
    write_jsonl,
)
from .report import finalize_run
from .repository import (
    fingerprint_inventory,
    inspect_git,
    inventory_for_mode,
    repository_identity,
    worktree_fingerprint,
)
from .repository_analysis import build_dependency_map, build_module_map, detect_profile
from .source_anchor import build_run_location


def _repository_name(state_root: Path, remote: str | None) -> str:
    if remote:
        tail = remote.rstrip("/").rsplit("/", 1)[-1]
        return tail.removesuffix(".git") or state_root.name
    return state_root.name


def _coverage_row(record: dict[str, Any]) -> dict[str, Any]:
    if record["kind"] == "unreadable":
        disposition = "UNREADABLE"
        reason = f"preflight could not read file ({record.get('readError', 'unknown')})"
    elif record["classification"] == "generated":
        disposition = "GENERATED"
        reason = "matched explicit generated pattern"
    elif record["classification"] == "vendored":
        disposition = "VENDORED"
        reason = "matched explicit vendored pattern"
    elif record["binary"]:
        disposition = "BINARY"
        reason = "binary or non-UTF-8 content"
    else:
        disposition = "PENDING"
        reason = "awaiting review"
    return {
        **record,
        "disposition": disposition,
        "reason": reason,
        "evidenceRefs": [],
    }


def _draft_artifacts(
    run_dir: Path,
    *,
    run_id: str,
    target: Path,
    config: dict[str, Any],
    records: list[dict[str, Any]],
    excluded: list[dict[str, str]],
    review_scope: dict[str, Any],
    module_map: dict[str, Any],
    dependency_map: dict[str, Any],
) -> None:
    state = inspect_git(target)
    source_fingerprint = fingerprint_inventory(records)
    manifest = {
        "documentType": "review-craft.manifest",
        "schemaVersion": SCHEMA_VERSION,
        "toolVersion": __version__,
        "status": "draft",
        "runId": run_id,
        "createdAt": utc_now(),
        "sealedAt": None,
        "target": {
            "repositoryName": _repository_name(state.root, state.remote),
            "identity": repository_identity(state, records),
            "revision": state.revision,
            "branch": state.branch,
            "remote": state.remote,
            "dirty": bool(state.status),
            "unborn": state.unborn,
            "sourceFingerprint": source_fingerprint,
            "dirtyFingerprint": sha256_bytes(
                state.status.encode("utf-8", errors="surrogateescape")
            ),
        },
        "configuration": config,
        "configFingerprint": sha256_json(config),
        "artifacts": ARTIFACT_PATHS,
    }
    quality_model = {
        "documentType": "review-craft.quality-model",
        "schemaVersion": SCHEMA_VERSION,
        "purpose": "",
        "audience": "",
        "criticalPaths": [],
        "invariants": [],
        "nonGoals": [],
        "compatibility": [],
        "performanceBudgets": [],
        "reliabilityRequirements": [],
        "authoritySources": [],
        "assumptions": [],
        "unknowns": [],
    }
    coverage_files = [_coverage_row(row) for row in records]
    accounted = sum(
        row["disposition"]
        in {"GENERATED", "VENDORED", "BINARY", "OUT_OF_SCOPE", "UNREADABLE", "DEFERRED"}
        for row in coverage_files
    )
    reviewed = sum(
        row["disposition"] in {"REVIEWED", "COVERED_BY_PARENT"}
        for row in coverage_files
    )
    accounted_percent = round(100 * accounted / len(coverage_files), 2) if coverage_files else 100.0
    reviewed_percent = round(100 * reviewed / len(coverage_files), 2) if coverage_files else 100.0
    coverage = {
        "documentType": "review-craft.coverage",
        "schemaVersion": SCHEMA_VERSION,
        "inventoryFingerprint": source_fingerprint,
        "files": coverage_files,
        "excluded": excluded,
        "summary": {
            "total": len(coverage_files),
            "reviewed": 0,
            "deferred": sum(
                1
                for row in coverage_files
                if row["disposition"] in {"PENDING", "DEFERRED", "UNREADABLE"}
            ),
        },
    }
    findings = {
        "documentType": "review-craft.findings",
        "schemaVersion": SCHEMA_VERSION,
        "findings": [],
    }
    decisions = {
        "documentType": "review-craft.decisions",
        "schemaVersion": SCHEMA_VERSION,
        "decisions": [],
    }
    scorecard = {
        "documentType": "review-craft.scorecard",
        "schemaVersion": SCHEMA_VERSION,
        "status": "provisional",
        "evidenceLevel": "E0",
        "confidence": "LOW",
        "coveragePercent": reviewed_percent,
        "accountedPercent": accounted_percent,
        "reviewedPercent": reviewed_percent,
        "unresolvedCandidates": 0,
        "assurance": draft_assurance_state(config, review_scope, coverage),
        "dimensions": [
            {
                "id": identifier,
                "label": label,
                "maximum": maximum,
                "awarded": 0,
                "deductions": [
                    {
                        "points": maximum,
                        "reason": "尚未完成审查，当前不形成正式评分",
                        "evidenceRefs": ["coverage:draft"],
                    }
                ],
            }
            for identifier, label, maximum in SCORE_DIMENSIONS
        ],
        "total": 0,
    }
    remediation = {
        "documentType": "review-craft.remediation-plan",
        "schemaVersion": SCHEMA_VERSION,
        "changeClass": "LOCAL_OPTIMIZATION",
        "targetScore": 0,
        "targetEvidenceLevel": "E1",
        "targetArchitecture": {
            "overview": "",
            "moduleBoundaries": [],
            "dependencyDirection": [],
            "coreDataFlow": [],
            "stateAndErrors": [],
            "directoryStructure": [],
            "testingStructure": [],
            "deliveryFlow": [],
        },
        "phases": [
            {
                "id": identifier,
                "title": title,
                "modificationScope": [],
                "prerequisites": [],
                "expectedBenefits": [],
                "risks": [],
                "acceptanceCriteria": [],
            }
            for identifier, title in REMEDIATION_PHASES
        ],
    }
    evidence_registry = {
        "documentType": "review-craft.evidence-registry",
        "schemaVersion": SCHEMA_VERSION,
        "artifacts": [],
    }
    write_json(run_dir / "review-manifest.json", manifest)
    write_json(run_dir / ARTIFACT_PATHS["reviewScope"], review_scope)
    write_json(run_dir / ARTIFACT_PATHS["qualityModel"], quality_model)
    write_json(run_dir / ARTIFACT_PATHS["coverage"], coverage)
    write_json(run_dir / ARTIFACT_PATHS["moduleMap"], module_map)
    write_json(run_dir / ARTIFACT_PATHS["dependencyMap"], dependency_map)
    write_jsonl(run_dir / ARTIFACT_PATHS["candidateLedger"], [])
    write_json(run_dir / ARTIFACT_PATHS["findings"], findings)
    write_json(run_dir / ARTIFACT_PATHS["decisions"], decisions)
    write_json(run_dir / ARTIFACT_PATHS["scorecard"], scorecard)
    write_json(run_dir / ARTIFACT_PATHS["remediationPlan"], remediation)
    write_json(run_dir / ARTIFACT_PATHS["evidenceRegistry"], evidence_registry, mode=0o600)
    write_jsonl(run_dir / ARTIFACT_PATHS["commands"], [])
    write_json(
        run_dir / "run-state.json",
        {
            "targetRoot": str(state.root),
            "worktreeFingerprint": worktree_fingerprint(state.root, records=records),
            "statusFingerprint": sha256_bytes(
                state.status.encode("utf-8", errors="surrogateescape")
            ),
            "mode": config["mode"],
            "diffBase": config["diffBase"],
        },
        mode=0o600,
    )


def command_preflight(args: argparse.Namespace) -> int:
    target = Path(args.target).expanduser().resolve(strict=True)
    if not target.is_dir():
        raise ValueError("--target: expected a directory")
    config = load_config(Path(args.config) if args.config else None)
    config, requested_base = effective_preflight_config(
        config,
        mode=args.mode,
        base=args.base,
        focus=args.focus,
        assurance=args.assurance,
    )
    state = inspect_git(target)
    root = state.root
    records, excluded, diff_context = inventory_for_mode(
        root,
        mode=config["mode"],
        scopes=config["scope"],
        excludes=config["exclude"],
        generated=config["generated"],
        vendored=config["vendored"],
        diff_base=config["diffBase"],
    )
    if config["assuranceLevel"] == "fast":
        eligible_files = eligible_file_count({"files": [_coverage_row(row) for row in records]})
        maximum = ASSURANCE_BUDGETS["fast"]["maxEligibleFiles"]
        if maximum is not None and eligible_files > maximum:
            raise ValueError(
                "fast assurance eligible-file budget exceeded: "
                f"{eligible_files} > {maximum}; narrow scope or use standard"
            )
    if diff_context is not None:
        config["diffBase"] = diff_context["baseRevision"]
    dimensions = config["focusDimensions"] or [row[0] for row in SCORE_DIMENSIONS]
    profile = detect_profile(root, records, config["profile"])
    review_scope = {
        "documentType": "review-craft.review-scope",
        "schemaVersion": SCHEMA_VERSION,
        "mode": config["mode"],
        "assuranceLevel": config["assuranceLevel"],
        "dimensions": dimensions,
        "profile": profile,
        "diff": (
            {
                "requestedBase": requested_base,
                "baseRevision": diff_context["baseRevision"],
                "changes": diff_context["changes"],
            }
            if diff_context is not None
            else None
        ),
    }
    module_map = build_module_map(records)
    dependency_map = build_dependency_map(root, records)
    state_hash = sha256_bytes(
        canonical_compact(
            {
                "identity": repository_identity(state, records),
                "config": config,
                "status": state.status,
            }
        ).encode("utf-8", errors="surrogateescape")
    )[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"rc-{stamp}-{state_hash}"
    output_root = (
        Path(args.output_root).expanduser().resolve()
        if args.output_root
        else Path(tempfile.gettempdir()) / "review-craft-runs"
    )
    run_dir = output_root / _repository_name(root, state.remote) / run_id
    if config["policy"]["outputOutsideRepository"]:
        try:
            run_dir.resolve().relative_to(root)
        except ValueError:
            pass
        else:
            raise ValueError("--output-root resolves inside the target repository")
    suffix = 2
    while run_dir.exists():
        run_dir = run_dir.with_name(f"{run_id}-{suffix}")
        suffix += 1
    run_dir.mkdir(parents=True, mode=0o700)
    _draft_artifacts(
        run_dir,
        run_id=run_dir.name,
        target=root,
        config=config,
        records=records,
        excluded=excluded,
        review_scope=review_scope,
        module_map=module_map,
        dependency_map=dependency_map,
    )
    print(
        json.dumps(
            {
                "runId": run_dir.name,
                "runDir": str(run_dir),
                "files": len(records),
                "mode": config["mode"],
                "profile": profile["resolved"],
                "assuranceLevel": config["assuranceLevel"],
            },
            ensure_ascii=False,
        )
    )
    return 0

def command_validate(args: argparse.Namespace) -> int:
    data = validate_run(Path(args.run_dir), final=not args.allow_draft)
    print(
        json.dumps(
            {
                "valid": True,
                "runId": data["manifest"]["runId"],
                "final": not args.allow_draft,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def command_anchor_location(args: argparse.Namespace) -> int:
    location = build_run_location(
        args.run_dir,
        path=args.path,
        line_start=args.line_start,
        line_end=args.line_end,
        role=args.role,
    )
    print(json.dumps(location, ensure_ascii=False, sort_keys=True))
    return 0


def command_finalize(args: argparse.Namespace) -> int:
    report = finalize_run(Path(args.run_dir), sealed_at=utc_now())
    print(json.dumps({"report": str(report)}, ensure_ascii=False, sort_keys=True))
    return 0


def command_verification_input(args: argparse.Namespace) -> int:
    data = validate_run(Path(args.run_dir), final=False)
    manifest = data["manifest"]
    if manifest.get("schemaVersion") != SCHEMA_VERSION or manifest.get("status") != "draft":
        raise ValueError("verification-input requires a current run.v5 draft")
    print(json.dumps(verification_input(data), ensure_ascii=True, sort_keys=True))
    return 0
