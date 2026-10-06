from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..repo import repo_path


SCHEMA = "design-craft.release-policy.v1"
LEVELS = ("operational_95", "certified_100")
EXPECTED_LEVEL_FIELDS = {
    "operational_95": {
        "required_hosts": ("codex", "pi"),
        "required_native": ("ios_simulator", "android_emulator"),
        "allowed_unverified": ("cursor", "claude", "physical_device"),
        "required_domains": (
            "contract_completeness",
            "operational_maturity",
            "performance_regression",
            "comparative_evaluation",
        ),
        "assets": (
            "design-craft-{version}.tgz",
            "design-craft-{version}.tgz.sha256",
            "design-craft-v{version}-release-assets.json",
            "design-craft-v{version}.spdx.json",
        ),
    },
    "certified_100": {
        "required_hosts": ("codex", "pi", "cursor", "claude"),
        "required_native": (
            "ios_simulator",
            "android_emulator",
            "physical_device",
        ),
        "allowed_unverified": (),
        "required_domains": (
            "contract_completeness",
            "operational_maturity",
            "performance_regression",
            "comparative_evaluation",
            "release_certification",
        ),
        "assets": (
            "design-craft-{version}.tgz",
            "design-craft-{version}.tgz.sha256",
            "design-craft-v{version}-release-assets.json",
            "design-craft-v{version}.spdx.json",
            "design-craft-v{version}-native-runtime.tgz",
            "design-craft-v{version}-native-runtime.tgz.sha256",
            "design-craft-v{version}-native-runtime.json",
        ),
    },
}


@dataclass(frozen=True)
class ReleaseLevel:
    name: str
    score: int
    required_hosts: tuple[str, ...]
    required_native: tuple[str, ...]
    allowed_unverified: tuple[str, ...]
    required_domains: tuple[str, ...]
    asset_templates: tuple[str, ...]
    permanent_native_bundle: bool
    extends: str | None = None

    def assets(self, version: str) -> tuple[str, ...]:
        return tuple(template.format(version=version) for template in self.asset_templates)


def _string_tuple(value: object, label: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValueError(f"{label} must be an array")
    values = tuple(item for item in value if isinstance(item, str) and item.strip())
    if len(values) != len(value) or len(values) != len(set(values)):
        raise ValueError(f"{label} must contain unique non-empty strings")
    return values


def load_policy(path: Path | None = None) -> dict[str, ReleaseLevel]:
    source = path or repo_path("contracts/release/policy.json")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA or payload.get("version") != 1:
        raise ValueError(f"release policy must use {SCHEMA} version 1")
    raw_levels = payload.get("levels")
    if not isinstance(raw_levels, dict) or tuple(raw_levels) != LEVELS:
        raise ValueError(f"release policy levels must be {LEVELS}")
    result: dict[str, ReleaseLevel] = {}
    for name in LEVELS:
        raw = raw_levels[name]
        if not isinstance(raw, dict):
            raise ValueError(f"release level {name} must be an object")
        score = raw.get("score")
        expected_score = 95 if name == "operational_95" else 100
        if score != expected_score:
            raise ValueError(f"{name}.score must be {expected_score}")
        permanent = raw.get("permanent_native_bundle")
        if not isinstance(permanent, bool):
            raise ValueError(f"{name}.permanent_native_bundle must be boolean")
        result[name] = ReleaseLevel(
            name=name,
            score=score,
            required_hosts=_string_tuple(raw.get("required_hosts"), f"{name}.required_hosts"),
            required_native=_string_tuple(raw.get("required_native"), f"{name}.required_native"),
            allowed_unverified=_string_tuple(
                raw.get("allowed_unverified"), f"{name}.allowed_unverified", allow_empty=True
            ),
            required_domains=_string_tuple(raw.get("required_domains"), f"{name}.required_domains"),
            asset_templates=_string_tuple(raw.get("assets"), f"{name}.assets"),
            permanent_native_bundle=permanent,
            extends=raw.get("extends") if isinstance(raw.get("extends"), str) else None,
        )
        expected = EXPECTED_LEVEL_FIELDS[name]
        observed_fields = {
            "required_hosts": result[name].required_hosts,
            "required_native": result[name].required_native,
            "allowed_unverified": result[name].allowed_unverified,
            "required_domains": result[name].required_domains,
            "assets": result[name].asset_templates,
        }
        for field, observed in observed_fields.items():
            if observed != expected[field]:
                raise ValueError(f"{name}.{field} must match the v1 release contract")
    operational = result["operational_95"]
    certified = result["certified_100"]
    if certified.extends != operational.name:
        raise ValueError("certified_100 must extend operational_95")
    if not set(operational.required_hosts).issubset(certified.required_hosts):
        raise ValueError("certified hosts must include operational hosts")
    if not set(operational.required_native).issubset(certified.required_native):
        raise ValueError("certified native requirements must include operational requirements")
    if len(operational.asset_templates) != 4 or len(certified.asset_templates) != 7:
        raise ValueError("operational and certified asset sets must contain exactly 4 and 7 assets")
    return result
