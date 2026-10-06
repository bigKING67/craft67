from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from .assurance import ASSURANCE_LEVELS
from .constants import PROFILES, REVIEW_MODES, SCORE_DIMENSIONS, SEMANTIC_CLAIM_LEVELS
from .jsonio import json_pointer_tokens, read_json

COMMAND_FIELDS = {"argv", "cwd", "timeoutSeconds", "evidenceClaims", "artifacts"}
EVIDENCE_ID_PATTERN = re.compile(r"[a-z][a-z0-9_-]{0,63}")
DEFAULT_ARTIFACT_MAX_BYTES = 50 * 1024 * 1024


def default_config() -> dict[str, Any]:
    return {
        "mode": "review",
        "assuranceLevel": "standard",
        "profile": "auto",
        "focusDimensions": [],
        "diffBase": None,
        "scope": ["."],
        "exclude": [],
        "generated": [],
        "vendored": [],
        "commands": {},
        "policy": {
            "allowNetwork": False,
            "allowInstall": False,
            "allowRepositoryMutation": False,
            "outputOutsideRepository": True,
        },
        "reportLanguage": "zh-CN",
    }


def validate_config(config: dict[str, Any]) -> None:
    for field in ("scope", "exclude", "generated", "vendored"):
        if not isinstance(config[field], list) or not all(
            isinstance(item, str) and item for item in config[field]
        ):
            raise ValueError(f"config.{field}: expected an array of strings")
    if not config["scope"]:
        raise ValueError("config.scope: must not be empty")
    if config["mode"] not in REVIEW_MODES:
        raise ValueError(f"config.mode: expected one of {', '.join(sorted(REVIEW_MODES))}")
    if config["assuranceLevel"] not in ASSURANCE_LEVELS:
        raise ValueError(
            f"config.assuranceLevel: expected one of {', '.join(sorted(ASSURANCE_LEVELS))}"
        )
    if config["profile"] not in PROFILES:
        raise ValueError(f"config.profile: expected one of {', '.join(sorted(PROFILES))}")
    focus_dimensions = config["focusDimensions"]
    valid_dimensions = {row[0] for row in SCORE_DIMENSIONS}
    if not isinstance(focus_dimensions, list) or not all(
        isinstance(item, str) and item in valid_dimensions for item in focus_dimensions
    ):
        raise ValueError("config.focusDimensions: expected canonical score dimension IDs")
    if len(focus_dimensions) != len(set(focus_dimensions)):
        raise ValueError("config.focusDimensions: duplicate dimension")
    if config["diffBase"] is not None and not (
        isinstance(config["diffBase"], str) and config["diffBase"].strip()
    ):
        raise ValueError("config.diffBase: expected a non-empty string or null")
    if config["reportLanguage"] != "zh-CN":
        raise ValueError("config.reportLanguage: only zh-CN is supported")
    _validate_commands(config["commands"])


def _validate_commands(commands: Any) -> None:
    if not isinstance(commands, dict):
        raise ValueError("config.commands: expected an object")
    for name, command in commands.items():
        _validate_command(name, command)


def _validate_command(name: Any, command: Any) -> None:
    if (
        not isinstance(name, str)
        or re.fullmatch(r"[a-z][a-z0-9_-]*", name) is None
        or not isinstance(command, dict)
    ):
        raise ValueError(f"config.commands.{name}: invalid command")
    unknown_command_fields = set(command) - COMMAND_FIELDS
    if unknown_command_fields:
        raise ValueError(
            f"config.commands.{name}: unsupported fields "
            f"{', '.join(sorted(unknown_command_fields))}"
        )
    argv = command.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(item, str) and item and "\0" not in item for item in argv)
    ):
        raise ValueError(f"config.commands.{name}.argv: expected a non-empty string array")
    cwd = command.get("cwd", ".")
    if not isinstance(cwd, str) or not cwd:
        raise ValueError(f"config.commands.{name}.cwd: expected a string")
    timeout = command.get("timeoutSeconds", 600)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise ValueError(f"config.commands.{name}.timeoutSeconds: expected a positive integer")
    _validate_evidence_claims(name, command.get("evidenceClaims", []))
    _validate_evidence_artifacts(name, command.get("artifacts", []))


def _valid_evidence_id(value: Any) -> bool:
    return isinstance(value, str) and EVIDENCE_ID_PATTERN.fullmatch(value) is not None


def _validate_pointer(value: Any, field: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field}: expected an RFC 6901 JSON pointer")
    try:
        json_pointer_tokens(value)
    except ValueError as error:
        raise ValueError(f"{field}: {error}") from error


def _validate_evidence_claims(command_name: str, claims: Any) -> None:
    prefix = f"config.commands.{command_name}.evidenceClaims"
    if not isinstance(claims, list) or len(claims) > 32:
        raise ValueError(f"{prefix}: expected an array with at most 32 entries")
    identifiers: set[str] = set()
    for index, claim in enumerate(claims):
        field = f"{prefix}[{index}]"
        if not isinstance(claim, dict):
            raise ValueError(f"{field}: expected an object")
        unknown = set(claim) - {"id", "kind", "jsonPointer", "equals"}
        if unknown:
            raise ValueError(f"{field}: unsupported fields {', '.join(sorted(unknown))}")
        identifier = claim.get("id")
        if not _valid_evidence_id(identifier):
            raise ValueError(f"{field}.id: expected a lowercase evidence identifier")
        if identifier in identifiers:
            raise ValueError(f"{prefix}: duplicate id {identifier}")
        identifiers.add(identifier)
        if claim.get("kind") not in SEMANTIC_CLAIM_LEVELS:
            raise ValueError(
                f"{field}.kind: expected one of {', '.join(sorted(SEMANTIC_CLAIM_LEVELS))}"
            )
        _validate_pointer(claim.get("jsonPointer"), f"{field}.jsonPointer")
        if "equals" not in claim or isinstance(claim["equals"], (dict, list)):
            raise ValueError(f"{field}.equals: expected a JSON scalar")


def _validate_evidence_artifacts(command_name: str, artifacts: Any) -> None:
    prefix = f"config.commands.{command_name}.artifacts"
    if not isinstance(artifacts, list) or len(artifacts) > 16:
        raise ValueError(f"{prefix}: expected an array with at most 16 entries")
    identifiers: set[str] = set()
    for index, artifact in enumerate(artifacts):
        field = f"{prefix}[{index}]"
        if not isinstance(artifact, dict):
            raise ValueError(f"{field}: expected an object")
        unknown = set(artifact) - {
            "id",
            "pathJsonPointer",
            "sha256JsonPointer",
            "sizeBytesJsonPointer",
            "maxBytes",
        }
        if unknown:
            raise ValueError(f"{field}: unsupported fields {', '.join(sorted(unknown))}")
        identifier = artifact.get("id")
        if not _valid_evidence_id(identifier):
            raise ValueError(f"{field}.id: expected a lowercase evidence identifier")
        if identifier in identifiers:
            raise ValueError(f"{prefix}: duplicate id {identifier}")
        identifiers.add(identifier)
        _validate_pointer(artifact.get("pathJsonPointer"), f"{field}.pathJsonPointer")
        for pointer_field in ("sha256JsonPointer", "sizeBytesJsonPointer"):
            if pointer_field in artifact:
                _validate_pointer(artifact[pointer_field], f"{field}.{pointer_field}")
        maximum = artifact.get("maxBytes", DEFAULT_ARTIFACT_MAX_BYTES)
        if (
            not isinstance(maximum, int)
            or isinstance(maximum, bool)
            or not 1 <= maximum <= 1024 * 1024 * 1024
        ):
            raise ValueError(f"{field}.maxBytes: expected an integer from 1 to 1073741824")


def load_config(path: Path | None) -> dict[str, Any]:
    config = default_config()
    if path is not None:
        supplied = read_json(path.expanduser().resolve(strict=True))
        if not isinstance(supplied, dict):
            raise ValueError("config: expected a JSON object")
        supplied = {key: value for key, value in supplied.items() if key != "$schema"}
        unknown = set(supplied) - set(config)
        if unknown:
            raise ValueError(f"config: unsupported fields {', '.join(sorted(unknown))}")
        for key, value in supplied.items():
            if key == "policy":
                if not isinstance(value, dict):
                    raise ValueError("config.policy: expected an object")
                unknown_policy = set(value) - set(config["policy"])
                if unknown_policy:
                    raise ValueError(
                        f"config.policy: unsupported fields {', '.join(sorted(unknown_policy))}"
                    )
                if not all(isinstance(item, bool) for item in value.values()):
                    raise ValueError("config.policy: expected boolean values")
                config["policy"].update(value)
            else:
                config[key] = value
    validate_config(config)
    return config


def focus_values(values: list[str] | None) -> list[str]:
    if not values:
        return []
    requested = {item.strip() for value in values for item in value.split(",") if item.strip()}
    valid = [row[0] for row in SCORE_DIMENSIONS]
    unknown = sorted(requested - set(valid))
    if unknown:
        raise ValueError(f"--focus: unsupported dimensions {', '.join(unknown)}")
    return [identifier for identifier in valid if identifier in requested]


def effective_preflight_config(
    config: dict[str, Any],
    *,
    mode: str | None,
    base: str | None,
    focus: list[str] | None,
    assurance: str | None,
) -> tuple[dict[str, Any], str | None]:
    effective = copy.deepcopy(config)
    if mode:
        effective["mode"] = mode
    if assurance:
        effective["assuranceLevel"] = assurance
    if base:
        if mode and mode != "diff":
            raise ValueError("--base can only be used with --mode diff")
        effective["mode"] = "diff"
        effective["diffBase"] = base
    selected_focus = focus_values(focus)
    if selected_focus:
        effective["focusDimensions"] = selected_focus
        if effective["mode"] == "review":
            effective["mode"] = "focus"
    validate_config(effective)
    effective_mode = effective["mode"]
    if effective_mode == "diff" and not effective["diffBase"]:
        raise ValueError("diff mode requires --base or config.diffBase")
    if effective_mode != "diff" and effective["diffBase"] is not None:
        raise ValueError("config.diffBase is only valid in diff mode")
    if effective_mode == "focus" and not effective["focusDimensions"]:
        raise ValueError("focus mode requires --focus or config.focusDimensions")
    if effective_mode == "review" and effective["focusDimensions"]:
        raise ValueError("review mode cannot declare focus dimensions")
    return effective, effective["diffBase"]
