#!/usr/bin/env python3
"""Deterministic quality linter for saved commerce-growth-os answers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = ROOT / "eval" / "cases.json"

EMPTY_ADVICE_TERMS = [
    "提升品牌曝光",
    "优化内容",
    "加强运营",
    "加大投放",
    "提高转化率",
    "找更多达人",
    "多做种草",
    "冲GMV",
    "冲gmv",
    "做全域布局",
]

MECHANISM_TERMS = [
    "机制",
    "动作",
    "指标",
    "owner",
    "负责人",
    "止损",
    "放量",
    "review",
    "复盘",
    "metric",
    "stop rule",
    "scale rule",
]

SCALE_TERMS = [
    "加预算",
    "加大投放",
    "放量",
    "翻倍预算",
    "投千川",
    "开万相台",
    "book",
    "double the budget",
    "scale budget",
    "add budget",
]

TACTIC_TERMS = [
    "投千川",
    "做小红书",
    "找达人",
    "开直播",
    "开万相台",
    "聚光",
    "达人直播",
    "talent livestream",
    "paid media",
]

ECONOMICS_TERMS = [
    "channel net profit",
    "渠道净利润",
    "break-even",
    "盈亏平衡",
    "gross-profit roi",
    "毛利roi",
    "unit economics",
    "经济模型",
    "算账",
    "毛利",
    "利润",
    "refund",
    "退款",
    "margin",
]

STOP_TERMS = ["stop rule", "止损", "停止", "暂停", "cut", "pause"]
SCALE_RULE_TERMS = ["scale rule", "放量", "加预算规则", "扩大", "increase only", "scale only"]

CURRENT_WORDS = [
    "当前",
    "现在",
    "最新",
    "还能",
    "是否还能",
    "still",
    "current",
    "latest",
    "today",
]

PLATFORM_TERMS = [
    "千川",
    "万相台",
    "聚光",
    "蒲公英",
    "星图",
    "京准通",
    "多多进宝",
    "磁力",
    "视频号",
    "微信小店",
    "juguang",
    "qianchuan",
    "wanxiangtai",
]

EVIDENCE_LABELS = [
    "Confirmed from user backend",
    "Officially verified",
    "Stable operating principle",
    "Needs current verification",
    "已由用户后台确认",
    "官方已核验",
    "稳定原则",
    "需要当前核验",
]

UNIVERSAL_REQUIRED_GROUPS = [
    ["decision", "judgment", "结论", "判断", "建议", "不建议"],
    ["confirmed", "已确认", "evidence", "证据", "assumption", "假设", "置信", "需要核验", "稳定原则"],
    ["mechanism", "机制", "action", "动作", "sop", "流程", "步骤", "根因"],
    ["owner", "负责人", "责任人"],
    ["success signal", "completion signal", "验收", "成功标准", "目标", "指标", "阈值", "通过条件"],
    ["risk", "风险", "例外", "异常"],
    ["next review", "review window", "下次复盘", "下一决策", "复核", "复盘", "review cadence"],
]

MODE_REQUIRED_GROUPS = {
    "quick_diagnosis": [
        ["current judgment", "当前判断", "判断"],
        ["bottleneck", "瓶颈"],
        ["missing data", "缺失数据", "假设", "assumptions"],
        ["next three actions", "next 3 actions", "三个动作", "3个动作"],
        ["risk", "风险"],
    ],
    "decision_memo": [
        ["decision", "结论", "判断", "建议", "不建议"],
        ["assumptions", "假设", "confirmed facts", "已确认", "evidence", "证据", "条件"],
        ["mechanism", "机制", "action", "动作", "条件"],
        ["owner", "负责人", "责任人"],
        ["next review", "review window", "下次复盘", "下一决策", "复核", "复盘"],
        ["risk", "风险"],
    ],
    "full_operating_plan": [
        ["business model", "经营模型", "经济模型", "break-even", "盈亏平衡"],
        ["assortment", "货盘", "sku"],
        ["price ladder", "价盘", "价格线"],
        ["channel jobs", "渠道角色", "渠道分工"],
        ["content", "内容"],
        ["fulfillment", "履约", "after-sale", "售后", "refund", "退款"],
        ["review cadence", "复盘", "review loop"],
    ],
    "data_review": [
        ["metric movement", "指标变化", "数据变化"],
        ["likely cause", "可能原因", "原因"],
        ["decision", "结论", "决策"],
        ["owner", "负责人", "action", "动作"],
        ["next review", "下次复盘", "next week", "下周"],
    ],
}

DOMAIN_REQUIRED_GROUPS = {
    "commercial": [
        ["economics", "unit economics", "business model", "经营模型", "经济模型", "算账", "channel net profit", "渠道净利润", "盈亏平衡"],
        STOP_TERMS,
        SCALE_RULE_TERMS,
    ],
    "growth": [
        ["economics", "unit economics", "经济模型", "算账", "channel net profit", "渠道净利润", "break-even", "盈亏平衡", "边际"],
        STOP_TERMS,
        SCALE_RULE_TERMS,
    ],
    "operations": [
        ["exception", "例外", "异常"],
        ["escalation", "升级", "上报"],
        ["recovery", "恢复", "补救", "回滚"],
    ],
    "brand": [
        ["approval", "审批", "审核", "批准"],
        ["veto", "否决", "一票否决", "禁止"],
        ["exit", "退出", "终止"],
    ],
    "content": [
        ["quality gate", "质量门", "质检", "审核标准"],
        ["rights", "授权", "版权", "使用权"],
        ["refresh", "更新", "刷新", "迭代"],
    ],
    "analytics": [
        ["confidence", "置信", "可信度"],
        ["alternative explanation", "其他解释", "替代解释", "备选原因"],
        ["next evidence", "下一证据", "待补证据", "进一步验证"],
    ],
}

CONTRADICTORY_SCALE_PATTERNS = [
    re.compile(
        r"(?:scale|add budget|放量|加预算).{0,120}(?:even if|even when|即使|哪怕|仍).{0,80}"
        r"(?:unprofitable|loss|below break-even|亏损|低于盈亏平衡)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"(?:even if|even when|即使|哪怕).{0,80}(?:unprofitable|loss|below break-even|亏损|低于盈亏平衡)"
        r".{0,120}(?:scale|add budget|放量|加预算)",
        re.IGNORECASE | re.DOTALL,
    ),
]


def contains_any(text: str, terms: list[str]) -> bool:
    text_lower = text.lower()
    return any(term.lower() in text_lower for term in terms)


def term_occurrences(text: str, terms: list[str]) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    text_lower = text.lower()
    for term in terms:
        term_lower = term.lower()
        if not term_lower.strip():
            raise ValueError("advice terms must be non-empty")
        start = 0
        while True:
            idx = text_lower.find(term_lower, start)
            if idx < 0:
                break
            hits.append((term, idx))
            start = idx + len(term_lower)
    return hits


def is_negated_context(text: str, idx: int) -> bool:
    """Recognize explicit local rejection, never unrelated nearby negation.

    This is a lexical smoke check, not semantic understanding. Quotes alone do
    not exempt advice; a directly attached rejection is required.
    """
    prefix = re.split(r"[。！？!?;；\n,，]", text[:idx].lower())[-1]
    # Rejection of an explicitly quoted recommendation applies inside that quote.
    for opening, closing in (("“", "”"), ("‘", "’"), ('"', '"')):
        if opening == closing:
            inside = prefix.count(opening) % 2 == 1
        else:
            inside = prefix.rfind(opening) > prefix.rfind(closing)
        if inside:
            prefix = prefix[:prefix.rfind(opening)]
            break
    # Double negation is deliberately not interpreted as rejection.
    if re.search(r"(?:不是|并非|不能不|不得不|not not)", prefix):
        return False
    return bool(re.search(
        r"(?:不要|不能|不建议|不应当|不应该|不应|避免|禁止|拒绝|不讨论|不涉及|不|"
        r"\bavoid|\bdo not|\bdon't|\bnever)"
        r"(?:直接|再|继续|盲目|采用|建议|执行|讨论|考虑|打|做|的建议|\s|[‘“\"'])*$",
        prefix,
    ))


def add_finding(findings: list[dict[str, Any]], severity: str, code: str, message: str) -> None:
    findings.append({"severity": severity, "code": code, "message": message})


def load_case_modes(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("cases must be a list")
    modes: dict[str, str] = {}
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError("each case must have a string id")
        case_id = case["id"]
        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        mode = case.get("output_mode")
        if mode is None:
            continue
        if not isinstance(mode, str) or mode not in MODE_REQUIRED_GROUPS:
            raise ValueError(f"unknown output_mode for {case_id}: {mode!r}")
        modes[case_id] = mode
    return modes


def load_case_domains(path: Path) -> dict[str, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("cases must be a list")
    domains: dict[str, list[str]] = {}
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError("each case must have a string id")
        case_id = case["id"]
        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        if "primary_domain" in case and "contract_domain" in case:
            raise ValueError(f"use primary_domain, not both domain fields, for {case_id}")
        primary = case.get("primary_domain", case.get("contract_domain"))
        configured = case.get("contract_domains")
        if primary is None and configured is None:
            continue
        if not isinstance(primary, str) or primary not in DOMAIN_REQUIRED_GROUPS:
            raise ValueError(f"unknown primary_domain for {case_id}: {primary!r}")
        active = [primary] if configured is None else configured
        if (
            not isinstance(active, list)
            or not active
            or any(not isinstance(domain, str) or domain not in DOMAIN_REQUIRED_GROUPS for domain in active)
            or len(active) != len(set(active))
        ):
            raise ValueError(f"invalid contract_domains for {case_id}: {active!r}")
        if primary not in active:
            raise ValueError(f"contract_domains must include primary_domain for {case_id}")
        domains[case_id] = active
    return domains


def mode_from_source(source: str | None, case_modes: dict[str, str] | None) -> str | None:
    if not source or not case_modes:
        return None
    case_id = Path(source).stem
    return case_modes.get(case_id)


def domains_from_source(
    source: str | None, case_domains: dict[str, list[str]] | None
) -> list[str] | None:
    if not source or not case_domains:
        return None
    return case_domains.get(Path(source).stem)


def analysis_sections(text: str, title: str) -> list[str]:
    """Read actual Markdown section bodies, stopping at the next peer heading."""
    lines = text.splitlines()
    sections = []
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if not heading or title not in heading.group(2) or re.search(r"没有|不存在|未提供|不提供|不考虑|无需|无须", heading.group(2)) or is_negated_context(heading.group(2), heading.group(2).find(title)):
            continue
        end = index + 1
        while end < len(lines):
            next_heading = re.match(r"^(#{1,6})\s+", lines[end].strip())
            if next_heading and len(next_heading.group(1)) <= len(heading.group(1)):
                break
            end += 1
        sections.append("\n".join(lines[index + 1:end]))
    return sections


def has_required_element(text: str, group: list[str]) -> bool:
    if contains_any(text, group):
        return True
    if "metric movement" in group:
        return any(not re.search(r"不是|并非|没有|未披露|未提供", match.group())
                   and not is_negated_context(text, match.start())
                   and not re.search(r"(?:未报告|未提供|没有提供)\s*$", text[max(0, match.start() - 12):match.start()])
                   for match in re.finditer(
                       r"(?:GMV|ROI|转化率|退款损失率?|品牌词搜索)[^。\n]{0,28}"
                       r"(?:[+-]\d+(?:\.\d+)?%|\d+(?:\.\d+)?(?:%|个百分点|→|降至|升至))", text, re.IGNORECASE))
    if "confidence" in group:
        # Explicit provenance limitations plus hypothesis status express confidence
        # without requiring an arbitrary confidence score or section label.
        return bool(re.search(r"用户提供[^。\n]{0,20}(?:尚未|未经)[^。\n]{0,12}(?:校验|核验|验证)", text)
                    and re.search(r"(?:这些|上述)?解释(?:目前)?(?:均为|仅为)假设[，,；; ]+(?:不能|无法)(?:排序为|确定为|确认)(?:根因|因果)", text))
    if "alternative explanation" in group:
        return any(sum(not re.search(r"(?:不考虑|无需|不用|忽略|不提供|没有|不存在|未提供|不支持)", item)
                       for item in re.findall(r"^\s*\d+[.、]\s*(\S.{8,})$", body, re.MULTILINE)) >= 2
                   for body in analysis_sections(text, "可能解释"))
    if "next evidence" in group:
        return any(not is_negated_context(body, match.start())
                   and not re.search(r"(?:无需|不用|不必|不需要|没有|未曾|未|不)\s*$", body[max(0, match.start() - 12):match.start()])
                   for title in ("待验证", "待补", "数据质量校验")
                   for body in analysis_sections(text, title)
                   for match in re.finditer(r"(?:确认|核验|核查|统一|排除|补充|补齐)[^。\n]{0,40}"
                                            r"(?:口径|归因|GMV|ROI|订单|退款|分母|数据)", body, re.IGNORECASE))
    # Accept concrete descriptions without prescribing a section title. These
    # bounded lexical alternatives do not establish semantic completeness.
    if "mechanism" in group:
        pattern = (
            r"(?P<setup>设置|建立)[^。！？!?;；\n]{0,20}(?:对照|测试单元)|"
            r"(?:先|每轮|每日)[^。！？!?;；\n]{0,20}?(?P<act>核对|削减|重分配|核定)|"
            r"\b(?:set up|establish)\b.{0,30}\b(?:control group|test group)\b"
        )
        for match in re.finditer(pattern, text, re.IGNORECASE):
            index = match.start("setup") if match.group("setup") else (
                match.start("act") if match.group("act") else match.start())
            prefix = text[max(0, index - 12):index]
            if not (is_negated_context(text, index)
                    or prefix.endswith(("无需", "不用", "不必", "不需要", "没有", "未曾"))):
                return True
        return False
    if "risk" in group:
        pattern = (
            r"(?:若|如果|一旦)[^。！？!?;；\n]{0,60}?(?P<bad>亏损|损失|无法履约|断货|违规)|"
            r"\bif\b[^。！？!?;；\n]{0,60}?\b(?P<bad_en>loss|losses|stockout|unprofitable)\b"
        )
        for match in re.finditer(pattern, text, re.IGNORECASE):
            outcome = match.start("bad") if match.group("bad") else match.start("bad_en")
            prefix = text[max(0, outcome - 12):outcome].lower()
            if not (is_negated_context(text, match.start())
                    or re.search(r"(?:(?:不|不会|没有|无)(?:产生|造成|出现)?(?:任何|明显|实际|经济|额外|重大|新的|的){0,2}|\bno\s|\bnot\s)$", prefix)):
                return True
    return False


def unlabeled_platform_current_claim(text: str) -> bool:
    capabilities = (
        "竞品词", "关键词定向", "后台入口", "后台字段", "归因字段", "归因窗口",
        "费率", "准入资格", "投放资格", "开户资格", "平台规则", "功能", "上线", "下线",
        "supports", "available", "eligibility", "fee rate", "attribution window",
        "reporting field", "platform policy",
    )
    # Bind currentness to capability/rule language in the same paragraph.
    # A platform mentioned elsewhere plus 'current ROI' is not such a claim.
    platform_heading_level: int | None = None
    for block in re.split(r"\n\s*\n", text):
        for line in block.splitlines():
            heading = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if heading:
                level = len(heading.group(1))
                if contains_any(heading.group(2), PLATFORM_TERMS):
                    platform_heading_level = level
                elif platform_heading_level is not None and level <= platform_heading_level:
                    platform_heading_level = None
        if (contains_any(block, CURRENT_WORDS)
            and (contains_any(block, PLATFORM_TERMS) or platform_heading_level is not None)
            and (contains_any(block, capabilities) or re.search(r"(?:支持|可用).{0,20}(?:关键词|定向|归因|搜索|竞价|投放|广告|直播|开户|账户)", block))
            and not contains_any(block, [label for label in EVIDENCE_LABELS if "stable" not in label.lower() and "稳定" not in label])):
            sentences = [part.strip() for part in re.split(r"[。！？!?，,；;\n]", block) if part.strip()]
            relevant = [part for part in sentences if contains_any(part, capabilities)]
            if relevant and all(
                re.search(r"(?:未|没有)(?:引用|核验|确认)[^。]{0,25}(?:功能|规则)", part)
                or (not re.search(r"无需|无须|不用|不必|不需要", part)
                    and re.search(r"(?:需|须|待)[^。]{0,30}(?:核验|核查|确认|后台[^。]{0,10}为准)", part))
                for part in relevant
            ):
                continue
            return True
    return False


def lint_required_groups(
    findings: list[dict[str, Any]],
    text: str,
    required_groups: list[list[str]],
    contract: str,
) -> None:
    if not required_groups:
        return
    missing = [
        group
        for group in required_groups
        if not has_required_element(text, group)
    ]
    for group in missing:
        add_finding(
            findings,
            "error",
            f"{contract}_missing_required_element",
            f"{contract} required element missing: " + " / ".join(group),
        )


def lint_answer(
    answer: str,
    source: str | None = None,
    mode: str | None = None,
    domain: str | list[str] | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    text = answer.strip()
    text_lower = text.lower()

    if not text:
        add_finding(findings, "error", "empty_answer", "Answer is empty.")
        return {"source": source, "passed": False, "findings": findings}

    empty_hits = [
        term
        for term, idx in term_occurrences(text, EMPTY_ADVICE_TERMS)
        if not is_negated_context(text, idx)
    ]
    if empty_hits and not contains_any(text, MECHANISM_TERMS):
        add_finding(
            findings,
            "error",
            "empty_advice_without_mechanism",
            "Empty advice phrase found without mechanism, owner, success signal, material risk, or review decision: "
            + ", ".join(sorted(set(empty_hits))),
        )

    if any(not is_negated_context(text, idx) for _, idx in term_occurrences(text, SCALE_TERMS)):
        if not contains_any(text, ECONOMICS_TERMS):
            add_finding(
                findings,
                "error",
                "scale_without_economics",
                "Scale/budget/live recommendation appears without unit economics or profit terms.",
            )
        if not contains_any(text, STOP_TERMS):
            add_finding(
                findings,
                "error",
                "scale_without_stop_rule",
                "Scale/budget/live recommendation appears without a stop rule.",
            )
        if not contains_any(text, SCALE_RULE_TERMS):
            add_finding(
                findings,
                "error",
                "scale_without_scale_rule",
                "Scale/budget/live recommendation appears without a scale rule.",
            )

    if contains_any(text, TACTIC_TERMS) and not contains_any(text, ECONOMICS_TERMS):
        add_finding(
            findings,
            "warning",
            "tactic_without_economics",
            "Platform tactic appears without economics terms; verify the answer explains why profit still works.",
        )

    if unlabeled_platform_current_claim(text):
        add_finding(
            findings,
            "error",
            "currentness_without_evidence_label",
            "Platform-current claim appears without an evidence label.",
        )

    decision_terms = ["建议", "不建议", "should", "decision", "结论", "判断"]
    missing_data_terms = ["缺", "missing", "不知道", "只有", "仅知道", "不完整"]
    assumption_terms = ["假设", "assumption", "confirmed facts", "已确认", "条件"]
    if contains_any(text, decision_terms) and contains_any(text, missing_data_terms):
        if not contains_any(text, assumption_terms):
            add_finding(
                findings,
                "error",
                "missing_data_without_assumptions",
                "Decision with missing data should separate confirmed facts, assumptions, and conditions.",
            )

    if "roi" in text_lower and not contains_any(text, ["break-even", "盈亏平衡", "毛利roi", "gross-profit roi"]):
        add_finding(
            findings,
            "warning",
            "roi_without_break_even_context",
            "ROI is mentioned without break-even or gross-profit ROI context.",
        )

    if any(
        True
        for clause in re.finditer(r"[^。！？!?;；\n]+", text)
        for pattern in CONTRADICTORY_SCALE_PATTERNS
        for match in pattern.finditer(clause.group())
        if not is_negated_context(clause.group(), match.start())
        and not is_negated_context(
            clause.group(),
            match.start() + list(re.finditer(r"scale|add budget|放量|加预算", match.group(), re.IGNORECASE))[-1].start(),
        )
    ):
        add_finding(
            findings,
            "error",
            "contradictory_scale_rule",
            "Scale recommendation contradicts the stated loss or break-even guardrail.",
        )

    lint_required_groups(findings, text, UNIVERSAL_REQUIRED_GROUPS, "universal")
    if mode:
        lint_required_groups(findings, text, MODE_REQUIRED_GROUPS.get(mode, []), mode)
    active_domains = [domain] if isinstance(domain, str) else (domain or [])
    for active_domain in active_domains:
        lint_required_groups(
            findings,
            text,
            DOMAIN_REQUIRED_GROUPS.get(active_domain, []),
            active_domain,
        )

    passed = not any(finding["severity"] == "error" for finding in findings)
    return {
        "source": source,
        "mode": mode,
        "domain": active_domains[0] if active_domains else None,
        "domains": active_domains,
        "passed": passed,
        "findings": findings,
    }


def lint_answer_dir(
    answer_dir: Path,
    case_modes: dict[str, str] | None = None,
    mode: str | None = None,
    case_domains: dict[str, list[str]] | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    files = sorted(answer_dir.glob("*.txt"))
    if not files:
        return {
            "answer_dir": str(answer_dir),
            "passed": False,
            "findings": [
                {
                    "severity": "error",
                    "code": "missing_answer_files",
                    "message": "No .txt answer files found.",
                }
            ],
            "answers": [],
        }
    answers = [
        lint_answer(
            path.read_text(encoding="utf-8"),
            str(path),
            mode or mode_from_source(str(path), case_modes),
            domain or domains_from_source(str(path), case_domains),
        )
        for path in files
    ]
    return {
        "answer_dir": str(answer_dir),
        "passed": all(answer["passed"] for answer in answers),
        "answers": answers,
    }


def self_test() -> None:
    analytics = (ROOT / "eval/regression-answers/analytics_scope_owner.txt").read_text(encoding="utf-8")
    result = lint_answer(analytics, domain="analytics", mode="data_review")
    if not result["passed"]:
        raise AssertionError(f"real analytics evidence descriptions should pass: {result}")
    probes = [
        (["metric movement"], "| GMV | +35% |", True),
        (["metric movement"], "GMV 很重要，但未提供变化。", False),
        (["metric movement"], "未报告 GMV +35%。", False),
        (["metric movement"], "GMV 不是 +35%，而是未披露。", False),
        (["confidence"], "用户提供的口径尚未经底表校验。解释绝非均为假设，不能忽略已确认的因果。", False),
        (["alternative explanation"], "## 这里没有可能解释\n1. 新客比例变化导致汇总转化下降。\n2. 退款成熟度不同导致暂时失真。", False),
        (["alternative explanation"], "## 可能解释\n1. 目前没有证据支持新客比例变化。\n2. 目前没有证据支持退款成熟度变化。", False),
        (["next evidence"], "## 待验证\n没有补充任何归因数据。", False),
        (["confidence"], "用户提供，尚未经底表校验。解释目前均为假设，不能排序为根因。", True),
        (["confidence"], "已知事实，所有原因都已经确定。", False),
        (["confidence"], "解释目前均为假设。", False),
        (["alternative explanation"], "## 可能解释\n1. 新客比例变化导致汇总转化下降。\n2. 退款成熟度不同导致暂时失真。", True),
        (["alternative explanation"], "## 可能解释\n\n## 决策\n1. 明天检查全部指标变化。\n2. 后天召开业务复盘会议。", False),
        (["alternative explanation"], "## 可能解释\n1. 不考虑新客比例变化影响转化。\n2. 忽略退款成熟度造成的变化。", False),
        (["next evidence"], "## 周一数据质量校验\n确认两周归因窗口和退款成熟度。", True),
        (["next evidence"], "## 周一数据质量校验\n无需确认任何归因窗口和数据。", False),
        (["next evidence"], "## 待验证\n明天继续努力。", False),
    ]
    for group, sample, expected in probes:
        if has_required_element(sample, group) != expected:
            raise AssertionError(f"analytics lexical boundary mismatch: {sample}")
    for sample, expected in [
        ("当前性说明：未引用平台当前功能或规则。千川归因窗口需以企业当前后台导出为准。", False),
        ("当前聚光支持竞品词拦截。千川归因窗口需以企业当前后台导出为准。", True),
        ("千川当前归因窗口已确定。", True),
        ("当前聚光支持竞品词，库存数据需核验。", True),
        ("稳定原则：预算按贡献利润。当前聚光支持竞品词。", True),
        ("当前聚光支持竞品词，无需核验。", True),
    ]:
        if unlabeled_platform_current_claim(sample) != expected:
            raise AssertionError(f"pending evidence scope mismatch: {sample}")
    fixture = ROOT / "eval/regression-answers/commercial_smoke.txt"
    result = lint_answer(fixture.read_text(encoding="utf-8"), domain="commercial", mode="decision_memo")
    if not result["passed"]:
        raise AssertionError(f"real answer semantic equivalents should pass lexical checks: {result}")
    for text, expected in (
        ("千川上月消耗15万元。当前ROI为2.0。", False),
        ("当前千川ROI为2.0，不支持翻倍预算。", False),
        ("聚光现在支持竞品词拦截。", True),
        ("聚光当前后台字段为自动归因。", True),
        ("当前千川平台规则已更改。", True),
        ("## 聚光\n\n当前支持竞品词拦截。", True),
        ("当前千川支持全域投放。", True),
        ("当前千川ROI为2.0，负责人需核对履约资格。", False),
        ("## 聚光\n\n## 财务\n\n当前支持预算安排。", False),
        ("当前聚光支持搜索定向。需要当前核验。", False),
        ("稳定原则：预算按贡献利润。\n\n当前聚光支持竞品词。", True),
    ):
        if unlabeled_platform_current_claim(text) != expected:
            raise AssertionError(f"currentness scope mismatch: {text}")
    for group, positive_description in (
        (["mechanism", "机制"], "设置对照单元和测试单元，每轮核定预算。"),
        (["risk", "风险"], "若退款上升，亏损会进一步扩大。"),
    ):
        if not has_required_element(positive_description, group):
            raise AssertionError("concrete description should not require a heading")
        for empty in ("销量很好，下月继续。", "这里不提供任何说明。", "不要设置对照单元。", "若退款上升也不会亏损。", "每日无需核对。", "若有问题明天再说。目前没有亏损。", "没有设置对照单元。", "如果不会产生任何亏损，就保持现状。"):
            findings = []
            lint_required_groups(findings, empty, [group], "probe")
            if not findings:
                raise AssertionError("missing mechanism/risk must remain an error")

    positive = """
    Decision: 不建议直接翻倍预算。
    Confirmed facts: ROI 2.0, gross margin 55%.
    Assumptions: fulfillment and refund remain stable next week.
    Economics: channel net profit and break-even ROI must be checked before scale.
    Action: keep spend flat. Owner: growth lead.
    Success signal: marginal ROI remains above break-even and refund loss stays within threshold.
    Risk: marginal traffic, refund loss, and price-channel conflict can break profit.
    Stop rule: pause if marginal ROI stays below break-even or refund rises.
    Scale rule: add budget only after payment CVR and refund loss stabilize.
    Currentness:
    - Stable operating principle: budget follows contribution profit.
    - Needs current verification: exact Qianchuan backend product name and report field.
    Next review: after seven days of stable cohort evidence.
    """
    negative = "现在聚光还能做竞品词，建议加大投放、提高转化率、冲GMV。"
    positive_result = lint_answer(positive, "positive", mode="decision_memo", domain="growth")
    negative_result = lint_answer(negative, "negative", mode="decision_memo")
    if not positive_result["passed"]:
        raise AssertionError(f"positive self-test should pass: {positive_result}")
    if negative_result["passed"]:
        raise AssertionError(f"negative self-test should fail: {negative_result}")

    data_review = """
    Metric movement: order totals disagree across exports. Likely cause: source-grain mismatch.
    Decision: 数据质量不足，先暂停因果归因。
    Evidence: observed order totals disagree across exports.
    Mechanism: reconcile source grain and timezone. Owner: analytics lead.
    Success signal: totals reconcile within the stated threshold. Risk: false attribution.
    Confidence: low. Alternative explanation: delayed refunds. Next evidence: raw order ledger.
    Next review: after the ledger is reconciled.
    """
    if not lint_answer(data_review, "data-review", mode="data_review", domain="analytics")["passed"]:
        raise AssertionError("data-quality review must not invent stop/scale rules")

    polarity_base = (
        "Decision: reconcile exports. Evidence: totals disagree. Mechanism: reconcile source grain. "
        "Owner: analytics lead. Success signal: totals match. Risk: false attribution. "
        "Confidence: low. Alternative explanation: timezone mismatch. Next evidence: raw ledger. "
        "Next review: after reconciliation."
    )
    for suffix in ("本次不讨论放量。", "不要加预算。", '不要采用“加预算”的建议。'):
        if not lint_answer(polarity_base + "\n" + suffix, domain="analytics")["passed"]:
            raise AssertionError(f"explicit rejection must not require scale economics: {suffix}")
    for suffix in ("建议加预算。", "不要犹豫，加预算。", '建议采用“加预算”的方案。'):
        result = lint_answer(polarity_base + "\n" + suffix, domain="analytics")
        if "scale_without_stop_rule" not in {item["code"] for item in result["findings"]}:
            raise AssertionError(f"affirmative scale advice must retain guardrails: {suffix}")

    crisis = """
    Decision: hold the response until facts are confirmed. Evidence: only one complaint is verified.
    Mechanism: approval by the crisis owner before publication. Owner: communications lead.
    Success signal: approved holding statement and stakeholder log. Risk: amplifying an unverified claim.
    Veto: legal or safety conflict. Exit: close the response cell after recovery criteria pass.
    Next review: in two hours.
    """
    if not lint_answer(crisis, "crisis", domain="brand")["passed"]:
        raise AssertionError("crisis response must not invent a scale rule")

    missing_guardrails = """
    Decision: add budget. Evidence: ROI improved. Mechanism: paid-media expansion. Owner: growth lead.
    Success signal: more orders. Risk: refunds. Next review: next week. Economics: margin is positive.
    """
    if lint_answer(missing_guardrails, "paid", domain="growth")["passed"]:
        raise AssertionError("paid scale without stop and scale rules must fail")

    for rejection in ('不要采用“即使亏损也加预算”的建议。', "即使亏损也不要加预算。"):
        if any(item["code"] == "contradictory_scale_rule"
               for item in lint_answer(positive + "\n" + rejection)["findings"]):
            raise AssertionError(f"rejected loss-making scale advice is not contradictory: {rejection}")
    contradiction = positive + "\nScale rule: 即使亏损也加预算。"
    if lint_answer(contradiction, "contradiction", mode="decision_memo", domain="growth")["passed"]:
        raise AssertionError("logically contradictory scale rule must fail")

    multi_domain = positive + """
    Exception: isolate the affected orders. Escalation: service lead notifies operations.
    Recovery: reopen only after the refund cause and fulfillment capacity are verified.
    """
    if not lint_answer(multi_domain, "multi-domain", domain=["growth", "operations"])["passed"]:
        raise AssertionError("a multi-domain answer must satisfy every configured contract")
    if lint_answer(positive, "missing-operations", domain=["growth", "operations"])["passed"]:
        raise AssertionError("missing one configured domain contract must fail")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint commerce-growth-os saved answers.")
    parser.add_argument("--answer", help="Path to one answer text file")
    parser.add_argument("--answer-dir", help="Directory containing .txt answer files")
    parser.add_argument("--mode", choices=sorted(MODE_REQUIRED_GROUPS), help="Apply one output-mode gate")
    parser.add_argument("--domain", choices=sorted(DOMAIN_REQUIRED_GROUPS), help="Apply one domain-specific gate")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Cases JSON used to infer modes for --answer-dir")
    parser.add_argument("--self-test", action="store_true", help="Run linter self-test")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print("commerce-growth-os answer linter self-test passed.")
            return 0
        case_modes = load_case_modes(Path(args.cases)) if args.cases else None
        case_domains = load_case_domains(Path(args.cases)) if args.cases else None
        if args.answer:
            path = Path(args.answer)
            result = lint_answer(
                path.read_text(encoding="utf-8"),
                str(path),
                args.mode or mode_from_source(str(path), case_modes),
                args.domain or domains_from_source(str(path), case_domains),
            )
        elif args.answer_dir:
            result = lint_answer_dir(
                Path(args.answer_dir),
                case_modes,
                args.mode,
                case_domains,
                args.domain,
            )
        else:
            result = {"passed": True, "message": "use --answer, --answer-dir, or --self-test"}

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("commerce-growth-os answer lint passed." if result["passed"] else "commerce-growth-os answer lint failed.")
            for finding in result.get("findings", []):
                print(f"{finding['severity']}: {finding['code']}: {finding['message']}")
            for answer in result.get("answers", []):
                for finding in answer.get("findings", []):
                    print(f"{answer['source']}: {finding['severity']}: {finding['code']}: {finding['message']}")
        return 0 if result["passed"] else 1
    except Exception as exc:  # noqa: BLE001 - CLI should report clean errors.
        print(f"lint_answer error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
