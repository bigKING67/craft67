#!/usr/bin/env python3
"""Deterministic, offline company-thesis tracking workspace and revision workflow."""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import re
import shutil
import stat
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterator

import financial_rigor
from fsutil import sha256_file
import report_audit
import research_workflow

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback is covered by host smoke.
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # pragma: no cover - unavailable on POSIX.
    msvcrt = None  # type: ignore[assignment]


TRACKING_REVISION_RE = re.compile(r"^t\d{4}$")
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}")
WORKSPACE_FILES = {
    "previous-thesis.md",
    "thesis.md",
    "card.md",
    "state.json",
    "update-plan.json",
    "run-state.json",
}
REVISION_FILES = {
    "card.md",
    "state.json",
    "thesis.md",
    "thesis-audit.json",
    "thesis-diff.json",
    "thesis-financial-audit.json",
    "update-plan.json",
}


class TrackingError(RuntimeError):
    def __init__(self, kind: str, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.kind = kind
        self.exit_code = exit_code


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def file_record(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}


def read_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise TrackingError("missing_artifact", f"{label} is missing or is not a regular file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as exc:
        raise TrackingError("invalid_artifact", f"cannot read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise TrackingError("invalid_artifact", f"{label} must be a JSON object")
    return payload


def write_bytes_atomic(path: Path, value: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        try:
            directory_descriptor = os.open(path.parent, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_json_atomic(path: Path, payload: Any, *, mode: int = 0o600) -> None:
    write_bytes_atomic(path, json_bytes(payload), mode=mode)


def assert_no_symlink_components(path: Path) -> None:
    absolute = path.expanduser().absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        if current.exists() and current.is_symlink():
            raise TrackingError("unsafe_path", f"symlink path component is not allowed: {current}")


def resolve_path(path: Path, label: str) -> Path:
    expanded = path.expanduser().absolute()
    if expanded.exists() and expanded.is_symlink():
        raise TrackingError("unsafe_path", f"{label} must not be a symlink")
    resolved = expanded.resolve()
    assert_no_symlink_components(resolved)
    return resolved


def require_descendant(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise TrackingError("unsafe_path", f"{label} must be inside {root}") from exc


def validate_tracking_root(path: Path, *, create: bool) -> Path:
    root = resolve_path(path, "tracking root")
    if root.exists() and not root.is_dir():
        raise TrackingError("invalid_tracking_root", f"tracking root is not a directory: {root}")
    if not create and not root.is_dir():
        raise TrackingError("missing_tracking_root", f"tracking root does not exist: {root}")
    if create:
        root.mkdir(parents=True, exist_ok=True)
        (root / "revisions").mkdir(mode=0o700, exist_ok=True)
        (root / ".working").mkdir(mode=0o700, exist_ok=True)
    for child in (root / "revisions", root / ".working"):
        if child.exists() and (child.is_symlink() or not child.is_dir()):
            raise TrackingError("unsafe_path", f"tracking directory is unsafe: {child}")
    return root


@contextlib.contextmanager
def tracking_lock(root: Path) -> Iterator[None]:
    lock_path = root / ".tracking.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    with os.fdopen(descriptor, "a+b", closefd=True) as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:  # pragma: no cover - Windows-only fallback.
            handle.seek(0)
            handle.write(b"\0")
            handle.flush()
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:  # pragma: no cover - Windows-only fallback.
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def parse_current(root: Path) -> dict[str, Any]:
    current = read_json(root / "current.json", "tracking current pointer")
    if current.get("schema") not in {"money-craft.tracking-current.v1", "money-craft.tracking-current.v2"}:
        raise TrackingError("invalid_current", "current.json has an unsupported schema")
    revision_id = current.get("tracking_revision")
    relative = current.get("path")
    if not isinstance(revision_id, str) or not TRACKING_REVISION_RE.fullmatch(revision_id):
        raise TrackingError("invalid_current", "current.json has an invalid tracking revision")
    if relative != f"revisions/{revision_id}":
        raise TrackingError("invalid_current", "current.json path does not match tracking_revision")
    return current


def current_thesis(root: Path) -> Path:
    current = parse_current(root)
    thesis = root / str(current["path"]) / "thesis.md"
    require_descendant(thesis.resolve(), root, "current thesis")
    if thesis.is_symlink() or not thesis.is_file():
        raise TrackingError("missing_thesis", f"current thesis does not exist: {thesis}")
    return thesis


def source_binding(source_revision: Path | None, previous_sha256: str) -> dict[str, Any] | None:
    if source_revision is None:
        return None
    candidate = resolve_path(source_revision, "source revision")
    manifest_path = candidate / "REVISION.json" if candidate.is_dir() else candidate
    payload = read_json(manifest_path, "source revision manifest")
    if payload.get("schema") != "codex.investment-archive-revision.v1":
        raise TrackingError("invalid_source_revision", "source revision must use codex.investment-archive-revision.v1")
    research_id = payload.get("research_id")
    revision_id = payload.get("revision_id")
    if not isinstance(research_id, str) or not research_id or not isinstance(revision_id, str) or not revision_id:
        raise TrackingError("invalid_source_revision", "source revision identity is incomplete")
    return {
        "research_id": research_id,
        "revision_id": revision_id,
        "revision_manifest_sha256": sha256_file(manifest_path),
        "previous_thesis_sha256": previous_sha256,
    }


def inherited_source_binding(previous: Path, previous_sha256: str) -> dict[str, Any] | None:
    state_path = previous.parent / "state.json"
    if state_path.is_file() and not state_path.is_symlink():
        state = read_json(state_path, "previous tracking state")
        value = state.get("source_research")
        if isinstance(value, dict):
            result = dict(value)
            result["previous_thesis_sha256"] = previous_sha256
            return result
    return None


def health_contract(thesis: dict[str, Any], *, legacy: bool = False) -> dict[str, Any]:
    hypothesis_states = {record["ID"]: record["状态"] for record in thesis["hypotheses"]}
    red_line_states = {record["ID"]: record["当前状态"] for record in thesis["red_lines"]}
    if (not hypothesis_states or not red_line_states
            or any(value not in research_workflow.HYPOTHESIS_STATES for value in hypothesis_states.values())
            or any(value not in research_workflow.RED_LINE_STATES for value in red_line_states.values())):
        raise TrackingError("invalid_health_input", "health requires nonempty, recognized hypothesis and red-line states")
    unverified = "UNVERIFIED" in hypothesis_states.values() or "UNVERIFIED" in red_line_states.values()
    watch = "WATCH" in red_line_states.values()
    broken = sum(value == "BROKEN" for value in hypothesis_states.values())
    damaged = sum(value == "DAMAGED" for value in hypothesis_states.values())
    weakened = sum(value == "WEAKENED" for value in hypothesis_states.values())
    triggered = sum(value == "TRIGGERED" for value in red_line_states.values())
    score = max(1, min(10, 10 - broken * 3 - damaged * 2 - weakened - triggered * 5))
    if broken or triggered:
        status = "BROKEN"
    elif damaged:
        status = "DAMAGED"
    elif weakened:
        status = "WEAKENED"
    elif not legacy and unverified:
        status = "UNVERIFIED"
    elif not legacy and watch:
        status = "WATCH"
    else:
        status = "SUPPORTED"
    if not legacy and unverified:
        score = None
    terms: list[str] = []
    for count, label, penalty in (
        (broken, "broken hypotheses", 3),
        (damaged, "damaged hypotheses", 2),
        (weakened, "weakened hypotheses", 1),
        (triggered, "triggered red lines", 5),
    ):
        if count:
            terms.append(f"{count} {label} x {penalty}")
    return {
        "score": score,
        "maximum": 10,
        "status": status,
        "formula": "UNVERIFIED: incomplete hypothesis or red-line evidence" if score is None else "max(1, " + ("10" if not terms else "10 - " + " - ".join(terms)) + ")",
        "hypotheses": hypothesis_states,
        "red_lines": red_line_states,
    }


def initial_state(thesis: dict[str, Any], *, as_of: str, source_research: dict[str, Any] | None) -> dict[str, Any]:
    health = health_contract(thesis)
    state: dict[str, Any] = {
        "schema": "money-craft.tracking-state.v2",
        "security": thesis["metadata"]["security"],
        "security_id": thesis["metadata"]["security_id"],
        "as_of": as_of,
        "data_cutoff": thesis["metadata"]["data_cutoff"],
        "base_currency": thesis["metadata"]["base_currency"],
        "tracking_revision": "DRAFT",
        "health": {key: health[key] for key in ("score", "maximum", "status", "formula")},
        "hypotheses": health["hypotheses"],
        "red_lines": health["red_lines"],
        "next_mandatory_review": {
            "event": "{{NEXT_MANDATORY_REVIEW_EVENT}}",
            "required_workflow": "{{NEXT_REQUIRED_WORKFLOW}}",
        },
        "full_research_triggers": [
            "any red line becomes TRIGGERED",
            "any core hypothesis becomes BROKEN",
            "decision-critical source conflict changes the valuation or conclusion",
            "material acquisition, impairment, financing, governance, or capital-allocation event",
        ],
        "automatic_trading": False,
    }
    if source_research is not None:
        state["source_research"] = source_research
    return state


def validate_state(state: dict[str, Any], thesis: dict[str, Any], *, final_revision: str | None = None) -> dict[str, Any]:
    legacy = final_revision is not None and state.get("schema") == "money-craft.tracking-state.v1"
    if not legacy and state.get("schema") != "money-craft.tracking-state.v2":
        raise TrackingError("invalid_tracking_state", "state.json has an unsupported schema")
    metadata = thesis["metadata"]
    for key in ("security", "security_id", "as_of", "data_cutoff", "base_currency"):
        if state.get(key) != metadata.get(key):
            raise TrackingError("tracking_state_mismatch", f"state.json does not match thesis field: {key}")
    revision = state.get("tracking_revision")
    if final_revision is None:
        if revision != "DRAFT" and (not isinstance(revision, str) or not TRACKING_REVISION_RE.fullmatch(revision)):
            raise TrackingError("invalid_tracking_state", "state tracking_revision must be DRAFT or tNNNN")
    elif revision != final_revision:
        raise TrackingError("tracking_state_mismatch", "state tracking_revision does not match revision directory")
    if state.get("automatic_trading") is not False:
        raise TrackingError("unsafe_tracking_state", "automatic_trading must be false")
    expected = health_contract(thesis, legacy=legacy)
    if state.get("hypotheses") != expected["hypotheses"]:
        raise TrackingError("tracking_state_mismatch", "state hypothesis map does not match thesis")
    if state.get("red_lines") != expected["red_lines"]:
        raise TrackingError("tracking_state_mismatch", "state red-line map does not match thesis")
    health = state.get("health")
    if not isinstance(health, dict):
        raise TrackingError("invalid_tracking_state", "state health must be an object")
    for key in ("score", "maximum", "status"):
        if health.get(key) != expected[key]:
            raise TrackingError("tracking_state_mismatch", f"state health does not match thesis: {key}")
    if not isinstance(health.get("formula"), str) or not health["formula"].strip():
        raise TrackingError("invalid_tracking_state", "state health formula is required")
    if not legacy:
        review = state.get("next_mandatory_review", {})
        if not isinstance(review, dict):
            raise TrackingError("invalid_review_due_date", "next_mandatory_review must be an object")
        due_date = review.get("due_date")
        if due_date is not None:
            try:
                if not isinstance(due_date, str) or dt.date.fromisoformat(due_date).isoformat() != due_date:
                    raise ValueError("not an ISO date")
                if due_date < metadata["as_of"]:
                    raise ValueError("review due date precedes thesis as_of")
            except (ValueError, TypeError) as exc:
                raise TrackingError("invalid_review_due_date", "review due_date must be YYYY-MM-DD on or after thesis as_of") from exc
    if PLACEHOLDER_RE.search(json.dumps(state, ensure_ascii=False)):
        raise TrackingError("unresolved_placeholder", "state.json contains unresolved placeholders")
    return expected


def render_card(template: str, thesis: dict[str, Any], as_of: str) -> str:
    replacements = {
        "{{SECURITY}}": thesis["metadata"]["security"],
        "{{SECURITY_ID}}": thesis["metadata"]["security_id"],
        "{{AS_OF}}": as_of,
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template


def allocate_workspace(root: Path) -> tuple[Path, str]:
    run_id = f"track-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    return root / ".working" / run_id, run_id


def remove_mutable_tree(path: Path) -> None:
    # Permissions live on the inode: a hard-linked file may also be a sealed revision elsewhere.
    # POSIX unlink only needs a writable directory; Windows needs writable files to delete them.
    for item in path.rglob("*"):
        if item.is_symlink():
            continue
        if item.is_dir():
            os.chmod(item, 0o700)
        elif os.name == "nt" or item.stat().st_nlink == 1:
            os.chmod(item, 0o600)
    os.chmod(path, 0o700)
    shutil.rmtree(path)


def initialize_tracking(
    tracking_root: Path,
    *,
    as_of: str,
    template_root: Path,
    previous: Path | None = None,
    source_revision: Path | None = None,
    workspace: Path | None = None,
) -> dict[str, Any]:
    root = validate_tracking_root(tracking_root, create=True)
    with tracking_lock(root):
        previous_path = resolve_path(previous, "previous thesis") if previous is not None else current_thesis(root)
        try:
            previous_snapshot = research_workflow.load_thesis(previous_path)
            plan = research_workflow.prepare_thesis_update(previous_path, as_of=as_of)
        except research_workflow.WorkflowError as exc:
            raise TrackingError(exc.kind, str(exc), exit_code=exc.exit_code) from exc
        previous_sha256 = previous_snapshot["sha256"]
        binding = source_binding(source_revision, previous_sha256)
        if binding is None:
            binding = inherited_source_binding(previous_path, previous_sha256)

        if workspace is None:
            workspace_path, run_id = allocate_workspace(root)
        else:
            workspace_path = resolve_path(workspace, "tracking workspace")
            working_root = (root / ".working").resolve()
            require_descendant(workspace_path, working_root, "tracking workspace")
            if workspace_path.parent != working_root:
                raise TrackingError("unsafe_path", "tracking workspace must be a direct child of .working")
            run_id = workspace_path.name
        if workspace_path.exists():
            raise TrackingError("workspace_exists", f"tracking workspace already exists: {workspace_path}")
        card_template = template_root / "tracking-card.md"
        if card_template.is_symlink() or not card_template.is_file():
            raise TrackingError("missing_template", f"tracking card template is missing: {card_template}")

        workspace_path.mkdir(mode=0o700)
        try:
            thesis_bytes = previous_path.read_bytes()
            write_bytes_atomic(workspace_path / "previous-thesis.md", thesis_bytes, mode=0o400)
            write_bytes_atomic(workspace_path / "thesis.md", thesis_bytes, mode=0o600)
            write_json_atomic(workspace_path / "update-plan.json", plan, mode=0o400)
            state = initial_state(previous_snapshot, as_of=as_of, source_research=binding)
            write_json_atomic(workspace_path / "state.json", state, mode=0o600)
            card = render_card(card_template.read_text(encoding="utf-8"), previous_snapshot, as_of)
            write_bytes_atomic(workspace_path / "card.md", card.encode("utf-8"), mode=0o600)
            run_state = {
                "schema": "money-craft.tracking-run-state.v1",
                "run_id": run_id,
                "tracking_root": str(root),
                "workspace": str(workspace_path),
                "as_of": as_of,
                "created_at": utc_now(),
                "previous": {
                    "path": str(previous_path),
                    "workspace_copy": "previous-thesis.md",
                    "sha256": previous_sha256,
                },
                "update_plan_sha256": sha256_file(workspace_path / "update-plan.json"),
                "source_research": binding,
                "execution_boundary": {
                    "network_used": False,
                    "account_access": False,
                    "automatic_trading": False,
                },
            }
            write_json_atomic(workspace_path / "run-state.json", run_state, mode=0o400)
        except Exception:
            remove_mutable_tree(workspace_path)
            raise
    return {
        "schema": "money-craft.tracking-init.v1",
        "valid": True,
        "workspace": str(workspace_path),
        "run_id": run_id,
        "tracking_root": str(root),
        "previous": run_state["previous"],
        "editable_files": ["thesis.md", "card.md", "state.json"],
        "immutable_files": ["previous-thesis.md", "update-plan.json", "run-state.json"],
        "execution_boundary": run_state["execution_boundary"],
    }


def load_workspace(workspace: Path) -> tuple[Path, Path, dict[str, Any]]:
    workspace_path = resolve_path(workspace, "tracking workspace")
    if not workspace_path.is_dir():
        raise TrackingError("missing_workspace", f"tracking workspace does not exist: {workspace_path}")
    run_state = read_json(workspace_path / "run-state.json", "tracking run state")
    if run_state.get("schema") != "money-craft.tracking-run-state.v1":
        raise TrackingError("invalid_workspace", "run-state.json has an unsupported schema")
    if run_state.get("run_id") != workspace_path.name:
        raise TrackingError("invalid_workspace", "run-state run_id must match the workspace name")
    created_at = run_state.get("created_at")
    try:
        if not isinstance(created_at, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}[Tt](?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)", created_at
        ):
            raise ValueError("invalid timestamp")
        dt.datetime.fromisoformat(created_at.upper().replace("Z", "+00:00"))
    except ValueError as exc:
        raise TrackingError("invalid_workspace", "run-state created_at must be a valid timestamp with timezone") from exc
    previous = run_state.get("previous")
    if (not isinstance(previous, dict) or not isinstance(previous.get("path"), str)
            or not previous["path"] or previous.get("workspace_copy") != "previous-thesis.md"
            or not isinstance(previous.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", previous["sha256"])
            or not isinstance(run_state.get("update_plan_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", run_state["update_plan_sha256"])):
        raise TrackingError("invalid_workspace", "run-state previous thesis or update plan binding is invalid")
    boundary = run_state.get("execution_boundary")
    if not isinstance(boundary, dict) or any(boundary.get(key) is not False for key in
            ("network_used", "account_access", "automatic_trading")):
        raise TrackingError("invalid_workspace", "run-state execution boundary is invalid")
    if run_state.get("source_research") is not None and not isinstance(run_state["source_research"], dict):
        raise TrackingError("invalid_workspace", "run-state source_research must be an object or null")
    if run_state.get("workspace") != str(workspace_path):
        raise TrackingError("workspace_mismatch", "run-state workspace binding does not match")
    root_value = run_state.get("tracking_root")
    if not isinstance(root_value, str):
        raise TrackingError("invalid_workspace", "run-state tracking_root is missing")
    root = validate_tracking_root(Path(root_value), create=False)
    working_root = (root / ".working").resolve()
    require_descendant(workspace_path, working_root, "tracking workspace")
    if workspace_path.parent != working_root:
        raise TrackingError("unsafe_path", "tracking workspace must be a direct child of .working")
    missing = [name for name in sorted(WORKSPACE_FILES) if not (workspace_path / name).is_file()]
    if missing:
        raise TrackingError("incomplete_workspace", "tracking workspace is missing: " + ", ".join(missing))
    return workspace_path, root, run_state


def next_revision_id(root: Path) -> str:
    revisions = [
        path.name
        for path in (root / "revisions").iterdir()
        if path.is_dir() and not path.is_symlink() and TRACKING_REVISION_RE.fullmatch(path.name)
    ]
    number = max((int(value[1:]) for value in revisions), default=0) + 1
    if number > 9999:
        raise TrackingError("revision_exhausted", "tracking revision namespace is exhausted")
    return f"t{number:04d}"


def validate_workspace_inputs(
    workspace: Path, run_state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], str]:
    previous = workspace / "previous-thesis.md"
    plan_path = workspace / "update-plan.json"
    expected_previous = run_state.get("previous", {})
    if not isinstance(expected_previous, dict) or sha256_file(previous) != expected_previous.get("sha256"):
        raise TrackingError("immutable_artifact_changed", "previous-thesis.md no longer matches run-state")
    if sha256_file(plan_path) != run_state.get("update_plan_sha256"):
        raise TrackingError("immutable_artifact_changed", "update-plan.json no longer matches run-state")
    plan = read_json(plan_path, "thesis update plan")
    try:
        expected_plan = research_workflow.prepare_thesis_update(previous, as_of=str(run_state.get("as_of", "")))
    except research_workflow.WorkflowError as exc:
        raise TrackingError(exc.kind, str(exc), exit_code=exc.exit_code) from exc
    original_path = expected_previous.get("path")
    if not isinstance(original_path, str):
        raise TrackingError("invalid_workspace", "run-state previous thesis path is missing")
    expected_plan["previous"]["filename"] = Path(original_path).name
    if plan != expected_plan:
        raise TrackingError("immutable_artifact_changed", "update-plan.json is not derived from the bound previous thesis")

    thesis_path = workspace / "thesis.md"
    try:
        thesis = research_workflow.load_thesis(thesis_path)
        diff = research_workflow.thesis_diff(previous, thesis_path)
    except research_workflow.WorkflowError as exc:
        raise TrackingError(exc.kind, str(exc), exit_code=exc.exit_code) from exc
    if thesis["metadata"]["as_of"] != run_state.get("as_of"):
        raise TrackingError("target_date_mismatch", "candidate thesis as_of does not match the tracking run target")
    report_result = report_audit.audit_file(thesis_path)
    financial_result = financial_rigor.audit_file(thesis_path)
    if not report_result["valid"]:
        raise TrackingError("report_audit_failed", "; ".join(report_result["errors"]))
    if not financial_result["valid"]:
        raise TrackingError("financial_audit_failed", "; ".join(financial_result["errors"]))

    card_path = workspace / "card.md"
    try:
        card = card_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise TrackingError("invalid_card", f"cannot read tracking card: {exc}") from exc
    if not card.strip() or PLACEHOLDER_RE.search(card):
        raise TrackingError("unresolved_placeholder", "card.md is empty or contains unresolved placeholders")
    state = read_json(workspace / "state.json", "tracking state")
    health = validate_state(state, thesis)
    return thesis, diff, report_result, financial_result, state, card


def make_tracking_manifest(
    revision: str,
    run_state: dict[str, Any],
    thesis: dict[str, Any],
    diff: dict[str, Any],
    state: dict[str, Any],
    financial_result: dict[str, Any],
    records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    health = health_contract(thesis)
    provider_captures = state.get("provider_captures")
    source_ids = sorted(provider_captures) if isinstance(provider_captures, dict) else []
    manifest: dict[str, Any] = {
        "schema": "money-craft.tracking-revision.v2",
        "security": thesis["metadata"]["security"],
        "security_id": thesis["metadata"]["security_id"],
        "tracking_revision": revision,
        "as_of": thesis["metadata"]["as_of"],
        "data_cutoff": thesis["metadata"]["data_cutoff"],
        "run_id": run_state["run_id"],
        "source_research": state.get("source_research"),
        "result": {
            "health_score": health["score"],
            "health_status": health["status"],
            "diff_signal": diff["signal"],
            "automatic_trading": False,
        },
        "audits": {
            "report_valid": True,
            "financial_valid": True,
            "financial_check_count": len(financial_result["checks"]),
            "diff_valid": diff.get("valid") is True,
        },
        "provider": {
            "network_checked": bool(source_ids),
            "captures_private": True,
            "source_ids": source_ids,
        },
        "files": records,
    }
    if manifest["source_research"] is None:
        del manifest["source_research"]
    return manifest


def make_checksums(stage: Path) -> bytes:
    names = ["TRACKING.json", *sorted(REVISION_FILES)]
    return "".join(f"{sha256_file(stage / name)}  {name}\n" for name in names).encode("utf-8")


def set_tree_read_only(root: Path, *, root_read_only: bool = True) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_symlink():
            raise TrackingError("unsafe_path", f"revision contains a symlink: {path}")
        os.chmod(path, 0o444 if path.is_file() else 0o555)
    os.chmod(root, 0o555 if root_read_only else 0o700)


def remove_owned_revision(path: Path) -> None:
    if not TRACKING_REVISION_RE.fullmatch(path.name) or path.is_symlink():
        raise TrackingError("unsafe_cleanup", f"refusing to remove unsafe revision path: {path}")
    remove_mutable_tree(path)


def remove_staging_directory(path: Path) -> None:
    if not path.name.startswith(".t") or ".staging." not in path.name or path.is_symlink():
        raise TrackingError("unsafe_cleanup", f"refusing to remove unsafe staging path: {path}")
    remove_mutable_tree(path)


def finalize_tracking(workspace: Path) -> dict[str, Any]:
    workspace_path, root, run_state = load_workspace(workspace)
    with tracking_lock(root):
        has_history = (root / "current.json").exists() or any(
            TRACKING_REVISION_RE.fullmatch(path.name) for path in (root / "revisions").iterdir()
        )
        if has_history and not _verify_tracking_locked(root)["valid"]:
            raise TrackingError(
                "invalid_history",
                "existing tracking history is invalid; preserve files and inspect track verify before recovery",
            )
        thesis, diff, report_result, financial_result, state, card = validate_workspace_inputs(
            workspace_path, run_state
        )
        if (root / "current.json").exists():
            latest = current_thesis(root)
            if sha256_file(latest) != run_state["previous"]["sha256"]:
                raise TrackingError("stale_previous", "current thesis changed; preserve this workspace and initialize a new update from current")
        revision = next_revision_id(root)
        destination = root / "revisions" / revision
        stage = root / "revisions" / f".{revision}.staging.{uuid.uuid4().hex}"
        if destination.exists() or stage.exists():
            raise TrackingError("revision_exists", f"tracking revision already exists: {destination}")
        stage.mkdir(mode=0o700)
        published = False
        pointer_update_started = False
        try:
            state = dict(state)
            state["tracking_revision"] = revision
            validate_state(state, thesis, final_revision=revision)
            outputs: dict[str, bytes] = {
                "card.md": card.encode("utf-8"),
                "state.json": json_bytes(state),
                "thesis.md": (workspace_path / "thesis.md").read_bytes(),
                "thesis-audit.json": json_bytes(report_result),
                "thesis-diff.json": json_bytes(diff),
                "thesis-financial-audit.json": json_bytes(financial_result),
                "update-plan.json": (workspace_path / "update-plan.json").read_bytes(),
            }
            for name, value in outputs.items():
                (stage / name).write_bytes(value)
                os.chmod(stage / name, 0o600)
            records = {name: file_record(stage / name) for name in sorted(REVISION_FILES)}
            manifest = make_tracking_manifest(
                revision, run_state, thesis, diff, state, financial_result, records
            )
            (stage / "TRACKING.json").write_bytes(json_bytes(manifest))
            (stage / "SHA256SUMS").write_bytes(make_checksums(stage))
            os.chmod(stage / "TRACKING.json", 0o600)
            os.chmod(stage / "SHA256SUMS", 0o600)
            set_tree_read_only(stage, root_read_only=False)
            os.replace(stage, destination)
            published = True
            os.chmod(destination, 0o555)
            current = {
                "schema": "money-craft.tracking-current.v2",
                "security": thesis["metadata"]["security"],
                "security_id": thesis["metadata"]["security_id"],
                "tracking_revision": revision,
                "path": f"revisions/{revision}",
                "as_of": thesis["metadata"]["as_of"],
                "data_cutoff": thesis["metadata"]["data_cutoff"],
                "tracking_manifest_sha256": sha256_file(destination / "TRACKING.json"),
                "checksums_sha256": sha256_file(destination / "SHA256SUMS"),
                "thesis_sha256": sha256_file(destination / "thesis.md"),
                "health_score": health_contract(thesis)["score"],
                "health_status": health_contract(thesis)["status"],
                "diff_signal": diff["signal"],
                "automatic_trading": False,
            }
            pointer_update_started = True
            write_json_atomic(root / "current.json", current, mode=0o600)
        except Exception:
            if stage.exists():
                remove_staging_directory(stage)
            preserve_revision = False
            if published and pointer_update_started:
                try:
                    # A directory fsync can fail after atomic pointer replacement.
                    # Never remove a revision that current may already reference.
                    pointer_bytes = (root / "current.json").read_bytes()
                    preserve_revision = json.loads(pointer_bytes).get("tracking_revision") == revision
                except FileNotFoundError:
                    pass
                except (OSError, ValueError, AttributeError):
                    preserve_revision = True
            if published and destination.exists() and not preserve_revision:
                remove_owned_revision(destination)
            raise

        if workspace_path.parent == (root / ".working").resolve() and workspace_path.name == run_state["run_id"]:
            remove_mutable_tree(workspace_path)
    return {
        "schema": "money-craft.tracking-revision.v2",
        "valid": True,
        "tracking_root": str(root),
        "tracking_revision": revision,
        "revision_path": str(destination),
        "current_path": str(root / "current.json"),
        "health_score": current["health_score"],
        "health_status": current["health_status"],
        "diff_signal": current["diff_signal"],
        "automatic_trading": False,
        "network_used": False,
    }


def parse_checksums(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise TrackingError("invalid_checksums", f"cannot read SHA256SUMS: {exc}") from exc
    checksums: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if not match or match.group(2) in checksums:
            raise TrackingError("invalid_checksums", f"invalid SHA256SUMS line: {line}")
        checksums[match.group(2)] = match.group(1)
    return checksums


def is_read_only(path: Path) -> bool:
    return stat.S_IMODE(path.stat().st_mode) & 0o222 == 0


def verify_revision(path: Path, *, require_read_only: bool) -> dict[str, Any]:
    revision = path.name
    errors: list[str] = []
    warnings: list[str] = []
    if path.is_symlink() or not path.is_dir() or not TRACKING_REVISION_RE.fullmatch(revision):
        return {"tracking_revision": revision, "valid": False, "errors": ["unsafe revision path"], "warnings": []}
    for item in [path, *path.rglob("*")]:
        if item.is_symlink():
            errors.append(f"symlink is not allowed: {item.relative_to(path)}")
        elif require_read_only and not is_read_only(item):
            errors.append(f"revision artifact is writable: {item.relative_to(path) if item != path else '.'}")
    try:
        manifest = read_json(path / "TRACKING.json", "tracking revision manifest")
        state = read_json(path / "state.json", "tracking state")
        diff = read_json(path / "thesis-diff.json", "thesis diff")
        plan = read_json(path / "update-plan.json", "thesis update plan")
        stored_report = read_json(path / "thesis-audit.json", "thesis report audit")
        stored_financial = read_json(path / "thesis-financial-audit.json", "thesis financial audit")
        if manifest.get("schema") not in {"money-craft.tracking-revision.v1", "money-craft.tracking-revision.v2"}:
            errors.append("TRACKING.json has an unsupported schema")
        if manifest.get("schema", "").rsplit(".", 1)[-1] != state.get("schema", "").rsplit(".", 1)[-1]:
            errors.append("manifest and state health contract versions differ")
        if state.get("schema") == "money-craft.tracking-state.v1":
            warnings.append("legacy health scoring is archival only; use status assessment for current interpretation")
        if manifest.get("tracking_revision") != revision:
            errors.append("TRACKING.json revision does not match directory")
        if manifest.get("result", {}).get("automatic_trading") is not False:
            errors.append("TRACKING.json automatic_trading must be false")
        records = manifest.get("files")
        if not isinstance(records, dict) or set(records) != REVISION_FILES:
            errors.append("TRACKING.json file inventory is incomplete")
        else:
            for name, record in records.items():
                artifact = path / name
                if not artifact.is_file() or artifact.is_symlink():
                    errors.append(f"missing regular artifact: {name}")
                elif record != file_record(artifact):
                    errors.append(f"file record mismatch: {name}")
        checksums = parse_checksums(path / "SHA256SUMS")
        expected_checksum_names = {"TRACKING.json", *REVISION_FILES}
        if set(checksums) != expected_checksum_names:
            errors.append("SHA256SUMS inventory is incomplete")
        for name, expected in checksums.items():
            artifact = path / name
            if not artifact.is_file() or sha256_file(artifact) != expected:
                errors.append(f"checksum mismatch: {name}")

        thesis_path = path / "thesis.md"
        try:
            thesis = research_workflow.load_thesis(thesis_path)
            expected_health = validate_state(state, thesis, final_revision=revision)
        except (research_workflow.WorkflowError, TrackingError) as exc:
            errors.append(str(exc))
            thesis = None
            expected_health = None
        report_result = report_audit.audit_file(thesis_path)
        financial_result = financial_rigor.audit_file(thesis_path)
        if stored_report != report_result or not report_result["valid"]:
            errors.append("stored report audit does not match thesis")
        if stored_financial != financial_result or not financial_result["valid"]:
            errors.append("stored financial audit does not match thesis")
        if diff.get("schema") != "money-craft.thesis-diff.v1" or diff.get("valid") is not True:
            errors.append("thesis diff is invalid")
        if plan.get("schema") != "money-craft.thesis-update-plan.v1":
            errors.append("thesis update plan is invalid")
        if diff.get("previous", {}).get("sha256") != plan.get("previous", {}).get("sha256"):
            errors.append("diff previous thesis does not match update plan")
        if thesis is not None:
            identity = {key: thesis["metadata"][key] for key in ("security", "security_id", "base_currency")}
            if diff.get("identity") != identity:
                errors.append("diff identity does not match thesis")
            if diff.get("current", {}).get("sha256") != thesis["sha256"]:
                errors.append("diff current thesis hash does not match thesis")
            for key in ("security", "security_id", "as_of", "data_cutoff"):
                if manifest.get(key) != thesis["metadata"].get(key):
                    errors.append(f"manifest does not match thesis field: {key}")
            result = manifest.get("result", {})
            if expected_health is not None:
                for key in ("score", "status"):
                    if result.get("health_" + key) != expected_health[key]:
                        errors.append(f"manifest health {key} does not match thesis")
            if result.get("diff_signal") != diff.get("signal"):
                errors.append("manifest diff signal does not match thesis diff")
        if not isinstance((path / "card.md").read_text(encoding="utf-8"), str) or PLACEHOLDER_RE.search(
            (path / "card.md").read_text(encoding="utf-8")
        ):
            errors.append("card contains unresolved placeholders")
    except (TrackingError, OSError, UnicodeDecodeError, TypeError, AttributeError) as exc:
        errors.append(str(exc))
    return {
        "tracking_revision": revision,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def verify_tracking(tracking_root: Path, *, require_read_only: bool = True) -> dict[str, Any]:
    root = validate_tracking_root(tracking_root, create=False)
    with tracking_lock(root):
        return _verify_tracking_locked(root, require_read_only=require_read_only)


def _verify_tracking_locked(root: Path, *, require_read_only: bool = True) -> dict[str, Any]:
    """Read one snapshot while the caller holds the tracking lock."""
    errors: list[str] = []
    warnings: list[str] = []
    revision_root = root / "revisions"
    revisions = sorted(
        path for path in revision_root.iterdir() if path.is_dir() and TRACKING_REVISION_RE.fullmatch(path.name)
    ) if revision_root.is_dir() else []
    if not revisions:
        errors.append("no tracking revisions found")
    if [path.name for path in revisions] != [f"t{index:04d}" for index in range(1, len(revisions) + 1)]:
        errors.append("tracking revisions are not contiguous from t0001")
    results = [verify_revision(path, require_read_only=require_read_only) for path in revisions]
    for result in results:
        errors.extend(f"{result['tracking_revision']}: {message}" for message in result["errors"])
        warnings.extend(f"{result['tracking_revision']}: {message}" for message in result["warnings"])
    for previous, revision in zip(revisions, revisions[1:]):
        try:
            diff = read_json(revision / "thesis-diff.json", "thesis diff")
            if diff.get("previous", {}).get("sha256") != sha256_file(previous / "thesis.md"):
                errors.append(f"{revision.name}: previous thesis does not match preceding revision {previous.name}")
        except (TrackingError, OSError, TypeError, AttributeError) as exc:
            errors.append(f"{revision.name}: cannot verify previous thesis link: {exc}")
    current: dict[str, Any] | None = None
    try:
        current = parse_current(root)
        if revisions and current["tracking_revision"] != revisions[-1].name:
            errors.append("current.json does not point to the latest tracking revision")
        current_revision = root / current["path"]
        if not current_revision.is_dir():
            errors.append("current.json points to a missing revision")
        else:
            expected = {
                "tracking_manifest_sha256": sha256_file(current_revision / "TRACKING.json"),
                "checksums_sha256": sha256_file(current_revision / "SHA256SUMS"),
                "thesis_sha256": sha256_file(current_revision / "thesis.md"),
            }
            for key, value in expected.items():
                if current.get(key) != value:
                    errors.append(f"current.json hash mismatch: {key}")
            manifest = read_json(current_revision / "TRACKING.json", "current tracking manifest")
            for key in ("security", "security_id", "as_of", "data_cutoff"):
                if current.get(key) != manifest.get(key):
                    errors.append(f"current.json does not match manifest field: {key}")
            if current.get("schema", "").rsplit(".", 1)[-1] != manifest.get("schema", "").rsplit(".", 1)[-1]:
                errors.append("current and manifest health contract versions differ")
            if current.get("schema") == "money-craft.tracking-current.v2" and current.get("health_status") != manifest.get("result", {}).get("health_status"):
                errors.append("current.json health status does not match manifest")
            if current.get("health_score") != manifest.get("result", {}).get("health_score"):
                errors.append("current.json health score does not match manifest")
            if current.get("diff_signal") != manifest.get("result", {}).get("diff_signal"):
                errors.append("current.json diff signal does not match manifest")
            if current.get("automatic_trading") is not False:
                errors.append("current.json automatic_trading must be false")
    except (TrackingError, OSError, ValueError, TypeError, AttributeError) as exc:
        errors.append(str(exc))
    working_root = root / ".working"
    workspaces = sorted(path.name for path in working_root.iterdir() if path.is_dir()) if working_root.is_dir() else []
    if workspaces:
        warnings.append(f"unfinished tracking workspaces: {len(workspaces)}")
    return {
        "schema": "money-craft.tracking-verify.v1",
        "valid": not errors,
        "tracking_root": str(root),
        "require_read_only": require_read_only,
        "current": current,
        "revision_count": len(revisions),
        "revisions": results,
        "working_count": len(workspaces),
        "warnings": warnings,
        "errors": errors,
        "network_used": False,
    }


def tracking_status(tracking_root: Path, *, today: dt.date | None = None) -> dict[str, Any]:
    root = validate_tracking_root(tracking_root, create=False)
    with tracking_lock(root):
        return _tracking_status_locked(root, today=today)


def _tracking_status_locked(root: Path, *, today: dt.date | None = None) -> dict[str, Any]:
    revision_root = root / "revisions"
    revisions = sorted(
        path.name
        for path in revision_root.iterdir()
        if path.is_dir() and not path.is_symlink() and TRACKING_REVISION_RE.fullmatch(path.name)
    ) if revision_root.is_dir() else []
    working_root = root / ".working"
    workspaces = sorted(
        path.name for path in working_root.iterdir() if path.is_dir() and not path.is_symlink()
    ) if working_root.is_dir() else []
    current = None
    verification = _verify_tracking_locked(root) if revisions or (root / "current.json").exists() else None
    if verification:
        current = verification["current"]
    assessment: dict[str, Any] = {
        "integrity": "VERIFIED" if verification and verification["valid"] else "INVALID" if verification else "UNVERIFIED",
        "freshness": "UNKNOWN", "status": "UNVERIFIED", "score": None,
        "assessed_on": (today or dt.datetime.now(dt.timezone.utc).date()).isoformat(),
        "reason": "no verified revision available", "evidence_scope": "recorded thesis states; not independent source verification",
    }
    if verification and verification["valid"] and current:
        revision_path = root / current["path"]
        thesis = research_workflow.load_thesis(revision_path / "thesis.md")
        state = read_json(revision_path / "state.json", "current tracking state")
        health = health_contract(thesis)
        review = state.get("next_mandatory_review")
        due = review.get("due_date") if isinstance(review, dict) else None
        # v1 allowed arbitrary review metadata. Do not reinterpret it as a valid deadline.
        try:
            if not isinstance(due, str) or dt.date.fromisoformat(due).isoformat() != due or due < thesis["metadata"]["as_of"]:
                due = None
        except ValueError:
            due = None
        date = assessment["assessed_on"]
        freshness = "NOT_YET_VALID" if thesis["metadata"]["as_of"] > date else "UNKNOWN" if due is None else "STALE" if date > due else "WITHIN_REVIEW_WINDOW"
        assessment.update(freshness=freshness, status=health["status"], score=health["score"],
                          reason="recorded hypothesis and red-line assessment", review_due_date=due)
        if freshness != "WITHIN_REVIEW_WINDOW":
            assessment.update(score=None, reason="review window missing, not yet valid or expired; recorded judgment is not current evidence")
            if assessment["status"] == "SUPPORTED":
                assessment["status"] = "UNVERIFIED"
    return {
        "schema": "money-craft.tracking-status.v2",
        "valid": verification["valid"] if verification else True,
        "assessment": assessment,
        "current_semantics": "archival pointer; use assessment for current interpretation",
        "errors": verification["errors"] if verification else [],
        "tracking_root": str(root),
        "current": current,
        "revision_count": len(revisions),
        "revisions": revisions,
        "working_count": len(workspaces),
        "workspaces": workspaces,
        "automatic_trading": False,
        "network_used": False,
    }
