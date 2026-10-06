"""Video Harness stage gates over a digest-bound ``production.json``.

The gates are code, not prompt guidance: every completion re-reads bound
artifacts, rejects digest drift, and records the outcome and reason.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from creative_craft_contracts import (
    TEMPLATES_DIR,
    VIDEO_STAGES,
    edit_document_duration_frames,
    edit_document_generated_share,
    edit_document_item_frames,
    load_json,
    nonempty,
    sha256_file,
    validate_data,
    write_atomic,
)
from creative_craft_project import _safe_relative_path

PRODUCTION_FILE = "production.json"
DONE = {"completed", "skipped"}
STAGE_KINDS = {
    "brief": {"brief", "note"},
    "reference": {"reference", "note"},
    "plan": {"production-plan", "note"},
    "select": {"production-plan", "note"},
    "generate": {"video-job", "execution-receipt", "production-plan", "media", "note"},
    "assemble": {"edit-document", "note"},
    "inspect": {"render-qa", "note"},
    "revise": {"edit-document", "note"},
    "export": {"edit-document", "render-qa", "media", "note"},
}
CONTRACT_KINDS = {
    "production-plan": "production-plan",
    "video-job": "video",
    "execution-receipt": "execution-receipt",
    "edit-document": "edit-document",
    "render-qa": "render-qa",
}
ALWAYS_REQUIRED = {"assemble", "inspect", "revise", "export"}
RECEIPT_OK = {"succeeded", "partial"}
REVISION_OPEN = {"in_progress", "blocked"}
# Gate outcomes that let a stage finish; inspect reports "accepted".
PASSING = {"completed", "accepted"}
ROUNDS_CEILING = 20  # video-production schema maximum for max_revision_rounds


class VideoError(ValueError):
    """A refused production operation; the message is user-facing."""


@dataclass
class Gate:
    ok: bool = True
    reasons: list[str] = field(default_factory=list)
    outcome: str = "completed"
    info: dict[str, Any] = field(default_factory=dict)

    def block(self, reason: str) -> None:
        self.ok = False
        self.reasons.append(reason)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _root(value: str) -> Path:
    root = Path(value).expanduser().absolute()
    if root.is_symlink():
        raise VideoError(f"production root must not be a symlink: {root}")
    return root.resolve()


def load_production(root: Path) -> dict[str, Any]:
    path = root / PRODUCTION_FILE
    if path.is_symlink():
        raise VideoError(f"{PRODUCTION_FILE} must not be a symlink")
    data = load_json(path)
    _, result = validate_data(data, "video-production")
    if not result.ok:
        raise VideoError(f"invalid {PRODUCTION_FILE}: " + "; ".join(result.errors))
    return data


def save_production(root: Path, data: dict[str, Any]) -> None:
    _, result = validate_data(data, "video-production")
    if not result.ok:
        raise VideoError(
            "refusing to write invalid production: " + "; ".join(result.errors)
        )
    write_atomic(
        root / PRODUCTION_FILE, json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )


def _event(data: dict[str, Any], stage: str, action: str, detail: str) -> None:
    data["events"].append(
        {"at": _now(), "stage": stage, "action": action, "detail": detail}
    )


def _stage(data: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in data["stages"]:
        if stage["id"] == stage_id:
            return stage
    raise VideoError(f"unknown stage: {stage_id}")


def _artifacts(
    data: dict[str, Any], stages: tuple[str, ...], kind: str
) -> list[dict[str, Any]]:
    return [
        artifact
        for stage in data["stages"]
        if stage["id"] in stages
        for artifact in stage["artifacts"]
        if artifact["kind"] == kind
    ]


def _latest(
    data: dict[str, Any], stages: tuple[str, ...], kind: str
) -> dict[str, Any] | None:
    found = _artifacts(data, stages, kind)
    return found[-1] if found else None


def _safe_file(root: Path, value: str) -> Path:
    path, error = _safe_relative_path(root, value, label="artifact path")
    if error or path is None:
        raise VideoError(error or "artifact path is invalid")
    if not path.is_file():
        raise VideoError(f"artifact file does not exist: {value}")
    return path


def _read_contract(root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    """Load a bound JSON artifact and re-validate it against its contract."""
    data = load_json(_safe_file(root, artifact["path"]))
    expected = CONTRACT_KINDS.get(artifact["kind"])
    if expected:
        _, result = validate_data(data, expected)
        if not result.ok:
            raise VideoError(f"{artifact['path']}: " + "; ".join(result.errors))
    return data


def drift_report(root: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Compare the latest binding of every path with the file on disk."""
    latest: dict[str, tuple[str, dict[str, Any]]] = {}
    for stage in data["stages"]:
        for artifact in stage["artifacts"]:
            latest[artifact["path"]] = (stage["id"], artifact)
    drift: list[dict[str, Any]] = []
    for path_text, (stage_id, artifact) in latest.items():
        path, error = _safe_relative_path(root, path_text, label="artifact path")
        actual = None
        if error or path is None:
            state = "unsafe"
        elif not path.is_file():
            state = "missing"
        else:
            actual = sha256_file(path)
            state = "ok" if actual == artifact["sha256"] else "modified"
        if state != "ok":
            drift.append(
                {
                    "path": path_text,
                    "stage": stage_id,
                    "kind": artifact["kind"],
                    "state": state,
                    "bound_sha256": artifact["sha256"],
                    "actual_sha256": actual,
                }
            )
    return drift


def _plan(root: Path, data: dict[str, Any], gate: Gate) -> dict[str, Any] | None:
    if data["plan"] is None:
        return None
    try:
        return _read_contract(
            root, {"kind": "production-plan", "path": data["plan"]["path"]}
        )
    except (ValueError, OSError) as exc:
        gate.block(f"production plan unreadable: {exc}")
        return None


def _qa_outcome(qa: dict[str, Any]) -> str:
    accepted = qa["verdict"] != "fail" and qa["review"]["decision"] == "accept"
    return "accepted" if accepted else "revise"


def evaluate_promises(
    plan: dict[str, Any] | None, doc: dict[str, Any]
) -> list[dict[str, Any]]:
    """Compute machine-checkable delivery promises against one edit revision."""
    results: list[dict[str, Any]] = []
    fps = doc["canvas"]["fps"]
    for promise in (plan or {}).get("delivery_promises", []):
        check = promise["check"]
        kind = check["kind"]
        entry: dict[str, Any] = {"id": promise["id"], "kind": kind}
        if kind == "duration_range":
            seconds = edit_document_duration_frames(doc) / fps
            entry.update(
                observed=round(seconds, 3),
                passed=check["min"] <= seconds <= check["max"],
            )
        elif kind == "captions_present":
            frames = edit_document_item_frames(doc)
            count = sum(
                1
                for item in doc["items"]
                if item["kind"] == "caption" and item["id"] in frames
            )
            entry.update(observed=count, passed=count > 0)
        elif kind == "max_generated_share":
            share = edit_document_generated_share(doc)
            entry.update(observed=round(share, 4), passed=share <= check["max"] + 1e-9)
        else:
            entry.update(observed=None, passed=None)
        results.append(entry)
    return results


def _gate_generate(
    root: Path, data: dict[str, Any], plan: dict[str, Any] | None, gate: Gate
) -> None:
    beats = [
        beat
        for beat in (plan or {}).get("beats", [])
        if beat["source_kind"] == "generate"
    ]
    gate.info["generate_beats"] = [beat["id"] for beat in beats]
    bound = {
        artifact["path"]: artifact for artifact in _stage(data, "generate")["artifacts"]
    }
    for beat in beats:
        ref = beat["generation_ref"]
        if ref is None or ref["receipt_path"] is None:
            gate.block(
                f"generate beat {beat['id']} needs generation_ref with job and receipt"
            )
            continue
        job_art = bound.get(ref["job_path"])
        receipt_art = bound.get(ref["receipt_path"])
        if job_art is None or job_art["kind"] != "video-job":
            gate.block(
                f"beat {beat['id']} job {ref['job_path']} is not bound as video-job"
            )
            continue
        if receipt_art is None or receipt_art["kind"] != "execution-receipt":
            gate.block(
                f"beat {beat['id']} receipt {ref['receipt_path']} is not bound as execution-receipt"
            )
            continue
        try:
            job = _read_contract(root, job_art)
            receipt = _read_contract(root, receipt_art)
        except (ValueError, OSError) as exc:
            gate.block(f"beat {beat['id']}: {exc}")
            continue
        if (
            receipt["job_id"] != job["job_id"]
            or receipt["job_sha256"] != job_art["sha256"]
        ):
            gate.block(
                f"beat {beat['id']} receipt is not bound to job {ref['job_path']}"
            )
        if receipt["outcome"] not in RECEIPT_OK:
            gate.block(f"beat {beat['id']} receipt outcome is {receipt['outcome']}")


def _gate_inspect(root: Path, data: dict[str, Any], gate: Gate) -> None:
    edit = _latest(data, ("assemble", "revise"), "edit-document")
    qa_art = _latest(data, ("inspect",), "render-qa")
    if edit is None:
        gate.block("no edit-document revision is bound")
        return
    if qa_art is None:
        gate.block("record a render-qa for the current revision")
        return
    try:
        doc = _read_contract(root, edit)
        qa = _read_contract(root, qa_art)
    except (ValueError, OSError) as exc:
        gate.block(str(exc))
        return
    if (
        qa["revision_sha256"] != edit["sha256"]
        or qa["revision"] != doc["revision"]
        or qa["project_id"] != doc["project_id"]
    ):
        gate.block(
            f"render-qa {qa_art['path']} is not bound to current revision {doc['revision']} "
            f"({edit['path']})"
        )
        return
    if qa["review"]["status"] != "done":
        gate.block("render-qa review is pending; review composited samples first")
        return
    gate.outcome = _qa_outcome(qa)
    gate.info.update(
        verdict=qa["verdict"],
        decision=qa["review"]["decision"],
        revision=doc["revision"],
    )
    if gate.outcome == "revise":
        rounds = data["revision_rounds"]
        limit = data["policy"]["max_revision_rounds"]
        gate.info["revision_round_available"] = rounds < limit


def _gate_revise(root: Path, data: dict[str, Any], gate: Gate) -> None:
    if _stage(data, "revise")["status"] not in REVISION_OPEN:
        gate.block("no revision was requested by inspection")
        return
    limit = data["policy"]["max_revision_rounds"]
    if data["revision_rounds"] >= limit:
        gate.block(f"revision round limit {limit} reached; needs a human decision")
        return
    edit = _latest(data, ("assemble", "revise"), "edit-document")
    qa_art = _latest(data, ("inspect",), "render-qa")
    if (
        edit is None
        or qa_art is None
        or edit not in _stage(data, "revise")["artifacts"]
    ):
        gate.block("record the revised edit-document in the revise stage")
        return
    try:
        doc = _read_contract(root, edit)
        qa = _read_contract(root, qa_art)
    except (ValueError, OSError) as exc:
        gate.block(str(exc))
        return
    if doc["revision"] <= qa["revision"]:
        gate.block(
            f"revision {doc['revision']} is not newer than inspected revision {qa['revision']}"
        )


def _gate_export(
    root: Path, data: dict[str, Any], plan: dict[str, Any] | None, gate: Gate
) -> None:
    edit = _latest(data, ("export",), "edit-document")
    if edit is None:
        gate.block("record the exported edit-document revision in the export stage")
        return
    accepted = None
    for qa_art in reversed(_artifacts(data, ("inspect",), "render-qa")):
        try:
            qa = _read_contract(root, qa_art)
        except (ValueError, OSError):
            continue
        if qa["review"]["status"] == "done" and _qa_outcome(qa) == "accepted":
            accepted = qa
            break
    if accepted is None:
        gate.block("no inspection passed with an accept review")
        return
    # reviewer_kind inside render-qa is agent-written; the policy needs a named,
    # separately recorded sign-off. A completed inspect stage is immutable, so its
    # approval belongs to the accepted inspection found above.
    if data["policy"].get("export_requires_human_review") and (
        _stage(data, "inspect")["approval"] is None
    ):
        gate.block(
            "policy.export_requires_human_review: the accepted inspection "
            f"(revision {accepted['revision']}) has no named sign-off; run "
            "video-approve --stage inspect --by <name>"
        )
        return
    if accepted["revision_sha256"] != edit["sha256"]:
        gate.block(
            f"exported revision {edit['path']} differs from the last accepted inspection "
            f"(revision {accepted['revision']})"
        )
        return
    media = _latest(data, ("export",), "media")
    export_qa_art = _latest(data, ("export",), "render-qa")
    if media is None or export_qa_art is None:
        gate.block("record the delivered media file and its export render-qa in the export stage")
        return
    try:
        doc = _read_contract(root, edit)
        export_qa = _read_contract(root, export_qa_art)
    except (ValueError, OSError) as exc:
        gate.block(str(exc))
        return
    if export_qa["render"]["kind"] != "export":
        gate.block("export render-qa must inspect an export render, not a preview")
    if export_qa["revision_sha256"] != edit["sha256"]:
        gate.block("export render-qa was produced for a different revision")
    if export_qa["render"]["sha256"] != media["sha256"]:
        gate.block(f"delivered file {media['path']} is not the render inspected by export render-qa")
    if export_qa["verdict"] == "fail":
        gate.block("export render-qa verdict is fail")
    if gate.reasons:
        return
    promises = evaluate_promises(plan, doc)
    gate.info["delivery_promises"] = promises
    for promise in promises:
        if promise["passed"] is False:
            gate.block(
                f"delivery promise {promise['id']} failed: observed {promise['observed']}"
            )


_PLAN_TOP_LEVEL = ("intended_use", "output", "delivery_promises", "brief_ref")
_BEAT_FIELDS = (
    "role",
    "purpose",
    "duration_seconds",
    "source_kind",
    "requirement",
    "hard_constraints",
    "locked",
)


def plan_structure_changes(
    approved: dict[str, Any], current: dict[str, Any]
) -> list[str]:
    """Differences a later stage made to the approved plan's structure.

    Filling selections and generation references is the job of select/generate,
    and a tbd beat may resolve to a concrete source kind. Everything else, plus
    the selection of a beat that was locked with one, is structural.
    """
    changes = [
        f"{key} changed"
        for key in _PLAN_TOP_LEVEL
        if approved.get(key) != current.get(key)
    ]
    before = {beat["id"]: beat for beat in approved["beats"]}
    after = {beat["id"]: beat for beat in current["beats"]}
    if list(before) != list(after):
        changes.append(
            f"beats changed from {list(before)} to {list(after)} (added, removed or reordered)"
        )
    for beat_id in before.keys() & after.keys():
        old, new = before[beat_id], after[beat_id]
        for key in _BEAT_FIELDS:
            if key == "source_kind" and old[key] == "tbd":
                continue
            if old.get(key) != new.get(key):
                changes.append(f"beat {beat_id} {key} changed")
        if old.get("locked") and old.get("selection") and old["selection"] != new.get(
            "selection"
        ):
            changes.append(f"locked beat {beat_id} selection changed")
    return sorted(changes)


PLAN_CHANGE_NOTE = "plan structure changed since it was last accepted"


def _accepted_plan(data: dict[str, Any]) -> dict[str, Any] | None:
    """Latest plan bound by a completed stage: approved, or accepted unchanged."""
    accepted = None
    for stage_id in ("plan", "select", "generate"):
        stage = _stage(data, stage_id)
        if stage["status"] != "completed":
            continue
        for artifact in stage["artifacts"]:
            if artifact["kind"] == "production-plan":
                accepted = artifact
    return accepted


def _check_plan_changes(root: Path, data: dict[str, Any], gate: Gate) -> None:
    approved_art = _accepted_plan(data)
    if approved_art is None or data["plan"] is None:
        return
    if data["plan"]["sha256"] == approved_art["sha256"]:
        return
    try:
        approved = _read_contract(root, approved_art)
        current = _read_contract(
            root, {"kind": "production-plan", "path": data["plan"]["path"]}
        )
    except (ValueError, OSError) as exc:
        gate.block(f"cannot compare with the approved plan: {exc}")
        return
    changes = plan_structure_changes(approved, current)
    if changes:
        gate.info["plan_changes"] = changes
        gate.info["approval_reason"] = PLAN_CHANGE_NOTE


def evaluate_gate(
    root: Path,
    data: dict[str, Any],
    stage_id: str,
    drift: list[dict[str, Any]] | None = None,
) -> Gate:
    """Evaluate a stage gate without mutating the production."""
    gate = Gate()
    for item in drift_report(root, data) if drift is None else drift:
        gate.block(f"artifact drift: {item['path']} is {item['state']}")
    for prior in VIDEO_STAGES[: VIDEO_STAGES.index(stage_id)]:
        if _stage(data, prior)["status"] not in DONE and not (
            stage_id == "revise" and prior == "inspect"
        ):
            gate.block(f"preceding stage {prior} is not completed or skipped")
    stage = _stage(data, stage_id)
    plan = _plan(root, data, gate)
    if stage_id in {"select", "generate"}:
        _check_plan_changes(root, data, gate)
    if stage_id in {"brief", "reference"}:
        if not stage["artifacts"]:
            gate.block(f"record at least one {stage_id} artifact or skip the stage")
    elif stage_id == "plan":
        bound = _latest(data, ("plan",), "production-plan")
        if bound is None:
            gate.block("record a production-plan in the plan stage")
        elif plan is not None and plan.get("brief_ref"):
            ref = plan["brief_ref"]
            try:
                matches = sha256_file(_safe_file(root, ref["path"])) == ref["sha256"]
            except ValueError as exc:
                gate.block(f"brief_ref: {exc}")
            else:
                if not matches:
                    gate.block(f"brief_ref digest differs from {ref['path']}")
    elif stage_id == "select":
        if plan is None:
            gate.block("select needs a production plan")
        else:
            candidates = []
            for beat in plan["beats"]:
                if beat["source_kind"] == "tbd":
                    gate.block(f"beat {beat['id']} source is still tbd")
                elif beat["source_kind"] == "footage":
                    if beat["selection"] is None:
                        gate.block(
                            f"footage beat {beat['id']} has no selected source range"
                        )
                    elif beat["selection"]["status"] == "candidate":
                        candidates.append(beat["id"])
            gate.info["candidates"] = candidates
    elif stage_id == "generate":
        _gate_generate(root, data, plan, gate)
    elif stage_id == "assemble":
        edit = _latest(data, ("assemble",), "edit-document")
        if edit is None:
            gate.block("record an edit-document revision in the assemble stage")
        else:
            try:
                _read_contract(root, edit)
            except (ValueError, OSError) as exc:
                gate.block(str(exc))
    elif stage_id == "inspect":
        _gate_inspect(root, data, gate)
    elif stage_id == "revise":
        _gate_revise(root, data, gate)
    elif stage_id == "export":
        _gate_export(root, data, plan, gate)
    if not gate.ok:
        gate.outcome = "blocked"
    elif (
        gate.outcome in PASSING
        and (
            stage_id in data["policy"]["approval_required"]
            or "approval_reason" in gate.info
            or (
                stage_id == "inspect"
                and data["policy"].get("export_requires_human_review", False)
            )
        )
        and stage["approval"] is None
    ):
        gate.outcome = "awaiting_approval"
    return gate


def _finish_stage(data: dict[str, Any], stage_id: str, note: str) -> None:
    stage = _stage(data, stage_id)
    stage["status"] = "completed"
    stage["note"] = note
    if stage_id == "inspect":
        revise = _stage(data, "revise")
        if revise["status"] not in DONE:
            rounds = data["revision_rounds"]
            revise["status"] = "completed" if rounds else "skipped"
            revise["note"] = (
                f"inspection accepted after {rounds} revision round(s)"
                if rounds
                else "inspection accepted; no revision round needed"
            )
            _event(data, "revise", "close", revise["note"])
    elif stage_id == "revise":
        data["revision_rounds"] += 1
        inspect = _stage(data, "inspect")
        inspect.update(
            status="pending", approval=None, note="re-inspect the revised edit"
        )
        _event(
            data,
            "inspect",
            "reopen",
            f"revision round {data['revision_rounds']} completed",
        )


MAX_ROUNDS_PER_EXTENSION = 3


def extend_revision_rounds(
    data: dict[str, Any], by: str, reason: str, rounds: int
) -> str:
    """Human decision to continue after the revision-round limit blocked revise."""
    revise = _stage(data, "revise")
    limit = data["policy"]["max_revision_rounds"]
    if revise["status"] != "blocked" or data["revision_rounds"] < limit:
        raise VideoError("revise is not blocked by the revision-round limit")
    if not nonempty(by) or not nonempty(reason):
        raise VideoError("--by and --reason are required to extend revision rounds")
    if not 1 <= rounds <= MAX_ROUNDS_PER_EXTENSION:
        raise VideoError(f"--rounds must be 1-{MAX_ROUNDS_PER_EXTENSION}")
    new_limit = limit + rounds
    if new_limit > ROUNDS_CEILING:
        raise VideoError(f"revision rounds cannot exceed {ROUNDS_CEILING}")
    data["policy"]["max_revision_rounds"] = new_limit
    note = f"round limit {limit} -> {new_limit} by {by.strip()}: {reason.strip()}"
    revise.update(status="in_progress", approval=None, note=note)
    _event(data, "revise", "extend-rounds", note)
    return note


def complete_stage(root: Path, data: dict[str, Any], stage_id: str) -> Gate:
    stage = _stage(data, stage_id)
    if stage["status"] in DONE:
        raise VideoError(f"stage {stage_id} is already {stage['status']}")
    gate = evaluate_gate(root, data, stage_id)
    if gate.outcome == "blocked":
        stage["status"] = "blocked"
        stage["note"] = "; ".join(gate.reasons)
    elif gate.outcome == "revise":
        stage.update(status="in_progress", approval=None)
        revise = _stage(data, "revise")
        if gate.info.get("revision_round_available"):
            stage["note"] = (
                f"revision requested ({gate.info['verdict']}, {gate.info['decision']})"
            )
            revise.update(status="in_progress", approval=None, note=stage["note"])
        else:
            limit = data["policy"]["max_revision_rounds"]
            stage["note"] = f"revision requested but round limit {limit} is reached"
            revise.update(
                status="blocked", note=stage["note"] + "; needs a human decision"
            )
            gate.outcome = "blocked"
            gate.reasons.append(stage["note"])
    elif gate.outcome == "awaiting_approval":
        stage["status"] = "awaiting_approval"
        stage["note"] = (
            f"{PLAN_CHANGE_NOTE}: " + "; ".join(gate.info["plan_changes"])
            if "plan_changes" in gate.info
            else "gate passed; awaiting approval"
        )
    else:
        _finish_stage(data, stage_id, "gate passed")
    _event(
        data,
        stage_id,
        "complete",
        f"{gate.outcome}: " + ("; ".join(gate.reasons) or "ok"),
    )
    return gate


def approve_stage(
    root: Path, data: dict[str, Any], stage_id: str, by: str, note: str
) -> None:
    stage = _stage(data, stage_id)
    if stage["status"] != "awaiting_approval":
        status = stage["status"]
        hint = {
            "in_progress": f"; run video-complete --stage {stage_id} first (recording an "
            "artifact reopens a stage that was awaiting approval)",
            "pending": f"; record its artifacts (video-record --stage {stage_id}) "
            f"and run video-complete --stage {stage_id} first",
            "blocked": "; resolve its blockers first (video-status lists them; a "
            "revision-round limit needs video-extend-rounds or a plan change), then "
            f"run video-complete --stage {stage_id}",
        }.get(status, "")
        raise VideoError(
            f"stage {stage_id} is {stage['status']}, not awaiting_approval{hint}"
        )
    if not nonempty(by):
        raise VideoError("--by must name the approver")
    stage["approval"] = {"by": by, "at": _now(), "note": note}
    gate = evaluate_gate(root, data, stage_id)
    if gate.outcome not in PASSING:
        stage["approval"] = None
        raise VideoError(
            "gate no longer passes: " + "; ".join(gate.reasons or [gate.outcome])
        )
    _finish_stage(data, stage_id, f"approved by {by}")
    _event(
        data, stage_id, "approve", f"approved by {by}" + (f": {note}" if note else "")
    )


def skip_stage(root: Path, data: dict[str, Any], stage_id: str, reason: str) -> None:
    stage = _stage(data, stage_id)
    if not nonempty(reason):
        raise VideoError("--reason is required to skip a stage")
    if stage["status"] in DONE:
        raise VideoError(f"stage {stage_id} is already {stage['status']}")
    if stage_id in ALWAYS_REQUIRED:
        raise VideoError(f"stage {stage_id} cannot be skipped")
    gate = Gate()
    for item in drift_report(root, data):
        gate.block(f"artifact drift: {item['path']} is {item['state']}")
    for prior in VIDEO_STAGES[: VIDEO_STAGES.index(stage_id)]:
        if _stage(data, prior)["status"] not in DONE:
            gate.block(f"preceding stage {prior} is not completed or skipped")
    plan = _plan(root, data, gate)
    if stage_id in {"select", "generate"}:
        _check_plan_changes(root, data, gate)
        if "plan_changes" in gate.info:
            gate.block(
                f"{PLAN_CHANGE_NOTE} ({'; '.join(gate.info['plan_changes'])}); "
                "complete the stage for approval instead of skipping"
            )
    if gate.reasons:
        raise VideoError("cannot skip: " + "; ".join(gate.reasons))
    if stage_id in {"select", "generate"} and plan is None:
        raise VideoError(f"cannot skip {stage_id} before a production plan is bound")
    kinds = {beat["source_kind"] for beat in (plan or {}).get("beats", [])}
    if stage_id == "generate" and "generate" in kinds:
        raise VideoError(
            "plan has generate beats; change the plan and record it before skipping"
        )
    if stage_id == "select" and kinds & {"footage", "tbd"}:
        raise VideoError("plan has footage or tbd beats; select cannot be skipped")
    stage.update(status="skipped", note=reason.strip())
    _event(data, stage_id, "skip", reason.strip())


def record_artifact(
    root: Path, data: dict[str, Any], stage_id: str, kind: str, value: str
) -> dict[str, Any]:
    stage = _stage(data, stage_id)
    if stage["status"] in DONE:
        raise VideoError(
            f"stage {stage_id} is {stage['status']}; bound evidence is immutable"
        )
    if stage_id == "revise" and stage["status"] not in REVISION_OPEN:
        raise VideoError("no revision round is open; inspection has not requested one")
    if kind not in STAGE_KINDS[stage_id]:
        raise VideoError(
            f"stage {stage_id} accepts kinds: "
            + ", ".join(sorted(STAGE_KINDS[stage_id]))
        )
    path = _safe_file(root, value)
    relative = path.relative_to(root).as_posix()
    if relative == PRODUCTION_FILE:
        raise VideoError(f"{PRODUCTION_FILE} cannot be recorded as an artifact")
    artifact = {"kind": kind, "path": relative, "sha256": sha256_file(path)}
    contract = CONTRACT_KINDS.get(kind)
    if kind == "brief" and path.suffix == ".json":
        contract = "brief"
    if contract:
        _, result = validate_data(load_json(path), contract)
        if not result.ok:
            raise VideoError(
                f"{relative} is not a valid {contract}: " + "; ".join(result.errors)
            )
    if kind == "edit-document" and stage_id in {"assemble", "revise"}:
        revision = load_json(path)["revision"]
        current = data["current_revision"]
        if current is not None and revision <= current:
            raise VideoError(
                f"revision {revision} is not newer than current revision {current}"
            )
        data["current_revision"] = revision
    # Compare with the latest binding of this path in each completed stage; an
    # earlier draft rebound before completion is superseded, not evidence.
    for done in data["stages"]:
        if done["status"] != "completed":
            continue
        latest = None
        for bound in done["artifacts"]:
            if bound["path"] == relative:
                latest = bound
        if latest is not None and latest["sha256"] != artifact["sha256"]:
            raise VideoError(
                f"{relative} is bound by completed stage {done['id']} and must "
                "stay unchanged; write changes to a new file"
            )
    if kind == "production-plan":
        data["plan"] = {"path": relative, "sha256": artifact["sha256"]}
    stage["artifacts"].append(artifact)
    if stage["status"] in {"pending", "blocked", "awaiting_approval"}:
        stage.update(status="in_progress", approval=None)
    _event(data, stage_id, "record", f"{kind} {relative} {artifact['sha256'][:12]}")
    return artifact


def _budget(data: dict[str, Any]) -> dict[str, Any]:
    reserved = sum(e["estimate"] for e in data["ledger"] if e["status"] == "reserved")
    settled = sum(e["actual"] for e in data["ledger"] if e["status"] == "settled")
    budget = data["policy"]["budget"]
    return {
        **budget,
        "reserved": reserved,
        "settled": settled,
        "committed": reserved + settled,
    }


def ledger_action(data: dict[str, Any], args: argparse.Namespace) -> str:
    entries = {entry["id"]: entry for entry in data["ledger"]}
    if args.action == "reserve":
        if args.id in entries:
            raise VideoError(f"ledger id {args.id} already exists")
        missing = [
            name
            for name in ("stage", "description", "estimate")
            if getattr(args, name) is None
        ]
        if missing:
            raise VideoError("reserve requires --" + ", --".join(missing))
        unknown = [
            e["id"]
            for e in data["ledger"]
            if e["stage"] == args.stage
            and e["status"] == "reserved"
            and e["provider_job_id"]
        ]
        if unknown:
            raise VideoError(
                f"submitted job(s) {', '.join(unknown)} have no settled outcome; settle or "
                "release them after checking the provider before reserving a retry"
            )
        budget = _budget(data)
        projected = budget["committed"] + args.estimate
        warning = ""
        if budget["cap"] is not None and projected > budget["cap"]:
            if budget["mode"] == "cap":
                raise VideoError(
                    f"reservation would commit {projected:g} over cap {budget['cap']:g}"
                )
            if budget["mode"] == "warn":
                warning = f"; over cap {budget['cap']:g}"
        data["ledger"].append(
            {
                "id": args.id,
                "stage": args.stage,
                "description": args.description,
                "estimate": args.estimate,
                "actual": None,
                "status": "reserved",
                "provider_job_id": args.provider_job_id,
            }
        )
        detail = f"reserve {args.id} {args.estimate:g} {budget['currency']}{warning}"
        _event(data, args.stage, "ledger", detail)
        return detail
    entry = entries.get(args.id)
    if entry is None:
        raise VideoError(f"unknown ledger id {args.id}")
    if entry["status"] != "reserved":
        raise VideoError(f"ledger {args.id} is already {entry['status']}")
    if args.action == "settle":
        if args.actual is None:
            raise VideoError("settle requires --actual")
        entry.update(status="settled", actual=args.actual)
        if args.provider_job_id:
            entry["provider_job_id"] = args.provider_job_id
        detail = f"settle {args.id} {args.actual:g}"
    else:
        entry["status"] = "released"
        detail = f"release {args.id}"
    _event(data, entry["stage"], "ledger", detail)
    return detail


def production_status(root: Path, data: dict[str, Any]) -> dict[str, Any]:
    drift = drift_report(root, data)
    stages = []
    for stage in data["stages"]:
        entry = {
            "id": stage["id"],
            "status": stage["status"],
            "note": stage["note"],
            "artifacts": len(stage["artifacts"]),
            "approval": stage["approval"],
        }
        if stage["status"] not in DONE:
            gate = evaluate_gate(root, data, stage["id"], drift)
            entry["gate"] = {
                "outcome": gate.outcome,
                "reasons": gate.reasons,
                **gate.info,
            }
        stages.append(entry)
    pending = [stage for stage in data["stages"] if stage["status"] not in DONE]
    current = pending[0]["id"] if pending else None
    if current == "inspect" and _stage(data, "revise")["status"] in REVISION_OPEN:
        current = "revise"
    if current is None:
        next_action = "all stages completed or skipped"
    else:
        status = _stage(data, current)["status"]
        gate = next(stage["gate"] for stage in stages if stage["id"] == current)
        if status == "awaiting_approval":
            next_action = f"video-approve --stage {current} --by <approver>"
        elif current == "revise" and status == "blocked" and (
            data["revision_rounds"] >= data["policy"]["max_revision_rounds"]
        ):
            next_action = (
                "human decision: accept the current cut, change the plan, or "
                "video-extend-rounds --by <name> --reason <why>"
            )
        elif gate["outcome"] == "blocked":
            next_action = f"resolve {current}: " + "; ".join(gate["reasons"])
        else:
            next_action = f"video-complete --stage {current}"
    candidates: list[str] = []
    promises: list[dict[str, Any]] = []
    gate = Gate()
    plan = _plan(root, data, gate)
    if plan:
        candidates = [
            beat["id"]
            for beat in plan["beats"]
            if beat["selection"] and beat["selection"]["status"] == "candidate"
        ]
    edit = _latest(data, ("assemble", "revise"), "edit-document")
    if edit:
        try:
            promises = evaluate_promises(plan, _read_contract(root, edit))
        except (ValueError, OSError):
            promises = []
    return {
        "production_id": data["production_id"],
        "current_stage": current,
        "next_action": next_action,
        "revision_rounds": data["revision_rounds"],
        "max_revision_rounds": data["policy"]["max_revision_rounds"],
        "current_revision": data["current_revision"],
        "drift": drift,
        "candidates": candidates,
        "delivery_promises_on_current_revision": promises,
        "budget": _budget(data),
        "stages": stages,
    }


# --- CLI adapters -----------------------------------------------------------


def _run(args: argparse.Namespace, action: Any) -> int:
    try:
        root = _root(args.root)
        data = load_production(root)
        code, message = action(root, data)
        save_production(root, data)
    except (VideoError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(message)
    return code


def cmd_video_init(args: argparse.Namespace) -> int:
    try:
        root = _root(args.root)
        root.mkdir(parents=True, exist_ok=True)
        if (root / PRODUCTION_FILE).exists() or (root / PRODUCTION_FILE).is_symlink():
            raise VideoError(f"{PRODUCTION_FILE} already exists in {root}")
        data = load_json(TEMPLATES_DIR / "video-production.json")
        data["production_id"] = args.production_id
        policy = data["policy"]
        if args.approval_required is not None:
            policy["approval_required"] = (
                [] if args.approval_required == ["none"] else args.approval_required
            )
        policy["max_revision_rounds"] = args.max_revision_rounds
        if args.export_requires_human_review:
            policy["export_requires_human_review"] = True
        policy["budget"] = {
            "currency": args.currency,
            "cap": args.budget_cap,
            "mode": args.budget_mode,
        }
        if args.edit_project:
            path, error = _safe_relative_path(
                root, args.edit_project, label="edit project"
            )
            if error or path is None:
                raise VideoError(error or "edit project path is invalid")
            data["edit_project"] = {"path": path.relative_to(root).as_posix()}
        _event(data, "production", "init", f"production {args.production_id} created")
        save_production(root, data)
    except (VideoError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(root / PRODUCTION_FILE)
    return 0


def cmd_video_status(args: argparse.Namespace) -> int:
    try:
        root = _root(args.root)
        payload = production_status(root, load_production(root))
    except (VideoError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Production: {payload['production_id']}")
        print(f"Current stage: {payload['current_stage'] or '-'}")
        print(f"Next action: {payload['next_action']}")
        print(
            f"Revision rounds: {payload['revision_rounds']}/{payload['max_revision_rounds']}"
        )
        for stage in payload["stages"]:
            gate = stage.get("gate")
            suffix = f" -> {gate['outcome']}" if gate else ""
            print(f"  {stage['id']:<9} {stage['status']}{suffix}")
            for reason in (gate or {}).get("reasons", []):
                print(f"            - {reason}")
        for item in payload["drift"]:
            print(
                f"DRIFT: {item['path']} ({item['stage']}/{item['kind']}) is {item['state']}"
            )
        if payload["candidates"]:
            print("Candidate selections: " + ", ".join(payload["candidates"]))
    return 1 if payload["drift"] else 0


def cmd_video_record(args: argparse.Namespace) -> int:
    def action(root: Path, data: dict[str, Any]) -> tuple[int, str]:
        before = _stage(data, args.stage)["status"]
        artifact = record_artifact(root, data, args.stage, args.kind, args.artifact)
        lines = [
            f"Recorded {artifact['kind']} {artifact['path']} sha256={artifact['sha256']}"
        ]
        # Recording reopens a judged stage; say so instead of leaving the next
        # video-approve to fail on an in_progress stage.
        if before in {"awaiting_approval", "blocked"}:
            lines.append(
                f"Stage {args.stage} was {before} and is reopened to in_progress"
                + f"; run video-complete --stage {args.stage} again"
                + (" before video-approve" if before == "awaiting_approval" else "")
                + "."
            )
        return 0, "\n".join(lines)

    return _run(args, action)


def cmd_video_complete(args: argparse.Namespace) -> int:
    def action(root: Path, data: dict[str, Any]) -> tuple[int, str]:
        gate = complete_stage(root, data, args.stage)
        lines = [
            f"{args.stage}: {gate.outcome}",
            *(f"  - {reason}" for reason in gate.reasons),
        ]
        for promise in gate.info.get("delivery_promises", []):
            lines.append(
                f"  promise {promise['id']}: {promise['passed']} ({promise['observed']})"
            )
        return (1 if gate.outcome == "blocked" else 0), "\n".join(lines)

    return _run(args, action)


def cmd_video_approve(args: argparse.Namespace) -> int:
    def action(root: Path, data: dict[str, Any]) -> tuple[int, str]:
        approve_stage(root, data, args.stage, args.by, args.note or "")
        return 0, f"{args.stage}: completed (approved by {args.by})"

    return _run(args, action)


def cmd_video_extend_rounds(args: argparse.Namespace) -> int:
    def action(root: Path, data: dict[str, Any]) -> tuple[int, str]:
        del root
        return 0, "revise: " + extend_revision_rounds(
            data, args.by, args.reason, args.rounds
        )

    return _run(args, action)


def cmd_video_skip(args: argparse.Namespace) -> int:
    def action(root: Path, data: dict[str, Any]) -> tuple[int, str]:
        skip_stage(root, data, args.stage, args.reason)
        return 0, f"{args.stage}: skipped"

    return _run(args, action)


def cmd_video_ledger(args: argparse.Namespace) -> int:
    def action(root: Path, data: dict[str, Any]) -> tuple[int, str]:
        del root
        return 0, ledger_action(data, args)

    return _run(args, action)


def register_video_commands(sub: Any) -> None:
    stages = list(VIDEO_STAGES)
    init = sub.add_parser(
        "video-init", help="create a gated video production state file"
    )
    init.add_argument("--root", required=True)
    init.add_argument("--production-id", required=True)
    init.add_argument(
        "--approval-required",
        nargs="*",
        choices=[*stages, "none"],
        help="stages that need approval (default: plan); pass 'none' to disable",
    )
    init.add_argument("--max-revision-rounds", type=int, default=3)
    init.add_argument(
        "--export-requires-human-review",
        action="store_true",
        help="export only after an inspection accepted by a human reviewer",
    )
    init.add_argument(
        "--budget-mode", choices=["observe", "warn", "cap"], default="observe"
    )
    init.add_argument("--budget-cap", type=float)
    init.add_argument("--currency", default="USD")
    init.add_argument("--edit-project")
    init.set_defaults(func=cmd_video_init)

    status = sub.add_parser(
        "video-status", help="stage gates, next action and digest drift"
    )
    status.add_argument("--root", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_video_status)

    record = sub.add_parser(
        "video-record", help="bind a project-relative artifact digest to a stage"
    )
    record.add_argument("--root", required=True)
    record.add_argument("--stage", required=True, choices=stages)
    record.add_argument(
        "--kind", required=True, choices=sorted(set().union(*STAGE_KINDS.values()))
    )
    record.add_argument("--artifact", required=True)
    record.set_defaults(func=cmd_video_record)

    complete = sub.add_parser(
        "video-complete", help="run a stage gate and record its outcome"
    )
    complete.add_argument("--root", required=True)
    complete.add_argument("--stage", required=True, choices=stages)
    complete.set_defaults(func=cmd_video_complete)

    approve = sub.add_parser("video-approve", help="approve a stage awaiting approval")
    approve.add_argument("--root", required=True)
    approve.add_argument("--stage", required=True, choices=stages)
    approve.add_argument("--by", required=True)
    approve.add_argument("--note")
    approve.set_defaults(func=cmd_video_approve)

    extend = sub.add_parser(
        "video-extend-rounds",
        help="human decision to allow more revision rounds after the limit blocked revise",
    )
    extend.add_argument("--root", required=True)
    extend.add_argument("--by", required=True)
    extend.add_argument("--reason", required=True)
    extend.add_argument("--rounds", type=int, default=1)
    extend.set_defaults(func=cmd_video_extend_rounds)

    skip = sub.add_parser(
        "video-skip", help="explicitly skip an optional stage with a reason"
    )
    skip.add_argument("--root", required=True)
    skip.add_argument("--stage", required=True, choices=stages)
    skip.add_argument("--reason", required=True)
    skip.set_defaults(func=cmd_video_skip)

    ledger = sub.add_parser(
        "video-ledger", help="reserve, settle or release budget entries"
    )
    ledger.add_argument("action", choices=["reserve", "settle", "release"])
    ledger.add_argument("--root", required=True)
    ledger.add_argument("--id", required=True)
    ledger.add_argument("--stage", choices=stages)
    ledger.add_argument("--description")
    ledger.add_argument("--estimate", type=float)
    ledger.add_argument("--actual", type=float)
    ledger.add_argument("--provider-job-id")
    ledger.set_defaults(func=cmd_video_ledger)
