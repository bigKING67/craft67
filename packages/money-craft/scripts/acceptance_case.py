#!/usr/bin/env python3
"""Collect and verify a metadata-driven Money Craft acceptance case."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills" / "money-craft" / "scripts" / "money_craft.py"
VERIFY_EVIDENCE = ROOT / "scripts" / "verify_evidence.py"
CASE_SCHEMA = "money-craft.acceptance-case.v1"
MANIFEST_SCHEMA = "money-craft.public-evidence-manifest.v1"
THSCODE_RE = re.compile(r"^\d{6}\.(?:SH|SZ|BJ)$")
SOURCE_ID_RE = re.compile(r"^S\d{2,4}$")
SAFE_FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SECRET_RE = re.compile(rb"sk-fuyao-[A-Za-z0-9_-]{12,}")

Runner = Callable[..., subprocess.CompletedProcess[str]]


class AcceptanceError(RuntimeError):
    """Fail closed when a case contract or collection step is invalid."""


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AcceptanceError(f"JSON object required: {path}")
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise AcceptanceError(f"{label} must stay inside the repository")
    return path


def validate_case(payload: dict[str, Any]) -> None:
    if payload.get("schema") != CASE_SCHEMA:
        raise AcceptanceError(f"schema must be {CASE_SCHEMA}")
    case_id = payload.get("case_id")
    if not isinstance(case_id, str) or not re.fullmatch(r"\d{6}", case_id):
        raise AcceptanceError("case_id must be a six-digit ticker")
    security = payload.get("security")
    if not isinstance(security, str) or not security.strip():
        raise AcceptanceError("security is required")
    thscode = payload.get("expected_thscode")
    if not isinstance(thscode, str) or not THSCODE_RE.fullmatch(thscode):
        raise AcceptanceError("expected_thscode must be a complete A-share thscode")
    if thscode[:6] != case_id:
        raise AcceptanceError("case_id and expected_thscode do not match")
    try:
        dt.date.fromisoformat(str(payload.get("as_of")))
    except ValueError as exc:
        raise AcceptanceError("as_of must be YYYY-MM-DD") from exc

    evidence_root = relative_path(str(payload.get("evidence_root", "")), "evidence_root")
    public_root = relative_path(str(payload.get("public_root", "")), "public_root")
    if evidence_root.parts[:2] != ("local", "evidence"):
        raise AcceptanceError("evidence_root must be under local/evidence")
    if public_root.parts[:2] != ("artifacts", "acceptance"):
        raise AcceptanceError("public_root must be under artifacts/acceptance")
    provider_documentation = payload.get("provider_documentation")
    if not isinstance(provider_documentation, str) or not provider_documentation.startswith(
        "https://fuyao.aicubes.cn/"
    ):
        raise AcceptanceError("provider_documentation must use the official Fuyao HTTPS origin")

    operations = payload.get("operations")
    if not isinstance(operations, list) or not operations:
        raise AcceptanceError("operations must be a non-empty array")
    official_sources = payload.get("official_sources")
    if not isinstance(official_sources, list) or not official_sources:
        raise AcceptanceError("official_sources must be a non-empty array")

    ids: set[str] = set()
    filenames: set[str] = set()
    for collection, kind in ((operations, "provider"), (official_sources, "official")):
        for item in collection:
            if not isinstance(item, dict):
                raise AcceptanceError(f"{kind} source must be an object")
            source_id = item.get("id")
            if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
                raise AcceptanceError(f"invalid {kind} source id")
            if source_id in ids:
                raise AcceptanceError(f"duplicate source id: {source_id}")
            ids.add(source_id)
            if not isinstance(item.get("title"), str) or not item["title"].strip():
                raise AcceptanceError(f"{source_id}.title is required")
            filename = item.get("output" if kind == "provider" else "local_path")
            if not isinstance(filename, str) or not SAFE_FILE_RE.fullmatch(filename):
                raise AcceptanceError(f"{source_id} has an unsafe file name")
            if filename in filenames:
                raise AcceptanceError(f"duplicate evidence file name: {filename}")
            filenames.add(filename)
            if kind == "official":
                if item.get("kind") not in {"official-document", "official-index"}:
                    raise AcceptanceError(f"{source_id}.kind is invalid")
                if not isinstance(item.get("url"), str) or not item["url"].startswith("https://"):
                    raise AcceptanceError(f"{source_id}.url must use HTTPS")
                try:
                    dt.date.fromisoformat(str(item.get("retrieved_on")))
                except ValueError as exc:
                    raise AcceptanceError(f"{source_id}.retrieved_on must be YYYY-MM-DD") from exc
            else:
                allow_error_codes = item.get("allow_error_codes", [])
                if not isinstance(allow_error_codes, list) or any(
                    isinstance(code, bool) or not isinstance(code, int) for code in allow_error_codes
                ):
                    raise AcceptanceError(f"{source_id}.allow_error_codes must contain integers")
                operation_command(RUNTIME, item, Path("captures"))
                arguments = item["arguments"]
                if "thscode" in arguments and arguments["thscode"] != thscode:
                    raise AcceptanceError(f"{source_id}.thscode does not match expected_thscode")
                if "thscodes" in arguments and arguments["thscodes"] != thscode:
                    raise AcceptanceError(f"{source_id}.thscodes must contain only expected_thscode")

    if operations[0].get("operation") != "search":
        raise AcceptanceError("the first operation must resolve ticker identity")
    if operations[0]["arguments"].get("query") != case_id:
        raise AcceptanceError("the first operation must search for case_id")


def load_case(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    validate_case(payload)
    return payload


def operation_command(runtime: Path, item: dict[str, Any], capture_root: Path) -> list[str]:
    operation = item.get("operation")
    arguments = item.get("arguments")
    if not isinstance(arguments, dict):
        raise AcceptanceError(f"{item.get('id')}.arguments must be an object")
    command = [sys.executable, str(runtime), "data"]
    option_order: list[tuple[str, str]]
    if operation == "search":
        option_order = [("query", "--query"), ("limit", "--limit")]
    elif operation == "snapshot":
        option_order = [("thscodes", "--thscodes")]
    elif operation == "valuations":
        option_order = [("thscodes", "--thscodes")]
    elif operation == "history":
        option_order = [
            ("thscode", "--thscode"),
            ("start", "--start"),
            ("end", "--end"),
            ("interval", "--interval"),
            ("adjust", "--adjust"),
        ]
    elif operation == "financials":
        option_order = [
            ("thscode", "--thscode"),
            ("statement", "--statement"),
            ("period", "--period"),
            ("limit", "--limit"),
            ("start", "--start"),
            ("end", "--end"),
        ]
    elif operation == "indicators":
        option_order = [("thscode", "--thscode"), ("report", "--report")]
    elif operation == "corporate-actions":
        option_order = [("thscode", "--thscode"), ("start", "--start"), ("end", "--end")]
    elif operation == "calendar":
        option_order = [("start", "--start"), ("end", "--end")]
    else:
        raise AcceptanceError(f"unsupported operation: {operation}")
    command.append(operation)
    known = {name for name, _ in option_order}
    unknown = sorted(set(arguments) - known)
    if unknown:
        raise AcceptanceError(f"unsupported arguments for {operation}: {', '.join(unknown)}")
    for name, option in option_order:
        if name in arguments and arguments[name] is not None:
            command.extend([option, str(arguments[name])])
    command.extend(["--capture-dir", str(capture_root), "--source-id", str(item["id"])])
    return command


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_name(f".{path.name}.staging.{os.getpid()}.{uuid.uuid4().hex}")
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if SECRET_RE.search(data):
        raise AcceptanceError(f"secret-like material rejected from {path.name}")
    try:
        with staging.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staging, path)
    finally:
        if staging.exists():
            staging.unlink()


def validate_identity(payload: dict[str, Any], case: dict[str, Any]) -> None:
    items = payload.get("data", {}).get("item", [])
    if not isinstance(items, list):
        raise AcceptanceError("ticker search data.item must be an array")
    matches = [
        item
        for item in items
        if isinstance(item, dict) and item.get("thscode") == case["expected_thscode"]
    ]
    if len(matches) != 1:
        raise AcceptanceError("ticker search did not resolve exactly one expected thscode")
    if matches[0].get("name") != case["security"]:
        raise AcceptanceError("ticker search name does not match the case contract")


def operation_status(item: dict[str, Any], payload: dict[str, Any], returncode: int | None = None) -> str:
    if payload.get("schema") != "money-craft.data-response.v1" or payload.get("provider") != "fuyao":
        raise AcceptanceError(f"{item['id']} response identity is invalid")
    expected_operation = str(item["operation"])
    actual_operation = payload.get("operation")
    if expected_operation == "financials":
        operation_matches = actual_operation == f"financials.{item['arguments']['statement']}"
    else:
        operation_matches = actual_operation == expected_operation
    if not operation_matches:
        raise AcceptanceError(f"{item['id']} response operation is invalid")
    if payload.get("ok") is True:
        if returncode not in (None, 0):
            raise AcceptanceError(f"{item['id']} returned ok=true with exit code {returncode}")
        return "passed"
    if payload.get("ok") is not False:
        raise AcceptanceError(f"{item['id']} response must declare ok=true or ok=false")
    code = payload.get("error", {}).get("code")
    if code not in item.get("allow_error_codes", []):
        kind = payload.get("error", {}).get("kind", "unknown_error")
        raise AcceptanceError(f"{item['id']} failed: {kind} code={code}")
    if returncode == 0:
        raise AcceptanceError(f"{item['id']} returned an error payload with exit code zero")
    return "allowed_error"


def collect(
    case: dict[str, Any],
    *,
    resume: bool = False,
    runtime: Path = RUNTIME,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    evidence_root = ROOT / relative_path(case["evidence_root"], "evidence_root")
    capture_root = evidence_root / "captures"
    if evidence_root.exists() and not resume:
        raise AcceptanceError(f"evidence root already exists; use --resume: {case['evidence_root']}")
    evidence_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if evidence_root.is_symlink() or not evidence_root.is_dir():
        raise AcceptanceError("evidence root must be a real directory")
    capture_root.mkdir(parents=True, exist_ok=True, mode=0o700)

    results: list[dict[str, Any]] = []
    for item in case["operations"]:
        destination = evidence_root / item["output"]
        if destination.exists():
            if not resume:
                raise AcceptanceError(f"normalized output already exists: {destination.name}")
            payload = load_json(destination)
            status = operation_status(item, payload)
            if item["operation"] == "search" and status == "passed":
                validate_identity(payload, case)
            results.append({"id": item["id"], "operation": item["operation"], "status": status, "resumed": True})
            continue

        command = operation_command(runtime, item, capture_root)
        completed = runner(command, cwd=ROOT, text=True, capture_output=True, check=False)
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AcceptanceError(f"{item['id']} did not return JSON") from exc
        if not isinstance(payload, dict):
            raise AcceptanceError(f"{item['id']} response must be an object")
        status = operation_status(item, payload, completed.returncode)
        if status == "passed":
            if item["operation"] == "search":
                validate_identity(payload, case)
            if isinstance(payload.get("capture"), dict):
                payload["capture"]["path"] = f"captures/{item['id']}"
        atomic_json(destination, payload)
        results.append({"id": item["id"], "operation": item["operation"], "status": status, "resumed": False})

    passed = sum(item["status"] == "passed" for item in results)
    allowed_errors = sum(item["status"] == "allowed_error" for item in results)
    summary = {
        "schema": "money-craft.acceptance-collection.v1",
        "case_id": case["case_id"],
        "security": case["security"],
        "thscode": case["expected_thscode"],
        "as_of": case["as_of"],
        "passed": passed,
        "allowed_errors": allowed_errors,
        "total": len(results),
        "complete": passed + allowed_errors == len(results),
        "results": results,
    }
    atomic_json(evidence_root / "collection-summary.json", summary)
    return summary


def provider_source(item: dict[str, Any], evidence_root: Path) -> dict[str, Any]:
    normalized_path = evidence_root / item["output"]
    payload = load_json(normalized_path)
    status = operation_status(item, payload)
    role = "normalized-response" if status == "passed" else "normalized-error"
    source = {
        "id": item["id"],
        "kind": "provider-response",
        "title": item["title"],
        "provider": "fuyao",
        "operation": payload.get("operation", item["operation"]),
        "retrieved_at": payload.get("fetched_at"),
        "distribution": "private-not-distributed",
        "files": [{"role": role, "path": item["output"], "sha256": sha256_file(normalized_path)}],
    }
    raw_response = evidence_root / "captures" / item["id"] / "response.json"
    if status == "passed":
        if not raw_response.is_file():
            raise AcceptanceError(f"missing captured provider response: {item['id']}")
        source["files"].append(
            {
                "role": "raw-response",
                "path": f"captures/{item['id']}/response.json",
                "sha256": sha256_file(raw_response),
            }
        )
    return source


def official_source(item: dict[str, Any], evidence_root: Path) -> dict[str, Any]:
    local_path = evidence_root / item["local_path"]
    if not local_path.is_file():
        raise AcceptanceError(f"missing official source: {item['local_path']}")
    kind = item.get("kind")
    prefix = local_path.read_bytes()[:16]
    if kind == "official-document" and not prefix.startswith(b"%PDF-"):
        raise AcceptanceError(f"official document is not a PDF: {item['local_path']}")
    if kind == "official-index" and b"<" not in prefix:
        raise AcceptanceError(f"official index is not HTML: {item['local_path']}")
    role = "downloaded-document" if kind == "official-document" else "web-snapshot"
    return {
        "id": item["id"],
        "kind": kind,
        "title": item["title"],
        "url": item["url"],
        "retrieved_on": item["retrieved_on"],
        "distribution": "private-not-distributed",
        "files": [{"role": role, "path": item["local_path"], "sha256": sha256_file(local_path)}],
    }


def build_manifest(case: dict[str, Any], output: Path | None = None) -> dict[str, Any]:
    evidence_root = ROOT / relative_path(case["evidence_root"], "evidence_root")
    if evidence_root.is_symlink() or not evidence_root.is_dir():
        raise AcceptanceError("evidence root must be a real directory")
    sources = [provider_source(item, evidence_root) for item in case["operations"]]
    sources.extend(official_source(item, evidence_root) for item in case["official_sources"])
    retrieved = [item.get("retrieved_at") for item in sources if isinstance(item.get("retrieved_at"), str)]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "case_id": case["case_id"],
        "security": case["security"],
        "thscode": case["expected_thscode"],
        "as_of": case["as_of"],
        "data_cutoff": max(retrieved) if retrieved else None,
        "distribution": {
            "mode": "metadata-only",
            "provider_payloads_distributed": False,
            "downloaded_documents_distributed": False,
            "note": "Only source metadata and SHA-256 bindings are public. Evidence files remain local and ignored by Git.",
        },
        "local_evidence": {
            "default_root": case["evidence_root"],
            "required_for_public_validation": False,
        },
        "provider_documentation": case["provider_documentation"],
        "source_count": len(sources),
        "sources": sorted(sources, key=lambda item: int(item["id"][1:])),
    }
    target = output or ROOT / relative_path(case["public_root"], "public_root") / "evidence-manifest.json"
    atomic_json(target, manifest)
    return manifest


def verify(case: dict[str, Any], *, require_private: bool) -> subprocess.CompletedProcess[str]:
    manifest = ROOT / relative_path(case["public_root"], "public_root") / "evidence-manifest.json"
    mode = "--require-private" if require_private else "--metadata-only"
    completed = subprocess.run(
        [sys.executable, str(VERIFY_EVIDENCE), str(manifest), mode],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise AcceptanceError(completed.stdout.strip() or completed.stderr.strip())
    return completed


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)
    for name in ("collect", "build-manifest", "verify"):
        command = subparsers.add_parser(name)
        command.add_argument("--case", required=True, type=Path)
        if name == "collect":
            command.add_argument("--resume", action="store_true")
        if name == "verify":
            command.add_argument("--require-private", action="store_true")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        case = load_case(args.case.resolve())
        if args.command == "collect":
            result = collect(case, resume=args.resume)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "build-manifest":
            result = build_manifest(case)
            print(json.dumps({"valid": True, "source_count": result["source_count"]}, indent=2))
        else:
            result = verify(case, require_private=args.require_private)
            print(result.stdout.strip())
        return 0
    except (AcceptanceError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
