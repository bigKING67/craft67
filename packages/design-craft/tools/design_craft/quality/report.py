from __future__ import annotations

from pathlib import Path

from ..release.evidence import evaluate_release
from ..release.policy import load_policy


SCHEMA = "design-craft.quality-report.v1"


def build_quality_report(
    *, baseline_path: Path | None, release_level: str = "operational_95"
) -> dict[str, object]:
    policy = load_policy()
    evidence = evaluate_release(
        policy[release_level], baseline_path=baseline_path, phase="candidate"
    )
    checks = {check["id"]: check for check in evidence["checks"]}

    def domain(name: str, check_ids: tuple[str, ...]) -> dict[str, object]:
        selected = [checks[check_id] for check_id in check_ids if check_id in checks]
        passed = bool(selected) and all(item["status"] == "passed" for item in selected)
        return {
            "name": name,
            "status": "passed" if passed else "incomplete",
            "checks": selected,
        }

    host_checks = tuple(
        check_id for check_id in checks if check_id.startswith("host_")
    )
    native_checks = tuple(
        check_id for check_id in checks if check_id.startswith("native_")
    )
    domains = {
        "contract_completeness": domain(
            "contract_completeness", ("contract_completeness",)
        ),
        "operational_maturity": domain(
            "operational_maturity", ("operational_maturity",)
        ),
        "performance_regression": domain(
            "performance_regression", ("performance_regression",)
        ),
        "comparative_evaluation": domain(
            "comparative_evaluation", ("comparative_evaluation", *host_checks)
        ),
        "release_certification": domain(
            "release_certification",
            (
                *host_checks,
                *native_checks,
                "clean_worktree",
                "install_provenance",
                "upstream_remote_review",
            ),
        ),
    }
    return {
        "schema": SCHEMA,
        "metric_policy": "independent_domains_no_composite_score",
        "release_level_evaluated": release_level,
        "domains": domains,
        "release_evidence": {
            "schema": evidence["schema"],
            "source_commit": evidence["source_commit"],
            "verified_hosts": evidence["verified_hosts"],
            "verified_native": evidence["verified_native"],
            "unverified": evidence["unverified"],
            "ok": evidence["ok"],
        },
        "ok": all(value["status"] == "passed" for value in domains.values()),
    }
