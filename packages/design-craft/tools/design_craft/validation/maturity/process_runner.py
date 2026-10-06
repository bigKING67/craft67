from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


SUMMARY_LIMIT = 1_500


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int | None
    duration_ms: float
    stdout: str
    stderr: str
    error_code: str | None


def bounded(value: str) -> str:
    normalized = value.strip()
    if len(normalized) <= SUMMARY_LIMIT:
        return normalized
    return normalized[:SUMMARY_LIMIT] + "\n...[truncated]"


def _resolve_command(command: list[str]) -> list[str]:
    resolved = list(command)
    if resolved and resolved[0] == "bash":
        executable = shutil.which(os.environ.get("DESIGN_CRAFT_BASH") or "bash")
        if executable and os.name == "nt":
            normalized = executable.replace("\\", "/").lower()
            if normalized.endswith("/windows/system32/bash.exe"):
                executable = None
        if not executable:
            raise OSError(
                "Git Bash is required; set DESIGN_CRAFT_BASH to Git for Windows bash.exe"
            )
        resolved[0] = executable
    return resolved


def run_command(
    command: list[str],
    *,
    root: Path,
    timeout: int = 180,
    environment: dict[str, str] | None = None,
) -> CommandResult:
    started = time.perf_counter()
    try:
        resolved = _resolve_command(command)
        env = dict(os.environ)
        env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
        if environment:
            env.update(environment)
        completed = subprocess.run(
            resolved,
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=tuple(command),
            returncode=None,
            duration_ms=round((time.perf_counter() - started) * 1_000, 3),
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            error_code="TIMEOUT",
        )
    except OSError as exc:
        return CommandResult(
            command=tuple(command),
            returncode=None,
            duration_ms=round((time.perf_counter() - started) * 1_000, 3),
            stdout="",
            stderr=str(exc),
            error_code="SPAWN_FAILED",
        )
    return CommandResult(
        command=tuple(command),
        returncode=completed.returncode,
        duration_ms=round((time.perf_counter() - started) * 1_000, 3),
        stdout=completed.stdout,
        stderr=completed.stderr,
        error_code=None if completed.returncode == 0 else "NONZERO_EXIT",
    )


def json_payload(result: CommandResult) -> dict[str, object]:
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
