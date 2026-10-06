#!/usr/bin/env python3
"""Validate complete L4 before/after eval case directories."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from design_craft_browser_evidence import validate_score_json  # noqa: E402
from design_craft_l4_evidence_manifest import first_present, validate_manifest  # noqa: E402


REQUIRED_FILES = (
    "input.md",
    "score.before.json",
    "score.after.json",
    "diff-summary.md",
    "validation.md",
    "screenshots.json",
)
PLACEHOLDER_PATTERN = re.compile(r"\bTODO\b|template only|replace this|<case>", re.I)


def read_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"{path}: invalid JSON: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{path}: JSON root must be an object"]
    return payload, []


def score_entry(payload: dict[str, Any]) -> dict[str, Any]:
    cases = payload.get("cases")
    if isinstance(cases, list) and cases and isinstance(cases[0], dict):
        return cases[0]
    return payload


def artifact_items(value: Any) -> list[Any]:
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, list):
        return value
    return []


def phase_evidence_sets(payload: dict[str, Any], phase: str) -> tuple[set[str], set[tuple[int, int]]]:
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return set(), set()
    phase_payload = artifacts.get(phase)
    hashes: set[str] = set()
    dimensions: set[tuple[int, int]] = set()
    for artifact in artifact_items(phase_payload):
        if not isinstance(artifact, dict):
            continue
        digest = first_present(artifact, "sha256", "artifact_sha256")
        if isinstance(digest, str):
            hashes.add(digest)
        dims = artifact.get("dimensions")
        if (
            isinstance(dims, list)
            and len(dims) == 2
            and all(isinstance(item, int) for item in dims)
        ):
            dimensions.add((dims[0], dims[1]))
    return hashes, dimensions


def text_has_placeholder(path: Path) -> bool:
    try:
        return bool(PLACEHOLDER_PATTERN.search(path.read_text(encoding="utf-8")))
    except OSError:
        return False


def json_has_placeholder(payload: Any) -> bool:
    if isinstance(payload, str):
        return bool(PLACEHOLDER_PATTERN.search(payload))
    if isinstance(payload, list):
        return any(json_has_placeholder(item) for item in payload)
    if isinstance(payload, dict):
        return any(json_has_placeholder(item) for item in payload.values())
    return False


def validate_score_phase(
    case_dir: Path,
    score_path: Path,
    screenshots: dict[str, Any],
    phase: str,
) -> list[str]:
    errors: list[str] = []
    payload, json_errors = read_json(score_path)
    if payload is None:
        return json_errors
    entry = score_entry(payload)
    case_label = entry.get("case_id") or payload.get("case_id") or score_path.name
    if (entry.get("evidence_level") or payload.get("evidence_level")) != "L4":
        errors.append(f"{score_path}: {case_label} evidence_level must be L4")
    hashes, dimensions = phase_evidence_sets(screenshots, phase)
    digest = entry.get("screenshot_sha256")
    if digest not in hashes:
        errors.append(f"{score_path}: {case_label} screenshot_sha256 must match screenshots.json artifacts.{phase}")
    dims = entry.get("screenshot_dimensions")
    if not isinstance(dims, list) or len(dims) != 2 or tuple(dims) not in dimensions:
        errors.append(f"{score_path}: {case_label} screenshot_dimensions must match screenshots.json artifacts.{phase}")
    if json_has_placeholder(payload):
        errors.append(f"{score_path}: {case_label} contains template/TODO placeholder text")
    return errors


def validate_case_dir(case_dir: Path, *, strict: bool, require_existing_files: bool) -> list[str]:
    errors: list[str] = []
    if not case_dir.is_dir():
        return [f"{case_dir}: case directory does not exist"]
    for name in REQUIRED_FILES:
        if not case_dir.joinpath(name).is_file():
            errors.append(f"{case_dir}: missing required file {name}")
    if errors:
        return errors

    screenshots_path = case_dir / "screenshots.json"
    errors.extend(
        validate_manifest(
            screenshots_path,
            strict=strict,
            require_existing_files=require_existing_files,
        )
    )

    screenshots, json_errors = read_json(screenshots_path)
    errors.extend(json_errors)
    if screenshots is None:
        return errors

    if strict:
        for markdown_name in ("input.md", "diff-summary.md", "validation.md"):
            markdown_path = case_dir / markdown_name
            if text_has_placeholder(markdown_path):
                errors.append(f"{markdown_path}: contains template/TODO placeholder text")
            if markdown_path.stat().st_size < 80:
                errors.append(f"{markdown_path}: strict L4 case file is too sparse")

        for score_name in ("score.before.json", "score.after.json"):
            score_path = case_dir / score_name
            errors.extend(validate_score_json(score_path))

        errors.extend(validate_score_phase(case_dir, case_dir / "score.before.json", screenshots, "before"))
        errors.extend(validate_score_phase(case_dir, case_dir / "score.after.json", screenshots, "after"))

        before_payload, before_errors = read_json(case_dir / "score.before.json")
        after_payload, after_errors = read_json(case_dir / "score.after.json")
        errors.extend(before_errors)
        errors.extend(after_errors)
        if before_payload is not None and after_payload is not None:
            before_score = score_entry(before_payload).get("expected_score")
            after_score = score_entry(after_payload).get("expected_score")
            if not isinstance(before_score, int) or not isinstance(after_score, int):
                errors.append(f"{case_dir}: before and after expected_score must be integers")
            elif after_score <= before_score:
                errors.append(f"{case_dir}: after expected_score must be greater than before expected_score")
    return errors


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def make_valid_case(root: Path) -> Path:
    case_dir = root / "valid"
    case_dir.mkdir(parents=True)
    digest_before = "a" * 64
    digest_after = "b" * 64
    common_viewports = [
        {
            "name": "desktop",
            "css_size": [1440, 900],
            "dimensions": [1440, 900],
            "artifact_sha256": digest_after,
            "horizontal_overflow": False,
        },
        {
            "name": "mobile",
            "css_size": [390, 844],
            "dimensions": [780, 1688],
            "artifact_sha256": "c" * 64,
            "horizontal_overflow": False,
        },
    ]
    (case_dir / "input.md").write_text(
        "# Generic L4 eval\n\nBefore and after evidence is captured from a generic local workbench.\n",
        encoding="utf-8",
    )
    (case_dir / "diff-summary.md").write_text(
        "# Diff summary\n\nChanged the generic workbench hierarchy and compacted the primary review surface.\n",
        encoding="utf-8",
    )
    (case_dir / "validation.md").write_text(
        "# Validation\n\nRan screenshot manifest, score JSON, and case directory validation commands.\n",
        encoding="utf-8",
    )
    write_json(
        case_dir / "screenshots.json",
        {
            "schema": "design-craft.l4-screenshots.v1",
            "case_id": "generic-l4-valid",
            "artifacts": {
                "before": {
                    "desktop": {
                        "tool": "tmwd_browser.browser_screenshot_ops",
                        "target": "viewport",
                        "path": "/tmp/generic-before.png",
                        "sha256": digest_before,
                        "dimensions": [1440, 900],
                        "viewport": {"width": 1440, "height": 900, "dpr": 1},
                    }
                },
                "after": {
                    "desktop": {
                        "tool": "tmwd_browser.browser_screenshot_ops",
                        "target": "viewport",
                        "path": "/tmp/generic-after.png",
                        "sha256": digest_after,
                        "dimensions": [1440, 900],
                        "viewport": {"width": 1440, "height": 900, "dpr": 1},
                    }
                },
            },
        },
    )
    base_score = {
        "evidence_level": "L4",
        "acceptable_range": [76, 92],
        "maturity_band": "production-ready calibration",
        "responsive_viewports": common_viewports,
        "state_checks": {"focus": "verified", "empty": "not applicable to fixture"},
        "required_findings": ["specific hierarchy finding", "specific rhythm finding", "specific state finding"],
        "false_positive_guards": ["guard one", "guard two", "guard three"],
    }
    write_json(
        case_dir / "score.before.json",
        {
            **base_score,
            "case_id": "generic-l4-valid-before",
            "expected_score": 78,
            "screenshot_sha256": digest_before,
            "screenshot_dimensions": [1440, 900],
        },
    )
    write_json(
        case_dir / "score.after.json",
        {
            **base_score,
            "case_id": "generic-l4-valid-after",
            "expected_score": 90,
            "screenshot_sha256": digest_after,
            "screenshot_dimensions": [1440, 900],
        },
    )
    return case_dir


def run_self_check() -> list[str]:
    temp_root = Path(tempfile.mkdtemp(prefix="design-craft-l4-case-"))
    try:
        valid_case = make_valid_case(temp_root)
        errors = validate_case_dir(valid_case, strict=True, require_existing_files=False)
        invalid_case = temp_root / "invalid"
        shutil.copytree(valid_case, invalid_case)
        (invalid_case / "validation.md").write_text("# Validation\n\n- TODO\n", encoding="utf-8")
        invalid_errors = validate_case_dir(invalid_case, strict=True, require_existing_files=False)
        if not any("placeholder" in error for error in invalid_errors):
            errors.append("self-check failed to reject placeholder validation.md")
        return errors
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate design-craft L4 before/after case directories.")
    parser.add_argument("--check", action="store_true", help="Run built-in validator self-checks.")
    parser.add_argument("--case-dir", action="append", default=[], help="Validate a before/after case directory.")
    parser.add_argument("--strict", action="store_true", help="Require completed real L4 evidence instead of scaffold placeholders.")
    parser.add_argument("--require-existing-files", action="store_true", help="Require screenshot artifact paths to exist locally.")
    args = parser.parse_args()

    if not args.check and not args.case_dir:
        parser.print_help(sys.stderr)
        return 2

    errors: list[str] = []
    if args.check:
        errors.extend(run_self_check())
    for item in args.case_dir:
        errors.extend(
            validate_case_dir(
                Path(item),
                strict=args.strict,
                require_existing_files=args.require_existing_files,
            )
        )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
