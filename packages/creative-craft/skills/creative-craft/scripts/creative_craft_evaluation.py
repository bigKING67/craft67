"""Prompt compilation and evidence-aware evaluation scoring."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from creative_craft_contracts import Result, ValidationContext, validate_data
from creative_craft_project import ProjectGraph, resolve_evidence_ref


def render_result(path: Path, kind: str, result: Result, as_json: bool) -> int:
    payload = {
        "file": str(path),
        "kind": kind,
        "valid": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"{status} {kind}: {path}")
        for message in result.errors:
            print(f"  ERROR: {message}")
        for message in result.warnings:
            print(f"  WARN:  {message}")
    return 0 if result.ok else 1


def bullet_lines(items: Iterable[Any]) -> list[str]:
    values = [str(item).strip() for item in items if str(item).strip()]
    return [f"- {value}" for value in values]


def section(title: str, lines: Iterable[str]) -> list[str]:
    values = [line for line in lines if line.strip()]
    if not values:
        return []
    return [f"### {title}", *values, ""]


def compile_image_markdown(data: dict[str, Any]) -> str:
    canvas = data["canvas"]
    prompt = data["prompt"]
    declared_status = data.get("declared_status", data.get("status", "unknown"))
    out: list[str] = [
        f"# Image execution pack — {data['job_id']}",
        "",
        f"- Provider profile: `{data['provider_profile']}`",
        f"- Execution surface: `{data.get('execution_surface', 'legacy-unspecified')}`",
        f"- Task: `{data['task_type']}`",
        f"- Execution mode: `{data['execution_mode']}`",
        f"- Declared status: `{declared_status}`",
        f"- Size: `{canvas['size']}`",
        f"- Quality: `{canvas['quality']}`",
        f"- Format: `{canvas['format']}`",
        f"- Compression: `{canvas['compression'] if canvas['compression'] is not None else 'provider default'}`",
        f"- Background: `{canvas['background']}`",
        f"- Variants: `{canvas['variants']}`",
        "",
        "## Prompt",
        "",
    ]
    prompt_lines: list[str] = []
    prompt_lines += section(
        "INTENDED USE AND OUTPUT",
        [
            data["intended_use"],
            (
                f"Create {canvas['variants']} output variant(s) at {canvas['size']}, "
                f"{canvas['quality']} quality, {canvas['format']} format, "
                f"{canvas['background']} background."
            ),
        ],
    )
    prompt_lines += section("BACKGROUND / SCENE", [prompt["scene"]])
    prompt_lines += section("SUBJECT", [prompt["subject"]])
    prompt_lines += section("ACTION / EXPRESSION", [prompt.get("action", "")])
    prompt_lines += section(
        "COMPOSITION / CAMERA / NEGATIVE SPACE", [prompt["composition"]]
    )
    prompt_lines += section("LIGHTING", [prompt["lighting"]])
    prompt_lines += section("MATERIALS / MEDIUM / STYLE", [prompt["materials_style"]])

    exact_text_lines: list[str] = []
    for item in prompt.get("exact_text", []):
        if not isinstance(item, dict):
            continue
        text = item.get("text", "")
        placement = item.get("placement", "")
        typography = item.get("typography", "")
        suffix = "; ".join(part for part in (placement, typography) if part)
        exact_text_lines.append(f'- "{text}"' + (f" — {suffix}" if suffix else ""))
    if exact_text_lines:
        exact_text_lines.append("- Include no other text unless explicitly listed.")
    prompt_lines += section("EXACT TEXT / TYPOGRAPHY", exact_text_lines)

    reference_lines: list[str] = []
    for ref in prompt.get("references", []):
        if not isinstance(ref, dict):
            continue
        line = f"- @{ref.get('asset_id')}: {ref.get('role')}"
        preserve = ref.get("preserve", [])
        if preserve:
            line += f" Preserve: {', '.join(str(x) for x in preserve)}."
        reference_lines.append(line)
    prompt_lines += section("REFERENCE MAP", reference_lines)
    prompt_lines += section("CHANGE ONLY", bullet_lines(prompt.get("change", [])))
    prompt_lines += section(
        "PRESERVE EXACTLY", bullet_lines(prompt.get("preserve", []))
    )
    prompt_lines += section("CONSTRAINTS", bullet_lines(prompt.get("constraints", [])))
    prompt_lines += section(
        "DO NOT ADD / EXCLUDE", bullet_lines(prompt.get("exclude", []))
    )

    out.extend(
        ["```text", *prompt_lines, "```", "", "## Post-generation inspection", ""]
    )
    out.extend(bullet_lines(data.get("inspection", [])))
    out.extend(
        [
            "",
            f"Rights status: `{data.get('rights', {}).get('status', 'UNVERIFIED')}`",
            "",
            (
                f"This pack was compiled from declared status `{declared_status}`; compilation is not "
                "evidence that an image was generated or approved."
            ),
        ]
    )
    return "\n".join(out).rstrip() + "\n"


def compile_video_markdown(data: dict[str, Any]) -> str:
    fmt = data["format"]
    declared_status = data.get("declared_status", data.get("status", "unknown"))
    out: list[str] = [
        f"# Video execution pack — {data['job_id']}",
        "",
        f"- Provider profile: `{data['provider_profile']}`",
        f"- Execution surface: `{data.get('execution_surface', 'legacy-unspecified')}`",
        f"- Task: `{data['task_type']}`",
        f"- Execution mode: `{data['execution_mode']}`",
        f"- Declared status: `{declared_status}`",
        f"- Duration: `{data['duration_seconds']}s`",
        f"- Aspect ratio: `{fmt['aspect_ratio']}`",
        f"- Resolution target: `{fmt['resolution_target']}`",
        f"- Language: `{fmt['language']}`",
        "",
        "## Prompt",
        "",
    ]
    prompt_lines: list[str] = []
    prompt_lines += section(
        "FORMAT AND INTENDED USE",
        [
            data["intended_use"],
            (
                f"{data['duration_seconds']}-second audiovisual video, "
                f"{fmt['aspect_ratio']}, {fmt['resolution_target']}, language {fmt['language']}."
            ),
        ],
    )
    prompt_lines += section("CREATIVE PREMISE", [data["premise"]])
    prompt_lines += section("END STATE", [data["end_state"]])

    reference_lines: list[str] = []
    for ref in data.get("references", []):
        if isinstance(ref, dict):
            reference_lines.append(
                f"- @{ref.get('asset_id')} ({ref.get('kind')}): {ref.get('role')}"
            )
    prompt_lines += section("REFERENCE MAP", reference_lines)
    prompt_lines += section(
        "CONTINUITY LOCKS", bullet_lines(data.get("continuity_locks", []))
    )

    beat_lines: list[str] = []
    for beat in data.get("timeline", []):
        if not isinstance(beat, dict):
            continue
        beat_lines.extend(
            [
                f"{beat.get('start'):g}–{beat.get('end'):g}s",
                f"- Visual: {beat.get('visual')}",
                f"- Action/performance: {beat.get('action')}",
                f"- Camera: {beat.get('camera')}",
                f"- Audio: {beat.get('audio')}",
                "",
            ]
        )
    prompt_lines += section("TIMESTAMPED BEATS", beat_lines)

    env = data.get("environment", {})
    prompt_lines += section(
        "ENVIRONMENT / MATERIAL / LIGHT / PHYSICS",
        [
            f"- Lighting: {env.get('lighting', '')}",
            f"- Materials: {env.get('materials', '')}",
            f"- Physics: {env.get('physics', '')}",
        ],
    )
    audio = data.get("dialogue_audio", {})
    audio_lines: list[str] = []
    for dialogue in audio.get("dialogue", []):
        audio_lines.append(f'- Dialogue: "{dialogue}"')
    audio_lines.extend(
        [
            f"- Voice: {audio.get('voice') or '(none)'}",
            f"- Ambience: {audio.get('ambience') or '(none)'}",
        ]
    )
    audio_lines.extend(f"- Effect: {x}" for x in audio.get("effects", []))
    audio_lines.append(f"- Music: {audio.get('music') or '(none)'}")
    prompt_lines += section(
        "DIALOGUE / VOICE / AMBIENCE / EFFECTS / MUSIC", audio_lines
    )

    edit = data.get("edit", {})
    edit_lines: list[str] = []
    if edit.get("range"):
        edit_lines.append(f"- Time range: {edit['range']}")
    edit_lines += bullet_lines(edit.get("change", []))
    prompt_lines += section("EDIT ONLY", edit_lines)
    prompt_lines += section("PRESERVE", bullet_lines(edit.get("preserve", [])))
    prompt_lines += section(
        "EXCLUDE / FAILURE CONDITIONS", bullet_lines(data.get("exclude", []))
    )

    out.extend(
        ["```text", *prompt_lines, "```", "", "## Post-generation inspection", ""]
    )
    out.extend(bullet_lines(data.get("inspection", [])))
    out.extend(
        [
            "",
            f"Rights status: `{data.get('rights', {}).get('status', 'UNVERIFIED')}`",
            "",
            (
                f"This pack was compiled from declared status `{declared_status}`; compilation is not "
                "evidence that a video was generated or approved."
            ),
        ]
    )
    return "\n".join(out).rstrip() + "\n"


def _score_evaluation_v1(data: dict[str, Any]) -> dict[str, Any]:
    _, validation = validate_data(data, "evaluation")
    if not validation.ok:
        return {
            "status": "invalid",
            "errors": validation.errors,
            "warnings": validation.warnings,
        }

    gates = data["gates"]
    required_gates = {
        "rights_clear": gates["rights_clear"],
        "brief_locked": gates["brief_locked"],
        "deliverable_specified": gates["deliverable_specified"],
    }
    if data["stage"] in {"output", "delivery"}:
        required_gates["actual_output_observed"] = bool(gates["actual_output_observed"])
    failed = [name for name, value in required_gates.items() if not value]
    if failed:
        return {
            "status": "blocked",
            "score": None,
            "coverage": None,
            "failed_gates": failed,
            "warnings": validation.warnings,
        }

    dimensions = data["dimensions"]
    total_weight = sum(float(d["weight"]) for d in dimensions)
    covered = [
        d
        for d in dimensions
        if d["evidence_state"] != "UNVERIFIED" and str(d.get("evidence", "")).strip()
    ]
    covered_weight = sum(float(d["weight"]) for d in covered)
    coverage = 100.0 * covered_weight / total_weight if total_weight else 0.0

    if coverage < 80.0:
        return {
            "status": "withheld",
            "score": None,
            "coverage": round(coverage, 2),
            "reason": "evidence coverage is below 80%",
            "warnings": validation.warnings,
        }

    numerator = sum((float(d["score"]) / 5.0) * float(d["weight"]) for d in covered)
    score = 100.0 * numerator / covered_weight if covered_weight else 0.0
    if coverage >= 100:
        coverage_confidence = "high"
    elif coverage >= 90:
        coverage_confidence = "medium"
    else:
        coverage_confidence = "low"
    explicit_conf = [d["confidence"] for d in covered]
    rank = {"low": 0, "medium": 1, "high": 2}
    min_dim = min(explicit_conf, key=lambda x: rank[x]) if explicit_conf else "low"
    confidence = min((coverage_confidence, min_dim), key=lambda x: rank[x])
    return {
        "status": "scored",
        "score": round(score, 2),
        "coverage": round(coverage, 2),
        "confidence": confidence,
        "stage": data["stage"],
        "recommendation": data["recommendation"],
        "warnings": validation.warnings,
        "dimensions": [
            {
                "id": d["id"],
                "weight": d["weight"],
                "score": d["score"],
                "evidence_state": d["evidence_state"],
                "confidence": d["confidence"],
            }
            for d in dimensions
        ],
    }


EVIDENCE_STRENGTH = {
    "OBSERVED": 1.0,
    "SPECIFIED": 0.9,
    "INFERRED": 0.7,
    "HYPOTHESIZED": 0.4,
    "UNVERIFIED": 0.0,
}


EVALUATION_TARGET_SCHEMAS = {
    "route": {"creative-craft.concept-routes.v1"},
    "direction": {"creative-craft.creative-direction.v1"},
    "output": {
        "creative-craft.image-job.v2",
        "creative-craft.video-job.v2",
        "creative-craft.execution-receipt.v1",
        "creative-craft.output-inspection.v1",
    },
    "delivery": {"creative-craft.delivery.v2"},
}


def _inspection_matches_receipt_output(
    inspection: dict[str, Any], receipt: dict[str, Any]
) -> bool:
    if inspection.get("job_id") != receipt.get("job_id"):
        return False
    if inspection.get("receipt_id") != receipt.get("receipt_id"):
        return False
    return any(
        isinstance(output, dict)
        and output.get("asset_id") == inspection.get("output_asset_id")
        and output.get("sha256") == inspection.get("output_sha256")
        for output in receipt.get("outputs", [])
    )


def _receipt_output_observed(graph: ProjectGraph, receipt: dict[str, Any]) -> bool:
    if receipt.get("outcome") not in {"succeeded", "partial"} or not receipt.get(
        "outputs"
    ):
        return False
    return any(
        artifact_type == "output-inspection"
        and _inspection_matches_receipt_output(record["data"], receipt)
        for (artifact_type, _), record in graph.records.items()
    )


def _job_output_observed(graph: ProjectGraph, job: dict[str, Any]) -> bool:
    job_id = job.get("job_id")
    return any(
        artifact_type == "execution-receipt"
        and record["data"].get("job_id") == job_id
        and _receipt_output_observed(graph, record["data"])
        for (artifact_type, _), record in graph.records.items()
    )


def _delivery_output_observed(graph: ProjectGraph, delivery: dict[str, Any]) -> bool:
    files = delivery.get("files", [])
    if not files:
        return False
    for item in files:
        if not isinstance(item, dict):
            return False
        receipt_record = graph.record("execution-receipt", str(item.get("receipt_id")))
        inspection_record = graph.record(
            "output-inspection", str(item.get("inspection_id"))
        )
        if receipt_record is None or inspection_record is None:
            return False
        receipt = receipt_record["data"]
        inspection = inspection_record["data"]
        if (
            receipt.get("job_id") != item.get("job_id")
            or inspection.get("job_id") != item.get("job_id")
            or inspection.get("output_asset_id") != item.get("asset_id")
            or inspection.get("output_sha256") != item.get("sha256")
            or not _inspection_matches_receipt_output(inspection, receipt)
        ):
            return False
    return True


def _target_output_observed(
    graph: ProjectGraph, target: dict[str, Any], schema_version: str
) -> bool:
    if schema_version in {"creative-craft.image-job.v2", "creative-craft.video-job.v2"}:
        return _job_output_observed(graph, target)
    if schema_version == "creative-craft.execution-receipt.v1":
        return _receipt_output_observed(graph, target)
    if schema_version == "creative-craft.output-inspection.v1":
        receipt = graph.record("execution-receipt", str(target.get("receipt_id")))
        return bool(
            receipt
            and receipt["data"].get("outcome") in {"succeeded", "partial"}
            and _inspection_matches_receipt_output(target, receipt["data"])
        )
    if schema_version == "creative-craft.delivery.v2":
        return _delivery_output_observed(graph, target)
    return False


def _evaluation_gates(data: dict[str, Any], graph: ProjectGraph) -> dict[str, bool]:
    brief = graph.record("brief", str(data.get("brief_id")))
    brief_locked = bool(brief and brief["data"].get("status") == "locked")
    target_ok, target, _ = resolve_evidence_ref(graph, data.get("target_ref"))
    deliverable_specified = bool(brief and brief["data"].get("deliverables"))
    if target_ok and isinstance(target, dict):
        if target.get("schema_version") == "creative-craft.creative-direction.v1":
            deliverable_specified = bool(target.get("deliverables"))
        elif target.get("schema_version") == "creative-craft.delivery.v2":
            deliverable_specified = bool(
                target.get("files") or target.get("validation")
            )

    relevant_asset_ids: set[str] = set()
    relevant_job_rights: list[str] = []
    if target_ok and isinstance(target, dict):
        for ref in target.get("reference_roles", []):
            if isinstance(ref, dict) and isinstance(ref.get("asset_id"), str):
                relevant_asset_ids.add(ref["asset_id"])
    for (artifact_type, _), record in graph.records.items():
        if artifact_type in {"image", "video"} and record["data"].get(
            "brief_id"
        ) == data.get("brief_id"):
            relevant_job_rights.append(
                str(record["data"].get("rights", {}).get("status"))
            )
            relevant_asset_ids.update(
                str(asset_id) for asset_id in record["data"].get("asset_refs", [])
            )
    rights_values: list[str] = list(relevant_job_rights)
    consent_values: list[str] = []
    for (artifact_type, _), record in graph.records.items():
        if artifact_type != "asset-ledger":
            continue
        for asset in record["data"].get("assets", []):
            if isinstance(asset, dict) and asset.get("asset_id") in relevant_asset_ids:
                rights_values.append(str(asset.get("rights_status")))
                consent_values.append(str(asset.get("consent_status")))
    rights_clear = (
        bool(rights_values)
        and all(value in {"CLEARED", "LIMITED"} for value in rights_values)
        and all(
            value in {"CLEARED", "LIMITED", "NOT_APPLICABLE"}
            for value in consent_values
        )
    )

    stage = str(data.get("stage"))
    target_schema = ""
    if target_ok and isinstance(target, dict):
        target_schema = str(target.get("schema_version"))
    target_compatible = bool(
        target_ok and target_schema in EVALUATION_TARGET_SCHEMAS.get(stage, set())
    )
    actual_output_observed = bool(
        stage not in {"output", "delivery"}
        or (
            target_compatible
            and isinstance(target, dict)
            and _target_output_observed(graph, target, target_schema)
        )
    )
    return {
        "rights_clear": rights_clear,
        "brief_locked": brief_locked,
        "deliverable_specified": deliverable_specified,
        "target_compatible": target_compatible,
        "actual_output_observed": actual_output_observed,
    }


def _score_evaluation_v2(
    data: dict[str, Any], graph: ProjectGraph | None
) -> dict[str, Any]:
    context = ValidationContext()
    _, validation = validate_data(data, "evaluation", context)
    if not validation.ok:
        return {
            "status": "invalid",
            "errors": validation.errors,
            "warnings": validation.warnings,
        }
    if graph is None:
        return {
            "status": "blocked",
            "score": None,
            "gate_status": {"project_evidence_bound": False},
            "failed_gates": ["project_evidence_bound"],
            "coverage": 0.0,
            "evidence_strength": 0.0,
            "evidence_distribution": {},
            "confidence": "INSUFFICIENT",
            "uncertainty": [
                "Evaluation v2 requires --root and a valid project manifest."
            ],
            "warnings": validation.warnings,
        }
    if not graph.result.ok:
        return {
            "status": "invalid",
            "errors": graph.result.errors,
            "warnings": graph.result.warnings,
        }

    gates = _evaluation_gates(data, graph)
    required_gates = ["rights_clear", "brief_locked", "deliverable_specified"]
    if data["stage"] in {"output", "delivery"}:
        required_gates.extend(("target_compatible", "actual_output_observed"))
    failed_gates = [name for name in required_gates if not gates[name]]
    dimensions = data["dimensions"]
    total_weight = sum(float(item["weight"]) for item in dimensions)
    covered = [
        item
        for item in dimensions
        if item["evidence_state"] != "UNVERIFIED" and item["evidence_refs"]
    ]
    covered_weight = sum(float(item["weight"]) for item in covered)
    coverage = 100.0 * covered_weight / total_weight if total_weight else 0.0
    distribution = {
        state: round(
            100.0
            * sum(
                float(item["weight"])
                for item in dimensions
                if item["evidence_state"] == state
            )
            / total_weight,
            2,
        )
        if total_weight
        else 0.0
        for state in EVIDENCE_STRENGTH
    }
    strength = (
        100.0
        * sum(
            float(item["weight"]) * EVIDENCE_STRENGTH[item["evidence_state"]]
            for item in dimensions
        )
        / total_weight
        if total_weight
        else 0.0
    )
    strong_weight = distribution["OBSERVED"] + distribution["SPECIFIED"]
    hypothesized_weight = distribution["HYPOTHESIZED"]
    if (
        not failed_gates
        and coverage == 100.0
        and strong_weight >= 80.0
        and hypothesized_weight == 0
    ):
        confidence = "STRONG"
    elif not failed_gates and coverage >= 90.0 and hypothesized_weight <= 20.0:
        confidence = "MIXED"
    elif not failed_gates and coverage >= 80.0:
        confidence = "WEAK"
    else:
        confidence = "INSUFFICIENT"
    score = None
    if coverage >= 80.0 and not failed_gates:
        score = (
            100.0
            * sum(
                (float(item["score"]) / 5.0) * float(item["weight"]) for item in covered
            )
            / covered_weight
            if covered_weight
            else None
        )
    uncertainty = list(data.get("remaining_unknowns", []))
    uncertainty.extend(
        f"{item['id']} is {item['evidence_state']}"
        for item in dimensions
        if item["evidence_state"] in {"HYPOTHESIZED", "UNVERIFIED"}
    )
    if failed_gates:
        status = "blocked"
    elif coverage < 80.0:
        status = "withheld"
    else:
        status = "scored"
    return {
        "status": status,
        "score": round(score, 2) if score is not None else None,
        "gate_status": gates,
        "failed_gates": failed_gates,
        "coverage": round(coverage, 2),
        "evidence_strength": round(strength, 2),
        "evidence_distribution": distribution,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "stage": data["stage"],
        "recommendation": data["recommendation"],
        "warnings": validation.warnings,
    }


def score_evaluation(
    data: dict[str, Any], graph: ProjectGraph | None = None
) -> dict[str, Any]:
    if data.get("schema_version") == "creative-craft.evaluation.v2":
        return _score_evaluation_v2(data, graph)
    return _score_evaluation_v1(data)
