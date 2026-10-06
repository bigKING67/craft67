#!/usr/bin/env python3
"""Validate host adapters and optionally prove model-free Skill discovery."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from install_skill import tree_sha256

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_OUTPUT_LIMIT = 2_000_000
Runner = Callable[..., tuple[int, str]]


def run(
    command: list[str],
    *,
    input_text: str | None = None,
    max_output_chars: int = 1000,
) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
        timeout=60,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode, output[:max_output_chars]


def parse_codex_discovery(output: str) -> bool:
    payload = json.loads(output)
    if not isinstance(payload, list):
        raise ValueError("Codex prompt input must be a JSON array")
    lines: list[str] = []
    for message in payload:
        if not isinstance(message, dict):
            continue
        for block in message.get("content", []):
            if not isinstance(block, dict) or block.get("type") != "input_text":
                continue
            lines.extend(str(block.get("text", "")).splitlines())
    agents_roots: set[str] = set()
    for line in lines:
        match = re.fullmatch(r"- `(r\d+)` = `([^`]+)`", line)
        if match and match.group(2).replace("\\", "/").endswith("/.agents/skills"):
            agents_roots.add(match.group(1))
    for line in lines:
        if not line.startswith("- money-craft:"):
            continue
        if any(f"(file: {root}/money-craft/SKILL.md)" in line for root in agents_roots):
            return True
    return False


def parse_pi_discovery(output: str) -> bool:
    for line in output.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("type") != "response" or payload.get("command") != "get_commands":
            continue
        if payload.get("success") is not True:
            continue
        commands = payload.get("data", {}).get("commands", [])
        for command in commands:
            if not isinstance(command, dict) or command.get("name") != "skill:money-craft":
                continue
            source_path = command.get("sourceInfo", {}).get("path", "")
            normalized = str(source_path).replace("\\", "/")
            if normalized.endswith("/.agents/skills/money-craft/SKILL.md"):
                return True
    return False


def parse_grok_discovery(output: str) -> bool:
    payload = json.loads(output)
    if not isinstance(payload, dict):
        raise ValueError("Grok inspect output must be a JSON object")
    for skill in payload.get("skills", []):
        if not isinstance(skill, dict) or skill.get("name") != "money-craft":
            continue
        source_path = skill.get("source", {}).get("path", "")
        normalized = str(source_path).replace("\\", "/")
        if normalized.endswith("/.agents/skills/money-craft/SKILL.md"):
            return True
    return False


def record_discovery(
    *,
    host: str,
    command: list[str],
    parser: Callable[[str], bool],
    check_name: str,
    method: str,
    checks: list[str],
    errors: list[str],
    discovery: dict[str, dict[str, Any]],
    runner: Runner,
    input_text: str | None = None,
) -> None:
    if shutil.which(command[0]) is None:
        errors.append(f"{command[0]} is unavailable")
        discovery[host] = {"status": "failed", "method": method, "reason": "cli unavailable"}
        return
    try:
        code, output = runner(
            command,
            input_text=input_text,
            max_output_chars=DISCOVERY_OUTPUT_LIMIT,
        )
    except subprocess.TimeoutExpired:
        errors.append(f"{host} discovery timed out")
        discovery[host] = {"status": "failed", "method": method, "reason": "timeout"}
        return
    if code:
        errors.append(f"{host} discovery command failed")
        discovery[host] = {
            "status": "failed",
            "method": method,
            "reason": "command failed",
        }
        return
    try:
        discovered = parser(output)
    except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
        discovered = False
    if not discovered:
        errors.append(f"{host} did not discover money-craft")
        discovery[host] = {
            "status": "failed",
            "method": method,
            "reason": "skill absent from host discovery output",
        }
        return
    checks.append(check_name)
    discovery[host] = {"status": "passed", "method": method}


def inspect_compatibility_installation(
    *,
    installed: Path,
    label: str,
    check_prefix: str,
    runner: Runner,
) -> dict[str, Any]:
    provenance_path = installed / "INSTALL_PROVENANCE.json"
    if (
        installed.is_symlink()
        or not (installed / "SKILL.md").is_file()
        or not provenance_path.is_file()
    ):
        return {
            "valid": False,
            "error": f"{label} installation is missing or invalid",
            "reason": "installation missing or invalid",
            "checks": [],
        }
    try:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "valid": False,
            "error": f"{label} installation provenance is invalid",
            "reason": "invalid provenance",
            "checks": [],
        }
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if (
        provenance.get("schema") != "money-craft.install-provenance.v1"
        or provenance.get("version") != version
    ):
        return {
            "valid": False,
            "error": f"{label} installation provenance identity is invalid",
            "reason": "provenance identity mismatch",
            "checks": [],
        }
    source_hash = tree_sha256(ROOT / "skills" / "money-craft")
    installed_hash = tree_sha256(installed, excluded_names={"INSTALL_PROVENANCE.json"})
    if provenance.get("source_skill_sha256") != source_hash or installed_hash != source_hash:
        return {
            "valid": False,
            "error": f"{label} installation does not match the canonical Skill",
            "reason": "source hash mismatch",
            "checks": [],
        }
    command = [sys.executable, str(installed / "scripts" / "money_craft.py"), "self-test", "--json"]
    try:
        code, output = runner(command, max_output_chars=100_000)
        payload = json.loads(output) if code == 0 else {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        code, payload = 1, {}
    if code or payload.get("runtime_valid") is not True:
        return {
            "valid": False,
            "error": f"{label} installed runtime self-test failed",
            "reason": "runtime self-test failed",
            "checks": [f"{check_prefix}-install-parity"],
        }
    return {
        "valid": True,
        "error": None,
        "reason": None,
        "checks": [
            f"{check_prefix}-install-parity",
            f"{check_prefix}-installed-runtime-self-test",
        ],
    }


def validate_shared_agents_compatibility(
    *,
    home: Path,
    checks: list[str],
    errors: list[str],
    discovery: dict[str, dict[str, Any]],
    runner: Runner,
) -> None:
    result = inspect_compatibility_installation(
        installed=home / ".agents" / "skills" / "money-craft",
        label="Shared Agent Skills",
        check_prefix="shared-agents",
        runner=runner,
    )
    checks.extend(result["checks"])
    if result["valid"] is not True:
        errors.append(result["error"])
        discovery["shared_agents"] = {
            "status": "failed",
            "method": "shared install parity and runtime self-test",
            "reason": result["reason"],
        }
        return
    discovery["shared_agents"] = {
        "status": "passed",
        "method": "shared install parity and runtime self-test",
    }


def validate_claude_compatibility(
    *,
    home: Path,
    checks: list[str],
    errors: list[str],
    warnings: list[str],
    discovery: dict[str, dict[str, Any]],
    runner: Runner,
) -> None:
    installed = home / ".claude" / "skills" / "money-craft"
    result = inspect_compatibility_installation(
        installed=installed,
        label="Claude compatibility",
        check_prefix="claude-compat",
        runner=runner,
    )
    checks.extend(result["checks"])
    if result["valid"] is not True:
        errors.append(result["error"])
        discovery["claude"] = {
            "status": "failed",
            "method": "compatibility install and runtime self-test",
            "reason": result["reason"],
            "fresh_session_tested": False,
        }
        return
    warnings.append("Claude compatibility is validated without a paid fresh model invocation")
    discovery["claude"] = {
        "status": "partial",
        "method": "compatibility install and runtime self-test",
        "fresh_session_tested": False,
        "reason": "Claude Code 2.1.x does not expose a model-free personal Skill discovery command",
    }


def run_host_discovery(
    *,
    home: Path,
    checks: list[str],
    errors: list[str],
    warnings: list[str],
    runner: Runner,
) -> dict[str, dict[str, Any]]:
    discovery: dict[str, dict[str, Any]] = {}
    validate_shared_agents_compatibility(
        home=home,
        checks=checks,
        errors=errors,
        discovery=discovery,
        runner=runner,
    )
    record_discovery(
        host="codex",
        command=["codex", "debug", "prompt-input", "Use $money-craft for global investment research."],
        parser=parse_codex_discovery,
        check_name="codex-live-skill-discovery",
        method="model-visible prompt catalog",
        checks=checks,
        errors=errors,
        discovery=discovery,
        runner=runner,
    )
    record_discovery(
        host="pi",
        command=[
            "pi",
            "--mode",
            "rpc",
            "--no-session",
            "--offline",
            "--no-extensions",
            "--no-prompt-templates",
            "--no-context-files",
        ],
        parser=parse_pi_discovery,
        check_name="pi-live-skill-discovery",
        method="fresh offline RPC get_commands",
        checks=checks,
        errors=errors,
        discovery=discovery,
        runner=runner,
        input_text='{"type":"get_commands","id":"money-craft-discovery"}\n',
    )
    record_discovery(
        host="grok",
        command=["grok", "inspect", "--json"],
        parser=parse_grok_discovery,
        check_name="grok-live-skill-discovery",
        method="live inspect",
        checks=checks,
        errors=errors,
        discovery=discovery,
        runner=runner,
    )
    validate_claude_compatibility(
        home=home,
        checks=checks,
        errors=errors,
        warnings=warnings,
        discovery=discovery,
        runner=runner,
    )
    return discovery


def validate(
    run_local_validators: bool,
    run_discovery: bool = False,
    *,
    home: Path | None = None,
    runner: Runner = run,
) -> dict[str, Any]:
    checks: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    expected = {
        "codex": ROOT / ".codex-plugin" / "plugin.json",
        "claude": ROOT / ".claude-plugin" / "plugin.json",
        "grok": ROOT / ".grok-plugin" / "plugin.json",
    }
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    for host, path in expected.items():
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{host} manifest invalid: {exc}")
            continue
        if manifest.get("name") != "money-craft" or manifest.get("version") != version:
            errors.append(f"{host} manifest identity mismatch")
        else:
            checks.append(f"{host}-manifest")
    if package.get("pi", {}).get("skills") == ["skills/money-craft"]:
        checks.append("pi-package-discovery")
    else:
        errors.append("Pi package discovery path is invalid")

    if run_local_validators:
        commands = {
            "claude-plugin-validate": ["claude", "plugin", "validate", str(ROOT)],
            "grok-plugin-validate": ["grok", "plugin", "validate", str(ROOT)],
            "codex-cli-present": ["codex", "--version"],
            "pi-cli-present": ["pi", "--version"],
        }
        for name, command in commands.items():
            if shutil.which(command[0]) is None:
                errors.append(f"{command[0]} is unavailable")
                continue
            try:
                code, output = runner(command)
            except subprocess.TimeoutExpired:
                errors.append(f"{name} timed out")
                continue
            if code:
                errors.append(f"{name} failed: {output}")
            else:
                checks.append(name)
    else:
        warnings.append("host CLI validators were not requested")
    discovery: dict[str, dict[str, Any]] = {}
    if run_discovery:
        discovery = run_host_discovery(
            home=home or Path.home(),
            checks=checks,
            errors=errors,
            warnings=warnings,
            runner=runner,
        )
    else:
        warnings.append("model-free live host discovery was not requested")
    return {
        "schema": "money-craft.host-smoke.v1",
        "valid": not errors,
        "discovery_tested": run_discovery,
        "fresh_session_tested": False,
        "provider_live_tested": False,
        "discovery": discovery,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-local-validators", action="store_true")
    parser.add_argument(
        "--run-discovery",
        action="store_true",
        help="prove Codex/Pi/Grok discovery and Claude compatibility without model inference",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = validate(args.run_local_validators, args.run_discovery)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
