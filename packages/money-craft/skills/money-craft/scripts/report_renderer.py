#!/usr/bin/env python3
"""Render audited Money Craft Markdown as portable HTML and print-ready PDF."""

from __future__ import annotations

import argparse
import contextlib
import os
import tempfile
import html
from html.parser import HTMLParser
import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable

from fsutil import sha256_file

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REPORTING_ROOT = SKILL_ROOT / "reporting"
DEFAULT_TEMPLATE = REPORTING_ROOT / "report.html"
DEFAULT_STYLE = REPORTING_ROOT / "report.css"
DEFAULT_SCRIPT = REPORTING_ROOT / "report.js"
CANONICAL_THEME = "editorial-ivory"
THEME_LABEL = "Money Craft Editorial Ivory"
LAYOUT_MODE = "research-publication"
RENDER_SCHEMA = "money-craft.report-render.v1"
VERIFY_SCHEMA = "money-craft.report-render-verify.v1"
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")
H2_RE = re.compile(r'<h2\s+id="([^"]+)">(.*?)</h2>', re.IGNORECASE | re.DOTALL)
TABLE_RE = re.compile(r"<table>.*?</table>", re.IGNORECASE | re.DOTALL)
SOURCE_REF_RE = re.compile(r"\[(S\d{2,4})\]")
URL_RE = re.compile(r"https?://[^\s<]+")
NUMERIC_CELL_RE = re.compile(
    r"^[\s~约]?[+−-]?(?:\d[\d,]*(?:\.\d+)?|\.\d+)(?:\s*(?:%|元|亿元|倍|万元|千元))?(?:\s|$)",
    re.IGNORECASE,
)
UNIT_SUFFIX_RE = re.compile(r"[（(]\s*([^（）()]{1,16})\s*[）)]\s*$")
# 图表系列注册表：色随实体固定顺序分配，禁止按出现顺序循环取色。
# 三套取值均已通过 dataviz validate_palette.js 六项检查（2026-08 记录）：
# light(surface #F8F6F0) / dark(surface #1D1C19) / print(#FFFFFF 全套沿用 light 值)。
# dark 值的唯一运行时来源是 report.css 的 [data-theme="dark"] token；
# 这里的 CHART_SERIES_DARK 供测试与 report.css 对账，防止两侧漂移。
CHART_SERIES_LIGHT: dict[str, str] = {
    "revenue": "#C4472D",
    "net_profit": "#1173A8",
    "eps": "#B04A7F",
    "operating_cash": "#AD7014",
    "capex_proxy": "#0E8266",
}
CHART_SERIES_DARK: dict[str, str] = {
    "revenue": "#E46B50",
    "net_profit": "#3D9AC0",
    "eps": "#C25E92",
    "operating_cash": "#BC8828",
    "capex_proxy": "#23917A",
}
CHART_SERIES_LABELS: dict[str, str] = {
    "revenue": "营业收入",
    "net_profit": "归母净利润",
    "eps": "基本每股收益",
    "operating_cash": "经营现金流",
    "capex_proxy": "资本开支代理项",
}
# 首屏财务小倍图固定三幅：收入、盈利、经营现金流。EPS/开支走扩展图或正文表。
PRIMARY_FINANCIAL_KEYS: tuple[str, ...] = ("revenue", "net_profit", "operating_cash")
# 行名匹配按注册顺序取第一个命中；excluded 用于阻止「扣非归母净利润」误入净利润面板。
CHART_SERIES_MATCHERS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("capex_proxy", ("资本开支代理项",), ()),
    ("operating_cash", ("经营现金流",), ()),
    ("eps", ("基本每股收益", "基本EPS"), ()),
    ("net_profit", ("归母净利润",), ("扣非",)),
    ("revenue", ("营业收入", "营业总收入"), ()),
)
SCENARIO_BAR_LIGHT = "#1173A8"
SCENARIO_BAR_DARK = "#3D9AC0"


class ReportRenderError(RuntimeError):
    """A fail-closed report rendition error."""


@dataclass(frozen=True)
class MarkdownTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ParsedReport:
    title: str
    metadata: dict[str, str]
    markdown_body: str
    source_text: str


def load_json(path: Path | None) -> dict[str, Any] | list[Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReportRenderError(f"cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, (dict, list)):
        raise ReportRenderError(f"JSON artifact must contain an object or array: {path}")
    return payload


def normalize_metadata_key(value: str) -> str:
    # Formatting may wrap a key; underscores inside YAML identifiers are semantic.
    value = re.sub(r"^([*_`]+)(.*?)\1$", r"\2", value.strip())
    return re.sub(r"\s+", " ", value).strip().strip("：:")


def parse_report(source_text: str) -> ParsedReport:
    metadata: dict[str, str] = {}
    text = source_text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) == 3:
            for line in parts[1].splitlines():
                if ":" not in line or line[:1].isspace():
                    continue
                key, value = line.split(":", 1)
                metadata[normalize_metadata_key(key)] = value.strip().strip('"\'')
            text = parts[2]

    text = re.sub(r"<style\b[^>]*>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
    title_match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if not title_match:
        raise ReportRenderError("report Markdown is missing a level-one title")
    title = re.sub(r"[*_`]", "", title_match.group(1)).strip()

    for line in text[: title_match.start()].splitlines() + text[title_match.end() :].splitlines()[:14]:
        stripped = line.strip()
        if not stripped.startswith(">"):
            continue
        value = stripped[1:].strip()
        value = re.sub(r"^\*\*(.*?)\*\*", r"\1", value)
        match = re.match(r"(.{2,36}?)[：:]\s*(.+)$", value)
        if match:
            metadata[normalize_metadata_key(match.group(1))] = re.sub(
                r"\*\*|`", "", match.group(2)
            ).strip()

    text = text[: title_match.start()] + text[title_match.end() :]
    first_section = re.search(r"^##\s+", text, re.MULTILINE)
    if first_section:
        text = text[first_section.start() :]
    text = re.sub(r"<!--\s*money-craft-calc:.*?-->", "", text, flags=re.DOTALL)
    return ParsedReport(title=title, metadata=metadata, markdown_body=text.strip(), source_text=source_text)


def metadata_value(metadata: dict[str, str], *needles: str) -> str | None:
    for needle in needles:
        for key, value in metadata.items():
            if needle.lower() in key.lower() and value.strip():
                return value.strip()
    return None


def clean_markdown_text(value: str) -> str:
    value = re.sub(r"\[(S\d{2,4})\]", "", value)
    value = re.sub(r"[*_`>#]", "", value)
    value = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", value)
    return re.sub(r"\s+", " ", value).strip()


def conclusion_text(parsed: ParsedReport) -> str:
    explicit = metadata_value(parsed.metadata, "核心结论", "结论")
    if explicit:
        return clean_markdown_text(explicit)
    match = re.search(
        r"^##\s+结论\s*$\n+(.+?)(?=\n\n|\n##\s+)",
        parsed.markdown_body,
        re.MULTILINE | re.DOTALL,
    )
    return clean_markdown_text(match.group(1)) if match else "请阅读完整证据后复核结论。"


def report_verdict(parsed: ParsedReport) -> str:
    haystack = " ".join(parsed.metadata.values()) + " " + conclusion_text(parsed)
    for value in ("WATCH", "SUPPORTED", "RISK", "BROKEN", "HOLD", "AVOID"):
        if re.search(rf"\b{value}\b", haystack, re.IGNORECASE):
            return value.upper()
    return "REVIEW"


def first_match(text: str, patterns: Iterable[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).replace(",", "").strip()
    return None


def report_identity(parsed: ParsedReport) -> str:
    identity = metadata_value(parsed.metadata, "security_id")
    if identity:
        return identity
    ticker = first_match(parsed.source_text, (r"\b(\d{6}\.(?:SH|SZ|BJ))\b",))
    if ticker:
        return ticker
    ticker = first_match(parsed.title, (r"\((\d{6})\)", r"\b(\d{6})\b"))
    return ticker or "SECURITY"


def report_date(parsed: ParsedReport) -> str:
    value = metadata_value(parsed.metadata, "研究日期", "as_of")
    match = re.search(r"20\d{2}-\d{2}-\d{2}", value or "")
    return match.group(0) if match else "UNSPECIFIED"


def print_identity(parsed: ParsedReport) -> str:
    return f"{report_identity(parsed)} · {report_date(parsed)}"


def data_cutoff(parsed: ParsedReport) -> str:
    return metadata_value(parsed.metadata, "数据截止", "data_cutoff") or "UNSPECIFIED"


def latest_period(parsed: ParsedReport) -> str:
    value = metadata_value(parsed.metadata, "最新正式报告期", "latest_report")
    if value:
        return value
    half_year = re.search(r"(20\d{2})\s*年(?:半年度报告|上半年)", parsed.source_text)
    if half_year:
        return f"{half_year.group(1)} 半年度"
    match = re.search(r"(20\d{2})\s*年第([一二三四1-4])季度", parsed.source_text)
    return f"{match.group(1)} Q{match.group(2)}" if match else "见正文"


def display_company_name(parsed: ParsedReport) -> str:
    value = re.sub(r"[（(]\s*\d{6}(?:\.(?:SH|SZ|BJ))?\s*[）)]", "", parsed.title)
    value = re.sub(r"基本面研究(?:报告)?$", "", value).strip()
    return value or parsed.title


def verdict_label(verdict: str) -> str:
    return {
        "WATCH": "观察",
        "SUPPORTED": "支持",
        "RISK": "风险",
        "BROKEN": "失效",
        "HOLD": "持有观察",
        "AVOID": "回避",
        "REVIEW": "待复核",
    }.get(verdict, verdict)


def metric_items(parsed: ParsedReport) -> list[dict[str, str]]:
    text = parsed.source_text
    price = first_match(
        text,
        (
            r"(?:前复权)?收盘价(?:为|：)?\s*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?)\s*元",
            r"价格\s*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?)\s*元",
        ),
    )
    pe = first_match(
        text,
        (
            r"静态\s*PE\s*(?:约|为)?\s*([0-9]+(?:\.[0-9]+)?)\s*倍",
            r"对应约?\s*([0-9]+(?:\.[0-9]+)?)\s*倍.*?PE",
        ),
    )
    ttm_pe = first_match(text, (r"PE\s*TTM\s*(?:约|为)?\s*([0-9]+(?:\.[0-9]+)?)\s*倍",))
    if ttm_pe:
        pe = ttm_pe
    adjusted = first_match(
        text,
        (r"扣非归母净利润(?:同比)?下降\s*(?:约)?\s*([0-9]+(?:\.[0-9]+)?)%",),
    )
    fcf = first_match(
        text,
        (r"FCF\s*代理值(?:同比)?(?:变化\s*=\s*)?下降\s*(?:约)?\s*([0-9]+(?:\.[0-9]+)?)%",),
    )
    items = [
        {
            "label": "截止日价格",
            "value": f"{price} 元" if price else "见正文",
            "note": "非实时行情",
            "tone": "neutral",
        },
        {
            "label": "PE · TTM" if ttm_pe else "静态 PE",
            "value": f"{pe}×" if pe else "见估值",
            "note": "报告明示口径",
            "tone": "neutral",
        },
        {
            "label": "扣非利润变化",
            "value": f"−{adjusted}%" if adjusted else "待复核",
            "note": "最新报告期同比",
            "tone": "negative" if adjusted else "neutral",
        },
        {
            "label": "FCF 代理值变化",
            "value": f"−{fcf}%" if fcf else "待复核",
            "note": "同比，非会计准则口径",
            "tone": "negative" if fcf else "neutral",
        },
    ]
    return items


def split_table_row(line: str) -> tuple[str, ...]:
    value = line.strip().strip("|")
    return tuple(cell.strip() for cell in re.split(r"(?<!\\)\|", value))


def parse_markdown_tables(text: str) -> list[MarkdownTable]:
    # Code examples are not research data. Keep blank boundaries so masking
    # cannot join a header outside code to rows inside a code block.
    lines: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        if fence is not None:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", line):
                fence = None
            lines.append("")
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if opening and not (opening.group(1)[0] == "`" and "`" in opening.group(2)):
            fence = (opening.group(1)[0], len(opening.group(1)))
            lines.append("")
            continue
        lines.append("" if line.expandtabs(4).startswith("    ") else line)
    tables: list[MarkdownTable] = []
    index = 0
    while index + 1 < len(lines):
        if "|" not in lines[index] or not re.match(r"^\s*\|?\s*:?-{3,}", lines[index + 1]):
            index += 1
            continue
        headers = split_table_row(lines[index])
        separators = split_table_row(lines[index + 1])
        if len(separators) != len(headers) or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separators):
            index += 1
            continue
        rows: list[tuple[str, ...]] = []
        index += 2
        while index < len(lines) and "|" in lines[index] and lines[index].strip():
            row = split_table_row(lines[index])
            if len(row) == len(headers):
                rows.append(row)
            index += 1
        if headers and rows:
            tables.append(MarkdownTable(headers=headers, rows=tuple(rows)))
    return tables


def numeric_value(value: str, *, suffixes: tuple[str, ...] = ()) -> float | None:
    """Accept a whole scalar, never extract numbers from ranges or prose.

    Units are caller-owned: trends inherit row units, YoY allows %, and
    per-share scenarios allow 元. Unsupported notation stays in the source table.
    """
    cleaned = value.strip().replace("−", "-")
    for wrapper in ("**", "__", "`", "*", "_"):
        if cleaned.startswith(wrapper) and cleaned.endswith(wrapper) and len(cleaned) > 2 * len(wrapper):
            cleaned = cleaned[len(wrapper):-len(wrapper)].strip()
            break
    suffix = "(?:" + "|".join(re.escape(item) for item in suffixes) + ")?" if suffixes else ""
    number = r"[+-]?(?:(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
    match = re.fullmatch(r"(" + number + r")\s*" + suffix, cleaned)
    if not match:
        return None
    scalar = match.group(1).replace(",", "")
    result = float(scalar)
    nonzero_mantissa = any(char in "123456789" for char in scalar.lower().split("e")[0])
    if not math.isfinite(result) or (result == 0 and nonzero_mantissa):
        return None
    return result


def financial_trend_table(tables: list[MarkdownTable]) -> MarkdownTable | None:
    for table in tables:
        years = sum(bool(re.fullmatch(r"20\d{2}", clean_markdown_text(header))) for header in table.headers)
        labels = " ".join(row[0] for row in table.rows if row)
        if years >= 3 and "营业收入" in labels and "归母净利润" in labels:
            return table
        # The canonical acceptance report puts years in rows, not columns.
        if (len(table.rows) >= 3 and table.headers[0] in {"年度", "年份", "年"}
                and all(re.fullmatch(r"20\d{2}", clean_markdown_text(row[0])) for row in table.rows)
                and "营业收入" in " ".join(table.headers)
                and "归母净利润" in " ".join(table.headers)):
            return MarkdownTable(
                headers=("指标", *(clean_markdown_text(row[0]) for row in table.rows)),
                rows=tuple((header, *(row[index] for row in table.rows))
                           for index, header in enumerate(table.headers) if index),
            )
    return None


def scenario_table(tables: list[MarkdownTable]) -> MarkdownTable | None:
    for table in tables:
        joined = " ".join(table.headers)
        labels = " ".join(row[0] for row in table.rows if row)
        has_complete_scenarios = (
            {"bear", "base", "bull"}.issubset({clean_markdown_text(row[0]).lower() for row in table.rows if row})
            or all(label in labels for label in ("悲观", "中性", "乐观"))
        )
        if "情景" in joined and ("价值" in joined or "目标价" in joined) and has_complete_scenarios:
            return table
    return None


def svg_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def series_class(key: str) -> str:
    """SVG class 名，与 report.css 中 --chart-* token 一一对应。"""
    return "cs-" + key.replace("_", "-")


def match_series_key(label: str) -> str | None:
    normalized = re.sub(r"\s+", "", clean_markdown_text(label))
    for key, keywords, excluded in CHART_SERIES_MATCHERS:
        if any(word in normalized for word in keywords) and not any(
            word in normalized for word in excluded
        ):
            return key
    return None


def format_chart_number(value: float, *, decimals: int = 2, signed: bool = False) -> str:
    """Keep nonzero labels nonzero, normalize signed zero and bound extreme text."""
    value = 0.0 if value == 0 else value
    sign = "+" if signed else ""
    if value != 0 and (abs(value) < 0.5 * 10 ** -decimals or abs(value) >= 1e12):
        return format(value, f"{sign}.3e").replace("-", "−")
    return format(value, f"{sign}.{decimals}f").replace("-", "−")


def format_value(value: float) -> str:
    if value != 0 and (abs(value) < 0.005 or abs(value) >= 1e12):
        return format_chart_number(value)
    value = 0.0 if value == 0 else value
    if abs(value) >= 1000:
        formatted = f"{value:,.0f}"
    elif abs(value) >= 100:
        formatted = f"{value:.1f}"
    else:
        formatted = f"{value:.2f}".rstrip("0").rstrip(".")
    return formatted.replace("-", "−")


def monetary_row_unit(label: str, first_header: str) -> str | None:
    """Require an explicit monetary row unit; never convert or infer scales."""
    match = UNIT_SUFFIX_RE.search(clean_markdown_text(label))
    if match is None:
        return None
    unit = match.group(1).strip()
    if re.fullmatch(r"(?:(?:人民币)?(?:元|千元|万元|百万元|亿元)|(?:千|万|百万|亿)?(?:美元|港元|欧元|日元))", unit) is None:
        return None
    header_unit = UNIT_SUFFIX_RE.search(clean_markdown_text(first_header))
    if header_unit is not None and header_unit.group(1).strip() != unit:
        return None
    return unit


def chronological_year_indices(table: MarkdownTable) -> list[int]:
    years = [(int(clean_markdown_text(header)), index) for index, header in enumerate(table.headers)
             if re.fullmatch(r"20\d{2}", clean_markdown_text(header))]
    if len(years) < 3 or len({year for year, _ in years}) != len(years):
        return []
    return [index for _, index in sorted(years)]


def financial_chart(table: MarkdownTable | None) -> str:
    """近五年核心财务 small multiples；每面板独立量程，数字只来自已披露表格。"""
    if table is None:
        return ""
    year_indices = chronological_year_indices(table)
    if len(year_indices) < 3:
        return ""
    years = [clean_markdown_text(table.headers[index]) for index in year_indices]
    panels: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for row in table.rows:
        if not row:
            continue
        raw_label = clean_markdown_text(row[0])
        key = match_series_key(raw_label)
        if key is None or key in seen_keys:
            continue
        values = [numeric_value(row[index]) for index in year_indices]
        if any(value is None for value in values):
            continue
        unit = monetary_row_unit(raw_label, table.headers[0])
        if unit is None:
            continue
        panels.append(
            {
                "key": key,
                "label": CHART_SERIES_LABELS[key],
                "unit": unit,
                "values": [float(value) for value in values],
            }
        )
        seen_keys.add(key)
    by_key = {panel["key"]: panel for panel in panels}
    panels = [by_key[key] for key in PRIMARY_FINANCIAL_KEYS if key in by_key]
    if not panels:
        return ""

    width, panel_height, pad_top, pad_bottom = 520, 100, 10, 14
    height = pad_top + panel_height * len(panels) + pad_bottom
    chart_left, chart_right = 132, 508
    css_class = series_class
    color_of = CHART_SERIES_LIGHT
    elements = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="核心财务趋势小倍图 {svg_text(years[0])}—{svg_text(years[-1])}，各面板独立量程">'
    ]
    for panel_index, panel in enumerate(panels):
        key = panel["key"]
        color = color_of[key]
        css = css_class(key)
        row_top = pad_top + panel_index * panel_height
        top = row_top + 24
        bottom = row_top + 76
        values: list[float] = panel["values"]
        low = min(values)
        high = max(values)
        span = high - low or max(abs(high), 1.0)
        if not math.isfinite(span):
            return ""
        xs = [
            chart_left + (chart_right - chart_left) * (int(years[index]) - int(years[0])) / (int(years[-1]) - int(years[0]))
            for index in range(len(values))
        ]
        ys = [bottom - (value - low) / span * (bottom - top) for value in values]
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
        change = "变化率不适用"
        if values[0] > 0:
            delta = (values[-1] / values[0] - 1) * 100
            change = format_chart_number(delta, decimals=1, signed=True) + "%" if math.isfinite(delta) else "变化率超出数值范围"
        series_title = "{} {}—{}".format(panel["label"], years[0], years[-1])
        elements.extend(
            [
                # 文字一律用文本 token；系列身份由紧邻色点与线形承载。
                f'<text x="0" y="{row_top + 24:.1f}" class="chart-name" fill="#171715" font-size="12" font-weight="650">{svg_text(panel["label"] + "（" + panel["unit"] + "）")}</text>',
                f'<text x="0" y="{row_top + 44:.1f}" class="chart-range" fill="#77736B" font-size="9.5">{svg_text(format_value(values[0]))} → {svg_text(format_value(values[-1]))}</text>',
                f'<circle cx="4" cy="{row_top + 62.5:.1f}" r="3" class="{css}" fill="{color}"/>',
                f'<text x="12" y="{row_top + 66:.1f}" class="chart-delta" fill="#4E4B45" font-size="10" font-weight="700">{change}</text>',
                f'<line x1="{chart_left:.1f}" y1="{bottom:.1f}" x2="{chart_right:.1f}" y2="{bottom:.1f}" class="chart-grid" stroke="#D5D0C6" stroke-width="1"/>',
                f'<polyline points="{points}" class="{css}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="square" stroke-linejoin="miter"><title>{svg_text(series_title)}</title></polyline>',
                f'<circle cx="{xs[0]:.1f}" cy="{ys[0]:.1f}" r="2.8" class="chart-ring ring-{key.replace("_", "-")}" fill="#F8F6F0" stroke="{color}" stroke-width="1.7"><title>{svg_text(f"{years[0]} {format_value(values[0])}")}</title></circle>',
                f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="3.5" class="{css}" fill="{color}"><title>{svg_text(f"{years[-1]} {format_value(values[-1])}")}</title></circle>',
                f'<text x="{chart_left:.1f}" y="{row_top + 94:.1f}" class="chart-tick" fill="#77736B" font-size="8.5">{svg_text(years[0])}</text>',
                f'<text x="{chart_right:.1f}" y="{row_top + 94:.1f}" text-anchor="end" class="chart-tick" fill="#77736B" font-size="8.5">{svg_text(years[-1])}</text>',
            ]
        )
        for year, value, x, y in zip(years[1:-1], values[1:-1], xs[1:-1], ys[1:-1]):
            point_label = f"{year} {format_value(value)} {panel['unit']}"
            elements.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" class="{css}" fill="{color}">'
                f'<title>{svg_text(point_label)}</title></circle>'
            )
        if panel_index < len(panels) - 1:
            elements.append(
                f'<line x1="0" y1="{row_top + panel_height - 1:.1f}" x2="{width}" y2="{row_top + panel_height - 1:.1f}" class="chart-grid" stroke="#D5D0C6" stroke-width="1"/>'
            )
    elements.append("</svg>")
    units = sorted({panel["unit"] for panel in panels if panel["unit"]})
    unit_text = " / ".join(units) if units else "单位见行标"
    return (
        '<figure class="evidence-figure" data-chart="financial-trends">'
        f'<div class="figure-head"><figcaption class="figure-title">核心财务轨迹</figcaption>'
        f'<span class="figure-meta">各指标独立量程 · {svg_text(unit_text)}</span></div>'
        + "".join(elements)
        + f'<p class="figure-note">{svg_text(years[0])}—{svg_text(years[-1])} · 点代表年度，百分比为首末年累计变化。各指标独立量程，精确值见正文表格。</p></figure>'
    )


def scenario_chart(table: MarkdownTable | None, current_price: float | None) -> str:
    """估值情景水平细条；单一冷蓝系列，蓝灰虚线标截止日价格，支持负值。"""
    if table is None:
        return ""
    # This chart compares per-share yuan values. Do not infer currencies or
    # turn enterprise/total values into share prices from a substring match.
    header_pattern = re.compile(
        r"(?:目标价|示意价值|每股(?:内在|合理)?价值)"
        r"(?:[（(](?P<unit>(?:人民币)?元(?:/股)?)[）)])?"
    )
    columns = [(index, header_pattern.fullmatch(re.sub(r"\s+", "", clean_markdown_text(header))))
               for index, header in enumerate(table.headers)]
    candidates = [(index, match) for index, match in columns if match is not None]
    if len(candidates) != 1:
        return ""
    value_index, header_match = candidates[0]
    explicit_header_unit = header_match.group("unit") is not None
    canonical_labels = {"bear", "base", "bull", "悲观", "中性", "乐观"}
    rows: list[tuple[str, float]] = []
    for row in table.rows:
        if not row:
            continue
        label = clean_markdown_text(row[0])
        if label.lower() not in canonical_labels:
            continue
        cell = row[value_index]
        if not explicit_header_unit and numeric_value(cell) is not None:
            return ""
        value = numeric_value(cell, suffixes=("元", "元/股", "人民币元", "人民币元/股"))
        if value is None:
            return ""
        rows.append((label, value))
    labels = {label.lower() for label, _ in rows}
    if len(rows) != 3 or labels not in ({"bear", "base", "bull"}, {"悲观", "中性", "乐观"}):
        return ""

    candidates = [value for _, value in rows]
    if current_price is not None:
        candidates.append(current_price)
    if not all(math.isfinite(value) for value in candidates):
        return ""
    low_bound = min(0.0, min(candidates))
    high_bound = max(max(candidates), 0.0)
    raw_span = high_bound - low_bound or max(abs(high_bound), abs(low_bound), 1.0)
    axis_min = low_bound - raw_span * 0.08 if low_bound < 0 else 0.0
    axis_max = high_bound + raw_span * 0.12
    plot_span = axis_max - axis_min
    if not math.isfinite(plot_span) or plot_span <= 0:
        return ""

    width = 520
    height = 236
    chart_left = 82
    chart_right = 502
    chart_width = chart_right - chart_left

    def x_at(value: float) -> float:
        return chart_left + ((value - axis_min) / plot_span) * chart_width

    zero_x = x_at(0.0)
    elements = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Bear Base Bull 估值情景与截止日价格比较，区间 {format_value(axis_min)} 到 {format_value(axis_max)} 元">'
    ]
    for tick in range(5):
        tick_value = axis_min + plot_span * (tick / 4)
        x = x_at(tick_value)
        elements.extend(
            [
                f'<line x1="{x:.1f}" y1="34" x2="{x:.1f}" y2="204" class="chart-grid" stroke="#D5D0C6" stroke-width="1"/>',
                f'<text x="{x:.1f}" y="222" text-anchor="middle" class="chart-tick" fill="#77736B" font-size="9">{svg_text(format_value(tick_value))}</text>',
            ]
        )
    for index, (label, value) in enumerate(rows):
        y = 60 + index * 54
        if value >= 0:
            bar_x, bar_width, label_anchor, label_x_offset = zero_x, (value / plot_span) * chart_width, "start", 7
        else:
            bar_width = ((-value) / plot_span) * chart_width
            bar_x, label_anchor, label_x_offset = zero_x - bar_width, "end", -7
        elements.extend(
            [
                f'<text x="{chart_left - 12}" y="{y + 4}" text-anchor="end" class="chart-name" fill="#171715" font-size="11" font-weight="650">{svg_text(label)}</text>',
                f'<rect x="{bar_x:.1f}" y="{y - 4}" width="{bar_width:.6g}" height="8" class="cs-scenario" fill="{SCENARIO_BAR_LIGHT}"><title>{svg_text(f"{label} {format_chart_number(value)} 元")}</title></rect>',
                f'<text x="{min(bar_x + bar_width + label_x_offset, chart_right - 1):.1f}" y="{y - 9}" text-anchor="{label_anchor}" class="chart-value" fill="#171715" font-size="10" font-weight="650">{svg_text(format_chart_number(value))}</text>',
            ]
        )
    if current_price is not None and axis_min <= current_price <= axis_max:
        x = x_at(current_price)
        elements.extend(
            [
                f'<line x1="{x:.1f}" y1="27" x2="{x:.1f}" y2="204" class="chart-price-line" stroke="#315868" stroke-width="1.6" stroke-dasharray="3 3"/>',
                f'<text x="{x:.1f}" y="18" text-anchor="middle" class="chart-price" fill="#315868" font-size="9" font-weight="700">截止日 {format_chart_number(current_price)}</text>',
            ]
        )
    elements.append("</svg>")
    return (
        '<figure class="evidence-figure" data-chart="valuation-scenarios">'
        '<div class="figure-head"><figcaption class="figure-title">价格与假设的距离</figcaption>'
        '<span class="figure-meta">元/股 · HYPOTHESIZED</span></div>'
        + "".join(elements)
        + '<p class="figure-note">'
        + ('虚线为报告截止日价格，' if current_price is not None else '未提供报告截止日价格；')
        + '细条为假设情景。不是目标价或收益承诺；口径与计算见估值章节。</p></figure>'
    )


@dataclass(frozen=True)
class ChartContext:
    """图表构建器的唯一输入；数字只允许从 canonical Markdown 的已披露表格派生。"""

    parsed: ParsedReport
    tables: list[MarkdownTable]
    evidence: dict[str, Any] | list[Any] | None


ChartBuilder = Callable[[ChartContext], str | None]


def chart_financial_trends(context: ChartContext) -> str | None:
    return financial_chart(financial_trend_table(context.tables))


def chart_valuation_scenarios(context: ChartContext) -> str | None:
    return scenario_chart(scenario_table(context.tables), current_price(context.parsed))


FALSIFICATION_ROW_RE = re.compile(r"^R\d{2,3}$")
FALSIFICATION_STATUSES = ("WATCH", "CLEAR", "UNVERIFIED", "BROKEN")


def yoy_percentage_value(header: str, cell: str) -> float | None:
    """A percent chart cannot infer percentage points, money or bare ratios."""
    normalized = re.sub(r"\s+", "", clean_markdown_text(header))
    match = re.fullmatch(
        r"同比(?:增长率|增速|变化率|变动率)?(?:[（(](?P<unit>%)[）)])?", normalized
    )
    if match is None:
        return None
    if match.group("unit") is None and numeric_value(cell) is not None:
        return None
    return numeric_value(cell, suffixes=("%",))


def yoy_change_table(tables: list[MarkdownTable]) -> tuple[MarkdownTable, int] | None:
    """返回 (表, 同比列下标)：含「同比」列头、≥2 行可解析数值且包含营业收入行。"""
    for table in tables:
        index = next(
            (
                position
                for position, header in enumerate(table.headers)
                if "同比" in clean_markdown_text(header)
            ),
            None,
        )
        if index is None or not table.rows:
            continue
        resolvable = sum(
            1 for row in table.rows if row and yoy_percentage_value(table.headers[index], row[index]) is not None
        )
        labels = " ".join(clean_markdown_text(row[0]) for row in table.rows if row)
        if resolvable >= 2 and "营业收入" in labels:
            return table, index
    return None


def earnings_quality_chart(table: MarkdownTable | None, value_index: int | None) -> str | None:
    """盈利质量背离图：最新报告期同比，正值冷蓝、负值朱砂，「持平」等非数值行跳过。"""
    if table is None or value_index is None:
        return None
    entries: list[tuple[str, float]] = []
    for row in table.rows:
        if not row:
            continue
        label = clean_markdown_text(row[0])
        if not label or "同比" in label:
            continue
        value = yoy_percentage_value(table.headers[value_index], row[value_index])
        if value is not None:
            entries.append((label[:10], value))
    if len(entries) < 2:
        return None
    # 超过 8 项时只绘制前 8 项，图注显式披露截断，不静默丢弃。
    truncated = len(entries) > 8
    entries = entries[:8]

    low = min(0.0, min(value for _, value in entries))
    high = max(max(value for _, value in entries), 0.0)
    raw_span = high - low or max(abs(high), abs(low), 1.0)
    axis_min = low - raw_span * 0.12 if low < 0 else 0.0
    axis_max = high + raw_span * 0.2
    plot_span = axis_max - axis_min
    if not math.isfinite(plot_span) or plot_span <= 0:
        return None

    width = 520
    row_height = 36
    top = 30
    height = top + row_height * len(entries) + 18
    plot_left, plot_right = 148, 464
    center_line = plot_left + ((-axis_min) / plot_span) * (plot_right - plot_left)

    def x_at(value: float) -> float:
        return plot_left + ((value - axis_min) / plot_span) * (plot_right - plot_left)

    elements = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="最新报告期同比变化，{len(entries)} 项指标，正负方向对比">',
        f'<line x1="{center_line:.1f}" y1="{top - 6}" x2="{center_line:.1f}" y2="{height - 16}" class="chart-grid" stroke="#D5D0C6" stroke-width="1"/>',
    ]
    for index, (label, value) in enumerate(entries):
        center_y = top + index * row_height + row_height / 2
        bar_y = center_y - 3.5
        if value >= 0:
            bar_x, bar_width = center_line, x_at(value) - center_line
        else:
            bar_width = center_line - x_at(value)
            bar_x = center_line - bar_width
        tone_class = "chart-yoy-pos" if value >= 0 else "chart-yoy-neg"
        tone_hex = "#1173A8" if value >= 0 else "#C4472D"
        # 数值标签默认放条形端点外侧；贴近画布边缘时翻转到内侧，避免与行名/边界相撞。
        end_x = x_at(value)
        if value >= 0:
            inside = (plot_right - end_x) < 52
            text_x, anchor = (end_x - 6, "end") if inside else (end_x + 6, "start")
        else:
            inside = (end_x - plot_left) < 52
            text_x, anchor = (end_x + 6, "start") if inside else (end_x - 6, "end")
        elements.extend(
            [
                f'<text x="{plot_left - 20}" y="{center_y + 4:.1f}" text-anchor="end" class="chart-name" fill="#171715" font-size="11">{svg_text(label)}</text>',
                f'<rect x="{bar_x:.1f}" y="{bar_y:.1f}" width="{bar_width:.6g}" height="7" class="{tone_class}" fill="{tone_hex}"><title>{svg_text(f"{label} {format_percent(value)}")}</title></rect>',
                f'<text x="{text_x:.1f}" y="{center_y - 6:.1f}" text-anchor="{anchor}" class="chart-value" fill="#171715" font-size="9.5" font-weight="650">{svg_text(format_percent(value))}</text>',
            ]
        )
    elements.append("</svg>")
    return (
        '<figure class="evidence-figure" data-chart="earnings-quality">'
        '<div class="figure-head"><figcaption class="figure-title">盈利质量｜同比变化</figcaption>'
        f'<span class="figure-meta">% · 原表同比{" · 仅显示前 8 项" if truncated else ""}</span></div>'
        + "".join(elements)
        + '<p class="figure-note">正值冷蓝、负值朱砂；「持平」或未披露行不绘制。数值转录自正文表格，证据状态、口径与计算见正文。</p></figure>'
    )


def format_percent(value: float) -> str:
    return format_chart_number(value, signed=True) + "%"


def cash_flow_structure_chart(table: MarkdownTable | None) -> str | None:
    """现金流结构：经营现金流 vs 资本开支代理项；FCF 代理为显式公式派生（INFERRED）。"""
    if table is None:
        return None
    year_indices = chronological_year_indices(table)
    if len(year_indices) < 3:
        return None
    series_values: dict[str, list[float]] = {}
    series_units: dict[str, str] = {}
    seen: set[str] = set()
    for row in table.rows:
        if not row:
            continue
        key = match_series_key(clean_markdown_text(row[0]))
        if key not in ("operating_cash", "capex_proxy") or key in seen:
            continue
        values = [numeric_value(row[index]) for index in year_indices]
        if any(value is None for value in values):
            continue
        series_values[key] = [float(value) for value in values]
        unit = monetary_row_unit(row[0], table.headers[0])
        if unit is None:
            return None
        series_units[key] = unit
        seen.add(key)
    if "operating_cash" not in series_values or "capex_proxy" not in series_values:
        return None
    # Subtraction requires an explicit shared unit; unrelated rows (e.g. EPS)
    # must not supply the unit for these two monetary series.
    cash_unit = series_units["operating_cash"]
    if not cash_unit or cash_unit != series_units["capex_proxy"]:
        return None
    operating = series_values["operating_cash"]
    capex = series_values["capex_proxy"]
    fcf = [o - c for o, c in zip(operating, capex)]
    if not all(math.isfinite(value) for value in fcf):
        return None
    years = [clean_markdown_text(table.headers[index]) for index in year_indices]

    width, height = 520, 300
    left, right, top, bottom = 60, 452, 56, 248
    all_values = operating + capex + fcf
    lo = min(0.0, min(all_values))
    hi = max(max(all_values), 0.001)
    span = hi - lo or hi
    if not math.isfinite(span):
        return None

    def y_at(value: float) -> float:
        return bottom - (value - lo) / span * (bottom - top)

    def x_at(index: int) -> float:
        return left + (right - left) * (int(years[index]) - int(years[0])) / (int(years[-1]) - int(years[0]))

    legend_items = (
        ("经营现金流", CHART_SERIES_LIGHT["operating_cash"], series_class("operating_cash")),
        ("资本开支代理项", CHART_SERIES_LIGHT["capex_proxy"], series_class("capex_proxy")),
        ("FCF 代理", "#171715", "chart-fcf"),
    )
    legend_x = left
    elements = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="现金流结构 {svg_text(years[0])}—{svg_text(years[-1])}，经营现金流、资本开支代理项与其差额 FCF 代理">',
    ]
    for name, color, css in legend_items:
        elements.append(
            f'<g transform="translate({legend_x:.0f} 26)"><circle cx="0" cy="-3.5" r="3.5" class="{css}" fill="{color}"/>'
            f'<text x="9" y="0" class="chart-name" fill="#171715" font-size="10">{svg_text(name)}</text></g>'
        )
        legend_x += 58 + len(name) * 10.5
    for tick in range(5):
        tick_value = lo + span * (tick / 4)
        y = y_at(tick_value)
        elements.extend(
            [
                f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" class="chart-grid" stroke="#D5D0C6" stroke-width="1"/>',
                f'<text x="{left - 10}" y="{y + 3:.1f}" text-anchor="end" class="chart-tick" fill="#77736B" font-size="9">{svg_text(format_value(tick_value))}</text>',
            ]
        )
    for index, year in enumerate(years):
        elements.append(
            f'<text x="{x_at(index):.1f}" y="{bottom + 20:.1f}" text-anchor="middle" class="chart-tick" fill="#77736B" font-size="9">{svg_text(year)}</text>'
        )

    def polyline_of(values: list[float], color: str, css: str, dashed: bool = False) -> str:
        points = " ".join(f"{x_at(i):.1f},{y_at(v):.1f}" for i, v in enumerate(values))
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        title = svg_text(f"{name_of(css)} {years[0]}—{years[-1]}")
        return (
            f'<polyline points="{points}" class="{css}" fill="none" stroke="{color}" '
            f'stroke-width="2.2" stroke-linecap="square" stroke-linejoin="miter"{dash}><title>{title}</title></polyline>'
        )

    def name_of(css: str) -> str:
        return next(item[0] for item in legend_items if item[2] == css)

    for values, color, css, ring_css, dashed in (
        (operating, CHART_SERIES_LIGHT["operating_cash"], series_class("operating_cash"), "ring-operating-cash", False),
        (capex, CHART_SERIES_LIGHT["capex_proxy"], series_class("capex_proxy"), "ring-capex-proxy", False),
        (fcf, "#171715", "chart-fcf", "ring-fcf", True),
    ):
        elements.append(polyline_of(values, color, css, dashed))
        start_x, end_x = x_at(0), x_at(len(values) - 1)
        start_y, end_y = y_at(values[0]), y_at(values[-1])
        ring_fill = "#F8F6F0"
        marker = (
            f'<circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="2.8" class="chart-ring {ring_css}" fill="{ring_fill}" stroke="{color}" stroke-width="1.7">'
            f'<title>{svg_text(f"{name_of(css)} {years[0]} {format_value(values[0])}")}</title></circle>'
        )
        end_marker = (
            f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="3.5" class="{css}" fill="{color}">'
            f'<title>{svg_text(f"{name_of(css)} {years[-1]} {format_value(values[-1])}")}</title></circle>'
        )
        elements.extend([marker, end_marker])
    elements.append("</svg>")
    return (
        '<figure class="evidence-figure" data-chart="cash-flow-structure">'
        '<div class="figure-head"><figcaption class="figure-title">现金流结构｜经营、开支与留存</figcaption>'
        f'<span class="figure-meta">{svg_text(cash_unit)} · FCF 代理 = 经营 − 开支</span></div>'
        + "".join(elements)
        + '<p class="figure-note">FCF 代理值由已披露两行相减派生（<span class="evidence-state" data-state="INFERRED">INFERRED</span>），非会计准则自由现金流；虚线即派生序列。</p></figure>'
    )


def falsification_rows(tables: list[MarkdownTable]) -> list[tuple[str, str, str]] | None:
    """证伪条件表嗅探：行首 R 编号 + material/fatal 强度 + WATCH/CLEAR/UNVERIFIED/BROKEN 状态。"""
    for table in tables:
        headers = [clean_markdown_text(header) for header in table.headers]
        state_columns = [i for i, header in enumerate(headers) if header in {"状态", "当前状态"}]
        severity_columns = [i for i, header in enumerate(headers) if header in {"强度", "严重度"}]
        if len(state_columns) != 1 or len(severity_columns) > 1:
            continue
        rows: list[tuple[str, str, str]] = []
        for row in table.rows:
            if not row:
                continue
            first = clean_markdown_text(row[0]).upper()
            if not FALSIFICATION_ROW_RE.match(first):
                continue
            status = clean_markdown_text(row[state_columns[0]]).upper()
            if status not in FALSIFICATION_STATUSES:
                continue
            severity = clean_markdown_text(row[severity_columns[0]]).lower() if severity_columns else ""
            severity = severity if severity in {"fatal", "material"} else ""
            rows.append((first, severity, status))
        if rows:
            return rows
    return None


def falsification_status_chart(rows: list[tuple[str, str, str]] | None) -> str | None:
    if not rows:
        return None
    counts = {word: 0 for word in FALSIFICATION_STATUSES}
    for _rid, _severity, status in rows:
        counts[status] += 1
    summary = " / ".join(f"{word} {count}" for word, count in counts.items() if count)
    items = "".join(
        "<li class=\"falsification-item\">"
        f'<span class="falsification-id">{svg_text(rid)}</span>'
        + (
            f'<span class="falsification-severity" data-severity="{severity}">{svg_text(severity)}</span>'
            if severity
            else ""
        )
        + f'<span class="status-chip" data-status="{status}">{status}</span></li>'
        for rid, severity, status in rows
    )
    return (
        '<figure class="evidence-figure evidence-figure-text" data-chart="falsification-status">'
        '<div class="figure-head"><figcaption class="figure-title">证伪条件状态</figcaption>'
        f'<span class="figure-meta">{summary}</span></div>'
        f'<ul class="falsification-list">{items}</ul>'
        '<p class="figure-note">WATCH=观察中、CLEAR=已排除、UNVERIFIED=证据不足、BROKEN=已触发；逐条论证见风险章节。</p></figure>'
    )


def evidence_coverage_chart(evidence: dict[str, Any] | list[Any] | None) -> str | None:
    """证据覆盖组件：来源槽位索引视图，数据来自已是渲染输入的 evidence manifest。"""
    if not isinstance(evidence, dict):
        return None
    groups = evidence.get("groups")
    if not isinstance(groups, list):
        return None
    slots: list[tuple[str, str]] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        source_id = str(group.get("source_id") or "").upper()
        if not source_id:
            continue
        title = clean_markdown_text(str(group.get("title") or ""))[:24]
        items = group.get("items")
        count_label = f"{len(items)} 项" if isinstance(items, list) else "条目数未提供"
        slots.append((source_id, f"{title} · {count_label}" if title else count_label))
    if not slots:
        return None
    slots.sort(key=lambda pair: pair[0])
    cells = "".join(
        f'<span class="coverage-slot"><span class="coverage-slot-id">{svg_text(source_id)}</span><span class="coverage-slot-title">{svg_text(title)}</span></span>'
        for source_id, title in slots
    )
    return (
        '<figure class="evidence-figure evidence-figure-text" data-chart="evidence-coverage">'
        '<div class="figure-head"><figcaption class="figure-title">证据来源清单</figcaption>'
        f'<span class="figure-meta">清单登记 {len(slots)} 组</span></div>'
        f'<div class="coverage-grid">{cells}</div>'
        '<p class="figure-note">仅展示 manifest 登记来源和条目数，不代表证据质量、采集成功或审计通过；哈希与 URL 定位符见「主要数据来源」章节。</p></figure>'
    )


def chart_earnings_quality(context: ChartContext) -> str | None:
    found = yoy_change_table(context.tables)
    if found is None:
        return None
    table, value_index = found
    return earnings_quality_chart(table, value_index)


def chart_cash_flow_structure(context: ChartContext) -> str | None:
    return cash_flow_structure_chart(financial_trend_table(context.tables))


def chart_falsification_status(context: ChartContext) -> str | None:
    return falsification_status_chart(falsification_rows(context.tables))


def chart_evidence_coverage(context: ChartContext) -> str | None:
    return evidence_coverage_chart(context.evidence)


# 图表注册表：新增图表类型时在此追加 builder，渲染顺序即元组顺序。
CHART_BUILDERS: tuple[ChartBuilder, ...] = (
    chart_financial_trends,
    chart_valuation_scenarios,
    chart_earnings_quality,
    chart_cash_flow_structure,
    chart_falsification_status,
    chart_evidence_coverage,
)


def build_visual_parts(context: ChartContext) -> list[str]:
    parts: list[str] = []
    for builder in CHART_BUILDERS:
        part = builder(context)
        if part:
            parts.append(part)
    return parts


class ReportBodyAudit(HTMLParser):
    """Accept report markup only, before trusted template assets are inserted."""
    tags = frozenset("p br hr h1 h2 h3 h4 h5 h6 blockquote pre code em strong b i u s del sup sub ul ol li dl dt dd table thead tbody tfoot tr th td caption colgroup col a img span div details summary".split())
    global_attributes = frozenset({"id", "class", "title", "lang", "dir"})
    tag_attributes = {
        "a": {"href"}, "img": {"src", "alt", "width", "height"},
        "th": {"colspan", "rowspan", "scope", "style"},
        "td": {"colspan", "rowspan", "style"},
        "ol": {"start", "reversed", "type"}, "li": {"value"},
        "col": {"span"}, "colgroup": {"span"}, "details": {"open"},
    }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.tags:
            raise ReportRenderError(f"report body contains unsupported HTML element: {tag}")
        allowed = self.global_attributes | self.tag_attributes.get(tag, set())
        for name, value in attrs:
            if name not in allowed:
                raise ReportRenderError(f"report body contains unsupported HTML attribute: {name}")
            if name == "style" and not re.fullmatch(r"\s*text-align\s*:\s*(?:left|right|center)\s*;?\s*", value or "", re.IGNORECASE):
                raise ReportRenderError("report body only permits table text alignment styles")

    def handle_endtag(self, tag: str) -> None:
        if tag not in self.tags:
            raise ReportRenderError(f"report body contains unsupported HTML closing element: {tag}")

    def handle_decl(self, decl: str) -> None:
        raise ReportRenderError("report body must not contain document declarations")

    def handle_pi(self, data: str) -> None:
        raise ReportRenderError("report body must not contain processing instructions")

    def unknown_decl(self, data: str) -> None:
        raise ReportRenderError("report body must not contain unknown declarations")


def markdown_to_html(markdown_body: str, *, chart_tables: list[MarkdownTable] | None = None,
                     visible_text: list[str] | None = None) -> str:
    try:
        import markdown  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ReportRenderError(
            "report rendering requires the optional `markdown` package; run with the configured report-render environment"
        ) from exc
    converter = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        output_format="html5",
    )
    if chart_tables is not None or visible_text is not None:
        from markdown.treeprocessors import Treeprocessor

        class CollectChartTables(Treeprocessor):
            def run(self, root):
                def prose(element):
                    if element.tag in {"code", "pre", "blockquote", "ul", "ol"}:
                        return ""
                    return (element.text or "") + "".join(prose(child) + (child.tail or "") for child in element)
                if visible_text is not None:
                    for element in root:
                        text = prose(element)
                        if "\x02" not in text and "\x03" not in text:
                            visible_text.append(text)
                if chart_tables is None:
                    return
                # Only actual top-level Markdown tables supply chart data.
                # Raw HTML is still stashed; comments/code/nested examples
                # cannot become data merely by containing pipe-delimited lines.
                for table in root.findall("table"):
                    headers = tuple("".join(cell.itertext()).strip() for cell in table.findall("./thead/tr/th"))
                    rows = tuple(tuple("".join(cell.itertext()).strip() for cell in row.findall("td"))
                                 for row in table.findall("./tbody/tr"))
                    cells = (*headers, *(cell for row in rows for cell in row))
                    if (headers and rows and all(len(row) == len(headers) for row in rows)
                            and not any("\x02" in cell or "\x03" in cell for cell in cells)):
                        chart_tables.append(MarkdownTable(headers, rows))

        converter.treeprocessors.register(CollectChartTables(converter), "chart_tables", 15)
    rendered = converter.convert(markdown_body)
    body_audit = ReportBodyAudit(convert_charrefs=True)
    body_audit.feed(rendered)
    body_audit.close()
    return rendered


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def decorate_text_nodes(rendered: str) -> str:
    tokens = re.split(r"(<[^>]+>)", rendered)
    output: list[str] = []
    in_script_or_style = False
    for token in tokens:
        lower = token.lower()
        if lower.startswith(("<script", "<style")):
            in_script_or_style = True
        if token.startswith("<") or in_script_or_style:
            output.append(token)
        else:
            token = SOURCE_REF_RE.sub(
                lambda match: f'<span class="source-ref">[{match.group(1)}]</span>', token
            )
            for state in ("OBSERVED", "INFERRED", "HYPOTHESIZED", "UNVERIFIED", "BROKEN"):
                token = re.sub(
                    rf"\b{state}\b",
                    f'<span class="evidence-state" data-state="{state}">{state}</span>',
                    token,
                )
            token = URL_RE.sub(
                lambda match: source_locator(html.unescape(match.group(0))),
                token,
            )
            output.append(token)
        if lower.startswith(("</script", "</style")):
            in_script_or_style = False
    rendered = "".join(output)
    rendered = re.sub(
        r'<a\s+href="(https?://[^"]+)"[^>]*>(.*?)</a>',
        lambda match: (
            f'<span class="source-url" data-source-url="{html.escape(html.unescape(match.group(1)), quote=True)}">'
            f"{match.group(2)}</span>"
        ),
        rendered,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return rendered


def source_locator(value: str) -> str:
    escaped = html.escape(value, quote=True)
    return f'<span class="source-url" data-source-url="{escaped}">{escaped}</span>'


def classify_table_cells(table_html: str) -> str:
    def classify(match: re.Match[str]) -> str:
        tag = match.group(1).lower()
        body = match.group(2)
        text = strip_tags(body).replace("\xa0", " ").strip()
        class_name = ' class="numeric"' if NUMERIC_CELL_RE.match(text) else ""
        return f"<{tag}{class_name}>{body}</{tag}>"

    return re.sub(r"<(td|th)>(.*?)</\1>", classify, table_html, flags=re.IGNORECASE | re.DOTALL)


def wrap_tables(rendered: str) -> str:
    return TABLE_RE.sub(
        lambda match: (
            '<div class="table-scroll" role="region" aria-label="数据表格" tabindex="0">'
            + classify_table_cells(match.group(0))
            + "</div>"
        ),
        rendered,
    )


def decorate_headings(rendered: str) -> tuple[str, list[tuple[str, str]]]:
    headings: list[tuple[str, str]] = []

    def replace(match: re.Match[str]) -> str:
        section_id = match.group(1)
        title = strip_tags(match.group(2))
        headings.append((section_id, title))
        section_kind = (
            ' data-section-kind="sources"'
            if "数据来源" in title or "来源索引" in title
            else ""
        )
        return (
            f'<h2 id="{html.escape(section_id, quote=True)}"{section_kind}>'
            f'<span class="section-index">{len(headings):02d}</span> <span>{match.group(2)}</span></h2>'
        )

    return H2_RE.sub(replace, rendered), headings


def current_price(parsed: ParsedReport) -> float | None:
    value = metric_items(parsed)[0]["value"]
    return numeric_value(value, suffixes=("元",))


def build_masthead(parsed: ParsedReport, revision: dict[str, Any] | None) -> str:
    identity = report_identity(parsed)
    revision_id = revision.get("revision_id") if isinstance(revision, dict) else None
    return f'''<header class="report-masthead">
  <div class="brand-lockup">
    <span class="brand-name"><b>Money</b><b>Craft</b></span>
    <span class="brand-subtitle">投资研究 · 长期视角</span>
  </div>
  <div class="masthead-tools">
    <dl class="masthead-meta">
      <div><dt>证券</dt><dd>{html.escape(identity)}</dd></div>
      <div><dt>研究日</dt><dd><time data-report-date>{html.escape(report_date(parsed))}</time></dd></div>
      <div><dt>数据截止</dt><dd><time data-data-cutoff>{html.escape(data_cutoff(parsed))}</time></dd></div>
      <div><dt>版本</dt><dd>{html.escape(str(revision_id or "阅读预览 · 未封存"))}</dd></div>
    </dl>
    <button class="theme-toggle" type="button" data-theme-toggle aria-pressed="false"><span>夜间阅读</span></button>
  </div>
  <span class="print-identity">{html.escape(print_identity(parsed))}</span>
</header>'''


def build_navigation(headings: list[tuple[str, str]]) -> str:
    items = "".join(
        f'<li><a href="#{html.escape(section_id, quote=True)}" data-index="{index:02d}">{html.escape(title)}</a></li>'
        for index, (section_id, title) in enumerate(headings, start=1)
    )
    return f'''<nav class="section-nav" aria-label="报告章节" data-section-nav>
  <div class="section-nav-head"><span class="nav-eyebrow">阅读索引</span><button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="report-sections"><span data-nav-toggle-label>浏览 {len(headings)} 个章节</span></button></div>
  <ol id="report-sections" data-nav-list>{items}</ol>
</nav>'''


def build_decision_brief(parsed: ParsedReport) -> str:
    metrics = "".join(
        (
            '<div class="metric">'
            f'<dt class="metric-label">{html.escape(item["label"])}</dt>'
            f'<dd class="metric-value {html.escape(item["tone"])}">{html.escape(item["value"])}</dd>'
            f'<dd class="metric-note">{html.escape(item["note"])}</dd>'
            "</div>"
        )
        for item in metric_items(parsed) if item["value"] not in {"见正文", "见估值", "待复核"}
    )
    verdict = report_verdict(parsed)
    rating = (
        f'<p class="decision-rating" data-verdict="{html.escape(verdict)}">研究判断 · '
        f'{html.escape(verdict_label(verdict))}</p>' if verdict != "REVIEW" else ""
    )
    return f'''<section class="decision-brief" aria-labelledby="report-title">
  <div class="decision-grid">
    <div class="decision-title-block">
      <p class="decision-kicker"><span>公司研究</span><span>{html.escape(report_identity(parsed))}</span><span>{html.escape(latest_period(parsed))}</span></p>
      <h1 id="report-title"><span>{html.escape(display_company_name(parsed))}</span></h1>
      <p class="report-subtitle">基本面研究</p>
      {rating}
    </div>
    <dl class="metric-strip" aria-label="正文已披露指标">{metrics}</dl>
  </div>
</section>'''


def human_status(value: str) -> str:
    mapping = {
        "PASS": "通过",
        "FAIL": "未通过",
        "UNKNOWN": "未知",
        "NOT BOUND": "未绑定",
        "BOUND": "已绑定",
        "UNSEALED": "未封存",
    }
    return mapping.get(value, value)


def audit_summary(
    audit: dict[str, Any] | list[Any] | None,
    archive_manifest: dict[str, Any] | list[Any] | None,
) -> tuple[str, str]:
    archive_audit = archive_manifest.get("audit") if isinstance(archive_manifest, dict) else None
    payload = archive_audit if isinstance(archive_audit, dict) else audit
    if isinstance(payload, dict):
        verdict = payload.get("verdict", "PASS" if payload.get("valid") is True else "FAIL" if payload.get("valid") is False else "UNKNOWN")
        if verdict not in ("PASS", "FAIL", "UNKNOWN"):
            verdict = "UNKNOWN"
        if payload.get("valid") is False:
            verdict = "FAIL"
        total = payload.get("total", payload.get("check_count"))
        if "total" in payload and "check_count" in payload and (
                type(payload["check_count"]) is not int or payload["total"] != payload["check_count"]):
            return "审计声明冲突", "UNKNOWN"
        passed = payload.get("pass_count")
        if total is not None and passed is not None:
            if type(total) is not int or type(passed) is not int or not 0 <= passed <= total:
                return "审计计数不可用", "UNKNOWN"
            if passed < total and verdict == "PASS":
                return "审计声明冲突", "UNKNOWN"
            return f"{passed}/{total} {human_status(verdict)}", verdict
        return human_status(verdict), verdict
    if isinstance(payload, list):
        return "审计格式未识别", "UNKNOWN"
    return human_status("NOT BOUND"), "UNKNOWN"


def evidence_summary(evidence: dict[str, Any] | list[Any] | None) -> str:
    if not isinstance(evidence, dict):
        return human_status("NOT BOUND")
    summary = evidence.get("summary")
    if not isinstance(summary, dict):
        summary = evidence.get("evidence") if isinstance(evidence.get("evidence"), dict) else {}
    def count(primary: str, alias: str) -> int | None:
        keys = [key for key in (primary, alias) if key in summary]
        if not keys:
            return None
        values = [summary[key] for key in keys]
        if any(type(value) is not int or value < 0 for value in values) or len(set(values)) != 1:
            raise ValueError("invalid or conflicting evidence count")
        return values[0]

    try:
        captured = count("captured", "captured_urls")
        expected = count("expected", "expected_urls")
        failed = count("failed", "failed_urls")
    except ValueError:
        return "清单计数不可用"
    if captured is not None and expected is not None:
        if captured > expected or (failed is not None and failed > expected):
            return "清单计数不可用"
        failure_label = str(failed) if failed is not None else "未提供"
        return f"清单计数 {captured}/{expected}，失败 {failure_label}"
    if summary:
        return "清单计数不可用"
    groups = evidence.get("groups")
    return f"清单登记 {len(groups)} 组（未核验）" if isinstance(groups, list) else human_status("BOUND")


def offline_status(revision: dict[str, Any] | None) -> str:
    if not isinstance(revision, dict):
        return human_status("NOT BOUND")
    verifier = revision.get("offline_verifier")
    if not isinstance(verifier, dict):
        return human_status("NOT BOUND")
    ok = verifier.get("ok") is True and verifier.get("verified_offline") is True
    return human_status("PASS" if ok else "FAIL")


def build_audit_seal(
    source_sha256: str,
    audit: dict[str, Any] | list[Any] | None,
    evidence: dict[str, Any] | list[Any] | None,
    revision: dict[str, Any] | None,
    archive_manifest: dict[str, Any] | list[Any] | None,
) -> str:
    audit_value, _verdict = audit_summary(audit, archive_manifest)
    revision_id = revision.get("revision_id") if isinstance(revision, dict) else None
    revision_label = human_status(str(revision_id or "UNSEALED")) if not revision_id else str(revision_id)
    items = (
        ("报告审计", audit_value),
        ("证据覆盖", evidence_summary(evidence)),
        ("离线核验", offline_status(revision)),
        ("源文哈希", source_sha256[:16]),
    )
    cells = "".join(
        f'<div class="audit-item"><span class="audit-label">{html.escape(label)}</span><span class="audit-value">{html.escape(value)}</span></div>'
        for label, value in items
    )
    return f'''<section class="audit-seal" aria-labelledby="audit-seal-title">
  <h2 id="audit-seal-title">证据与完整性</h2>
  <div class="audit-grid">{cells}</div>
  <p class="audit-note">本阅读层绑定版本 {html.escape(revision_label)} 与源 Markdown 哈希。审计和离线状态为输入清单声明，本次渲染不重新执行这些检查。HTML/PDF 可重建，不替代正式研究、原始证据、审计结论或离线核验。本报告不构成交易指令。</p>
</section>'''


def replace_template(template: str, values: dict[str, str]) -> str:
    # Substitute only tokens present in the template, never tokens introduced
    # by report content or another replacement value.
    document = PLACEHOLDER_RE.sub(
        lambda match: values.get(match.group(0)[2:-2], match.group(0)), template
    )
    leftovers = PLACEHOLDER_RE.findall(document)
    if leftovers:
        raise ReportRenderError(f"report template has unresolved placeholders: {sorted(set(leftovers))}")
    return document


def build_document(
    parsed: ParsedReport,
    source_sha256: str,
    *,
    template: str,
    style: str,
    script: str,
    audit: dict[str, Any] | list[Any] | None,
    evidence: dict[str, Any] | list[Any] | None,
    revision: dict[str, Any] | None,
    archive_manifest: dict[str, Any] | list[Any] | None,
    charts: bool,
) -> tuple[str, int]:
    tables: list[MarkdownTable] = []
    visible_text: list[str] = []
    rendered = markdown_to_html(parsed.markdown_body, chart_tables=tables, visible_text=visible_text)
    # Derived summaries must use visible prose, never comments or code examples.
    parsed = replace(parsed, source_text=parsed.title + "\n" + "\n".join(visible_text))
    rendered = decorate_text_nodes(rendered)
    rendered = wrap_tables(rendered)
    rendered, headings = decorate_headings(rendered)
    # Keep the entire opening conclusion, including citations, exactly once.
    # Its place is before the data spread; subsequent sections retain their order.
    lead = ""
    conclusion = (
        re.match(r'(<h2\b[^>]*>.*?</h2>.*?)(?=<h2\b|\Z)', rendered, re.DOTALL)
        if headings and headings[0][1] == "结论" else None
    )
    if conclusion:
        lead = conclusion.group(1)
        rendered = rendered[conclusion.end():]
    visual_parts: list[str] = []
    if charts:
        context = ChartContext(parsed=parsed, tables=tables, evidence=evidence)
        visual_parts = build_visual_parts(context)
    # 首屏主图固定收录注册表前两位图表（财务趋势 + 估值情景）；缺输入静默降级时，
    # 后续扩展图表不得漂移进主视图改变其组成。
    primary_parts, extended_parts = [], []
    for part in visual_parts:
        target = primary_parts if re.search(
            r'data-chart="(?:financial-trends|valuation-scenarios)"', part
        ) else extended_parts
        target.append(part)
    visual_summary = (
        '<section class="visual-summary" aria-label="核心数据视图">'
        + "".join(primary_parts)
        + "</section>"
        if primary_parts
        else ""
    )
    visual_extended = (
        '<section class="visual-extended" aria-label="扩展数据视图">'
        + "".join(extended_parts)
        + "</section>"
        if extended_parts
        else ""
    )
    description = conclusion_text(parsed)
    document = replace_template(
        template,
        {
            "TITLE": html.escape(parsed.title),
            "DESCRIPTION": html.escape(description, quote=True),
            "SOURCE_SHA256": source_sha256,
            "STYLE": style,
            "SCRIPT": script,
            "MASTHEAD": build_masthead(parsed, revision),
            "NAVIGATION": build_navigation(headings),
            "DECISION_BRIEF": build_decision_brief(parsed),
            "LEAD": lead,
            "VISUAL_SUMMARY": visual_summary,
            "VISUAL_EXTENDED": visual_extended,
            "ARTICLE": rendered,
            "AUDIT_SEAL": build_audit_seal(
                source_sha256, audit, evidence, revision, archive_manifest
            ),
            "FOOTER_META": html.escape(print_identity(parsed)),
        },
    )
    return document, len(visual_parts)


class ResourceAttributeAudit(HTMLParser):
    """Inspect decoded attributes; plain source citations are not dependencies."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.dependency_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name not in {"href", "xlink:href", "src", "srcset", "poster", "action", "formaction", "ping", "background"} and not (tag == "object" and name == "data"):
                continue
            address = (value or "").strip()
            if name in {"href", "xlink:href"} and address.startswith("#"):
                continue
            if name in {"src", "href", "xlink:href"} and re.fullmatch(
                r"data:image/(?:png|jpeg|gif|webp);base64,[A-Za-z0-9+/=\s]+", address, re.IGNORECASE
            ):
                continue
            self.dependency_count += 1


def verify_html_text(
    document: str, *, source_sha256: str | None = None, expected_report: ParsedReport | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if '<meta name="offline-portable" content="true">' not in document:
        errors.append("HTML does not declare offline portability")
    if '<meta name="generator" content="Money Craft">' not in document:
        errors.append("HTML does not declare the Money Craft generator")
    resource_audit = ResourceAttributeAudit()
    resource_audit.feed(document)
    resource_audit.close()
    if resource_audit.dependency_count:
        errors.append("HTML contains a nonportable resource or navigation attribute")
    if re.search(r"<script[^>]+\bsrc\s*=|<link[^>]+\bhref\s*=", document, re.IGNORECASE):
        errors.append("HTML contains an external script or stylesheet reference")
    placeholders = PLACEHOLDER_RE.findall(document)
    if placeholders:
        errors.append(f"HTML contains {len(placeholders)} unresolved placeholders")
    if "<main" not in document or "<nav" not in document or "<article" not in document:
        errors.append("HTML is missing report landmarks")
    embedded_hash = first_match(
        document,
        (r'<meta\s+name="money-craft-source-sha256"\s+content="([0-9a-f]{64})"',),
    )
    if source_sha256 and embedded_hash != source_sha256:
        errors.append("HTML source hash does not match canonical Markdown")
    if expected_report is not None:
        for attribute, expected in (("data-report-date", report_date(expected_report)),
                                    ("data-data-cutoff", data_cutoff(expected_report))):
            observed = re.search(rf'<time\s+{attribute}>(.*?)</time>', document)
            if expected != "UNSPECIFIED" and (observed is None or html.unescape(observed.group(1)) != expected):
                errors.append(f"HTML {attribute} does not match canonical Markdown")
    return {
        "schema": VERIFY_SCHEMA,
        "valid": not errors,
        "portable_html": not errors,
        "source_sha256": embedded_hash,
        "external_dependency_count": resource_audit.dependency_count,
        "placeholder_count": len(placeholders),
        "errors": errors,
    }


def pdf_page_count(path: Path) -> int:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ReportRenderError(
            "PDF verification requires the optional `pypdf` package; run with the configured report-render environment"
        ) from exc
    return len(PdfReader(str(path)).pages)


def write_pdf(html_path: Path, pdf_path: Path) -> int:
    try:
        from weasyprint import HTML  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ReportRenderError(
            "PDF rendering requires the optional `weasyprint` package; run with the configured report-render environment"
        ) from exc
    HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(str(pdf_path))
    if not pdf_path.is_file() or not pdf_path.read_bytes().startswith(b"%PDF"):
        raise ReportRenderError("PDF renderer did not produce a valid PDF header")
    return pdf_page_count(pdf_path)


def validate_output_separation(inputs: Iterable[Path], outputs: Iterable[Path]) -> None:
    """Reject path aliases before render outputs can modify their inputs."""
    input_paths = list(inputs)
    output_paths = list(outputs)
    def aliases(left: Path, right: Path) -> bool:
        return left.resolve() == right.resolve() or (
            left.exists() and right.exists() and left.samefile(right)
        )
    for index, output in enumerate(output_paths):
        if any(aliases(output, source) for source in input_paths):
            raise ReportRenderError("render output must not alias any report input")
        if any(aliases(output, other) for other in output_paths[:index]):
            raise ReportRenderError("HTML and PDF outputs must be distinct files")


def render_report(
    source: Path,
    *,
    output_html: Path,
    output_pdf: Path | None,
    template_path: Path = DEFAULT_TEMPLATE,
    style_path: Path = DEFAULT_STYLE,
    script_path: Path = DEFAULT_SCRIPT,
    evidence_manifest: Path | None = None,
    audit_path: Path | None = None,
    revision_manifest: Path | None = None,
    archive_manifest: Path | None = None,
    charts: bool = True,
    requested_theme: str = CANONICAL_THEME,
) -> dict[str, Any]:
    paths = (
        (source, "source"),
        (template_path, "template"),
        (style_path, "style"),
        (script_path, "script"),
    )
    for path, label in paths:
        if not path.is_file():
            raise ReportRenderError(f"{label} not found: {path}")
    for optional, label in (
        (evidence_manifest, "evidence manifest"),
        (audit_path, "audit"),
        (revision_manifest, "revision manifest"),
        (archive_manifest, "archive manifest"),
    ):
        if optional is not None and not optional.is_file():
            raise ReportRenderError(f"{label} not found: {optional}")
    if requested_theme != CANONICAL_THEME:
        raise ReportRenderError(
            f"unsupported theme `{requested_theme}`; Money Craft reports use exactly `{CANONICAL_THEME}`"
        )

    validate_output_separation(
        [*(path for path, _label in paths),
         *(path for path in (evidence_manifest, audit_path, revision_manifest, archive_manifest) if path is not None)],
        [output_html, *([output_pdf] if output_pdf is not None else [])],
    )
    source_sha_before = sha256_file(source)
    try:
        source_text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ReportRenderError(f"cannot read report source {source}: {exc}") from exc
    parsed = parse_report(source_text)
    audit = load_json(audit_path)
    evidence = load_json(evidence_manifest)
    revision_payload = load_json(revision_manifest)
    archive_payload = load_json(archive_manifest)
    revision = revision_payload if isinstance(revision_payload, dict) else None
    document, chart_count = build_document(
        parsed,
        source_sha_before,
        template=template_path.read_text(encoding="utf-8"),
        style=style_path.read_text(encoding="utf-8"),
        script=script_path.read_text(encoding="utf-8"),
        audit=audit,
        evidence=evidence,
        revision=revision,
        archive_manifest=archive_payload,
        charts=charts,
    )
    verification = verify_html_text(document, source_sha256=source_sha_before, expected_report=parsed)
    if not verification["valid"]:
        raise ReportRenderError(f"portable HTML verification failed: {verification['errors']}")

    output_html.parent.mkdir(parents=True, exist_ok=True)
    pages = None
    with contextlib.ExitStack() as staging:
        html_directory = Path(staging.enter_context(tempfile.TemporaryDirectory(
            prefix=".money-craft-render-", dir=output_html.parent
        )))
        staged_html = html_directory / output_html.name
        staged_html.write_text(document, encoding="utf-8")
        staged_pdf = None
        if output_pdf is not None:
            output_pdf.parent.mkdir(parents=True, exist_ok=True)
            pdf_directory = Path(staging.enter_context(tempfile.TemporaryDirectory(
                prefix=".money-craft-render-", dir=output_pdf.parent
            )))
            staged_pdf = pdf_directory / output_pdf.name
            pages = write_pdf(staged_html, staged_pdf)
        source_sha_after = sha256_file(source)
        if source_sha_before != source_sha_after:
            raise ReportRenderError("canonical Markdown changed during report rendering")
        asset_hashes = {"template": sha256_file(template_path), "style": sha256_file(style_path), "script": sha256_file(script_path)}
        # Each replacement is atomic; the HTML/PDF pair is not a transaction.
        os.replace(staged_html, output_html)
        if staged_pdf is not None:
            os.replace(staged_pdf, output_pdf)

    return {
        "schema": RENDER_SCHEMA,
        "valid": True,
        "source": str(source),
        "source_sha256": source_sha_after,
        "template": str(template_path),
        "template_sha256": asset_hashes["template"],
        "style": str(style_path),
        "style_sha256": asset_hashes["style"],
        "script": str(script_path),
        "script_sha256": asset_hashes["script"],
        "theme": CANONICAL_THEME,
        "requested_theme": requested_theme,
        "theme_label": THEME_LABEL,
        "layout_mode": LAYOUT_MODE,
        "portable_html": True,
        "title": parsed.title,
        "html": str(output_html),
        "pdf": str(output_pdf) if output_pdf else None,
        "pages": pages,
        "html_bytes": output_html.stat().st_size,
        "pdf_bytes": output_pdf.stat().st_size if output_pdf else None,
        "placeholders": verification["placeholder_count"],
        "external_dependencies": verification["external_dependency_count"],
        "charts": chart_count,
        "network_used": False,
    }


def resolve_output_paths(
    source: Path,
    *,
    output_dir: Path | None,
    output_html: Path | None,
    output_pdf: Path | None,
    html_only: bool,
) -> tuple[Path, Path | None]:
    if output_dir is None and output_html is None and output_pdf is None:
        raise ReportRenderError(
            "report rendering requires an explicit --output-dir, --output-html, or --output-pdf; "
            "canonical research directories are never implicit render targets"
        )
    if html_only and output_pdf is not None:
        raise ReportRenderError("--html-only cannot be combined with --output-pdf")
    explicit_output = output_html or output_pdf
    if output_dir is None and explicit_output is None:
        raise ReportRenderError("explicit report output resolution failed")
    resolved_dir = (
        output_dir.expanduser().resolve()
        if output_dir is not None
        else explicit_output.expanduser().resolve().parent
    )
    resolved_html = (
        output_html.expanduser().resolve()
        if output_html is not None
        else resolved_dir / f"{source.stem}.html"
    )
    resolved_pdf = None
    if not html_only:
        resolved_pdf = (
            output_pdf.expanduser().resolve()
            if output_pdf is not None
            else resolved_dir / f"{source.stem}.pdf"
        )
    return resolved_html, resolved_pdf


def verify_rendered_report(source: Path, html_path: Path, pdf_path: Path | None) -> dict[str, Any]:
    errors: list[str] = []
    if not source.is_file():
        errors.append(f"source not found: {source}")
        source_sha = None
    else:
        source_sha = sha256_file(source)
    if not html_path.is_file():
        errors.append(f"HTML not found: {html_path}")
        html_result = None
    else:
        html_result = verify_html_text(
            html_path.read_text(encoding="utf-8"), source_sha256=source_sha,
            expected_report=parse_report(source.read_text(encoding="utf-8")) if source.is_file() else None,
        )
        errors.extend(html_result["errors"])
    pages = None
    if pdf_path is not None:
        if not pdf_path.is_file() or not pdf_path.read_bytes().startswith(b"%PDF"):
            errors.append(f"PDF is missing or invalid: {pdf_path}")
        else:
            pages = pdf_page_count(pdf_path)
            if pages < 1:
                errors.append("PDF has no pages")
    return {
        "schema": VERIFY_SCHEMA,
        "valid": not errors,
        "source": str(source),
        "source_sha256": source_sha,
        "html": str(html_path),
        "pdf": str(pdf_path) if pdf_path else None,
        "pages": pages,
        "portable_html": bool(html_result and html_result["portable_html"]),
        "network_required": False,
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--output-html", type=Path)
    parser.add_argument("--output-pdf", type=Path)
    parser.add_argument("--html-only", action="store_true")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--style", type=Path, default=DEFAULT_STYLE)
    parser.add_argument("--script", type=Path, default=DEFAULT_SCRIPT)
    parser.add_argument("--theme", default=CANONICAL_THEME)
    parser.add_argument("--layout-mode", default=LAYOUT_MODE)
    parser.add_argument("--author", default="Money Craft")
    parser.add_argument("--evidence-manifest", type=Path)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--revision-manifest", type=Path)
    parser.add_argument("--archive-manifest", type=Path)
    parser.add_argument("--no-charts", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    try:
        output_html, output_pdf = resolve_output_paths(
            source,
            output_dir=args.output_dir,
            output_html=args.output_html,
            output_pdf=args.output_pdf,
            html_only=args.html_only,
        )
        result = render_report(
            source,
            output_html=output_html,
            output_pdf=output_pdf,
            template_path=args.template.expanduser().resolve(),
            style_path=args.style.expanduser().resolve(),
            script_path=args.script.expanduser().resolve(),
            evidence_manifest=args.evidence_manifest.expanduser().resolve()
            if args.evidence_manifest
            else None,
            audit_path=args.audit.expanduser().resolve() if args.audit else None,
            revision_manifest=args.revision_manifest.expanduser().resolve()
            if args.revision_manifest
            else None,
            archive_manifest=args.archive_manifest.expanduser().resolve()
            if args.archive_manifest
            else None,
            charts=not args.no_charts,
            requested_theme=args.theme,
        )
    except (OSError, UnicodeDecodeError, ReportRenderError) as exc:
        print(
            json.dumps(
                {
                    "schema": RENDER_SCHEMA,
                    "valid": False,
                    "error": {"kind": "report_render_failed", "message": str(exc)},
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
