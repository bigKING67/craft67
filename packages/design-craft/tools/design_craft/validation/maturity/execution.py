from __future__ import annotations

from .model import GateRunner, MaturityContext, MaturityGateResult
from .process_runner import bounded, run_command


def gate_result(
    gate_id: str,
    passed: bool,
    duration_ms: float,
    evidence: object,
    error: str = "",
) -> MaturityGateResult:
    return MaturityGateResult(
        gate_id=gate_id,
        status="passed" if passed else "failed",
        duration_ms=round(duration_ms, 3),
        evidence=evidence,
        error="" if passed else bounded(error or "gate failed"),
    )


def command_gate(
    gate_id: str,
    command: list[str],
    *,
    timeout: int = 180,
    evidence: object | None = None,
) -> GateRunner:
    def evaluate(context: MaturityContext) -> MaturityGateResult:
        result = run_command(command, root=context.root, timeout=timeout)
        return gate_result(
            gate_id,
            result.returncode == 0,
            result.duration_ms,
            evidence if evidence is not None else {"command": command},
            result.stderr or result.stdout or result.error_code or "command failed",
        )

    return evaluate
