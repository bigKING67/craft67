from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Keep the existing module-level contract constants importable from case_store.
from .case_validation import (
    CASE_ALLOWED_FIELDS,
    CASE_OPTIONAL_FIELDS,
    CASE_REQUIRED_FIELDS,
    COLLECTION_REQUIRED_FIELDS,
    CONFIDENCES,
    EVENT_DATA_FIELDS,
    EVENT_REQUIRED_FIELDS,
    EVENT_TYPES,
    EVIDENCE_ID_RE,
    EVIDENCE_REQUIRED_FIELDS,
    FINDING_ID_RE,
    FINDING_REQUIRED_FIELDS,
    FINDING_STATUSES,
    PATH_ID_RE,
    PATH_REQUIRED_FIELDS,
    PATH_STATUSES,
    ROUTE_IDS,
    SEVERITIES,
    SHA256_RE,
    SNAPSHOTS,
    build_manifest,
    event_material,
    read_events,
    validate_case_directory,
    validate_event_records,
)
from .common import (
    FileLock,
    ReverseCraftError,
    atomic_write_bytes,
    atomic_write_json,
    canonical_json,
    ensure_private_directory,
    home_root,
    load_json,
    PRIVATE_FILE_MODE,
    safe_component,
    sha256_bytes,
    sha256_file,
    slugify,
    utc_now,
)


def runs_root(home: str | None = None) -> Path:
    return home_root(home) / "runs"


def case_dir(case_id: str, home: str | None = None) -> Path:
    safe_component(case_id, field="case id")
    root = runs_root(home)
    target = (root / case_id).resolve()
    if target.parent != root.resolve():
        raise ReverseCraftError("case path escapes run root")
    return target


def _empty_collection(schema: str) -> dict[str, Any]:
    return {"schema": schema, "items": []}


def _load_case(case_id: str, home: str | None = None) -> tuple[Path, dict[str, Any]]:
    directory = case_dir(case_id, home)
    case = load_json(directory / "case.json")
    if not isinstance(case, dict):
        raise ReverseCraftError(f"invalid case document in {directory / 'case.json'}")
    if case.get("id") != case_id:
        raise ReverseCraftError(f"case identity mismatch in {directory / 'case.json'}")
    return directory, case


def _require_open(case: dict[str, Any]) -> None:
    if case.get("state") != "open":
        raise ReverseCraftError(f"case is {case.get('state')}; mutation is not allowed")


def _next_id(items: Iterable[dict[str, Any]], prefix: str) -> str:
    maximum = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        raw = str(item.get("id", ""))
        if raw.startswith(prefix + "-"):
            try:
                maximum = max(maximum, int(raw.split("-", 1)[1]))
            except ValueError:
                continue
    return f"{prefix}-{maximum + 1:04d}"


def _assert_event_stream_appendable(directory: Path, case: dict[str, Any]) -> list[Any]:
    events = read_events(directory)
    event_errors = validate_event_records(events)
    if event_errors:
        raise ReverseCraftError("event stream validation failed: " + "; ".join(event_errors))
    prev_hash = events[-1]["event_hash"] if events else None
    has_count = "event_count" in case
    has_hash = "last_event_hash" in case
    if has_count != has_hash:
        raise ReverseCraftError("case event anchor is incomplete")
    if has_count and (case["event_count"] != len(events) or case["last_event_hash"] != prev_hash):
        raise ReverseCraftError("case event anchor does not match the event stream")
    return events


def _append_event(directory: Path, case: dict[str, Any], event_type: str, data: Any) -> dict[str, Any]:
    events = _assert_event_stream_appendable(directory, case)
    prev_hash = events[-1]["event_hash"] if events else None
    material = event_material(len(events) + 1, utc_now(), event_type, data, prev_hash)
    event = {**material, "event_hash": sha256_bytes(canonical_json(material))}
    path = directory / "events.ndjson"
    with path.open("ab") as handle:
        handle.write(canonical_json(event) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event


def _record_case_event(directory: Path, case: dict[str, Any], event_type: str, data: Any) -> dict[str, Any]:
    event = _append_event(directory, case, event_type, data)
    case["updated_at"] = event["at"]
    case["event_count"] = event["seq"]
    case["last_event_hash"] = event["event_hash"]
    atomic_write_json(directory / "case.json", case)
    return event


def init_case(title: str, scope: str, route_id: str | None = None, home: str | None = None) -> dict[str, Any]:
    if not title.strip() or not scope.strip():
        raise ReverseCraftError("title and scope must not be empty")
    if route_id is not None and (not isinstance(route_id, str) or route_id not in ROUTE_IDS):
        raise ReverseCraftError("route id must be a registered route (R0..R41 or R44)")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    case_id = f"{timestamp}-{slugify(title)}-{secrets.token_hex(2)}"
    directory = case_dir(case_id, home)
    ensure_private_directory(runs_root(home))
    ensure_private_directory(directory, parents=False, exist_ok=False)
    ensure_private_directory(directory / "artifacts", parents=False)
    ensure_private_directory(directory / "reports", parents=False)
    created_at = utc_now()
    case = {
        "schema": "reverse-craft.case.v1",
        "id": case_id,
        "title": title.strip(),
        "scope": scope.strip(),
        "route_id": route_id,
        "state": "open",
        "created_at": created_at,
        "updated_at": created_at,
        "sealed_at": None,
        "event_count": 0,
        "last_event_hash": None,
    }
    atomic_write_json(directory / "case.json", case)
    atomic_write_json(directory / "evidence.json", _empty_collection("reverse-craft.evidence.v1"))
    atomic_write_json(directory / "findings.json", _empty_collection("reverse-craft.findings.v1"))
    atomic_write_json(directory / "paths.json", _empty_collection("reverse-craft.paths.v1"))
    (directory / "events.ndjson").touch(mode=0o600)
    if os.name != "nt":
        (directory / "events.ndjson").chmod(PRIVATE_FILE_MODE)
    _record_case_event(directory, case, "case.initialized", {"id": case_id, "route_id": route_id})
    return {"schema": "reverse-craft.case-init.v1", "case": case, "directory": str(directory)}


def case_status(case_id: str, home: str | None = None) -> dict[str, Any]:
    directory, case = _load_case(case_id, home)
    evidence = load_json(directory / "evidence.json")["items"]
    findings = load_json(directory / "findings.json")["items"]
    paths = load_json(directory / "paths.json")["items"]
    return {
        "schema": "reverse-craft.case-status.v1",
        "case": case,
        "directory": str(directory),
        "counts": {"evidence": len(evidence), "findings": len(findings), "paths": len(paths), "events": len(read_events(directory))},
        "sealed": (directory / "seal.json").exists(),
    }


def add_evidence(
    case_id: str,
    file_path: str,
    kind: str,
    note: str | None = None,
    external: bool = False,
    source: str | None = None,
    home: str | None = None,
) -> dict[str, Any]:
    source_path = Path(file_path).expanduser().resolve()
    if not source_path.is_file():
        raise ReverseCraftError(f"evidence file not found or not regular: {source_path}")
    if not kind.strip():
        raise ReverseCraftError("evidence kind must not be empty")
    directory, _ = _load_case(case_id, home)
    with FileLock(directory / ".case.lock"):
        case = load_json(directory / "case.json")
        _require_open(case)
        _assert_event_stream_appendable(directory, case)
        collection = load_json(directory / "evidence.json")
        evidence_id = _next_id(collection["items"], "E")
        source_stat = source_path.stat()
        digest = sha256_file(source_path)
        stored_path: str | None = None
        if not external:
            name = re_safe_filename(source_path.name)
            destination = directory / "artifacts" / f"{evidence_id}-{name}"
            temp = destination.with_name(f".{destination.name}.{secrets.token_hex(4)}.tmp")
            try:
                shutil.copyfile(source_path, temp)
                if temp.stat().st_size != source_stat.st_size or sha256_file(temp) != digest:
                    raise ReverseCraftError("evidence changed or copy verification failed")
                if os.name != "nt":
                    temp.chmod(PRIVATE_FILE_MODE)
                os.replace(temp, destination)
            finally:
                temp.unlink(missing_ok=True)
            stored_path = str(destination.relative_to(directory))
        item = {
            "id": evidence_id,
            "kind": kind.strip(),
            "source": source or str(source_path),
            "acquisition": "external-reference" if external else "verified-copy",
            "observed_at": utc_now(),
            "size": source_stat.st_size,
            "sha256": digest,
            "stored_path": stored_path,
            "external_path": str(source_path) if external else None,
            "note": note,
        }
        collection["items"].append(item)
        atomic_write_json(directory / "evidence.json", collection)
        _record_case_event(
            directory, case, "evidence.added",
            {"id": evidence_id, "sha256": digest, "size": source_stat.st_size},
        )
    return {"schema": "reverse-craft.evidence-add.v1", "case_id": case_id, "evidence": item}


def re_safe_filename(name: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in ".-_" else "_" for character in name)
    cleaned = cleaned.strip(".")[:120]
    return cleaned or "artifact.bin"


def _markdown_code_span(value: Any) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return "not recorded"
    longest_run = 0
    current_run = 0
    for character in text:
        if character == "`":
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0
    fence = "`" * (longest_run + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{padding}{text}{padding}{fence}"


def add_finding(
    case_id: str,
    title: str,
    severity: str,
    status: str,
    evidence_ids: list[str],
    statement: str | None = None,
    reproduction: str | None = None,
    confidence: str = "medium",
    home: str | None = None,
) -> dict[str, Any]:
    if not isinstance(severity, str) or severity not in SEVERITIES:
        raise ReverseCraftError(f"severity must be one of {sorted(SEVERITIES)}")
    if not isinstance(status, str) or status not in FINDING_STATUSES:
        raise ReverseCraftError(f"status must be one of {sorted(FINDING_STATUSES)}")
    if not isinstance(confidence, str) or confidence not in CONFIDENCES:
        raise ReverseCraftError(f"confidence must be one of {sorted(CONFIDENCES)}")
    if not title.strip():
        raise ReverseCraftError("finding title must not be empty")
    directory, _ = _load_case(case_id, home)
    with FileLock(directory / ".case.lock"):
        case = load_json(directory / "case.json")
        _require_open(case)
        _assert_event_stream_appendable(directory, case)
        evidence = load_json(directory / "evidence.json")["items"]
        known = {item["id"] for item in evidence}
        unknown = sorted(set(evidence_ids) - known)
        if unknown:
            raise ReverseCraftError(f"unknown evidence ids: {', '.join(unknown)}")
        if status in {"supported", "confirmed"} and not evidence_ids:
            raise ReverseCraftError(f"{status} finding requires evidence")
        if status == "confirmed" and confidence != "high" and not reproduction:
            raise ReverseCraftError("confirmed finding requires high confidence or a reproduction note")
        collection = load_json(directory / "findings.json")
        finding_id = _next_id(collection["items"], "F")
        item = {
            "id": finding_id,
            "title": title.strip(),
            "statement": statement or title.strip(),
            "severity": severity,
            "status": status,
            "confidence": confidence,
            "evidence_ids": list(dict.fromkeys(evidence_ids)),
            "reproduction": reproduction,
            "created_at": utc_now(),
        }
        collection["items"].append(item)
        atomic_write_json(directory / "findings.json", collection)
        _record_case_event(
            directory, case, "finding.added",
            {"id": finding_id, "status": status, "evidence_ids": item["evidence_ids"]},
        )
    return {"schema": "reverse-craft.finding-add.v1", "case_id": case_id, "finding": item}


def add_path(
    case_id: str,
    title: str,
    finding_ids: list[str],
    status: str = "supported",
    preconditions: str | None = None,
    impact: str | None = None,
    validation: str | None = None,
    home: str | None = None,
) -> dict[str, Any]:
    if not isinstance(status, str) or status not in PATH_STATUSES:
        raise ReverseCraftError(f"status must be one of {sorted(PATH_STATUSES)}")
    if not title.strip() or not finding_ids:
        raise ReverseCraftError("path title and at least one finding are required")
    directory, _ = _load_case(case_id, home)
    with FileLock(directory / ".case.lock"):
        case = load_json(directory / "case.json")
        _require_open(case)
        _assert_event_stream_appendable(directory, case)
        findings = load_json(directory / "findings.json")["items"]
        by_id = {item["id"]: item for item in findings}
        unknown = sorted(set(finding_ids) - set(by_id))
        if unknown:
            raise ReverseCraftError(f"unknown finding ids: {', '.join(unknown)}")
        refuted = [finding_id for finding_id in finding_ids if by_id[finding_id]["status"] == "refuted"]
        if refuted and status != "refuted":
            raise ReverseCraftError(f"non-refuted path cannot include refuted findings: {', '.join(refuted)}")
        collection = load_json(directory / "paths.json")
        path_id = _next_id(collection["items"], "P")
        item = {
            "id": path_id,
            "title": title.strip(),
            "status": status,
            "finding_ids": list(dict.fromkeys(finding_ids)),
            "preconditions": preconditions,
            "impact": impact,
            "validation": validation,
            "created_at": utc_now(),
        }
        collection["items"].append(item)
        atomic_write_json(directory / "paths.json", collection)
        _record_case_event(
            directory, case, "path.added",
            {"id": path_id, "status": status, "finding_ids": item["finding_ids"]},
        )
    return {"schema": "reverse-craft.path-add.v1", "case_id": case_id, "path": item}


def validate_case(case_id: str, home: str | None = None) -> dict[str, Any]:
    return validate_case_directory(case_id, case_dir(case_id, home))


def render_report(case_id: str, output: str | None = None, home: str | None = None) -> dict[str, Any]:
    directory, case = _load_case(case_id, home)
    with FileLock(directory / ".case.lock"):
        case = load_json(directory / "case.json")
        _require_open(case)
        _assert_event_stream_appendable(directory, case)
        evidence = load_json(directory / "evidence.json")["items"]
        findings = load_json(directory / "findings.json")["items"]
        paths = load_json(directory / "paths.json")["items"]
        validation = validate_case(case_id, home)
        if not validation["valid"]:
            raise ReverseCraftError("case validation failed: " + "; ".join(validation["errors"]))
        lines = [
            f"# {case['title']}",
            "",
            "## Objective and scope",
            "",
            case["scope"],
            "",
            "## Outcome",
            "",
            "Generated from the current Reverse Craft case graph. Confirmed conclusions are listed below; "
            "absence from this report is not evidence of absence.",
            "",
            "## Findings",
            "",
        ]
        if not findings:
            lines.append("No findings recorded.")
        for item in findings:
            lines.extend([
                f"### {item['id']} - {item['title']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Severity: `{item['severity']}`",
                f"- Confidence: `{item['confidence']}`",
                f"- Evidence: {', '.join(f'`{value}`' for value in item['evidence_ids']) or 'none'}",
                f"- Statement: {item['statement']}",
            ])
            if item.get("reproduction"):
                lines.append(f"- Reproduction: {item['reproduction']}")
            lines.append("")
        lines.extend(["## Paths", ""])
        if not paths:
            lines.append("No paths recorded.")
        for item in paths:
            lines.extend([
                f"### {item['id']} - {item['title']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Findings: {' -> '.join(f'`{value}`' for value in item['finding_ids'])}",
                f"- Preconditions: {item.get('preconditions') or 'not recorded'}",
                f"- Impact: {item.get('impact') or 'not recorded'}",
                f"- Validation: {item.get('validation') or 'not recorded'}",
                "",
            ])
        lines.extend(["## Evidence", ""])
        if not evidence:
            lines.append("No evidence recorded.")
        for item in evidence:
            location = item.get("stored_path") or item.get("external_path")
            lines.extend([
                f"- `{item['id']}` {_markdown_code_span(item['kind'])}: `{item['sha256']}` "
                f"({item['size']} bytes, {_markdown_code_span(location)})",
                f"  - Source: {_markdown_code_span(item['source'])}",
                f"  - Acquisition: {_markdown_code_span(item['acquisition'])}",
                f"  - Observed at: {_markdown_code_span(item['observed_at'])}",
                f"  - Note: {_markdown_code_span(item.get('note'))}",
            ])
        lines.extend([
            "",
            "## Verification and limitations",
            "",
            f"- Case validation: `{'PASS' if validation['valid'] else 'FAIL'}`",
            f"- Validation errors: {len(validation['errors'])}",
            f"- Validation warnings: {len(validation['warnings'])}",
            f"- Route: `{case.get('route_id') or 'not recorded'}`",
            f"- Generated at: `{utc_now()}`",
            "",
        ])
        content = "\n".join(lines).encode("utf-8")
        if output:
            destination = Path(output).expanduser().resolve()
        else:
            destination = directory / "reports" / "report.md"
        reports_root = (directory / "reports").resolve()
        if reports_root not in destination.parents:
            raise ReverseCraftError("report output must remain inside the case reports directory")
        ensure_private_directory(destination.parent)
        atomic_write_bytes(destination, content)
        digest = sha256_file(destination)
        _record_case_event(
            directory, case, "report.rendered",
            {"path": str(destination.relative_to(directory)), "sha256": digest},
        )
    return {"schema": "reverse-craft.report.v1", "case_id": case_id, "path": str(destination), "sha256": digest}


def seal_case(case_id: str, home: str | None = None) -> dict[str, Any]:
    directory, _ = _load_case(case_id, home)
    with FileLock(directory / ".case.lock"):
        case = load_json(directory / "case.json")
        _require_open(case)
        _assert_event_stream_appendable(directory, case)
        validation = validate_case(case_id, home)
        if not validation["valid"]:
            raise ReverseCraftError("case validation failed: " + "; ".join(validation["errors"]))
        if validation["counts"]["evidence"] < 1:
            raise ReverseCraftError("cannot seal a case without evidence")
        sealed_at = utc_now()
        case["state"] = "sealed"
        case["sealed_at"] = sealed_at
        _record_case_event(directory, case, "case.sealed", {"id": case_id, "sealed_at": sealed_at})
        manifest = build_manifest(directory)
        seal = {
            "schema": "reverse-craft.seal.v1",
            "case_id": case_id,
            "sealed_at": sealed_at,
            **manifest,
        }
        atomic_write_json(directory / "seal.json", seal)
    final_validation = validate_case(case_id, home)
    if not final_validation["valid"]:
        raise ReverseCraftError("post-seal validation failed: " + "; ".join(final_validation["errors"]))
    return {"schema": "reverse-craft.case-seal.v1", "case_id": case_id, "seal": seal, "valid": True}
