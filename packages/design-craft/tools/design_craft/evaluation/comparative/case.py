from __future__ import annotations

from pathlib import Path

from scripts.design_craft_comparative_common import sha256_file, variant_ids

from .contract import REQUIRED_OBSERVED_FILES
from .definition import validate_definition
from .judge_evidence import validate_blind_map, validate_judge_evidence
from .result import validate_result
from .run_evidence import validate_run


def validate_case(
    case_dir: Path,
    *,
    require_observed: bool,
    require_current_source: bool = True,
) -> list[str]:
    variants, weights, errors = validate_definition(
        case_dir,
        require_skill_paths=require_current_source,
        require_scorecard_parity=require_current_source,
    )
    if errors:
        return errors
    try:
        required_variants = variant_ids(variants)
    except ValueError as exc:
        return [f"{case_dir}/variants.json: {exc}"]
    observed_any = any(case_dir.glob("output.*.md")) or any(
        case_dir.glob("run.*.json")
    ) or any(case_dir.joinpath(name).exists() for name in REQUIRED_OBSERVED_FILES)
    if not require_observed and not observed_any:
        return []
    prompt_hash = sha256_file(case_dir / "prompt.md")
    variant_map = {
        item.get("id"): item
        for item in variants.get("variants", [])
        if isinstance(item, dict)
    }
    runs: dict[str, dict] = {}
    for variant_id in required_variants:
        payload, run_errors = validate_run(
            case_dir,
            variant_id,
            variant_map.get(variant_id, {}),
            prompt_hash=prompt_hash,
            require_current_source=require_current_source,
        )
        if payload:
            runs[variant_id] = payload
        errors.extend(run_errors)
    for name in REQUIRED_OBSERVED_FILES:
        if not case_dir.joinpath(name).is_file():
            errors.append(f"{case_dir}: missing observed comparative artifact {name}")
    if errors:
        return errors
    blind_map, map_errors = validate_blind_map(case_dir, required_variants)
    errors.extend(map_errors)
    judge_manifest, judgment, judge_errors = validate_judge_evidence(
        case_dir, weights
    )
    errors.extend(judge_errors)
    if not errors:
        errors.extend(
            validate_result(
                case_dir,
                blind_map=blind_map,
                judge_manifest=judge_manifest,
                judgment=judgment,
                runs=runs,
                required_variants=required_variants,
                require_current_source=require_current_source,
            )
        )
    return errors
