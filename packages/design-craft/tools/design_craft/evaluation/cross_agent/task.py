from __future__ import annotations

from pathlib import Path

from tools.design_craft.repo import REPO_ROOT

from .contract import (
    HOSTS,
    load_evidence_status,
    read_text,
    sha256_text,
    validate_task_definition,
)
from .history import validate_historical_task_definition
from .output import validate_output
from .score import validate_observed_score


def observed_hosts(task_dir: Path) -> set[str]:
    return {
        host
        for host in HOSTS
        if (task_dir / f"{host}-output.md").is_file()
        and (task_dir / f"score.{host}.json").is_file()
    }


def validate_observed_task(
    task_dir: Path,
    required_hosts: tuple[str, ...] = (),
    *,
    skill_root: Path = REPO_ROOT / "skills/design-craft",
    require_current_schema: bool = False,
    require_current_source: bool = False,
    historical: bool = False,
    require_any_observed: bool = False,
) -> list[str]:
    errors = (
        validate_historical_task_definition(task_dir)
        if historical
        else validate_task_definition(task_dir)
    )
    if errors:
        return errors

    prompt_path = task_dir / "prompt.md"
    prompt_hash = sha256_text(read_text(prompt_path))
    observed = observed_hosts(task_dir)
    if require_any_observed and not observed:
        errors.append(f"{task_dir}: at least one observed host is required")
    states: dict[str, str] = {}
    if not historical:
        states, status_errors = load_evidence_status(
            task_dir / "evidence-status.json"
        )
        errors.extend(status_errors)

    for host in HOSTS:
        output_path = task_dir / f"{host}-output.md"
        score_path = task_dir / f"score.{host}.json"
        unverified_path = task_dir / f"{host}-unverified.md"
        has_any_observed = output_path.exists() or score_path.exists()
        if has_any_observed:
            errors.extend(validate_output(task_dir, host))
            errors.extend(
                validate_observed_score(
                    task_dir,
                    host,
                    prompt_hash,
                    skill_root=skill_root,
                    require_current_schema=require_current_schema,
                    require_current_source=require_current_source,
                )
            )
            if historical:
                if unverified_path.exists():
                    errors.append(
                        f"{unverified_path}: remove stale unverified note after "
                        "recording an observed run"
                    )
            elif states.get(host) != "observed":
                errors.append(
                    f"{task_dir / 'evidence-status.json'}: "
                    f"hosts.{host}.status must be observed"
                )
        elif historical:
            if not unverified_path.is_file():
                errors.append(
                    f"{unverified_path}: missing explicit {host} unverified note"
                )
            else:
                text = read_text(unverified_path).lower()
                if "unverified" not in text or "reason" not in text:
                    errors.append(
                        f"{unverified_path}: must record {host} as unverified "
                        "with a reason"
                    )
        else:
            state = states.get(host)
            if state not in {"pending", "unverified"}:
                errors.append(
                    f"{task_dir / 'evidence-status.json'}: hosts.{host}.status "
                    "must be pending or unverified without observed artifacts"
                )

    for host in required_hosts:
        if host not in observed:
            errors.append(f"{task_dir}: required observed host is missing: {host}")

    if historical:
        comparison_path = task_dir / "comparison.md"
        if not comparison_path.is_file():
            errors.append(f"{comparison_path}: missing comparison summary")
            return errors
        comparison = read_text(comparison_path).lower()
        if len(comparison.strip()) < 80:
            errors.append(f"{comparison_path}: comparison summary is too sparse")
        for term in HOSTS:
            if term not in comparison:
                errors.append(f"{comparison_path}: comparison must mention {term}")
    return errors
