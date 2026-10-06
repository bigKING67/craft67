from __future__ import annotations

import json
from pathlib import Path

from ..repo import repo_path
from .model import GateSpec


REGISTRY_SCHEMA = "design-craft.validation-gates.v1"
KNOWN_PROFILES = frozenset(
    {"contracts", "portable", "local", "operational-release", "certified-release"}
)
KNOWN_EXECUTION = frozenset({"parallel", "serial"})


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_string_list(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty string array")
    normalized = tuple(_require_string(item, f"{label}[]") for item in value)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{label} must not contain duplicates")
    return normalized


def load_registry(path: Path | None = None) -> tuple[GateSpec, ...]:
    registry_path = path or repo_path("contracts/validation/gates.json")
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if payload.get("schema") != REGISTRY_SCHEMA:
        raise ValueError(f"validation registry schema must be {REGISTRY_SCHEMA}")
    raw_gates = payload.get("gates")
    if not isinstance(raw_gates, list) or not raw_gates:
        raise ValueError("validation registry must define at least one gate")

    gates: list[GateSpec] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_gates):
        if not isinstance(raw, dict):
            raise ValueError(f"gates[{index}] must be an object")
        gate_id = _require_string(raw.get("id"), f"gates[{index}].id")
        if gate_id in seen:
            raise ValueError(f"duplicate validation gate id: {gate_id}")
        seen.add(gate_id)
        command = _require_string_list(raw.get("command"), f"{gate_id}.command")
        profiles = frozenset(_require_string_list(raw.get("profiles"), f"{gate_id}.profiles"))
        unknown_profiles = profiles - KNOWN_PROFILES
        if unknown_profiles:
            raise ValueError(f"{gate_id}.profiles contains unknown values: {sorted(unknown_profiles)}")
        timeout_seconds = raw.get("timeout_seconds")
        if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise ValueError(f"{gate_id}.timeout_seconds must be a positive integer")
        execution = _require_string(raw.get("execution"), f"{gate_id}.execution")
        if execution not in KNOWN_EXECUTION:
            raise ValueError(f"{gate_id}.execution must be one of {sorted(KNOWN_EXECUTION)}")
        priority = raw.get("priority", 0)
        if not isinstance(priority, int) or isinstance(priority, bool) or priority < 0:
            raise ValueError(f"{gate_id}.priority must be a non-negative integer")
        depends_on_raw = raw.get("depends_on", [])
        if not isinstance(depends_on_raw, list):
            raise ValueError(f"{gate_id}.depends_on must be an array")
        depends_on = tuple(_require_string(item, f"{gate_id}.depends_on[]") for item in depends_on_raw)
        environment_raw = raw.get("environment", {})
        if not isinstance(environment_raw, dict):
            raise ValueError(f"{gate_id}.environment must be an object")
        environment = {
            _require_string(key, f"{gate_id}.environment key"): _require_string(
                value, f"{gate_id}.environment[{key!r}]"
            )
            for key, value in environment_raw.items()
        }
        gates.append(
            GateSpec(
                gate_id=gate_id,
                command=command,
                profiles=profiles,
                timeout_seconds=timeout_seconds,
                execution=execution,
                priority=priority,
                depends_on=depends_on,
                environment=environment,
            )
        )

    gate_ids = {gate.gate_id for gate in gates}
    gate_order = {gate.gate_id: index for index, gate in enumerate(gates)}
    for gate in gates:
        missing = set(gate.depends_on) - gate_ids
        if missing:
            raise ValueError(f"{gate.gate_id}.depends_on references unknown gates: {sorted(missing)}")
        if gate.gate_id in gate.depends_on:
            raise ValueError(f"{gate.gate_id} must not depend on itself")
        if gate.execution == "parallel" and gate.depends_on:
            raise ValueError(f"parallel gate {gate.gate_id} must not declare dependencies")
        later_dependencies = sorted(
            dependency
            for dependency in gate.depends_on
            if gate_order[dependency] >= gate_order[gate.gate_id]
        )
        if later_dependencies:
            raise ValueError(
                f"{gate.gate_id}.depends_on must reference earlier gates: "
                f"{later_dependencies}"
            )
    return tuple(gates)


def select_gates(gates: tuple[GateSpec, ...], profile: str) -> tuple[GateSpec, ...]:
    if profile not in KNOWN_PROFILES:
        raise ValueError(f"unknown validation profile: {profile}")
    selected = tuple(gate for gate in gates if profile in gate.profiles)
    selected_ids = {gate.gate_id for gate in selected}
    for gate in selected:
        missing = set(gate.depends_on) - selected_ids
        if missing:
            raise ValueError(
                f"profile {profile} selects {gate.gate_id} without dependencies: {sorted(missing)}"
            )
    return selected
