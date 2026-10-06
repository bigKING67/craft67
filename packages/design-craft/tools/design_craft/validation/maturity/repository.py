from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from ...release.metadata import validate_release_metadata
from .execution import command_gate, gate_result
from .model import GateRunner, MaturityContext, MaturityGateResult
from .process_runner import json_payload, run_command


def release_metadata(phase: str) -> GateRunner:
    gate_id = f"release_metadata_{phase}"

    def evaluate(context: MaturityContext) -> MaturityGateResult:
        started = time.perf_counter()
        payload = validate_release_metadata(phase=phase, root=context.root)
        return gate_result(
            gate_id,
            payload.get("ok") is True,
            (time.perf_counter() - started) * 1_000,
            {
                "schema": payload.get("schema"),
                "version": payload.get("version"),
                "tag": payload.get("tag"),
                "changelog_state": payload.get("changelog_state"),
            },
            "; ".join(str(item) for item in payload.get("errors", [])),
        )

    return evaluate


def clean_worktree(context: MaturityContext) -> MaturityGateResult:
    result = run_command(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        root=context.root,
        timeout=30,
    )
    dirty_count = len(
        [line for line in result.stdout.splitlines() if line.strip()]
    )
    return gate_result(
        "clean_worktree",
        result.returncode == 0 and dirty_count == 0,
        result.duration_ms,
        {"dirty_path_count": dirty_count},
        result.stderr or "release worktree must be clean",
    )


def install_provenance(context: MaturityContext) -> MaturityGateResult:
    install_root = Path(
        os.environ.get("DESIGN_CRAFT_SKILL_ROOT", Path.home() / ".agents/skills")
    ).expanduser()
    result = run_command(
        [
            sys.executable,
            "scripts/design_craft_install_verify.py",
            "--source",
            "skills/design-craft",
            "--installed",
            str(install_root / "design-craft"),
            "--expected-name",
            "design-craft",
            "--expected-version",
            (context.root / "VERSION").read_text(encoding="utf-8").strip(),
            "--require-metadata",
            "--json",
        ],
        root=context.root,
    )
    payload = json_payload(result)
    return gate_result(
        "install_provenance",
        result.returncode == 0 and payload.get("ok") is True,
        result.duration_ms,
        {
            "installed": str(install_root / "design-craft"),
            "schema": payload.get("schema"),
        },
        result.stderr
        or "; ".join(str(item) for item in payload.get("errors", [])),
    )


def upstream_remote_review(context: MaturityContext) -> MaturityGateResult:
    return command_gate(
        "upstream_remote_review",
        [
            sys.executable,
            "scripts/upstream_absorption_report.py",
            "--remote-details",
            "--fail-on-unreviewed",
        ],
        timeout=240,
        evidence={"mode": "live_remote_read"},
    )(context)


def main_branch(context: MaturityContext) -> MaturityGateResult:
    result = run_command(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        root=context.root,
        timeout=30,
    )
    branch = result.stdout.strip()
    return gate_result(
        "main_branch",
        result.returncode == 0 and branch == "main",
        result.duration_ms,
        {"branch": branch or None},
        result.stderr or "final release verification must run from main",
    )
