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
import tempfile
from pathlib import Path

from scripts.design_craft_comparative_common import sha256_file, variant_ids

from .contract import REQUIRED_DEFINITION_FILES

TRIALS_DIR = "trials"
AGGREGATE_FILE = "aggregate.json"
AGGREGATE_SCHEMA = "design-craft.comparative-aggregate.v1"
MIN_TRIALS = 3
TRIAL_NAME = re.compile(r"[1-9][0-9]*")


def has_trials(case_dir: Path) -> bool:
    return (case_dir / TRIALS_DIR).is_dir()


def is_trial_dir(path: Path) -> bool:
    return (
        path.parent.parent.name == TRIALS_DIR
        and TRIAL_NAME.fullmatch(path.parent.name) is not None
        and path.name == path.parent.parent.parent.name
    )


def trial_dir(case_dir: Path, trial: int) -> Path:
    return case_dir / TRIALS_DIR / str(trial) / case_dir.name


def scan_trials(case_dir: Path) -> tuple[list[tuple[int, Path]], list[str]]:
    """Return numbered trials and an error for every entry that is not one.

    Unrecognised entries are errors, not skips, so a trial cannot drop out of
    the mean by being renamed.
    """
    root = case_dir / TRIALS_DIR
    if not root.is_dir():
        return [], []
    found: list[tuple[int, Path]] = []
    errors: list[str] = []
    for entry in sorted(root.iterdir()):
        if not (entry.is_dir() and TRIAL_NAME.fullmatch(entry.name)):
            errors.append(f"{entry}: unexpected entry under {TRIALS_DIR}/")
            continue
        nested = sorted(child.name for child in entry.iterdir())
        if nested != [case_dir.name]:
            errors.append(f"{entry}: must contain only {case_dir.name}/")
            continue
        found.append((int(entry.name), entry / case_dir.name))
    return sorted(found), errors


def _missing_definitions(case_dir: Path) -> list[str]:
    return [
        f"{case_dir}: missing definition file {name}"
        for name in REQUIRED_DEFINITION_FILES
        if not (case_dir / name).is_file()
    ]


def prepare_trial(case_dir: Path, trial: int) -> Path:
    missing = _missing_definitions(case_dir)
    if missing:
        raise ValueError("; ".join(missing))
    existing, errors = scan_trials(case_dir)
    if errors:
        raise ValueError("; ".join(errors))
    expected = len(existing) + 1
    if trial != expected:
        raise ValueError(f"next trial for {case_dir.name} must be {expected}")
    target = trial_dir(case_dir, trial)
    target.parent.parent.mkdir(exist_ok=True)
    # Build beside the target and rename, so a failed copy leaves nothing.
    with tempfile.TemporaryDirectory(dir=target.parent.parent) as raw:
        staging = Path(raw) / case_dir.name
        staging.mkdir()
        for name in REQUIRED_DEFINITION_FILES:
            shutil.copy2(case_dir / name, staging / name)
        target.parent.mkdir()
        try:
            staging.rename(target)
        except OSError:
            target.parent.rmdir()
            raise
    return target


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_aggregate(case_dir: Path) -> dict:
    """Rebuild the aggregate from trial results; raises ValueError if incomplete."""
    try:
        variants = _read_json(case_dir / "variants.json")
        required = variant_ids(variants)
        trials = []
        for number, path in scan_trials(case_dir)[0]:
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
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"{case_dir}: cannot build aggregate: {exc!r}") from exc
    means = (
        {
            variant: round(sum(t["scores"][variant] for t in trials) / len(trials), 2)
            for variant in required
        }
        if trials
        else {}
    )
    ranked = sorted(means.items(), key=lambda item: item[1], reverse=True)
    winner = (
        ranked[0][0] if len(ranked) > 1 and ranked[0][1] > ranked[1][1] else None
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


def validate_trial_set(
    case_dir: Path,
    *,
    require_current_source: bool,
) -> tuple[dict | None, list[str]]:
    """Validate every trial and rebuild the aggregate, without reading aggregate.json."""
    # Imported here to avoid a cycle: the CLI dispatches between both modules.
    from .case import validate_case

    errors = _missing_definitions(case_dir)
    if errors:
        return None, errors
    trials, errors = scan_trials(case_dir)
    if len(trials) < MIN_TRIALS:
        errors.append(
            f"{case_dir}: repeated-trial evidence needs at least {MIN_TRIALS} "
            f"trials, found {len(trials)}"
        )
    numbers = [number for number, _ in trials]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"{case_dir}: trials must be numbered 1..n without gaps")
    for _, path in trials:
        for name in REQUIRED_DEFINITION_FILES:
            copy = path / name
            if not copy.is_file() or copy.read_bytes() != (case_dir / name).read_bytes():
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
        return None, errors
    try:
        aggregate = build_aggregate(case_dir)
    except ValueError as exc:
        return None, [str(exc)]
    seeds = [trial["seed_sha256"] for trial in aggregate["trials"]]
    if None in seeds or len(set(seeds)) != len(seeds):
        return None, [f"{case_dir}: every trial needs its own blind seed"]
    return aggregate, []


def validate_trials(
    case_dir: Path,
    *,
    require_current_source: bool,
    require_win: bool = True,
) -> list[str]:
    aggregate, errors = validate_trial_set(
        case_dir, require_current_source=require_current_source
    )
    if errors or aggregate is None:
        return errors
    aggregate_path = case_dir / AGGREGATE_FILE
    try:
        recorded = _read_json(aggregate_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{aggregate_path}: {exc}"]
    if recorded != aggregate:
        errors.append(f"{aggregate_path}: must match the recorded trial results")
    if require_current_source and require_win:
        means = aggregate["mean_scores"]
        if aggregate["mean_winner"] != "design-craft" or not all(
            means["design-craft"] > score
            for variant, score in means.items()
            if variant != "design-craft"
        ):
            errors.append(
                f"{aggregate_path}: certification requires design-craft to have "
                "the highest mean score across trials"
            )
    return errors
