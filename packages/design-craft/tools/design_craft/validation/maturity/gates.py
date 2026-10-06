from __future__ import annotations

import re
import sys

from .development import (
    RUNTIME_SCRIPTS,
    comparative_contracts,
    contract_completeness,
    cross_agent_contracts,
    detector_degraded_contract,
    l4_evidence_contract,
    platform_fixtures,
    portable_route_fallback,
    portable_runtime_payload,
    route_pack,
    upstream_lock_parity,
)
from .evidence import (
    TASKS,
    comparative_evaluation,
    host_current_source,
    native_current_source,
    performance_regression,
)
from .execution import command_gate, gate_result
from .model import GateRunner, MaturityContext, MaturityGateResult
from .repository import (
    clean_worktree,
    install_provenance,
    main_branch,
    release_metadata,
    upstream_remote_review,
)


STATIC_GATES: dict[str, GateRunner] = {
    "contract_completeness": contract_completeness,
    "release_metadata_candidate": release_metadata("candidate"),
    "release_metadata_final": release_metadata("final"),
    "portable_runtime_payload": portable_runtime_payload,
    "portable_route_fallback": portable_route_fallback,
    "detector_degraded_contract": detector_degraded_contract,
    "platform_fixtures": platform_fixtures,
    "upstream_lock_parity": upstream_lock_parity,
    "workflow_contract": command_gate(
        "workflow_contract",
        [
            sys.executable,
            "scripts/design_craft_workflow_validate.py",
            "--check",
            "--validate",
        ],
    ),
    "package_boundary": command_gate(
        "package_boundary",
        [
            sys.executable,
            "scripts/design_craft_package_validate.py",
            "--check",
            "--validate",
        ],
        timeout=240,
    ),
    "active_scope": command_gate(
        "active_scope",
        [
            sys.executable,
            "scripts/design_craft_active_scope_validate.py",
            "--root",
            ".",
        ],
    ),
    "route_pack": route_pack,
    "cross_agent_contracts": cross_agent_contracts,
    "comparative_contracts": comparative_contracts,
    "installer_contract": command_gate(
        "installer_contract",
        [
            sys.executable,
            "scripts/design_craft_parallel_unittest.py",
            "--jobs",
            "5",
            "--include-target",
            "tests.contract.test_installer",
        ],
        timeout=180,
    ),
    "l4_evidence_contract": l4_evidence_contract,
    "performance_regression": performance_regression,
    "comparative_evaluation": comparative_evaluation,
    "clean_worktree": clean_worktree,
    "install_provenance": install_provenance,
    "upstream_remote_review": upstream_remote_review,
    "main_branch": main_branch,
}


def gate_runner(gate_id: str) -> GateRunner:
    if gate_id in STATIC_GATES:
        return STATIC_GATES[gate_id]
    host_match = re.fullmatch(
        r"host_(codex|pi|cursor|claude)_current_source", gate_id
    )
    if host_match:
        return host_current_source(host_match.group(1))
    native_match = re.fullmatch(
        r"native_(ios_simulator|android_emulator|physical_device)_current_source",
        gate_id,
    )
    if native_match:
        return native_current_source(native_match.group(1))
    raise ValueError(f"no maturity gate runner registered for {gate_id}")


# Compatibility aliases for callers that imported the former private helpers.
_command_gate = command_gate
_result = gate_result
