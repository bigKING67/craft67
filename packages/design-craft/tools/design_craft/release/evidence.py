from __future__ import annotations

import subprocess
from pathlib import Path

from ..repo import REPO_ROOT
from ..validation.maturity.reporter import build_report
from ..validation.maturity.runner import evaluate_maturity
from .policy import ReleaseLevel


REPORT_SCHEMA = "design-craft.release-evidence.v1"


def _check(
    check_id: str,
    passed: bool,
    evidence: object,
    error: str = "",
) -> dict[str, object]:
    return {
        "id": check_id,
        "status": "passed" if passed else "failed",
        "evidence": evidence,
        "error": "" if passed else error,
    }


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=30,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def evaluate_release(
    level: ReleaseLevel,
    *,
    baseline_path: Path | None,
    benchmark_result_path: Path | None = None,
    benchmark_observation_path: Path | None = None,
    phase: str = "candidate",
) -> dict[str, object]:
    if phase not in {"candidate", "final"}:
        raise ValueError("release phase must be candidate or final")

    evaluation = evaluate_maturity(
        level.name,
        phase=phase,
        baseline_path=baseline_path,
        benchmark_result_path=benchmark_result_path,
        benchmark_observation_path=benchmark_observation_path,
    )
    maturity = build_report(evaluation, phase=phase, root=str(REPO_ROOT))
    gate_checks = [
        _check(
            gate["gate_id"],
            gate["status"] == "passed",
            gate["evidence"],
            gate["error"],
        )
        for gate in maturity["gates"]
    ]
    aggregate = _check(
        "operational_maturity",
        maturity["ok"] is True,
        {
            "schema": maturity["schema"],
            "profile": maturity["profile"],
            "failed_gate_ids": maturity["failed_gate_ids"],
            "metric_policy": maturity["metric_policy"],
        },
        "required maturity gates failed: " + ", ".join(maturity["failed_gate_ids"]),
    )
    checks = [aggregate, *gate_checks]

    if level.name == "certified_100":
        certification_ids = {
            "host_cursor_current_source",
            "host_claude_current_source",
            "native_physical_device_current_source",
        }
        certification_checks = [
            check for check in gate_checks if check["id"] in certification_ids
        ]
        certification_ok = (
            len(certification_checks) == len(certification_ids)
            and all(check["status"] == "passed" for check in certification_checks)
        )
        checks.append(
            _check(
                "release_certification",
                certification_ok,
                {"required": sorted(certification_ids)},
                "Cursor, Claude, and physical-device evidence are all required",
            )
        )

    check_by_id = {str(check["id"]): check for check in checks}
    missing_domains = [
        domain for domain in level.required_domains if domain not in check_by_id
    ]
    if missing_domains:
        checks.append(
            _check(
                "release_policy_domains",
                False,
                {"required_domains": list(level.required_domains)},
                "release evaluator is missing required domains: "
                + ", ".join(missing_domains),
            )
        )

    verified_hosts = [
        host
        for host in level.required_hosts
        if check_by_id.get(f"host_{host}_current_source", {}).get("status") == "passed"
    ]
    verified_native = [
        native
        for native in level.required_native
        if check_by_id.get(f"native_{native}_current_source", {}).get("status") == "passed"
    ]
    branch = _git("symbolic-ref", "--quiet", "--short", "HEAD")
    head = _git("rev-parse", "HEAD")
    ok = all(check["status"] == "passed" for check in checks)
    return {
        "schema": REPORT_SCHEMA,
        "release_level": level.name,
        "release_level_score": level.score,
        "phase": phase,
        "source_commit": head,
        "branch": branch or None,
        "verified_hosts": verified_hosts,
        "verified_native": verified_native,
        "unverified": maturity["unverified"],
        "evidence_retention": (
            "self_contained_native_release_bundle"
            if level.permanent_native_bundle
            else "workflow_artifact_90_days"
        ),
        "maturity": {
            "schema": maturity["schema"],
            "status": maturity["status"],
            "failed_gate_ids": maturity["failed_gate_ids"],
        },
        "checks": checks,
        "ok": ok,
    }
