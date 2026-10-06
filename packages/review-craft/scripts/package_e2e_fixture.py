#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


def _installed_runtime(package_root: Path) -> dict[str, Any]:
    runtime_root = package_root / "skills/review-craft/lib"
    sys.path.insert(0, str(runtime_root))
    import review_craft
    from review_craft.constants import (
        ARTIFACT_PATHS,
        REMEDIATION_PHASES,
        SCHEMA_VERSION,
        SCORE_DIMENSIONS,
    )
    from review_craft.jsonio import read_json, sha256_json, write_json, write_jsonl
    from review_craft.source_anchor import build_run_location

    module_path = Path(review_craft.__file__).resolve()
    try:
        module_path.relative_to(package_root.resolve())
    except ValueError as error:
        raise RuntimeError(f"runtime resolved outside installed package: {module_path}") from error
    return {
        "ARTIFACT_PATHS": ARTIFACT_PATHS,
        "REMEDIATION_PHASES": REMEDIATION_PHASES,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "SCORE_DIMENSIONS": SCORE_DIMENSIONS,
        "build_run_location": build_run_location,
        "read_json": read_json,
        "sha256_json": sha256_json,
        "write_json": write_json,
        "write_jsonl": write_jsonl,
    }


def _deductions(maximum: int, awarded: int) -> list[dict[str, Any]]:
    if awarded == maximum:
        return []
    return [
        {
            "points": maximum - awarded,
            "reason": "Installed-package fixture confirmed an incorrect result.",
            "evidenceRefs": ["RC-FINDING-001"],
        }
    ]


def populate_run(run_dir: Path, runtime: dict[str, Any]) -> None:
    artifacts = runtime["ARTIFACT_PATHS"]
    read_json = runtime["read_json"]
    write_json = runtime["write_json"]
    write_jsonl = runtime["write_jsonl"]
    schema_version = runtime["SCHEMA_VERSION"]

    quality_model = read_json(run_dir / artifacts["qualityModel"])
    quality_model.update(
        {
            "purpose": "Exercise the exact installed Review Craft package.",
            "audience": "Release-contract maintainers.",
            "criticalPaths": ["Call answer and receive the contract value."],
            "invariants": ["answer returns 42 after the authorized fix."],
            "nonGoals": ["No network, UI, or multi-user behavior."],
            "compatibility": ["Python 3.10 and newer."],
            "performanceBudgets": ["No material performance budget for this fixture."],
            "reliabilityRequirements": ["The function does not raise."],
            "authoritySources": ["app.py and the configured behavior check."],
            "assumptions": ["This fixture represents a small library."],
            "unknowns": [],
        }
    )
    write_json(run_dir / artifacts["qualityModel"], quality_model)

    coverage = read_json(run_dir / artifacts["coverage"])
    for row in coverage["files"]:
        row["disposition"] = "REVIEWED"
        row["reason"] = "Inspected by the installed-package fixture."
        row["evidenceRefs"] = [f"source:{row['path']}"]
    coverage["summary"]["reviewed"] = len(coverage["files"])
    coverage["summary"]["deferred"] = 0
    write_json(run_dir / artifacts["coverage"], coverage)

    location = runtime["build_run_location"](
        run_dir,
        path="app.py",
        line_start=1,
        line_end=2,
        role="primary",
    )
    candidate = {
        "id": "RC-CORR-001",
        "category": "correctness",
        "type": "incorrect_result",
        "title": "Fixture returns the stale value",
        "locations": [location],
        "evidence": [
            {
                "kind": "source_trace",
                "ref": "source:app.py:1-2",
                "summary": "The function returns 41 while the bound contract requires 42.",
            }
        ],
        "claimedImpact": ["The returned result is incorrect."],
        "confidence": "HIGH",
        "validation": {
            "status": "CONFIRMED",
            "method": "Direct source trace against the fixture contract.",
            "evidenceRefs": ["source:app.py:1-2"],
            "remainingUncertainty": "",
        },
    }
    write_jsonl(run_dir / artifacts["candidateLedger"], [candidate])

    finding = {
        "id": "RC-FINDING-001",
        "candidateId": "RC-CORR-001",
        "title": "Fixture returns the stale value",
        "category": "correctness",
        "locations": [location],
        "evidenceRefs": ["source:app.py:1-2"],
        "rootCause": "The fixture constant did not move with its behavior contract.",
        "currentImpact": "Callers receive the wrong integer.",
        "longTermRisk": "Tests and examples can preserve the stale behavior.",
        "validationStatus": "CONFIRMED",
        "confidence": "HIGH",
        "severity": "MEDIUM",
        "priority": "P1",
        "recommendation": "Update the constant and run the bound behavior check.",
        "decisionId": "RC-DECISION-001",
        "modificationCost": "LOW",
        "modificationRisk": "LOW",
        "verification": ["Call answer and assert that it returns 42."],
    }
    write_json(
        run_dir / artifacts["findings"],
        {
            "documentType": "review-craft.findings",
            "schemaVersion": schema_version,
            "findings": [finding],
        },
    )
    decisions = [
        {
            "id": "RC-DECISION-001",
            "subject": "app.answer constant",
            "findingRefs": ["RC-FINDING-001"],
            "decision": "CLEAN_UP",
            "rationale": "A local correction is sufficient.",
            "alternatives": ["A rewrite would add no value."],
            "migration": "",
            "compatibilityRisks": [],
            "rollback": "",
            "verification": ["Run the configured behavior check."],
        },
        {
            "id": "RC-DECISION-KEEP-001",
            "subject": "single-function module boundary",
            "findingRefs": [],
            "decision": "KEEP",
            "rationale": "The module has one cohesive responsibility.",
            "alternatives": [],
            "migration": "",
            "compatibilityRisks": [],
            "rollback": "",
            "verification": ["Confirm the module retains one public behavior."],
        },
    ]
    write_json(
        run_dir / artifacts["decisions"],
        {
            "documentType": "review-craft.decisions",
            "schemaVersion": schema_version,
            "decisions": decisions,
        },
    )

    awarded_by_id = {
        "correctness": 18,
        "architecture": 18,
        "maintainability": 12,
        "performance": 12,
        "codeQuality": 8,
        "testing": 8,
        "dependenciesSecurity": 4,
        "repositoryExperience": 5,
    }
    dimensions = []
    for identifier, label, maximum in runtime["SCORE_DIMENSIONS"]:
        awarded = awarded_by_id[identifier]
        dimensions.append(
            {
                "id": identifier,
                "label": label,
                "maximum": maximum,
                "awarded": awarded,
                "deductions": _deductions(maximum, awarded),
            }
        )
    write_json(
        run_dir / artifacts["scorecard"],
        {
            "documentType": "review-craft.scorecard",
            "schemaVersion": schema_version,
            "status": "final",
            "evidenceLevel": "E1",
            "confidence": "HIGH",
            "coveragePercent": 100.0,
            "accountedPercent": 100.0,
            "reviewedPercent": 100.0,
            "unresolvedCandidates": 0,
            "dimensions": dimensions,
            "total": 85,
        },
    )

    target_architecture = {
        "overview": "Keep the fixture as a minimal single-module library.",
        "moduleBoundaries": ["answer remains in the domain module."],
        "dependencyDirection": ["The behavior check reads only the public source."],
        "coreDataFlow": ["caller -> answer -> integer"],
        "stateAndErrors": ["The function remains stateless and deterministic."],
        "directoryStructure": ["Implementation and contract remain directly discoverable."],
        "testingStructure": ["Use one focused structured behavior assertion."],
        "deliveryFlow": ["Run the behavior assertion before delivery."],
    }
    phases = [
        {
            "id": identifier,
            "title": title,
            "modificationScope": ["The fixture module and focused behavior check."],
            "prerequisites": ["Preserve the source fingerprint as baseline."],
            "expectedBenefits": ["Restore the declared behavior with regression evidence."],
            "risks": ["A caller may have encoded the stale value."],
            "acceptanceCriteria": ["The check passes with no unrelated target mutation."],
        }
        for identifier, title in runtime["REMEDIATION_PHASES"]
    ]
    write_json(
        run_dir / artifacts["remediationPlan"],
        {
            "documentType": "review-craft.remediation-plan",
            "schemaVersion": schema_version,
            "changeClass": "LOCAL_OPTIMIZATION",
            "targetScore": 92,
            "targetEvidenceLevel": "E3",
            "targetArchitecture": target_architecture,
            "phases": phases,
        },
    )


def write_attempt_assessment(
    attempt_dir: Path, output: Path, runtime: dict[str, Any]
) -> None:
    read_json = runtime["read_json"]
    manifest = read_json(attempt_dir / "attempt-manifest.json")
    evidence = read_json(attempt_dir / "attempt-evidence.json")
    runtime["write_json"](
        output,
        {
            "documentType": "review-craft.fix-attempt-assessment",
            "schemaVersion": "review-craft.fix-attempt.v1",
            "fixId": manifest["fixId"],
            "attemptId": manifest["attemptId"],
            "evidenceSha256": runtime["sha256_json"](evidence),
            "kind": "AUTOMATED",
            "assessor": "installed-package-e2e",
            "assessedAt": evidence["completedAt"],
            "findings": [
                {
                    "findingId": "RC-FINDING-001",
                    "status": "RESOLVED",
                    "rationale": "The declared change and structured behavior claim both passed.",
                    "evidenceRefs": [
                        "change:app.py",
                        "claim:check:fixed-behavior-check",
                    ],
                }
            ],
            "measurements": [],
            "remainingRisks": [],
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Installed-package E2E fixture authoring")
    parser.add_argument("--package-root", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    populate = subparsers.add_parser("populate-run")
    populate.add_argument("--run-dir", required=True)
    assessment = subparsers.add_parser("write-assessment")
    assessment.add_argument("--attempt-dir", required=True)
    assessment.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package_root = Path(args.package_root).resolve(strict=True)
    runtime = _installed_runtime(package_root)
    if args.command == "populate-run":
        populate_run(Path(args.run_dir).resolve(strict=True), runtime)
    else:
        write_attempt_assessment(
            Path(args.attempt_dir).resolve(strict=True),
            Path(args.output).resolve(),
            runtime,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
