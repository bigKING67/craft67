#!/usr/bin/env python3
"""Deterministic rubric smoke scorer for saved commerce-growth-os answers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from lint_answer import is_negated_context, term_occurrences


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = ROOT / "eval" / "cases.json"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("eval cases must contain a non-empty cases list")
    seen: set[str] = set()
    for case in cases:
        case_id = case.get("id")
        if not case_id or not re.fullmatch(r"[a-z0-9_]+", case_id):
            raise ValueError(f"invalid case id: {case_id!r}")
        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        required_groups = case.get("required_groups")
        if not isinstance(required_groups, list) or not required_groups:
            raise ValueError(f"{case_id}: required_groups must be non-empty")
        for group in required_groups:
            if not isinstance(group, list) or not group or not all(isinstance(term, str) for term in group):
                raise ValueError(f"{case_id}: each required group must be a non-empty string list")
        forbidden_terms = case.get("forbidden_terms", [])
        if not isinstance(forbidden_terms, list) or not all(isinstance(term, str) and term.strip() for term in forbidden_terms):
            raise ValueError(f"{case_id}: forbidden_terms must be a non-empty-string list")
    return cases


def score_answer(case: dict[str, Any], answer: str) -> dict[str, Any]:
    text = normalize(answer)
    required_groups = case["required_groups"]
    matched: list[list[str]] = []
    missing: list[list[str]] = []
    for group in required_groups:
        normalized_group = [normalize(term) for term in group]
        if any(term in text for term in normalized_group):
            matched.append(group)
        else:
            missing.append(group)

    forbidden = [
        term
        for term in case.get("forbidden_terms", [])
        if any(not is_negated_context(answer, idx)
               for _, idx in term_occurrences(answer, [term]))
    ]
    score = len(matched) / len(required_groups)
    passed = score >= case.get("min_score", 0.75) and not forbidden
    return {
        "id": case["id"],
        "score": round(score, 4),
        "passed": passed,
        "matched": matched,
        "missing": missing,
        "forbidden": forbidden,
    }


def score_answer_dir(cases: list[dict[str, Any]], answer_dir: Path) -> dict[str, Any]:
    results = []
    for case in cases:
        answer_file = answer_dir / f"{case['id']}.txt"
        if not answer_file.exists():
            results.append(
                {
                    "id": case["id"],
                    "score": 0.0,
                    "passed": False,
                    "missing_answer_file": str(answer_file),
                }
            )
            continue
        results.append(score_answer(case, answer_file.read_text(encoding="utf-8")))
    return {
        "cases": results,
        "passed": all(result.get("passed") for result in results),
    }


def self_test(cases: list[dict[str, Any]]) -> None:
    by_id = {case["id"]: case for case in cases}
    qianchuan = by_id["qianchuan_budget_scale"]
    positive = """
    Decision: 不建议直接翻倍。ROI = 2.0, but break-even ROI is 2.702703.
    Gross-profit ROI and marginal traffic risk show the plan should be capped first.
    Stop rule: pause if ROI stays below break-even or refund worsens.
    Scale rule: only add budget after conversion and price-channel risk are stable.
    """
    for suffix, expected in (
        ("不要直接翻倍预算。", True),
        ("不应直接翻倍预算。", True),
        ('不要采用“直接翻倍预算”的建议。', True),
        ("建议直接翻倍预算。", False),
        ("不要犹豫，直接翻倍预算。", False),
        ('建议采用“直接翻倍预算”的方案。', False),
        ("不是不能直接翻倍预算。", False),
        ("不要直接翻倍预算。随后直接翻倍预算。", False),
    ):
        actual = score_answer(qianchuan, positive + "\n" + suffix)["passed"]
        if actual != expected:
            raise AssertionError(f"advice polarity mismatch: {suffix}: {actual}")
    try:
        score_answer({"id": "empty-term", "required_groups": [["Decision"]], "forbidden_terms": [""]}, positive)
    except ValueError:
        pass
    else:
        raise AssertionError("empty forbidden term must fail without looping")
    negative = "建议直接翻倍预算，因为ROI很好。"
    positive_score = score_answer(qianchuan, positive)
    negative_score = score_answer(qianchuan, negative)
    if not positive_score["passed"]:
        raise AssertionError(f"positive self-test should pass: {positive_score}")
    if negative_score["passed"]:
        raise AssertionError(f"negative self-test should fail: {negative_score}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Score saved commerce-growth-os eval answers.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Path to eval cases JSON")
    parser.add_argument("--list", action="store_true", help="List case ids and prompts")
    parser.add_argument("--case-id", help="Score one case by id; requires --answer")
    parser.add_argument("--answer", help="Path to an answer text file for --case-id")
    parser.add_argument("--answer-dir", help="Directory containing <case-id>.txt answer files")
    parser.add_argument("--self-test", action="store_true", help="Validate cases and scorer behavior")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--summary", action="store_true", help="Print only pass/fail counts for answer directories")
    args = parser.parse_args()

    try:
        cases = load_cases(Path(args.cases))
        if args.self_test:
            self_test(cases)
            print("commerce-growth-os eval scorer self-test passed.")
            return 0
        if args.list:
            for case in cases:
                print(f"{case['id']}\t{case.get('output_mode', '')}\t{case['prompt']}")
            return 0
        if args.case_id:
            if not args.answer:
                raise ValueError("--case-id requires --answer")
            case = next((candidate for candidate in cases if candidate["id"] == args.case_id), None)
            if case is None:
                raise ValueError(f"unknown case id: {args.case_id}")
            result = score_answer(case, Path(args.answer).read_text(encoding="utf-8"))
        elif args.answer_dir:
            result = score_answer_dir(cases, Path(args.answer_dir))
        else:
            result = {
                "cases": len(cases),
                "message": "cases loaded; use --list, --self-test, --case-id, or --answer-dir",
            }
        if args.summary and isinstance(result, dict) and "cases" in result:
            failed = [case["id"] for case in result["cases"] if not case.get("passed")]
            result = {
                "passed": result.get("passed", False),
                "cases": len(result["cases"]),
                "failed": failed,
            }
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        if isinstance(result, dict) and result.get("passed") is False:
            return 1
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should report clean errors.
        print(f"score_eval error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
