#!/usr/bin/env python3
"""Scan frontend files for token bypass and one-off visual values."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SKIP_DIRS = {".git", ".next", ".turbo", "build", "coverage", "dist", "node_modules", "out", "upstreams"}
TEXT_SUFFIXES = {".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".mdx"}
SEVERITY_ORDER = {"info": 1, "medium": 2, "high": 3}
TOKEN_HINT_RE = re.compile(r"var\(|theme\(|token|--[a-z0-9-]+|className=|class=", re.I)


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
            "source": "design-craft.token-audit",
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
    lower = text.lower()
    has_token_hints = bool(TOKEN_HINT_RE.search(text))

    literal_color_lines = []
    literal_radius_lines = []
    literal_shadow_lines = []
    literal_spacing_lines = []

    for index, line_text in enumerate(lines, start=1):
        line_lower = line_text.lower()
        if re.search(r"(?<![A-Za-z0-9_-])#[0-9A-Fa-f]{3,8}\b|rgba?\(|hsla?\(|oklch\(", line_text):
            literal_color_lines.append((index, line_text))
        if re.search(r"\bborder-radius\s*:\s*\d+px", line_lower):
            literal_radius_lines.append((index, line_text))
        if re.search(r"\bbox-shadow\s*:\s*", line_lower):
            literal_shadow_lines.append((index, line_text))
        if re.search(r"\b(?:margin|padding|gap)\s*:\s*[^;\n]*\d+px", line_lower):
            literal_spacing_lines.append((index, line_text))

    if has_token_hints:
        for index, line_text in literal_color_lines[:8]:
            add(findings, root, path, index, "literal-color-with-token-system", "medium", "Literal color appears in a file that also uses token/class conventions; verify token bypass is intentional.", line_text)
        for index, line_text in literal_radius_lines[:8]:
            add(findings, root, path, index, "literal-radius-with-token-system", "info", "Literal radius appears near token/class conventions; verify it belongs to the system scale.", line_text)
        for index, line_text in literal_shadow_lines[:8]:
            add(findings, root, path, index, "literal-shadow-with-token-system", "info", "Literal shadow appears near token/class conventions; verify it is a reusable elevation token.", line_text)
        for index, line_text in literal_spacing_lines[:8]:
            add(findings, root, path, index, "literal-spacing-with-token-system", "info", "Literal spacing appears near token/class conventions; verify it follows the project scale.", line_text)
    elif len(literal_color_lines) >= 6:
        add(findings, root, path, 1, "unstructured-color-scale", "medium", "Multiple literal colors and no token hints detected; consider defining semantic color tokens.", lines[0] if lines else "")

    unique_hex = sorted(set(re.findall(r"(?<![A-Za-z0-9_-])#[0-9A-Fa-f]{6}\b", text)))
    if len(unique_hex) >= 10:
        add(findings, root, path, 1, "many-one-off-colors", "medium", f"{len(unique_hex)} unique hex colors detected; verify this is not accidental palette drift.", lines[0] if lines else "")

    if re.search(r"\bprimary\b", lower) and re.search(r"\bsecondary\b", lower) and len(literal_color_lines) >= 4:
        add(findings, root, path, 1, "semantic-names-plus-literals", "medium", "Semantic visual names and literal colors coexist; consolidate around role tokens.", lines[0] if lines else "")

    return findings


def should_fail(findings: list[dict], threshold: str) -> bool:
    if threshold == "never":
        return False
    want = SEVERITY_ORDER[threshold]
    return any(SEVERITY_ORDER.get(item["severity"], 0) >= want for item in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan frontend files for token bypass signals.")
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
        print(f"design-craft token audit target: {root}")
        print(f"findings: {len(findings)}")
        for item in findings[:80]:
            print(f"- {item['severity']} {item['rule']} {item['path']}:{item['line']} {item['message']}")
        if len(findings) > 80:
            print(f"... {len(findings) - 80} more findings omitted")

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())
