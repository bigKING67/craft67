"""Shared, deterministic contracts for Write Craft behavior evaluation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "write-craft.behavior-cases.v3"
SUPPORTED_SCHEMAS = {"write-craft.behavior-cases.v2", SCHEMA}
JUDGMENT_SCHEMA = "write-craft.judgment.v1"
READER_RESPONSE_SCHEMA = "write-craft.reader-response.v1"
READER_JUDGMENT_SCHEMA = "write-craft.reader-judgment.v1"
VALID_SUITES = {"smoke", "full"}
VALID_TRACKS = {"regression", "exploration"}
VALID_STATUSES = {"PASS", "FAIL", "UNCERTAIN"}
FINAL_STATUSES = VALID_STATUSES | {"ERROR", "NOT_RUN"}
VALID_UNKNOWN_STATES = {"not_stated", "explicitly_unknown"}
SEMANTIC_LIST_FIELDS = {
    "facts",
    "allowed_inferences",
    "forbidden_inferences",
    "reader_truths",
    "reader_misreadings",
}


class ContractError(ValueError):
    """Raised when an evaluation contract or model response is invalid."""


def semantic_contract_errors(value: object, label: str) -> list[str]:
    """Validate an optional human-authored semantic acceptance ledger."""

    if value is None:
        return []
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    expected_fields = SEMANTIC_LIST_FIELDS | {"unknowns"}
    if set(value) != expected_fields:
        return [f"{label} must contain exactly {sorted(expected_fields)}"]

    errors: list[str] = []
    for field in sorted(SEMANTIC_LIST_FIELDS):
        items = value.get(field)
        if (
            not isinstance(items, list)
            or not all(isinstance(item, str) and item.strip() for item in items)
            or len(items) != len(set(items))
        ):
            errors.append(f"{label}.{field} must be unique non-empty strings")
    facts = value.get("facts")
    forbidden = value.get("forbidden_inferences")
    if isinstance(facts, list) and not facts:
        errors.append(f"{label}.facts must not be empty")
    if isinstance(forbidden, list) and not forbidden:
        errors.append(f"{label}.forbidden_inferences must not be empty")

    unknowns = value.get("unknowns")
    if not isinstance(unknowns, list):
        errors.append(f"{label}.unknowns must be an array")
    else:
        topics: list[str] = []
        for item in unknowns:
            if not isinstance(item, dict) or set(item) != {"topic", "state"}:
                errors.append(f"{label}.unknowns entries need only topic and state")
                continue
            topic = item.get("topic")
            state = item.get("state")
            if not isinstance(topic, str) or not topic.strip():
                errors.append(f"{label}.unknowns topic must be non-empty")
            else:
                topics.append(topic)
            if state not in VALID_UNKNOWN_STATES:
                errors.append(
                    f"{label}.unknowns state must be one of {sorted(VALID_UNKNOWN_STATES)}"
                )
        if len(topics) != len(set(topics)):
            errors.append(f"{label}.unknowns topics must be unique")
    return errors


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def han_character_count(value: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", value))


def resolve_fixture(root: Path, raw_path: str) -> Path:
    fixture_root = (root / "evals" / "fixtures").resolve()
    candidate = (root / raw_path).resolve()
    try:
        candidate.relative_to(fixture_root)
    except ValueError as exc:
        raise ContractError(f"source_file must stay under evals/fixtures: {raw_path}") from exc
    if not candidate.is_file():
        raise ContractError(f"source_file does not exist: {raw_path}")
    return candidate


def case_sources(case: dict[str, Any], root: Path = ROOT) -> list[dict[str, str]]:
    """Resolve one legacy source or a v3 source collection into frozen text."""

    has_source = isinstance(case.get("source"), str) and bool(case["source"].strip())
    has_source_file = isinstance(case.get("source_file"), str) and bool(
        case["source_file"].strip()
    )
    has_sources = isinstance(case.get("sources"), list) and bool(case["sources"])
    if sum((has_source, has_source_file, has_sources)) != 1:
        raise ContractError(
            "case must define exactly one of source, source_file, or sources"
        )

    if has_source:
        text = case["source"]
        return [
            {
                "source_id": "source-1",
                "text": text,
                "text_sha256": sha256_text(text),
            }
        ]
    if has_source_file:
        text = resolve_fixture(root, case["source_file"]).read_text(encoding="utf-8")
        return [
            {
                "source_id": "source-1",
                "text": text,
                "text_sha256": sha256_text(text),
            }
        ]

    resolved: list[dict[str, str]] = []
    raw_sources = case.get("sources")
    if not isinstance(raw_sources, list):
        raise ContractError("sources must be a non-empty list")
    for item in raw_sources:
        if not isinstance(item, dict):
            raise ContractError("every source entry must be an object")
        source_id = item.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ContractError("every source entry needs a non-empty source_id")
        has_text = isinstance(item.get("text"), str) and bool(item["text"].strip())
        has_source_file = isinstance(item.get("source_file"), str) and bool(
            item["source_file"].strip()
        )
        if has_text == has_source_file:
            raise ContractError(
                f"source {source_id} must define exactly one of text or source_file"
            )
        if has_text:
            text = item["text"]
        else:
            text = resolve_fixture(root, item["source_file"]).read_text(encoding="utf-8")
        resolved.append(
            {
                "source_id": source_id,
                "text": text,
                "text_sha256": sha256_text(text),
            }
        )
    return resolved


def format_sources(sources: list[dict[str, str]], *, legacy_plain: bool = False) -> str:
    if legacy_plain and len(sources) == 1:
        return sources[0]["text"]
    blocks: list[str] = []
    for source in sources:
        numbered = "\n".join(
            f"L{index}: {line}"
            for index, line in enumerate(source["text"].splitlines(), start=1)
        )
        blocks.append(
            f"【source_id={source['source_id']} text_sha256={source['text_sha256']}】\n"
            f"{numbered}"
        )
    return "\n\n".join(blocks)


def resolved_case_digest(case: dict[str, Any], sources: list[dict[str, str]]) -> str:
    if "sources" not in case and len(sources) == 1:
        return sha256_text(
            canonical_json({"case": case, "source": sources[0]["text"]})
        )
    return sha256_text(canonical_json({"case": case, "sources": sources}))


def artifact_sources(
    input_payload: dict[str, Any], case: dict[str, Any]
) -> list[dict[str, str]]:
    legacy = input_payload.get("source")
    if isinstance(legacy, str):
        return [
            {
                "source_id": "source-1",
                "text": legacy,
                "text_sha256": sha256_text(legacy),
            }
        ]
    raw_sources = input_payload.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ContractError("rejudge input.json is missing frozen source material")
    sources: list[dict[str, str]] = []
    for item in raw_sources:
        if not isinstance(item, dict):
            raise ContractError("rejudge frozen sources must be objects")
        source_id = item.get("source_id")
        text = item.get("text")
        digest = item.get("text_sha256")
        if (
            not isinstance(source_id, str)
            or not source_id.strip()
            or not isinstance(text, str)
            or not text.strip()
            or digest != sha256_text(text)
        ):
            raise ContractError("rejudge frozen source metadata is invalid")
        sources.append(
            {"source_id": source_id, "text": text, "text_sha256": digest}
        )
    if "sources" not in case:
        raise ContractError("rejudge input source shape does not match its case")
    return sources


def aggregate_status(statuses: list[str]) -> str:
    if not statuses:
        return "NOT_RUN"
    if any(status not in FINAL_STATUSES for status in statuses):
        raise ContractError("cannot aggregate an invalid status")
    for status in ("ERROR", "FAIL", "UNCERTAIN", "NOT_RUN"):
        if status in statuses:
            return status
    return "PASS"
