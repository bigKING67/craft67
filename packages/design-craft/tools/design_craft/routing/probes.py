from __future__ import annotations

import json
import os
import shutil
import subprocess
import tomllib
from pathlib import Path


def child_process_env(**overrides: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.update(overrides)
    return environment


def bundled_model_catalog() -> tuple[dict[str, dict], str | None]:
    codex = shutil.which("codex")
    if not codex:
        return {}, "codex executable is unavailable; runtime model compatibility was not checked"
    try:
        completed = subprocess.run(
            [codex, "debug", "models", "--bundled"],
            env=child_process_env(),
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {}, f"failed to load bundled model catalog: {exc}"
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        return {}, f"codex debug models --bundled failed: {detail[:240]}"
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {}, f"bundled model catalog is not valid JSON: {exc}"
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return {}, "bundled model catalog does not contain a models list"
    return {
        str(item.get("slug")): item
        for item in models
        if isinstance(item, dict) and str(item.get("slug", "")).strip()
    }, None


def runtime_profiles(config: dict) -> list[dict[str, str]]:
    profiles: list[dict[str, str]] = []

    def add(role: str, model: object, reasoning: object = "") -> None:
        model_name = str(model or "").strip()
        if model_name:
            profiles.append(
                {
                    "role": role,
                    "model": model_name,
                    "reasoning": str(reasoning or "").strip(),
                }
            )

    add("main", config.get("model"), config.get("model_reasoning_effort"))
    add("review_model", config.get("review_model"))
    agents = config.get("agents")
    if isinstance(agents, dict):
        for role, raw in agents.items():
            if isinstance(raw, dict):
                add(f"agent:{role}", raw.get("model"), raw.get("model_reasoning_effort"))
    return profiles


def run_route_probe(
    source_root: Path,
    arguments: list[str],
    *,
    runtime_model: str | None = None,
    runtime_reasoning: str | None = None,
) -> tuple[int, dict, str]:
    route_plan = source_root / "tools/frontend_route_plan.sh"
    environment = child_process_env(
        CODEX_HOME=str(source_root),
        FRONTEND_WORKSPACE_ROOT=str(source_root),
        FRONTEND_PREFLIGHT_LOG_ENABLED="0",
        FRONTEND_ROUTE_TELEMETRY_LOG_ENABLED="0",
        FRONTEND_RUNTIME_SESSION_DISCOVERY="0",
    )
    environment.pop("CODEX_EFFECTIVE_MODEL", None)
    environment.pop("CODEX_EFFECTIVE_REASONING", None)
    if runtime_model is not None:
        environment["CODEX_EFFECTIVE_MODEL"] = runtime_model
    if runtime_reasoning is not None:
        environment["CODEX_EFFECTIVE_REASONING"] = runtime_reasoning
    try:
        completed = subprocess.run(
            ["bash", str(route_plan), *arguments],
            cwd=source_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, {}, str(exc)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        detail = (completed.stderr or completed.stdout).strip()
        return completed.returncode, {}, f"invalid route JSON: {exc}; {detail[:240]}"
    return completed.returncode, payload, (completed.stderr or "").strip()
