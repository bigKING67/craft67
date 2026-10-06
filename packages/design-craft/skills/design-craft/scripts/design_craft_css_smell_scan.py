#!/usr/bin/env python3
"""Scan frontend files for static CSS/UI implementation smell signals."""

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
            "source": "design-craft.css-smell",
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
    lines = text.splitlines()

    hex_re = re.compile(r"(?<![A-Za-z0-9_-])#[0-9A-Fa-f]{3,8}\b")
    px_re = re.compile(r"(?<![\w-])(?:margin|padding|gap|top|right|bottom|left|width|height|min-width|max-width|min-height|max-height|border-radius)\s*:\s*[^;\n]*\b(?:[3579]|1[13579]|2[13579]|3[13579])px")
    fixed_width_re = re.compile(r"\b(?:width|min-width|max-width)\s*:\s*(?:[4-9]\d{2,}|1\d{3,})px")

    file_hex_count = len(hex_re.findall(text))
    file_shadow_count = len(re.findall(r"\bbox-shadow\s*:", text))

    for index, line_text in enumerate(lines, start=1):
        lower = line_text.lower()
        if re.search(r"\btransition\s*:\s*all\b|\btransition-all\b", lower):
            add(findings, root, path, index, "transition-all", "medium", "Broad transition-all detected; prefer explicit transform/opacity/color properties.", line_text)
        if re.search(r"\bposition\s*:\s*(absolute|fixed)\b", lower) and not re.search(r"popover|modal|toast|tooltip|overlay|dropdown|sr-only|visually-hidden", lower):
            add(findings, root, path, index, "absolute-normal-layout", "info", "Absolute/fixed positioning may be normal layout; verify it is not a fragile placement hack.", line_text)
        if fixed_width_re.search(lower):
            add(findings, root, path, index, "fixed-responsive-width", "medium", "Large fixed width detected; verify responsive behavior and overflow.", line_text)
        if px_re.search(lower):
            add(findings, root, path, index, "magic-spacing", "info", "Odd pixel value in spacing or sizing; prefer the project spacing scale unless justified.", line_text)
        if re.search(r"\bbox-shadow\s*:", lower):
            add(findings, root, path, index, "shadow-review", "info", "Box shadow detected; verify elevation carries structure rather than decoration.", line_text)

    if file_hex_count >= 8:
        add(findings, root, path, 1, "hardcoded-color-cluster", "medium", f"{file_hex_count} hardcoded hex colors detected; prefer semantic tokens where available.", lines[0] if lines else "")
    elif file_hex_count > 0:
        add(findings, root, path, 1, "hardcoded-color", "info", f"{file_hex_count} hardcoded hex color(s) detected; verify tokens are unavailable or intentionally evolved.", lines[0] if lines else "")

    if file_shadow_count >= 6:
        add(findings, root, path, 1, "shadow-overuse", "medium", f"{file_shadow_count} box-shadow declarations detected; verify surface hierarchy is not overdecorated.", lines[0] if lines else "")

    return findings


def should_fail(findings: list[dict], threshold: str) -> bool:
    if threshold == "never":
        return False
    want = SEVERITY_ORDER[threshold]
    return any(SEVERITY_ORDER.get(item["severity"], 0) >= want for item in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan CSS/UI files for design-craft smell signals.")
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
        print(f"design-craft css smell scan target: {root}")
        print(f"findings: {len(findings)}")
        for item in findings[:80]:
            print(f"- {item['severity']} {item['rule']} {item['path']}:{item['line']} {item['message']}")
        if len(findings) > 80:
            print(f"... {len(findings) - 80} more findings omitted")

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())
