#!/usr/bin/env python3
"""Run isolated Write Craft behavior evaluations through Pi.

The generator loads only the repository Skill and may use the read tool so the
Skill can open its progressive references. The judge runs in a fresh context
without tools or skills. Model calls are opt-in and never run in CI.
Models named `anthropic/<model>` or `claude-code/<model>` run through the local
Claude Code CLI instead of Pi; structured-tool reviews still require Pi.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.eval_contracts import (
        JUDGMENT_SCHEMA,
        READER_JUDGMENT_SCHEMA,
        READER_RESPONSE_SCHEMA,
        SCHEMA,
        SUPPORTED_SCHEMAS,
        VALID_STATUSES,
        VALID_SUITES,
        VALID_TRACKS,
        ContractError,
        aggregate_status,
        artifact_sources,
        canonical_json,
        case_sources,
        format_sources,
        han_character_count,
        resolve_fixture,
        resolved_case_digest,
        semantic_contract_errors,
        sha256_text,
    )
except ModuleNotFoundError:
    from eval_contracts import (  # type: ignore[no-redef]
        JUDGMENT_SCHEMA,
        READER_JUDGMENT_SCHEMA,
        READER_RESPONSE_SCHEMA,
        SCHEMA,
        SUPPORTED_SCHEMAS,
        VALID_STATUSES,
        VALID_SUITES,
        VALID_TRACKS,
        ContractError,
        aggregate_status,
        artifact_sources,
        canonical_json,
        case_sources,
        format_sources,
        han_character_count,
        resolve_fixture,
        resolved_case_digest,
        semantic_contract_errors,
        sha256_text,
    )


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "cases.json"
JUDGE_FIXTURES_PATH = ROOT / "evals" / "judge-fixtures.json"
SKILL_ROOT = ROOT / "skills" / "write-craft"
STRUCTURED_OUTPUT_EXTENSION = ROOT / "scripts" / "eval_structured_output.ts"
FACT_JUDGMENT_TOOL = "submit_fact_judgment"
READER_RESPONSE_TOOL = "submit_reader_response"
READER_JUDGMENT_TOOL = "submit_reader_judgment"
DEFAULT_RAW_JSONL_MAX_BYTES = 1_048_576
MIN_RAW_JSONL_MAX_BYTES = 256


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def candidate_limit_issues(case: dict[str, Any], candidate: str) -> list[str]:
    limits = case.get("limits")
    if not isinstance(limits, dict):
        return []
    maximum = limits.get("max_han_characters")
    if type(maximum) is not int or maximum < 1:
        return []
    actual = han_character_count(candidate)
    if actual <= maximum:
        return []
    return [
        f"完整输出包含 {actual} 个汉字，超过 max_han_characters={maximum}；"
        "标题、表格、附注和说明均计入"
    ]


def apply_deterministic_checks(
    judgment: dict[str, Any], case: dict[str, Any], candidate: str
) -> dict[str, Any]:
    issues = candidate_limit_issues(case, candidate)
    if not issues:
        return judgment
    blocking = judgment["blocking_issues"]
    for issue in issues:
        if issue not in blocking:
            blocking.append(issue)
    judgment["status"] = "FAIL"
    return judgment


def skill_digest(skill_root: Path = SKILL_ROOT) -> str:
    digest = hashlib.sha256()
    for path in sorted(skill_root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(skill_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def assistant_usage_summary(jsonl: str) -> dict[str, Any]:
    usage_keys = (
        "input",
        "output",
        "cacheRead",
        "cacheWrite",
        "cacheWrite1h",
        "reasoning",
        "totalTokens",
    )
    cost_keys = ("input", "output", "cacheRead", "cacheWrite", "total")
    summary: dict[str, Any] = {
        "responses": 0,
        "usage": {key: 0 for key in usage_keys},
        "cost": {key: 0.0 for key in cost_keys},
    }
    for line in jsonl.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("message") if isinstance(event, dict) else None
        if (
            not isinstance(message, dict)
            or event.get("type") != "message_end"
            or message.get("role") != "assistant"
        ):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        summary["responses"] += 1
        for key in usage_keys:
            value = usage.get(key, 0)
            if type(value) in {int, float}:
                summary["usage"][key] += value
        cost = usage.get("cost")
        if isinstance(cost, dict):
            for key in cost_keys:
                value = cost.get(key, 0)
                if type(value) in {int, float}:
                    summary["cost"][key] += value
    return summary


def merge_usage_summaries(*summaries: dict[str, Any]) -> dict[str, Any]:
    merged = assistant_usage_summary("")
    for summary in summaries:
        responses = summary.get("responses", 0)
        if type(responses) is int:
            merged["responses"] += responses
        for section in ("usage", "cost"):
            values = summary.get(section)
            if not isinstance(values, dict):
                continue
            for key in merged[section]:
                value = values.get(key, 0)
                if type(value) in {int, float}:
                    merged[section][key] += value
    return merged


def structured_output_metadata(
    tool_name: str | None = None, jsonl: str | None = None
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "transport": "pi_tool",
        "extension": STRUCTURED_OUTPUT_EXTENSION.relative_to(ROOT).as_posix(),
        "extension_sha256": hashlib.sha256(
            STRUCTURED_OUTPUT_EXTENSION.read_bytes()
        ).hexdigest(),
    }
    if tool_name:
        metadata["tool"] = tool_name
    if tool_name and jsonl is not None:
        metadata.update(
            {
                "tool_calls": 0,
                "successful_executions": 0,
                "failed_executions": 0,
            }
        )
        for line in jsonl.splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") == "message_end":
                message = event.get("message")
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, list):
                    metadata["tool_calls"] += sum(
                        1
                        for block in content
                        if isinstance(block, dict)
                        and block.get("type") == "toolCall"
                        and block.get("name") == tool_name
                    )
            elif (
                event.get("type") == "tool_execution_end"
                and event.get("toolName") == tool_name
            ):
                execution = event.get("result")
                failed = event.get("isError") is True or (
                    isinstance(execution, dict) and execution.get("isError") is True
                )
                if failed:
                    metadata["failed_executions"] += 1
                else:
                    metadata["successful_executions"] += 1
    return metadata


def evaluator_metadata() -> dict[str, Any]:
    paths = (
        ROOT / "scripts" / "eval_behavior.py",
        ROOT / "scripts" / "eval_contracts.py",
        STRUCTURED_OUTPUT_EXTENSION,
    )
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def validate_payload(payload: object, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["behavior cases must contain a JSON object"]
    schema = payload.get("schema")
    if schema not in SUPPORTED_SCHEMAS:
        errors.append(f"behavior cases schema must be one of {sorted(SUPPORTED_SCHEMAS)}")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["behavior cases must contain a non-empty cases array"]

    ids: set[str] = set()
    for index, case in enumerate(cases):
        label = f"case[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label} must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{label}.id must be a non-empty string")
            case_id = label
        elif case_id in ids:
            errors.append(f"duplicate behavior case id: {case_id}")
        else:
            ids.add(case_id)
        suite = case.get("suite")
        if suite not in VALID_SUITES:
            errors.append(f"{case_id}.suite must be one of {sorted(VALID_SUITES)}")
        track = case.get("track")
        if schema == SCHEMA and track not in VALID_TRACKS:
            errors.append(f"{case_id}.track must be one of {sorted(VALID_TRACKS)}")
        elif track is not None and track not in VALID_TRACKS:
            errors.append(f"{case_id}.track must be one of {sorted(VALID_TRACKS)}")
        tags = case.get("tags")
        if (
            not isinstance(tags, list)
            or not tags
            or not all(isinstance(tag, str) and tag.strip() for tag in tags)
            or len(tags) != len(set(tags))
        ):
            errors.append(f"{case_id}.tags must be unique non-empty strings")
        if not isinstance(case.get("request"), str) or not case["request"].strip():
            errors.append(f"{case_id}.request must be a non-empty string")
        limits = case.get("limits")
        if limits is not None and (
            not isinstance(limits, dict)
            or set(limits) != {"max_han_characters"}
            or type(limits.get("max_han_characters")) is not int
            or limits["max_han_characters"] < 1
        ):
            errors.append(
                f"{case_id}.limits must contain one positive max_han_characters integer"
            )
        max_revisions = case.get("max_revisions", 0)
        if type(max_revisions) is not int or max_revisions not in {0, 1}:
            errors.append(f"{case_id}.max_revisions must be 0 or 1")

        has_source = isinstance(case.get("source"), str) and bool(case["source"].strip())
        has_source_file = isinstance(case.get("source_file"), str) and bool(
            case["source_file"].strip()
        )
        has_sources = isinstance(case.get("sources"), list) and bool(case["sources"])
        if sum((has_source, has_source_file, has_sources)) != 1:
            errors.append(
                f"{case_id} must define exactly one of source, source_file, or sources"
            )
        else:
            try:
                resolved = case_sources(case, root)
            except ContractError as exc:
                errors.append(f"{case_id}: {exc}")
            else:
                source_ids = [item["source_id"] for item in resolved]
                if len(source_ids) != len(set(source_ids)):
                    errors.append(f"{case_id}.sources source_id values must be unique")

        expected = case.get("expected")
        if not isinstance(expected, dict):
            errors.append(f"{case_id}.expected must be an object")
            continue
        for field in ("must", "must_not"):
            values = expected.get(field)
            if (
                not isinstance(values, list)
                or not values
                or not all(isinstance(value, str) and value.strip() for value in values)
                or len(values) != len(set(values))
            ):
                errors.append(f"{case_id}.expected.{field} must be unique non-empty strings")
        errors.extend(
            semantic_contract_errors(
                case.get("semantic_contract"), f"{case_id}.semantic_contract"
            )
        )
        reader_test = case.get("reader_test")
        if reader_test is not None:
            if not isinstance(reader_test, dict):
                errors.append(f"{case_id}.reader_test must be an object")
            else:
                persona = reader_test.get("persona")
                questions = reader_test.get("questions")
                if not isinstance(persona, str) or not persona.strip():
                    errors.append(f"{case_id}.reader_test.persona must be non-empty")
                if not isinstance(questions, list) or not questions:
                    errors.append(f"{case_id}.reader_test.questions must be non-empty")
                else:
                    question_ids: list[str] = []
                    for question in questions:
                        if not isinstance(question, dict):
                            errors.append(
                                f"{case_id}.reader_test questions must be objects"
                            )
                            continue
                        question_id = question.get("id")
                        question_text = question.get("question")
                        answer_key = question.get("answer_key")
                        if not isinstance(question_id, str) or not question_id.strip():
                            errors.append(
                                f"{case_id}.reader_test question ids must be non-empty"
                            )
                        else:
                            question_ids.append(question_id)
                        if not isinstance(question_text, str) or not question_text.strip():
                            errors.append(
                                f"{case_id}.reader_test question text must be non-empty"
                            )
                        if (
                            not isinstance(answer_key, list)
                            or not answer_key
                            or not all(
                                isinstance(value, str) and value.strip()
                                for value in answer_key
                            )
                        ):
                            errors.append(
                                f"{case_id}.reader_test answer_key must be non-empty strings"
                            )
                    if len(question_ids) != len(set(question_ids)):
                        errors.append(
                            f"{case_id}.reader_test question ids must be unique"
                        )
    return errors


def load_cases(path: Path = CASES_PATH, root: Path = ROOT) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"unable to read behavior cases: {exc}") from exc
    errors = validate_payload(payload, root)
    if errors:
        raise ContractError("; ".join(errors))
    return payload["cases"]


def load_judge_fixtures(path: Path = JUDGE_FIXTURES_PATH) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"unable to read judge fixtures: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != "write-craft.judge-fixtures.v1":
        raise ContractError("judge fixtures schema is invalid")
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ContractError("judge fixtures must be a non-empty array")
    ids: set[str] = set()
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            raise ContractError("judge fixtures must be objects")
        fixture_id = fixture.get("id")
        case = fixture.get("case")
        if not isinstance(fixture_id, str) or not fixture_id.strip() or fixture_id in ids:
            raise ContractError("judge fixture ids must be unique and non-empty")
        ids.add(fixture_id)
        if (
            not isinstance(case, dict)
            or not isinstance(case.get("id"), str)
            or not isinstance(case.get("request"), str)
            or not case["request"].strip()
            or not isinstance(case.get("expected"), dict)
            or any(
                not isinstance(case["expected"].get(field), list)
                or not case["expected"][field]
                for field in ("must", "must_not")
            )
        ):
            raise ContractError(f"judge fixture {fixture_id} has an invalid case")
        semantic_errors = semantic_contract_errors(
            case.get("semantic_contract"),
            f"judge fixture {fixture_id}.case.semantic_contract",
        )
        if semantic_errors:
            raise ContractError("; ".join(semantic_errors))
        for field in ("source", "candidate"):
            if not isinstance(fixture.get(field), str) or not fixture[field].strip():
                raise ContractError(f"judge fixture {fixture_id} has invalid {field}")
        if fixture.get("expected_status") not in {"PASS", "FAIL"}:
            raise ContractError(
                f"judge fixture {fixture_id} expected_status must be PASS or FAIL"
            )
        if ("expected_editorial_status" in fixture and fixture["expected_editorial_status"]
                not in {"NEEDS_EDIT", "NO_ISSUES_FOUND"}):
            raise ContractError("invalid expected_editorial_status")
    return fixtures


def case_source(case: dict[str, Any], root: Path = ROOT) -> str:
    sources = case_sources(case, root)
    return format_sources(sources, legacy_plain="sources" not in case)


def select_cases(
    cases: list[dict[str, Any]],
    suite: str,
    case_ids: list[str],
    track: str | None = None,
) -> list[dict[str, Any]]:
    if case_ids:
        requested = set(case_ids)
        available = {case["id"] for case in cases}
        missing = sorted(requested - available)
        if missing:
            raise ContractError(f"unknown case ids: {missing}")
        selected = [case for case in cases if case["id"] in requested]
        return [case for case in selected if track is None or case.get("track") == track]
    if suite == "smoke":
        selected = [case for case in cases if case["suite"] == "smoke"]
        return [case for case in selected if track is None or case.get("track") == track]
    if suite == "full":
        return [case for case in cases if track is None or case.get("track") == track]
    raise ContractError(f"unknown suite: {suite}")


def message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    parts = [
        block.get("text", "")
        for block in content
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    ]
    return "".join(parts).strip()


def extract_final_assistant_message(jsonl: str) -> dict[str, Any]:
    final: dict[str, Any] | None = None
    malformed: list[int] = []
    for line_number, line in enumerate(jsonl.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed.append(line_number)
            continue
        if (
            isinstance(event, dict)
            and event.get("type") == "message_end"
            and isinstance(event.get("message"), dict)
            and event["message"].get("role") == "assistant"
        ):
            final = event["message"]
    if malformed:
        raise ContractError(f"Pi JSONL contains malformed lines: {malformed}")
    if final is None:
        raise ContractError("Pi JSONL contains no final assistant message")
    if final.get("errorMessage") or final.get("stopReason") in {"error", "aborted"}:
        raise ContractError(
            f"assistant message ended with an error: {final.get('errorMessage') or final.get('stopReason')}"
        )
    return final


def extract_final_assistant(jsonl: str) -> dict[str, Any]:
    final = extract_final_assistant_message(jsonl)
    text = message_text(final)
    if not text:
        raise ContractError("final assistant message contains no text")
    return {"text": text, "message": final}


def extract_final_tool_call(jsonl: str, tool_name: str) -> dict[str, Any]:
    final = extract_final_assistant_message(jsonl)
    content = final.get("content")
    if not isinstance(content, list):
        raise ContractError("final assistant message contains no content blocks")
    tool_calls = [
        block
        for block in content
        if isinstance(block, dict) and block.get("type") == "toolCall"
    ]
    if len(tool_calls) != 1:
        raise ContractError(
            f"final assistant message must contain exactly one {tool_name} tool call"
        )
    tool_call = tool_calls[0]
    if tool_call.get("name") != tool_name:
        raise ContractError(
            f"final assistant called {tool_call.get('name')!r}, expected {tool_name!r}"
        )
    arguments = tool_call.get("arguments")
    if not isinstance(arguments, dict):
        raise ContractError(f"{tool_name} arguments must be an object")
    return {"arguments": arguments, "message": final}


def strip_json_fence(text: str) -> str:
    match = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", text, flags=re.S | re.I)
    return match.group(1) if match else text.strip()


def parse_judgment(text: str, case: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(strip_json_fence(text))
    except json.JSONDecodeError as exc:
        raise ContractError(f"judge did not return valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != JUDGMENT_SCHEMA:
        raise ContractError(f"judge schema must be {JUDGMENT_SCHEMA}")
    if payload.get("case_id") != case["id"]:
        raise ContractError("judge case_id does not match the evaluated case")

    expected = case["expected"]
    for field in ("must", "must_not"):
        checks = payload.get(field)
        if not isinstance(checks, list) or len(checks) != len(expected[field]):
            raise ContractError(f"judge {field} checks do not cover every criterion")
        for criterion, check in zip(expected[field], checks, strict=True):
            if not isinstance(check, dict) or check.get("criterion") != criterion:
                raise ContractError(f"judge {field} criteria changed or reordered")
            if check.get("status") not in VALID_STATUSES:
                raise ContractError(f"judge {field} status is invalid")
            if not isinstance(check.get("evidence"), str) or not check["evidence"].strip():
                raise ContractError(f"judge {field} evidence must be non-empty")

    blocking = payload.get("blocking_issues")
    if not isinstance(blocking, list) or not all(
        isinstance(item, str) and item.strip() for item in blocking
    ):
        raise ContractError("judge blocking_issues must be an array of non-empty strings")

    statuses = [
        check["status"]
        for field in ("must", "must_not")
        for check in payload[field]
    ]
    computed = (
        "FAIL"
        if blocking
        else "PASS"
        if all(status == "PASS" for status in statuses)
        else "FAIL"
        if "FAIL" in statuses
        else "UNCERTAIN"
    )
    if payload.get("status") != computed:
        raise ContractError(
            f"judge status {payload.get('status')!r} does not match computed status {computed}"
        )
    payload["status"] = computed
    if "editorial" in payload:
        payload["editorial"] = validate_editorial(payload["editorial"])
    return payload


def normalize_fact_tool_arguments(
    arguments: dict[str, Any], case: dict[str, Any], *, require_editorial: bool = False
) -> dict[str, Any]:
    """Convert the unambiguous tool protocol into the persisted judgment schema."""
    presence_to_status = {
        "ABSENT": "PASS",
        "PRESENT": "FAIL",
        "UNCERTAIN": "UNCERTAIN",
    }
    expected = case["expected"]
    must = arguments.get("must")
    if not isinstance(must, list):
        raise ContractError("fact tool must must be an array")
    if len(must) != len(expected["must"]):
        raise ContractError("fact tool must checks do not cover every criterion")

    normalized_must: list[dict[str, Any]] = []
    for index, (criterion, check) in enumerate(
        zip(expected["must"], must, strict=True), start=1
    ):
        if not isinstance(check, dict):
            raise ContractError("fact tool must checks must be objects")
        if check.get("criterion_index") != index:
            raise ContractError("fact tool must criterion_index changed or reordered")
        normalized_must.append(
            {
                "criterion": criterion,
                "status": check.get("status"),
                "evidence": check.get("evidence"),
            }
        )

    must_not = arguments.get("must_not")
    if not isinstance(must_not, list):
        raise ContractError("fact tool must_not must be an array")
    if len(must_not) != len(expected["must_not"]):
        raise ContractError("fact tool must_not checks do not cover every criterion")

    normalized_must_not: list[dict[str, Any]] = []
    for index, (criterion, check) in enumerate(
        zip(expected["must_not"], must_not, strict=True), start=1
    ):
        if not isinstance(check, dict):
            raise ContractError("fact tool must_not checks must be objects")
        if check.get("criterion_index") != index:
            raise ContractError(
                "fact tool must_not criterion_index changed or reordered"
            )
        presence = check.get("presence")
        if presence not in presence_to_status:
            raise ContractError(
                "fact tool must_not presence must be ABSENT, PRESENT, or UNCERTAIN"
            )
        normalized_must_not.append(
            {
                "criterion": criterion,
                "status": presence_to_status[presence],
                "evidence": check.get("evidence"),
            }
        )

    normalized = {
        "schema": arguments.get("schema"),
        "case_id": arguments.get("case_id"),
        "must": normalized_must,
        "must_not": normalized_must_not,
        "blocking_issues": arguments.get("blocking_issues"),
    }
    if require_editorial and "editorial" not in arguments:
        raise ContractError("live fact judgment requires editorial review")
    if "editorial" in arguments:
        normalized["editorial"] = validate_editorial(arguments["editorial"])
    statuses = [
        check.get("status")
        for field in ("must", "must_not")
        for check in normalized.get(field) or []
        if isinstance(check, dict)
    ]
    blocking = normalized["blocking_issues"]
    normalized["status"] = (
        "FAIL"
        if blocking
        else "PASS"
        if all(status == "PASS" for status in statuses)
        else "FAIL"
        if "FAIL" in statuses
        else "UNCERTAIN"
    )
    return normalized


def validate_editorial(payload: Any, candidate: str | None = None) -> dict[str, Any]:
    """Separate located editorial observations from the legacy contract verdict."""
    if not isinstance(payload, dict) or payload.get("schema") != "write-craft.editorial.v1":
        raise ContractError("editorial schema must be write-craft.editorial.v1")
    issues = payload.get("issues")
    if not isinstance(issues, list):
        raise ContractError("editorial issues must be an array")
    for issue in issues:
        if not isinstance(issue, dict) or issue.get("kind") not in {
            "redundancy", "irrelevant_commentary", "structure", "sentence", "wording", "presentation"
        }:
            raise ContractError("editorial issue kind is invalid")
        for field in ("quote", "reason", "suggestion"):
            if not isinstance(issue.get(field), str) or not issue[field].strip():
                raise ContractError(f"editorial {field} must be non-empty")
        if candidate is not None and issue["quote"] not in candidate:
            raise ContractError("editorial quote not found in candidate")
    return {"schema": "write-craft.editorial.v1", "issues": issues,
            "status": "NEEDS_EDIT" if issues else "NO_ISSUES_FOUND"}


def generator_prompt(case: dict[str, Any], source: str) -> str:
    return f"""/skill:write-craft

这是一次隔离的真实写作任务。请直接完成用户请求，不要讨论评测过程，也不要提及隐藏的验收标准。

【用户请求】
{case['request']}

【原始材料】
{source}
"""


def revision_prompt(
    case: dict[str, Any],
    source: str,
    candidate: str,
    judgment: dict[str, Any],
) -> str:
    failed_checks = [
        {
            "criterion": check["criterion"],
            "status": check["status"],
            "evidence": check["evidence"],
        }
        for field in ("must", "must_not")
        for check in judgment[field]
        if check["status"] != "PASS"
    ]
    feedback = json.dumps(
        {
            "status": judgment["status"],
            "blocking_issues": judgment["blocking_issues"],
            "failed_or_uncertain_checks": failed_checks,
            "editorial_issues": judgment.get("editorial", {}).get("issues", []),
        },
        ensure_ascii=False,
        indent=2,
    )
    return f"""/skill:write-craft

这是同一份重要文档唯一允许的一次纠正。请根据原始材料和独立事实复核反馈，返回一份完整替换稿。

要求：
- 修复反馈指出的事实、遗漏和交付问题，但不要为了显得完整而增加新的角色、流程、原因、边界、建议或待确认项。
- 对有原文定位的编辑问题，合并重复信息、调整论证顺序或修复措辞；不要因偏好建议删掉必要条件。事实已经通过时，仍须检查编辑后是否改变原意。
- 保留初稿中已有来源支持且与用户请求相关的内容。
- 无法由来源支持的表述应删除、收窄或明确为来源中的未知；不要与评审争辩。
- 只输出可直接使用的完整成稿，不要解释修改过程、提及评测或附加后续服务话术。

【用户请求】
{case['request']}

【原始材料】
{source}

【初稿】
{candidate}

【独立事实复核反馈】
{feedback}
"""


def judge_prompt(case: dict[str, Any], source: str, candidate: str,
                 editorial_findings: list[dict[str, Any]] | None = None) -> str:
    contract = json.dumps(case["expected"], ensure_ascii=False, indent=2)
    semantic_contract = json.dumps(
        case.get("semantic_contract", {}), ensure_ascii=False, indent=2
    )
    limits = json.dumps(case.get("limits", {}), ensure_ascii=False, indent=2)
    advisory = ""
    if editorial_findings is not None:
        advisory = (
            "\n【独立编辑提出的候选问题，不是已确认结论】\n"
            + json.dumps(editorial_findings, ensure_ascii=False, indent=2)
            + "\n根据原始材料、用户任务和候选稿独立核实这些意见，不机械采纳。"
              "仅把确有依据的问题纳入最终 editorial；可拒绝偏好、误报或会删除必要条件的建议，"
              "本阶段只确认或驳回已列出的编辑问题，不新增 editorial 问题；"
              "确认时保留该候选问题的 kind 和 quote 原文，reason 和 suggestion 可按来源纠正。"
              "候选为空时 editorial.issues 必须为空。"
              "新的事实错误仍须通过 must、must_not 或 blocking_issues 报告，不能因编辑候选为空而放行。"
              "不要把候选问题的数量当成必须确认的数量。\n"
        )
    return f"""你是一个独立的文档行为验收员。你没有参与候选稿的生成，只能根据本消息中的请求、原始材料、候选稿和验收合同判分。不要重写候选稿。

判分规则：
- must 项只有在候选稿明确满足且没有越过原始材料证据边界时才为 PASS。
- 原始材料是语义依据；如果验收合同或账本与原文冲突，记录为阻断问题，不按错误账本放行。特别区分“不要求”和“禁止”、“可选”和“不采集”，不能把非必填改成禁用。
- must 和 must_not 都按验收合同原有顺序用从 1 开始的 criterion_index 标识；不要复制或改写验收项文字。
- must_not 项不填写 PASS/FAIL，而是判断禁用行为是否出现：没有出现填 ABSENT，出现填 PRESENT，无法判断才填 UNCERTAIN。
- 工具不接收顶层 status；程序会把 must 的 status、must_not 的 presence 和 blocking_issues 归一化为最终 PASS/FAIL/UNCERTAIN。
- 语义账本是人工冻结的判分边界，不会提供给生成者。`facts` 是本用例支持的事实；`allowed_inferences` 只允许其中写明的有界解释，不能据此推出更强结论；`forbidden_inferences` 一旦出现在候选稿中即为阻断问题。`unknowns.state=explicitly_unknown` 才可以写成“尚未确定/待确认”；`unknowns.state=not_stated` 只能写成“材料未说明/未列出”，不得升级为尚未决定、尚未验证、永远不做或必须补齐。空账本表示本用例仍只按来源与验收合同判断。
- 除逐项合同外，检查标题、摘要、表格、正文、下一步和结尾话术组成的完整候选稿。影响理解或决策的无来源事实、新审批、新负责人、新范围、新流程或内部矛盾，即使没有被逐字列入 must_not，也属于阻断问题。内容听起来合理或不与来源冲突，不能替代来源支持；把新增内容称为“合理延伸”“概括性衔接”“自然下一步”，或说“读者已意识到歧义”，也不能作为放行理由。来源没有陈述或必然推出的原因、流程、基线、负责人、决定和边界仍应判为无依据新增。来源列出若干未知，不表示其他常见项目字段、子项或补齐流程也自动成为本稿的缺口；来源给出试点与比较指标，也不自动建立后续推广、停止或继续投入的决定与规则。忠实解释、概括和信息重排本身不是错误。
- 来源没有提到某个字段，只能证明该字段未出现在这份来源中，不能自动授权候选稿把它突出为“材料未说明”“尚缺”“待补”或决策缺口。若 must_not 禁止新增缺口，那么这类缺失声明本身就算禁用行为 PRESENT；只有用户要求缺口分析，或来源明确把该项标为未知/缺失时，才按合同判断是否可以保留。
- 严格保护状态与模态：“当前不允许”“本期不做”“必须人工确认”是项目规则或当前边界，不等于系统永久“不具备能力”“无法做到”；反向改写同样不成立。把政策边界写成技术能力边界属于阻断问题，即使最终操作结果看起来相同。
- 无法确定时使用 UNCERTAIN。不要用常识替候选稿补齐。
- evidence 必须引用或准确指出候选稿中的依据；缺少依据时说明缺失。
- 表达质量合同必须逐项实际检查，事实准确不能覆盖交付违约。若合同禁止重复，比较段落各自增加的信息：完整场景后仅换词重述用途、输出和人工边界的整段属于重复，不能笼统称为“强调”放行；在验收步骤中重申同一边界但增加可执行检查，则不因词义重复自动判错。若合同禁止无关缺失清单，即使“材料未说明”属实，也须检查它是否有助于本次阅读任务。只按当前合同执行，不把一般简洁偏好变成所有文档的阻断门槛。
- 原始材料提供 source_id、text_sha256 和行号时，evidence 应使用这些真实定位；不得编造来源或行号。定位有效不等于语义推断自动正确。
- must 中每一个 status 字段的值必须精确等于 PASS、FAIL 或 UNCERTAIN 三者之一；must_not 中每一个 presence 字段必须精确等于 ABSENT、PRESENT 或 UNCERTAIN 三者之一。禁止添加解释、空格或其他文字；所有解释只能写进 evidence。
- blocking_issues 只记录足以阻止通过的问题；只要该数组非空，程序计算的最终 status 就是 FAIL。
- 无论合同是否列出文风要求，都填写 editorial：逐篇检查结构、段落信息贡献、句子关系、措辞、呈现及无关写作说明。每项问题给出候选稿中连续且原样的 quote、具体 reason 和不改变事实的 suggestion；不要重写全文，没有发现则 issues 为空。不要为凑数量报告偏好。专用术语重现、独立摘要、增加了实际检查的边界重申不自动算重复；短进展的标题与条目、正文与范围表重复整套流程且没有独立阅读需要时，要记录新增信息不足。来源说未提供旧流程，不代表解释新方案时必须写出这项缺失。
- 结构检查要区分“中心回答是否出现”和“理由是否支持回答”。检查上层判断与下层依据、同层分组是否一致、顺序是否有因果/时间/组成/重要性依据；标题数量和结论前置本身不能证明结构良好。状态汇报不必有推荐或理由树。理由、行动和结果混列，或列出各选项共有能力却未解释选择差异时，定位实际结构问题。缺少来源依据时不能要求补造论证。
- 语义分组与视觉分块不同。自然段中通过明确的因果、时序和目标关系已经区分信息作用时，不因没有分段、小标题、表格或编号而判结构失败。除非用户明确规定排版形式，否则应检查信息之间的逻辑关系，而非强制各类信息独占一块；相反，已有标题也不能掩盖实际混类。
- 编辑检查须跨段比较，尤其检查开头与结尾、场景与流程、正文与表格。报告重复时，在 reason 中同时指出另一处对应表述及两处为何没有不同用途；不能只凭同一个词多次出现判重复。重组任务还须检查决定性依据的位置：若先展开大量细节再解释为何选择该方案，定位这个次序问题；沿用原稿顺序不是正确性的证明，但也不能仅因顺序未变就判错。
- 结论、建议或请求决定可以先于详细论据出现，这是正常的结论先行；不要要求读者必须先看完所有依据才看到请求。顺序问题指决定性理由被无关紧要的细节隔开，不是成本、分工等全部信息都必须挤到首句。quote 应复制候选稿的一小段连续原文，不拼接句段、不补标点、不改写。
- editorial 是独立的编辑观察，不自动改变原有合同 status；若同一问题违反明确合同，还须将对应合同项判 FAIL/PRESENT，不能只记为编辑建议。反之，普通编辑问题不要伪装成事实错误。NO_ISSUES_FOUND 只表示本次未发现，不能证明可直接发送或真人已读懂。
- 诊断前明确句子所说的对象与关系，不把不同种类的比较、能力或证据混为一谈。判断缺失说明是否多余，要看它是否服务用户当前任务；真实但无关的缺失说明属于相关性问题，不凭空改判成无依据因果。反过来，用户要求的比较因材料缺失无法完成时，应保留这个限制。
- 本用例的 must 数组必须恰好有 {len(case['expected']['must'])} 项，criterion_index 依次为 {list(range(1, len(case['expected']['must']) + 1))}；must_not 数组必须恰好有 {len(case['expected']['must_not'])} 项，criterion_index 依次为 {list(range(1, len(case['expected']['must_not']) + 1))}。不得增删、合并或重复检查项。
- 最终必须且只能调用 `{FACT_JUDGMENT_TOOL}` 一次；把判定填入工具参数。不要改用正文、JSON 文本或 Markdown 代码块作答。

工具参数结构：
{{
  "schema": "{JUDGMENT_SCHEMA}",
  "case_id": "{case['id']}",
  "must": [{{"criterion_index": 1, "status": "PASS | FAIL | UNCERTAIN", "evidence": "候选稿依据或缺失说明"}}],
  "must_not": [{{"criterion_index": 1, "presence": "ABSENT | PRESENT | UNCERTAIN", "evidence": "未出现或出现的依据"}}],
  "blocking_issues": ["阻止通过的问题；没有则为空数组"],
  "editorial": {{"schema": "write-craft.editorial.v1", "issues": [{{"kind": "redundancy | irrelevant_commentary | structure | sentence | wording | presentation", "quote": "候选稿原文", "reason": "具体问题及影响", "suggestion": "编辑方向"}}]}}
}}

【用户请求】
{case['request']}

【原始材料】
{source}

【候选稿】
{candidate}

【验收合同】
{contract}

【语义账本】
{semantic_contract}

【确定性长度限制】
{limits}
{advisory}
"""


def reader_prompt(case: dict[str, Any], candidate: str) -> str:
    reader_test = case["reader_test"]
    public_questions = [
        {"id": item["id"], "question": item["question"]}
        for item in reader_test["questions"]
    ]
    questions = json.dumps(public_questions, ensure_ascii=False, indent=2)
    return f"""你是一名没有参与项目讨论的独立读者。你只能看到候选文档、读者身份和中性问题；不要猜测文档没有说明的内容，也不要评价隐藏的写作标准。不要把并列出现的事实推断成因果关系，也不要把“当前不允许”改读成系统永久没有能力。

读者身份：{reader_test['persona']}

先用自己的话简要复述文档，再逐题回答。每个答案必须引用候选文档中的依据；没有答案就明确写“文档未说明”。最后列出含义不明确处和阅读后自然产生的问题。歧义只记录候选文档实际造成的不明确，不要把常见尽调清单伪装成文档缺失；自然问题可以超出文档，但必须保持为问题，不能写成事实。

最终必须且只能调用 `{READER_RESPONSE_TOOL}` 一次；把复述和回答填入工具参数。不要改用正文、JSON 文本或 Markdown 代码块作答。工具参数结构：
{{
  "schema": "{READER_RESPONSE_SCHEMA}",
  "case_id": "{case['id']}",
  "restatement": "自由复述",
  "answers": [{{"question_id": "原样复制问题 id", "answer": "回答", "evidence": "候选文档依据或文档未说明"}}],
  "ambiguities": ["含义不明确处；没有则为空数组"],
  "natural_questions": ["理解后仍会提出的业务问题；没有则为空数组"]
}}

【候选文档】
{candidate}

【问题】
{questions}
"""


def parse_reader_response(text: str, case: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(strip_json_fence(text))
    except json.JSONDecodeError as exc:
        raise ContractError(f"reader did not return valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != READER_RESPONSE_SCHEMA:
        raise ContractError(f"reader schema must be {READER_RESPONSE_SCHEMA}")
    if payload.get("case_id") != case["id"]:
        raise ContractError("reader case_id does not match the evaluated case")
    if not isinstance(payload.get("restatement"), str) or not payload["restatement"].strip():
        raise ContractError("reader restatement must be non-empty")
    questions = case["reader_test"]["questions"]
    answers = payload.get("answers")
    if not isinstance(answers, list) or len(answers) != len(questions):
        raise ContractError("reader answers must cover every question")
    for question, answer in zip(questions, answers, strict=True):
        if not isinstance(answer, dict) or answer.get("question_id") != question["id"]:
            raise ContractError("reader question ids changed or reordered")
        for field in ("answer", "evidence"):
            if not isinstance(answer.get(field), str) or not answer[field].strip():
                raise ContractError(f"reader {field} must be non-empty")
    for field in ("ambiguities", "natural_questions"):
        values = payload.get(field)
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            raise ContractError(f"reader {field} must be an array of non-empty strings")
    return payload


def reader_judgment_prompt(
    case: dict[str, Any],
    source: str,
    candidate: str,
    reader_response: dict[str, Any],
) -> str:
    reader_contract = json.dumps(case["reader_test"], ensure_ascii=False, indent=2)
    semantic_contract = json.dumps(
        case.get("semantic_contract", {}), ensure_ascii=False, indent=2
    )
    response = json.dumps(reader_response, ensure_ascii=False, indent=2)
    return f"""你是独立的读者理解核对员。根据原始材料、候选文档、答案要点和盲读者回答，判断读者是否准确理解；不要因为读者不同意方案或提出正常业务追问而扣分。

规则：
- 每个问题逐项判定 PASS、FAIL 或 UNCERTAIN。
- 语义账本是人工冻结的理解边界。读者理解应覆盖相关 `reader_truths`，不得形成 `reader_misreadings`。`unknowns.state=not_stated` 只能理解为材料没有说明，不能理解为项目尚未决定或以后必须补齐；`explicitly_unknown` 才表示来源明确说未知。空账本表示仍只按来源、候选文档和答案要点判断。
- 逐题判定前，先检查盲读者的自由复述、全部答案和歧义列表。只要其中出现原始材料不支持的确定性因果、能力边界、状态、决定、缺失项或与候选文档矛盾的陈述，就加入 blocking_issues 并将最终状态判为 FAIL，即使答案要点本身全部命中。natural_questions 中保持为问题的正常追问不因此失败。
- 读者准确回答“文档未说明”，但原始材料存在本次任务必须保留的答案时，应判为文档覆盖失败。
- 原始材料本来未知且候选文档准确保留未知，不因缺少确定答案而失败。
- 候选文档新增错误且读者准确复述时，理解阶段仍应指出错误，不能以“读懂了”为通过理由。候选稿若从试点和比较指标推出后续推广、停止或继续投入的决定，或把来源中的未知拆成新的必填子项，即使读者正确复述或主动指出歧义，也属于来源忠实性阻断问题；不得以“合理延伸”放行。
- blocking_issues 只写足以阻止理解验收的问题；非空时最终 status 必须为 FAIL。
- 最终必须且只能调用 `{READER_JUDGMENT_TOOL}` 一次；把核对结果填入工具参数。不要改用正文、JSON 文本或 Markdown 代码块作答。

工具参数结构：
{{
  "schema": "{READER_JUDGMENT_SCHEMA}",
  "case_id": "{case['id']}",
  "status": "PASS | FAIL | UNCERTAIN",
  "answers": [{{"question_id": "原样复制问题 id", "status": "PASS | FAIL | UNCERTAIN", "evidence": "核对依据"}}],
  "blocking_issues": ["阻止通过的问题；没有则为空数组"]
}}

【原始材料】
{source}

【候选文档】
{candidate}

【读者测试合同】
{reader_contract}

【语义账本】
{semantic_contract}

【盲读者回答】
{response}
"""


def parse_reader_judgment(text: str, case: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(strip_json_fence(text))
    except json.JSONDecodeError as exc:
        raise ContractError(f"reader judge did not return valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != READER_JUDGMENT_SCHEMA:
        raise ContractError(f"reader judge schema must be {READER_JUDGMENT_SCHEMA}")
    if payload.get("case_id") != case["id"]:
        raise ContractError("reader judge case_id does not match the evaluated case")
    questions = case["reader_test"]["questions"]
    answers = payload.get("answers")
    if not isinstance(answers, list) or len(answers) != len(questions):
        raise ContractError("reader judge answers must cover every question")
    statuses: list[str] = []
    for question, answer in zip(questions, answers, strict=True):
        if not isinstance(answer, dict) or answer.get("question_id") != question["id"]:
            raise ContractError("reader judge question ids changed or reordered")
        if answer.get("status") not in VALID_STATUSES:
            raise ContractError("reader judge answer status is invalid")
        if not isinstance(answer.get("evidence"), str) or not answer["evidence"].strip():
            raise ContractError("reader judge evidence must be non-empty")
        statuses.append(answer["status"])
    blocking = payload.get("blocking_issues")
    if not isinstance(blocking, list) or not all(
        isinstance(item, str) and item.strip() for item in blocking
    ):
        raise ContractError("reader judge blocking_issues must be non-empty strings")
    computed = (
        "FAIL"
        if blocking or "FAIL" in statuses
        else "PASS"
        if all(status == "PASS" for status in statuses)
        else "UNCERTAIN"
    )
    if payload.get("status") != computed:
        raise ContractError(
            f"reader judge status {payload.get('status')!r} does not match computed status {computed}"
        )
    payload["status"] = computed
    return payload


def run_command(args: list[str], timeout: int) -> dict[str, Any]:
    if claude_code_model(args) is not None:
        return run_claude_code(args, timeout)
    return run_process(args, timeout)


def run_process(
    args: list[str], timeout: int, *, cwd: Path = ROOT, stdin: str | None = None
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "duration_seconds": round(time.monotonic() - started, 3),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr or ""
        return {
            "returncode": None,
            "stdout": stdout,
            "stderr": stderr,
            "duration_seconds": round(time.monotonic() - started, 3),
            "timed_out": True,
        }
    except FileNotFoundError as exc:
        return {
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "duration_seconds": round(time.monotonic() - started, 3),
            "timed_out": False,
        }


def pi_args(
    *,
    prompt: str,
    model: str,
    thinking: str,
    with_skill: bool,
    structured_tool: str | None = None,
) -> list[str]:
    if with_skill and structured_tool:
        raise ValueError("generator Skill and structured review tool cannot share a Pi run")
    args = [
        "pi",
        "--mode",
        "json",
        "--no-session",
        "--no-skills",
        "--no-extensions",
        "--no-context-files",
        "--no-approve",
        "--model",
        model,
        "--thinking",
        thinking,
    ]
    if with_skill:
        args.extend(["--tools", "read", "--skill", str(SKILL_ROOT)])
    elif structured_tool:
        args.extend(
            [
                "--extension",
                str(STRUCTURED_OUTPUT_EXTENSION),
                "--tools",
                structured_tool,
            ]
        )
    else:
        args.append("--no-tools")
    args.append(prompt)
    return args


CLAUDE_CODE_PREFIXES = ("anthropic/", "claude-code/")
SKILL_COMMAND = "/skill:write-craft"


def claude_code_model(args: list[str]) -> str | None:
    """Return the Claude model for a Pi command that should run in Claude Code."""
    if not args or args[0] != "pi" or "--model" not in args:
        return None
    model = args[args.index("--model") + 1]
    for prefix in CLAUDE_CODE_PREFIXES:
        if model.startswith(prefix):
            return model[len(prefix):]
    return None


def claude_code_invocation(args: list[str]) -> tuple[list[str], str]:
    """Translate Pi arguments into a `claude -p` command and stdin prompt."""
    model = claude_code_model(args)
    if model is None:
        raise ValueError("not a Claude Code model")
    if "--extension" in args:
        raise ContractError("structured-tool reviews are not supported through Claude Code")
    prompt = args[-1]
    command = [
        "claude", "-p", "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--setting-sources", "", "--strict-mcp-config", "--disable-slash-commands",
    ]
    if "--skill" in args:
        skill = Path(args[args.index("--skill") + 1]).resolve()
        command += ["--tools", "Read", "--allowedTools", "Read", "--add-dir", str(skill)]
        instruction = (
            f"先用 Read 阅读 {skill / 'SKILL.md'}，并按其中要求读取 references 下的文件，"
            "然后按该 Skill 完成任务。最终回复只输出成稿。"
        )
        if prompt.startswith(SKILL_COMMAND):
            prompt = instruction + prompt[len(SKILL_COMMAND):]
        else:
            prompt = instruction + "\n\n" + prompt
    else:
        command += ["--tools", ""]
    return command, prompt


def claude_stream_to_pi_jsonl(stream: str, model: str) -> str:
    """Convert Claude Code stream-json into the Pi events this evaluator reads."""
    events: list[dict[str, Any]] = []
    for line in stream.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if event.get("type") == "assistant" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use" \
                        and block.get("name") == "Read":
                    params = block.get("input") if isinstance(block.get("input"), dict) else {}
                    read_args = {"path": params.get("file_path")}
                    read_args.update({k: params[k] for k in ("offset", "limit") if k in params})
                    events.append({"type": "tool_execution_start", "toolCallId": block.get("id"),
                                   "toolName": "read", "args": read_args})
        elif event.get("type") == "user" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    events.append({"type": "tool_execution_end",
                                   "toolCallId": block.get("tool_use_id"),
                                   "isError": bool(block.get("is_error"))})
        elif event.get("type") == "result":
            usage = event.get("usage") if isinstance(event.get("usage"), dict) else {}
            counts = {
                "input": usage.get("input_tokens", 0),
                "output": usage.get("output_tokens", 0),
                "cacheRead": usage.get("cache_read_input_tokens", 0),
                "cacheWrite": usage.get("cache_creation_input_tokens", 0),
            }
            counts["totalTokens"] = sum(v for v in counts.values() if type(v) is int)
            counts["cost"] = {"total": event.get("total_cost_usd") or 0.0}
            text = event.get("result") if isinstance(event.get("result"), str) else ""
            final: dict[str, Any] = {
                "role": "assistant", "provider": "claude-code", "model": model,
                "content": [{"type": "text", "text": text}], "usage": counts,
                "stopReason": "error" if event.get("is_error") else "stop",
            }
            if event.get("is_error"):
                final["errorMessage"] = text or str(event.get("subtype") or "error")
            events.append({"type": "message_end", "message": final})
    return "\n".join(json.dumps(event, ensure_ascii=False) for event in events)


def run_claude_code(args: list[str], timeout: int) -> dict[str, Any]:
    try:
        command, prompt = claude_code_invocation(args)
    except ContractError as exc:
        return {"returncode": 2, "stdout": "", "stderr": str(exc),
                "duration_seconds": 0.0, "timed_out": False}
    # Run outside the repository so project CLAUDE.md files do not enter the context.
    with tempfile.TemporaryDirectory(prefix="write-craft-claude-") as workdir:
        completed = run_process(command, timeout, cwd=Path(workdir), stdin=prompt)
    completed["stdout"] = claude_stream_to_pi_jsonl(completed["stdout"], command[3])
    return completed


def safe_message_metadata(message: dict[str, Any]) -> dict[str, Any]:
    return {
        key: message[key]
        for key in ("provider", "model", "usage", "stopReason", "timestamp")
        if key in message
    }


def skill_read_trace(jsonl: str) -> dict[str, Any]:
    """Retain read receipts, not contents or reasoning; success is not compliance."""
    reads: list[dict[str, Any]] = []
    pending: dict[str, dict[str, Any]] = {}
    malformed = 0
    for line in jsonl.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if not isinstance(event, dict):
            continue
        call_id = event.get("toolCallId")
        if not isinstance(call_id, str):
            continue
        if event.get("type") == "tool_execution_start" and event.get("toolName") == "read":
            args = event.get("args")
            args = args if isinstance(args, dict) else {}
            raw_path = args.get("path", args.get("file_path"))
            path = "OUTSIDE_SKILL_OR_UNKNOWN"
            if isinstance(raw_path, str):
                try:
                    candidate = Path(raw_path).expanduser()
                    if not candidate.is_absolute():
                        candidate = ROOT / candidate
                    path = str(candidate.resolve().relative_to(SKILL_ROOT.resolve()))
                except (ValueError, OSError, RuntimeError):
                    pass
            item: dict[str, Any] = {"path": path, "status": "UNCONFIRMED"}
            for key in ("offset", "limit"):
                value = args.get(key)
                if type(value) is int and value > 0:
                    item[key] = value
            reads.append(item)
            pending[call_id] = item
        elif event.get("type") == "tool_execution_end" and call_id in pending:
            item = pending.pop(call_id)
            if event.get("isError") is False:
                item["status"] = "SUCCEEDED"
            elif event.get("isError") is True:
                item["status"] = "FAILED"
    return {"reads": reads, "malformed_lines": malformed,
            "evidence_limit": "Read completion does not prove full content visibility or rule compliance."}


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def persist_raw_jsonl(
    path: Path, raw: str, *, enabled: bool, max_bytes: int
) -> dict[str, Any]:
    """Optionally persist bounded Pi JSONL without affecting in-memory parsing."""
    raw_bytes = raw.encode("utf-8")
    metadata: dict[str, Any] = {
        "enabled": enabled,
        "persisted": False,
        "original_bytes": len(raw_bytes),
        "stored_bytes": 0,
        "truncated": False,
        "max_bytes": max_bytes,
    }
    if not enabled:
        return metadata
    if max_bytes < MIN_RAW_JSONL_MAX_BYTES:
        raise ValueError(
            f"raw JSONL limit must be at least {MIN_RAW_JSONL_MAX_BYTES} bytes"
        )

    if len(raw_bytes) <= max_bytes:
        path.write_bytes(raw_bytes)
        stored_bytes = len(raw_bytes)
    else:
        marker = {
            "type": "write_craft_raw_log_truncated",
            "original_bytes": len(raw_bytes),
            "max_bytes": max_bytes,
            "retention": "last_complete_json_lines",
        }
        marker_bytes = (
            json.dumps(marker, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        retained: list[bytes] = []
        remaining = max_bytes - len(marker_bytes)
        for line in reversed(raw.splitlines()):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError:
                continue
            encoded = (line + "\n").encode("utf-8")
            if len(encoded) <= remaining:
                retained.append(encoded)
                remaining -= len(encoded)
        payload = marker_bytes + b"".join(reversed(retained))
        path.write_bytes(payload)
        stored_bytes = len(payload)
        metadata["truncated"] = True

    metadata.update(
        {
            "persisted": True,
            "path": path.name,
            "stored_bytes": stored_bytes,
        }
    )
    return metadata


def run_fact_review(
    *,
    case: dict[str, Any],
    source: str,
    candidate: str,
    model: str,
    thinking: str,
    timeout: int,
    output_dir: Path,
    keep_raw_jsonl: bool = False,
    raw_jsonl_max_bytes: int = DEFAULT_RAW_JSONL_MAX_BYTES,
    focused_editorial: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    focused = None
    if focused_editorial:
        focused = run_editorial_review(
            case=case, candidate=candidate, model=model, thinking=thinking,
            timeout=timeout, output_dir=output_dir / "editorial",
            keep_raw_jsonl=keep_raw_jsonl, raw_jsonl_max_bytes=raw_jsonl_max_bytes,
        )
        if focused["status"] == "ERROR":
            return {"status": "ERROR", "error": focused["error"],
                    "review": {"model": model, "thinking": thinking,
                               "focused_editorial": focused["review"],
                               "usage_summary": focused["review"]["usage_summary"]}}
    judged = run_command(
        pi_args(
            prompt=judge_prompt(case, source, candidate,
                                focused["editorial"]["issues"] if focused else None),
            model=model,
            thinking=thinking,
            with_skill=False,
            structured_tool=FACT_JUDGMENT_TOOL,
        ),
        timeout,
    )
    raw_log = persist_raw_jsonl(
        output_dir / "judge.jsonl",
        judged["stdout"],
        enabled=keep_raw_jsonl,
        max_bytes=raw_jsonl_max_bytes,
    )
    (output_dir / "judge.stderr.txt").write_text(
        judged["stderr"], encoding="utf-8"
    )
    review: dict[str, Any] = {
        "model": model,
        "thinking": thinking,
        "returncode": judged["returncode"],
        "duration_seconds": judged["duration_seconds"],
        "timed_out": judged["timed_out"],
        "structured_output": structured_output_metadata(
            FACT_JUDGMENT_TOOL, judged["stdout"]
        ),
        "usage_summary": assistant_usage_summary(judged["stdout"]),
        "raw_log": raw_log,
    }
    if focused:
        review["focused_editorial"] = focused["review"]
        review["usage_summary"] = merge_usage_summaries(
            review["usage_summary"], focused["review"]["usage_summary"]
        )
    result: dict[str, Any] = {"status": "ERROR", "review": review}
    if judged["timed_out"]:
        result["error"] = "judge timed out"
        return result
    if judged["returncode"] != 0:
        result["error"] = f"judge exited with {judged['returncode']}"
        return result
    try:
        judge_final = extract_final_tool_call(judged["stdout"], FACT_JUDGMENT_TOOL)
        judgment = parse_judgment(
            json.dumps(
                normalize_fact_tool_arguments(judge_final["arguments"], case, require_editorial=True),
                ensure_ascii=False,
            ),
            case,
        )
        judgment = apply_deterministic_checks(judgment, case, candidate)
        judgment["editorial"] = validate_editorial(judgment["editorial"], candidate)
        if focused is not None:
            proposed = {
                (issue["kind"], issue["quote"])
                for issue in focused["editorial"]["issues"]
            }
            if any(
                (issue["kind"], issue["quote"]) not in proposed
                for issue in judgment["editorial"]["issues"]
            ):
                # Reject the review contract, rather than silently dropping a
                # finding or letting a new preference consume a revision.
                raise ContractError(
                    "source adjudication introduced an unproposed editorial issue"
                )
    except ContractError as exc:
        result["error"] = str(exc)
        return result

    write_json(output_dir / "judgment.json", judgment)
    review["message"] = safe_message_metadata(judge_final["message"])
    result.update(
        {
            "status": judgment["status"],
            "judgment": judgment,
            "judgment_sha256": sha256_text(canonical_json(judgment)),
            "blocking_issues": judgment["blocking_issues"],
        }
    )
    return result


def run_editorial_review(
    *, case: dict[str, Any], candidate: str, model: str, thinking: str,
    timeout: int, output_dir: Path,
    keep_raw_jsonl: bool = False,
    raw_jsonl_max_bytes: int = DEFAULT_RAW_JSONL_MAX_BYTES,
) -> dict[str, Any]:
    """Read the prose in a fresh context without the source-contract checklist."""
    prompt = f"""你是独立中文编辑，只检查成稿的结构、信息贡献和语言，不核验项目事实、不提出新方案、不重写全文。
逐段检查新增信息，比较开头与后文、场景与流程/表格、标题与段落是否同义重述；检查决定性理由是否被实现细节隔开。
结论、建议或决定请求可以先于详细论据，不要要求读完所有依据再看到请求；没有标题或表格本身不是缺陷。
重复问题在 reason 中同时指出另一处对应原句及两处为何没有不同用途。独立阅读的摘要、新增验收动作或不同适用条件的重申可以保留；场景中的执行人或复核节点不因验收表提到相同条件就应被删除。不要为偏好凑问题。
按信息作用判断删除：提案意图不等于实际实施状态，前提不等于它的行动含义，执行说明不等于验收检查；删去其中一处会失去这些区别时，不是冗余。只报告能够定位实际理解或判断障碍的问题，正常可懂的句式不因另有写法就需要修改，不以猜测读者会误读作为证据。没有原始来源，不建议补造新的因果或职责关系。
不同作用的信息可以在同一段里，通过清楚的因果、条件或时序关系区分即可。不要求每一种信息另起段落，也不因缺少分类标签就判定逻辑混乱；必须指出实际不成立或不清楚的关系。
quote 复制候选稿的一小段连续原文，不补标点、不改写、不拼接。没有发现问题则 issues 为空。
只输出 JSON：{{"schema":"write-craft.editorial.v1","issues":[{{"kind":"redundancy|irrelevant_commentary|structure|sentence|wording|presentation","quote":"原文","reason":"具体问题","suggestion":"不改变原意的编辑方向"}}]}}。

【用户请求】
{case['request']}

【候选稿】
{candidate}
"""
    output_dir.mkdir(parents=True, exist_ok=False)
    write_json(output_dir / "input.json", {
        "case_id": case["id"], "candidate_sha256": sha256_text(candidate),
        "prompt_sha256": sha256_text(prompt),
    })
    response = run_command(pi_args(prompt=prompt, model=model, thinking=thinking,
                                  with_skill=False), timeout)
    review = {key: response[key] for key in ("returncode", "duration_seconds", "timed_out")}
    review.update({"model": model, "thinking": thinking,
                   "usage_summary": assistant_usage_summary(response["stdout"]),
                   "raw_log": persist_raw_jsonl(output_dir / "editorial.jsonl", response["stdout"],
                                                enabled=keep_raw_jsonl, max_bytes=raw_jsonl_max_bytes)})
    result: dict[str, Any] = {"status": "ERROR", "review": review}
    try:
        if response["timed_out"] or response["returncode"] != 0:
            raise ContractError("focused editorial review did not complete")
        final = extract_final_assistant(response["stdout"])
        review["message"] = safe_message_metadata(final["message"])
        payload = json.loads(strip_json_fence(final["text"]))
        write_json(output_dir / "unvalidated.json", payload)
        result["editorial"] = validate_editorial(payload, candidate)
        result["status"] = result["editorial"]["status"]
    except (ContractError, json.JSONDecodeError) as exc:
        result["error"] = str(exc)
    write_json(output_dir / "result.json", result)
    return result


def git_state() -> dict[str, Any]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    return {
        "revision": revision.stdout.strip() if revision.returncode == 0 else None,
        "dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
    }


def pi_version() -> str | None:
    completed = subprocess.run(
        ["pi", "--version"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def evaluate_case(
    *,
    case: dict[str, Any],
    run_index: int,
    output_root: Path,
    model: str,
    judge_model: str,
    reader_model: str,
    reader_judge_model: str,
    thinking: str,
    judge_thinking: str,
    reader_thinking: str,
    reader_judge_thinking: str,
    timeout: int,
    keep_raw_jsonl: bool = False,
    raw_jsonl_max_bytes: int = DEFAULT_RAW_JSONL_MAX_BYTES,
    focused_editorial: bool = False,
) -> dict[str, Any]:
    sources = case_sources(case)
    source = format_sources(sources, legacy_plain="sources" not in case)
    max_revisions = case.get("max_revisions", 0)
    case_dir = output_root / f"{case['id']}--{run_index}"
    case_dir.mkdir(parents=True)
    input_payload = {
        "case": case,
        "case_digest": resolved_case_digest(case, sources),
        "run_index": run_index,
    }
    if "sources" in case:
        input_payload["sources"] = sources
    else:
        input_payload["source"] = sources[0]["text"]
    write_json(case_dir / "input.json", input_payload)

    generated = run_command(
        pi_args(
            prompt=generator_prompt(case, source),
            model=model,
            thinking=thinking,
            with_skill=True,
        ),
        timeout,
    )
    generator_raw_log = persist_raw_jsonl(
        case_dir / "generator.jsonl",
        generated["stdout"],
        enabled=keep_raw_jsonl,
        max_bytes=raw_jsonl_max_bytes,
    )
    (case_dir / "generator.stderr.txt").write_text(generated["stderr"], encoding="utf-8")
    result: dict[str, Any] = {
        "case_id": case["id"],
        "run_index": run_index,
        "status": "ERROR",
        "case_digest": input_payload["case_digest"],
        "generator": {
            "model": model,
            "thinking": thinking,
            "returncode": generated["returncode"],
            "duration_seconds": generated["duration_seconds"],
            "timed_out": generated["timed_out"],
            "usage_summary": assistant_usage_summary(generated["stdout"]),
            "raw_log": generator_raw_log,
            "skill_read_trace": skill_read_trace(generated["stdout"]),
        },
        "judge": {"model": judge_model, "thinking": judge_thinking},
        "revision_policy": {"max_revisions": max_revisions},
        "focused_editorial": focused_editorial,
        "revisions_used": 0,
        "stages": {
            "generation": "ERROR",
            "fact_review": "NOT_RUN",
            "revision": "NOT_RUN",
            "reader": "NOT_RUN",
            "reader_review": "NOT_RUN",
        },
        "usage_summary": assistant_usage_summary(generated["stdout"]),
    }
    if generated["timed_out"]:
        result["error"] = "generator timed out"
        write_json(case_dir / "result.json", result)
        return result
    if generated["returncode"] != 0:
        result["error"] = f"generator exited with {generated['returncode']}"
        write_json(case_dir / "result.json", result)
        return result
    try:
        final = extract_final_assistant(generated["stdout"])
    except ContractError as exc:
        result["error"] = str(exc)
        write_json(case_dir / "result.json", result)
        return result

    candidate = final["text"]
    (case_dir / "candidate.md").write_text(candidate + "\n", encoding="utf-8")
    if max_revisions:
        initial_dir = case_dir / "initial"
        initial_dir.mkdir()
        (initial_dir / "candidate.md").write_text(candidate + "\n", encoding="utf-8")
    else:
        initial_dir = case_dir
    result["generator"]["message"] = safe_message_metadata(final["message"])
    result["candidate_sha256"] = sha256_text(candidate)
    result["stages"]["generation"] = "PASS"
    if isinstance(case.get("limits"), dict):
        result["candidate_metrics"] = {
            "han_characters": han_character_count(candidate)
        }

    fact_review = run_fact_review(
        case=case,
        source=source,
        candidate=candidate,
        model=judge_model,
        thinking=judge_thinking,
        timeout=timeout,
        output_dir=initial_dir,
        focused_editorial=focused_editorial,
        keep_raw_jsonl=keep_raw_jsonl,
        raw_jsonl_max_bytes=raw_jsonl_max_bytes,
    )
    result["judge"] = fact_review["review"]
    result["usage_summary"] = merge_usage_summaries(
        result["usage_summary"], fact_review["review"]["usage_summary"]
    )
    if fact_review["status"] == "ERROR":
        result["stages"]["fact_review"] = "ERROR"
        result["error"] = fact_review["error"]
        write_json(case_dir / "result.json", result)
        return result

    judgment = fact_review["judgment"]
    result["status"] = judgment["status"]
    result["blocking_issues"] = judgment["blocking_issues"]
    result["stages"]["fact_review"] = judgment["status"]
    if max_revisions:
        result["initial_attempt"] = {
            "candidate_sha256": result["candidate_sha256"],
            "judgment_sha256": fact_review["judgment_sha256"],
            "status": judgment["status"],
            "blocking_issues": judgment["blocking_issues"],
            "judge": fact_review["review"],
            "editorial": judgment["editorial"],
        }

    if max_revisions == 1 and (
        judgment["status"] != "PASS"
        or judgment["editorial"]["status"] == "NEEDS_EDIT"
    ):
        revision_dir = case_dir / "revision-1"
        revision_dir.mkdir()
        revised = run_command(
            pi_args(
                prompt=revision_prompt(case, source, candidate, judgment),
                model=model,
                thinking=thinking,
                with_skill=True,
            ),
            timeout,
        )
        revision_raw_log = persist_raw_jsonl(
            revision_dir / "generator.jsonl",
            revised["stdout"],
            enabled=keep_raw_jsonl,
            max_bytes=raw_jsonl_max_bytes,
        )
        (revision_dir / "generator.stderr.txt").write_text(
            revised["stderr"], encoding="utf-8"
        )
        result["revision"] = {
            "model": model,
            "thinking": thinking,
            "returncode": revised["returncode"],
            "duration_seconds": revised["duration_seconds"],
            "timed_out": revised["timed_out"],
            "usage_summary": assistant_usage_summary(revised["stdout"]),
            "raw_log": revision_raw_log,
            "skill_read_trace": skill_read_trace(revised["stdout"]),
        }
        result["usage_summary"] = merge_usage_summaries(
            result["usage_summary"], result["revision"]["usage_summary"]
        )
        if revised["timed_out"]:
            result["stages"]["revision"] = "ERROR"
            result["status"] = "ERROR"
            result["error"] = "revision timed out"
            write_json(case_dir / "result.json", result)
            return result
        if revised["returncode"] != 0:
            result["stages"]["revision"] = "ERROR"
            result["status"] = "ERROR"
            result["error"] = f"revision exited with {revised['returncode']}"
            write_json(case_dir / "result.json", result)
            return result
        try:
            revised_final = extract_final_assistant(revised["stdout"])
        except ContractError as exc:
            result["stages"]["revision"] = "ERROR"
            result["status"] = "ERROR"
            result["error"] = str(exc)
            write_json(case_dir / "result.json", result)
            return result

        candidate = revised_final["text"]
        (revision_dir / "candidate.md").write_text(
            candidate + "\n", encoding="utf-8"
        )
        (case_dir / "candidate.md").write_text(candidate + "\n", encoding="utf-8")
        result["revision"]["message"] = safe_message_metadata(
            revised_final["message"]
        )
        result["revisions_used"] = 1
        result["stages"]["revision"] = "PASS"
        result["candidate_sha256"] = sha256_text(candidate)
        if isinstance(case.get("limits"), dict):
            result["candidate_metrics"] = {
                "han_characters": han_character_count(candidate)
            }

        fact_review = run_fact_review(
            case=case,
            source=source,
            candidate=candidate,
            model=judge_model,
            thinking=judge_thinking,
            timeout=timeout,
            output_dir=revision_dir,
            focused_editorial=focused_editorial,
            keep_raw_jsonl=keep_raw_jsonl,
            raw_jsonl_max_bytes=raw_jsonl_max_bytes,
        )
        result["judge"] = fact_review["review"]
        result["usage_summary"] = merge_usage_summaries(
            result["usage_summary"], fact_review["review"]["usage_summary"]
        )
        if fact_review["status"] == "ERROR":
            result["stages"]["fact_review"] = "ERROR"
            result["status"] = "ERROR"
            result["error"] = fact_review["error"]
            write_json(case_dir / "result.json", result)
            return result
        judgment = fact_review["judgment"]

    write_json(case_dir / "judgment.json", judgment)
    result["judgment_sha256"] = fact_review["judgment_sha256"]
    result["editorial"] = judgment["editorial"]
    result["status"] = judgment["status"]
    result["blocking_issues"] = judgment["blocking_issues"]
    result["stages"]["fact_review"] = judgment["status"]
    if judgment["status"] != "PASS" or not isinstance(case.get("reader_test"), dict):
        write_json(case_dir / "result.json", result)
        return result

    read = run_command(
        pi_args(
            prompt=reader_prompt(case, candidate),
            model=reader_model,
            thinking=reader_thinking,
            with_skill=False,
            structured_tool=READER_RESPONSE_TOOL,
        ),
        timeout,
    )
    reader_raw_log = persist_raw_jsonl(
        case_dir / "reader.jsonl",
        read["stdout"],
        enabled=keep_raw_jsonl,
        max_bytes=raw_jsonl_max_bytes,
    )
    (case_dir / "reader.stderr.txt").write_text(read["stderr"], encoding="utf-8")
    result["reader"] = {
        "model": reader_model,
        "thinking": reader_thinking,
        "returncode": read["returncode"],
        "duration_seconds": read["duration_seconds"],
        "timed_out": read["timed_out"],
        "structured_output": structured_output_metadata(
            READER_RESPONSE_TOOL, read["stdout"]
        ),
        "usage_summary": assistant_usage_summary(read["stdout"]),
        "raw_log": reader_raw_log,
    }
    result["usage_summary"] = merge_usage_summaries(
        result["usage_summary"], result["reader"]["usage_summary"]
    )
    if read["timed_out"]:
        result["stages"]["reader"] = "ERROR"
        result["status"] = "ERROR"
        result["error"] = "reader timed out"
        write_json(case_dir / "result.json", result)
        return result
    if read["returncode"] != 0:
        result["stages"]["reader"] = "ERROR"
        result["status"] = "ERROR"
        result["error"] = f"reader exited with {read['returncode']}"
        write_json(case_dir / "result.json", result)
        return result
    try:
        reader_final = extract_final_tool_call(read["stdout"], READER_RESPONSE_TOOL)
        reader_response = parse_reader_response(
            json.dumps(reader_final["arguments"], ensure_ascii=False), case
        )
    except ContractError as exc:
        result["stages"]["reader"] = "ERROR"
        result["status"] = "ERROR"
        result["error"] = str(exc)
        write_json(case_dir / "result.json", result)
        return result
    write_json(case_dir / "reader-response.json", reader_response)
    result["reader_response"] = reader_response
    result["reader"]["message"] = safe_message_metadata(reader_final["message"])
    result["reader_response_sha256"] = sha256_text(canonical_json(reader_response))
    result["stages"]["reader"] = "PASS"

    reader_judged = run_command(
        pi_args(
            prompt=reader_judgment_prompt(case, source, candidate, reader_response),
            model=reader_judge_model,
            thinking=reader_judge_thinking,
            with_skill=False,
            structured_tool=READER_JUDGMENT_TOOL,
        ),
        timeout,
    )
    reader_judge_raw_log = persist_raw_jsonl(
        case_dir / "reader-judge.jsonl",
        reader_judged["stdout"],
        enabled=keep_raw_jsonl,
        max_bytes=raw_jsonl_max_bytes,
    )
    (case_dir / "reader-judge.stderr.txt").write_text(
        reader_judged["stderr"], encoding="utf-8"
    )
    result["reader_judge"] = {
        "model": reader_judge_model,
        "thinking": reader_judge_thinking,
        "returncode": reader_judged["returncode"],
        "duration_seconds": reader_judged["duration_seconds"],
        "timed_out": reader_judged["timed_out"],
        "structured_output": structured_output_metadata(
            READER_JUDGMENT_TOOL, reader_judged["stdout"]
        ),
        "usage_summary": assistant_usage_summary(reader_judged["stdout"]),
        "raw_log": reader_judge_raw_log,
    }
    result["usage_summary"] = merge_usage_summaries(
        result["usage_summary"], result["reader_judge"]["usage_summary"]
    )
    if reader_judged["timed_out"]:
        result["stages"]["reader_review"] = "ERROR"
        result["status"] = "ERROR"
        result["error"] = "reader judge timed out"
        write_json(case_dir / "result.json", result)
        return result
    if reader_judged["returncode"] != 0:
        result["stages"]["reader_review"] = "ERROR"
        result["status"] = "ERROR"
        result["error"] = f"reader judge exited with {reader_judged['returncode']}"
        write_json(case_dir / "result.json", result)
        return result
    try:
        reader_judge_final = extract_final_tool_call(
            reader_judged["stdout"], READER_JUDGMENT_TOOL
        )
        reader_judgment = parse_reader_judgment(
            json.dumps(reader_judge_final["arguments"], ensure_ascii=False), case
        )
    except ContractError as exc:
        result["stages"]["reader_review"] = "ERROR"
        result["status"] = "ERROR"
        result["error"] = str(exc)
        write_json(case_dir / "result.json", result)
        return result
    write_json(case_dir / "reader-judgment.json", reader_judgment)
    result["reader_judgment"] = reader_judgment
    result["reader_judge"]["message"] = safe_message_metadata(
        reader_judge_final["message"]
    )
    result["reader_judgment_sha256"] = sha256_text(canonical_json(reader_judgment))
    result["stages"]["reader_review"] = reader_judgment["status"]
    result["status"] = aggregate_status(
        [judgment["status"], reader_judgment["status"]]
    )
    result["blocking_issues"] = judgment["blocking_issues"] + reader_judgment[
        "blocking_issues"
    ]
    write_json(case_dir / "result.json", result)
    return result


def calibrate_judge(
    *,
    fixtures: list[dict[str, Any]],
    output_root: Path,
    judge_model: str,
    judge_thinking: str,
    timeout: int,
    keep_raw_jsonl: bool = False,
    raw_jsonl_max_bytes: int = DEFAULT_RAW_JSONL_MAX_BYTES,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    aborted_after_system_error = False
    for fixture in fixtures:
        fixture_dir = output_root / fixture["id"]
        fixture_dir.mkdir(parents=True)
        write_json(fixture_dir / "input.json", fixture)
        judged = run_command(
            pi_args(
                prompt=judge_prompt(
                    fixture["case"], fixture["source"], fixture["candidate"]
                ),
                model=judge_model,
                thinking=judge_thinking,
                with_skill=False,
                structured_tool=FACT_JUDGMENT_TOOL,
            ),
            timeout,
        )
        raw_log = persist_raw_jsonl(
            fixture_dir / "judge.jsonl",
            judged["stdout"],
            enabled=keep_raw_jsonl,
            max_bytes=raw_jsonl_max_bytes,
        )
        (fixture_dir / "judge.stderr.txt").write_text(
            judged["stderr"], encoding="utf-8"
        )
        result: dict[str, Any] = {
            "fixture_id": fixture["id"],
            "expected_status": fixture["expected_status"],
            "status": "ERROR",
            "judge": {
                "model": judge_model,
                "thinking": judge_thinking,
                "returncode": judged["returncode"],
                "duration_seconds": judged["duration_seconds"],
                "timed_out": judged["timed_out"],
                "structured_output": structured_output_metadata(
                    FACT_JUDGMENT_TOOL, judged["stdout"]
                ),
                "usage_summary": assistant_usage_summary(judged["stdout"]),
                "raw_log": raw_log,
            },
        }
        if judged["timed_out"]:
            result["error"] = "judge calibration timed out"
        elif judged["returncode"] != 0:
            result["error"] = f"judge calibration exited with {judged['returncode']}"
        else:
            try:
                judge_final = extract_final_tool_call(
                    judged["stdout"], FACT_JUDGMENT_TOOL
                )
                judgment = parse_judgment(
                    json.dumps(
                        normalize_fact_tool_arguments(
                            judge_final["arguments"], fixture["case"], require_editorial=True
                        ),
                        ensure_ascii=False,
                    ),
                    fixture["case"],
                )
                judgment["editorial"] = validate_editorial(judgment["editorial"], fixture["candidate"])
            except ContractError as exc:
                result["error"] = str(exc)
            else:
                write_json(fixture_dir / "judgment.json", judgment)
                result["judge"]["message"] = safe_message_metadata(
                    judge_final["message"]
                )
                result["judge_status"] = judgment["status"]
                result["editorial"] = judgment["editorial"]
                result["judgment_sha256"] = sha256_text(canonical_json(judgment))
                result["status"] = (
                    "PASS"
                    if judgment["status"] == fixture["expected_status"]
                    else "FAIL"
                )
                if (fixture.get("expected_editorial_status") is not None
                        and judgment["editorial"]["status"] != fixture["expected_editorial_status"]):
                    result["status"] = "FAIL"
                if result["status"] == "FAIL":
                    result["error"] = (
                        f"expected contract={fixture['expected_status']}, got {judgment['status']}; "
                        f"expected editorial={fixture.get('expected_editorial_status')}, "
                        f"got {judgment['editorial']['status']}"
                    )
        write_json(fixture_dir / "result.json", result)
        results.append(result)
        if result["status"] == "ERROR":
            aborted_after_system_error = True
            break

    completed_ids = {result["fixture_id"] for result in results}
    summary = {
        "schema": "write-craft.judge-calibration-run.v1",
        "finished_at": utc_now(),
        "judge": {"model": judge_model, "thinking": judge_thinking},
        "evaluator": evaluator_metadata(),
        "structured_output": structured_output_metadata(),
        "raw_jsonl": {
            "enabled": keep_raw_jsonl,
            "max_bytes_per_stage": raw_jsonl_max_bytes,
        },
        "selected_fixture_ids": [fixture["id"] for fixture in fixtures],
        "not_run_fixture_ids": [
            fixture["id"] for fixture in fixtures if fixture["id"] not in completed_ids
        ],
        "aborted_after_system_error": aborted_after_system_error,
        "usage_summary": merge_usage_summaries(
            *[
                result["judge"]["usage_summary"]
                for result in results
                if isinstance(result.get("judge"), dict)
                and isinstance(result["judge"].get("usage_summary"), dict)
            ]
        ),
        "status": aggregate_status([result["status"] for result in results]),
        "results": results,
    }
    write_json(output_root / "run.json", summary)
    return summary


def rejudge_case(
    *,
    case_dir: Path,
    judge_model: str,
    judge_thinking: str,
    timeout: int,
    keep_raw_jsonl: bool = False,
    raw_jsonl_max_bytes: int = DEFAULT_RAW_JSONL_MAX_BYTES,
) -> dict[str, Any]:
    case_dir = case_dir.resolve()
    input_path = case_dir / "input.json"
    candidate_path = case_dir / "candidate.md"
    result_path = case_dir / "result.json"
    if not input_path.is_file() or not candidate_path.is_file() or not result_path.is_file():
        raise ContractError(
            "--rejudge directory must contain input.json, candidate.md, and result.json"
        )
    try:
        input_text = input_path.read_text(encoding="utf-8")
        result_text = result_path.read_text(encoding="utf-8")
        input_payload = json.loads(input_text)
        original_result = json.loads(result_text)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"unable to read rejudge source artifacts: {exc}") from exc
    if not isinstance(input_payload, dict) or not isinstance(original_result, dict):
        raise ContractError("rejudge source artifacts must contain JSON objects")
    case = input_payload.get("case")
    if not isinstance(case, dict):
        raise ContractError("rejudge input.json is missing its case")
    sources = artifact_sources(input_payload, case)
    source = format_sources(sources, legacy_plain="sources" not in case)
    case_schema = SCHEMA if case.get("track") in VALID_TRACKS else "write-craft.behavior-cases.v2"
    contract_errors = validate_payload({"schema": case_schema, "cases": [case]})
    if contract_errors:
        raise ContractError("invalid rejudge case: " + "; ".join(contract_errors))
    case_digest = resolved_case_digest(case, sources)
    if input_payload.get("case_digest") != case_digest:
        raise ContractError("rejudge input case_digest does not match its case and sources")
    if original_result.get("case_id") != case.get("id"):
        raise ContractError("rejudge result case_id does not match input.json")
    if original_result.get("case_digest") != case_digest:
        raise ContractError("rejudge result case_digest does not match input.json")
    candidate = candidate_path.read_text(encoding="utf-8").strip()
    if not candidate:
        raise ContractError("rejudge candidate.md is empty")
    candidate_sha256 = sha256_text(candidate)
    if original_result.get("candidate_sha256") != candidate_sha256:
        raise ContractError("rejudge candidate.md does not match the original result hash")

    index = 1
    while (case_dir / f"rejudge-{index}").exists():
        index += 1
    output_dir = case_dir / f"rejudge-{index}"
    output_dir.mkdir()
    judged = run_command(
        pi_args(
            prompt=judge_prompt(case, source, candidate),
            model=judge_model,
            thinking=judge_thinking,
            with_skill=False,
            structured_tool=FACT_JUDGMENT_TOOL,
        ),
        timeout,
    )
    raw_log = persist_raw_jsonl(
        output_dir / "judge.jsonl",
        judged["stdout"],
        enabled=keep_raw_jsonl,
        max_bytes=raw_jsonl_max_bytes,
    )
    (output_dir / "judge.stderr.txt").write_text(judged["stderr"], encoding="utf-8")
    result: dict[str, Any] = {
        "schema": "write-craft.rejudge.v1",
        "case_id": case.get("id"),
        "source_case_dir": str(case_dir),
        "source_input_sha256": sha256_text(input_text),
        "source_result_sha256": sha256_text(result_text),
        "evaluator": evaluator_metadata(),
        "case_digest": case_digest,
        "candidate_sha256": candidate_sha256,
        "judge": {
            "model": judge_model,
            "thinking": judge_thinking,
            "returncode": judged["returncode"],
            "duration_seconds": judged["duration_seconds"],
            "timed_out": judged["timed_out"],
            "structured_output": structured_output_metadata(
                FACT_JUDGMENT_TOOL, judged["stdout"]
            ),
            "usage_summary": assistant_usage_summary(judged["stdout"]),
            "raw_log": raw_log,
        },
        "status": "ERROR",
        "usage_summary": assistant_usage_summary(judged["stdout"]),
    }
    if isinstance(case.get("limits"), dict):
        result["candidate_metrics"] = {
            "han_characters": han_character_count(candidate)
        }
    if judged["timed_out"]:
        result["error"] = "judge timed out"
    elif judged["returncode"] != 0:
        result["error"] = f"judge exited with {judged['returncode']}"
    else:
        try:
            judge_final = extract_final_tool_call(
                judged["stdout"], FACT_JUDGMENT_TOOL
            )
            judgment = parse_judgment(
                json.dumps(
                    normalize_fact_tool_arguments(judge_final["arguments"], case, require_editorial=True),
                    ensure_ascii=False,
                ),
                case,
            )
            judgment = apply_deterministic_checks(judgment, case, candidate)
            judgment["editorial"] = validate_editorial(judgment["editorial"], candidate)
        except ContractError as exc:
            result["error"] = str(exc)
        else:
            write_json(output_dir / "judgment.json", judgment)
            result["judge"]["message"] = safe_message_metadata(judge_final["message"])
            result["judgment_sha256"] = sha256_text(canonical_json(judgment))
            result["status"] = judgment["status"]
            result["editorial"] = judgment["editorial"]
            result["blocking_issues"] = judgment["blocking_issues"]
    write_json(output_dir / "result.json", result)
    result["output"] = str(output_dir)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Pi generator model, e.g. deepseek/deepseek-v4-flash")
    parser.add_argument(
        "--judge-model",
        required=True,
        help="Pi judge model, e.g. deepseek/deepseek-v4-flash",
    )
    parser.add_argument(
        "--reader-model",
        help="blind reader model; defaults to --judge-model when reader_test is present",
    )
    parser.add_argument(
        "--reader-judge-model",
        help="reader-comprehension judge; defaults to --judge-model",
    )
    parser.add_argument("--suite", choices=sorted(VALID_SUITES), default="smoke")
    parser.add_argument("--track", choices=sorted(VALID_TRACKS))
    parser.add_argument("--case", action="append", default=[], dest="case_ids")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--thinking", default="medium")
    parser.add_argument("--judge-thinking", default="high")
    parser.add_argument("--reader-thinking", default="medium")
    parser.add_argument("--reader-judge-thinking", default="high")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--focused-editorial", action="store_true",
                        help="also review prose in a separate context; share the existing revision budget")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--keep-raw-jsonl",
        action="store_true",
        help="persist bounded raw Pi JSONL for debugging; disabled by default",
    )
    parser.add_argument(
        "--raw-jsonl-max-bytes",
        type=int,
        default=DEFAULT_RAW_JSONL_MAX_BYTES,
        help=(
            "maximum bytes kept for each opted-in raw JSONL file "
            f"(default: {DEFAULT_RAW_JSONL_MAX_BYTES})"
        ),
    )
    parser.add_argument(
        "--rejudge",
        type=Path,
        help="explicitly rejudge an existing case artifact without regenerating it",
    )
    parser.add_argument(
        "--calibrate-judge",
        action="store_true",
        help="run the positive and negative judge fixtures without generating drafts",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.runs < 1:
        print("ERROR: --runs must be at least 1", file=sys.stderr)
        return 2
    if args.timeout < 1:
        print("ERROR: --timeout must be at least 1", file=sys.stderr)
        return 2
    if args.raw_jsonl_max_bytes < MIN_RAW_JSONL_MAX_BYTES:
        print(
            "ERROR: --raw-jsonl-max-bytes must be at least "
            f"{MIN_RAW_JSONL_MAX_BYTES}",
            file=sys.stderr,
        )
        return 2
    if args.rejudge and args.calibrate_judge:
        print("ERROR: --rejudge and --calibrate-judge are mutually exclusive", file=sys.stderr)
        return 2
    if args.focused_editorial and (args.rejudge or args.calibrate_judge):
        print("ERROR: --focused-editorial requires a generation run", file=sys.stderr)
        return 2
    if args.calibrate_judge and args.case_ids:
        print("ERROR: --case selects generation cases, not judge calibration fixtures", file=sys.stderr)
        return 2
    if args.rejudge:
        try:
            result = rejudge_case(
                case_dir=args.rejudge,
                judge_model=args.judge_model,
                judge_thinking=args.judge_thinking,
                timeout=args.timeout,
                keep_raw_jsonl=args.keep_raw_jsonl,
                raw_jsonl_max_bytes=args.raw_jsonl_max_bytes,
            )
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] == "PASS" else 1
    if args.calibrate_judge:
        try:
            fixtures = load_judge_fixtures()
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_root = (
            args.output_dir.resolve()
            if args.output_dir
            else ROOT
            / ".artifacts"
            / "write-craft-evals"
            / f"{timestamp}-judge-calibration"
        )
        if output_root.exists():
            print(f"ERROR: output directory already exists: {output_root}", file=sys.stderr)
            return 2
        output_root.mkdir(parents=True)
        summary = calibrate_judge(
            fixtures=fixtures,
            output_root=output_root,
            judge_model=args.judge_model,
            judge_thinking=args.judge_thinking,
            timeout=args.timeout,
            keep_raw_jsonl=args.keep_raw_jsonl,
            raw_jsonl_max_bytes=args.raw_jsonl_max_bytes,
        )
        print(
            json.dumps(
                {"status": summary["status"], "output": str(output_root)},
                ensure_ascii=False,
            )
        )
        return 0 if summary["status"] == "PASS" else 1
    if not args.model:
        print("ERROR: --model is required unless --rejudge is used", file=sys.stderr)
        return 2
    try:
        cases = select_cases(load_cases(), args.suite, args.case_ids, args.track)
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_root = (
        args.output_dir.resolve()
        if args.output_dir
        else ROOT / ".artifacts" / "write-craft-evals" / timestamp
    )
    if output_root.exists():
        print(f"ERROR: output directory already exists: {output_root}", file=sys.stderr)
        return 2
    output_root.mkdir(parents=True)

    started_at = utc_now()
    reader_model = args.reader_model or args.judge_model
    reader_judge_model = args.reader_judge_model or args.judge_model
    results: list[dict[str, Any]] = []
    aborted = False
    for case in cases:
        for run_index in range(1, args.runs + 1):
            print(f"RUN {case['id']} #{run_index}", file=sys.stderr, flush=True)
            result = evaluate_case(
                case=case,
                run_index=run_index,
                output_root=output_root,
                model=args.model,
                judge_model=args.judge_model,
                reader_model=reader_model,
                reader_judge_model=reader_judge_model,
                thinking=args.thinking,
                judge_thinking=args.judge_thinking,
                reader_thinking=args.reader_thinking,
                reader_judge_thinking=args.reader_judge_thinking,
                timeout=args.timeout,
                keep_raw_jsonl=args.keep_raw_jsonl,
                raw_jsonl_max_bytes=args.raw_jsonl_max_bytes,
                focused_editorial=args.focused_editorial,
            )
            results.append(result)
            editorial_state = result.get("editorial", {}).get("status", "NOT_EVALUATED")
            print(f"  {result['status']} / editorial={editorial_state}", file=sys.stderr, flush=True)
            if result["status"] == "ERROR":
                aborted = True
                break
        if aborted:
            break

    summary = {
        "schema": "write-craft.eval-run.v1",
        "started_at": started_at,
        "finished_at": utc_now(),
        "pi_version": pi_version(),
        "evaluator": evaluator_metadata(),
        "structured_output": structured_output_metadata(),
        "git": git_state(),
        "skill_sha256": skill_digest(),
        "cases_schema": SCHEMA,
        "suite": args.suite,
        "track": args.track or "all",
        "selected_case_ids": [case["id"] for case in cases],
        "runs_per_case": args.runs,
        "generator": {"model": args.model, "thinking": args.thinking},
        "judge": {"model": args.judge_model, "thinking": args.judge_thinking},
        "reader": {"model": reader_model, "thinking": args.reader_thinking},
        "reader_judge": {
            "model": reader_judge_model,
            "thinking": args.reader_judge_thinking,
        },
        "timeout_seconds": args.timeout,
        "raw_jsonl": {
            "enabled": args.keep_raw_jsonl,
            "max_bytes_per_stage": args.raw_jsonl_max_bytes,
        },
        "usage_summary": merge_usage_summaries(
            *[
                result["usage_summary"]
                for result in results
                if isinstance(result.get("usage_summary"), dict)
            ]
        ),
        "aborted_after_system_error": aborted,
        "focused_editorial": args.focused_editorial,
        "editorial_status": (
            "NOT_EVALUATED" if aborted or any("editorial" not in item for item in results)
            else "NEEDS_EDIT" if any(item["editorial"]["status"] == "NEEDS_EDIT" for item in results)
            else "NO_ISSUES_FOUND"
        ),
        "status": aggregate_status([item["status"] for item in results]),
        "results": results,
    }
    write_json(output_root / "run.json", summary)
    print(json.dumps({"status": summary["status"], "output": str(output_root)}, ensure_ascii=False))
    return 0 if (summary["status"] == "PASS" and (
        not args.focused_editorial or summary["editorial_status"] == "NO_ISSUES_FOUND"
    )) else 1


if __name__ == "__main__":
    raise SystemExit(main())
