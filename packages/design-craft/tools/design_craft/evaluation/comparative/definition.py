from __future__ import annotations

import json
from pathlib import Path

from scripts.design_craft_comparative_common import (
    VARIANTS_SCHEMA,
    load_scorecard,
    render_scorecard_markdown,
    validate_judgment_schema,
    variant_ids,
)
from tools.design_craft.repo import REPO_ROOT

from .contract import REQUIRED_DEFINITION_FILES


def load_variants(
    case_dir: Path, *, require_skill_paths: bool = True
) -> tuple[dict, list[str]]:
    path = case_dir / "variants.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"{path}: invalid variants JSON: {exc}"]
    errors: list[str] = []
    if payload.get("schema") != VARIANTS_SCHEMA:
        errors.append(f"{path}: schema must be {VARIANTS_SCHEMA}")
    if payload.get("host") != "pi":
        errors.append(f"{path}: comparative host must be pi")
    items = payload.get("variants")
    try:
        required = variant_ids(payload)
    except ValueError as exc:
        errors.append(f"{path}: {exc}")
        required = ("baseline", "invalid-focused", "design-craft")
    ids = (
        [item.get("id") for item in items if isinstance(item, dict)]
        if isinstance(items, list)
        else []
    )
    if sorted(ids) != sorted(required) or len(ids) != len(required):
        errors.append(f"{path}: variants must be {list(required)} exactly once")
    for item in items if isinstance(items, list) else []:
        paths = item.get("skill_paths")
        if not isinstance(paths, list) or not all(
            isinstance(value, str) for value in paths
        ):
            errors.append(
                f"{path}: variant {item.get('id')} skill_paths must be an array"
            )
            continue
        if item.get("id") == "baseline" and paths:
            errors.append(f"{path}: baseline must not load skills")
        if item.get("id") != "baseline" and not paths:
            errors.append(f"{path}: variant {item.get('id')} must load at least one skill")
        for relative in paths:
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                errors.append(
                    f"{path}: variant skill path must stay repository-relative: {relative}"
                )
            elif require_skill_paths and not REPO_ROOT.joinpath(
                relative, "SKILL.md"
            ).is_file():
                errors.append(f"{path}: missing variant skill {relative}")
    return payload, errors


def validate_definition(
    case_dir: Path,
    *,
    require_skill_paths: bool = True,
    require_scorecard_parity: bool = True,
) -> tuple[dict, dict[str, int], list[str]]:
    errors: list[str] = []
    for name in REQUIRED_DEFINITION_FILES:
        if not case_dir.joinpath(name).is_file():
            errors.append(f"{case_dir}: missing {name}")
    if errors:
        return {}, {}, errors
    variants, variant_errors = load_variants(
        case_dir, require_skill_paths=require_skill_paths
    )
    errors.extend(variant_errors)
    weights, scorecard_errors = load_scorecard(case_dir)
    errors.extend(scorecard_errors)
    if require_scorecard_parity:
        try:
            rendered_scorecard = render_scorecard_markdown(case_dir)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{case_dir}/scorecard.json: cannot render scorecard: {exc}")
        else:
            if (
                case_dir / "scorecard.md"
            ).read_text(encoding="utf-8") != rendered_scorecard:
                errors.append(
                    f"{case_dir}/scorecard.md: must be generated exactly from scorecard.json"
                )
    if weights:
        errors.extend(validate_judgment_schema(case_dir, weights))
    prompt = (case_dir / "prompt.md").read_text(encoding="utf-8").lower()
    if "do not name" not in prompt or "skill" not in prompt:
        errors.append(
            f"{case_dir}/prompt.md: must prohibit skill/source brand disclosure"
        )
    return variants, weights, errors


def active_cases(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and not path.name.startswith("_") and path.name != "history"
    )
