from __future__ import annotations

from .model import GateSpec


SOURCE_BOOTSTRAP_GATES = frozenset(
    {
        "skill-schema",
        "repository-contracts",
        "tooling-contracts",
        "package-boundary",
        "public-repository",
        "workflow-contract",
        "source-test-suite",
        "development-maturity",
    }
)

REQUIRED_GATES = {
    "contracts": frozenset(
        {
            "workflow-contract",
            "source-test-suite",
        }
    ),
    "portable": SOURCE_BOOTSTRAP_GATES,
    "local": SOURCE_BOOTSTRAP_GATES | {"install-provenance"},
    "operational-release": SOURCE_BOOTSTRAP_GATES
    | {"install-provenance", "operational-evidence"},
    "certified-release": SOURCE_BOOTSTRAP_GATES
    | {"install-provenance", "certified-evidence"},
}


def profile_contract_errors(
    gates: tuple[GateSpec, ...], profile: str
) -> list[str]:
    required = REQUIRED_GATES.get(profile)
    if required is None:
        return [f"validation profile contract is undefined: {profile}"]

    errors: list[str] = []
    gate_ids = {gate.gate_id for gate in gates}
    missing = sorted(required - gate_ids)
    if missing:
        errors.append(
            f"validation profile {profile} is missing bootstrap gates: {missing}"
        )

    if profile == "contracts":
        non_parallel = sorted(
            gate.gate_id for gate in gates if gate.execution != "parallel"
        )
        if non_parallel:
            errors.append(
                "contracts profile gates must all be parallel: " + str(non_parallel)
            )
        return errors

    development_gate = next(
        (gate for gate in gates if gate.gate_id == "development-maturity"),
        None,
    )
    if development_gate is None:
        return errors
    parallel_gate_ids = {
        gate.gate_id for gate in gates if gate.execution == "parallel"
    }
    if development_gate.execution != "serial":
        errors.append("development maturity must remain a serial gate")
    elif set(development_gate.depends_on) != parallel_gate_ids:
        errors.append("development maturity must depend on every parallel source gate")
    return errors


def require_profile_contract(gates: tuple[GateSpec, ...], profile: str) -> None:
    errors = profile_contract_errors(gates, profile)
    if errors:
        raise ValueError("; ".join(errors))
