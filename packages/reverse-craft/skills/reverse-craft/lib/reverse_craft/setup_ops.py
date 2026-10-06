from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

from . import __version__
from .common import (
    ReverseCraftError,
    atomic_write_json,
    bounded_text,
    canonical_json,
    ensure_private_directory,
    home_root,
    load_json,
    parse_utc,
    redact_sensitive_text,
    sha256_bytes,
    utc_now,
)

PROFILE_TOOLS = {
    "core": ["git", "file", "jq", "openssl"],
    "binary": ["binutils", "gdb", "radare2"],
    "android": ["adb", "jadx", "apktool"],
    "ios": [],
    "web": ["node"],
    "forensics": ["yara", "tshark", "exiftool"],
    "firmware": ["binwalk", "unsquashfs", "qemu-system"],
    "wireless": ["aircrack-ng", "tshark", "rtl-sdr"],
}

BINARIES = {
    "git": ["git"], "file": ["file"], "jq": ["jq"], "openssl": ["openssl"],
    "binutils": ["objdump", "gobjdump"], "gdb": ["gdb"], "radare2": ["radare2", "r2"],
    "adb": ["adb"], "jadx": ["jadx"], "apktool": ["apktool"], "node": ["node"],
    "yara": ["yara"], "tshark": ["tshark"], "exiftool": ["exiftool"], "binwalk": ["binwalk"],
    "unsquashfs": ["unsquashfs"], "qemu-system": ["qemu-system-x86_64", "qemu-system-aarch64"],
    "aircrack-ng": ["aircrack-ng"], "rtl-sdr": ["rtl_sdr"],
}

PACKAGES = {
    "brew": {
        "git": "git", "file": "file-formula", "jq": "jq", "openssl": "openssl@3",
        "binutils": "binutils", "gdb": "gdb", "radare2": "radare2",
        "adb": "android-platform-tools", "jadx": "jadx", "apktool": "apktool", "node": "node",
        "yara": "yara", "tshark": "wireshark", "exiftool": "exiftool", "binwalk": "binwalk",
        "unsquashfs": "squashfs", "qemu-system": "qemu", "aircrack-ng": "aircrack-ng", "rtl-sdr": "rtl-sdr",
    },
    "apt-get": {
        "git": "git", "file": "file", "jq": "jq", "openssl": "openssl",
        "binutils": "binutils", "gdb": "gdb", "radare2": "radare2",
        "adb": "adb", "apktool": "apktool", "node": "nodejs", "yara": "yara", "tshark": "tshark",
        "exiftool": "libimage-exiftool-perl", "binwalk": "binwalk", "unsquashfs": "squashfs-tools",
        "qemu-system": "qemu-system", "aircrack-ng": "aircrack-ng", "rtl-sdr": "rtl-sdr",
    },
    "winget": {
        "git": "Git.Git", "jq": "jqlang.jq", "gdb": "MSYS2.MSYS2", "radare2": "RadareOrg.Radare2",
        "adb": "Google.PlatformTools", "jadx": "skylot.jadx", "node": "OpenJS.NodeJS.LTS",
        "yara": "VirusTotal.YARA", "exiftool": "OliverBetz.ExifTool",
    },
}


def _has_root_privileges() -> bool:
    geteuid = getattr(os, "geteuid", None)
    return callable(geteuid) and geteuid() == 0


def _manager() -> str | None:
    if shutil.which("brew"):
        return "brew"
    if shutil.which("apt-get") and _has_root_privileges():
        return "apt-get"
    if shutil.which("winget"):
        return "winget"
    return None


def _argv(manager: str, package: str) -> list[str]:
    if manager == "brew":
        return [shutil.which("brew") or "brew", "install", package]
    if manager == "apt-get":
        return [shutil.which("apt-get") or "apt-get", "install", "-y", package]
    if manager == "winget":
        return [shutil.which("winget") or "winget", "install", "--id", package, "--exact", "--accept-package-agreements", "--accept-source-agreements"]
    raise ReverseCraftError(f"unsupported package manager: {manager}")


def _tool_set(profile: str) -> list[str]:
    if profile == "all":
        return list(dict.fromkeys(tool for name in PROFILE_TOOLS for tool in PROFILE_TOOLS[name]))
    if profile not in PROFILE_TOOLS:
        raise ReverseCraftError(f"unknown setup profile: {profile}")
    return PROFILE_TOOLS[profile]


def _present(tool: str) -> bool:
    return any(shutil.which(binary) for binary in BINARIES[tool])


def _plan_digest(plan: dict[str, Any]) -> str:
    material = {key: value for key, value in plan.items() if key != "plan_sha256"}
    return sha256_bytes(canonical_json(material))


def _redact_output(value: str) -> str:
    return redact_sensitive_text(value)


def create_plan(profile: str, output: str, home: str | None = None) -> dict[str, Any]:
    manager = _manager()
    tools = _tool_set(profile)
    actions: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    for tool in tools:
        if _present(tool):
            continue
        package = PACKAGES.get(manager or "", {}).get(tool)
        if manager and package:
            actions.append({
                "id": f"install-{tool}",
                "tool": tool,
                "manager": manager,
                "package": package,
                "argv": _argv(manager, package),
                "expected_binaries": BINARIES[tool],
                "reason": f"missing tool for {profile} profile",
            })
        else:
            unavailable.append({"tool": tool, "reason": "no safe package mapping for current platform/privilege"})
    created = parse_utc(utc_now())
    plan: dict[str, Any] = {
        "schema": "reverse-craft.setup-plan.v1",
        "id": str(uuid.uuid4()),
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "expires_at": (created + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
        "generated_by": __version__,
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "profile": profile,
        "manager": manager,
        "actions": actions,
        "unavailable": unavailable,
        "home": str(home_root(home)),
    }
    plan["plan_sha256"] = _plan_digest(plan)
    destination = Path(output).expanduser().resolve()
    atomic_write_json(destination, plan)
    return {"schema": "reverse-craft.setup-plan-receipt.v1", "path": str(destination), "sha256": plan["plan_sha256"], "actions": len(actions), "unavailable": unavailable}


def _validate_action(action: dict[str, Any], manager: str) -> None:
    tool = action.get("tool")
    package = action.get("package")
    if tool not in BINARIES or PACKAGES.get(manager, {}).get(tool) != package:
        raise ReverseCraftError(f"setup action is not in the built-in catalog: {tool}/{package}")
    expected = _argv(manager, package)
    if action.get("argv") != expected:
        raise ReverseCraftError(f"setup argv does not match the safe template: {tool}")
    if action.get("expected_binaries") != BINARIES[tool]:
        raise ReverseCraftError(f"setup expected binaries were modified: {tool}")


def apply_plan(plan_path: str, expected_sha256: str, yes: bool, home: str | None = None) -> dict[str, Any]:
    if not yes:
        raise ReverseCraftError("setup apply requires --yes")
    source = Path(plan_path).expanduser().resolve()
    plan = load_json(source)
    if plan.get("schema") != "reverse-craft.setup-plan.v1":
        raise ReverseCraftError("unsupported setup plan schema")
    expected_keys = {
        "schema", "id", "created_at", "expires_at", "generated_by", "platform", "profile",
        "manager", "actions", "unavailable", "home", "plan_sha256",
    }
    if set(plan) != expected_keys:
        raise ReverseCraftError("setup plan has missing or unexpected top-level fields")
    try:
        if str(uuid.UUID(plan["id"])) != plan["id"]:
            raise ValueError
    except (ValueError, TypeError, AttributeError) as exc:
        raise ReverseCraftError("setup plan id is not a canonical UUID") from exc
    if plan.get("profile") not in {*PROFILE_TOOLS, "all"}:
        raise ReverseCraftError("setup plan has an invalid profile")
    if not isinstance(plan.get("actions"), list) or not isinstance(plan.get("unavailable"), list):
        raise ReverseCraftError("setup plan actions/unavailable must be arrays")
    actual = _plan_digest(plan)
    if plan.get("plan_sha256") != actual or expected_sha256 != actual:
        raise ReverseCraftError("setup plan SHA-256 mismatch")
    if parse_utc(plan["expires_at"]) < parse_utc(utc_now()):
        raise ReverseCraftError("setup plan has expired")
    current_platform = {"system": platform.system(), "machine": platform.machine()}
    if plan.get("platform") != current_platform:
        raise ReverseCraftError("setup plan platform does not match this host")
    configured_home = home_root(home)
    if Path(plan.get("home", "")).resolve() != configured_home:
        raise ReverseCraftError("setup plan home does not match the requested home")
    manager = plan.get("manager")
    if manager not in PACKAGES:
        if plan.get("actions"):
            raise ReverseCraftError("setup plan has actions but no supported manager")
    action_ids: set[str] = set()
    for action in plan.get("actions", []):
        if not isinstance(action, dict) or action.get("id") != f"install-{action.get('tool')}" or action.get("id") in action_ids:
            raise ReverseCraftError("setup plan has an invalid or duplicate action id")
        action_ids.add(action["id"])
        if action.get("manager") != manager:
            raise ReverseCraftError(f"setup action manager mismatch: {action.get('id')}")
        _validate_action(action, manager)
    setup_dir = configured_home / "setup"
    transaction_dir = setup_dir / "transactions"
    ensure_private_directory(setup_dir)
    ensure_private_directory(transaction_dir)
    journal_path = transaction_dir / f"{plan['id']}.json"
    journal: dict[str, Any] = {
        "schema": "reverse-craft.setup-transaction.v1",
        "id": plan["id"],
        "plan_path": str(source),
        "plan_sha256": actual,
        "started_at": utc_now(),
        "finished_at": None,
        "status": "running",
        "receipts": [],
    }
    try:
        fd = os.open(journal_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        previous = load_json(journal_path)
        if previous.get("status") == "complete":
            raise ReverseCraftError("setup plan was already applied") from exc
        raise ReverseCraftError("setup transaction already exists; inspect its journal before creating a new plan") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(journal, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    for action in plan.get("actions", []):
        started = utc_now()
        try:
            completed = subprocess.run(action["argv"], text=True, capture_output=True, timeout=1200, check=False)
            receipt = {
                "action_id": action["id"], "tool": action["tool"], "argv": action["argv"],
                "started_at": started, "finished_at": utc_now(), "exit_code": completed.returncode,
                "stdout": _redact_output(completed.stdout), "stderr": _redact_output(completed.stderr),
                "expected_available": any(shutil.which(binary) for binary in action["expected_binaries"]),
            }
        except subprocess.TimeoutExpired as exc:
            receipt = {
                "action_id": action["id"], "tool": action["tool"], "argv": action["argv"],
                "started_at": started, "finished_at": utc_now(), "exit_code": None,
                "stdout": bounded_text((exc.stdout or "") if isinstance(exc.stdout, str) else ""),
                "stderr": "command timed out", "expected_available": False,
            }
        journal["receipts"].append(receipt)
        if receipt["exit_code"] != 0 or receipt["expected_available"] is not True:
            journal["status"] = "failed"
            journal["finished_at"] = utc_now()
            atomic_write_json(journal_path, journal)
            reason = "command failed" if receipt["exit_code"] != 0 else "expected binary not found after install"
            raise ReverseCraftError(f"setup action failed: {action['id']}: {reason} (see {journal_path})")
        atomic_write_json(journal_path, journal)
    journal["status"] = "complete"
    journal["finished_at"] = utc_now()
    atomic_write_json(journal_path, journal)
    return {"schema": "reverse-craft.setup-apply.v1", "status": "complete", "journal": str(journal_path), "receipts": journal["receipts"]}


def setup_status(home: str | None = None) -> dict[str, Any]:
    root = home_root(home) / "setup" / "transactions"
    transactions: list[dict[str, Any]] = []
    if root.is_dir():
        for path in sorted(root.glob("*.json")):
            transaction = load_json(path)
            transactions.append({
                "id": transaction.get("id"), "status": transaction.get("status"),
                "started_at": transaction.get("started_at"), "finished_at": transaction.get("finished_at"),
                "path": str(path),
            })
    return {"schema": "reverse-craft.setup-status.v1", "transactions": transactions}
