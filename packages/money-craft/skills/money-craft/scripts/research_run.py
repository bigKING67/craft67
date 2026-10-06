#!/usr/bin/env python3
"""Portable, evidence-gated research run workspaces."""

from __future__ import annotations

import datetime as dt
import contextlib
import errno
import functools
import stat
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import financial_rigor
import financial_reconciliation
from fsutil import sha256_file
import report_audit
import research_workflow

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows host required.
    fcntl = None
try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX host.
    msvcrt = None

PLAN_SCHEMA = "money-craft.company-research-plan.v1"
CASE_SCHEMA = "money-craft.research-case.v1"
STATE_SCHEMA = "money-craft.research-run-state.v1"
INIT_SCHEMA = "money-craft.research-init.v1"
COLLECTION_SCHEMA = "money-craft.research-collection.v1"
IMPORT_SCHEMA = "money-craft.official-import.v1"
STATUS_SCHEMA = "money-craft.research-status.v1"
FINALIZE_SCHEMA = "money-craft.research-finalize.v1"
RECEIPT_SCHEMA = "money-craft.research-completion-receipt.v1"
MANIFEST_SCHEMA = "money-craft.public-evidence-manifest.v1"
PROVIDER_DOCUMENTATION = {
    "fuyao": "https://fuyao.aicubes.cn/docs/api-reference/overview/",
    "yfinance": "https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html",
}
SOURCE_ID_RE = re.compile(r"^S\d{2,4}$")
SECRET_RE = re.compile(rb"sk-fuyao-[A-Za-z0-9_-]{12,}")
MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
MAX_OFFICIAL_SOURCE_BYTES = 100 * 1024 * 1024
MAX_STATE_EVENTS = 1000
SHANGHAI = ZoneInfo("Asia/Shanghai")
OUTPUT_ROOT_ENV = "MONEY_CRAFT_OUTPUT_ROOT"
DEFAULT_OUTPUT_ROOT_RELATIVE = Path("Documents") / "sixseven" / "money"
BASE_RECEIPT_BOUND_FILES = {
    "plan.json",
    "case.json",
    "evidence-manifest.json",
    "report.md",
    "thesis.md",
    "report-audit.json",
    "report-financial-audit.json",
    "thesis-audit.json",
    "thesis-financial-audit.json",
}
RECONCILIATION_BOUND_FILES = {
    "financial-reconciliation.json",
    "financial-reconciliation-audit.json",
}

Runner = Callable[..., subprocess.CompletedProcess[str]]


class ResearchRunError(RuntimeError):
    """A research workspace is unsafe, inconsistent, or incomplete."""

    def __init__(self, kind: str, message: str, *, exit_code: int = 4) -> None:
        super().__init__(message)
        self.kind = kind
        self.exit_code = exit_code


def provider_documentation(adapter: str) -> str:
    try:
        return PROVIDER_DOCUMENTATION[adapter]
    except KeyError as exc:
        raise ResearchRunError("invalid_plan", f"unsupported provider adapter: {adapter}") from exc


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def encoded_json(payload: dict[str, Any]) -> bytes:
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(data) > MAX_JSON_BYTES:
        raise ResearchRunError("artifact_too_large", "research JSON artifact exceeds the size limit")
    if SECRET_RE.search(data):
        raise ResearchRunError("secret_material", "secret-like material rejected from research workspace")
    return data


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_bytes(path: Path, data: bytes, *, replace: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_name(f".{path.name}.staging.{os.getpid()}.{uuid.uuid4().hex}")
    try:
        with staging.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if replace:
            os.replace(staging, path)
        else:
            # Same-directory hard link publishes complete bytes only if absent.
            # Never fall back to check-then-replace on unsupported filesystems.
            try:
                os.link(staging, path)
            except FileExistsError as exc:
                raise ResearchRunError("existing_artifact", f"artifact already exists: {path.name}") from exc
    finally:
        if staging.exists():
            staging.unlink()


def atomic_json(path: Path, payload: dict[str, Any], *, replace: bool = True) -> None:
    atomic_bytes(path, encoded_json(payload), replace=replace)


def load_json(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise ResearchRunError("missing_artifact", f"missing research artifact: {path.name}") from exc
    except OSError as exc:
        raise ResearchRunError("invalid_artifact", f"cannot inspect JSON artifact {path.name}: {exc}") from exc
    if path.is_symlink() or not path.is_file():
        raise ResearchRunError("invalid_artifact", f"JSON artifact must be a regular file: {path.name}")
    if metadata.st_size < 2 or metadata.st_size > MAX_JSON_BYTES:
        raise ResearchRunError("invalid_artifact", f"JSON artifact size is invalid: {path.name}")
    try:
        raw = path.read_bytes()
        if SECRET_RE.search(raw):
            raise ResearchRunError("secret_material", f"secret-like material found in {path.name}")
        payload = json.loads(raw.decode("utf-8"))
    except ResearchRunError:
        raise
    except (OSError, ValueError, RecursionError) as exc:
        raise ResearchRunError("invalid_artifact", f"invalid JSON artifact {path.name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ResearchRunError("invalid_artifact", f"JSON object required: {path.name}")
    return payload


def workspace_path(value: Path | str) -> Path:
    raw = Path(value).expanduser()
    if raw.is_symlink():
        raise ResearchRunError("invalid_workspace", "workspace must not be a symlink")
    path = raw.resolve(strict=False)
    if path.exists() and (path.is_symlink() or not path.is_dir()):
        raise ResearchRunError("invalid_workspace", "workspace must be a real directory")
    return path


@contextlib.contextmanager
def workspace_lock(workspace: Path | str, *, allow_missing: bool = False):
    root = workspace_path(workspace)
    if not root.is_dir() and not (allow_missing and not root.exists()):
        raise ResearchRunError("missing_workspace", "research workspace does not exist")
    if fcntl is None and msvcrt is None:
        raise ResearchRunError("unsupported_lock", "this platform has no supported workspace lock")
    # Keep the inode after release: unlinking a lock allows split ownership.
    lock_path = root.with_name(f".{root.name}.research.lock")
    if lock_path.is_symlink():
        raise ResearchRunError("unsafe_lock", "workspace lock must not be a symlink")
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ResearchRunError("unsafe_lock", "workspace lock must be a regular unshared file")
        try:
            if fcntl is not None:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:  # pragma: no cover - Windows host required.
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            if exc.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                raise ResearchRunError("workspace_busy", "research workspace is in use; retry after the active operation finishes") from exc
            raise
        try:
            yield root
        finally:
            if fcntl is not None:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            else:  # pragma: no cover - Windows host required.
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(descriptor)


def locked_workspace(function):
    @functools.wraps(function)
    def run(workspace, *args, **kwargs):
        with workspace_lock(workspace) as root:
            return function(root, *args, **kwargs)
    return run


def output_root(
    value: Path | str | None = None,
    *,
    environment: dict[str, str] | None = None,
    home: Path | None = None,
) -> tuple[Path, str]:
    environ = os.environ if environment is None else environment
    if value is not None:
        raw = Path(value).expanduser()
        source = "command-line"
    elif environ.get(OUTPUT_ROOT_ENV, "").strip():
        raw = Path(environ[OUTPUT_ROOT_ENV].strip()).expanduser()
        source = f"environment:{OUTPUT_ROOT_ENV}"
    else:
        raw = (home if home is not None else Path.home()) / DEFAULT_OUTPUT_ROOT_RELATIVE
        source = "default"
    if raw.is_symlink():
        raise ResearchRunError("invalid_output_root", "research output root must not be a symlink")
    resolved = raw.resolve(strict=False)
    if resolved.exists() and not resolved.is_dir():
        raise ResearchRunError("invalid_output_root", "research output root must be a directory")
    return resolved, source


def company_directory_name(plan: dict[str, Any]) -> str:
    identity = plan.get("identity")
    if not isinstance(identity, dict):
        raise ResearchRunError("invalid_plan", "plan identity is required for the research output path")
    security_id = identity.get("security_id")
    security = identity.get("security")
    if not isinstance(security_id, str) or not research_workflow.SECURITY_ID_RE.fullmatch(security_id):
        raise ResearchRunError("invalid_plan", "plan security_id is invalid for the research output path")
    if not isinstance(security, str) or not security.strip():
        raise ResearchRunError("invalid_plan", "plan security name is required for the research output path")
    normalized = unicodedata.normalize("NFKC", security).strip()
    normalized = re.sub(r"[\x00-\x1f<>:\"/\\|?*]+", "-", normalized)
    normalized = re.sub(r"\s+", "", normalized).strip(" .-")
    if not normalized:
        raise ResearchRunError("invalid_plan", "plan security name has no safe path characters")
    if len(normalized) > 80:
        normalized = normalized[:80].rstrip(" .-")
    thscode = identity.get("thscode")
    identity_slug = thscode[:6] if isinstance(thscode, str) else security_id.replace(":", "-")
    return f"{identity_slug}-{normalized}"


def allocate_default_workspace(
    plan: dict[str, Any],
    *,
    root: Path | str | None = None,
    environment: dict[str, str] | None = None,
    home: Path | None = None,
) -> tuple[Path, str]:
    archive_root, _source = output_root(root, environment=environment, home=home)
    as_of = plan.get("as_of")
    try:
        dt.date.fromisoformat(str(as_of))
    except ValueError as exc:
        raise ResearchRunError("invalid_plan", "plan as_of must be an ISO date") from exc
    research_root = archive_root / company_directory_name(plan) / str(as_of) / ".research"
    for _attempt in range(10):
        run_id = uuid.uuid4().hex
        workspace = research_root / run_id
        if not workspace.exists() and not workspace.is_symlink():
            return workspace, run_id
    raise ResearchRunError("workspace_collision", "could not allocate a unique research workspace")


def operation_slug(item: dict[str, Any]) -> str:
    operation = item["operation"]
    arguments = item["arguments"]
    if operation == "financials":
        return str(arguments["statement"])
    if operation == "corporate-actions":
        return "actions"
    return str(operation)


def operation_title(item: dict[str, Any]) -> str:
    provider = str(item.get("provider", "fuyao"))
    operation = item["operation"]
    arguments = item["arguments"]
    if provider == "yfinance":
        titles = {
            "search": "yfinance/Yahoo Finance ticker identity search",
            "snapshot": "yfinance/Yahoo Finance market snapshot",
            "valuations": "yfinance/Yahoo Finance valuation measures",
            "history": "yfinance/Yahoo Finance adjusted daily price history",
            "corporate-actions": "yfinance/Yahoo Finance corporate actions",
        }
        if operation in titles:
            return titles[operation]
        if operation == "financials":
            return f"yfinance/Yahoo Finance {arguments['period']} {arguments['statement']} statements"
        raise ResearchRunError("invalid_plan", f"unsupported yfinance provider operation: {operation}")
    if provider != "fuyao":
        raise ResearchRunError("invalid_plan", f"unsupported provider: {provider}")
    titles = {
        "search": "Fuyao A-share ticker search",
        "snapshot": "Fuyao A-share price snapshot",
        "valuations": "Fuyao A-share valuation snapshot",
        "history": "Fuyao forward-adjusted daily price history",
        "corporate-actions": "Fuyao corporate-action adjustment factors",
        "calendar": "Fuyao trading calendar",
    }
    if operation in titles:
        return titles[operation]
    if operation == "financials":
        return f"Fuyao {arguments['period']} {arguments['statement']} statements"
    if operation == "indicators":
        return f"Fuyao {arguments['report']} financial indicators"
    raise ResearchRunError("invalid_plan", f"unsupported provider operation: {operation}")


def derived_case(plan: dict[str, Any], plan_sha256: str) -> dict[str, Any]:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ResearchRunError("invalid_plan", f"plan schema must be {PLAN_SCHEMA}")
    identity = plan.get("identity")
    operations = plan.get("provider_operations")
    requirements = plan.get("official_evidence_requirements")
    if not isinstance(identity, dict) or not isinstance(operations, list):
        raise ResearchRunError("invalid_plan", "plan identity and provider_operations are required")
    if not isinstance(requirements, list) or not requirements:
        raise ResearchRunError("invalid_plan", "official evidence requirements are required")
    seen: set[str] = set()
    case_operations: list[dict[str, Any]] = []
    plan_provider = plan.get("provider")
    if not isinstance(plan_provider, dict):
        raise ResearchRunError("invalid_plan", "plan provider is required")
    default_provider = str(plan_provider.get("adapter", "fuyao"))
    documentation = provider_documentation(default_provider)
    for item in operations:
        if not isinstance(item, dict) or not isinstance(item.get("arguments"), dict):
            raise ResearchRunError("invalid_plan", "provider operation must be an object")
        source_id = item.get("id")
        if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id) or source_id in seen:
            raise ResearchRunError("invalid_plan", "provider source IDs must be unique Sxx identifiers")
        seen.add(source_id)
        operation_provider = str(item.get("provider", default_provider))
        if operation_provider != default_provider:
            raise ResearchRunError("invalid_plan", "provider operation adapter must match plan provider")
        provider_documentation(operation_provider)
        case_operations.append(
            {
                "id": source_id,
                "title": operation_title(item),
                "provider": operation_provider,
                "operation": item["operation"],
                "arguments": item["arguments"],
                "output": f"{source_id}-{operation_slug(item)}.normalized.json",
            }
        )
    official_sources: list[dict[str, Any]] = []
    for item in requirements:
        if not isinstance(item, dict):
            raise ResearchRunError("invalid_plan", "official evidence requirement must be an object")
        source_id = item.get("id")
        if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id) or source_id in seen:
            raise ResearchRunError("invalid_plan", "official source IDs must be unique Sxx identifiers")
        seen.add(source_id)
        role = item.get("role")
        if not isinstance(role, str) or not role:
            raise ResearchRunError("invalid_plan", f"{source_id}.role is required")
        required = item.get("required", True)
        if not isinstance(required, bool):
            raise ResearchRunError("invalid_plan", f"{source_id}.required must be boolean")
        trigger = item.get("trigger")
        if trigger is not None and (not isinstance(trigger, str) or not trigger.strip()):
            raise ResearchRunError("invalid_plan", f"{source_id}.trigger must be non-empty text")
        kind = item.get("kind", "official-index" if "index" in role else ("official-document" if required else "official-material"))
        if kind not in {"official-index", "official-document", "official-material"}:
            raise ResearchRunError("invalid_plan", "official evidence requires an official source kind")
        source = {
            "id": source_id,
            "role": role,
            "period": item.get("period"),
            "kind": kind,
            "status": "pending",
        }
        if "required" in item:
            source["required"] = required
        if trigger is not None:
            source["trigger"] = trigger.strip()
        official_sources.append(source)
    public_sources = []
    public_requirements = plan.get("public_evidence_requirements", [])
    if not isinstance(public_requirements, list):
        raise ResearchRunError("invalid_plan", "public evidence requirements must be an array")
    for item in public_requirements:
        if (not isinstance(item, dict) or not isinstance(item.get("id"), str)
                or not SOURCE_ID_RE.fullmatch(item["id"]) or item["id"] in seen
                or item.get("required") is not False
                or not isinstance(item.get("role"), str) or not item["role"].strip()):
            raise ResearchRunError("invalid_plan", "public sources need unique IDs, a role and required=false")
        seen.add(item["id"])
        public_sources.append({"id": item["id"], "role": item["role"], "required": False,
                               "kind": "public-material", "trust": "unverified-public", "status": "pending"})
    return {
        "schema": CASE_SCHEMA,
        "plan_sha256": plan_sha256,
        "identity": identity,
        "as_of": plan.get("as_of"),
        "provider_documentation": documentation,
        "operations": case_operations,
        "official_sources": official_sources,
        **({"public_sources": public_sources} if "public_evidence_requirements" in plan else {}),
    }


def reconciliation_contract(plan: dict[str, Any]) -> dict[str, Any] | None:
    contract = plan.get("reconciliation_contract")
    if contract is None:
        return None
    if not isinstance(contract, dict):
        raise ResearchRunError("invalid_plan", "reconciliation_contract must be an object")
    if (
        contract.get("schema") != financial_reconciliation.SCHEMA
        or contract.get("path") != "financial-reconciliation.json"
        or contract.get("audit_path") != "financial-reconciliation-audit.json"
        or contract.get("required") is not True
    ):
        raise ResearchRunError("invalid_plan", "reconciliation_contract has an unsupported identity")
    checks = contract.get("required_checks")
    if (
        not isinstance(checks, list)
        or not checks
        or any(item not in financial_reconciliation.CHECK_INPUTS for item in checks)
    ):
        raise ResearchRunError("invalid_plan", "reconciliation_contract.required_checks is invalid")
    disclosure_source_ids = contract.get("material_disclosure_source_ids")
    if disclosure_source_ids != ["S18", "S19", "S20"]:
        raise ResearchRunError("invalid_plan", "reconciliation_contract material disclosure sources are invalid")
    basis = contract.get("period_basis")
    if not isinstance(basis, list) or len(basis) != 2:
        raise ResearchRunError("invalid_plan", "reconciliation_contract.period_basis is invalid")
    return contract


def reconciliation_template(plan: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    identity = plan["identity"]
    return {
        "schema": financial_reconciliation.SCHEMA,
        "security": identity["security"],
        "security_id": identity["security_id"],
        "as_of": plan["as_of"],
        "base_currency": identity["base_currency"],
        "required_checks": contract["required_checks"],
        "period_basis": [
            {
                "role": item["role"],
                "period": item["period"],
                "basis": "unverified",
                "source_ids": ["S11"],
                "notes": "Confirm whether the source presents reported, restated, or comparable-estimate figures.",
            }
            for item in contract["period_basis"]
        ],
        "restatement_assessment": {
            "status": "unverified",
            "source_ids": ["S11", "S12"],
            "notes": "Inspect the formal filing and notes for retrospective restatement or accounting correction.",
        },
        "material_disclosure_assessment": [
            {
                "source_id": source_id,
                "status": "unverified",
                "notes": "Resolve whether this conditional disclosure route was triggered.",
            }
            for source_id in contract["material_disclosure_source_ids"]
        ],
        "checks": [],
        "presentation_to_economics": {
            "status": "unverified",
            "source_ids": ["S11"],
            "notes": "Resolve material accounting presentation effects before finalization.",
            "items": [],
        },
        "subsequent_events": {
            "status": "unverified",
            "source_ids": ["S11", "S13"],
            "notes": "Search official post-reporting-period disclosures and resolve material events.",
            "items": [],
        },
    }


def receipt_bound_files(plan: dict[str, Any]) -> set[str]:
    files = set(BASE_RECEIPT_BOUND_FILES)
    if reconciliation_contract(plan) is not None:
        files.update(RECONCILIATION_BOUND_FILES)
    return files


def render_draft(template: str, plan: dict[str, Any]) -> str:
    identity = plan["identity"]
    provider = plan.get("provider", {})
    provider_status = provider.get("availability") or (
        "available" if provider.get("configured") is True else "unavailable"
    )
    replacements = {
        "{{screen_or_research_or_earnings}}": "research",
        "{{security_name}}": identity["security"],
        "{{market_symbol}}": identity["security_id"],
        "{{YYYY-MM-DD}}": plan["as_of"],
        "{{base_currency}}": identity["base_currency"],
        "{{provider_availability}}": provider_status,
    }
    for marker, value in replacements.items():
        template = template.replace(marker, str(value))
    return template


def initialize_workspace(
    workspace: Path | str,
    plan: dict[str, Any],
    *,
    template_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    root = workspace_path(workspace)
    if root.exists() or root.is_symlink():
        raise ResearchRunError("existing_workspace", "workspace already exists; choose a new workspace")
    root.parent.mkdir(parents=True, exist_ok=True)
    with workspace_lock(root, allow_missing=True):
        return _initialize_workspace_locked(root, plan, template_root=template_root, run_id=run_id)


def _initialize_workspace_locked(
    workspace: Path | str,
    plan: dict[str, Any],
    *,
    template_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    root = workspace_path(workspace)
    if root.exists() or root.is_symlink():
        raise ResearchRunError("existing_workspace", "workspace already exists; choose a new workspace")
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = root.with_name(f".{root.name}.staging.{uuid.uuid4().hex}")
    if staging.exists() or staging.is_symlink():
        raise ResearchRunError("existing_workspace", "workspace staging path already exists")
    staging.mkdir(mode=0o700)
    try:
        plan_data = encoded_json(plan)
        plan_sha256 = sha256_bytes(plan_data)
        case = derived_case(plan, plan_sha256)
        case_data = encoded_json(case)
        effective_run_id = run_id or uuid.uuid4().hex
        if not re.fullmatch(r"[0-9a-f]{32}", effective_run_id):
            raise ResearchRunError("invalid_run_id", "research run_id must be 32 lowercase hex characters")
        state = {
            "schema": STATE_SCHEMA,
            "run_id": effective_run_id,
            "created_at": utc_now(),
            "plan_sha256": plan_sha256,
            "revision": 1,
            "events": [
                {
                    "sequence": 1,
                    "type": "initialized",
                    "at": utc_now(),
                    "details": {
                        "security_id": plan["identity"]["security_id"],
                        "as_of": plan["as_of"],
                        "provider_operation_count": len(case["operations"]),
                    },
                }
            ],
        }
        (staging / "evidence" / "captures").mkdir(parents=True, mode=0o700)
        atomic_bytes(staging / "plan.json", plan_data, replace=False)
        atomic_bytes(staging / "case.json", case_data, replace=False)
        atomic_json(staging / "run-state.json", state, replace=False)
        for name in ("report.md", "thesis.md"):
            template = (template_root / name).read_text(encoding="utf-8")
            atomic_bytes(staging / name, render_draft(template, plan).encode("utf-8"), replace=False)
        contract = reconciliation_contract(plan)
        if contract is not None:
            atomic_json(staging / contract["path"], reconciliation_template(plan, contract), replace=False)
        os.replace(staging, root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return {
        "schema": INIT_SCHEMA,
        "valid": True,
        "workspace": str(root),
        "run_id": state["run_id"],
        "plan_sha256": plan_sha256,
        "provider_operation_count": len(case["operations"]),
        "official_source_count": len(case["official_sources"]),
        "reconciliation_required": reconciliation_contract(plan) is not None,
        "network_used": False,
    }


def validate_state(state: dict[str, Any]) -> None:
    required = {"schema", "run_id", "created_at", "plan_sha256", "revision", "events"}
    if set(state) != required:
        raise ResearchRunError("invalid_state", "run-state fields are invalid")
    if state.get("schema") != STATE_SCHEMA:
        raise ResearchRunError("invalid_state", f"run-state schema must be {STATE_SCHEMA}")
    if not isinstance(state.get("run_id"), str) or not re.fullmatch(r"[0-9a-f]{32}", state["run_id"]):
        raise ResearchRunError("invalid_state", "run-state run_id is invalid")
    if not isinstance(state.get("plan_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", state["plan_sha256"]):
        raise ResearchRunError("invalid_state", "run-state plan hash is invalid")
    events = state.get("events")
    if not isinstance(events, list) or not events or len(events) > MAX_STATE_EVENTS:
        raise ResearchRunError("invalid_state", "run-state events are invalid")
    if type(state.get("revision")) is not int or state["revision"] != len(events):
        raise ResearchRunError("invalid_state", "run-state revision must match its event count")

    def valid_timestamp(value: Any) -> bool:
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt](?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]+)?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])", value):
            return False
        try:
            return dt.datetime.fromisoformat(value.replace("z", "Z").replace("Z", "+00:00")).utcoffset() is not None
        except ValueError:
            return False

    if not valid_timestamp(state["created_at"]):
        raise ResearchRunError("invalid_state", "run-state creation timestamp is invalid")
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict) or set(event) != {"sequence", "type", "at", "details"}:
            raise ResearchRunError("invalid_state", "run-state event fields are invalid")
        if type(event["sequence"]) is not int or event["sequence"] != index:
            raise ResearchRunError("invalid_state", "run-state events must be append-only and sequential")
        if not isinstance(event["type"], str) or not event["type"] or not isinstance(event["details"], dict):
            raise ResearchRunError("invalid_state", "run-state event type or details are invalid")
        if not valid_timestamp(event["at"]):
            raise ResearchRunError("invalid_state", "run-state event timestamp is invalid")


def load_workspace(workspace: Path | str) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = workspace_path(workspace)
    if not root.is_dir():
        raise ResearchRunError("missing_workspace", "research workspace does not exist")
    plan = load_json(root / "plan.json")
    case = load_json(root / "case.json")
    state = load_json(root / "run-state.json")
    validate_state(state)
    plan_sha256 = sha256_file(root / "plan.json")
    if state.get("plan_sha256") != plan_sha256 or case.get("plan_sha256") != plan_sha256:
        raise ResearchRunError("plan_drift", "plan.json changed after workspace initialization")
    expected_case = derived_case(plan, plan_sha256)
    if case.get("schema") != CASE_SCHEMA:
        raise ResearchRunError("invalid_case", f"case schema must be {CASE_SCHEMA}")
    for field in ("identity", "as_of", "provider_documentation", "operations"):
        if case.get(field) != expected_case[field]:
            raise ResearchRunError("case_drift", f"case.{field} no longer matches plan.json")
    for collection in ("official_sources", "public_sources"):
        actual_sources = case.get(collection, [])
        if not isinstance(actual_sources, list) or len(actual_sources) != len(expected_case.get(collection, [])):
            raise ResearchRunError("case_drift", "official source requirements no longer match plan.json")
        for expected, actual in zip(expected_case.get(collection, []), actual_sources):
            if not isinstance(actual, dict) or any(
                actual.get(key) != value for key, value in expected.items() if key != "status"
            ):
                raise ResearchRunError("case_drift", "official source identity no longer matches plan.json")
            if actual.get("status") not in {"pending", "imported"}:
                raise ResearchRunError("invalid_case", f"{expected['id']}.status is invalid")
            allowed = set(expected)
            if actual["status"] == "imported":
                allowed.update({"title", "url", "retrieved_on", "local_path", "sha256", "bytes"})
                if collection == "public_sources":
                    allowed.update({"captured_at", "observed_at"})
            if set(actual) != allowed:
                raise ResearchRunError("invalid_case", f"{expected['id']} contains unsupported metadata")
    evidence_root = root / "evidence"
    if evidence_root.is_symlink():
        raise ResearchRunError("invalid_case", "research evidence directory must not be a symlink")
    capture_root = evidence_root / "captures"
    if capture_root.is_symlink():
        raise ResearchRunError("invalid_case", "research capture directory must not be a symlink")
    operations_by_id = {item["id"]: item for item in case["operations"]}
    if capture_root.is_dir():
        for path in capture_root.iterdir():
            staged = re.fullmatch(r"\.(S[0-9]{2,4})\.staging\.[0-9a-f]{32}", path.name)
            source_id = staged.group(1) if staged else path.name
            operation = operations_by_id.get(source_id)
            if operation is None:
                continue
            normalized = evidence_root / operation["output"]
            if staged or not normalized.exists():
                raise ResearchRunError("incomplete_collection", "capture has no normalized result or capture staging remains; preserve this workspace and create a new run")
    official_by_id = {item["id"]: item for item in file_sources(case)}
    for path in evidence_root.iterdir():
        published = re.fullmatch(r"(S[0-9]{2,4})-(?:official|public)\.(pdf|html)", path.name)
        staging = re.fullmatch(r"\.(S[0-9]{2,4})-(?:official|public)\.(pdf|html)\.staging\.[0-9a-f]{32}", path.name)
        match = published or staging
        if match is None or match.group(1) not in official_by_id:
            continue
        source = official_by_id[match.group(1)]
        if staging or source["status"] == "pending":
            raise ResearchRunError("incomplete_import", "unregistered official evidence or import staging remains; preserve this workspace and create a new run")
    imported_ids = {item["id"] for item in file_sources(case) if item["status"] == "imported"}
    recorded_ids = {event.get("details", {}).get("source_id") for event in state["events"]
                    if event.get("type") in {"official-source-imported", "public-source-imported"} and isinstance(event.get("details"), dict)
                    and isinstance(event["details"].get("source_id"), str)}
    if not imported_ids.issubset(recorded_ids):
        raise ResearchRunError("incomplete_import", "official import has no completion event; preserve this workspace and create a new run")
    return root, plan, case, state


def require_unsealed_workspace(root: Path) -> None:
    receipt = root / "completion-receipt.json"
    if receipt.exists() or receipt.is_symlink():
        raise ResearchRunError(
            "finalized_workspace", "research is sealed; preserve its artifacts and create a new workspace for new evidence"
        )


def record_event(root: Path, state: dict[str, Any], event_type: str, details: dict[str, Any]) -> None:
    events = state["events"]
    if len(events) >= MAX_STATE_EVENTS:
        raise ResearchRunError("state_limit", "run-state event limit reached")
    state = dict(state)
    state["revision"] += 1
    state["events"] = [
        *events,
        {
            "sequence": len(events) + 1,
            "type": event_type,
            "at": utc_now(),
            "details": details,
        },
    ]
    atomic_json(root / "run-state.json", state)


def operation_command(runtime: Path, item: dict[str, Any], capture_root: Path) -> list[str]:
    provider = str(item.get("provider", "fuyao"))
    operation = item.get("operation")
    arguments = item.get("arguments")
    if not isinstance(arguments, dict):
        raise ResearchRunError("invalid_case", f"{item.get('id')}.arguments must be an object")
    option_orders = {
        "search": [("query", "--query"), ("limit", "--limit")],
        "snapshot": [("thscodes", "--thscodes"), ("symbol", "--symbol")],
        "valuations": [("thscodes", "--thscodes"), ("symbol", "--symbol")],
        "history": [
            ("thscode", "--thscode"),
            ("symbol", "--symbol"),
            ("start", "--start"),
            ("end", "--end"),
            ("interval", "--interval"),
            ("adjust", "--adjust"),
        ],
        "financials": [
            ("thscode", "--thscode"),
            ("symbol", "--symbol"),
            ("statement", "--statement"),
            ("period", "--period"),
            ("limit", "--limit"),
            ("start", "--start"),
            ("end", "--end"),
        ],
        "indicators": [("thscode", "--thscode"), ("report", "--report")],
        "corporate-actions": [
            ("thscode", "--thscode"),
            ("symbol", "--symbol"),
            ("start", "--start"),
            ("end", "--end"),
        ],
        "calendar": [("start", "--start"), ("end", "--end")],
    }
    if operation not in option_orders:
        raise ResearchRunError("invalid_case", f"unsupported operation: {operation}")
    option_order = option_orders[operation]
    unknown = sorted(set(arguments) - {name for name, _ in option_order})
    if unknown:
        raise ResearchRunError("invalid_case", f"unsupported arguments for {operation}: {', '.join(unknown)}")
    command = [sys.executable, str(runtime), "data", str(operation), "--provider", provider]
    for name, option in option_order:
        if name in arguments and arguments[name] is not None:
            command.extend([option, str(arguments[name])])
    command.extend(["--capture-dir", str(capture_root), "--source-id", str(item["id"])])
    return command


def operation_status(
    item: dict[str, Any], payload: dict[str, Any], returncode: int | None = None
) -> tuple[str, dict[str, Any] | None]:
    expected_provider = str(item.get("provider", "fuyao"))
    if payload.get("schema") != "money-craft.data-response.v1" or payload.get("provider") != expected_provider:
        raise ResearchRunError("invalid_response", f"{item['id']} response identity is invalid")
    expected = str(item["operation"])
    actual = payload.get("operation")
    matches = actual == (f"financials.{item['arguments']['statement']}" if expected == "financials" else expected)
    if not matches:
        raise ResearchRunError("invalid_response", f"{item['id']} response operation is invalid")
    if payload.get("ok") is True:
        if returncode not in (None, 0):
            raise ResearchRunError("invalid_response", f"{item['id']} returned ok=true with non-zero exit")
        if expected_provider == "fuyao" and expected in {"snapshot", "valuations"}:
            data = payload.get("data")
            rows = data.get("item") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ResearchRunError("invalid_response", f"{item['id']} batch rows are missing")
            requested = item["arguments"]["thscodes"].split(",")
            seen: set[str] = set()
            for row in rows:
                identity = row.get("thscode") if isinstance(row, dict) else None
                if not isinstance(identity, str) or identity not in requested or identity in seen:
                    raise ResearchRunError("invalid_response", f"{item['id']} batch identity is invalid")
                seen.add(identity)
            missing = [identity for identity in requested if identity not in seen]
            if missing:
                return "provider_gap", {"kind": "missing_requested_securities", "code": None, "retryable": False, "missing": missing}
        return "passed", None
    if payload.get("ok") is not False or returncode == 0:
        raise ResearchRunError("invalid_response", f"{item['id']} error response is invalid")
    error = payload.get("error")
    if not isinstance(error, dict):
        raise ResearchRunError("invalid_response", f"{item['id']} error details are missing")
    return "provider_gap", {
        "kind": error.get("kind"),
        "code": error.get("code"),
        "retryable": error.get("retryable") is True,
    }


def validate_identity(payload: dict[str, Any], case: dict[str, Any]) -> None:
    data = payload.get("data")
    items = data.get("item") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise ResearchRunError("identity_mismatch", "ticker search data.item must be an array")
    identity = case["identity"]
    provider = str(payload.get("provider"))
    if provider == "yfinance":
        expected_symbol = identity.get("provider_identifiers", {}).get("yfinance")
        matches = [
            item
            for item in items
            if isinstance(item, dict) and str(item.get("symbol", "")).upper() == expected_symbol
        ]
        if len(matches) != 1:
            raise ResearchRunError("identity_mismatch", "yfinance search did not resolve the exact provider symbol")
        currency = matches[0].get("currency")
        if isinstance(currency, str) and currency and currency.upper() != identity["base_currency"]:
            raise ResearchRunError("identity_mismatch", "yfinance search currency conflicts with the plan identity")
        quote_type = matches[0].get("quoteType")
        if isinstance(quote_type, str) and quote_type.upper() not in {"EQUITY", "STOCK"}:
            raise ResearchRunError("identity_mismatch", "yfinance search result is not a listed equity")
        return
    if provider != "fuyao":
        raise ResearchRunError("identity_mismatch", "unsupported provider identity response")
    matches = [
        item
        for item in items
        if isinstance(item, dict) and item.get("thscode") == identity["thscode"]
    ]
    if len(matches) != 1 or matches[0].get("name") != identity["security"]:
        raise ResearchRunError("identity_mismatch", "ticker search did not resolve the exact plan identity")


def normalized_payload(path: Path) -> dict[str, Any]:
    return load_json(path)


@locked_workspace
def collect_workspace(
    workspace: Path | str,
    *,
    runtime: Path,
    resume: bool = False,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    return _collect_workspace_locked(workspace, runtime=runtime, resume=resume, runner=runner)


def _collect_workspace_locked(
    workspace: Path | str,
    *,
    runtime: Path,
    resume: bool = False,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    root, _plan, case, state = load_workspace(workspace)
    require_unsealed_workspace(root)
    if not case["operations"]:
        raise ResearchRunError(
            "provider_unavailable",
            "this research plan has no executable structured-data provider operations",
        )
    if len(state["events"]) >= MAX_STATE_EVENTS:
        raise ResearchRunError("state_limit", "run-state event limit reached")
    evidence_root = root / "evidence"
    capture_root = evidence_root / "captures"
    capture_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    results: list[dict[str, Any]] = []
    for item in case["operations"]:
        destination = evidence_root / item["output"]
        if destination.exists() or destination.is_symlink():
            if not resume or destination.is_symlink() or not destination.is_file():
                raise ResearchRunError("existing_artifact", f"normalized output already exists: {destination.name}")
            payload = normalized_payload(destination)
            status, error = operation_status(item, payload, 0 if payload.get("ok") is True else 1)
            if payload.get("ok") is True:
                validate_provider_capture(root, item, payload)
                if item["operation"] == "search":
                    validate_identity(payload, case)
            result = {"id": item["id"], "operation": item["operation"], "status": status, "resumed": True}
            if error:
                result["error"] = error
            results.append(result)
            if item["operation"] == "search" and status != "passed":
                break
            continue

        completed = runner(
            operation_command(runtime, item, capture_root),
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ResearchRunError("invalid_response", f"{item['id']} did not return JSON") from exc
        if not isinstance(payload, dict):
            raise ResearchRunError("invalid_response", f"{item['id']} response must be an object")
        status, error = operation_status(item, payload, completed.returncode)
        if payload.get("ok") is True:
            if item["operation"] == "search":
                validate_identity(payload, case)
            capture = payload.get("capture")
            if not isinstance(capture, dict):
                raise ResearchRunError("missing_capture", f"{item['id']} passed without an evidence capture")
            capture["path"] = f"captures/{item['id']}"
            validate_provider_capture(root, item, payload)
        atomic_json(destination, payload, replace=False)
        result = {"id": item["id"], "operation": item["operation"], "status": status, "resumed": False}
        if error:
            result["error"] = error
        results.append(result)
        if item["operation"] == "search" and status != "passed":
            break

    passed = sum(item["status"] == "passed" for item in results)
    gaps = sum(item["status"] == "provider_gap" for item in results)
    terminal = len(results)
    total = len(case["operations"])
    summary = {
        "schema": COLLECTION_SCHEMA,
        "valid": terminal == total and gaps == 0,
        "identity_verified": bool(results and results[0]["status"] == "passed"),
        "network_boundary": "explicit-provider-collection",
        "network_requests_attempted": sum(not item["resumed"] for item in results),
        "passed": passed,
        "provider_gaps": gaps,
        "terminal": terminal,
        "total": total,
        "complete": terminal == total,
        "results": results,
    }
    atomic_json(evidence_root / "collection-summary.json", summary)
    record_event(
        root,
        state,
        "provider-collection",
        {
            "passed": passed,
            "provider_gaps": gaps,
            "terminal": terminal,
            "total": total,
            "resume": resume,
            "network_requests_attempted": summary["network_requests_attempted"],
        },
    )
    return summary


def file_sources(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [*case["official_sources"], *case.get("public_sources", [])]


def source_namespace(item: dict[str, Any]) -> str:
    return "public" if item["kind"] == "public-material" else "official"


def validate_public_times(captured_at: str, observed_at: str, as_of: str) -> None:
    try:
        captured = dt.datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        observed = dt.datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if captured.utcoffset() is None or observed.utcoffset() is None or observed > captured:
            raise ValueError("timezone or ordering")
        if observed.astimezone(SHANGHAI).date() > dt.date.fromisoformat(as_of):
            raise ValueError("observation after research cutoff")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ResearchRunError("invalid_public_source", "public evidence needs timezone-aware capture/observation times, observed <= capture and research cutoff") from exc


def validate_https_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ResearchRunError("invalid_official_source", "official source URL must use HTTPS without credentials")
    return value


def validate_official_file(path: Path, kind: str) -> tuple[int, str]:
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise ResearchRunError("missing_official_source", "official source file does not exist") from exc
    if path.is_symlink() or not path.is_file():
        raise ResearchRunError("invalid_official_source", "official source must be a regular file, not a symlink")
    if metadata.st_size < 1 or metadata.st_size > MAX_OFFICIAL_SOURCE_BYTES:
        raise ResearchRunError("invalid_official_source", "official source size is outside the allowed range")
    with path.open("rb") as handle:
        prefix = handle.read(1024).lstrip().lower()
    is_pdf = prefix.startswith(b"%pdf-")
    is_html = b"<" in prefix
    if kind == "official-document" and not (is_pdf or is_html):
        raise ResearchRunError("invalid_official_source", "official filing must be PDF or HTML")
    if kind == "official-index" and not is_html:
        raise ResearchRunError("invalid_official_source", "official index is not HTML")
    if kind in {"official-material", "public-material"} and not (is_pdf or is_html):
        raise ResearchRunError("invalid_official_source", "optional official material must be PDF or HTML")
    if kind not in {"official-document", "official-index", "official-material", "public-material"}:
        raise ResearchRunError("invalid_official_source", f"unsupported official source kind: {kind}")
    return metadata.st_size, ".pdf" if is_pdf else ".html"


def import_official_source(workspace: Path | str, **kwargs: Any) -> dict[str, Any]:
    return _import_file_source(workspace, collection="official_sources", **kwargs)


def import_public_source(workspace: Path | str, *, captured_at: str, observed_at: str, **kwargs: Any) -> dict[str, Any]:
    return _import_file_source(workspace, collection="public_sources", captured_at=captured_at, observed_at=observed_at, **kwargs)


@locked_workspace
def _import_file_source(
    workspace: Path | str,
    *,
    source_id: str,
    source_file: Path,
    url: str,
    title: str | None = None,
    retrieved_on: str | None = None,
    collection: str,
    captured_at: str | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    root, plan, case, state = load_workspace(workspace)
    require_unsealed_workspace(root)
    if len(state["events"]) >= MAX_STATE_EVENTS:
        raise ResearchRunError("state_limit", "run-state event limit reached")
    original_case_bytes = (root / "case.json").read_bytes()
    sources = case.get(collection, [])
    matches = [item for item in sources if item["id"] == source_id]
    if len(matches) != 1:
        raise ResearchRunError("invalid_public_source" if collection == "public_sources" else "invalid_official_source",
                               "source-id is not a requirement of this source type in plan.json")
    source = matches[0]
    if source.get("status") != "pending":
        raise ResearchRunError("existing_artifact", f"official source already imported: {source_id}")
    kind = source["kind"]
    if collection == "public_sources":
        validate_public_times(captured_at, observed_at, plan["as_of"])
    namespace = source_namespace(source)
    source_file = Path(os.path.abspath(source_file.expanduser()))
    size, suffix = validate_official_file(source_file, kind)
    url = validate_https_url(url)
    if namespace == "public":
        capture_date = dt.datetime.fromisoformat(captured_at.replace("Z", "+00:00")).astimezone(SHANGHAI).date().isoformat()
        if retrieved_on is not None and retrieved_on != capture_date:
            raise ResearchRunError("invalid_public_source", "retrieved-on must match the public capture date")
        retrieved_on = capture_date
    date_value = retrieved_on or dt.datetime.now(SHANGHAI).date().isoformat()
    try:
        dt.date.fromisoformat(date_value)
    except ValueError as exc:
        raise ResearchRunError("invalid_official_source", "retrieved-on must be YYYY-MM-DD") from exc
    resolved_title = title.strip() if isinstance(title, str) else f"{plan['identity']['security']} {source['role']}"
    if not resolved_title or len(resolved_title) > 256:
        raise ResearchRunError("invalid_official_source", "official source title must contain 1..256 characters")
    relative = f"{source_id}-{namespace}{suffix}"
    destination = root / "evidence" / relative
    if destination.exists() or destination.is_symlink():
        raise ResearchRunError("existing_artifact", f"official evidence already exists: {relative}")
    staging = destination.with_name(f".{destination.name}.staging.{uuid.uuid4().hex}")
    staged_identity = None
    try:
        with source_file.open("rb") as input_handle, staging.open("xb") as output_handle:
            shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
            output_handle.flush()
            os.fsync(output_handle.fileno())
        metadata = staging.stat()
        staged_identity = (metadata.st_dev, metadata.st_ino)
        os.replace(staging, destination)
        digest = sha256_file(destination)
        updated_source = {
            **source,
            "status": "imported",
            "title": resolved_title,
            "url": url,
            "retrieved_on": date_value,
            "local_path": relative,
            "sha256": digest,
            "bytes": size,
            **({"captured_at": captured_at, "observed_at": observed_at} if namespace == "public" else {}),
        }
        updated_case = dict(case)
        updated_case[collection] = [updated_source if item["id"] == source_id else item for item in sources]
        atomic_json(root / "case.json", updated_case)
    except Exception:
        if staging.exists():
            staging.unlink()
        # A failed call may already have published case.json. Only roll back
        # our evidence when the original case is still confirmed on disk.
        try:
            unchanged = (root / "case.json").read_bytes() == original_case_bytes
            metadata = destination.lstat()
            owned = (metadata.st_dev, metadata.st_ino) == staged_identity
        except OSError:
            unchanged = owned = False
        if unchanged and owned:
            destination.unlink()
        raise
    record_event(root, state, f"{namespace}-source-imported", {"source_id": source_id, "sha256": digest, "bytes": size})
    return {
        "schema": "money-craft.public-import.v1" if namespace == "public" else IMPORT_SCHEMA,
        "valid": True,
        "source_id": source_id,
        "kind": kind,
        "title": resolved_title,
        "url": url,
        "retrieved_on": date_value,
        "local_path": f"evidence/{relative}",
        "sha256": digest,
        "bytes": size,
        **({"captured_at": captured_at, "observed_at": observed_at, "trust": "unverified-public"}
           if namespace == "public" else {}),
    }


def fuyao_request_projection(item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Expected sanitized CLI request for the supported research operations."""
    args = item["arguments"]
    operation = item["operation"]
    def option(key: str, default: Any) -> Any:
        value = args.get(key)
        return default if value is None else value
    def security(key: str) -> str:
        return ",".join(dict.fromkeys(part.strip().upper() for part in args[key].split(",")))
    def milliseconds(value: str) -> int:
        return int(dt.datetime.combine(dt.date.fromisoformat(value), dt.time(), tzinfo=SHANGHAI).timestamp() * 1000)
    try:
        if operation == "search":
            return "/api/meta/tickers/search", {"q": args["query"].strip(), "asset_type": "a-share", "limit": option("limit", 10)}
        if operation in {"snapshot", "valuations"}:
            path = "/api/a-share/prices/snapshot" if operation == "snapshot" else "/api/a-share/valuations/snapshot"
            return path, {"thscodes": security("thscodes")}
        if operation == "calendar":
            return "/api/a-share/calendar/trading-days", {"start": args.get("start"), "end": args.get("end")}
        if operation == "corporate-actions":
            return "/api/a-share/corporate-actions/adjustment-factors", {"thscode": security("thscode"), "from": args.get("start"), "to": args.get("end")}
        if operation == "indicators":
            return "/api/a-share/financials/indicators", {"thscode": security("thscode"), "report": args["report"]}
        if operation == "history":
            return "/api/a-share/prices/historical", {"thscode": security("thscode"), "interval": option("interval", "1d"), "adjust": option("adjust", "forward"), "start": milliseconds(args["start"]), "end": milliseconds(args["end"]), "start_date": args["start"], "end_date": args["end"]}
        if operation == "financials":
            paths = {"income": "income-statements", "balance": "balance-sheets", "cash-flow": "cash-flow-statements"}
            params = {"thscode": security("thscode"), "period": option("period", "annual")}
            if args.get("start") is not None:
                params.update(start=milliseconds(args["start"]), end=milliseconds(args["end"]), start_date=args["start"], end_date=args["end"])
            else:
                params["limit"] = 4 if args.get("limit") is None else args["limit"]
            return "/api/a-share/financials/" + paths[args["statement"]], params
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        raise ResearchRunError("invalid_case", f"invalid request arguments: {item['id']}") from exc
    raise ResearchRunError("invalid_case", f"unsupported Fuyao request: {item['id']}")


def yfinance_request_projection(item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    args, operation = item["arguments"], item["operation"]
    def option(key: str, default: Any) -> Any:
        return default if args.get(key) is None else args[key]
    try:
        if operation == "search":
            return "yfinance://search", {"query": args["query"].strip(), "limit": option("limit", 10)}
        params: dict[str, Any] = {"symbol": args["symbol"].strip().upper()}
        if operation in {"snapshot", "valuations"}:
            return "yfinance://" + operation, params
        if operation == "history":
            adjust = option("adjust", "forward")
            params.update(start=args["start"], end=args["end"], interval=option("interval", "1d"), adjust="auto" if adjust in {"auto", "forward"} else "none")
        elif operation == "financials":
            params.update(period=option("period", "annual"), limit=option("limit", 4))
            return "yfinance://financials/" + args["statement"], params
        elif operation == "corporate-actions":
            params.update(start=args.get("start"), end=args.get("end"))
        else:
            raise ValueError("unsupported operation")
        return "yfinance://" + operation, params
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ResearchRunError("invalid_case", f"invalid yfinance request: {item['id']}") from exc


def validate_provider_request(root: Path, item: dict[str, Any], payload: dict[str, Any]) -> None:
    request = load_json(root / "evidence" / "captures" / item["id"] / "request.json")
    provider = payload["provider"]
    projection = fuyao_request_projection if provider == "fuyao" else yfinance_request_projection
    path, parameters = projection(item)
    expected = {"schema": "money-craft.sanitized-request.v1", "provider": provider, "operation": payload["operation"], "method": "GET", "path": path}
    if any(request.get(key) != value for key, value in expected.items()):
        raise ResearchRunError("invalid_capture", f"captured request differs from research operation: {item['id']}")
    try:
        canonical = json.dumps(parameters, sort_keys=True, allow_nan=False)
        if any(json.dumps(value, sort_keys=True, allow_nan=False) != canonical for value in (request.get("parameters"), payload.get("parameters"))):
            raise ValueError("parameter mismatch")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ResearchRunError("evidence_drift", f"request parameters differ from research case: {item['id']}") from exc


def validate_fuyao_capture_content(raw: Path, item: dict[str, Any], payload: dict[str, Any]) -> None:
    """Reproduce the CLI projection; capture hashes alone do not bind normalized data."""
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    try:
        with raw.open("rb") as stream:
            content = stream.read(MAX_JSON_BYTES + 1)
        if len(content) > MAX_JSON_BYTES:
            raise ValueError("capture exceeds JSON limit")
        captured = json.loads(
            content.decode("utf-8"), object_pairs_hook=unique_object,
            parse_float=lambda value: str(Decimal(value)),
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON constant")),
        )
        if not isinstance(captured, dict) or type(captured.get("code")) is not int or captured["code"] != 0:
            raise ValueError("capture is not a successful response")
        if captured.get("request_id") != payload.get("request_id") or not isinstance(captured.get("data"), dict):
            raise ValueError("capture identity or data is invalid")
        projected = captured["data"]
        timestamp = projected.get("timestamp")
        if item["operation"] == "calendar":
            start, end = item["arguments"].get("start"), item["arguments"].get("end")
            if start or end:
                rows = projected.get("item")
                if not isinstance(rows, list) or any(not isinstance(row, dict) or not isinstance(row.get("date"), str) for row in rows):
                    raise ValueError("invalid calendar rows")
                start_key = start.replace("-", "") if start else None
                end_key = end.replace("-", "") if end else None
                projected = dict(projected)
                projected["item"] = [row for row in rows if (not start_key or row["date"] >= start_key) and (not end_key or row["date"] <= end_key)]
        # JSON comparison preserves type distinctions such as True versus 1.
        expected = json.dumps([projected, timestamp], sort_keys=True, ensure_ascii=False, allow_nan=False)
        actual = json.dumps([payload.get("data"), payload.get("source_timestamp_ms")], sort_keys=True, ensure_ascii=False, allow_nan=False)
        if actual != expected:
            raise ValueError("normalized content differs")
    except (OSError, UnicodeError, ValueError, TypeError, InvalidOperation, RecursionError) as exc:
        raise ResearchRunError("evidence_drift", f"normalized data differs from captured response: {item['id']}") from exc


def validate_yfinance_capture_content(raw: Path, item: dict[str, Any], payload: dict[str, Any]) -> None:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    try:
        with raw.open("rb") as stream:
            content = stream.read(MAX_JSON_BYTES + 1)
        if len(content) > MAX_JSON_BYTES:
            raise ValueError("oversized export")
        export = json.loads(content.decode("utf-8"), object_pairs_hook=unique_object,
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite constant")))
        _path, parameters = yfinance_request_projection(item)
        effective = {key: value for key, value in parameters.items() if value is not None}
        expected = {"schema": "money-craft.yfinance-adapter-export.v1", "provider": "yfinance",
                    "operation": payload["operation"], "parameters": effective,
                    "symbol": effective.get("symbol"), "fetched_at": payload.get("fetched_at"), "data": payload.get("data")}
        if not isinstance(export, dict) or not isinstance(export.get("data"), dict) or payload.get("request_id") is not None:
            raise ValueError("invalid export")
        actual = {key: export.get(key) for key in expected}
        if json.dumps(actual, sort_keys=True, allow_nan=False) != json.dumps(expected, sort_keys=True, allow_nan=False):
            raise ValueError("export differs")
        if json.dumps(export["data"].get("timestamp"), allow_nan=False) != json.dumps(payload.get("source_timestamp_ms"), allow_nan=False):
            raise ValueError("timestamp differs")
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise ResearchRunError("evidence_drift", f"normalized data differs from yfinance export: {item['id']}") from exc


def validate_provider_capture(root: Path, item: dict[str, Any], payload: dict[str, Any]) -> Path:
    folder = root / "evidence" / "captures" / item["id"]
    raw = folder / "response.json"
    if any(path.is_symlink() for path in (root / "evidence", folder.parent, folder, raw)) or not raw.is_file():
        raise ResearchRunError("missing_capture", f"missing or unsafe provider capture: {item['id']}")
    capture = load_json(folder / "capture.json")
    expected = {
        "schema": "money-craft.source-capture.v1", "source_id": item["id"],
        "provider": payload.get("provider"), "operation": payload.get("operation"),
        "request_id": payload.get("request_id"), "fetched_at": payload.get("fetched_at"),
    }
    if any(capture.get(key) != value for key, value in expected.items()):
        raise ResearchRunError("invalid_capture", f"provider capture metadata differs from response: {item['id']}")
    if capture.get("response_sha256") != sha256_file(raw) or capture.get("response_bytes") != raw.stat().st_size:
        raise ResearchRunError("evidence_drift", f"provider response changed after capture: {item['id']}")
    if payload.get("provider") in {"fuyao", "yfinance"}:
        validate_provider_request(root, item, payload)
    if payload.get("provider") == "fuyao":
        validate_fuyao_capture_content(raw, item, payload)
    elif payload.get("provider") == "yfinance":
        validate_yfinance_capture_content(raw, item, payload)
    return raw


def inspect_provider(root: Path, case: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    results: list[dict[str, Any]] = []
    pending: list[str] = []
    gaps: list[str] = []
    for item in case["operations"]:
        path = root / "evidence" / item["output"]
        if not path.is_file() or path.is_symlink():
            pending.append(item["id"])
            results.append({"id": item["id"], "status": "pending"})
            continue
        payload = normalized_payload(path)
        status, error = operation_status(item, payload, 0 if payload.get("ok") is True else 1)
        if payload.get("ok") is True:
            if item["operation"] == "search":
                validate_identity(payload, case)
            validate_provider_capture(root, item, payload)
        if status == "provider_gap":
            gaps.append(item["id"])
        result = {"id": item["id"], "status": status}
        if error:
            result["error"] = error
        results.append(result)
    return results, pending, gaps


def inspect_official(root: Path, case: dict[str, Any], collection: str = "official_sources") -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    pending: list[str] = []
    for item in case.get(collection, []):
        if item.get("status") == "pending":
            is_required = item.get("required", True)
            if is_required:
                pending.append(item["id"])
            results.append(
                {
                    "id": item["id"],
                    "status": "pending" if is_required else "optional-not-imported",
                    "required": is_required,
                    "trigger": item.get("trigger"),
                }
            )
            continue
        metadata_fields = ("title", "url", "retrieved_on", "local_path", "sha256", "bytes")
        if any(key not in item for key in metadata_fields):
            raise ResearchRunError("invalid_case", f"{item['id']} imported metadata is incomplete")
        namespace = source_namespace(item)
        if namespace == "public":
            validate_public_times(item.get("captured_at"), item.get("observed_at"), case["as_of"])
        local_path = item["local_path"]
        if not isinstance(local_path, str) or local_path not in {
            f"{item['id']}-{namespace}.pdf", f"{item['id']}-{namespace}.html"
        }:
            raise ResearchRunError("invalid_case", f"{item['id']} official path must match its imported source file")
        validate_https_url(str(item["url"]))
        path = root / "evidence" / local_path
        _size, suffix = validate_official_file(path, str(item["kind"]))
        if local_path != f"{item['id']}-{namespace}{suffix}":
            raise ResearchRunError("invalid_case", f"{item['id']} official file format does not match its imported path")
        if sha256_file(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise ResearchRunError("evidence_drift", f"official evidence changed after import: {item['id']}")
        results.append(
            {
                "id": item["id"],
                "status": "imported",
                "required": item.get("required", True),
                "sha256": item["sha256"],
            }
        )
    return results, pending


def available_evidence_sources(root: Path, case: dict[str, Any]) -> dict[str, set[str]]:
    """Return registered citation targets for passed or imported evidence.

    A normalized provider error is deliberately excluded: it is retained for
    diagnostics, but cannot support a report or thesis citation.
    """
    sources: dict[str, set[str]] = {}
    for item in case["operations"]:
        normalized = root / "evidence" / item["output"]
        if not normalized.is_file() or normalized.is_symlink():
            continue
        payload = normalized_payload(normalized)
        status, _error = operation_status(item, payload, 0 if payload.get("ok") is True else 1)
        if status != "passed":
            continue
        raw = validate_provider_capture(root, item, payload)
        sources[item["id"]] = {
            f"evidence/{item['output']}",
            f"evidence/captures/{item['id']}/response.json",
        }
    for item in file_sources(case):
        if item.get("status") == "imported":
            sources[item["id"]] = {f"evidence/{item['local_path']}", item["url"]}
    return sources


def citation_binding_audit(path: Path, evidence_sources: dict[str, set[str]] | None) -> dict[str, Any]:
    if evidence_sources is None:
        return {"valid": False, "errors": ["research evidence map is required for citation verification"]}
    if not path.is_file() or path.is_symlink():
        return {"valid": False, "errors": [f"citation document is unavailable: {path.name}"]}
    text = path.read_text(encoding="utf-8")
    _metadata, body, _errors = report_audit.parse_frontmatter(text)
    source_section = report_audit.extract_section(body, "来源索引")
    definitions = {
        source_id: target.strip()
        for source_id, target in report_audit.SOURCE_DEFINITION_RE.findall(source_section)
    }
    body_without_index = report_audit.section_pattern("来源索引").sub("", body)
    cited_ids = set(report_audit.SOURCE_RE.findall(body_without_index))
    errors: list[str] = []
    for source_id in sorted(cited_ids | set(definitions)):
        if source_id not in evidence_sources:
            errors.append(f"{source_id} is not a passed or imported research evidence source")
    for source_id, target in definitions.items():
        link = re.fullmatch(r"\[[^\]]+\]\(([^\s)]+)\)", target)
        local_candidate = link.group(1) if link else target
        local_match = re.fullmatch(r"`?(evidence/[^`\s]+)`?", local_candidate)
        if "evidence/" in local_candidate and not re.match(r"^https?://[^\s]+$", local_candidate):
            if local_match is None:
                errors.append(f"{source_id} local evidence path must be an exact evidence/... path")
            elif local_match.group(1) not in evidence_sources.get(source_id, set()):
                errors.append(f"{source_id} local evidence path does not match its verified manifest path")
        if re.search(r"https?://", local_candidate):
            if not re.fullmatch(r"https?://[^\s`]+", local_candidate):
                errors.append(f"{source_id} public source URL must be an exact URL or single Markdown link")
            elif local_candidate not in evidence_sources.get(source_id, set()):
                errors.append(f"{source_id} public source URL does not match its imported evidence URL")
    return {
        "valid": not errors,
        "cited_source_ids": sorted(cited_ids),
        "defined_source_ids": sorted(definitions),
        "errors": errors,
    }


def document_audits(
    path: Path,
    plan: dict[str, Any],
    schema: str,
    *,
    evidence_sources: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise ResearchRunError("invalid_document", f"research document must be a regular file: {path.name}")
    if path.is_file() and path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise ResearchRunError("invalid_document", f"research document exceeds the size limit: {path.name}")
    report_result = report_audit.audit_file(path)
    financial_result = financial_rigor.audit_file(path)
    metadata = report_result.get("metadata", {})
    expected = {
        "schema": schema,
        "security": plan["identity"]["security"],
        "security_id": plan["identity"]["security_id"],
        "as_of": plan["as_of"],
        "base_currency": plan["identity"]["base_currency"],
    }
    actual = dict(metadata)
    try:
        actual["security_id"] = report_audit.security_id_from_metadata(metadata)
    except ValueError:
        pass  # report_audit.audit_file already reports the parse reason; avoid a duplicate error
    identity_errors = [f"{key} must match plan.json" for key, value in expected.items() if actual.get(key) != value]
    if identity_errors:
        report_result = dict(report_result)
        report_result["valid"] = False
        report_result["errors"] = [*report_result.get("errors", []), *identity_errors]
    if schema == "money-craft.thesis.v1" and report_result["valid"] and financial_result["valid"]:
        try:
            research_workflow.load_thesis(path)
        except research_workflow.WorkflowError as exc:
            report_result = dict(report_result)
            report_result["valid"] = False
            report_result["errors"] = [*report_result.get("errors", []), str(exc)]
    if schema == "money-craft.report.v1" and reconciliation_contract(plan) is not None and path.is_file():
        text = path.read_text(encoding="utf-8")
        reconciliation_errors: list[str] = []
        for heading in ("重大披露与期后事项", "重述口径与三表勾稽"):
            section = report_audit.extract_section(text, heading)
            if not section.strip():
                reconciliation_errors.append(f"missing or empty required section: {heading}")
            elif not re.search(r"\[S\d{2,4}\]", section):
                reconciliation_errors.append(f"{heading} must cite at least one [S#] source")
        if reconciliation_errors:
            report_result = dict(report_result)
            report_result["valid"] = False
            report_result["errors"] = [*report_result.get("errors", []), *reconciliation_errors]
    citation_binding = citation_binding_audit(path, evidence_sources)
    if not citation_binding["valid"]:
        report_result = dict(report_result)
        report_result["valid"] = False
        report_result["errors"] = [*report_result.get("errors", []), *citation_binding["errors"]]
    return {
        "report": report_result,
        "financial": financial_result,
        "citation_binding": citation_binding,
        "valid": report_result["valid"] and financial_result["valid"] and citation_binding["valid"],
    }


def reconciliation_audit(root: Path, plan: dict[str, Any], case: dict[str, Any]) -> dict[str, Any] | None:
    contract = reconciliation_contract(plan)
    if contract is None:
        return None
    allowed_source_ids: set[str] = set()
    for item in case["operations"]:
        normalized = root / "evidence" / item["output"]
        if normalized.is_file() and not normalized.is_symlink():
            payload = normalized_payload(normalized)
            status, _error = operation_status(item, payload, 0 if payload.get("ok") is True else 1)
            if status == "passed":
                allowed_source_ids.add(item["id"])
    allowed_source_ids.update(item["id"] for item in file_sources(case) if item.get("status") == "imported")
    return financial_reconciliation.audit_file(
        root / contract["path"],
        expected_contract=contract,
        expected_identity={
            "security": plan["identity"]["security"],
            "security_id": plan["identity"]["security_id"],
            "as_of": plan["as_of"],
            "base_currency": plan["identity"]["base_currency"],
        },
        allowed_source_ids=allowed_source_ids,
    )


def receipt_status(
    root: Path, plan: dict[str, Any], plan_sha256: str, *, case: dict[str, Any], run_id: str, provider_gaps: list[str]
) -> tuple[bool, str | None]:
    path = root / "completion-receipt.json"
    if not path.is_file() or path.is_symlink():
        return False, None
    receipt = load_json(path)
    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("plan_sha256") != plan_sha256:
        return False, "completion receipt identity is invalid"
    required = {"schema", "valid", "run_id", "completed_at", "plan_sha256", "bindings", "provider_gaps", "automatic_trading"}
    if not required <= receipt.keys() or receipt.keys() - required - {"assessment"}:
        return False, "completion receipt fields are invalid"
    if receipt["valid"] is not True or receipt["automatic_trading"] is not False:
        return False, "completion receipt completion flags are invalid"
    if receipt["run_id"] != run_id or receipt["provider_gaps"] != provider_gaps:
        return False, "completion receipt run or provider gaps do not match workspace"
    try:
        completed_at = dt.datetime.fromisoformat(receipt["completed_at"].replace("Z", "+00:00"))
        if completed_at.utcoffset() is None:
            raise ValueError("completion timestamp requires timezone")
    except (AttributeError, TypeError, ValueError):
        return False, "completion receipt timestamp is invalid"
    # Historical v1 receipts omitted assessment; present assessments must retain
    # the same bounded claims as the current evidence state.
    if "assessment" in receipt and receipt["assessment"] != {
        "artifact_integrity": "VERIFIED",
        "receipt_integrity": "VERIFIED",
        "evidence_coverage": "PARTIAL" if provider_gaps else "COMPLETE",
        "citation_binding": "VERIFIED",
        "claim_support": "UNVERIFIED",
        "source_freshness": "UNVERIFIED",
    }:
        return False, "completion receipt assessment is invalid"
    bindings = receipt.get("bindings")
    if not isinstance(bindings, dict):
        return False, "completion receipt bindings are missing"
    if set(bindings) != receipt_bound_files(plan):
        return False, "completion receipt binding allowlist is invalid"
    for name, expected_hash in bindings.items():
        if not isinstance(name, str) or not isinstance(expected_hash, str):
            return False, "completion receipt binding is invalid"
        bound = root / name
        if not bound.is_file() or bound.is_symlink() or sha256_file(bound) != expected_hash:
            return False, f"completion receipt is stale: {name}"
    # The manifest binds evidence contents, not merely a list of path strings.
    manifest = load_json(root / "evidence-manifest.json")
    try:
        if manifest.get("schema") != MANIFEST_SCHEMA or not isinstance(manifest.get("sources"), list):
            return False, "completion manifest is invalid"
        for source in manifest["sources"]:
            for item in source["files"]:
                relative = Path(item["path"])
                if relative.is_absolute() or not relative.parts or relative.parts[0] != "evidence" or ".." in relative.parts:
                    return False, "completion manifest evidence path is invalid"
                bound = root / relative
                if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
                    return False, "completion manifest evidence path is invalid"
                if not bound.is_file() or sha256_file(bound) != item["sha256"]:
                    return False, f"completion receipt is stale: {relative.as_posix()}"
        expected_manifest = build_manifest(root, plan, case)
        if json.dumps(manifest, sort_keys=True, allow_nan=False) != json.dumps(expected_manifest, sort_keys=True, allow_nan=False):
            return False, "completion manifest does not match the current research evidence inventory"
    except (KeyError, TypeError, ValueError, RecursionError, ResearchRunError):
        return False, "completion manifest evidence binding is invalid"
    return True, None


def finalization_event_status(state: dict[str, Any], manifest_hash: str | None, gap_count: int, *, receipt_valid: bool) -> tuple[bool, str | None]:
    events = state["events"]
    finalized = [event for event in events if event.get("type") == "finalized"]
    if not finalized:
        return False, None
    if not receipt_valid:
        return False, "completion event requires an existing verified receipt"
    if len(finalized) != 1 or finalized[0] is not events[-1]:
        return False, "completion event must be unique and terminal"
    details = finalized[0].get("details")
    if (not isinstance(details, dict) or manifest_hash is None
            or details.get("manifest_sha256") != manifest_hash
            or type(details.get("provider_gap_count")) is not int
            or details["provider_gap_count"] != gap_count):
        return False, "completion event does not bind the current manifest and provider gaps"
    return True, None


@locked_workspace
def research_status(workspace: Path | str) -> dict[str, Any]:
    return _research_status_locked(workspace)


def _research_status_locked(workspace: Path | str, *, require_finalization_event: bool = True) -> dict[str, Any]:
    root, plan, case, state = load_workspace(workspace)
    provider_results, provider_pending, provider_gaps = inspect_provider(root, case)
    official_results, official_pending = inspect_official(root, case)
    public_results, _public_pending = inspect_official(root, case, "public_sources")
    provider_stage = "not_applicable" if not case["operations"] else "pending"
    if case["operations"] and len(provider_pending) < len(case["operations"]):
        provider_stage = "incomplete" if provider_pending else ("complete_with_gaps" if provider_gaps else "complete")
    provider_availability = plan.get("provider", {}).get("availability")
    if not case["operations"] and provider_availability not in {None, "available"}:
        adapter = plan.get("provider", {}).get("adapter", "fuyao")
        provider_gaps.append(f"provider:{adapter}:{provider_availability}")
    required_official_count = sum(1 for item in case["official_sources"] if item.get("required", True))
    official_stage = "pending" if len(official_pending) == required_official_count else (
        "incomplete" if official_pending else "complete"
    )
    evidence_sources = available_evidence_sources(root, case)
    report_checks = document_audits(
        root / "report.md", plan, "money-craft.report.v1", evidence_sources=evidence_sources
    )
    thesis_checks = document_audits(
        root / "thesis.md", plan, "money-craft.thesis.v1", evidence_sources=evidence_sources
    )
    reconciliation_checks = reconciliation_audit(root, plan, case)
    reconciliation_valid = reconciliation_checks is None or reconciliation_checks["valid"]
    report_stage = "complete" if report_checks["valid"] else "draft"
    thesis_stage = "complete" if thesis_checks["valid"] else "draft"
    plan_sha256 = sha256_file(root / "plan.json")
    receipt_valid, receipt_error = receipt_status(
        root, plan, plan_sha256, case=case, run_id=state["run_id"], provider_gaps=provider_gaps
    )
    manifest_exists = (root / "evidence-manifest.json").is_file()
    ready_for_report = not provider_pending and not official_pending
    citation_binding_valid = report_checks["citation_binding"]["valid"] and thesis_checks["citation_binding"]["valid"]
    if provider_pending or official_pending:
        evidence_coverage = "PENDING"
    elif provider_gaps:
        evidence_coverage = "PARTIAL"
    else:
        evidence_coverage = "COMPLETE"
    if receipt_valid:
        receipt_integrity = "VERIFIED"
        artifact_integrity = "VERIFIED"
    elif receipt_error and "stale" in receipt_error:
        receipt_integrity = "STALE"
        artifact_integrity = "STALE"
    elif receipt_error:
        receipt_integrity = "INVALID"
        artifact_integrity = "INVALID"
    else:
        receipt_integrity = "PENDING"
        artifact_integrity = "VERIFIED"
    assessment = {
        "artifact_integrity": artifact_integrity,
        "receipt_integrity": receipt_integrity,
        "evidence_coverage": evidence_coverage,
        "citation_binding": "VERIFIED" if citation_binding_valid else "INVALID",
        "claim_support": "UNVERIFIED",
        "source_freshness": "UNVERIFIED",
    }
    finalization_recorded, finalization_error = finalization_event_status(
        state, sha256_file(root / "evidence-manifest.json") if manifest_exists else None, len(provider_gaps), receipt_valid=receipt_valid
    )
    complete = (
        finalization_error is None
        and (finalization_recorded or not require_finalization_event)
        and receipt_valid
        and ready_for_report
        and report_checks["valid"]
        and thesis_checks["valid"]
        and reconciliation_valid
        and manifest_exists
        and citation_binding_valid
    )
    warnings = []
    if finalization_error:
        warnings.append(finalization_error)
    elif receipt_valid and not finalization_recorded:
        warnings.append("completion event is missing; retry finalize to verify artifacts and complete the event")
    if provider_gaps:
        warnings.append("provider gaps are declared evidence limitations and must be addressed in the report")
    if receipt_error:
        warnings.append(receipt_error)
    if reconciliation_checks is not None and not reconciliation_checks["valid"]:
        warnings.append("financial reconciliation is incomplete or invalid")
    if not citation_binding_valid:
        warnings.append("report or thesis citations are not bound to passed or imported research evidence")
    return {
        "schema": STATUS_SCHEMA,
        "valid": True,
        "run_id": state["run_id"],
        "identity": plan["identity"],
        "as_of": plan["as_of"],
        "plan_sha256": plan_sha256,
        "stages": {
            "finalization_event": "complete" if finalization_recorded else "pending",
            "plan": "complete",
            "provider_evidence": provider_stage,
            "official_evidence": official_stage,
            "report": report_stage,
            "thesis": thesis_stage,
            "financial_reconciliation": (
                "not-required-legacy"
                if reconciliation_checks is None
                else ("complete" if reconciliation_checks["valid"] else "draft")
            ),
            "audit": (
                "complete"
                if report_checks["valid"] and thesis_checks["valid"] and reconciliation_valid
                else "pending"
            ),
            "manifest": "complete" if manifest_exists else "pending",
            "receipt": "complete" if receipt_valid else "pending",
        },
        "missing_sources": [*provider_pending, *official_pending],
        "provider_gaps": provider_gaps,
        "provider_results": provider_results,
        "official_results": official_results,
        "public_results": public_results,
        "reconciliation": reconciliation_checks,
        "assessment": assessment,
        "ready_for_report": ready_for_report,
        "complete": complete,
        "network_used_by_status": False,
        "warnings": warnings,
    }


def provider_source(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    normalized = root / "evidence" / item["output"]
    payload = normalized_payload(normalized)
    status, _error = operation_status(item, payload, 0 if payload.get("ok") is True else 1)
    files = [
        {
            "role": "normalized-response" if payload.get("ok") is True else "normalized-error",
            "path": f"evidence/{item['output']}",
            "sha256": sha256_file(normalized),
        }
    ]
    if payload.get("ok") is True:
        raw = validate_provider_capture(root, item, payload)
        files.append(
            {
                "role": "raw-response" if item.get("provider", "fuyao") == "fuyao" else "adapter-export",
                "path": f"evidence/captures/{item['id']}/response.json",
                "sha256": sha256_file(raw),
            }
        )
        if payload.get("provider") in {"fuyao", "yfinance"}:
            files.append({"role": "sanitized-request", "path": f"evidence/captures/{item['id']}/request.json", "sha256": sha256_file(raw.parent / "request.json")})
        files.append({
            "role": "capture-metadata",
            "path": f"evidence/captures/{item['id']}/capture.json",
            "sha256": sha256_file(raw.parent / "capture.json"),
        })
    return {
        "id": item["id"],
        "kind": "provider-response",
        "title": item["title"],
        "provider": item.get("provider", "fuyao"),
        "operation": payload.get("operation"),
        "retrieved_at": payload.get("fetched_at"),
        "status": status,
        "distribution": "private-not-distributed",
        "files": files,
    }


def official_source(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    path = root / "evidence" / item["local_path"]
    role = "downloaded-document" if path.suffix.lower() == ".pdf" else "web-snapshot"
    return {
        "id": item["id"],
        "kind": item["kind"],
        "title": item["title"],
        "url": item["url"],
        "retrieved_on": item["retrieved_on"],
        **({"captured_at": item["captured_at"], "observed_at": item["observed_at"],
            "trust": item["trust"], "role": item["role"]} if item["kind"] == "public-material" else {}),
        "distribution": "private-not-distributed",
        "files": [{"role": role, "path": f"evidence/{item['local_path']}", "sha256": sha256_file(path)}],
    }


def build_manifest(root: Path, plan: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    sources = [provider_source(root, item) for item in case["operations"]]
    sources.extend(official_source(root, item) for item in file_sources(case) if item.get("status") == "imported")
    retrieved = [item.get("retrieved_at") for item in sources if isinstance(item.get("retrieved_at"), str)]
    identity = plan["identity"]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "case_id": identity["ticker"] if "thscode" in identity else identity["security_id"],
        "security": identity["security"],
        "security_id": identity["security_id"],
        "base_currency": identity["base_currency"],
        "as_of": plan["as_of"],
        "data_cutoff": max(retrieved) if retrieved else None,
        "distribution": {
            "mode": "metadata-only",
            "provider_payloads_distributed": False,
            "downloaded_documents_distributed": False,
            "note": "Only source metadata and SHA-256 bindings may be distributed. Evidence files remain local.",
        },
        "local_evidence": {"default_root": "evidence", "required_for_public_validation": False},
        "provider_documentation": case["provider_documentation"],
        "source_count": len(sources),
        "sources": sorted(sources, key=lambda item: int(item["id"][1:])),
    }
    if "thscode" in identity:
        manifest["thscode"] = identity["thscode"]
    return manifest


@locked_workspace
def finalize_workspace(workspace: Path | str) -> dict[str, Any]:
    root, plan, case, state = load_workspace(workspace)
    status = _research_status_locked(root, require_finalization_event=False)
    sealed = (root / "completion-receipt.json").exists()
    if sealed and not status["complete"]:
        raise ResearchRunError("finalized_workspace", "sealed research artifacts changed; preserve the receipt and create a new workspace")
    if status["missing_sources"]:
        raise ResearchRunError(
            "incomplete_evidence",
            "cannot finalize while required sources are missing: " + ", ".join(status["missing_sources"]),
        )
    finalization_recorded = status["stages"]["finalization_event"] == "complete"
    if any(event.get("type") == "finalized" for event in state["events"]) and not finalization_recorded:
        raise ResearchRunError("invalid_state", "existing completion event is inconsistent; preserve the workspace")
    if not finalization_recorded and len(state["events"]) >= MAX_STATE_EVENTS:
        raise ResearchRunError("state_limit", "run-state event limit reached")
    manifest = load_json(root / "evidence-manifest.json") if sealed else build_manifest(root, plan, case)
    if not sealed:
        atomic_json(root / "evidence-manifest.json", manifest)
    evidence_sources = available_evidence_sources(root, case)
    report_checks = document_audits(
        root / "report.md", plan, "money-craft.report.v1", evidence_sources=evidence_sources
    )
    thesis_checks = document_audits(
        root / "thesis.md", plan, "money-craft.thesis.v1", evidence_sources=evidence_sources
    )
    reconciliation_checks = reconciliation_audit(root, plan, case)
    reconciliation_valid = reconciliation_checks is None or reconciliation_checks["valid"]
    audit_payloads = {
        "report-audit.json": report_checks["report"],
        "report-financial-audit.json": report_checks["financial"],
        "thesis-audit.json": thesis_checks["report"],
        "thesis-financial-audit.json": thesis_checks["financial"],
    }
    contract = reconciliation_contract(plan)
    if contract is not None and reconciliation_checks is not None:
        audit_payloads[contract["audit_path"]] = reconciliation_checks
    if not sealed:
        for name, payload in audit_payloads.items():
            atomic_json(root / name, payload)
    citation_binding_valid = report_checks["citation_binding"]["valid"] and thesis_checks["citation_binding"]["valid"]
    valid = report_checks["valid"] and thesis_checks["valid"] and reconciliation_valid and citation_binding_valid
    receipt_path = root / "completion-receipt.json"
    receipt: dict[str, Any] | None = None
    if valid:
        bindings = {name: sha256_file(root / name) for name in sorted(receipt_bound_files(plan))}
        candidate = {
            "schema": RECEIPT_SCHEMA,
            "valid": True,
            "run_id": state["run_id"],
            "completed_at": utc_now(),
            "plan_sha256": sha256_file(root / "plan.json"),
            "bindings": bindings,
            "provider_gaps": status["provider_gaps"],
            "assessment": {
                **status["assessment"],
                "artifact_integrity": "VERIFIED",
                "receipt_integrity": "VERIFIED",
            },
            "automatic_trading": False,
        }
        if receipt_path.exists():
            receipt = load_json(receipt_path)
            comparable = {key: value for key, value in receipt.items() if key != "completed_at"}
            expected = {key: value for key, value in candidate.items() if key != "completed_at"}
            if "assessment" not in comparable:
                expected.pop("assessment")
            if comparable != expected:
                raise ResearchRunError("finalized_workspace", "completion receipt already binds different artifacts")
        else:
            atomic_json(receipt_path, candidate, replace=False)
            receipt = candidate
        if not finalization_recorded:
            record_event(
                root,
                state,
                "finalized",
                {
                    "manifest_sha256": bindings["evidence-manifest.json"],
                    "provider_gap_count": len(status["provider_gaps"]),
                },
            )
    return {
        "schema": FINALIZE_SCHEMA,
        "valid": valid,
        "run_id": state["run_id"],
        "evidence_manifest": {
            "path": "evidence-manifest.json",
            "sha256": sha256_file(root / "evidence-manifest.json"),
            "source_count": manifest["source_count"],
        },
        "audits": {
            "report": report_checks,
            "thesis": thesis_checks,
            "financial_reconciliation": reconciliation_checks,
        },
        "provider_gaps": status["provider_gaps"],
        "receipt": (
            {"path": "completion-receipt.json", "sha256": sha256_file(receipt_path)} if receipt is not None else None
        ),
        "automatic_trading": False,
    }
