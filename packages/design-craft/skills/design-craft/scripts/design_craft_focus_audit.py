#!/usr/bin/env python3
"""Scan frontend files for static focus and interactive-state risks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SKIP_DIRS = {".git", ".next", ".turbo", "build", "coverage", "dist", "node_modules", "out", "upstreams"}
TEXT_SUFFIXES = {".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".mdx"}
SEVERITY_ORDER = {"info": 1, "medium": 2, "high": 3}


def iter_files(root: Path):
    if root.is_file():
        if root.suffix.lower() in TEXT_SUFFIXES:
            yield root
        return
    for candidate in root.rglob("*"):
        if not candidate.is_file() or candidate.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            parts = candidate.relative_to(root).parts
        except ValueError:
            parts = candidate.parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        if candidate.stat().st_size <= 400_000:
            yield candidate


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def add(findings: list[dict], root: Path, path: Path, line: int, rule: str, severity: str, message: str, text: str) -> None:
    findings.append(
        {
            "source": "design-craft.focus-audit",
            "rule": rule,
            "severity": severity,
            "path": rel(path, root),
            "line": line,
            "message": message,
            "snippet": text.strip()[:180],
        }
    )


def scan_file(root: Path, path: Path) -> list[dict]:
    findings: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    lines = text.splitlines()

    for index, line_text in enumerate(lines, start=1):
        line_lower = line_text.lower()
        if re.search(r"\boutline\s*:\s*[\"']?(?:0|none)\b", line_lower):
            surrounding = "\n".join(lines[max(0, index - 4) : min(len(lines), index + 3)]).lower()
            if not re.search(r"focus-visible|box-shadow|outline-offset|ring-|focus:", surrounding):
                add(findings, root, path, index, "outline-none-without-replacement", "high", "outline is removed without an obvious nearby visible focus replacement.", line_text)
            else:
                add(findings, root, path, index, "outline-none-review", "info", "outline is removed; verify replacement focus style is visible in all themes.", line_text)

        if re.search(r"\bdisabled\b", line_lower) and "opacity" in line_lower and not re.search(r"cursor|aria-disabled|not-allowed|data-disabled", line_lower):
            add(findings, root, path, index, "disabled-opacity-only", "medium", "Disabled styling appears opacity-only; verify semantics and non-color state treatment.", line_text)

    has_interactive = bool(
        re.search(r"<(?:button|a|input|select|textarea)\b", lower)
        or re.search(r"\brole=[\"'](?:button|link|tab|menuitem|switch|checkbox)[\"']", lower)
        or re.search(r"\b(onclick|onkeydown|onpointerdown|onmousedown)=", lower)
        or re.search(r"\b(?:button|input|select|textarea|a):", lower)
    )
    if has_interactive and "focus-visible" not in lower and ":focus" not in lower and "focus:" not in lower and "focusring" not in lower:
        add(findings, root, path, 1, "interactive-without-focus-style", "medium", "Interactive markup/selectors detected without an obvious focus-visible or focus style in this file.", lines[0] if lines else "")

    if "hover" in lower and "focus" not in lower:
        add(findings, root, path, 1, "hover-without-focus-peer", "info", "Hover styling appears without a focus peer; verify keyboard users receive equivalent feedback.", lines[0] if lines else "")

    return findings


def should_fail(findings: list[dict], threshold: str) -> bool:
    if threshold == "never":
        return False
    want = SEVERITY_ORDER[threshold]
    return any(SEVERITY_ORDER.get(item["severity"], 0) >= want for item in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan frontend files for focus/state risks.")
    parser.add_argument("--target", default=".", help="File or directory to scan.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--fail-on", choices=["high", "medium", "info", "never"], default="never")
    args = parser.parse_args()

    root = Path(args.target).expanduser().resolve()
    scan_root = root if root.is_dir() else root.parent
    findings: list[dict] = []
    for path in iter_files(root):
        findings.extend(scan_file(scan_root, path))

    payload = {"target": str(root), "finding_count": len(findings), "findings": findings}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"design-craft focus audit target: {root}")
        print(f"findings: {len(findings)}")
        for item in findings[:80]:
            print(f"- {item['severity']} {item['rule']} {item['path']}:{item['line']} {item['message']}")
        if len(findings) > 80:
            print(f"... {len(findings) - 80} more findings omitted")

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())
