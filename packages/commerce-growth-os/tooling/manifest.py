"""Load and validate the stable, repository-level Skill pack manifest schema."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SUPPORTED_SCHEMA_VERSION = 2
_SEMVER_PATTERN = re.compile(r"\A(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\Z")
_SKILL_NAME_PATTERN = re.compile(r"\A[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class ManifestError(ValueError):
    """Raised when a manifest does not satisfy the shared base schema."""


def parse_semantic_version(value: object, *, field: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not _SEMVER_PATTERN.fullmatch(value):
        raise ManifestError(f"{field} must be a semantic version in MAJOR.MINOR.PATCH form")
    major, minor, patch = value.split(".")
    return int(major), int(minor), int(patch)


def _require_nonempty_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"manifest {field} must be a non-empty string")
    return value


def _validate_resources(skill: dict[str, Any], name: str) -> None:
    resources = skill.get("resources", [])
    if not isinstance(resources, list):
        raise ManifestError(f"resources for {name} must be a list")

    targets: set[str] = set()
    for index, resource in enumerate(resources):
        if not isinstance(resource, dict) or set(resource) != {"source", "target"}:
            raise ManifestError(f"invalid resource mapping for {name} at index {index}")
        source = resource["source"]
        target = resource["target"]
        if not isinstance(source, str) or not source.strip():
            raise ManifestError(f"resource source for {name} at index {index} must be a non-empty string")
        if not isinstance(target, str) or not target.strip():
            raise ManifestError(f"resource target for {name} at index {index} must be a non-empty string")
        if target in targets:
            raise ManifestError(f"duplicate resource target for {name}: {target}")
        targets.add(target)


def _validate_skills(payload: dict[str, Any]) -> None:
    skills = payload.get("skills")
    if not isinstance(skills, list) or not skills:
        raise ManifestError("manifest must define a non-empty skills list")

    names: set[str] = set()
    for index, skill in enumerate(skills):
        if not isinstance(skill, dict):
            raise ManifestError(f"skill at index {index} must be an object")
        name = skill.get("name")
        if not isinstance(name, str) or not _SKILL_NAME_PATTERN.fullmatch(name):
            raise ManifestError(f"skill at index {index} has an invalid name: {name!r}")
        if name in names:
            raise ManifestError(f"manifest contains duplicate skill name: {name}")
        names.add(name)

        source = skill.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ManifestError(f"source for {name} must be a non-empty string")

        routing_terms = skill.get("routing_terms", [])
        if not isinstance(routing_terms, list) or any(
            not isinstance(term, str) or not term.strip() for term in routing_terms
        ):
            raise ManifestError(f"routing_terms for {name} must be a list of non-empty strings")
        _validate_resources(skill, name)


def load_manifest(path: Path) -> dict[str, Any]:
    """Return a manifest validated against shared schema, not release policy."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid manifest JSON at line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(payload, dict):
        raise ManifestError("manifest root must be an object")
    schema_version = payload.get("schema_version")
    if type(schema_version) is not int or schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ManifestError(f"unsupported manifest schema: {schema_version!r}")

    _require_nonempty_string(payload, "pack_name")
    parse_semantic_version(payload.get("pack_version"), field="pack_version")
    parse_semantic_version(payload.get("minimum_installer_version"), field="minimum_installer_version")
    _require_nonempty_string(payload, "default_install_root")

    duplicate_roots = payload.get("duplicate_discovery_roots", [])
    if not isinstance(duplicate_roots, list) or any(
        not isinstance(root, str) or not root.strip() for root in duplicate_roots
    ):
        raise ManifestError("duplicate_discovery_roots must be a list of non-empty strings")

    _validate_skills(payload)
    return payload
