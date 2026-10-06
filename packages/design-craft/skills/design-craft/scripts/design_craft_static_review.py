#!/usr/bin/env python3
"""Aggregate design-craft static scanner signals into one review packet."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA = "design-craft.static-review.v1"
SEVERITY_ORDER = {"info": 1, "medium": 2, "high": 3}
SCANNERS = (
    ("css_smells", "design_craft_css_smell_scan.py", "CSS smell signals"),
    ("focus_risks", "design_craft_focus_audit.py", "Focus/state risks"),
    ("token_bypasses", "design_craft_token_audit.py", "Token bypass signals"),
)


def run_scanner(script_dir: Path, script_name: str, target: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(script_dir / script_name), "--target", str(target), "--json"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{script_name} failed with exit {result.returncode}: {result.stderr.strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{script_name} emitted invalid JSON: {exc}") from exc


def normalize_findings(scanner_key: str, scanner_label: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for item in payload.get("findings", []):
        if not isinstance(item, dict):
            continue
        normalized = dict(item)
        normalized["scanner"] = scanner_key
        normalized["scanner_label"] = scanner_label
        normalized.setdefault("severity", "info")
        normalized.setdefault("rule", "unknown")
        normalized.setdefault("path", "")
        normalized.setdefault("line", 0)
        normalized.setdefault("message", "")
        findings.append(normalized)
    return findings


def build_interpretation(summary: dict[str, int], findings: list[dict[str, Any]]) -> list[str]:
    rules = Counter(str(item.get("rule", "")) for item in findings)
    scanners = Counter(str(item.get("scanner", "")) for item in findings)
    interpretation: list[str] = []

    if summary["high"] > 0:
        interpretation.append("High-severity interaction or focus risk needs manual review before design sign-off.")
    if scanners["token_bypasses"] > 0:
        interpretation.append("Potential token drift: verify literal colors, spacing, radius, and shadows against the project design system.")
    if scanners["focus_risks"] > 0:
        interpretation.append("Potential focus/state risk: verify keyboard-visible focus, disabled semantics, and hover/focus parity in browser.")
    if scanners["css_smells"] > 0:
        interpretation.append("Potential surface composition risk: review fixed widths, transition-all, magic spacing, shadows, and hardcoded color clusters.")
    if rules["shadow-overuse"] or rules["shadow-review"]:
        interpretation.append("Surface overdecoration risk: confirm elevation communicates hierarchy rather than decorative card soup.")
    if rules["fixed-responsive-width"]:
        interpretation.append("Responsive risk: fixed widths require viewport evidence, not static approval.")
    if not interpretation:
        interpretation.append("No static scanner findings were detected; visual quality still requires product-context and browser evidence.")
    return interpretation


def aggregate(target: Path) -> dict[str, Any]:
    script_dir = Path(__file__).resolve().parent
    all_findings: list[dict[str, Any]] = []
    scanner_counts: dict[str, int] = {}

    for scanner_key, script_name, scanner_label in SCANNERS:
        payload = run_scanner(script_dir, script_name, target)
        findings = normalize_findings(scanner_key, scanner_label, payload)
        scanner_counts[scanner_key] = len(findings)
        all_findings.extend(findings)

    severity_counts = Counter(str(item.get("severity", "info")) for item in all_findings)
    summary = {
        "total_findings": len(all_findings),
        "css_smells": scanner_counts.get("css_smells", 0),
        "focus_risks": scanner_counts.get("focus_risks", 0),
        "token_bypasses": scanner_counts.get("token_bypasses", 0),
        "high": severity_counts.get("high", 0),
        "medium": severity_counts.get("medium", 0),
        "info": severity_counts.get("info", 0),
    }

    top_findings = sorted(
        all_findings,
        key=lambda item: (
            -SEVERITY_ORDER.get(str(item.get("severity", "info")), 0),
            str(item.get("path", "")),
            int(item.get("line", 0) or 0),
            str(item.get("rule", "")),
        ),
    )[:20]

    return {
        "schema": SCHEMA,
        "target": str(target),
        "summary": summary,
        "top_findings": top_findings,
        "design_interpretation": build_interpretation(summary, all_findings),
    }


def should_fail(summary: dict[str, int], threshold: str) -> bool:
    if threshold == "never":
        return False
    want = SEVERITY_ORDER[threshold]
    return any(
        SEVERITY_ORDER[severity] >= want and summary.get(severity, 0) > 0
        for severity in ("high", "medium", "info")
    )


def print_text(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    print(f"design-craft static review target: {payload['target']}")
    print(
        "findings: "
        f"{summary['total_findings']} total, "
        f"{summary['high']} high, "
        f"{summary['medium']} medium, "
        f"{summary['info']} info"
    )
    print(
        "scanners: "
        f"{summary['css_smells']} css, "
        f"{summary['focus_risks']} focus, "
        f"{summary['token_bypasses']} token"
    )
    print("interpretation:")
    for item in payload["design_interpretation"]:
        print(f"- {item}")
    print("top findings:")
    for item in payload["top_findings"]:
        line = item.get("line", 0)
        path = item.get("path", "")
        print(
            f"- {item.get('severity')} {item.get('scanner')}:{item.get('rule')} "
            f"{path}:{line} {item.get('message')}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate design-craft static scanner signals.")
    parser.add_argument("--target", default=".", help="File or directory to scan.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--fail-on", choices=["high", "medium", "info", "never"], default="never")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    payload = aggregate(target)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(payload)

    return 1 if should_fail(payload["summary"], args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
