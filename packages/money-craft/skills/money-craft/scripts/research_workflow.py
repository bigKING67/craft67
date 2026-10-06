#!/usr/bin/env python3
"""Deterministic company-research planning and thesis revision contracts."""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import financial_rigor
import report_audit

THSCODE_RE = re.compile(r"^\d{6}\.(?:SH|SZ|BJ)$")
SECURITY_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,15}:[A-Z0-9][A-Z0-9._-]{0,31}$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
THSCODE_MARKETS = {"SH": "CN-SH", "SZ": "CN-SZ", "BJ": "CN-BJ"}
MARKET_EXCHANGES = {"CN-SH": "SSE", "CN-SZ": "SZSE", "CN-BJ": "BSE"}
REPORT_RE = re.compile(r"^((?:19|20)\d{2})-([1-4])$")
HYPOTHESIS_ID_RE = re.compile(r"^H\d{2,4}$")
RED_LINE_ID_RE = re.compile(r"^R\d{2,4}$")
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
HYPOTHESIS_COLUMNS = ("ID", "假设", "指标与阈值", "验证来源", "频率", "状态")
RED_LINE_COLUMNS = ("ID", "条件", "严重度", "当前状态", "证据")
UPDATE_COLUMNS = ("日期", "假设变化", "估值变化", "结论变化", "来源")
HYPOTHESIS_STATES = {"SUPPORTED", "WEAKENED", "DAMAGED", "BROKEN", "UNVERIFIED"}
RED_LINE_STATES = {"CLEAR", "WATCH", "TRIGGERED", "UNVERIFIED"}
RED_LINE_SEVERITIES = {"fatal", "material"}
SHANGHAI = ZoneInfo("Asia/Shanghai")


class WorkflowError(RuntimeError):
    def __init__(self, kind: str, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.kind = kind
        self.exit_code = exit_code


def parse_date(value: str, label: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise WorkflowError("invalid_date", f"{label} must be YYYY-MM-DD") from exc


def parse_report_period(value: str) -> tuple[int, int]:
    match = REPORT_RE.fullmatch(value)
    if not match:
        raise WorkflowError("invalid_report_period", "latest report must match YYYY-1 through YYYY-4")
    return int(match.group(1)), int(match.group(2))


def report_period_end(year: int, quarter: int) -> dt.date:
    return {
        1: dt.date(year, 3, 31),
        2: dt.date(year, 6, 30),
        3: dt.date(year, 9, 30),
        4: dt.date(year, 12, 31),
    }[quarter]


def shift_years(value: dt.date, years: int) -> dt.date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def security_id_from_thscode(thscode: str) -> str:
    code = thscode.strip().upper()
    if not THSCODE_RE.fullmatch(code):
        raise WorkflowError("invalid_identity", "thscode must be a complete Fuyao A-share code")
    return f"{THSCODE_MARKETS[code[-2:]]}:{code[:6]}"


def thscode_from_security_id(security_id: str) -> str | None:
    normalized = security_id.strip().upper()
    if not SECURITY_ID_RE.fullmatch(normalized):
        raise WorkflowError(
            "invalid_identity",
            "security_id must use Money Craft MARKET:SYMBOL syntax, for example HK:00700 or US-NASDAQ:NVDA",
        )
    market, ticker = normalized.split(":", 1)
    suffixes = {value: key for key, value in THSCODE_MARKETS.items()}
    suffix = suffixes.get(market)
    if suffix is None:
        return None
    if not re.fullmatch(r"\d{6}", ticker):
        raise WorkflowError("invalid_identity", f"{market} security_id must use a six-digit symbol")
    return f"{ticker}.{suffix}"


def yfinance_symbol_from_security_id(security_id: str) -> str | None:
    normalized = security_id.strip().upper()
    if not SECURITY_ID_RE.fullmatch(normalized):
        raise WorkflowError(
            "invalid_identity",
            "security_id must use Money Craft MARKET:SYMBOL syntax, for example HK:00700 or US-NASDAQ:NVDA",
        )
    market, ticker = normalized.split(":", 1)
    if market == "HK":
        if not ticker.isdigit() or len(ticker) > 5:
            raise WorkflowError("invalid_identity", "HK security_id must use a numeric symbol of at most five digits")
        return f"{ticker.lstrip('0').zfill(4)}.HK"
    if market == "US" or market.startswith("US-"):
        return ticker.replace(".", "-")
    return None


def normalize_security_identity(
    *,
    security: str,
    security_id: str | None,
    thscode: str | None,
    base_currency: str | None,
) -> dict[str, Any]:
    name = security.strip()
    if not name or len(name) > 128:
        raise WorkflowError("invalid_identity", "security must be a non-empty name of at most 128 characters")

    normalized_thscode = thscode.strip().upper() if isinstance(thscode, str) and thscode.strip() else None
    if normalized_thscode is not None and not THSCODE_RE.fullmatch(normalized_thscode):
        raise WorkflowError("invalid_identity", "thscode must be a complete Fuyao A-share code")
    normalized_security_id = (
        security_id.strip().upper() if isinstance(security_id, str) and security_id.strip() else None
    )
    if normalized_security_id is None and normalized_thscode is None:
        raise WorkflowError("invalid_identity", "security_id is required unless legacy --thscode is provided")
    if normalized_security_id is None:
        normalized_security_id = security_id_from_thscode(str(normalized_thscode))
    if not SECURITY_ID_RE.fullmatch(normalized_security_id):
        raise WorkflowError(
            "invalid_identity",
            "security_id must use Money Craft MARKET:SYMBOL syntax, for example HK:00700 or US-NASDAQ:NVDA",
        )
    derived_thscode = thscode_from_security_id(normalized_security_id)
    if normalized_thscode is not None and derived_thscode != normalized_thscode:
        raise WorkflowError("identity_mismatch", "security_id and thscode identify different securities")
    if normalized_thscode is None:
        normalized_thscode = derived_thscode

    market, ticker = normalized_security_id.split(":", 1)
    currency = base_currency.strip().upper() if isinstance(base_currency, str) else ""
    if not currency:
        if normalized_thscode is None:
            raise WorkflowError("invalid_currency", "base_currency is required outside the Fuyao A-share adapter")
        currency = "CNY"
    if not CURRENCY_RE.fullmatch(currency):
        raise WorkflowError("invalid_currency", "base_currency must be a three-letter uppercase currency code")

    identity: dict[str, Any] = {
        "security": name,
        "security_id": normalized_security_id,
        "market": market,
        "ticker": ticker,
        "instrument_type": "listed-equity",
        "base_currency": currency,
        "provider_identifiers": {},
    }
    if normalized_thscode is not None:
        identity.update(
            {
                "thscode": normalized_thscode,
                "exchange": MARKET_EXCHANGES[market],
                "share_class": "A-share",
                "provider_identifiers": {"fuyao": normalized_thscode},
            }
        )
    else:
        yfinance_symbol = yfinance_symbol_from_security_id(normalized_security_id)
        if yfinance_symbol is not None:
            identity["provider_identifiers"] = {"yfinance": yfinance_symbol}
            if market == "HK":
                identity.update({"exchange": "HKEX", "share_class": "ordinary-share"})
            else:
                exchange = market.removeprefix("US-") if market.startswith("US-") else "US"
                identity.update({"exchange": exchange, "share_class": "common-stock"})
    return identity


def add_evidence_requirements(plan: dict[str, Any], declarations: list[dict[str, Any]] | None) -> None:
    """Extend a newly constructed plan, never an initialized workspace."""
    if declarations is None:
        return
    if not isinstance(declarations, list) or len(declarations) > 16:
        raise WorkflowError("invalid_additional_evidence", "additional evidence must be an array of at most 16 declarations")
    seen = {item["id"] for key in ("provider_operations", "official_evidence_requirements", "public_evidence_requirements")
            for item in plan[key]}
    staged: list[tuple[str, dict[str, Any]]] = []
    for item in declarations:
        if not isinstance(item, dict) or set(item) - {"id", "kind", "role", "period"}:
            raise WorkflowError("invalid_additional_evidence", "source declarations accept only id, kind, role and optional period")
        source_id, kind, role = item.get("id"), item.get("kind"), item.get("role")
        if not isinstance(source_id, str) or not re.fullmatch(r"S[0-9]{2,4}", source_id) or source_id in seen:
            raise WorkflowError("invalid_additional_evidence", "additional source IDs must be unique Sxx identifiers and not collide with the plan")
        if kind not in ("official-document", "official-index", "official-material", "public-material"):
            raise WorkflowError("invalid_additional_evidence", "unsupported additional source kind")
        if not isinstance(role, str) or not 1 <= len(role.strip()) <= 256:
            raise WorkflowError("invalid_additional_evidence", "additional source role must contain 1..256 characters")
        period = item.get("period")
        if period is not None and (not isinstance(period, str) or not REPORT_RE.fullmatch(period)):
            raise WorkflowError("invalid_additional_evidence", "additional source period must be YYYY-1..4 or null")
        seen.add(source_id)
        collection = "public_evidence_requirements" if kind == "public-material" else "official_evidence_requirements"
        staged.append((collection, {"id": source_id, "kind": kind, "role": role.strip(), "period": period, "required": False}))
    for collection, requirement in staged:
        plan[collection].append(requirement)


def company_research_plan(
    *,
    security: str,
    as_of: str,
    latest_report: str,
    provider: dict[str, Any],
    security_id: str | None = None,
    thscode: str | None = None,
    base_currency: str | None = None,
    latest_report_end: str | None = None,
    latest_annual_report: str | None = None,
    additional_evidence: list[dict[str, Any]] | None = None,
    today: dt.date | None = None,
) -> dict[str, Any]:
    identity = normalize_security_identity(
        security=security,
        security_id=security_id,
        thscode=thscode,
        base_currency=base_currency,
    )
    code = identity.get("thscode")
    research_date = parse_date(as_of, "as_of")
    current_date = today or dt.datetime.now(SHANGHAI).date()
    if research_date > current_date:
        raise WorkflowError("future_as_of", "as_of cannot be later than the current Asia/Shanghai date")
    report_year, report_quarter = parse_report_period(latest_report)
    if latest_report_end is None:
        if code is None:
            raise WorkflowError(
                "missing_report_end",
                "latest_report_end is required outside A-share calendar-quarter reporting",
            )
        effective_report_end = report_period_end(report_year, report_quarter)
    else:
        effective_report_end = parse_date(latest_report_end, "latest_report_end")
    if code is not None and effective_report_end != report_period_end(report_year, report_quarter):
        raise WorkflowError("report_end_mismatch", "A-share report end must match its calendar-quarter period")
    if effective_report_end > research_date:
        raise WorkflowError("future_report_period", "latest report period ends after as_of")
    if latest_annual_report is None:
        if code is None and report_quarter != 4:
            raise WorkflowError(
                "missing_annual_period",
                "latest_annual_report is required for non-A-share interim research",
            )
        annual_report = latest_report if report_quarter == 4 else f"{report_year - 1}-4"
    else:
        parse_report_period(latest_annual_report)
        if not latest_annual_report.endswith("-4"):
            raise WorkflowError("invalid_report_period", "latest_annual_report must identify an annual YYYY-4 period")
        annual_report = latest_annual_report
    if parse_report_period(annual_report) > (report_year, report_quarter):
        raise WorkflowError("invalid_annual_period", "latest annual report cannot be later than latest report period")
    history_start = shift_years(research_date, -5).isoformat()
    month_start = research_date.replace(day=1).isoformat()
    comparison_period = f"{report_year - 1}-{report_quarter}"
    reconciliation_checks = ["balance-sheet-equation", "cash-balance-tie"]
    if report_quarter > 1:
        reconciliation_checks.append("quarter-from-ytd")

    provider = dict(provider)
    adapter = provider.get("adapter") or ("fuyao" if isinstance(code, str) else "yfinance")
    if adapter not in {"fuyao", "yfinance"}:
        raise WorkflowError("invalid_provider", "provider adapter must be fuyao or yfinance")
    provider_identifier = identity["provider_identifiers"].get(adapter)
    security_supported = isinstance(provider_identifier, str)
    provider.update(
        {
            "adapter": adapter,
            "adapter_scope": (
                "A-share structured data"
                if adapter == "fuyao"
                else "Hong Kong and U.S. secondary market data via Yahoo Finance"
            ),
            "security_supported": security_supported,
        }
    )
    mode = provider.get("mode")
    if mode not in {"auto", "required", "disabled"}:
        raise WorkflowError("invalid_provider_mode", "provider mode must be auto, required, or disabled")
    if mode == "required" and not security_supported:
        raise WorkflowError("provider_unsupported", f"{adapter} required mode does not support this security_id")
    provider_available = security_supported and mode != "disabled" and provider.get("configured") is True
    if provider_available:
        provider["availability"] = "available"
    elif mode == "disabled":
        provider["availability"] = "disabled"
    elif not security_supported:
        provider["availability"] = "unsupported-security"
    else:
        provider["availability"] = "not-configured"

    fuyao_operations = [
        {"id": "S01", "operation": "search", "arguments": {"query": code[:6], "limit": 3}},
        {"id": "S02", "operation": "snapshot", "arguments": {"thscodes": code}},
        {"id": "S03", "operation": "valuations", "arguments": {"thscodes": code}},
        {
            "id": "S04",
            "operation": "history",
            "arguments": {
                "thscode": code,
                "start": history_start,
                "end": as_of,
                "interval": "1d",
                "adjust": "forward",
            },
        },
        {
            "id": "S05",
            "operation": "financials",
            "arguments": {"thscode": code, "statement": "income", "period": "annual", "limit": 5},
        },
        {
            "id": "S06",
            "operation": "financials",
            "arguments": {"thscode": code, "statement": "balance", "period": "annual", "limit": 5},
        },
        {
            "id": "S07",
            "operation": "financials",
            "arguments": {"thscode": code, "statement": "cash-flow", "period": "annual", "limit": 5},
        },
        {"id": "S08", "operation": "indicators", "arguments": {"thscode": code, "report": annual_report}},
        {
            "id": "S09",
            "operation": "corporate-actions",
            "arguments": {"thscode": code, "start": history_start, "end": as_of},
        },
        {"id": "S10", "operation": "calendar", "arguments": {"start": month_start, "end": as_of}},
        {
            "id": "S14",
            "operation": "financials",
            "arguments": {"thscode": code, "statement": "income", "period": "quarterly", "limit": 8},
        },
        {
            "id": "S15",
            "operation": "financials",
            "arguments": {"thscode": code, "statement": "balance", "period": "quarterly", "limit": 8},
        },
        {
            "id": "S16",
            "operation": "financials",
            "arguments": {"thscode": code, "statement": "cash-flow", "period": "quarterly", "limit": 8},
        },
    ] if isinstance(code, str) else []
    if isinstance(code, str) and latest_report != annual_report:
        fuyao_operations.append(
            {"id": "S17", "operation": "indicators", "arguments": {"thscode": code, "report": latest_report}}
        )

    yfinance_operations = [
        {
            "id": "S01",
            "provider": "yfinance",
            "operation": "search",
            "arguments": {"query": provider_identifier, "limit": 5},
        },
        {
            "id": "S02",
            "provider": "yfinance",
            "operation": "snapshot",
            "arguments": {"symbol": provider_identifier},
        },
        {
            "id": "S03",
            "provider": "yfinance",
            "operation": "valuations",
            "arguments": {"symbol": provider_identifier},
        },
        {
            "id": "S04",
            "provider": "yfinance",
            "operation": "history",
            "arguments": {
                "symbol": provider_identifier,
                "start": history_start,
                "end": as_of,
                "interval": "1d",
                "adjust": "auto",
            },
        },
        {
            "id": "S05",
            "provider": "yfinance",
            "operation": "financials",
            "arguments": {"symbol": provider_identifier, "statement": "income", "period": "annual", "limit": 5},
        },
        {
            "id": "S06",
            "provider": "yfinance",
            "operation": "financials",
            "arguments": {"symbol": provider_identifier, "statement": "balance", "period": "annual", "limit": 5},
        },
        {
            "id": "S07",
            "provider": "yfinance",
            "operation": "financials",
            "arguments": {"symbol": provider_identifier, "statement": "cash-flow", "period": "annual", "limit": 5},
        },
        {
            "id": "S09",
            "provider": "yfinance",
            "operation": "corporate-actions",
            "arguments": {"symbol": provider_identifier, "start": history_start, "end": as_of},
        },
        {
            "id": "S14",
            "provider": "yfinance",
            "operation": "financials",
            "arguments": {"symbol": provider_identifier, "statement": "income", "period": "quarterly", "limit": 8},
        },
        {
            "id": "S15",
            "provider": "yfinance",
            "operation": "financials",
            "arguments": {"symbol": provider_identifier, "statement": "balance", "period": "quarterly", "limit": 8},
        },
        {
            "id": "S16",
            "provider": "yfinance",
            "operation": "financials",
            "arguments": {"symbol": provider_identifier, "statement": "cash-flow", "period": "quarterly", "limit": 8},
        },
    ]
    if provider_available:
        operations = fuyao_operations if adapter == "fuyao" else yfinance_operations
        for item in operations:
            item.setdefault("provider", adapter)
    else:
        operations = []

    plan = {
        "schema": "money-craft.company-research-plan.v1",
        "mode": "research",
        "identity": identity,
        "as_of": as_of,
        "latest_report_period": latest_report,
        "latest_report_end": effective_report_end.isoformat(),
        "latest_annual_period": annual_report,
        "provider": provider,
        "execution_boundary": {
            "plan_only": True,
            "network_used": False,
            "account_access": False,
            "automatic_trading": False,
        },
        "stages": [
            {"id": "identity", "gate": "exact security_id, name, market, and currency reconciliation"},
            {"id": "official-evidence", "gate": "latest and annual formal filings acquired"},
            {"id": "provider-cross-check", "gate": "bounded operations captured or gaps declared"},
            {"id": "research", "gate": "facts separated from inference and counterevidence retained"},
            {"id": "valuation-and-thesis", "gate": "three scenarios and testable assumptions"},
            {"id": "audit", "gate": "report, financial, and reconciliation audits valid"},
        ],
        "public_evidence_requirements": [
            {"id": "S31", "role": "public quotation snapshot", "required": False},
            {"id": "S32", "role": "public quotation cross-check snapshot", "required": False},
        ],
        "official_evidence_requirements": [
            {"id": "S11", "role": "latest-period formal filing", "period": latest_report, "required": True},
            {"id": "S12", "role": "latest audited annual report", "period": annual_report, "required": True},
            {
                "id": "S13",
                "role": "exchange disclosure or issuer investor-relations index",
                "period": None,
                "required": True,
            },
            {
                "id": "S21",
                "role": "historical audited annual report for comparable financial history",
                "period": None,
                "required": False,
                "trigger": "earlier annual financial statements needed for historical or normalized baseline",
            },
            {
                "id": "S22",
                "role": "additional historical audited annual report for comparative balances",
                "period": None,
                "required": False,
                "trigger": "additional earlier balances or accounting notes needed for multi-year analysis",
            },
            {
                "id": "S18",
                "role": "material transaction, subsidiary finance, equity incentive or capital-structure disclosure",
                "period": None,
                "required": False,
                "trigger": "decision-critical subsidiary, governance, dilution, or contingent-obligation fact",
            },
            {
                "id": "S19",
                "role": "official management Q&A or roadshow transcript",
                "period": None,
                "required": False,
                "trigger": "management explanation or an unanswered material question affects the thesis",
            },
            {
                "id": "S20",
                "role": "post-reporting-period material event disclosure",
                "period": None,
                "required": False,
                "trigger": (
                    "financing, listing, acquisition, disposal, repurchase, "
                    "or other material event after period end"
                ),
            },
        ],
        "material_disclosure_contract": {
            "policy": "conditional",
            "index_source_id": "S13",
            "routes": [
                {
                    "source_id": "S18",
                    "source_types": [
                        "material transaction",
                        "subsidiary capital increase",
                        "equity incentive",
                        "capital raising",
                        "related-party transaction",
                    ],
                },
                {
                    "source_id": "S19",
                    "source_types": ["earnings briefing", "roadshow transcript", "official management Q&A"],
                },
                {
                    "source_id": "S20",
                    "source_types": ["post-reporting-period material announcement"],
                },
            ],
            "completion_rule": (
                "Import each triggered optional source; resolve every route in the reconciliation artifact and report."
            ),
        },
        "reconciliation_contract": {
            "schema": "money-craft.financial-reconciliation.v1",
            "path": "financial-reconciliation.json",
            "audit_path": "financial-reconciliation-audit.json",
            "required": True,
            "required_checks": reconciliation_checks,
            "material_disclosure_source_ids": ["S18", "S19", "S20"],
            "period_basis": [
                {"role": "current", "period": latest_report},
                {"role": "comparison", "period": comparison_period},
            ],
        },
        "provider_operations": operations,
        "artifact_contract": {
            "report": {"path": "report.md", "schema": "money-craft.report.v1"},
            "thesis": {"path": "thesis.md", "schema": "money-craft.thesis.v1"},
            "financial_reconciliation": {
                "path": "financial-reconciliation.json",
                "schema": "money-craft.financial-reconciliation.v1",
                "audit_path": "financial-reconciliation-audit.json",
            },
            "evidence_manifest": {
                "path": "evidence-manifest.json",
                "schema": "money-craft.public-evidence-manifest.v1",
                "distribution": "metadata-only",
            },
            "audits": [
                "report-audit.json",
                "report-financial-audit.json",
                "thesis-audit.json",
                "thesis-financial-audit.json",
                "financial-reconciliation-audit.json",
            ],
        },
        "completion_gate": {
            "official_sources_required": True,
            "provider_is_primary_source": False,
            "report_audit_required": True,
            "financial_audit_required": True,
            "financial_reconciliation_required": True,
            "raw_provider_payloads_public": False,
        },
    }
    add_evidence_requirements(plan, additional_evidence)
    return plan


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_table_row(line: str) -> list[str]:
    value = line.strip()
    if not value.startswith("|") or not value.endswith("|"):
        return []
    cells = re.split(r"(?<!\\)\|", value[1:-1])
    return [cell.replace(r"\|", "|").strip() for cell in cells]


def parse_table(section: str, columns: tuple[str, ...], label: str) -> list[dict[str, str]]:
    lines = [line for line in section.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        raise WorkflowError("missing_table", f"{label} table is required")
    header = split_table_row(lines[0])
    separator = split_table_row(lines[1])
    if header != list(columns) or len(separator) != len(header) or not all(
        TABLE_SEPARATOR_RE.fullmatch(cell.replace(" ", "")) for cell in separator
    ):
        raise WorkflowError("invalid_table", f"{label} table columns are invalid")
    records: list[dict[str, str]] = []
    for line in lines[2:]:
        values = split_table_row(line)
        if len(values) != len(header):
            raise WorkflowError("invalid_table", f"{label} table row has the wrong number of columns")
        records.append(dict(zip(header, values)))
    if not records:
        raise WorkflowError("empty_table", f"{label} table must contain at least one row")
    return records


def validate_records(
    records: list[dict[str, str]],
    *,
    id_pattern: re.Pattern[str],
    state_column: str,
    states: set[str],
    label: str,
) -> None:
    seen: set[str] = set()
    for record in records:
        record_id = record["ID"]
        if not id_pattern.fullmatch(record_id) or record_id in seen:
            raise WorkflowError("invalid_table_id", f"{label} contains an invalid or duplicate ID: {record_id}")
        seen.add(record_id)
        if record[state_column] not in states:
            raise WorkflowError("invalid_status", f"{record_id} has unsupported status: {record[state_column]}")


def load_thesis(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise WorkflowError("missing_thesis", f"thesis does not exist: {path}")
    try:
        text = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise WorkflowError("invalid_thesis", f"cannot read thesis: {exc}") from exc
    report_result = report_audit.audit_text(text)
    if not report_result["valid"]:
        raise WorkflowError("report_audit_failed", "; ".join(report_result["errors"]))
    financial_result = financial_rigor.audit_text(text)
    if not financial_result["valid"]:
        raise WorkflowError("financial_audit_failed", "; ".join(financial_result["errors"]))
    metadata, body, frontmatter_errors = report_audit.parse_frontmatter(text)
    if frontmatter_errors or metadata.get("schema") != "money-craft.thesis.v1" or metadata.get("workflow") != "thesis":
        raise WorkflowError("invalid_thesis", "document must use money-craft.thesis.v1 with workflow thesis")
    try:
        canonical_security_id = report_audit.security_id_from_metadata(metadata)
    except ValueError as exc:
        raise WorkflowError("invalid_thesis", str(exc)) from exc
    metadata = {**metadata, "security_id": canonical_security_id}

    hypotheses = parse_table(
        report_audit.extract_section(body, "核心假设"), HYPOTHESIS_COLUMNS, "核心假设"
    )
    red_lines = parse_table(
        report_audit.extract_section(body, "证伪条件"), RED_LINE_COLUMNS, "证伪条件"
    )
    updates = parse_table(
        report_audit.extract_section(body, "更新记录"), UPDATE_COLUMNS, "更新记录"
    )
    validate_records(
        hypotheses,
        id_pattern=HYPOTHESIS_ID_RE,
        state_column="状态",
        states=HYPOTHESIS_STATES,
        label="核心假设",
    )
    validate_records(
        red_lines,
        id_pattern=RED_LINE_ID_RE,
        state_column="当前状态",
        states=RED_LINE_STATES,
        label="证伪条件",
    )
    for record in red_lines:
        if record["严重度"] not in RED_LINE_SEVERITIES:
            raise WorkflowError("invalid_severity", f"{record['ID']} has unsupported severity: {record['严重度']}")
    update_dates = [parse_date(record["日期"], "update date") for record in updates]
    if update_dates != sorted(update_dates):
        raise WorkflowError("invalid_update_history", "update history dates must be non-decreasing")
    if update_dates[-1] != parse_date(metadata["as_of"], "thesis as_of"):
        raise WorkflowError("update_date_mismatch", "latest update row date must equal thesis as_of")
    source_pairs = report_audit.SOURCE_DEFINITION_RE.findall(
        report_audit.extract_section(body, "来源索引")
    )
    sources = {source_id: target.strip() for source_id, target in source_pairs}
    return {
        "path": resolved,
        "filename": resolved.name,
        "sha256": sha256_text(text),
        "metadata": metadata,
        "body": body,
        "hypotheses": hypotheses,
        "red_lines": red_lines,
        "updates": updates,
        "sources": sources,
        "sections": {
            name: report_audit.extract_section(body, name).strip()
            for name in ("结论", "事实与证据", "估值与假设", "风险与反方证据")
        },
        "audits": {
            "report": {"valid": True, "warnings": report_result["warnings"]},
            "financial": {"valid": True, "check_count": len(financial_result["checks"])},
        },
    }


def prepare_thesis_update(previous: Path, *, as_of: str) -> dict[str, Any]:
    snapshot = load_thesis(previous)
    previous_date = parse_date(snapshot["metadata"]["as_of"], "previous as_of")
    next_date = parse_date(as_of, "as_of")
    if next_date < previous_date:
        raise WorkflowError("time_reversal", "new thesis as_of cannot be earlier than the previous version")
    return {
        "schema": "money-craft.thesis-update-plan.v1",
        "identity": {
            "security": snapshot["metadata"]["security"],
            "security_id": snapshot["metadata"]["security_id"],
            "base_currency": snapshot["metadata"]["base_currency"],
        },
        "previous": {
            "filename": snapshot["filename"],
            "sha256": snapshot["sha256"],
            "as_of": snapshot["metadata"]["as_of"],
            "data_cutoff": snapshot["metadata"]["data_cutoff"],
        },
        "target": {
            "as_of": as_of,
            "revision_kind": "same-date-revision" if next_date == previous_date else "periodic-update",
            "required_update_record_date": as_of,
        },
        "hypotheses": snapshot["hypotheses"],
        "red_lines": snapshot["red_lines"],
        "preserved_update_history": snapshot["updates"],
        "existing_source_ids": sorted(snapshot["sources"]),
        "required_actions": [
            "acquire new official evidence before changing factual claims",
            "evaluate every existing hypothesis as SUPPORTED, WEAKENED, DAMAGED, BROKEN, or UNVERIFIED",
            "evaluate every red line as CLEAR, WATCH, TRIGGERED, or UNVERIFIED",
            "preserve all prior update rows verbatim and append exactly one new row",
            "recalculate valuation receipts and run both audits",
        ],
        "completion_gate": {
            "identity_unchanged": True,
            "history_append_only": True,
            "report_audit_required": True,
            "financial_audit_required": True,
        },
        "previous_audits": snapshot["audits"],
    }


def record_diff(
    previous: list[dict[str, str]], current: list[dict[str, str]], *, state_column: str
) -> dict[str, Any]:
    old = {record["ID"]: record for record in previous}
    new = {record["ID"]: record for record in current}
    changed: list[dict[str, Any]] = []
    transitions: list[dict[str, str]] = []
    for record_id in sorted(old.keys() & new.keys()):
        fields = [key for key in old[record_id] if old[record_id][key] != new[record_id][key]]
        if fields:
            changed.append(
                {
                    "id": record_id,
                    "changed_fields": fields,
                    "previous": old[record_id],
                    "current": new[record_id],
                }
            )
        if old[record_id][state_column] != new[record_id][state_column]:
            transitions.append(
                {
                    "id": record_id,
                    "previous": old[record_id][state_column],
                    "current": new[record_id][state_column],
                }
            )
    return {
        "added": [new[record_id] for record_id in sorted(new.keys() - old.keys())],
        "removed": [old[record_id] for record_id in sorted(old.keys() - new.keys())],
        "changed": changed,
        "status_transitions": transitions,
    }


def thesis_diff(previous: Path, current: Path) -> dict[str, Any]:
    old = load_thesis(previous)
    new = load_thesis(current)
    identity_fields = ("security", "security_id", "base_currency")
    for field in identity_fields:
        if old["metadata"].get(field) != new["metadata"].get(field):
            raise WorkflowError("identity_mismatch", f"thesis identity changed: {field}")
    old_date = parse_date(old["metadata"]["as_of"], "previous as_of")
    new_date = parse_date(new["metadata"]["as_of"], "current as_of")
    if new_date < old_date:
        raise WorkflowError("time_reversal", "current thesis as_of is earlier than previous thesis")
    old_cutoff = dt.datetime.fromisoformat(old["metadata"]["data_cutoff"].replace("Z", "+00:00"))
    new_cutoff = dt.datetime.fromisoformat(new["metadata"]["data_cutoff"].replace("Z", "+00:00"))
    if new_cutoff < old_cutoff:
        raise WorkflowError("cutoff_reversal", "current data_cutoff is earlier than previous data_cutoff")
    if new["updates"][: len(old["updates"])] != old["updates"]:
        raise WorkflowError("history_rewrite", "previous update rows must be preserved verbatim")
    appended_updates = new["updates"][len(old["updates"]) :]
    if len(appended_updates) != 1:
        raise WorkflowError("invalid_update_count", "current thesis must append exactly one update row")
    if appended_updates[0]["日期"] != new["metadata"]["as_of"]:
        raise WorkflowError("update_date_mismatch", "new update row date must equal current thesis as_of")

    hypotheses = record_diff(old["hypotheses"], new["hypotheses"], state_column="状态")
    red_lines = record_diff(old["red_lines"], new["red_lines"], state_column="当前状态")
    source_ids = set(old["sources"]) | set(new["sources"])
    source_changes = {
        "added": {key: new["sources"][key] for key in sorted(set(new["sources"]) - set(old["sources"]))},
        "removed": {key: old["sources"][key] for key in sorted(set(old["sources"]) - set(new["sources"]))},
        "changed": {
            key: {"previous": old["sources"][key], "current": new["sources"][key]}
            for key in sorted(source_ids)
            if key in old["sources"]
            and key in new["sources"]
            and old["sources"][key] != new["sources"][key]
        },
    }
    section_changes = {
        name: {
            "changed": old["sections"][name] != new["sections"][name],
            "previous_sha256": sha256_text(old["sections"][name]),
            "current_sha256": sha256_text(new["sections"][name]),
        }
        for name in old["sections"]
    }
    current_hypothesis_states = {record["状态"] for record in new["hypotheses"]}
    current_red_line_states = {record["当前状态"] for record in new["red_lines"]}
    if "BROKEN" in current_hypothesis_states or "TRIGGERED" in current_red_line_states:
        signal = "CRITICAL_REVIEW"
    elif {"DAMAGED", "WEAKENED"} & current_hypothesis_states or "WATCH" in current_red_line_states:
        signal = "REVIEW_REQUIRED"
    elif any(source_changes.values()) or any(item["changed"] for item in section_changes.values()) or any(
        hypotheses[key] or red_lines[key] for key in ("added", "removed", "changed")
    ):
        signal = "CHANGED"
    else:
        signal = "NO_MATERIAL_CHANGE"
    warnings: list[str] = []
    if hypotheses["removed"]:
        warnings.append("hypotheses were removed; confirm that the new update row explains each removal")
    if red_lines["removed"]:
        warnings.append("red lines were removed; confirm that the new update row explains each removal")
    if source_changes["removed"]:
        warnings.append("source definitions were removed; verify that historical citations remain resolvable")

    return {
        "schema": "money-craft.thesis-diff.v1",
        "valid": True,
        "identity": {field: new["metadata"][field] for field in identity_fields},
        "previous": {
            "filename": old["filename"],
            "sha256": old["sha256"],
            "as_of": old["metadata"]["as_of"],
            "data_cutoff": old["metadata"]["data_cutoff"],
        },
        "current": {
            "filename": new["filename"],
            "sha256": new["sha256"],
            "as_of": new["metadata"]["as_of"],
            "data_cutoff": new["metadata"]["data_cutoff"],
        },
        "signal": signal,
        "hypotheses": hypotheses,
        "red_lines": red_lines,
        "sections": section_changes,
        "sources": source_changes,
        "appended_update": appended_updates[0],
        "audits": {"previous": old["audits"], "current": new["audits"]},
        "warnings": warnings,
    }
