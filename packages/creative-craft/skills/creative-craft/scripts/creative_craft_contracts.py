"""Versioned artifact contracts and the portable JSON Schema runtime."""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import math
import os
import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]
TEMPLATES_DIR = SKILL_ROOT / "templates"
PROVIDERS_DIR = SKILL_ROOT / "providers"
SURFACES_DIR = PROVIDERS_DIR / "surfaces"

EVIDENCE_STATES = {
    "SPECIFIED",
    "OBSERVED",
    "INFERRED",
    "HYPOTHESIZED",
    "UNVERIFIED",
}
IMAGE_PROFILE_ID = "openai.gpt-image-2.2026-04-21"
VIDEO_PROFILE_ID = "bytedance.seedance-2.5.2026-07-31"

ARTIFACT_REGISTRY: dict[str, dict[str, Any]] = {
    "creative-craft.brief.v1": {
        "kind": "brief",
        "schema": "creative-brief.schema.json",
        "template": "creative-brief.json",
        "legacy": False,
    },
    "creative-craft.asset-ledger.v1": {
        "kind": "asset-ledger",
        "schema": "asset-ledger.schema.json",
        "template": "asset-ledger.json",
        "legacy": False,
    },
    "creative-craft.concept-routes.v1": {
        "kind": "concept-routes",
        "schema": "concept-routes.schema.json",
        "template": "concept-routes.json",
        "legacy": False,
    },
    "creative-craft.critique.v1": {
        "kind": "critique",
        "schema": "critique.schema.json",
        "template": "critique.json",
        "legacy": False,
    },
    "creative-craft.image-job.v1": {
        "kind": "image",
        "schema": "image-job.schema.json",
        "template": None,
        "legacy": True,
    },
    "creative-craft.video-job.v1": {
        "kind": "video",
        "schema": "video-job.schema.json",
        "template": None,
        "legacy": True,
    },
    "creative-craft.evaluation.v1": {
        "kind": "evaluation",
        "schema": "evaluation.schema.json",
        "template": None,
        "legacy": True,
    },
    "creative-craft.delivery.v1": {
        "kind": "delivery",
        "schema": "delivery-manifest.schema.json",
        "template": None,
        "legacy": True,
    },
    "creative-craft.project-manifest.v1": {
        "kind": "project-manifest",
        "schema": "project-manifest.schema.json",
        "template": None,
        "legacy": True,
    },
    "creative-craft.project-manifest.v2": {
        "kind": "project-manifest",
        "schema": "project-manifest-v2.schema.json",
        "template": "project-manifest.json",
        "legacy": False,
    },
    "creative-craft.creative-direction.v1": {
        "kind": "creative-direction",
        "schema": "creative-direction.schema.json",
        "template": "creative-direction.json",
        "legacy": False,
    },
    "creative-craft.copy-sheet.v1": {
        "kind": "copy-sheet",
        "schema": "copy-sheet.schema.json",
        "template": "copy-sheet.json",
        "legacy": False,
    },
    "creative-craft.image-job.v2": {
        "kind": "image",
        "schema": "image-job-v2.schema.json",
        "template": "image-job.json",
        "legacy": False,
    },
    "creative-craft.video-job.v2": {
        "kind": "video",
        "schema": "video-job-v2.schema.json",
        "template": "video-job.json",
        "legacy": False,
    },
    "creative-craft.execution-receipt.v1": {
        "kind": "execution-receipt",
        "schema": "execution-receipt.schema.json",
        "template": "execution-receipt.json",
        "legacy": False,
    },
    "creative-craft.output-inspection.v1": {
        "kind": "output-inspection",
        "schema": "output-inspection.schema.json",
        "template": "output-inspection.json",
        "legacy": False,
    },
    "creative-craft.revision-lineage.v1": {
        "kind": "revision-lineage",
        "schema": "revision-lineage.schema.json",
        "template": "revision-lineage.json",
        "legacy": False,
    },
    "creative-craft.evaluation.v2": {
        "kind": "evaluation",
        "schema": "evaluation-v2.schema.json",
        "template": "evaluation.json",
        "legacy": False,
    },
    "creative-craft.delivery.v2": {
        "kind": "delivery",
        "schema": "delivery-manifest-v2.schema.json",
        "template": "delivery-manifest.json",
        "legacy": False,
    },
    "creative-craft.brand-pack.v1": {
        "kind": "brand-pack",
        "schema": "brand-pack.schema.json",
        "template": "brand-pack.json",
        "legacy": False,
    },
    "creative-craft.brand-binding.v1": {
        "kind": "brand-binding",
        "schema": "brand-binding.schema.json",
        "template": "brand-binding.json",
        "legacy": False,
    },
    "creative-craft.reference-pack.v1": {
        "kind": "reference-pack",
        "schema": "reference-pack.schema.json",
        "template": "reference-pack.json",
        "legacy": False,
    },
    "creative-craft.reference-binding.v1": {
        "kind": "reference-binding",
        "schema": "reference-binding.schema.json",
        "template": "reference-binding.json",
        "legacy": False,
    },
    "creative-craft.reference-binding-history.v1": {
        "kind": "reference-binding-history",
        "schema": "reference-binding-history.schema.json",
        "template": "reference-binding-history.json",
        "legacy": False,
    },
    "creative-craft.edit-document.v2": {
        "kind": "edit-document",
        "schema": "edit-document-v2.schema.json",
        "template": None,
        "legacy": False,
    },
    "creative-craft.render-qa.v1": {
        "kind": "render-qa",
        "schema": "render-qa.schema.json",
        "template": None,
        "legacy": False,
    },
    "creative-craft.production-plan.v1": {
        "kind": "production-plan",
        "schema": "production-plan.schema.json",
        "template": "production-plan.json",
        "legacy": False,
    },
    "creative-craft.video-production.v1": {
        "kind": "video-production",
        "schema": "video-production.schema.json",
        "template": "video-production.json",
        "legacy": False,
    },
}

# Brand and Reference artifacts are opt-in. Keeping an explicit project
# inventory prevents a generic seed from silently acquiring authority,
# research, binding, or lineage templates.
PROJECT_SEED_SCHEMA_VERSIONS = {
    "creative-craft.brief.v1",
    "creative-craft.asset-ledger.v1",
    "creative-craft.concept-routes.v1",
    "creative-craft.critique.v1",
    "creative-craft.project-manifest.v2",
    "creative-craft.creative-direction.v1",
    "creative-craft.copy-sheet.v1",
    "creative-craft.image-job.v2",
    "creative-craft.video-job.v2",
    "creative-craft.evaluation.v2",
    "creative-craft.delivery.v2",
}
PROJECT_MANIFEST_SEED_SCHEMA_VERSIONS = {
    "creative-craft.brief.v1",
    "creative-craft.asset-ledger.v1",
    "creative-craft.concept-routes.v1",
    "creative-craft.critique.v1",
    "creative-craft.creative-direction.v1",
    "creative-craft.copy-sheet.v1",
    "creative-craft.image-job.v2",
    "creative-craft.video-job.v2",
    "creative-craft.evaluation.v2",
    "creative-craft.delivery.v2",
}

METADATA_SCHEMAS = {
    "creative-craft.provider.v1": "provider-profile.schema.json",
    "creative-craft.surface.v1": "surface-profile.schema.json",
    "creative-craft.sources.v1": "source-lock.schema.json",
}


@dataclass(frozen=True)
class ValidationContext:
    skill_root: Path = SKILL_ROOT

    @property
    def schemas_dir(self) -> Path:
        return self.skill_root / "schemas"

    @property
    def providers_dir(self) -> Path:
        return self.skill_root / "providers"

    @property
    def surfaces_dir(self) -> Path:
        return self.providers_dir / "surfaces"


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: Result) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def warn(self, condition: bool, message: str) -> None:
        if not condition:
            self.warnings.append(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON value must be an object: {path}")  # noqa: TRY004
    return value


def write_atomic(path: Path, text: str) -> None:
    path = path.expanduser().absolute()
    if path.is_symlink():
        raise ValueError(f"write destination must not be a symlink: {path}")
    if path.parent.is_symlink():
        raise ValueError(
            f"write destination parent must not be a symlink: {path.parent}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    legacy_tmp = path.with_name(path.name + ".tmp")
    if legacy_tmp.is_symlink():
        raise ValueError(f"temporary path must not be a symlink: {legacy_tmp}")
    if legacy_tmp.exists():
        raise ValueError(
            f"legacy temporary path must not exist before an atomic write: {legacy_tmp}"
        )

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            fd = -1
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except Exception:
        if fd >= 0:
            os.close(fd)
        tmp.unlink(missing_ok=True)
        raise


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


PLACEHOLDER_VALUE_PATTERN = re.compile(
    r"^(?:tbd|todo|unknown|placeholder|replace-me|example(?:\.[a-z]+)?)$",
    re.IGNORECASE,
)


def is_placeholder_value(value: Any) -> bool:
    if not nonempty(value):
        return True
    stripped = str(value).strip()
    return (
        bool(PLACEHOLDER_VALUE_PATTERN.fullmatch(stripped))
        or ("<" in stripped and ">" in stripped)
        or bool(re.search(r"://[^/]*\.invalid(?:/|$)", stripped, re.IGNORECASE))
    )


def json_content_sha256(data: dict[str, Any]) -> str:
    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def reference_history_filename(binding_id: str) -> str:
    digest = hashlib.sha256(binding_id.encode("utf-8")).hexdigest()
    return f"{digest}.json"


def require_string(
    result: Result, data: dict[str, Any], key: str, prefix: str = ""
) -> None:
    result.require(nonempty(data.get(key)), f"{prefix}{key} must be a non-empty string")


def require_list(
    result: Result, data: dict[str, Any], key: str, prefix: str = ""
) -> None:
    result.require(isinstance(data.get(key), list), f"{prefix}{key} must be an array")


def _schema_type_matches(value: Any, expected: str) -> bool:
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "number": lambda item: (
            isinstance(item, (int, float)) and not isinstance(item, bool)
        ),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }
    checker = checks.get(expected)
    return bool(checker and checker(value))


def _json_path(parts: tuple[Any, ...]) -> str:
    if not parts:
        return "<root>"
    return ".".join(str(part) for part in parts)


def _resolve_local_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(
            f"only local JSON Schema references are supported: {reference}"
        )
    current: Any = root_schema
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"unresolved local JSON Schema reference: {reference}")
        current = current[part]
    if not isinstance(current, dict):
        raise ValueError(  # noqa: TRY004
            f"JSON Schema reference is not an object: {reference}"
        )
    return current


def _json_values_equal(left: Any, right: Any) -> bool:
    """Compare values with JSON Schema equality, keeping booleans distinct from numbers."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if (
        isinstance(left, (int, float))
        and not isinstance(left, bool)
        and isinstance(right, (int, float))
        and not isinstance(right, bool)
    ):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_values_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_values_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return bool(left == right)


def _json_equality_key(value: Any) -> tuple[Any, ...]:
    """Build a hashable index key that is compatible with JSON Schema equality."""
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, (int, float)):
        return ("number", value)
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, list):
        return ("array", tuple(_json_equality_key(item) for item in value))
    if isinstance(value, dict):
        return (
            "object",
            tuple(
                sorted((key, _json_equality_key(item)) for key, item in value.items())
            ),
        )
    return (type(value).__name__, repr(value))


def _first_json_duplicate(value: list[Any]) -> tuple[int, int] | None:
    indexed: dict[tuple[Any, ...], list[tuple[int, Any]]] = {}
    for right_index, right_value in enumerate(value):
        key = _json_equality_key(right_value)
        for left_index, left_value in indexed.get(key, []):
            if _json_values_equal(left_value, right_value):
                return left_index, right_index
        indexed.setdefault(key, []).append((right_index, right_value))
    return None


def _validate_schema_node(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: tuple[Any, ...],
    result: Result,
) -> None:
    if "$ref" in schema:
        try:
            target = _resolve_local_ref(root_schema, str(schema["$ref"]))
        except ValueError as exc:
            result.errors.append(str(exc))
            return
        _validate_schema_node(value, target, root_schema, path, result)
        return

    expected = schema.get("type")
    expected_types = [expected] if isinstance(expected, str) else expected
    if isinstance(expected_types, list) and not any(
        isinstance(item, str) and _schema_type_matches(value, item)
        for item in expected_types
    ):
        label = " or ".join(str(item) for item in expected_types)
        result.errors.append(f"{_json_path(path)} must be {label}")
        return

    if "const" in schema and value != schema["const"]:
        result.errors.append(f"{_json_path(path)} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        result.errors.append(f"{_json_path(path)} must be one of {schema['enum']!r}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    result.errors.append(f"{_json_path(path + (key,))} is required")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child_value in value.items():
                child_schema = properties.get(key)
                if isinstance(child_schema, dict):
                    _validate_schema_node(
                        child_value, child_schema, root_schema, path + (key,), result
                    )
                elif schema.get("additionalProperties") is False:
                    result.errors.append(f"{_json_path(path + (key,))} is not allowed")

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            result.errors.append(
                f"{_json_path(path)} must contain at least {minimum} items"
            )
        maximum = schema.get("maxItems")
        if isinstance(maximum, int) and len(value) > maximum:
            result.errors.append(
                f"{_json_path(path)} must contain at most {maximum} items"
            )
        if schema.get("uniqueItems") is True:
            duplicate = _first_json_duplicate(value)
            if duplicate is not None:
                result.errors.append(
                    f"{_json_path(path)} must contain unique items; "
                    f"indexes {duplicate[0]} and {duplicate[1]} are equal"
                )
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, child_value in enumerate(value):
                _validate_schema_node(
                    child_value, item_schema, root_schema, path + (index,), result
                )

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            result.errors.append(
                f"{_json_path(path)} must contain at least {minimum} characters"
            )
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            result.errors.append(
                f"{_json_path(path)} does not match pattern {pattern!r}"
            )

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            result.errors.append(f"{_json_path(path)} must be >= {minimum}")
        maximum = schema.get("maximum")
        if isinstance(maximum, (int, float)) and value > maximum:
            result.errors.append(f"{_json_path(path)} must be <= {maximum}")
        exclusive_minimum = schema.get("exclusiveMinimum")
        if isinstance(exclusive_minimum, (int, float)) and value <= exclusive_minimum:
            result.errors.append(f"{_json_path(path)} must be > {exclusive_minimum}")
        exclusive_maximum = schema.get("exclusiveMaximum")
        if isinstance(exclusive_maximum, (int, float)) and value >= exclusive_maximum:
            result.errors.append(f"{_json_path(path)} must be < {exclusive_maximum}")


def validate_against_schema(data: dict[str, Any], schema_path: Path) -> Result:
    result = Result()
    try:
        schema = load_json(schema_path)
    except ValueError as exc:
        result.errors.append(str(exc))
        return result
    _validate_schema_node(data, schema, schema, (), result)
    return result


def provider_profiles(providers_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    root = providers_dir or PROVIDERS_DIR
    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.json")):
        data = load_json(path)
        profile_id = data.get("profile_id")
        if isinstance(profile_id, str):
            if profile_id in profiles:
                raise ValueError(f"duplicate provider profile_id: {profile_id}")
            profiles[profile_id] = data
    return profiles


def surface_profiles(surfaces_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    root = surfaces_dir or SURFACES_DIR
    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.json")):
        data = load_json(path)
        surface_id = data.get("surface_id")
        if isinstance(surface_id, str):
            if surface_id in profiles:
                raise ValueError(f"duplicate execution surface_id: {surface_id}")
            profiles[surface_id] = data
    return profiles


def validate_brief(data: dict[str, Any]) -> Result:
    r = Result()
    r.require(
        data.get("schema_version") == "creative-craft.brief.v1",
        "schema_version must be creative-craft.brief.v1",
    )
    require_string(r, data, "brief_id")
    r.require(
        data.get("status") in {"draft", "working", "locked", "superseded"},
        "status is invalid",
    )
    project = data.get("project")
    r.require(isinstance(project, dict), "project must be an object")
    if isinstance(project, dict):
        require_string(r, project, "name", "project.")
        require_string(r, project, "owner", "project.")
    objective = data.get("objective")
    r.require(isinstance(objective, dict), "objective must be an object")
    if isinstance(objective, dict):
        require_string(r, objective, "business", "objective.")
        require_string(r, objective, "communication", "objective.")
    audience = data.get("audience")
    r.require(isinstance(audience, dict), "audience must be an object")
    if isinstance(audience, dict):
        require_string(r, audience, "primary", "audience.")
        require_string(r, audience, "context", "audience.")
    for key in ("tension", "insight"):
        item = data.get(key)
        r.require(isinstance(item, dict), f"{key} must be an object")
        if isinstance(item, dict):
            require_string(r, item, "statement", f"{key}.")
            r.require(
                item.get("evidence_state") in EVIDENCE_STATES,
                f"{key}.evidence_state is invalid",
            )
    require_string(r, data, "proposition")
    response = data.get("desired_response")
    r.require(isinstance(response, dict), "desired_response must be an object")
    if isinstance(response, dict):
        for key in ("feel", "think", "do"):
            require_string(r, response, key, "desired_response.")
    constraints = data.get("constraints")
    r.require(isinstance(constraints, dict), "constraints must be an object")
    if isinstance(constraints, dict):
        require_list(r, constraints, "must", "constraints.")
        require_list(r, constraints, "must_not", "constraints.")
    if data.get("status") == "locked":
        r.warn(bool(data.get("channels")), "locked brief has no channels")
        r.warn(bool(data.get("deliverables")), "locked brief has no deliverables")
        insight = data.get("insight", {})
        r.warn(
            insight.get("evidence_state") != "UNVERIFIED",
            "locked brief still has an unverified insight",
        )
    return r


def validate_asset_ledger(data: dict[str, Any]) -> Result:
    r = Result()
    r.require(
        data.get("schema_version") == "creative-craft.asset-ledger.v1",
        "schema_version must be creative-craft.asset-ledger.v1",
    )
    require_string(r, data, "project_id")
    assets = data.get("assets")
    r.require(isinstance(assets, list), "assets must be an array")
    seen: set[str] = set()
    if isinstance(assets, list):
        for i, asset in enumerate(assets):
            p = f"assets[{i}]."
            r.require(isinstance(asset, dict), f"assets[{i}] must be an object")
            if not isinstance(asset, dict):
                continue
            asset_id = asset.get("asset_id")
            r.require(nonempty(asset_id), p + "asset_id must be a non-empty string")
            if isinstance(asset_id, str):
                r.require(asset_id not in seen, p + f"duplicate asset_id: {asset_id}")
                seen.add(asset_id)
            for key in ("path_or_uri", "mime_type", "creator", "owner"):
                require_string(r, asset, key, p)
            r.require(
                asset.get("rights_status")
                in {"CLEARED", "LIMITED", "EXPIRED", "REJECTED", "UNVERIFIED"},
                p + "rights_status is invalid",
            )
            r.require(
                asset.get("consent_status")
                in {"CLEARED", "LIMITED", "REJECTED", "UNVERIFIED", "NOT_APPLICABLE"},
                p + "consent_status is invalid",
            )
            require_list(r, asset, "allowed_use", p)
            require_list(r, asset, "reference_roles", p)
            digest = asset.get("sha256")
            if digest is not None:
                r.require(
                    isinstance(digest, str)
                    and bool(re.fullmatch(r"[0-9a-fA-F]{64}", digest)),
                    p + "sha256 must be null or a 64-character hex digest",
                )
    return r


def parse_image_size(size: str) -> tuple[int, int] | None:
    if size == "auto":
        return None
    match = re.fullmatch(r"(\d+)x(\d+)", size)
    if not match:
        raise ValueError("size must be auto or WIDTHxHEIGHT")
    return int(match.group(1)), int(match.group(2))


def validate_image_job(
    data: dict[str, Any], context: ValidationContext | None = None
) -> Result:
    context = context or ValidationContext()
    r = Result()
    version = data.get("schema_version")
    r.require(
        version in {"creative-craft.image-job.v1", "creative-craft.image-job.v2"},
        "schema_version must be creative-craft.image-job.v1 or v2",
    )
    for key in ("job_id", "brief_id", "provider_profile", "intended_use"):
        require_string(r, data, key)
    r.require(data.get("task_type") in {"generate", "edit"}, "task_type is invalid")
    r.require(
        data.get("execution_mode") in {"single_turn", "multi_turn"},
        "execution_mode is invalid",
    )
    if version == "creative-craft.image-job.v1":
        r.require(
            data.get("status")
            in {"draft", "ready", "executed", "inspected", "approved", "superseded"},
            "status is invalid",
        )
    else:
        for key in ("direction_id", "selected_route_id", "execution_surface"):
            require_string(r, data, key)
        require_list(r, data, "asset_refs")
        asset_refs = data.get("asset_refs", [])
        if isinstance(asset_refs, list):
            r.require(
                len(asset_refs) == len(set(asset_refs)),
                "asset_refs must not contain duplicates",
            )
        r.require(
            data.get("declared_status") in {"draft", "ready", "superseded"},
            "declared_status is invalid",
        )

    try:
        profiles = provider_profiles(context.providers_dir)
        surfaces = surface_profiles(context.surfaces_dir)
    except ValueError as exc:
        r.errors.append(str(exc))
        profiles = {}
        surfaces = {}
    profile_id = data.get("provider_profile")
    profile = profiles.get(profile_id)
    r.require(profile is not None, f"unknown provider_profile: {profile_id!r}")
    if version == "creative-craft.image-job.v2":
        surface_id = data.get("execution_surface")
        surface = surfaces.get(surface_id)
        r.require(surface is not None, f"unknown execution_surface: {surface_id!r}")
        if surface:
            r.require(
                surface.get("available") is True,
                f"execution_surface is not currently available: {surface_id!r}",
            )
            r.require(
                profile_id in surface.get("provider_profiles", []),
                "execution_surface does not support provider_profile",
            )
            r.require(
                data.get("execution_mode") in surface.get("modes", []),
                "execution_surface does not support execution_mode",
            )
            r.require(
                data.get("task_type") in surface.get("modes", []),
                "execution_surface does not support task_type",
            )

    canvas = data.get("canvas")
    r.require(isinstance(canvas, dict), "canvas must be an object")
    if isinstance(canvas, dict):
        for key in ("size", "quality", "format", "background"):
            require_string(r, canvas, key, "canvas.")
        r.require(
            canvas.get("quality") in {"low", "medium", "high", "auto"},
            "canvas.quality is invalid",
        )
        r.require(
            canvas.get("format") in {"png", "jpeg", "webp"}, "canvas.format is invalid"
        )
        compression = canvas.get("compression")
        r.require(
            compression is None
            or (
                isinstance(compression, int)
                and not isinstance(compression, bool)
                and 0 <= compression <= 100
            ),
            "canvas.compression must be null or an integer from 0 to 100",
        )
        if compression is not None:
            r.require(
                canvas.get("format") in {"jpeg", "webp"},
                "canvas.compression is supported only for jpeg or webp",
            )
        if canvas.get("background") == "transparent":
            r.require(
                version == "creative-craft.image-job.v2"
                and (profile or {}).get("capabilities", {}).get("transparent_background") is True,
                "transparent background requires a capable v2 provider",
            )
            r.require(canvas.get("format") in {"png", "webp"}, "transparent background requires PNG/WebP")
        else:
            r.require(canvas.get("background") in {"opaque", "auto"}, "canvas.background is invalid")
        variants = canvas.get("variants")
        r.require(
            isinstance(variants, int) and variants >= 1,
            "canvas.variants must be an integer >= 1",
        )
        size = canvas.get("size")
        if isinstance(size, str) and profile:
            try:
                parsed = parse_image_size(size)
            except ValueError as exc:
                r.errors.append(f"canvas.size: {exc}")
            else:
                if parsed is not None:
                    width, height = parsed
                    caps = profile["capabilities"]["size"]
                    r.require(
                        max(width, height) <= caps["max_edge_px"],
                        f"canvas.size maximum edge exceeds {caps['max_edge_px']}px",
                    )
                    r.require(
                        width % caps["edge_multiple_px"] == 0
                        and height % caps["edge_multiple_px"] == 0,
                        f"canvas.size edges must be multiples of {caps['edge_multiple_px']}px",
                    )
                    ratio = max(width, height) / min(width, height)
                    r.require(
                        ratio <= caps["max_aspect_ratio"],
                        f"canvas.size aspect ratio exceeds {caps['max_aspect_ratio']}:1",
                    )
                    pixels = width * height
                    r.require(
                        caps["min_total_pixels"] <= pixels <= caps["max_total_pixels"],
                        "canvas.size total pixels are outside the provider profile",
                    )
                    if pixels > caps["experimental_above_total_pixels"]:
                        r.warnings.append(
                            "canvas.size is above the provider profile's experimental reliability boundary"
                        )

    prompt = data.get("prompt")
    r.require(isinstance(prompt, dict), "prompt must be an object")
    if isinstance(prompt, dict):
        for key in ("scene", "subject", "composition", "lighting", "materials_style"):
            require_string(r, prompt, key, "prompt.")
        for key in (
            "exact_text",
            "references",
            "change",
            "preserve",
            "constraints",
            "exclude",
        ):
            require_list(r, prompt, key, "prompt.")
        if data.get("task_type") == "edit":
            r.warn(bool(prompt.get("change")), "edit job has no explicit change list")
            r.warn(
                bool(prompt.get("preserve")), "edit job has no explicit preserve list"
            )
        seen_refs: set[str] = set()
        for i, ref in enumerate(
            prompt.get("references", [])
            if isinstance(prompt.get("references"), list)
            else []
        ):
            if not isinstance(ref, dict):
                r.errors.append(f"prompt.references[{i}] must be an object")
                continue
            asset_id = ref.get("asset_id")
            role = ref.get("role")
            r.require(
                nonempty(asset_id), f"prompt.references[{i}].asset_id is required"
            )
            r.require(nonempty(role), f"prompt.references[{i}].role is required")
            if isinstance(asset_id, str):
                r.require(
                    asset_id not in seen_refs,
                    f"prompt.references[{i}] duplicates asset_id {asset_id}",
                )
                seen_refs.add(asset_id)
    require_list(r, data, "inspection")
    rights = data.get("rights")
    r.require(isinstance(rights, dict), "rights must be an object")
    if isinstance(rights, dict):
        r.require(
            rights.get("status") in {"CLEARED", "LIMITED", "REJECTED", "UNVERIFIED"},
            "rights.status is invalid",
        )
        if data.get("status") in {"approved"}:
            r.require(
                rights.get("status") in {"CLEARED", "LIMITED"},
                "approved image job cannot have rejected or unverified rights",
            )
    return r


def validate_video_job(
    data: dict[str, Any], context: ValidationContext | None = None
) -> Result:
    context = context or ValidationContext()
    r = Result()
    version = data.get("schema_version")
    r.require(
        version in {"creative-craft.video-job.v1", "creative-craft.video-job.v2"},
        "schema_version must be creative-craft.video-job.v1 or v2",
    )
    for key in (
        "job_id",
        "brief_id",
        "provider_profile",
        "intended_use",
        "premise",
        "end_state",
    ):
        require_string(r, data, key)
    r.require(
        data.get("task_type")
        in {
            "text_to_video",
            "image_to_video",
            "reference_to_video",
            "extend_video",
            "edit_video",
        },
        "task_type is invalid",
    )
    r.require(
        data.get("execution_mode") in {"single_pass", "extension", "edit"},
        "execution_mode is invalid",
    )
    if version == "creative-craft.video-job.v1":
        r.require(
            data.get("status")
            in {"draft", "ready", "executed", "inspected", "approved", "superseded"},
            "status is invalid",
        )
    else:
        for key in ("direction_id", "selected_route_id", "execution_surface"):
            require_string(r, data, key)
        require_list(r, data, "asset_refs")
        asset_refs = data.get("asset_refs", [])
        if isinstance(asset_refs, list):
            r.require(
                len(asset_refs) == len(set(asset_refs)),
                "asset_refs must not contain duplicates",
            )
        r.require(
            data.get("declared_status") in {"draft", "ready", "superseded"},
            "declared_status is invalid",
        )

    try:
        profiles = provider_profiles(context.providers_dir)
        surfaces = surface_profiles(context.surfaces_dir)
    except ValueError as exc:
        r.errors.append(str(exc))
        profiles = {}
        surfaces = {}
    profile_id = data.get("provider_profile")
    profile = profiles.get(profile_id)
    r.require(profile is not None, f"unknown provider_profile: {profile_id!r}")
    if version == "creative-craft.video-job.v2":
        surface_id = data.get("execution_surface")
        surface = surfaces.get(surface_id)
        r.require(surface is not None, f"unknown execution_surface: {surface_id!r}")
        if surface:
            r.require(
                surface.get("available") is True,
                f"execution_surface is not currently available: {surface_id!r}",
            )
            r.require(
                profile_id in surface.get("provider_profiles", []),
                "execution_surface does not support provider_profile",
            )
            r.require(
                data.get("execution_mode") in surface.get("modes", []),
                "execution_surface does not support execution_mode",
            )

    duration = data.get("duration_seconds")
    r.require(
        isinstance(duration, (int, float))
        and not isinstance(duration, bool)
        and duration > 0,
        "duration_seconds must be a positive number",
    )
    if (
        isinstance(duration, (int, float))
        and not isinstance(duration, bool)
        and profile
    ):
        maximum = profile["capabilities"]["single_pass_max_seconds"]
        r.require(
            duration <= maximum,
            f"duration_seconds exceeds the current per-job limit of {maximum}s; use extension jobs",
        )

    fmt = data.get("format")
    r.require(isinstance(fmt, dict), "format must be an object")
    if isinstance(fmt, dict):
        for key in ("aspect_ratio", "resolution_target", "language"):
            require_string(r, fmt, key, "format.")

    refs = data.get("references")
    r.require(isinstance(refs, list), "references must be an array")
    counts = {"images": 0, "videos": 0, "audio": 0}
    seen_refs: set[str] = set()
    if isinstance(refs, list):
        for i, ref in enumerate(refs):
            if not isinstance(ref, dict):
                r.errors.append(f"references[{i}] must be an object")
                continue
            asset_id = ref.get("asset_id")
            kind = ref.get("kind")
            role = ref.get("role")
            r.require(nonempty(asset_id), f"references[{i}].asset_id is required")
            r.require(
                kind in {"image", "video", "audio", "clay_render"},
                f"references[{i}].kind is invalid",
            )
            r.require(nonempty(role), f"references[{i}].role is required")
            if isinstance(asset_id, str):
                r.require(
                    asset_id not in seen_refs,
                    f"references[{i}] duplicates asset_id {asset_id}",
                )
                seen_refs.add(asset_id)
            if kind in {"image", "clay_render"}:
                counts["images"] += 1
            elif kind == "video":
                counts["videos"] += 1
            elif kind == "audio":
                counts["audio"] += 1
    if profile:
        limits = profile["capabilities"]["reference_limits"]
        for key, count in counts.items():
            r.require(
                count <= limits[key],
                f"{key} reference count {count} exceeds provider profile limit {limits[key]}",
            )

    require_list(r, data, "continuity_locks")
    timeline = data.get("timeline")
    r.require(
        isinstance(timeline, list) and bool(timeline),
        "timeline must be a non-empty array",
    )
    last_end = 0.0
    if isinstance(timeline, list):
        for i, beat in enumerate(timeline):
            if not isinstance(beat, dict):
                r.errors.append(f"timeline[{i}] must be an object")
                continue
            start = beat.get("start")
            end = beat.get("end")
            numeric = all(
                isinstance(v, (int, float)) and not isinstance(v, bool)
                for v in (start, end)
            )
            r.require(numeric, f"timeline[{i}] start/end must be numbers")
            if numeric:
                r.require(
                    0 <= start < end, f"timeline[{i}] must satisfy 0 <= start < end"
                )
                if isinstance(duration, (int, float)) and not isinstance(
                    duration, bool
                ):
                    r.require(
                        end <= duration, f"timeline[{i}].end exceeds duration_seconds"
                    )
                r.require(
                    start >= last_end,
                    f"timeline[{i}] overlaps or is out of chronological order",
                )
                if start > last_end:
                    r.warnings.append(
                        f"timeline has an uncovered gap from {last_end:g}s to {start:g}s"
                    )
                last_end = max(last_end, float(end))
            for key in ("visual", "action", "camera", "audio"):
                require_string(r, beat, key, f"timeline[{i}].")
        if (
            isinstance(duration, (int, float))
            and not isinstance(duration, bool)
            and timeline
            and last_end < duration
        ):
            r.warnings.append(
                f"timeline ends at {last_end:g}s but duration_seconds is {duration:g}s"
            )

    env = data.get("environment")
    r.require(isinstance(env, dict), "environment must be an object")
    if isinstance(env, dict):
        for key in ("lighting", "materials", "physics"):
            require_string(r, env, key, "environment.")
    audio = data.get("dialogue_audio")
    r.require(isinstance(audio, dict), "dialogue_audio must be an object")
    if isinstance(audio, dict):
        require_list(r, audio, "dialogue", "dialogue_audio.")
        require_list(r, audio, "effects", "dialogue_audio.")
        for key in ("voice", "ambience", "music"):
            if not isinstance(audio.get(key), str):
                r.errors.append(f"dialogue_audio.{key} must be a string")

    edit = data.get("edit")
    r.require(isinstance(edit, dict), "edit must be an object")
    if isinstance(edit, dict):
        require_list(r, edit, "change", "edit.")
        require_list(r, edit, "preserve", "edit.")
        if (
            data.get("task_type") == "edit_video"
            or data.get("execution_mode") == "edit"
        ):
            r.warn(nonempty(edit.get("range")), "edit job has no explicit time range")
            r.warn(bool(edit.get("change")), "edit job has no change list")
            r.warn(bool(edit.get("preserve")), "edit job has no preserve list")
    if data.get("task_type") == "extend_video":
        r.warn(
            bool(data.get("continuity_locks")), "extension job has no continuity locks"
        )
        r.warn(
            any(ref.get("kind") == "video" for ref in refs if isinstance(ref, dict))
            if isinstance(refs, list)
            else False,
            "extension job has no source video reference",
        )

    require_list(r, data, "exclude")
    require_list(r, data, "inspection")
    rights = data.get("rights")
    r.require(isinstance(rights, dict), "rights must be an object")
    if isinstance(rights, dict):
        r.require(
            rights.get("status") in {"CLEARED", "LIMITED", "REJECTED", "UNVERIFIED"},
            "rights.status is invalid",
        )
        if data.get("status") == "approved":
            r.require(
                rights.get("status") in {"CLEARED", "LIMITED"},
                "approved video job cannot have rejected or unverified rights",
            )
    return r


def validate_evaluation(data: dict[str, Any]) -> Result:
    r = Result()
    r.require(
        data.get("schema_version") == "creative-craft.evaluation.v1",
        "schema_version must be creative-craft.evaluation.v1",
    )
    for key in ("evaluation_id", "target_id", "brief_id", "recommendation"):
        require_string(r, data, key)
    r.require(
        data.get("stage") in {"route", "direction", "output", "delivery"},
        "stage is invalid",
    )
    gates = data.get("gates")
    r.require(isinstance(gates, dict), "gates must be an object")
    if isinstance(gates, dict):
        for key in ("rights_clear", "brief_locked", "deliverable_specified"):
            r.require(isinstance(gates.get(key), bool), f"gates.{key} must be boolean")
        r.require(
            isinstance(gates.get("actual_output_observed"), (bool, type(None))),
            "gates.actual_output_observed must be boolean or null",
        )
    dims = data.get("dimensions")
    r.require(
        isinstance(dims, list) and bool(dims), "dimensions must be a non-empty array"
    )
    seen: set[str] = set()
    if isinstance(dims, list):
        for i, dim in enumerate(dims):
            if not isinstance(dim, dict):
                r.errors.append(f"dimensions[{i}] must be an object")
                continue
            dim_id = dim.get("id")
            r.require(nonempty(dim_id), f"dimensions[{i}].id is required")
            if isinstance(dim_id, str):
                r.require(dim_id not in seen, f"duplicate dimension id: {dim_id}")
                seen.add(dim_id)
            weight = dim.get("weight")
            score = dim.get("score")
            r.require(
                isinstance(weight, (int, float))
                and not isinstance(weight, bool)
                and weight > 0,
                f"dimensions[{i}].weight must be > 0",
            )
            r.require(
                isinstance(score, (int, float))
                and not isinstance(score, bool)
                and 0 <= score <= 5,
                f"dimensions[{i}].score must be between 0 and 5",
            )
            r.require(
                dim.get("evidence_state") in EVIDENCE_STATES,
                f"dimensions[{i}].evidence_state is invalid",
            )
            r.require(
                isinstance(dim.get("evidence"), str),
                f"dimensions[{i}].evidence must be a string",
            )
            r.require(
                dim.get("confidence") in {"low", "medium", "high"},
                f"dimensions[{i}].confidence is invalid",
            )
        total_weight = sum(
            float(d.get("weight", 0))
            for d in dims
            if isinstance(d, dict) and isinstance(d.get("weight"), (int, float))
        )
        r.warn(
            math.isclose(total_weight, 100.0, rel_tol=0, abs_tol=0.001),
            f"dimension weights sum to {total_weight:g}, not 100",
        )
    require_list(r, data, "remaining_unknowns")
    return r


def validate_concept_routes(data: dict[str, Any]) -> Result:
    r = Result()
    r.require(
        data.get("schema_version") == "creative-craft.concept-routes.v1",
        "schema_version must be creative-craft.concept-routes.v1",
    )
    require_string(r, data, "brief_id")
    routes = data.get("routes")
    r.require(
        isinstance(routes, list) and bool(routes), "routes must be a non-empty array"
    )
    seen: set[str] = set()
    if isinstance(routes, list):
        mechanisms: list[str] = []
        for i, route in enumerate(routes):
            if not isinstance(route, dict):
                r.errors.append(f"routes[{i}] must be an object")
                continue
            for key in (
                "route_id",
                "name",
                "premise",
                "mechanism",
                "hook",
                "architecture",
                "visual_world",
                "hero_moment",
                "why_it_may_win",
            ):
                require_string(r, route, key, f"routes[{i}].")
            route_id = route.get("route_id")
            if isinstance(route_id, str):
                r.require(route_id not in seen, f"duplicate route_id: {route_id}")
                seen.add(route_id)
            mechanism = route.get("mechanism")
            if isinstance(mechanism, str):
                mechanisms.append(mechanism.strip().lower())
            r.require(
                route.get("decision")
                in {
                    "SELECT",
                    "SELECT_FOR_TEST",
                    "HOLD",
                    "MERGE_ELEMENT",
                    "REWORK",
                    "REJECT",
                },
                f"routes[{i}].decision is invalid",
            )
        if len(mechanisms) > 1:
            r.warn(
                len(set(mechanisms)) == len(mechanisms),
                "two or more routes use identical mechanism text; verify real distinctness",
            )
    return r


def validate_critique(data: dict[str, Any]) -> Result:
    r = Result()
    r.require(
        data.get("schema_version") == "creative-craft.critique.v1",
        "schema_version must be creative-craft.critique.v1",
    )
    require_string(r, data, "critique_id")
    require_string(r, data, "asset_id")
    for key in (
        "observations",
        "interpretations",
        "performance_hypotheses",
        "decisions",
        "unknowns",
    ):
        require_list(r, data, key)
    allowed = {
        "KEEP",
        "AMPLIFY",
        "POLISH",
        "SIMPLIFY",
        "RECOMPOSE",
        "REWRITE",
        "REGENERATE",
        "RE_EDIT",
        "RE_SHOOT",
        "REPLACE",
        "DROP",
        "TEST",
        "DEFER",
        "DOCUMENT",
    }
    for i, decision in enumerate(
        data.get("decisions", []) if isinstance(data.get("decisions"), list) else []
    ):
        r.require(isinstance(decision, dict), f"decisions[{i}] must be an object")
        if isinstance(decision, dict):
            r.require(
                decision.get("decision") in allowed,
                f"decisions[{i}].decision is invalid",
            )
    return r


def validate_delivery(data: dict[str, Any]) -> Result:
    r = Result()
    r.require(
        data.get("schema_version") == "creative-craft.delivery.v1",
        "schema_version must be creative-craft.delivery.v1",
    )
    for key in ("delivery_id", "project_id", "selected_route"):
        require_string(r, data, key)
    r.require(
        data.get("status")
        in {
            "planned",
            "prompt_ready",
            "generated",
            "inspected",
            "needs_revision",
            "approved",
            "delivered",
            "published",
            "superseded",
        },
        "status is invalid",
    )
    files = data.get("files")
    r.require(isinstance(files, list), "files must be an array")
    seen: set[str] = set()
    if isinstance(files, list):
        for i, item in enumerate(files):
            if not isinstance(item, dict):
                r.errors.append(f"files[{i}] must be an object")
                continue
            asset_id = item.get("asset_id")
            r.require(nonempty(asset_id), f"files[{i}].asset_id is required")
            if isinstance(asset_id, str):
                r.require(
                    asset_id not in seen, f"duplicate delivery asset_id: {asset_id}"
                )
                seen.add(asset_id)
            for key in (
                "path_or_uri",
                "role",
                "channel",
                "placement",
                "aspect_ratio",
                "format",
                "language",
                "source",
            ):
                require_string(r, item, key, f"files[{i}].")
            r.require(
                item.get("rights_status")
                in {"CLEARED", "LIMITED", "REJECTED", "UNVERIFIED"},
                f"files[{i}].rights_status is invalid",
            )
            if data.get("status") in {"approved", "delivered", "published"}:
                r.require(
                    item.get("rights_status") in {"CLEARED", "LIMITED"},
                    f"files[{i}] cannot be {data.get('status')} with unresolved rights",
                )
                r.require(
                    nonempty(item.get("sha256")),
                    f"files[{i}] needs sha256 for {data.get('status')} delivery",
                )
    require_list(r, data, "validation")
    require_list(r, data, "remaining_risks")
    return r


def validate_project_manifest(data: dict[str, Any]) -> Result:
    r = Result()
    seen_ids: set[tuple[str, str]] = set()
    seen_paths: set[str] = set()
    for index, artifact in enumerate(data.get("artifacts", [])):
        if not isinstance(artifact, dict):
            continue
        key = (str(artifact.get("artifact_type")), str(artifact.get("artifact_id")))
        r.require(
            key not in seen_ids,
            f"artifacts[{index}] duplicates artifact identity {key}",
        )
        seen_ids.add(key)
        path = str(artifact.get("path", ""))
        r.require(
            path not in seen_paths, f"artifacts[{index}] duplicates path {path!r}"
        )
        seen_paths.add(path)
        r.require(
            artifact.get("schema_version") in ARTIFACT_REGISTRY,
            f"artifacts[{index}] has unsupported schema_version",
        )
    return r


def validate_creative_direction(data: dict[str, Any]) -> Result:
    r = Result()
    approval = data.get("approval", {})
    if data.get("status") == "approved":
        r.require(
            approval.get("status") == "approved",
            "approved direction requires approval.status=approved",
        )
        for key in ("approved_by", "approved_at", "basis"):
            r.require(
                nonempty(approval.get(key)),
                f"approved direction requires approval.{key}",
            )
    if data.get("status") == "locked":
        for key in ("message_hierarchy", "visual_world", "invariants", "deliverables"):
            r.require(bool(data.get(key)), f"locked direction requires {key}")
        r.require(
            bool(data.get("image_art_direction") or data.get("video_treatment")),
            "locked direction requires image_art_direction or video_treatment",
        )
    seen: set[str] = set()
    for index, ref in enumerate(data.get("reference_roles", [])):
        if isinstance(ref, dict):
            asset_id = ref.get("asset_id")
            if isinstance(asset_id, str):
                r.require(
                    asset_id not in seen,
                    f"reference_roles[{index}] duplicates asset_id {asset_id}",
                )
                seen.add(asset_id)
    return r


def _parse_utc_timestamp(value: Any, label: str, result: Result) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        result.errors.append(f"{label} must be an ISO-8601 timestamp with timezone")
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except (ValueError, OverflowError):
        result.errors.append(f"{label} must be an ISO-8601 timestamp with timezone")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        result.errors.append(f"{label} must include a timezone offset or Z")
        return None
    return parsed.astimezone(dt.timezone.utc)


def validate_copy_sheet(data: dict[str, Any]) -> Result:
    r = Result()
    status = data.get("status")
    use_scope = data.get("use_scope")
    approval = data.get("approval", {})
    strategy = data.get("strategy", {})

    collections = (
        ("proof_hierarchy", "proof_id"),
        ("copy_routes", "route_id"),
        ("copy_units", "unit_id"),
    )
    ids_by_collection: dict[str, set[str]] = {}
    for collection, id_field in collections:
        seen: set[str] = set()
        for index, item in enumerate(data.get(collection, [])):
            if not isinstance(item, dict):
                continue
            item_id = item.get(id_field)
            if isinstance(item_id, str):
                r.require(
                    item_id not in seen,
                    f"{collection}[{index}] duplicates {id_field} {item_id!r}",
                )
                seen.add(item_id)
        ids_by_collection[collection] = seen

    priorities = [
        item.get("priority")
        for item in data.get("proof_hierarchy", [])
        if isinstance(item, dict)
    ]
    r.require(
        len(priorities) == len(set(priorities)),
        "proof_hierarchy priorities must be unique",
    )
    selected_route_id = data.get("selected_copy_route_id")
    if selected_route_id is not None:
        r.require(
            selected_route_id in ids_by_collection["copy_routes"],
            "selected_copy_route_id must reference copy_routes",
        )

    copy_texts = {
        str(item.get("text"))
        for item in data.get("copy_units", [])
        if isinstance(item, dict)
    }
    for value in data.get("mandatory_copy", []):
        r.require(
            value in copy_texts, f"mandatory_copy is absent from copy_units: {value!r}"
        )
    legal_texts = {
        str(item.get("text"))
        for item in data.get("copy_units", [])
        if isinstance(item, dict) and item.get("role") == "legal"
    }
    for value in data.get("legal_copy", []):
        r.require(
            value in legal_texts,
            f"legal_copy requires a matching legal copy unit: {value!r}",
        )

    evidence_items: list[tuple[str, dict[str, Any]]] = []
    if isinstance(strategy, dict):
        evidence_items.append(("strategy", strategy))
    for collection in ("proof_hierarchy", "copy_routes", "copy_units"):
        evidence_items.extend(
            (f"{collection}[{index}]", item)
            for index, item in enumerate(data.get(collection, []))
            if isinstance(item, dict)
        )

    if status in {"reviewed", "approved"}:
        r.require(
            bool(data.get("copy_routes")), f"{status} copy sheet requires copy_routes"
        )
        r.require(
            bool(data.get("copy_units")), f"{status} copy sheet requires copy_units"
        )
        r.require(
            nonempty(selected_route_id),
            f"{status} copy sheet requires selected_copy_route_id",
        )
        for label, item in evidence_items:
            evidence_state = item.get("evidence_state")
            r.require(
                evidence_state != "UNVERIFIED", f"{status} {label} cannot be UNVERIFIED"
            )
            r.require(
                bool(item.get("evidence_refs")),
                f"{status} {label} requires evidence_refs",
            )

    reviewed_at: dt.datetime | None = None
    approved_at: dt.datetime | None = None
    if status == "draft":
        r.require(use_scope == "exploration", "draft copy sheet is exploration only")
        r.require(
            approval.get("status") == "pending",
            "draft copy sheet requires pending approval",
        )
    elif status == "reviewed":
        r.require(use_scope == "internal", "reviewed copy sheet is internal only")
        r.require(
            approval.get("status") == "reviewed",
            "reviewed copy sheet requires reviewed approval",
        )
        r.require(
            nonempty(approval.get("reviewed_by")),
            "reviewed copy sheet requires reviewed_by",
        )
        reviewed_at = _parse_utc_timestamp(
            approval.get("reviewed_at"), "approval.reviewed_at", r
        )
    elif status == "approved":
        r.require(
            use_scope == "public", "approved copy sheet requires public use_scope"
        )
        r.require(
            approval.get("status") == "approved",
            "approved copy sheet requires approved approval",
        )
        for key in ("reviewed_by", "approved_by", "basis"):
            value = approval.get(key)
            r.require(
                nonempty(value) and not is_placeholder_value(value),
                f"approved copy sheet requires named approval.{key}",
            )
        reviewed_at = _parse_utc_timestamp(
            approval.get("reviewed_at"), "approval.reviewed_at", r
        )
        approved_at = _parse_utc_timestamp(
            approval.get("approved_at"), "approval.approved_at", r
        )
        if reviewed_at and approved_at:
            r.require(
                approved_at >= reviewed_at,
                "approval.approved_at must not precede reviewed_at",
            )
        for label, item in evidence_items:
            r.require(
                item.get("evidence_state") not in {"HYPOTHESIZED", "UNVERIFIED"},
                f"approved {label} requires specified, observed, or inferred evidence",
            )
    return r


def validate_execution_receipt(
    data: dict[str, Any], context: ValidationContext | None = None
) -> Result:
    context = context or ValidationContext()
    r = Result()
    try:
        profiles = provider_profiles(context.providers_dir)
        surfaces = surface_profiles(context.surfaces_dir)
    except ValueError as exc:
        r.errors.append(str(exc))
        return r
    profile_id = data.get("provider_profile")
    surface_id = data.get("execution_surface")
    r.require(profile_id in profiles, f"unknown provider_profile: {profile_id!r}")
    r.require(surface_id in surfaces, f"unknown execution_surface: {surface_id!r}")
    if profile_id in profiles:
        profile = profiles[profile_id]
        r.require(
            data.get("model") == profile.get("model"),
            "receipt model differs from provider profile",
        )
        expected_snapshot = profile.get("snapshot")
        if expected_snapshot is not None:
            r.require(
                data.get("snapshot") == expected_snapshot,
                "receipt snapshot differs from provider profile",
            )
    if surface_id in surfaces:
        r.require(
            profile_id in surfaces[surface_id].get("provider_profiles", []),
            "execution_surface does not support provider_profile",
        )
    if data.get("outcome") in {"succeeded", "partial"}:
        r.require(
            bool(data.get("outputs")),
            f"{data.get('outcome')} receipt requires at least one output",
        )
    if data.get("outcome") in {"failed", "cancelled"}:
        r.require(
            not data.get("outputs"),
            f"{data.get('outcome')} receipt must not claim outputs; use partial",
        )
    started = _parse_utc_timestamp(data.get("started_at"), "started_at", r)
    completed = _parse_utc_timestamp(data.get("completed_at"), "completed_at", r)
    if started is not None and completed is not None:
        r.require(completed >= started, "completed_at must be at or after started_at")
    seen: set[str] = set()
    seen_paths: set[str] = set()
    for index, output in enumerate(data.get("outputs", [])):
        if isinstance(output, dict):
            asset_id = output.get("asset_id")
            if isinstance(asset_id, str):
                r.require(
                    asset_id not in seen,
                    f"outputs[{index}] duplicates asset_id {asset_id}",
                )
                seen.add(asset_id)
            path = output.get("path")
            if isinstance(path, str):
                r.require(
                    path not in seen_paths, f"outputs[{index}] duplicates path {path}"
                )
                seen_paths.add(path)
    return r


def validate_output_inspection(data: dict[str, Any]) -> Result:
    r = Result()
    approval = data.get("approval", {})
    check_ids: set[str] = set()
    for group in (
        "findings",
        "invariant_checks",
        "copy_checks",
        "technical_checks",
        "rights_checks",
    ):
        for index, check in enumerate(data.get(group, [])):
            if isinstance(check, dict) and isinstance(check.get("id"), str):
                r.require(
                    check["id"] not in check_ids,
                    f"{group}[{index}] duplicates check id {check['id']}",
                )
                check_ids.add(check["id"])
    if data.get("decision") == "approved":
        for group in ("invariant_checks", "technical_checks", "rights_checks"):
            r.require(bool(data.get(group)), f"approved inspection requires {group}")
        for key in ("approved_by", "approved_at", "approval_basis"):
            r.require(
                nonempty(approval.get(key)),
                f"approved inspection requires approval.{key}",
            )
        for group in (
            "invariant_checks",
            "copy_checks",
            "technical_checks",
            "rights_checks",
        ):
            failed = [
                item
                for item in data.get(group, [])
                if isinstance(item, dict) and item.get("status") in {"fail", "unknown"}
            ]
            r.require(not failed, f"approved inspection has unresolved {group}")
        inspected_at = _parse_utc_timestamp(data.get("inspected_at"), "inspected_at", r)
        approved_at = _parse_utc_timestamp(
            approval.get("approved_at"), "approval.approved_at", r
        )
        if inspected_at is not None and approved_at is not None:
            r.require(
                approved_at >= inspected_at,
                "approval.approved_at must be at or after inspected_at",
            )
    return r


def validate_revision_lineage(data: dict[str, Any]) -> Result:
    r = Result()
    if data.get("decision") != "draft":
        for key in (
            "new_job_ref",
            "new_receipt_ref",
            "new_output_ref",
            "observed_result",
            "comparison",
        ):
            r.require(nonempty(data.get(key)), f"completed revision requires {key}")
    r.warn(
        len(data.get("integration_changes", [])) <= 3,
        "revision has many integration changes; verify that one primary variable remains isolated",
    )
    return r


def validate_evaluation_v2(data: dict[str, Any]) -> Result:
    r = Result()
    seen: set[str] = set()
    total_weight = 0.0
    for index, dimension in enumerate(data.get("dimensions", [])):
        if not isinstance(dimension, dict):
            continue
        dimension_id = dimension.get("id")
        if isinstance(dimension_id, str):
            r.require(
                dimension_id not in seen, f"duplicate dimension id: {dimension_id}"
            )
            seen.add(dimension_id)
        weight = dimension.get("weight")
        if isinstance(weight, (int, float)) and not isinstance(weight, bool):
            total_weight += float(weight)
        refs = dimension.get("evidence_refs", [])
        if dimension.get("evidence_state") == "UNVERIFIED":
            r.require(
                not refs, f"dimensions[{index}] UNVERIFIED evidence must not cite refs"
            )
        else:
            r.require(
                bool(refs), f"dimensions[{index}] evidence_refs must not be empty"
            )
    r.warn(
        math.isclose(total_weight, 100.0, rel_tol=0, abs_tol=0.001),
        f"dimension weights sum to {total_weight:g}, not 100",
    )
    return r


def validate_delivery_v2(data: dict[str, Any]) -> Result:
    r = Result()
    asset_ids = [
        item.get("asset_id") for item in data.get("files", []) if isinstance(item, dict)
    ]
    r.require(
        len(asset_ids) == len(set(asset_ids)),
        "delivery files must not duplicate asset_id",
    )
    if data.get("status") == "delivered":
        r.require(bool(data.get("files")), "delivered manifest requires files")
        for key in ("job_refs", "receipt_refs", "inspection_refs"):
            r.require(bool(data.get(key)), f"delivered manifest requires {key}")
        for index, item in enumerate(data.get("files", [])):
            if isinstance(item, dict):
                r.require(
                    item.get("rights_status") in {"CLEARED", "LIMITED"},
                    f"files[{index}] has unresolved rights",
                )
    return r


def validate_brand_pack_artifact(data: dict[str, Any]) -> Result:
    r = Result()
    roles: set[str] = set()
    paths: set[str] = set()
    brand_roles = 0
    for index, item in enumerate(data.get("authority_files", [])):
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        path = item.get("path")
        if isinstance(role, str):
            r.require(
                role not in roles, f"authority_files[{index}] duplicates role {role!r}"
            )
            roles.add(role)
            if role == "brand":
                brand_roles += 1
        if isinstance(path, str):
            r.require(
                path not in paths, f"authority_files[{index}] duplicates path {path!r}"
            )
            paths.add(path)
    r.require(
        brand_roles == 1,
        "brand pack requires exactly one authority file with role='brand'",
    )
    ledger = data.get("asset_ledger", {})
    if isinstance(ledger, dict):
        r.require(
            ledger.get("path") not in paths,
            "asset_ledger.path must not duplicate an authority file path",
        )
    source_ids: set[str] = set()
    for index, source in enumerate(data.get("source_references", [])):
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        if isinstance(source_id, str):
            r.require(
                source_id not in source_ids,
                f"source_references[{index}] duplicates source_id {source_id!r}",
            )
            source_ids.add(source_id)
    if data.get("status") == "approved":
        r.require(
            nonempty(data.get("approved_at")),
            "approved brand pack requires approved_at",
        )
        r.require(
            bool(data.get("source_references")),
            "approved brand pack requires at least one source reference",
        )
        for index, source in enumerate(data.get("source_references", [])):
            if isinstance(source, dict):
                r.require(
                    nonempty(source.get("reviewed_at")),
                    f"approved brand pack requires source_references[{index}].reviewed_at",
                )
                if nonempty(source.get("reviewed_at")):
                    try:
                        dt.datetime.fromisoformat(
                            str(source.get("reviewed_at")).replace("Z", "+00:00")
                        )
                    except ValueError:
                        r.errors.append(
                            f"source_references[{index}].reviewed_at must be ISO-8601"
                        )
        if nonempty(data.get("approved_at")):
            try:
                dt.datetime.fromisoformat(
                    str(data.get("approved_at")).replace("Z", "+00:00")
                )
            except ValueError:
                r.errors.append("approved_at must be ISO-8601")
        r.warn(
            nonempty(data.get("review_after")),
            "approved brand pack has no review_after date",
        )
    return r


def validate_brand_binding(data: dict[str, Any]) -> Result:
    r = Result()
    try:
        dt.datetime.fromisoformat(str(data.get("imported_at")).replace("Z", "+00:00"))
    except ValueError:
        r.errors.append("imported_at must be an ISO-8601 timestamp")
    source = data.get("source", {})
    if isinstance(source, dict) and source.get("commit") is not None:
        r.require(
            nonempty(source.get("repository_or_uri")),
            "source.commit requires source.repository_or_uri",
        )
    return r


def validate_reference_pack_artifact(data: dict[str, Any]) -> Result:
    r = Result()
    for field_name in ("reviewed_at", "review_after"):
        value = data.get(field_name)
        if value is None:
            continue
        try:
            dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            r.errors.append(f"{field_name} must be ISO-8601 or null")
    source_ids: set[str] = set()
    for index, source in enumerate(data.get("source_references", [])):
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        if isinstance(source_id, str):
            r.require(
                source_id not in source_ids,
                f"source_references[{index}] duplicates source_id {source_id!r}",
            )
            source_ids.add(source_id)
        captured_at = source.get("captured_at")
        if captured_at is not None:
            try:
                dt.datetime.fromisoformat(str(captured_at).replace("Z", "+00:00"))
            except ValueError:
                r.errors.append(
                    f"source_references[{index}].captured_at must be ISO-8601"
                )

    reference_ids: set[str] = set()
    observation_ids: set[str] = set()
    principle_ids: set[str] = set()
    for index, entity in enumerate(data.get("entities", [])):
        if not isinstance(entity, dict):
            continue
        reference_id = entity.get("reference_id")
        if isinstance(reference_id, str):
            r.require(
                reference_id not in reference_ids,
                f"entities[{index}] duplicates reference_id {reference_id!r}",
            )
            reference_ids.add(reference_id)
        for source_ref in entity.get("source_refs", []):
            r.require(
                source_ref in source_ids,
                f"entities[{index}] references unknown source {source_ref!r}",
            )
        entity_observation_ids: set[str] = set()
        for observation in entity.get("observations", []):
            if not isinstance(observation, dict):
                continue
            observation_id = observation.get("observation_id")
            if isinstance(observation_id, str):
                r.require(
                    observation_id not in observation_ids,
                    f"duplicate observation_id {observation_id!r}",
                )
                observation_ids.add(observation_id)
                entity_observation_ids.add(observation_id)
            if observation.get("evidence_state") == "UNVERIFIED":
                r.require(
                    not observation.get("evidence_refs"),
                    f"observation {observation_id!r} is UNVERIFIED and must not cite evidence",
                )
            else:
                r.require(
                    bool(observation.get("evidence_refs")),
                    f"observation {observation_id!r} requires evidence_refs",
                )
        for principle in entity.get("transferable_principles", []):
            if not isinstance(principle, dict):
                continue
            principle_id = principle.get("principle_id")
            if isinstance(principle_id, str):
                r.require(
                    principle_id not in principle_ids,
                    f"duplicate principle_id {principle_id!r}",
                )
                principle_ids.add(principle_id)
            for observation_id in principle.get("derived_from", []):
                r.require(
                    observation_id in entity_observation_ids,
                    f"principle {principle_id!r} derives from unknown observation {observation_id!r}",
                )
        r.require(
            entity.get("may_override_primary_brand") is False,
            f"entities[{index}] must not override the primary brand",
        )

    if data.get("status") == "reviewed":
        r.require(
            nonempty(data.get("reviewed_at")),
            "reviewed reference pack requires reviewed_at",
        )
        r.require(
            bool(data.get("source_references")),
            "reviewed reference pack requires source_references",
        )
        r.require(
            bool(data.get("entities")), "reviewed reference pack requires entities"
        )
        for index, source in enumerate(data.get("source_references", [])):
            if isinstance(source, dict):
                r.require(
                    nonempty(source.get("captured_at")),
                    f"reviewed reference pack requires source_references[{index}].captured_at",
                )
                r.require(
                    not is_placeholder_value(source.get("uri")),
                    f"reviewed reference pack source_references[{index}].uri must not be a placeholder",
                )
                r.require(
                    isinstance(source.get("sha256"), str)
                    and bool(re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256")))),
                    f"reviewed reference pack source_references[{index}] requires a content SHA-256",
                )
                r.require(
                    nonempty(source.get("snapshot_path")),
                    f"reviewed reference pack source_references[{index}] requires snapshot_path",
                )
        for entity in data.get("entities", []):
            if not isinstance(entity, dict):
                continue
            for observation in entity.get("observations", []):
                if isinstance(observation, dict):
                    r.require(
                        observation.get("evidence_state") != "UNVERIFIED",
                        "reviewed reference pack cannot contain UNVERIFIED observations",
                    )
        r.warn(
            nonempty(data.get("review_after")),
            "reviewed reference pack has no review_after date",
        )
    return r


def validate_reference_binding(data: dict[str, Any]) -> Result:
    r = Result()
    try:
        dt.datetime.fromisoformat(str(data.get("imported_at")).replace("Z", "+00:00"))
    except ValueError:
        r.errors.append("imported_at must be an ISO-8601 timestamp")
    source = data.get("source", {})
    if isinstance(source, dict) and source.get("commit") is not None:
        r.require(
            nonempty(source.get("repository_or_uri")),
            "source.commit requires source.repository_or_uri",
        )
    return r


def validate_reference_binding_history(data: dict[str, Any]) -> Result:
    r = Result()
    try:
        dt.datetime.fromisoformat(str(data.get("archived_at")).replace("Z", "+00:00"))
    except ValueError:
        r.errors.append("archived_at must be an ISO-8601 timestamp")
    binding = data.get("binding")
    if not isinstance(binding, dict):
        return r
    r.extend(validate_reference_binding(binding))
    r.require(
        data.get("history_id") == binding.get("binding_id"),
        "history_id must equal binding.binding_id",
    )
    r.require(
        data.get("binding_sha256") == json_content_sha256(binding),
        "binding_sha256 must match canonical binding content",
    )
    return r


# --- Video Harness v1: shared edit/QA contracts and production evidence ---

VIDEO_STAGES = (
    "brief",
    "reference",
    "plan",
    "select",
    "generate",
    "assemble",
    "inspect",
    "revise",
    "export",
)
EDIT_DOCUMENT_MAX_SECONDS = 600
SELECTION_EVIDENCE_TOLERANCE_SECONDS = 2.0
_TIME_EPSILON = 1e-6
# Matches Node edit-document.mjs: container durations from ffprobe are rounded.
_ASSET_DURATION_TOLERANCE = 0.001


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _indexed_ids(r: Result, values: Any, label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(values if isinstance(values, list) else []):
        if not isinstance(value, dict) or not isinstance(value.get("id"), str):
            continue
        r.require(
            value["id"] not in indexed,
            f"{label}[{index}] duplicates id {value['id']}",
        )
        indexed.setdefault(value["id"], value)
    return indexed


def media_speed(item: dict[str, Any]) -> float:
    """Playback rate of a media item (P2 ``speed``; 1 when absent)."""
    return float(item.get("speed", 1))


def media_source_end(item: dict[str, Any], fps: int) -> float:
    """Source time (seconds) consumed by a media item: in + frames / fps * speed."""
    return float(item["source_in_seconds"]) + item["frames"] / fps * media_speed(item)


def linked_caption_frames(
    caption: dict[str, Any], target: dict[str, Any], fps: int
) -> tuple[int, int] | None:
    """Output frames of a linked caption, clipped to its media item's source range.

    Source seconds map to output frames through the item's speed, so a caption
    on a 2x item occupies half as many output frames as its source span.
    """
    link = caption.get("link", {})
    speed = media_speed(target)
    source_in = float(target["source_in_seconds"])
    source_out = media_source_end(target, fps)
    start = max(float(link["source_from"]), source_in)
    end = min(float(link["source_to"]), source_out)
    if end <= start:
        return None
    first = target["start_frame"] + round((start - source_in) / speed * fps)
    last = target["start_frame"] + round((end - source_in) / speed * fps)
    return (first, last) if last > first else None


def edit_document_item_frames(data: dict[str, Any]) -> dict[str, tuple[int, int]]:
    """Resolved half-open output frame ranges for every timed item of a valid document."""
    fps = int(data["canvas"]["fps"])
    items = {item["id"]: item for item in data.get("items", [])}
    resolved: dict[str, tuple[int, int]] = {}
    for item_id, item in items.items():
        if "link" in item:
            target = items.get(item["link"]["item_id"])
            frames = linked_caption_frames(item, target, fps) if target else None
            if frames:
                resolved[item_id] = frames
        elif "start_frame" in item and "frames" in item:
            resolved[item_id] = (
                item["start_frame"],
                item["start_frame"] + item["frames"],
            )
    return resolved


def edit_document_duration_frames(data: dict[str, Any]) -> int:
    """Output length: the maximum end of media, graphic and unlinked caption items."""
    ends = [
        item["start_frame"] + item["frames"]
        for item in data.get("items", [])
        if "link" not in item and "start_frame" in item and "frames" in item
    ]
    return max(ends, default=0)


def edit_document_generated_share(data: dict[str, Any]) -> float:
    """Share of output frames whose topmost video media uses a generated asset."""
    duration = edit_document_duration_frames(data)
    if duration <= 0:
        return 0.0
    order = {
        track["id"]: index
        for index, track in enumerate(data.get("tracks", []))
        if track.get("kind") == "video"
    }
    generated = {
        asset["id"]
        for asset in data.get("assets", [])
        if asset.get("origin", {}).get("kind") == "generated"
    }
    video_items = [
        item
        for item in data.get("items", [])
        if item.get("kind") == "media" and item.get("track_id") in order
    ]
    bounds = sorted(
        {0, duration}
        | {item["start_frame"] for item in video_items}
        | {item["start_frame"] + item["frames"] for item in video_items}
    )
    generated_frames = 0
    for start, end in itertools.pairwise(bounds):
        covering = [
            item
            for item in video_items
            if item["start_frame"] <= start < item["start_frame"] + item["frames"]
        ]
        if covering:
            # Graphics are overlays and never occlude media. Inside a crossfade
            # both items on the top track are visible; the span counts as
            # generated when either is (upper bound for a maximum-share promise).
            top_order = max(order[item["track_id"]] for item in covering)
            if any(
                item["asset_id"] in generated
                for item in covering
                if order[item["track_id"]] == top_order
            ):
                generated_frames += min(end, duration) - start
    return generated_frames / duration


_GRAPHIC_FIELDS = frozenset(
    {
        "id",
        "track_id",
        "kind",
        "template",
        "vars",
        "start_frame",
        "frames",
        "fade_in_frames",
        "fade_out_frames",
        "opacity",
    }
)
_GRAPHIC_VAR_MAX_LENGTH = 200
# Same grammar as integrations/local-production/templates.mjs variable names.
_GRAPHIC_VAR_NAME = r"[a-z][a-z0-9_]{0,31}"


def _graphic_var_ok(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if _is_number(value):
        return math.isfinite(value)
    # Length in UTF-16 code units, matching JavaScript string length in Node.
    return (
        isinstance(value, str)
        and 1 <= len(value.encode("utf-16-le")) // 2 <= _GRAPHIC_VAR_MAX_LENGTH
    )


def _check_fades(r: Result, label: str, item: dict[str, Any]) -> None:
    fades = [item.get(key, 0) for key in ("fade_in_frames", "fade_out_frames")]
    if isinstance(item.get("frames"), int) and all(
        isinstance(value, int) for value in fades
    ):
        r.require(
            sum(fades) <= item["frames"],
            f"{label} fade_in_frames + fade_out_frames exceed frames {item['frames']}",
        )


def _check_ducking(r: Result, data: dict[str, Any], tracks: dict[str, Any]) -> None:
    for index, track in enumerate(data.get("tracks", [])):
        duck = track.get("duck") if isinstance(track, dict) else None
        if not isinstance(duck, dict):
            continue
        label = f"tracks[{index}] ({track.get('id')})"
        r.require(
            track.get("kind") == "audio",
            f"{label} duck is only allowed on audio tracks",
        )
        under = duck.get("under_track_id")
        target = tracks.get(str(under))
        if under == track.get("id"):
            r.errors.append(f"{label} duck must not reference its own track")
        elif target is None:
            r.errors.append(f"{label} duck references unknown track {under!r}")
        else:
            r.require(
                target.get("kind") in {"video", "audio"},
                f"{label} duck must reference a video or audio track",
            )
            r.require(
                "duck" not in target,
                f"{label} duck target {under} must not have its own duck (one level only)",
            )


def _check_same_track_timing(
    r: Result, by_track: dict[str, list[tuple[int, int, str, dict[str, Any]]]]
) -> None:
    """Same-track items must not overlap, except a declared crossfade.

    Matches Node validateV2: the overlap is the immediately preceding media
    item's end minus this item's start and must equal the crossfade frames,
    which may not exceed either item's length; any other overlap is invalid.
    """
    for track_id, spans in by_track.items():
        spans.sort(key=lambda span: (span[0], span[1]))
        for index, (start, end, item_id, item) in enumerate(spans):
            transition = item.get("transition_in")
            crossfade = (
                transition.get("frames") if isinstance(transition, dict) else None
            )
            if crossfade is not None:
                previous = spans[index - 1] if index else None
                prev_start, prev_end, prev_id, prev_item = previous or (0, 0, "", {})
                overlap = prev_end - start
                r.require(
                    previous is not None
                    and prev_item.get("kind") == "media"
                    and prev_start < start
                    and overlap == crossfade
                    and crossfade <= min(end - start, prev_end - prev_start),
                    f"track {track_id} item {item_id} crossfade of {crossfade} frames "
                    "must exactly overlap the end of its preceding media item"
                    + (f" {prev_id}" if previous else ""),
                )
            for previous_index in range(index):
                prev_start, prev_end, prev_id, _ = spans[previous_index]
                if prev_end <= start:
                    continue
                if crossfade is not None and previous_index == index - 1:
                    continue  # judged above
                r.errors.append(
                    f"track {track_id} items {prev_id} and {item_id} "
                    "overlap without a matching crossfade"
                )


def _check_template_bindings(r: Result, data: dict[str, Any]) -> None:
    """When present, graphic_templates pins exactly the templates graphics use."""
    bindings = data.get("graphic_templates")
    if not isinstance(bindings, list):
        return
    used = {
        str(item.get("template"))
        for item in data.get("items") or []
        if isinstance(item, dict) and item.get("kind") == "graphic"
    }
    bound: set[str] = set()
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            continue
        template_id = str(binding.get("id"))
        r.require(
            template_id not in bound,
            f"graphic_templates[{index}] duplicates binding for {template_id!r}",
        )
        bound.add(template_id)
        r.require(
            binding.get("file") == f"templates/{binding.get('sha256')}.json",
            f"graphic_templates[{index}] file must be templates/<sha256>.json",
        )
        r.require(
            template_id in used,
            f"graphic_templates[{index}] binds {template_id!r}, which no graphic uses",
        )
    for template_id in sorted(used - bound):
        r.errors.append(f"graphic template {template_id!r} has no graphic_templates binding")


def validate_edit_document(data: dict[str, Any]) -> Result:
    r = Result()
    revision = data.get("revision")
    if revision == 1:
        r.require(
            data.get("parent_sha256") is None,
            "revision 1 must have parent_sha256 null",
        )
    else:
        r.require(
            isinstance(data.get("parent_sha256"), str),
            "revision > 1 requires parent_sha256",
        )
    fps = data.get("canvas", {}).get("fps")
    assets = _indexed_ids(r, data.get("assets"), "assets")
    for asset_id, asset in assets.items():
        if "frame_rate" in asset:
            r.require(
                asset.get("video") is True,
                f"asset {asset_id!r} frame_rate requires a video stream",
            )
    tracks = _indexed_ids(r, data.get("tracks"), "tracks")
    items = _indexed_ids(r, data.get("items"), "items")
    _check_ducking(r, data, tracks)
    by_track: dict[str, list[tuple[int, int, str, dict[str, Any]]]] = {}
    for index, item in enumerate(data.get("items", [])):
        label = f"items[{index}] ({item.get('id')})"
        track = tracks.get(str(item.get("track_id")))
        if track is None:
            r.errors.append(
                f"{label} references unknown track {item.get('track_id')!r}"
            )
        track_kind = track.get("kind") if track else None
        timed = False
        if item.get("kind") == "media":
            timed = True
            for key in (
                "asset_id",
                "start_frame",
                "frames",
                "source_in_seconds",
                "volume",
            ):
                r.require(key in item, f"{label} media item requires {key}")
            for key in ("text", "style", "link", "template", "vars"):
                r.require(key not in item, f"{label} media item must not set {key}")
            if track_kind == "audio":
                for key in ("fit", "opacity", "transform"):
                    r.require(
                        key not in item, f"{label} audio-track item must not set {key}"
                    )
            r.require(
                track_kind != "caption",
                f"{label} media item cannot be on a caption track",
            )
            _check_fades(r, label, item)
            asset = assets.get(str(item.get("asset_id")))
            if "asset_id" in item and asset is None:
                r.errors.append(
                    f"{label} references unknown asset {item.get('asset_id')!r}"
                )
            if asset is not None:
                if track_kind == "video":
                    r.require(
                        asset.get("video") is True,
                        f"{label} on a video track requires an asset with video",
                    )
                if track_kind == "audio":
                    r.require(
                        asset.get("audio") is True,
                        f"{label} on an audio track requires an asset with audio",
                    )
                if (
                    _is_number(item.get("source_in_seconds"))
                    and isinstance(item.get("frames"), int)
                    and _is_number(item.get("speed", 1))
                    and fps
                    and _is_number(asset.get("duration"))
                ):
                    source_end = media_source_end(item, fps)
                    r.require(
                        source_end <= asset["duration"] + _ASSET_DURATION_TOLERANCE,
                        f"{label} source range ends at {source_end:g}s beyond asset "
                        f"duration {asset['duration']:g}s",
                    )
        elif item.get("kind") == "graphic":
            timed = True
            r.require(
                track_kind == "video",
                f"{label} graphic item must be on a video track",
            )
            for key in ("template", "vars", "start_frame", "frames"):
                r.require(key in item, f"{label} graphic item requires {key}")
            for key in sorted(set(item) - _GRAPHIC_FIELDS):
                r.errors.append(f"{label} graphic item must not set {key}")
            variables = item.get("vars")
            if isinstance(variables, dict):
                for name, value in variables.items():
                    r.require(
                        re.fullmatch(_GRAPHIC_VAR_NAME, str(name)) is not None,
                        f"{label} vars key {name!r} must match {_GRAPHIC_VAR_NAME}",
                    )
                    r.require(
                        _graphic_var_ok(value),
                        f"{label} vars.{name} must be a string of 1-"
                        f"{_GRAPHIC_VAR_MAX_LENGTH} characters, a finite number "
                        "or a boolean",
                    )
            _check_fades(r, label, item)
        elif item.get("kind") == "caption":
            r.require(
                track_kind == "caption",
                f"{label} caption item must be on a caption track",
            )
            r.require(nonempty(item.get("text")), f"{label} caption item requires text")
            for key in (
                "asset_id",
                "source_in_seconds",
                "volume",
                "fit",
                "opacity",
                "transform",
                "speed",
                "fade_in_frames",
                "fade_out_frames",
                "transition_in",
                "template",
                "vars",
            ):
                r.require(key not in item, f"{label} caption item must not set {key}")
            link = item.get("link")
            if isinstance(link, dict):
                for key in ("start_frame", "frames"):
                    r.require(
                        key not in item, f"{label} linked caption must not set {key}"
                    )
                target = items.get(str(link.get("item_id")))
                r.require(
                    target is not None and target.get("kind") == "media",
                    f"{label} link must reference a media item, got {link.get('item_id')!r}",
                )
                linked_asset = assets.get(str((target or {}).get("asset_id")))
                if linked_asset is not None and _is_number(link.get("source_to")):
                    r.require(
                        link["source_to"]
                        <= linked_asset["duration"] + _ASSET_DURATION_TOLERANCE,
                        f"{label} link.source_to exceeds the linked asset duration",
                    )
                if _is_number(link.get("source_from")) and _is_number(
                    link.get("source_to")
                ):
                    r.require(
                        link["source_to"] > link["source_from"],
                        f"{label} link.source_to must be greater than link.source_from",
                    )
                    if (
                        target is not None
                        and target.get("kind") == "media"
                        and fps
                        and all(
                            key in target
                            for key in ("start_frame", "frames", "source_in_seconds")
                        )
                        and _is_number(target.get("speed", 1))
                        and link["source_to"] > link["source_from"]
                    ):
                        r.warn(
                            linked_caption_frames(item, target, fps) is not None,
                            f"{label} link range lies outside the linked item's source range",
                        )
            else:
                for key in ("start_frame", "frames"):
                    r.require(
                        key in item, f"{label} caption without link requires {key}"
                    )
        if (
            timed
            and track is not None
            and isinstance(item.get("start_frame"), int)
            and isinstance(item.get("frames"), int)
        ):
            by_track.setdefault(track["id"], []).append(
                (
                    item["start_frame"],
                    item["start_frame"] + item["frames"],
                    str(item.get("id")),
                    item,
                )
            )
    _check_same_track_timing(r, by_track)
    _check_template_bindings(r, data)
    if r.ok and fps:
        duration = edit_document_duration_frames(data)
        r.require(duration >= 1, "edit duration must be at least one frame")
        r.require(
            duration <= EDIT_DOCUMENT_MAX_SECONDS * fps,
            f"edit duration {duration} frames exceeds {EDIT_DOCUMENT_MAX_SECONDS} seconds",
        )
    return r


def render_qa_expected_verdict(checks: list[dict[str, Any]]) -> str:
    statuses = {check.get("status") for check in checks if isinstance(check, dict)}
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "pass_with_warnings"
    return "pass"


def validate_render_qa(data: dict[str, Any]) -> Result:
    r = Result()
    review = data.get("review", {})
    if review.get("status") == "done":
        r.require(
            review.get("decision") != "pending",
            "completed review requires a decision other than pending",
        )
        r.require(
            nonempty(review.get("reviewer")), "completed review requires reviewer"
        )
    if review.get("decision") == "pending":
        r.require(
            review.get("status") == "pending",
            "pending decision requires review.status pending",
        )
    checks = data.get("checks", [])
    expected = render_qa_expected_verdict(checks)
    r.require(
        data.get("verdict") == expected,
        f"verdict {data.get('verdict')!r} contradicts checks; expected {expected!r}",
    )
    r.warn(
        not any(check.get("status") == "unknown" for check in checks),
        "some checks are unknown; the verdict does not cover them",
    )
    samples = _indexed_ids(r, data.get("samples"), "samples")
    _indexed_ids(r, checks, "checks")
    findings = review.get("findings", [])
    _indexed_ids(r, findings, "review.findings")
    for group, entries in (("checks", checks), ("review.findings", findings)):
        for index, entry in enumerate(entries):
            for ref in entry.get("refs", []):
                sample_id = ref.get("sample_id")
                r.require(
                    sample_id is None or sample_id in samples,
                    f"{group}[{index}] references unknown sample {sample_id!r}",
                )
    for index, finding in enumerate(findings):
        if finding.get("severity") == "critical":
            r.require(
                nonempty(finding.get("fix")),
                f"review.findings[{index}] critical finding requires fix",
            )
    return r


def validate_production_plan(data: dict[str, Any]) -> Result:
    r = Result()
    promises = _indexed_ids(r, data.get("delivery_promises"), "delivery_promises")
    for promise_id, promise in promises.items():
        check = promise.get("check", {})
        kind = check.get("kind")
        label = f"delivery promise {promise_id}"
        if kind == "duration_range":
            minimum, maximum = check.get("min"), check.get("max")
            r.require(
                _is_number(minimum) and _is_number(maximum),
                f"{label} duration_range requires min and max",
            )
            if _is_number(minimum) and _is_number(maximum):
                r.require(0 <= minimum <= maximum, f"{label} requires 0 <= min <= max")
        elif kind == "max_generated_share":
            maximum = check.get("max")
            r.require(
                _is_number(maximum) and 0 <= maximum <= 1,
                f"{label} max_generated_share requires max between 0 and 1",
            )
            r.require(
                "min" not in check, f"{label} max_generated_share must not set min"
            )
        else:
            r.require(
                "min" not in check and "max" not in check,
                f"{label} {kind} must not set min or max",
            )
    beats = _indexed_ids(r, data.get("beats"), "beats")
    total = 0.0
    for beat_id, beat in beats.items():
        label = f"beat {beat_id}"
        if _is_number(beat.get("duration_seconds")):
            total += beat["duration_seconds"]
        source_kind = beat.get("source_kind")
        r.require(
            beat.get("generation_ref") is None or source_kind == "generate",
            f"{label} generation_ref requires source_kind generate",
        )
        r.require(
            beat.get("selection") is None or source_kind != "tbd",
            f"{label} with source_kind tbd must not have a selection",
        )
        selection = beat.get("selection")
        if not isinstance(selection, dict):
            continue
        start = selection.get("source_start_seconds")
        end = selection.get("source_end_seconds")
        if not (_is_number(start) and _is_number(end)):
            continue
        r.require(end > start, f"{label} selection end must be after start")
        for index, evidence in enumerate(selection.get("evidence", [])):
            ev_start = evidence.get("start_seconds")
            ev_end = evidence.get("end_seconds")
            if not (_is_number(ev_start) and _is_number(ev_end)):
                continue
            r.require(
                ev_end >= ev_start, f"{label} evidence[{index}] end precedes start"
            )
            tolerance = SELECTION_EVIDENCE_TOLERANCE_SECONDS
            r.require(
                ev_start <= end + tolerance and ev_end >= start - tolerance,
                f"{label} evidence[{index}] lies outside the selected source range "
                f"(±{tolerance:g}s)",
            )
    target = data.get("output", {}).get("duration_seconds_target")
    if _is_number(target) and target > 0 and beats:
        r.warn(
            abs(total - target) <= max(1.0, target * 0.2),
            f"beat durations total {total:g}s; output target is {target:g}s",
        )
    return r


def validate_video_production(data: dict[str, Any]) -> Result:
    r = Result()
    stages = data.get("stages", [])
    r.require(
        [stage.get("id") for stage in stages] == list(VIDEO_STAGES),
        "stages must list " + ", ".join(VIDEO_STAGES) + " in order",
    )
    policy = data.get("policy", {})
    budget = policy.get("budget", {})
    if budget.get("mode") == "cap":
        r.require(
            _is_number(budget.get("cap")), "budget mode cap requires a numeric cap"
        )
    max_rounds = policy.get("max_revision_rounds")
    if isinstance(max_rounds, int) and isinstance(data.get("revision_rounds"), int):
        r.require(
            data["revision_rounds"] <= max_rounds,
            "revision_rounds must not exceed policy.max_revision_rounds",
        )
    required_approval = set(policy.get("approval_required", []))
    if policy.get("export_requires_human_review") is True:
        required_approval.add("inspect")
    for stage in stages:
        stage_id = stage.get("id")
        if stage.get("status") == "awaiting_approval":
            # select/generate also wait for approval when they change the
            # approved plan's structure, regardless of policy.
            r.require(
                stage_id in required_approval
                or (
                    stage_id in {"select", "generate"}
                    and str(stage.get("note", "")).startswith(
                        "plan structure changed since it was last accepted"
                    )
                ),
                f"stage {stage_id} awaits approval it does not require",
            )
        if stage.get("status") == "completed" and stage_id in required_approval:
            r.require(
                stage.get("approval") is not None,
                f"stage {stage_id} is completed without its required approval",
            )
        if stage.get("status") == "skipped":
            r.require(
                nonempty(stage.get("note")), f"skipped stage {stage_id} requires a note"
            )
    ledger = _indexed_ids(r, data.get("ledger"), "ledger")
    for entry_id, entry in ledger.items():
        settled = entry.get("status") == "settled"
        r.require(
            (entry.get("actual") is not None) == settled,
            f"ledger {entry_id} actual must be set exactly when settled",
        )
    return r


def _no_semantic_validation(data: dict[str, Any]) -> Result:
    del data
    return Result()


def _call_semantic_validator(
    schema_version: str, data: dict[str, Any], context: ValidationContext
) -> Result:
    simple: dict[str, Callable[[dict[str, Any]], Result]] = {
        "creative-craft.brief.v1": validate_brief,
        "creative-craft.asset-ledger.v1": validate_asset_ledger,
        "creative-craft.concept-routes.v1": validate_concept_routes,
        "creative-craft.critique.v1": validate_critique,
        "creative-craft.evaluation.v1": validate_evaluation,
        "creative-craft.delivery.v1": validate_delivery,
        "creative-craft.project-manifest.v1": validate_project_manifest,
        "creative-craft.project-manifest.v2": validate_project_manifest,
        "creative-craft.creative-direction.v1": validate_creative_direction,
        "creative-craft.copy-sheet.v1": validate_copy_sheet,
        "creative-craft.output-inspection.v1": validate_output_inspection,
        "creative-craft.revision-lineage.v1": validate_revision_lineage,
        "creative-craft.evaluation.v2": validate_evaluation_v2,
        "creative-craft.delivery.v2": validate_delivery_v2,
        "creative-craft.brand-pack.v1": validate_brand_pack_artifact,
        "creative-craft.brand-binding.v1": validate_brand_binding,
        "creative-craft.reference-pack.v1": validate_reference_pack_artifact,
        "creative-craft.reference-binding.v1": validate_reference_binding,
        "creative-craft.reference-binding-history.v1": validate_reference_binding_history,
        "creative-craft.edit-document.v2": validate_edit_document,
        "creative-craft.render-qa.v1": validate_render_qa,
        "creative-craft.production-plan.v1": validate_production_plan,
        "creative-craft.video-production.v1": validate_video_production,
    }
    if schema_version in {"creative-craft.image-job.v1", "creative-craft.image-job.v2"}:
        return validate_image_job(data, context)
    if schema_version in {"creative-craft.video-job.v1", "creative-craft.video-job.v2"}:
        return validate_video_job(data, context)
    if schema_version == "creative-craft.execution-receipt.v1":
        return validate_execution_receipt(data, context)
    return simple.get(schema_version, _no_semantic_validation)(data)


SCHEMA_TO_KIND = {
    schema_version: entry["kind"] for schema_version, entry in ARTIFACT_REGISTRY.items()
}


def validate_data(
    data: dict[str, Any], kind: str = "auto", context: ValidationContext | None = None
) -> tuple[str, Result]:
    context = context or ValidationContext()
    schema_version = str(data.get("schema_version"))
    entry = ARTIFACT_REGISTRY.get(schema_version)
    if entry is None:
        return "unknown", Result(
            errors=[
                f"cannot infer kind from schema_version {data.get('schema_version')!r}"
            ]
        )
    resolved = str(entry["kind"])
    if kind != "auto" and kind != resolved:
        return resolved, Result(
            errors=[
                f"artifact kind {resolved!r} does not match requested kind {kind!r}"
            ]
        )
    structural = validate_against_schema(
        data, context.schemas_dir / str(entry["schema"])
    )
    if not structural.ok:
        return resolved, structural
    structural.extend(_call_semantic_validator(schema_version, data, context))
    return resolved, structural


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


ARTIFACT_ID_FIELDS = {
    "brief": "brief_id",
    "concept-routes": None,
    "creative-direction": "direction_id",
    "copy-sheet": "copy_sheet_id",
    "image": "job_id",
    "video": "job_id",
    "execution-receipt": "receipt_id",
    "output-inspection": "inspection_id",
    "revision-lineage": "revision_id",
    "evaluation": "evaluation_id",
    "delivery": "delivery_id",
    "project-manifest": "manifest_id",
    "critique": "critique_id",
    "asset-ledger": None,
    "brand-pack": "pack_id",
    "brand-binding": "binding_id",
    "reference-pack": "reference_pack_id",
    "reference-binding": "binding_id",
    "reference-binding-history": "history_id",
    "edit-document": None,
    "render-qa": "qa_id",
    "production-plan": "plan_id",
    "video-production": "production_id",
}
