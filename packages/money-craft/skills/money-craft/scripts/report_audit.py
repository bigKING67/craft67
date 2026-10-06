#!/usr/bin/env python3
"""Audit Money Craft Markdown metadata, sections, sources, and placeholders."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

THSCODE_RE = re.compile(r"^\d{6}\.(?:SH|SZ|BJ)$")
SECURITY_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,15}:[A-Z0-9][A-Z0-9._-]{0,31}$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
THSCODE_MARKETS = {"SH": "CN-SH", "SZ": "CN-SZ", "BJ": "CN-BJ"}
SOURCE_RE = re.compile(r"\[(S\d{2,4})\]")
SOURCE_DEFINITION_RE = re.compile(r"^[ \t]*-[ \t]+\[(S\d{2,4})\][ \t]*(.*?)[ \t]*$", re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}")
REQUIRED_HEADINGS = {
    "结论",
    "事实与证据",
    "估值与假设",
    "风险与反方证据",
    "证伪条件",
    "来源索引",
}
VALID_SCHEMAS = {"money-craft.report.v1", "money-craft.thesis.v1"}
VALID_WORKFLOWS = {"screen", "research", "earnings", "thesis", "industry", "theme", "portfolio"}
FINANCIAL_TERMS = re.compile(
    r"收入|利润|现金流|资产|负债|股本|ROE|毛利率|净利率|PE|PB|PS|PCF|估值|市值|股价",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+−–－＋]?\d[\d,.]*(?:%|倍|亿元|元|万亿|x)?")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, text, ["missing YAML-style frontmatter"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text, ["unterminated frontmatter"]
    values: dict[str, str] = {}
    for line_number, line in enumerate(text[4:end].splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"frontmatter line {line_number} is not key: value")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or key in values:
            errors.append(f"invalid or duplicate frontmatter key at line {line_number}")
            continue
        values[key] = value
    return values, text[end + 5 :], errors


def valid_iso_date(value: str) -> bool:
    try:
        return dt.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def valid_iso_datetime(value: str) -> bool:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return "T" in value and parsed.tzinfo is not None


def security_id_from_metadata(metadata: dict[str, str]) -> str:
    security_id = metadata.get("security_id", "").strip().upper()
    thscode = metadata.get("thscode", "").strip().upper()
    if security_id:
        if not SECURITY_ID_RE.fullmatch(security_id):
            raise ValueError("security_id must use Money Craft MARKET:SYMBOL syntax")
    elif thscode:
        if not THSCODE_RE.fullmatch(thscode):
            raise ValueError("legacy thscode must be a six-digit Fuyao A-share code")
        security_id = f"{THSCODE_MARKETS[thscode[-2:]]}:{thscode[:6]}"
    else:
        raise ValueError("security_id is required; legacy A-share documents may provide thscode")
    if thscode:
        if not THSCODE_RE.fullmatch(thscode):
            raise ValueError("legacy thscode must be a six-digit Fuyao A-share code")
        expected = f"{THSCODE_MARKETS[thscode[-2:]]}:{thscode[:6]}"
        if security_id != expected:
            raise ValueError("security_id and thscode identify different securities")
    return security_id


def section_pattern(heading: str) -> re.Pattern[str]:
    return re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )


def extract_section(body: str, heading: str) -> str:
    match = section_pattern(heading).search(body)
    return match.group("body") if match else ""


def audit_text(text: str) -> dict[str, Any]:
    metadata, body, errors = parse_frontmatter(text)
    warnings: list[str] = []
    required_metadata = {
        "schema",
        "workflow",
        "security",
        "as_of",
        "data_cutoff",
        "base_currency",
        "provider_status",
    }
    for key in sorted(required_metadata - metadata.keys()):
        errors.append(f"missing frontmatter field: {key}")
    if metadata.get("schema") not in VALID_SCHEMAS:
        errors.append("schema must be money-craft.report.v1 or money-craft.thesis.v1")
    if metadata.get("workflow") not in VALID_WORKFLOWS:
        errors.append("workflow must be screen, research, earnings, thesis, industry, theme, or portfolio")
    try:
        security_id_from_metadata(metadata)
    except ValueError as exc:
        errors.append(str(exc))
    if not valid_iso_date(metadata.get("as_of", "")):
        errors.append("as_of must be YYYY-MM-DD")
    if not valid_iso_datetime(metadata.get("data_cutoff", "")):
        errors.append("data_cutoff must be an ISO-8601 timestamp")
    if not CURRENCY_RE.fullmatch(metadata.get("base_currency", "")):
        errors.append("base_currency must be a three-letter uppercase currency code")
    heading_list = re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
    headings = set(heading_list)
    contract_headings = REQUIRED_HEADINGS | ({"核心假设", "更新记录"} if metadata.get("schema") == "money-craft.thesis.v1" else set())
    for heading in sorted(contract_headings):
        if heading_list.count(heading) > 1:
            errors.append(f"duplicate contract section: {heading}")
    for heading in sorted(REQUIRED_HEADINGS - headings):
        errors.append(f"missing required section: {heading}")
    placeholders = PLACEHOLDER_RE.findall(text)
    if placeholders:
        errors.append(f"unresolved template placeholders: {len(placeholders)}")

    sources_section = extract_section(body, "来源索引")
    definition_pairs = SOURCE_DEFINITION_RE.findall(sources_section)
    definitions = {source_id: target.strip() for source_id, target in definition_pairs}
    if len(definitions) != len(definition_pairs):
        errors.append("duplicate source definitions are not allowed")
    if len(definitions) < 2:
        errors.append("at least two source definitions are required")
    for source_id, target in definitions.items():
        if not target or PLACEHOLDER_RE.search(target):
            errors.append(f"{source_id}: source target is missing")
        elif not (re.search(r"https?://", target) or "`" in target or "/" in target):
            warnings.append(f"{source_id}: source has no URL or local path")

    body_without_index = section_pattern("来源索引").sub("", body)
    citations = set(SOURCE_RE.findall(body_without_index))
    for source_id in sorted(citations - definitions.keys()):
        errors.append(f"unresolved source citation: {source_id}")
    for source_id in sorted(definitions.keys() - citations):
        warnings.append(f"unused source definition: {source_id}")

    facts = extract_section(body, "事实与证据")
    fact_lines = [line.strip() for line in facts.splitlines() if line.strip().startswith("-")]
    if not fact_lines:
        errors.append("事实与证据 must contain source-bound bullets")
    for line in fact_lines:
        if (NUMBER_RE.search(line) or FINANCIAL_TERMS.search(line)) and not SOURCE_RE.search(line):
            errors.append(f"source missing from factual bullet: {line[:80]}")

    for line_number, line in enumerate(body_without_index.splitlines(), start=1):
        if NUMBER_RE.search(line) and FINANCIAL_TERMS.search(line):
            if not SOURCE_RE.search(line) and "money-craft-calc" not in line:
                warnings.append(f"line {line_number}: financial statement may need a source or calculation receipt")

    return {
        "schema": "money-craft.report-audit.v1",
        "valid": not errors,
        "metadata": metadata,
        "source_count": len(definitions),
        "citation_count": len(citations),
        "warnings": warnings,
        "errors": errors,
    }


def audit_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "schema": "money-craft.report-audit.v1",
            "valid": False,
            "metadata": {},
            "source_count": 0,
            "citation_count": 0,
            "warnings": [],
            "errors": [f"report does not exist: {path}"],
        }
    return audit_text(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit_file(Path(args.report).expanduser().resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
