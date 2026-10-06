from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GateSpec:
    gate_id: str
    command: tuple[str, ...]
    profiles: frozenset[str]
    timeout_seconds: int
    execution: str
    priority: int = 0
    depends_on: tuple[str, ...] = ()
    environment: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    status: str
    exit_code: int | None
    duration_ms: float
    stdout_summary: str
    stderr_summary: str
    error_code: str | None = None

    @property
    def passed(self) -> bool:
        return self.status == "passed"
