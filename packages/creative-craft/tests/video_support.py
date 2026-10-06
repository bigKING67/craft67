"""Synthetic Video Harness artifacts: talking head + B-roll + captions.

Everything here is fabricated test data. Digests of media files are fake and no
render took place; render-qa documents are labelled as synthetic.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
from typing import Any

from support import ROOT, cc, load, write_json

FPS = 30
TALK_SHA = "a" * 64
BROLL_SHA = "b" * 64
GEN_SHA = "c" * 64


def run_cli(*argv: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cc.main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


def _asset(
    asset_id: str, sha: str, duration: float, kind: str = "import"
) -> dict[str, Any]:
    origin: dict[str, Any] = {"kind": kind}
    if kind == "generated":
        origin["provenance_ref"] = "jobs/gen-job.json"
    return {
        "id": asset_id,
        "file": f"assets/{sha}.media",
        "sha256": sha,
        "duration": duration,
        "video": True,
        "audio": asset_id == "talk",
        "width": 1080,
        "height": 1920,
        "origin": origin,
    }


def edit_document(
    revision: int = 1, parent: str | None = None, *, generated: bool = False
) -> dict[str, Any]:
    """Revision 1: 20 s cut. Revision 2 trims the second talking segment to 15 s total."""
    talk2_frames = 300 if revision == 1 else 150
    assets = [_asset("talk", TALK_SHA, 60), _asset("broll", BROLL_SHA, 12)]
    broll_asset = "broll"
    if generated:
        assets.append(_asset("gen", GEN_SHA, 5, "generated"))
        broll_asset = "gen"
    return {
        "schema_version": "creative-craft.edit-document.v2",
        "project_id": "talk-broll",
        "revision": revision,
        "parent_sha256": parent,
        "title": "Talking head with B-roll (synthetic)",
        "canvas": {"width": 1080, "height": 1920, "fps": FPS},
        "assets": assets,
        "tracks": [
            {"id": "v_main", "kind": "video", "locked": False, "name": "Talk"},
            {"id": "v_broll", "kind": "video", "locked": False, "name": "B-roll"},
            {"id": "c_sub", "kind": "caption", "locked": False},
        ],
        "items": [
            {
                "id": "talk1",
                "track_id": "v_main",
                "kind": "media",
                "asset_id": "talk",
                "start_frame": 0,
                "frames": 300,
                "source_in_seconds": 2.0,
                "volume": 1,
            },
            {
                "id": "talk2",
                "track_id": "v_main",
                "kind": "media",
                "asset_id": "talk",
                "start_frame": 300,
                "frames": talk2_frames,
                "source_in_seconds": 30.0,
                "volume": 1,
            },
            {
                "id": "broll1",
                "track_id": "v_broll",
                "kind": "media",
                "asset_id": broll_asset,
                "start_frame": 120,
                "frames": 90,
                "source_in_seconds": 1.0,
                "volume": 0,
            },
            {
                "id": "cap1",
                "track_id": "c_sub",
                "kind": "caption",
                "text": "先说结论",
                "link": {"item_id": "talk1", "source_from": 2.0, "source_to": 5.0},
            },
            {
                "id": "cap2",
                "track_id": "c_sub",
                "kind": "caption",
                "text": "再看细节",
                "link": {"item_id": "talk2", "source_from": 30.0, "source_to": 33.0},
            },
        ],
        "change": {
            "author": "agent",
            "summary": f"Synthetic revision {revision}",
            "operations_sha256": None,
        },
    }


def render_qa(
    doc: dict[str, Any],
    doc_sha: str,
    *,
    decision: str = "accept",
    status: str = "pass",
    review_status: str = "done",
    kind: str = "preview",
    render_file: str | None = None,
    render_sha: str = "d" * 64,
    reviewer_kind: str = "agent",
) -> dict[str, Any]:
    verdict = {"pass": "pass", "warn": "pass_with_warnings", "fail": "fail"}[status]
    seconds = cc.edit_document_duration_frames(doc) / FPS
    findings = []
    if decision in {"revise", "reject"}:
        findings.append(
            {
                "id": "f1",
                "severity": "major",
                "observation": "Second talking segment drags after the point lands.",
                "refs": [
                    {"time_seconds": 14.0, "item_id": "talk2", "sample_id": "s-talk2"}
                ],
                "fix": "Trim talk2 to five seconds.",
            }
        )
    return {
        "schema_version": "creative-craft.render-qa.v1",
        "qa_id": f"qa-r{doc['revision']}",
        "project_id": doc["project_id"],
        "revision": doc["revision"],
        "revision_sha256": doc_sha,
        "render": {
            "kind": kind,
            "file": render_file or f"renders/r{doc['revision']}.mp4",
            "sha256": render_sha,
            "width": 540,
            "height": 960,
            "fps": FPS,
            "duration_seconds": seconds,
            "has_audio": True,
        },
        "tool": {"name": "synthetic-fixture", "version": "0"},
        "created_at": "2026-10-02T00:00:00Z",
        "checks": [
            {
                "id": "duration",
                "category": "structure",
                "status": status,
                "observation": "Synthetic check; no real render was measured.",
            },
        ],
        "samples": [
            {
                "id": "s-talk2",
                "time_seconds": 14.0,
                "reason": "item_mid",
                "item_id": "talk2",
                "file": "qa/s-talk2.png",
                "sha256": "e" * 64,
            },
        ],
        "boundary_clips": [],
        "contact_sheet": None,
        "verdict": verdict,
        "review": {
            "status": review_status,
            "reviewer": "synthetic-agent" if review_status == "done" else None,
            "reviewer_kind": reviewer_kind,
            "decision": decision if review_status == "done" else "pending",
            "findings": findings,
        },
        "unverified": [
            "Synthetic fixture: no real render, frames or audio were inspected."
        ],
    }


def _evidence(
    start: float, end: float, excerpt: str, modality: str = "asr"
) -> dict[str, Any]:
    return {
        "modality": modality,
        "start_seconds": start,
        "end_seconds": end,
        "excerpt": excerpt,
        "raw_score": None,
        "method": "synthetic transcript",
    }


def _beat(
    beat_id: str,
    role: str,
    seconds: float,
    source_kind: str,
    selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": beat_id,
        "role": role,
        "purpose": f"{role} beat",
        "duration_seconds": seconds,
        "source_kind": source_kind,
        "requirement": f"{role} requirement",
        "hard_constraints": [],
        "selection": selection,
        "generation_ref": None,
        "locked": False,
    }


def production_plan(
    *,
    broll_status: str = "candidate",
    extra_beats: list[dict[str, Any]] | None = None,
    duration_range: tuple[float, float] = (12, 18),
    max_share: float = 0.5,
) -> dict[str, Any]:
    beats = [
        _beat(
            "hook",
            "hook",
            10,
            "footage",
            {
                "asset_ref": "talk",
                "source_start_seconds": 2.0,
                "source_end_seconds": 12.0,
                "evidence": [_evidence(2.0, 5.0, "先说结论")],
                "reason": "Strongest opening line.",
                "status": "confirmed",
            },
        ),
        _beat(
            "broll",
            "illustrate",
            3,
            "footage",
            {
                "asset_ref": "broll",
                "source_start_seconds": 1.0,
                "source_end_seconds": 4.0,
                "evidence": [_evidence(1.0, 4.0, "hands on product", "frame")],
                "reason": "Shows the detail.",
                "status": broll_status,
            },
        ),
        _beat(
            "point",
            "point",
            5,
            "footage",
            {
                "asset_ref": "talk",
                "source_start_seconds": 30.0,
                "source_end_seconds": 35.0,
                "evidence": [_evidence(30.0, 33.0, "再看细节")],
                "reason": "Delivers the detail.",
                "status": "confirmed",
            },
        ),
    ]
    beats.extend(extra_beats or [])
    return {
        "schema_version": "creative-craft.production-plan.v1",
        "plan_id": "talk-broll-plan",
        "title": "Talking head + B-roll cut (synthetic)",
        "brief_ref": None,
        "intended_use": "Internal method example; synthetic data only.",
        "output": {"duration_seconds_target": 15, "ratio": "9:16", "language": "zh-CN"},
        "delivery_promises": [
            {
                "id": "length",
                "statement": "Cut runs within the planned range.",
                "check": {
                    "kind": "duration_range",
                    "min": duration_range[0],
                    "max": duration_range[1],
                },
            },
            {
                "id": "captions",
                "statement": "Spoken lines are captioned.",
                "check": {"kind": "captions_present"},
            },
            {
                "id": "generated",
                "statement": "Generated shots stay a minority.",
                "check": {"kind": "max_generated_share", "max": max_share},
            },
            {
                "id": "tone",
                "statement": "Tone feels conversational.",
                "check": {"kind": "manual"},
            },
        ],
        "beats": beats,
    }


def generate_beat() -> dict[str, Any]:
    beat = _beat("gen", "gap", 3, "generate")
    beat["generation_ref"] = {
        "job_path": "jobs/gen-job.json",
        "receipt_path": "jobs/gen-receipt.json",
    }
    return beat


def write_generation(root: Path, *, outcome: str = "succeeded") -> None:
    job = load("skills/creative-craft/templates/video-job.json")
    job["job_id"] = "gen-job"
    job_path = root / "jobs/gen-job.json"
    job_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(job_path, job)
    receipt = load("skills/creative-craft/templates/execution-receipt.json")
    receipt.update(
        receipt_id="gen-receipt",
        job_id="gen-job",
        job_sha256=cc.sha256_file(job_path),
        provider_profile="bytedance.seedance-2.5.2026-07-31",
        execution_surface="bytedance.jimeng_web",
        model="Seedance 2.5",
        snapshot=None,
        outcome=outcome,
        outputs=[]
        if outcome == "failed"
        else [
            {
                "asset_id": "gen",
                "path": "media/gen.mp4",
                "sha256": GEN_SHA,
                "mime_type": "video/mp4",
                "bytes": 1,
            }
        ],
        limitations=["Synthetic receipt; no provider execution occurred."],
    )
    write_json(root / "jobs/gen-receipt.json", receipt)


def write_doc(root: Path, rel: str, data: dict[str, Any]) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, data)
    return cc.sha256_file(path)


def production(root: Path) -> dict[str, Any]:
    return json.loads((root / "production.json").read_text(encoding="utf-8"))


def stage(root: Path, stage_id: str) -> dict[str, Any]:
    return next(item for item in production(root)["stages"] if item["id"] == stage_id)


def build_talking_head_production(
    root: Path, *, generated: bool = False, human_review: bool = False
) -> dict[str, str]:
    """Run the full gated flow through the CLI and return the bound file paths."""
    r = str(root)

    def ok(*argv: str) -> str:
        code, out, err = run_cli(*argv)
        if code != 0:
            raise AssertionError(f"{argv} failed: {out}{err}")
        return out

    policy = ["--export-requires-human-review"] if human_review else []
    ok("video-init", "--root", r, "--production-id", "talk-broll", *policy)
    (root / "brief.md").write_text(
        "# Brief (synthetic)\n15 s vertical cut with B-roll and captions.\n",
        encoding="utf-8",
    )
    ok(
        "video-record",
        "--root",
        r,
        "--stage",
        "brief",
        "--kind",
        "brief",
        "--artifact",
        "brief.md",
    )
    ok("video-complete", "--root", r, "--stage", "brief")
    ok(
        "video-skip",
        "--root",
        r,
        "--stage",
        "reference",
        "--reason",
        "Founder footage is the only reference.",
    )
    plan = production_plan(extra_beats=[generate_beat()] if generated else None)
    write_doc(root, "plan.json", plan)
    ok(
        "video-record",
        "--root",
        r,
        "--stage",
        "plan",
        "--kind",
        "production-plan",
        "--artifact",
        "plan.json",
    )
    ok("video-complete", "--root", r, "--stage", "plan")
    ok(
        "video-approve",
        "--root",
        r,
        "--stage",
        "plan",
        "--by",
        "producer",
        "--note",
        "beats agreed",
    )
    ok("video-complete", "--root", r, "--stage", "select")
    if generated:
        write_generation(root)
        ok(
            "video-record",
            "--root",
            r,
            "--stage",
            "generate",
            "--kind",
            "video-job",
            "--artifact",
            "jobs/gen-job.json",
        )
        ok(
            "video-record",
            "--root",
            r,
            "--stage",
            "generate",
            "--kind",
            "execution-receipt",
            "--artifact",
            "jobs/gen-receipt.json",
        )
        ok("video-complete", "--root", r, "--stage", "generate")
    else:
        ok(
            "video-skip",
            "--root",
            r,
            "--stage",
            "generate",
            "--reason",
            "All beats use existing footage.",
        )
    doc1 = edit_document(1, generated=generated)
    sha1 = write_doc(root, "edit/revisions/000001.json", doc1)
    ok(
        "video-record",
        "--root",
        r,
        "--stage",
        "assemble",
        "--kind",
        "edit-document",
        "--artifact",
        "edit/revisions/000001.json",
    )
    ok("video-complete", "--root", r, "--stage", "assemble")
    write_doc(
        root, "qa/r1.json", render_qa(doc1, sha1, decision="revise", status="warn")
    )
    ok(
        "video-record",
        "--root",
        r,
        "--stage",
        "inspect",
        "--kind",
        "render-qa",
        "--artifact",
        "qa/r1.json",
    )
    ok("video-complete", "--root", r, "--stage", "inspect")
    doc2 = edit_document(2, sha1, generated=generated)
    sha2 = write_doc(root, "edit/revisions/000002.json", doc2)
    ok(
        "video-record",
        "--root",
        r,
        "--stage",
        "revise",
        "--kind",
        "edit-document",
        "--artifact",
        "edit/revisions/000002.json",
    )
    ok("video-complete", "--root", r, "--stage", "revise")
    reviewer_kind = "human" if human_review else "agent"
    qa2 = render_qa(doc2, sha2, decision="accept", reviewer_kind=reviewer_kind)
    write_doc(root, "qa/r2.json", qa2)
    ok(
        "video-record",
        "--root",
        r,
        "--stage",
        "inspect",
        "--kind",
        "render-qa",
        "--artifact",
        "qa/r2.json",
    )
    ok("video-complete", "--root", r, "--stage", "inspect")
    if human_review:
        ok("video-approve", "--root", r, "--stage", "inspect", "--by", "reviewer", "--note", "watched the cut")
    record_export_render(root, doc2, sha2, ok)
    ok(
        "video-record",
        "--root",
        r,
        "--stage",
        "export",
        "--kind",
        "edit-document",
        "--artifact",
        "edit/revisions/000002.json",
    )
    ok("video-complete", "--root", r, "--stage", "export")
    return {"doc1": sha1, "doc2": sha2}


def record_export_render(
    root: Path, doc: dict[str, Any], doc_sha: str, ok: Any, *, kind: str = "export"
) -> str:
    """Bind a placeholder delivered file and its export render-qa to the export stage."""
    media = root / "renders" / f"r{doc['revision']}-export.synthetic"
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(f"synthetic export of revision {doc['revision']}\n".encode())
    media_sha = cc.sha256_file(media)
    qa = render_qa(
        doc,
        doc_sha,
        kind=kind,
        render_file=media.relative_to(root).as_posix(),
        render_sha=media_sha,
    )
    qa_rel = f"qa/r{doc['revision']}-export.json"
    write_doc(root, qa_rel, qa)
    r = str(root)
    for kind_name, rel in (("media", media.relative_to(root).as_posix()), ("render-qa", qa_rel)):
        ok("video-record", "--root", r, "--stage", "export", "--kind", kind_name, "--artifact", rel)
    return media_sha


__all__ = [
    "FPS",
    "ROOT",
    "build_talking_head_production",
    "copy",
    "edit_document",
    "generate_beat",
    "production",
    "production_plan",
    "record_export_render",
    "render_qa",
    "run_cli",
    "stage",
    "write_doc",
    "write_generation",
]
