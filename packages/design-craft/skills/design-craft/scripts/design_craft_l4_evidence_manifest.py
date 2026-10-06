#!/usr/bin/env python3
"""Validate L4 before/after screenshot evidence manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA = "design-craft.l4-screenshots.v1"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SECRET_PATTERNS = [
    re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", re.I),
    re.compile(r"\b(?:sk|pk|ak|api|token|secret|key)[-_]?[A-Za-z0-9]{12,}\b", re.I),
    re.compile(r"data:image/[a-z0-9.+-]+;base64,", re.I),
]
VALID_TARGETS = {"viewport", "selector", "clip", "full_page"}


def is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and value > 0


def valid_dimension_pair(value: Any, *, allow_zero: bool = False) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) and (item > 0 or (allow_zero and item == 0)) for item in value)
    )


def valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_PATTERN.fullmatch(value))


def first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(walk_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(walk_strings(item))
        return result
    return []


def phase_items(value: Any) -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        return [(str(key), item) for key, item in value.items()]
    if isinstance(value, list):
        return [(str(index), item) for index, item in enumerate(value)]
    return []


def validate_viewport(path: Path, label: str, value: Any, *, strict: bool) -> list[str]:
    errors: list[str] = []
    if value in (None, "") and not strict:
        return errors
    if not isinstance(value, dict):
        return [f"{path}: {label}.viewport must be an object"]
    for key in ("width", "height", "dpr"):
        item = value.get(key)
        if strict and not is_positive_number(item):
            errors.append(f"{path}: {label}.viewport.{key} must be positive")
        if not strict and item not in (None, 0) and not is_positive_number(item):
            errors.append(f"{path}: {label}.viewport.{key} must be positive when provided")
    if "is_mobile" in value and not isinstance(value.get("is_mobile"), bool):
        errors.append(f"{path}: {label}.viewport.is_mobile must be boolean when provided")
    return errors


def validate_layout_metrics(path: Path, label: str, value: Any) -> list[str]:
    errors: list[str] = []
    if value in (None, ""):
        return errors
    if not isinstance(value, dict):
        return [f"{path}: {label}.layout_metrics must be an object when provided"]
    if "horizontal_overflow" in value and not isinstance(value.get("horizontal_overflow"), bool):
        errors.append(f"{path}: {label}.layout_metrics.horizontal_overflow must be boolean")
    selectors = value.get("selectors")
    if selectors is not None and not isinstance(selectors, dict):
        errors.append(f"{path}: {label}.layout_metrics.selectors must be an object when provided")
    return errors


def validate_artifact(
    path: Path,
    label: str,
    artifact: Any,
    *,
    strict: bool,
    require_existing_files: bool,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(artifact, dict):
        return [f"{path}: {label} must be an object"]

    if strict:
        for key in ("tool", "target", "dimensions", "viewport"):
            if key not in artifact:
                errors.append(f"{path}: {label} missing required field {key}")
        if "path" not in artifact and "artifact_path" not in artifact:
            errors.append(f"{path}: {label} missing required field path or artifact_path")
        if "sha256" not in artifact and "artifact_sha256" not in artifact:
            errors.append(f"{path}: {label} missing required field sha256 or artifact_sha256")

    tool = artifact.get("tool")
    if strict and not (isinstance(tool, str) and tool and tool != "TODO"):
        errors.append(f"{path}: {label}.tool must name the capture tool")

    target = artifact.get("target")
    if target not in (None, "") and target not in VALID_TARGETS:
        errors.append(f"{path}: {label}.target must be one of {sorted(VALID_TARGETS)}")
    if strict and target not in VALID_TARGETS:
        errors.append(f"{path}: {label}.target is required")

    artifact_path = first_present(artifact, "path", "artifact_path")
    if strict and not (isinstance(artifact_path, str) and artifact_path and artifact_path != "TODO"):
        errors.append(f"{path}: {label}.path must point to a repo-external screenshot artifact")
    if isinstance(artifact_path, str) and artifact_path.startswith("data:"):
        errors.append(f"{path}: {label}.path must not embed data URLs or base64")
    if require_existing_files and isinstance(artifact_path, str) and artifact_path and artifact_path != "TODO":
        if not Path(artifact_path).expanduser().exists():
            errors.append(f"{path}: {label}.path does not exist: {artifact_path}")

    sha256 = first_present(artifact, "sha256", "artifact_sha256")
    if strict and not valid_sha256(sha256):
        errors.append(f"{path}: {label}.sha256 must be a lowercase 64-character SHA-256")
    if not strict and sha256 not in (None, "") and not valid_sha256(sha256):
        errors.append(f"{path}: {label}.sha256 must be a lowercase 64-character SHA-256 when provided")

    dimensions = artifact.get("dimensions")
    if strict and not valid_dimension_pair(dimensions):
        errors.append(f"{path}: {label}.dimensions must be two positive integers")
    if not strict and dimensions is not None and not valid_dimension_pair(dimensions, allow_zero=True):
        errors.append(f"{path}: {label}.dimensions must be two integers when provided")

    errors.extend(validate_viewport(path, label, artifact.get("viewport"), strict=strict))
    errors.extend(validate_layout_metrics(path, label, artifact.get("layout_metrics")))
    return errors


def validate_manifest(path: Path, *, strict: bool, require_existing_files: bool) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]

    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{path}: manifest must be an object"]
    if payload.get("schema") != SCHEMA:
        errors.append(f"{path}: schema must be {SCHEMA}")
    case_id = payload.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        errors.append(f"{path}: case_id is required")
    if strict and str(case_id).lower() in {"todo", "template"}:
        errors.append(f"{path}: strict manifest case_id cannot be template/TODO")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return errors + [f"{path}: artifacts must be an object"]
    phase_names = ("before", "after")
    phase_keys: dict[str, set[str]] = {}
    for phase in phase_names:
        phase_payload = artifacts.get(phase)
        if phase_payload is None:
            errors.append(f"{path}: artifacts.{phase} is required")
            continue
        items = phase_items(phase_payload)
        if strict and not items:
            errors.append(f"{path}: artifacts.{phase} must include at least one screenshot artifact")
        if not isinstance(phase_payload, (dict, list)):
            errors.append(f"{path}: artifacts.{phase} must be an object or list")
            continue
        phase_keys[phase] = {key for key, _ in items}
        for key, artifact in items:
            errors.extend(
                validate_artifact(
                    path,
                    f"artifacts.{phase}.{key}",
                    artifact,
                    strict=strict,
                    require_existing_files=require_existing_files,
                )
            )

    if strict and all(phase in phase_keys for phase in phase_names):
        if not (phase_keys["before"] & phase_keys["after"]):
            errors.append(f"{path}: strict manifests need at least one shared before/after artifact key")

    layout_delta = payload.get("layout_delta")
    if layout_delta is not None and not isinstance(layout_delta, dict):
        errors.append(f"{path}: layout_delta must be an object when provided")

    for text in walk_strings(payload):
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path}: possible embedded secret or base64 screenshot: {text[:80]}")
                return errors
    return errors


def run_self_check() -> list[str]:
    valid_payload = {
        "schema": SCHEMA,
        "case_id": "generic-workbench-polish",
        "route": "http://127.0.0.1:4173/example",
        "artifacts": {
            "before": {
                "desktop": {
                    "tool": "tmwd_browser.browser_screenshot_ops",
                    "target": "viewport",
                    "path": "/tmp/before.png",
                    "sha256": "a" * 64,
                    "dimensions": [1200, 800],
                    "viewport": {"width": 1200, "height": 800, "dpr": 1},
                    "layout_metrics": {"horizontal_overflow": False},
                }
            },
            "after": {
                "desktop": {
                    "tool": "tmwd_browser.browser_screenshot_ops",
                    "target": "viewport",
                    "path": "/tmp/after.png",
                    "sha256": "b" * 64,
                    "dimensions": [1200, 800],
                    "viewport": {"width": 1200, "height": 800, "dpr": 1},
                    "layout_metrics": {"horizontal_overflow": False},
                }
            },
        },
        "layout_delta": {},
    }
    with tempfile.NamedTemporaryFile(
        prefix="design-craft-l4-manifest-self-check-",
        suffix=".json",
        delete=False,
    ) as handle:
        tmp = Path(handle.name)
    try:
        tmp.write_text(json.dumps(valid_payload), encoding="utf-8")
        errors = validate_manifest(tmp, strict=True, require_existing_files=False)
        invalid_payload = dict(valid_payload)
        invalid_payload["artifacts"] = {
            "before": {"desktop": {**valid_payload["artifacts"]["before"]["desktop"], "sha256": "bad"}},
            "after": valid_payload["artifacts"]["after"],
        }
        tmp.write_text(json.dumps(invalid_payload), encoding="utf-8")
        invalid_errors = validate_manifest(tmp, strict=True, require_existing_files=False)
        if not any("sha256" in error for error in invalid_errors):
            errors.append("self-check failed to reject invalid sha256")
        invalid_payload["artifacts"] = {
            "before": {
                "desktop": {
                    **valid_payload["artifacts"]["before"]["desktop"],
                    "path": "data:image/png;base64,AAAA",
                    "sha256": "a" * 64,
                    "dimensions": [0, 800],
                    "viewport": {"width": 1200, "height": 800, "dpr": 0},
                    "layout_metrics": {"horizontal_overflow": "false"},
                }
            },
            "after": valid_payload["artifacts"]["after"],
        }
        tmp.write_text(json.dumps(invalid_payload), encoding="utf-8")
        invalid_errors = validate_manifest(tmp, strict=True, require_existing_files=False)
        expected_markers = ("base64", "dimensions", "viewport.dpr", "horizontal_overflow")
        for marker in expected_markers:
            if not any(marker in error for error in invalid_errors):
                errors.append(f"self-check failed to reject invalid {marker}")
        invalid_payload["artifacts"] = {
            "before": valid_payload["artifacts"]["before"],
            "after": {"mobile": valid_payload["artifacts"]["after"]["desktop"]},
        }
        tmp.write_text(json.dumps(invalid_payload), encoding="utf-8")
        invalid_errors = validate_manifest(tmp, strict=True, require_existing_files=False)
        if not any("shared before/after artifact key" in error for error in invalid_errors):
            errors.append("self-check failed to reject non-matching before/after keys")
    finally:
        tmp.unlink(missing_ok=True)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate design-craft L4 screenshot manifests.")
    parser.add_argument("--check", action="store_true", help="Run built-in validator self-checks.")
    parser.add_argument("--validate-screenshots-json", action="append", default=[], help="Validate a screenshots.json manifest.")
    parser.add_argument("--strict", action="store_true", help="Require real evidence fields instead of allowing template placeholders.")
    parser.add_argument("--require-existing-files", action="store_true", help="Also require screenshot artifact paths to exist on this machine.")
    args = parser.parse_args()

    if not args.check and not args.validate_screenshots_json:
        parser.print_help(sys.stderr)
        return 2

    errors: list[str] = []
    if args.check:
        errors.extend(run_self_check())
    for item in args.validate_screenshots_json:
        errors.extend(
            validate_manifest(
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
