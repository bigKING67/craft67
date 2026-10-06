#!/usr/bin/env python3
"""Probe native SDK availability and validate observed native runtime evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from design_craft_evidence_common import (
    files_sha256,
    git_is_ancestor,
    git_root,
    git_tree_sha256,
    read_version,
    tree_sha256,
)


PROBE_SCHEMA = "design-craft.native-runtime-probe.v1"
EVIDENCE_SCHEMA_V2 = "design-craft.native-runtime-evidence.v2"
EVIDENCE_SCHEMA = "design-craft.native-runtime-evidence.v3"
VALIDATION_SCHEMA = "design-craft.native-runtime-validation.v1"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.design_craft.release.native_ios_observation import validate_success_log

DEFAULT_SKILL_ROOT = ROOT / "skills/design-craft"
DEFAULT_FIXTURE_ROOT = ROOT / "evals/native-runtime/fixtures"
PLATFORM_FILES = {
    "ios": "ios-observed.json",
    "android": "android-observed.json",
}
PLATFORM_RUNTIME_KIND = {
    "ios": "ios_simulator",
    "android": "android_emulator",
}
RUNTIME_KINDS = {
    "ios": {"ios_simulator", "ios_device"},
    "android": {"android_emulator", "android_device"},
}
REQUIRED_ASSERTIONS = {
    "ios_simulator": {
        "build_succeeded",
        "install_and_launch_succeeded",
        "runtime_interaction_observed",
        "before_and_after_screenshots_captured",
    },
    "ios_device": {
        "build_succeeded",
        "install_and_launch_succeeded",
        "runtime_interaction_observed",
        "before_and_after_screenshots_captured",
        "physical_device_confirmed",
        "device_authorization_confirmed",
    },
    "android_emulator": {
        "build_succeeded",
        "install_and_launch_succeeded",
        "accessibility_tree_observed",
        "interaction_observed",
        "screenshot_captured",
    },
    "android_device": {
        "build_succeeded",
        "install_and_launch_succeeded",
        "accessibility_tree_observed",
        "interaction_observed",
        "screenshot_captured",
        "physical_device_confirmed",
        "device_authorization_confirmed",
    },
}
REQUIRED_ARTIFACT_ROLES = {
    "ios_simulator": {
        "before_screenshot",
        "after_screenshot",
        "interaction_marker",
        "launch_log",
    },
    "ios_device": {
        "before_screenshot",
        "after_screenshot",
        "interaction_marker",
        "launch_log",
    },
    "android_emulator": {
        "before_accessibility_tree",
        "after_accessibility_tree",
        "after_screenshot",
        "launch_log",
    },
    "android_device": {
        "before_accessibility_tree",
        "after_accessibility_tree",
        "after_screenshot",
        "launch_log",
    },
}
ARTIFACT_ROLE_SUFFIXES = {
    "before_screenshot": {".png"},
    "after_screenshot": {".png"},
    "after_accessibility_tree": {".xml"},
    "before_accessibility_tree": {".xml"},
    "interaction_marker": {".txt"},
    "launch_log": {".txt", ".log"},
}
NATIVE_CONTRACT_FILES = {
    "ios": (
        "scripts/design_craft_evidence_common.py",
        "scripts/design_craft_native_runtime_record.py",
        "scripts/design_craft_native_runtime_validate.py",
        "scripts/native_runtime_ci_ios.sh",
        "tools/design_craft/release/native_ios_observation.py",
        ".github/workflows/native-runtime.yml",
    ),
    "android": (
        "scripts/design_craft_evidence_common.py",
        "scripts/design_craft_native_runtime_record.py",
        "scripts/design_craft_native_runtime_validate.py",
        "scripts/native_runtime_android_common.sh",
        "scripts/native_runtime_ci_android.sh",
        "scripts/native_runtime_device_android.sh",
        ".github/workflows/native-runtime.yml",
    ),
}


def native_contract_sha256(platform_name: str) -> str:
    return files_sha256(ROOT, NATIVE_CONTRACT_FILES[platform_name])
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def run(command: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(command, 1, "", str(exc))


def command_path(name: str) -> str | None:
    return shutil.which(name)


def probe_environment() -> dict:
    xcode_select = run(["xcode-select", "-p"]) if command_path("xcode-select") else None
    simctl = run(["xcrun", "--find", "simctl"]) if command_path("xcrun") else None
    ios_devices: list[str] = []
    if simctl and simctl.returncode == 0:
        listed = run(["xcrun", "simctl", "list", "devices", "available", "-j"], timeout=30)
        if listed.returncode == 0:
            try:
                payload = json.loads(listed.stdout)
                for devices in payload.get("devices", {}).values():
                    for device in devices:
                        if device.get("isAvailable"):
                            ios_devices.append(str(device.get("name", "Simulator")))
            except json.JSONDecodeError:
                pass

    adb_path = command_path("adb")
    adb_devices: list[str] = []
    if adb_path:
        listed = run([adb_path, "devices", "-l"])
        if listed.returncode == 0:
            connected = [
                line.split("\t", 1)[0]
                for line in listed.stdout.splitlines()[1:]
                if line.strip() and "\tdevice" in line
            ]
            adb_devices = [
                "emulator" if serial.startswith("emulator-") else "physical-device"
                for serial in connected
            ]

    emulator_path = command_path("emulator")
    android_avds: list[str] = []
    if emulator_path:
        listed = run([emulator_path, "-list-avds"])
        if listed.returncode == 0:
            android_avds = [line.strip() for line in listed.stdout.splitlines() if line.strip()]

    return {
        "schema": PROBE_SCHEMA,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "ios": {
            "xcode_select_path": xcode_select.stdout.strip() if xcode_select and xcode_select.returncode == 0 else None,
            "xcodebuild_path": command_path("xcodebuild"),
            "simctl_path": simctl.stdout.strip() if simctl and simctl.returncode == 0 else None,
            "available_simulators": ios_devices,
            "ready": bool(simctl and simctl.returncode == 0 and ios_devices),
            "detail": "simctl unavailable" if not simctl or simctl.returncode != 0 else "no available Simulator runtime" if not ios_devices else "ready",
        },
        "android": {
            "adb_path": adb_path,
            "emulator_path": emulator_path,
            "available_avds": android_avds,
            "connected_devices": adb_devices,
            "connected_device_count": len(adb_devices),
            "device_ready": "physical-device" in adb_devices,
            "ready": bool(adb_path and emulator_path and android_avds),
            "detail": "adb unavailable" if not adb_path else "emulator unavailable" if not emulator_path else "no AVD configured" if not android_avds else "ready",
        },
    }


def validate_artifact_content(role: str, artifact_path: Path) -> str | None:
    expected_suffixes = ARTIFACT_ROLE_SUFFIXES.get(role)
    if expected_suffixes and artifact_path.suffix.lower() not in expected_suffixes:
        return f"role {role} requires one of {sorted(expected_suffixes)}"
    if role in {"before_screenshot", "after_screenshot"}:
        if not artifact_path.read_bytes().startswith(PNG_SIGNATURE):
            return f"role {role} must contain PNG data"
    elif role in {"before_accessibility_tree", "after_accessibility_tree"}:
        try:
            ET.parse(artifact_path)
        except (ET.ParseError, OSError) as exc:
            return f"role {role} must contain valid XML: {exc}"
        text = artifact_path.read_text(encoding="utf-8", errors="replace")
        expected_text = (
            "Native runtime evidence title"
            if role == "before_accessibility_tree"
            else "Runtime interaction confirmed"
        )
        if expected_text not in text:
            return f"role {role} must contain {expected_text!r}"
    elif role == "interaction_marker":
        if "Runtime interaction confirmed" not in artifact_path.read_text(
            encoding="utf-8", errors="replace"
        ):
            return "role interaction_marker must confirm the runtime interaction"
    return None


def validate_evidence(
    path: Path,
    expected_platform: str,
    expected_runtime_kind: str | None = None,
    *,
    require_current_source: bool = False,
    skill_root: Path = DEFAULT_SKILL_ROOT,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
) -> tuple[dict, list[str]]:
    if not path.is_file():
        return {}, [f"missing observed evidence: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"invalid evidence JSON {path}: {exc}"]

    errors: list[str] = []
    evidence_schema = payload.get("schema")
    if evidence_schema not in {EVIDENCE_SCHEMA_V2, EVIDENCE_SCHEMA}:
        errors.append(f"{path}: schema must be {EVIDENCE_SCHEMA_V2} or {EVIDENCE_SCHEMA}")
    if payload.get("platform") != expected_platform:
        errors.append(f"{path}: platform must be {expected_platform}")
    if payload.get("verified") is not True:
        errors.append(f"{path}: verified must be true")
    runtime_kind = payload.get("runtime_kind")
    if runtime_kind not in RUNTIME_KINDS[expected_platform]:
        errors.append(f"{path}: invalid runtime_kind for {expected_platform}")
    if expected_runtime_kind and runtime_kind != expected_runtime_kind:
        errors.append(f"{path}: runtime_kind must be {expected_runtime_kind}")
    if payload.get("evidence_level") != "runtime_observed":
        errors.append(f"{path}: evidence_level must be runtime_observed")
    observed_at = payload.get("observed_at")
    if not isinstance(observed_at, str) or not observed_at.endswith("Z"):
        errors.append(f"{path}: observed_at must be a UTC timestamp ending in Z")
    runtime_id = payload.get("runtime_id")
    if payload.get("runtime_id_kind") != "sha256":
        errors.append(f"{path}: runtime_id_kind must be sha256")
    if not isinstance(runtime_id, str) or not re.fullmatch(
        r"sha256:[0-9a-f]{64}", runtime_id
    ):
        errors.append(f"{path}: runtime_id must be a redacted SHA-256 identifier")
    if not isinstance(payload.get("tool"), str) or not payload["tool"].strip():
        errors.append(f"{path}: tool is required")
    if not re.fullmatch(r"[0-9a-f]{40}", str(payload.get("source_commit", ""))):
        errors.append(f"{path}: source_commit must be a full lowercase Git SHA")
    source_dirty = payload.get("source_dirty")
    skill_source_dirty = payload.get("skill_source_dirty")
    if not isinstance(source_dirty, bool):
        errors.append(f"{path}: source_dirty must be boolean")
    if not isinstance(skill_source_dirty, bool):
        errors.append(f"{path}: skill_source_dirty must be boolean")
    if isinstance(source_dirty, bool) and isinstance(skill_source_dirty, bool):
        if source_dirty is not skill_source_dirty:
            errors.append(f"{path}: source_dirty must alias skill_source_dirty")
    if not isinstance(payload.get("repo_dirty"), bool):
        errors.append(f"{path}: repo_dirty must be boolean")
    if not isinstance(payload.get("skill_version"), str) or not payload["skill_version"].strip():
        errors.append(f"{path}: skill_version is required")
    digest_keys = ["skill_tree_sha256", "fixture_tree_sha256"]
    if evidence_schema == EVIDENCE_SCHEMA:
        digest_keys.append("contract_sha256")
    for key in digest_keys:
        if not re.fullmatch(r"[0-9a-f]{64}", str(payload.get(key, ""))):
            errors.append(f"{path}: {key} must be 64 lowercase hex characters")
    if not isinstance(payload.get("capture_context"), str) or not payload["capture_context"].strip():
        errors.append(f"{path}: capture_context is required")
    workflow = payload.get("workflow")
    if evidence_schema == EVIDENCE_SCHEMA:
        if workflow is not None and not isinstance(workflow, dict):
            errors.append(f"{path}: workflow must be an object or null")
        elif isinstance(workflow, dict):
            expected_workflow_keys = {
                "repository",
                "run_id",
                "run_attempt",
                "url",
                "event",
                "head_sha",
                "ref",
            }
            if set(workflow) != expected_workflow_keys:
                errors.append(f"{path}: workflow keys are incomplete or unsupported")
            for key in ("repository", "url", "event", "ref"):
                if not isinstance(workflow.get(key), str) or not workflow[key].strip():
                    errors.append(f"{path}: workflow.{key} must be a non-empty string")
            for key in ("run_id", "run_attempt"):
                if not isinstance(workflow.get(key), int) or isinstance(workflow.get(key), bool) or workflow[key] <= 0:
                    errors.append(f"{path}: workflow.{key} must be a positive integer")
            if not re.fullmatch(r"[0-9a-f]{40}", str(workflow.get("head_sha", ""))):
                errors.append(f"{path}: workflow.head_sha must be a full lowercase Git SHA")
    commands = payload.get("commands")
    if not isinstance(commands, list) or not commands or not all(isinstance(item, str) and item.strip() for item in commands):
        errors.append(f"{path}: commands must be a non-empty string array")
    assertions = payload.get("assertions")
    required_assertions = REQUIRED_ASSERTIONS.get(str(runtime_kind), set())
    if not isinstance(assertions, dict):
        errors.append(f"{path}: assertions must be an object")
    else:
        missing_assertions = sorted(required_assertions - set(assertions))
        if missing_assertions:
            errors.append(
                f"{path}: assertions are missing required checks: {missing_assertions}"
            )
        if not all(value is True for value in assertions.values()):
            errors.append(f"{path}: every recorded runtime assertion must pass")
    artifacts = payload.get("artifacts")
    artifact_paths: dict[str, Path] = {}
    if not isinstance(artifacts, list) or not artifacts:
        errors.append(f"{path}: at least one runtime artifact is required")
    else:
        evidence_dir = path.parent.resolve()
        observed_roles: set[str] = set()
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"{path}: artifact {index} must be an object")
                continue
            role = artifact.get("role")
            if not isinstance(role, str) or role not in ARTIFACT_ROLE_SUFFIXES:
                errors.append(f"{path}: artifact {index} has an invalid role")
                continue
            if role in observed_roles:
                errors.append(f"{path}: artifact role {role} must be unique")
                continue
            observed_roles.add(role)
            raw_artifact_path = artifact.get("path")
            if not isinstance(raw_artifact_path, str) or not raw_artifact_path.strip():
                errors.append(f"{path}: artifact {index} path is required")
                continue
            sha = str(artifact.get("sha256", ""))
            if not re.fullmatch(r"[0-9a-f]{64}", sha):
                errors.append(f"{path}: artifact {index} sha256 must be 64 lowercase hex characters")
            expected_bytes = artifact.get("bytes")
            if not isinstance(expected_bytes, int) or isinstance(expected_bytes, bool) or expected_bytes <= 0:
                errors.append(f"{path}: artifact {index} bytes must be a positive integer")

            relative_path = Path(raw_artifact_path)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                errors.append(f"{path}: artifact {index} path must stay relative to the evidence directory")
                continue
            artifact_path = (evidence_dir / relative_path).resolve()
            if artifact_path != evidence_dir and evidence_dir not in artifact_path.parents:
                errors.append(f"{path}: artifact {index} path escapes the evidence directory")
                continue
            if not artifact_path.is_file():
                errors.append(f"{path}: artifact {index} file is missing: {artifact_path}")
                continue
            artifact_paths[role] = artifact_path
            observed_bytes = artifact_path.stat().st_size
            if isinstance(expected_bytes, int) and observed_bytes != expected_bytes:
                errors.append(
                    f"{path}: artifact {index} byte count does not match {artifact_path}"
                )
            observed_sha = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            if observed_sha != sha:
                errors.append(f"{path}: artifact {index} hash does not match {artifact_path}")
            content_error = validate_artifact_content(role, artifact_path)
            if content_error:
                errors.append(f"{path}: artifact {index} {content_error}")

        required_roles = REQUIRED_ARTIFACT_ROLES.get(str(runtime_kind), set())
        missing_roles = sorted(required_roles - observed_roles)
        if missing_roles:
            errors.append(f"{path}: artifacts are missing required roles: {missing_roles}")

    if require_current_source:
        if evidence_schema != EVIDENCE_SCHEMA:
            errors.append(f"{path}: certified native evidence must use {EVIDENCE_SCHEMA}")
        source_commit = str(payload.get("source_commit", ""))
        expected_skill_tree = tree_sha256(skill_root)
        expected_fixture_tree = tree_sha256(
            fixture_root / expected_platform,
            ignored_dirs={"build", ".gradle"},
        )
        if skill_source_dirty is not False:
            errors.append(
                f"{path}: certified native evidence must record skill_source_dirty=false"
            )
        if payload.get("skill_version") != read_version(skill_root):
            errors.append(f"{path}: skill_version must match the current skill version")
        if payload.get("skill_tree_sha256") != expected_skill_tree:
            errors.append(f"{path}: skill_tree_sha256 must match the current skill tree")
        if payload.get("fixture_tree_sha256") != expected_fixture_tree:
            errors.append(
                f"{path}: fixture_tree_sha256 must match the current {expected_platform} fixture tree"
            )
        if evidence_schema == EVIDENCE_SCHEMA and payload.get("contract_sha256") != native_contract_sha256(expected_platform):
            errors.append(
                f"{path}: contract_sha256 must match the current {expected_platform} runtime contract"
            )
        if expected_platform == "ios":
            marker_path = artifact_paths.get("interaction_marker")
            launch_path = artifact_paths.get("launch_log")
            if marker_path is not None and launch_path is not None:
                log_errors = validate_success_log(
                    launch_path.read_text(encoding="utf-8", errors="replace"),
                    marker_path.read_text(encoding="utf-8", errors="replace"),
                )
                errors.extend(f"{path}: {error}" for error in log_errors)
        if runtime_kind in {"ios_simulator", "android_emulator"}:
            if not isinstance(workflow, dict):
                errors.append(
                    f"{path}: current Simulator/Emulator evidence must include GitHub workflow identity"
                )
            elif workflow.get("head_sha") != source_commit:
                errors.append(f"{path}: workflow.head_sha must match source_commit")
        if re.fullmatch(r"[0-9a-f]{40}", source_commit):
            try:
                repository = git_root(skill_root)
            except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError):
                errors.append(f"{path}: current skill source is not in a Git repository")
            else:
                if not git_is_ancestor(repository, source_commit):
                    errors.append(f"{path}: source_commit must be an ancestor of current HEAD")
                else:
                    try:
                        committed_skill_tree = git_tree_sha256(
                            repository,
                            skill_root,
                            source_commit,
                        )
                    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
                        errors.append(
                            f"{path}: cannot inspect skill tree at source_commit: {exc}"
                        )
                    else:
                        if payload.get("skill_tree_sha256") != committed_skill_tree:
                            errors.append(
                                f"{path}: source_commit skill tree must match skill_tree_sha256"
                            )
    return payload, errors


def validate_root(
    root: Path,
    required: list[str],
    require_real_device: bool = False,
    *,
    require_current_source: bool = False,
    skill_root: Path = DEFAULT_SKILL_ROOT,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
) -> dict:
    evidence: dict[str, dict] = {}
    errors: list[str] = []
    for name in required:
        payload, platform_errors = validate_evidence(
            root / PLATFORM_FILES[name],
            name,
            PLATFORM_RUNTIME_KIND[name],
            require_current_source=require_current_source,
            skill_root=skill_root,
            fixture_root=fixture_root,
        )
        if payload:
            evidence[name] = payload
        errors.extend(platform_errors)
    if require_real_device:
        device_path = root / "real-device-observed.json"
        try:
            device_payload = json.loads(device_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"missing or invalid real-device evidence: {device_path}: {exc}")
        else:
            device_platform = device_payload.get("platform")
            if device_platform not in PLATFORM_FILES:
                errors.append(f"{device_path}: platform must be ios or android")
            else:
                payload, device_errors = validate_evidence(
                    device_path,
                    device_platform,
                    f"{device_platform}_device",
                    require_current_source=require_current_source,
                    skill_root=skill_root,
                    fixture_root=fixture_root,
                )
                if payload:
                    evidence["real_device"] = payload
                errors.extend(device_errors)
    return {
        "schema": VALIDATION_SCHEMA,
        "root": str(root),
        "required_platforms": required,
        "require_real_device": require_real_device,
        "require_current_source": require_current_source,
        "ok": not errors,
        "evidence": evidence,
        "errors": errors,
    }


def run_self_check() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="design-craft-native-runtime-") as raw:
        root = Path(raw)
        before_path = root / "before.png"
        after_path = root / "after.png"
        marker_path = root / "runtime-interaction.txt"
        launch_path = root / "launch.txt"
        attempt = "live-self-check-1"
        before_path.write_bytes(PNG_SIGNATURE + b"before")
        after_path.write_bytes(PNG_SIGNATURE + b"after")
        marker_path.write_text(
            f"Runtime interaction confirmed attempt={attempt}\n",
            encoding="utf-8",
        )
        launch_path.write_text(
            "\n".join(
                (
                    "[poll observations]",
                    json.dumps(
                        {
                            "schema": "design-craft.native-ios-poll.v1",
                            "phase": "live",
                            "attempt": attempt,
                            "poll": 1,
                            "openurl_exit": 0,
                            "url_receipt": True,
                            "app_confirmation": True,
                            "marker_exists": True,
                            "marker_state": "confirmed",
                            "marker_confirmed": True,
                            "decision": "fully_confirmed",
                            "fallback_allowed": False,
                            "transport_warning": None,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "[system confirmation action] not-attempted",
                    "[confirmed interaction path] live-deep-link",
                    "",
                )
            ),
            encoding="utf-8",
        )

        def artifact(role: str, artifact_path: Path) -> dict[str, object]:
            return {
                "role": role,
                "path": artifact_path.name,
                "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
                "bytes": artifact_path.stat().st_size,
            }

        valid = {
            "schema": EVIDENCE_SCHEMA,
            "platform": "ios",
            "verified": True,
            "runtime_kind": "ios_simulator",
            "evidence_level": "runtime_observed",
            "observed_at": "2026-01-01T00:00:00Z",
            "runtime_id_kind": "sha256",
            "runtime_id": f"sha256:{'d' * 64}",
            "tool": "fixture",
            "source_commit": "a" * 40,
            "source_dirty": False,
            "skill_source_dirty": False,
            "repo_dirty": False,
            "skill_version": "0.0.0",
            "skill_tree_sha256": "b" * 64,
            "fixture_tree_sha256": "c" * 64,
            "contract_sha256": "e" * 64,
            "capture_context": "fixture",
            "workflow": {
                "repository": "example/design-craft",
                "run_id": 1,
                "run_attempt": 1,
                "url": "https://example.invalid/example/design-craft/actions/runs/1",
                "event": "workflow_dispatch",
                "head_sha": "a" * 40,
                "ref": "refs/heads/main",
            },
            "commands": ["xcrun simctl boot fixture"],
            "assertions": {
                "build_succeeded": True,
                "install_and_launch_succeeded": True,
                "runtime_interaction_observed": True,
                "before_and_after_screenshots_captured": True,
            },
            "artifacts": [
                artifact("before_screenshot", before_path),
                artifact("after_screenshot", after_path),
                artifact("interaction_marker", marker_path),
                artifact("launch_log", launch_path),
            ],
        }
        path = root / "ios-observed.json"
        path.write_text(json.dumps(valid), encoding="utf-8")
        _, valid_errors = validate_evidence(path, "ios")
        errors.extend(valid_errors)
        valid["evidence_level"] = "static_source"
        path.write_text(json.dumps(valid), encoding="utf-8")
        _, invalid_errors = validate_evidence(path, "ios")
        if not any("runtime_observed" in item for item in invalid_errors):
            errors.append("self-check failed to reject static evidence")
        valid["evidence_level"] = "runtime_observed"
        valid["artifacts"][0]["path"] = "missing.png"
        path.write_text(json.dumps(valid), encoding="utf-8")
        _, missing_artifact_errors = validate_evidence(path, "ios")
        if not any("file is missing" in item for item in missing_artifact_errors):
            errors.append("self-check failed to reject missing runtime artifacts")

        valid["artifacts"][0]["path"] = before_path.name
        valid["runtime_id"] = "raw-device-identifier"
        path.write_text(json.dumps(valid), encoding="utf-8")
        _, raw_id_errors = validate_evidence(path, "ios")
        if not any("redacted SHA-256" in item for item in raw_id_errors):
            errors.append("self-check failed to reject a raw runtime identifier")
        valid["runtime_id"] = f"sha256:{'d' * 64}"

        removed_assertion = valid["assertions"].pop("runtime_interaction_observed")
        path.write_text(json.dumps(valid), encoding="utf-8")
        _, assertion_errors = validate_evidence(path, "ios")
        if not any("missing required checks" in item for item in assertion_errors):
            errors.append("self-check failed to reject a missing required assertion")
        valid["assertions"]["runtime_interaction_observed"] = removed_assertion

        removed_artifact = valid["artifacts"].pop()
        path.write_text(json.dumps(valid), encoding="utf-8")
        _, role_errors = validate_evidence(path, "ios")
        if not any("missing required roles" in item for item in role_errors):
            errors.append("self-check failed to reject a missing required artifact role")
        valid["artifacts"].append(removed_artifact)

        source_repo = root / "source-repo"
        source_skill = source_repo / "skills/design-craft"
        source_fixtures = source_repo / "evals/native-runtime/fixtures"
        shutil.copytree(DEFAULT_SKILL_ROOT, source_skill)
        shutil.copytree(DEFAULT_FIXTURE_ROOT / "ios", source_fixtures / "ios")
        for command in (
            ("git", "init", "-q"),
            ("git", "config", "user.email", "fixture@example.invalid"),
            ("git", "config", "user.name", "Fixture"),
            ("git", "add", "."),
            ("git", "commit", "-qm", "native evidence fixture"),
        ):
            subprocess.run(command, cwd=source_repo, check=True)

        valid["skill_version"] = read_version(source_skill)
        valid["skill_tree_sha256"] = tree_sha256(source_skill)
        valid["fixture_tree_sha256"] = tree_sha256(
            source_fixtures / "ios",
            ignored_dirs={"build", ".gradle"},
        )
        valid["contract_sha256"] = native_contract_sha256("ios")
        valid["source_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=source_repo, text=True
        ).strip()
        valid["workflow"]["head_sha"] = valid["source_commit"]
        path.write_text(json.dumps(valid), encoding="utf-8")
        _, current_errors = validate_evidence(
            path,
            "ios",
            require_current_source=True,
            skill_root=source_skill,
            fixture_root=source_fixtures,
        )
        errors.extend(current_errors)
        valid["fixture_tree_sha256"] = "d" * 64
        path.write_text(json.dumps(valid), encoding="utf-8")
        _, stale_errors = validate_evidence(
            path,
            "ios",
            require_current_source=True,
            skill_root=source_skill,
            fixture_root=source_fixtures,
        )
        if not any("fixture_tree_sha256" in item for item in stale_errors):
            errors.append("self-check failed to reject stale fixture-bound evidence")
        valid["fixture_tree_sha256"] = tree_sha256(
            source_fixtures / "ios",
            ignored_dirs={"build", ".gradle"},
        )
        valid["contract_sha256"] = "f" * 64
        path.write_text(json.dumps(valid), encoding="utf-8")
        _, contract_errors = validate_evidence(
            path,
            "ios",
            require_current_source=True,
            skill_root=source_skill,
            fixture_root=source_fixtures,
        )
        if not any("contract_sha256" in item for item in contract_errors):
            errors.append("self-check failed to reject stale runtime-contract evidence")
        valid["contract_sha256"] = native_contract_sha256("ios")

        device_root = root / "device"
        device_root.mkdir()
        before_xml = device_root / "window-before.xml"
        after_xml = device_root / "window-after.xml"
        device_png = device_root / "android-device.png"
        device_launch = device_root / "launch.txt"
        before_xml.write_text(
            '<hierarchy><node content-desc="Native runtime evidence title" /></hierarchy>',
            encoding="utf-8",
        )
        after_xml.write_text(
            '<hierarchy><node text="Runtime interaction confirmed" /></hierarchy>',
            encoding="utf-8",
        )
        device_png.write_bytes(PNG_SIGNATURE + b"device")
        device_launch.write_text("physical device launched\n", encoding="utf-8")

        def device_artifact(role: str, artifact_path: Path) -> dict[str, object]:
            return {
                "role": role,
                "path": artifact_path.name,
                "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
                "bytes": artifact_path.stat().st_size,
            }

        device_payload = {
            **valid,
            "platform": "android",
            "runtime_kind": "android_device",
            "fixture_tree_sha256": "e" * 64,
            "contract_sha256": native_contract_sha256("android"),
            "assertions": {
                assertion: True for assertion in REQUIRED_ASSERTIONS["android_device"]
            },
            "artifacts": [
                device_artifact("before_accessibility_tree", before_xml),
                device_artifact("after_accessibility_tree", after_xml),
                device_artifact("after_screenshot", device_png),
                device_artifact("launch_log", device_launch),
            ],
        }
        (device_root / "real-device-observed.json").write_text(
            json.dumps(device_payload), encoding="utf-8"
        )
        device_validation = validate_root(device_root, [], require_real_device=True)
        if not device_validation["ok"]:
            errors.extend(device_validation["errors"])
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true", help="Probe native SDK and runtime availability")
    parser.add_argument("--write-probe", help="Write the probe JSON to this path")
    parser.add_argument("--validate", action="store_true", help="Validate observed runtime evidence")
    parser.add_argument("--root", default="evals/native-runtime")
    parser.add_argument("--require", action="append", choices=sorted(PLATFORM_FILES), default=[])
    parser.add_argument("--require-real-device", action="store_true")
    parser.add_argument(
        "--require-current-source",
        action="store_true",
        help="Require clean evidence bound to the current skill and fixture trees.",
    )
    parser.add_argument("--skill-root", default=str(DEFAULT_SKILL_ROOT))
    parser.add_argument("--fixture-root", default=str(DEFAULT_FIXTURE_ROOT))
    parser.add_argument("--check", action="store_true", help="Run offline validation self-checks")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.check:
        errors = run_self_check()
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        return 0

    if args.probe or args.write_probe:
        payload = probe_environment()
        if args.write_probe:
            path = Path(args.write_probe).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.json or not args.write_probe:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.validate:
        if args.require:
            required = args.require
        elif args.require_real_device:
            required = []
        else:
            required = sorted(PLATFORM_FILES)
        payload = validate_root(
            Path(args.root).expanduser().resolve(),
            required,
            require_real_device=args.require_real_device,
            require_current_source=args.require_current_source,
            skill_root=Path(args.skill_root).expanduser().resolve(),
            fixture_root=Path(args.fixture_root).expanduser().resolve(),
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        elif payload["ok"]:
            print("native runtime evidence verified")
        else:
            print("\n".join(payload["errors"]), file=sys.stderr)
        return 0 if payload["ok"] else 2

    parser.error("choose --probe, --write-probe, --validate, or --check")


if __name__ == "__main__":
    raise SystemExit(main())
