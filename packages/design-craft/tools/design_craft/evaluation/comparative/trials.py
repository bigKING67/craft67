"""Repeated-trial comparative evidence.

Each trial lives at ``<case>/trials/<n>/<case-id>/`` and is a complete
single-run case: byte-identical copies of the parent definition files plus one
independent generation, blind packet, judge and result. ``aggregate.json`` in
the parent binds every trial result by hash and carries per-variant means.
Certification compares means across trials instead of a single judged run.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from scripts.design_craft_comparative_common import sha256_file, variant_ids

from .contract import REQUIRED_DEFINITION_FILES

TRIALS_DIR = "trials"
AGGREGATE_FILE = "aggregate.json"
AGGREGATE_SCHEMA = "design-craft.comparative-aggregate.v1"
MIN_TRIALS = 3


def has_trials(case_dir: Path) -> bool:
    return (case_dir / TRIALS_DIR).is_dir()


def is_trial_dir(path: Path) -> bool:
    return path.parent.parent.name == TRIALS_DIR


def trial_dir(case_dir: Path, trial: int) -> Path:
    return case_dir / TRIALS_DIR / str(trial) / case_dir.name


def trial_dirs(case_dir: Path) -> list[tuple[int, Path]]:
    root = case_dir / TRIALS_DIR
    if not root.is_dir():
        return []
    found = []
    for entry in root.iterdir():
        if entry.is_dir() and re.fullmatch(r"[1-9][0-9]*", entry.name):
            found.append((int(entry.name), entry / case_dir.name))
    return sorted(found)


def prepare_trial(case_dir: Path, trial: int) -> Path:
    if trial < 1:
        raise ValueError("trial numbers start at 1")
    target = trial_dir(case_dir, trial)
    if target.exists():
        raise ValueError(f"{target} already exists")
    target.mkdir(parents=True)
    for name in REQUIRED_DEFINITION_FILES:
        shutil.copy2(case_dir / name, target / name)
    return target


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_aggregate(case_dir: Path) -> dict:
    variants = _read_json(case_dir / "variants.json")
    required = variant_ids(variants)
    trials = []
    for number, path in trial_dirs(case_dir):
        result = _read_json(path / "comparison.json")
        blind_map = _read_json(path / "blind-map.json")
        trials.append(
            {
                "trial": number,
                "comparison_sha256": sha256_file(path / "comparison.json"),
                "seed_sha256": blind_map.get("seed_sha256"),
                "scores": {
                    variant: result["results"][variant]["score"]
                    for variant in required
                },
                "winner": result.get("winner"),
            }
        )
    means = {
        variant: round(sum(t["scores"][variant] for t in trials) / len(trials), 2)
        for variant in required
    } if trials else {}
    ranked = sorted(means.items(), key=lambda item: item[1], reverse=True)
    winner = (
        ranked[0][0]
        if len(ranked) > 1 and ranked[0][1] > ranked[1][1]
        else None
    )
    return {
        "schema": AGGREGATE_SCHEMA,
        "case_id": case_dir.name,
        "focused_variant": variants.get("focused_variant"),
        "trial_count": len(trials),
        "trials": trials,
        "mean_scores": means,
        "mean_winner": winner,
    }


def validate_trials(
    case_dir: Path,
    *,
    require_current_source: bool,
) -> list[str]:
    # Imported here to avoid a cycle: case.py dispatches to this module.
    from .case import validate_case

    errors: list[str] = []
    trials = trial_dirs(case_dir)
    if len(trials) < MIN_TRIALS:
        errors.append(
            f"{case_dir}: repeated-trial evidence needs at least {MIN_TRIALS} "
            f"trials, found {len(trials)}"
        )
    numbers = [number for number, _ in trials]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"{case_dir}: trials must be numbered 1..n without gaps")
    for number, path in trials:
        for name in REQUIRED_DEFINITION_FILES:
            copy = path / name
            if not copy.is_file() or copy.read_bytes() != (
                case_dir / name
            ).read_bytes():
                errors.append(f"{path}: {name} must match the parent definition")
        errors.extend(
            validate_case(
                path,
                require_observed=True,
                require_current_source=require_current_source,
                require_win=False,
            )
        )
    if errors:
        return errors

    expected = build_aggregate(case_dir)
    seeds = [trial["seed_sha256"] for trial in expected["trials"]]
    if None in seeds or len(set(seeds)) != len(seeds):
        errors.append(f"{case_dir}: every trial needs its own blind seed")
    aggregate_path = case_dir / AGGREGATE_FILE
    try:
        recorded = _read_json(aggregate_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [*errors, f"{aggregate_path}: {exc}"]
    if recorded != expected:
        errors.append(f"{aggregate_path}: must match the recorded trial results")
    if require_current_source:
        means = expected["mean_scores"]
        if expected["mean_winner"] != "design-craft" or not all(
            means["design-craft"] > score
            for variant, score in means.items()
            if variant != "design-craft"
        ):
            errors.append(
                f"{aggregate_path}: certification requires design-craft to have "
                "the highest mean score across trials"
            )
    return errors
