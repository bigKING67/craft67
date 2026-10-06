#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "reverse-craft"
SCHEMA = ROOT / "tests" / "fixtures" / "host-response.schema.json"
R0_REPLAN_SCHEMA = ROOT / "tests" / "fixtures" / "host-r0-replan-response.schema.json"
EVALUATION_MODE = "blind-contract"
SKILL_NAME = "reverse-craft"
OUTPUT_FIELDS = "route_id, module_reference, runtime_truth, mutates, evidence_chain"
R0_REPLAN_OUTPUT_FIELDS = (
    "route_id, module_reference, bounded_operation_replan, phase_move_replan, "
    "primary_route_unchanged, progress_record, replan_gate, change_required"
)
DEFAULT_RESPONSE_INSTRUCTIONS = """route_id, module_reference, and runtime_truth must be JSON strings; mutates must be a JSON boolean; evidence_chain must be a JSON array of strings. Copy route_id and module_reference exactly from the primary deterministic route; if the route command is unavailable, read its route/module data and preserve the full reference string without shortening it. For runtime_truth, copy the shortest exact name or phrase used by the Skill for the canonical runtime or default public collection mechanism. Use the Skill's exact evidence labels and order."""
R0_REPLAN_RESPONSE_INSTRUCTIONS = """route_id, module_reference, and replan_gate must be JSON strings; bounded_operation_replan and phase_move_replan must each be a JSON array of booleans in the task's checkpoint order; primary_route_unchanged and change_required must be JSON booleans; progress_record must be a JSON array of strings. Copy route_id and module_reference exactly from the primary deterministic route; if the route command is unavailable, read its route/module data and preserve the full reference string without shortening it. Read the primary route's module and decide whether replanning is required at each checkpoint. State whether that route remains primary after progress stalls. For progress_record, copy the exact labels in module order that must be recorded before replanning. Copy replan_gate as the shortest exact named gate from the module. State whether the next feasible plan must change one of the module's allowed dimensions."""


def evaluation_prompt(
    task: str,
    output_fields: str = OUTPUT_FIELDS,
    response_instructions: str = DEFAULT_RESPONSE_INSTRUCTIONS,
) -> str:
    return f"""{task} Load the explicitly invoked Skill and follow its deterministic routing instructions. You may inspect only files inside that Skill and, when the host supports it, run only its dependency-free read-only route command. Do not access a network or target, modify files, or invent routes or metadata. Return exactly one JSON object with these fields: {output_fields}. {response_instructions} Do not explain the result or use Markdown."""


PROFILES = {
    "r3": {
        "task": "An authorized sandbox task asks for a read-only planning decision about reconstructing a frontend-signing chain behind a browser request. No artifact or live browser is available.",
        "expected": {
            "route_id": "R3",
            "module_reference": "modules/web-api-identity.md",
            "runtime_truth": "browser67",
            "mutates": False,
            "evidence_chain": ["Evidence", "Finding", "Path", "Report"],
        },
    },
    "r44": {
        "task": "An authorized analyst asks for a read-only planning decision about enriching a malware IOC from public sources and preparing an intelligence handoff. No source lookup is authorized or available.",
        "expected": {
            "route_id": "R44",
            "module_reference": "modules/threat-intelligence-osint.md",
            "runtime_truth": "Web search",
            "mutates": False,
            "evidence_chain": ["Evidence", "Finding", "Path", "Report"],
        },
        "normalizers": {
            "runtime_truth": {
                "Web search": "Web search",
                "normal Web search": "Web search",
            },
        },
    },
    "r0-replan": {
        "task": "An authorized sandbox analyst is examining an unfamiliar stripped executable. Compare four read-only planning checkpoints that yielded no new Evidence: after two bounded operations and after the next operation; after one move between analysis phases and after the next such move. A debugger is available and authorized but has not yet been used. Give only the planning decisions; do not analyze a target.",
        "output_fields": R0_REPLAN_OUTPUT_FIELDS,
        "response_instructions": R0_REPLAN_RESPONSE_INSTRUCTIONS,
        "response_schema": R0_REPLAN_SCHEMA,
        "expected": {
            "route_id": "R0",
            "module_reference": "modules/binary-foundations.md",
            "bounded_operation_replan": [False, True],
            "phase_move_replan": [False, True],
            "primary_route_unchanged": True,
            "progress_record": ["current hypothesis", "attempts", "evidence gap", "decision delta"],
            "replan_gate": "feasibility gate",
            "change_required": True,
        },
        "normalizers": {
            "progress_record": {
                "current hypothesis": "current hypothesis",
                "hypothesis": "current hypothesis",
            },
        },
    },
}
for _profile in PROFILES.values():
    _profile["prompt"] = evaluation_prompt(
        _profile["task"],
        _profile.get("output_fields", OUTPUT_FIELDS),
        _profile.get("response_instructions", DEFAULT_RESPONSE_INSTRUCTIONS),
    )


def response_schema_path(profile: dict[str, Any]) -> Path:
    return profile.get("response_schema", SCHEMA)


def string_leaves(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [leaf for item in value.values() for leaf in string_leaves(item)]
    if isinstance(value, (list, tuple)):
        return [leaf for item in value for leaf in string_leaves(item)]
    return []


def semantic_schema_keywords(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in {"const", "enum"}:
                findings.append(child)
            findings.extend(semantic_schema_keywords(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(semantic_schema_keywords(item, f"{path}[{index}]"))
    return findings


def unsupported_schema_keywords(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key == "uniqueItems":
                findings.append(child)
            findings.extend(unsupported_schema_keywords(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(unsupported_schema_keywords(item, f"{path}[{index}]"))
    return findings


def expectation_exposure_errors(prompt: str, expected: dict[str, Any], response_schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    schema_text = json.dumps(response_schema, ensure_ascii=False, sort_keys=True)
    for value in sorted(set(string_leaves(expected))):
        if value in prompt:
            errors.append(f"prompt exposes expected value: {value}")
        if value in schema_text:
            errors.append(f"response schema exposes expected value: {value}")
    for path in semantic_schema_keywords(response_schema):
        errors.append(f"response schema contains answer-bearing constraint: {path}")
    for path in unsupported_schema_keywords(response_schema):
        errors.append(f"response schema contains unsupported constraint: {path}")
    return errors


def skill_source_files(root: Path = SKILL) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def skill_bundle_sha256(root: Path = SKILL) -> str:
    digest = hashlib.sha256()
    for path in skill_source_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def skill_identity(root: Path = SKILL) -> dict[str, Any]:
    entrypoint = root / "SKILL.md"
    version_file = root / "VERSION"
    return {
        "name": SKILL_NAME,
        "version": version_file.read_text(encoding="utf-8").strip(),
        "path": str(root),
        "entrypoint_sha256": hashlib.sha256(entrypoint.read_bytes()).hexdigest(),
        "bundle_sha256": skill_bundle_sha256(root),
        "source_file_count": len(skill_source_files(root)),
    }


def host_prompt(host: str, prompt: str) -> str:
    if host == "codex":
        return f"Use ${SKILL_NAME} for this evaluation.\n\n{prompt}"
    if host == "pi":
        return f"/skill:{SKILL_NAME} {prompt}"
    raise ValueError(f"unsupported host: {host}")


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def private_contract(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "expected": profile["expected"],
        "normalizers": profile.get("normalizers", {}),
    }


def expected_contract_sha256(profile: dict[str, Any]) -> str:
    return canonical_json_sha256(private_contract(profile))


def evaluation_receipt(prompt: str, schema_bytes: bytes, profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_mode": EVALUATION_MODE,
        "expectation_exposed": False,
        "evaluation_prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "host_prompt_sha256": {
            host: hashlib.sha256(host_prompt(host, prompt).encode("utf-8")).hexdigest()
            for host in ("codex", "pi")
        },
        "response_schema_sha256": hashlib.sha256(schema_bytes).hexdigest(),
        "expected_contract_sha256": expected_contract_sha256(profile),
        "skill": skill_identity(),
    }


def materialize_skill(target: Path) -> dict[str, Any]:
    shutil.copytree(SKILL, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    identity = skill_identity(target)
    identity["path"] = str(target)
    return identity


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real Codex and Pi Reverse Craft behavior evaluations")
    parser.add_argument("--host", choices=["all", "codex", "pi"], default="all")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="r3")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--regrade-receipt")
    parser.add_argument("--output")
    return parser.parse_args()


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("host output does not contain a JSON object")


def normalize_payload(value: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(value)
    for field, aliases in profile.get("normalizers", {}).items():
        raw = normalized.get(field)
        if isinstance(raw, str):
            normalized[field] = aliases.get(raw, raw)
        elif isinstance(raw, list):
            normalized[field] = [
                aliases.get(item, item) if isinstance(item, str) else item
                for item in raw
            ]
    return normalized


def validate_payload(value: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    expected = profile["expected"]
    normalized = normalize_payload(value, profile)
    errors = [
        f"{key}: expected {expected_value!r}, got {value.get(key)!r}"
        for key, expected_value in expected.items()
        if normalized.get(key) != expected_value
    ]
    extra = sorted(set(value) - set(expected))
    if extra:
        errors.append(f"unexpected keys: {extra}")
    return errors


def safe_error_tail(value: str) -> str:
    tail = value[-1500:]
    tail = re.sub(r"(?i)(api key provided:\s*)[^.,\s]+", r"\1[REDACTED]", tail)
    tail = re.sub(r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._-]+", r"\1[REDACTED]", tail)
    return tail


def run_codex(workspace: Path, timeout: int, prompt: str, profile: dict[str, Any]) -> dict[str, Any]:
    binary = shutil.which("codex")
    if not binary:
        return {"host": "codex", "status": "missing", "valid": False}
    skill_target = workspace / ".agents" / "skills" / "reverse-craft"
    skill_target.parent.mkdir(parents=True)
    snapshot = materialize_skill(skill_target)
    prompt = host_prompt("codex", prompt)
    output = workspace / "codex-output.json"
    codex_env = {**os.environ, "NO_COLOR": "1"}
    # A generic OPENAI_API_KEY can override Codex's own authenticated account.
    codex_env.pop("OPENAI_API_KEY", None)
    completed = subprocess.run(
        [
            binary, "exec", "--ephemeral", "--ignore-rules", "--sandbox", "read-only",
            "--disable", "hooks", "--disable", "memories", "--disable", "plugins", "--disable", "apps",
            "--skip-git-repo-check", "-C", str(workspace),
            "--output-schema", str(response_schema_path(profile)),
            "--output-last-message", str(output), prompt,
        ],
        text=True, capture_output=True, timeout=timeout, check=False,
        env=codex_env,
    )
    raw = output.read_text(encoding="utf-8") if output.is_file() else completed.stdout
    try:
        payload = extract_json(raw)
        normalized_payload = normalize_payload(payload, profile)
        errors = validate_payload(payload, profile)
    except Exception as exc:
        payload = None
        normalized_payload = None
        errors = [f"{type(exc).__name__}: {exc}"]
    if snapshot["bundle_sha256"] != skill_bundle_sha256():
        errors.append("materialized Skill snapshot does not match source bundle")
    return {
        "host": "codex", "status": "passed" if completed.returncode == 0 and not errors else "failed",
        "valid": completed.returncode == 0 and not errors, "exit_code": completed.returncode,
        "version": subprocess.run([binary, "--version"], text=True, capture_output=True, timeout=10, check=False).stdout.strip(),
        "invocation": {"mode": "explicit", "syntax": f"${SKILL_NAME}", "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()},
        "skill_snapshot": snapshot,
        "payload": payload,
        "payload_sha256": canonical_json_sha256(payload) if payload is not None else None,
        "normalized_payload": normalized_payload,
        "normalized_payload_sha256": canonical_json_sha256(normalized_payload) if normalized_payload is not None else None,
        "errors": errors,
        "stderr_tail": safe_error_tail(completed.stderr) if completed.returncode else "",
    }


def run_pi(workspace: Path, timeout: int, prompt: str, profile: dict[str, Any]) -> dict[str, Any]:
    binary = shutil.which("pi")
    if not binary:
        return {"host": "pi", "status": "missing", "valid": False}
    session_dir = workspace / "pi-sessions"
    session_dir.mkdir()
    skill_target = workspace / "eval-skills" / "reverse-craft"
    skill_target.parent.mkdir()
    snapshot = materialize_skill(skill_target)
    prompt = host_prompt("pi", prompt)
    env = {**os.environ, "PI_CODING_AGENT_SESSION_DIR": str(session_dir), "NO_COLOR": "1"}
    completed = subprocess.run(
        [
            binary, "--print", "--no-session", "--no-extensions", "--no-context-files", "--no-skills",
            "--tools", "read", "--skill", str(skill_target), prompt,
        ],
        cwd=workspace, text=True, capture_output=True, timeout=timeout, check=False, env=env,
    )
    try:
        payload = extract_json(completed.stdout)
        normalized_payload = normalize_payload(payload, profile)
        errors = validate_payload(payload, profile)
    except Exception as exc:
        payload = None
        normalized_payload = None
        errors = [f"{type(exc).__name__}: {exc}"]
    if snapshot["bundle_sha256"] != skill_bundle_sha256():
        errors.append("materialized Skill snapshot does not match source bundle")
    return {
        "host": "pi", "status": "passed" if completed.returncode == 0 and not errors else "failed",
        "valid": completed.returncode == 0 and not errors, "exit_code": completed.returncode,
        "version": subprocess.run([binary, "--version"], text=True, capture_output=True, timeout=10, check=False).stdout.strip(),
        "invocation": {"mode": "explicit", "syntax": f"/skill:{SKILL_NAME}", "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()},
        "skill_snapshot": snapshot,
        "payload": payload,
        "payload_sha256": canonical_json_sha256(payload) if payload is not None else None,
        "normalized_payload": normalized_payload,
        "normalized_payload_sha256": canonical_json_sha256(normalized_payload) if normalized_payload is not None else None,
        "errors": errors,
        "stderr_tail": safe_error_tail(completed.stderr) if completed.returncode else "",
    }


def stable_skill_identity(value: dict[str, Any]) -> dict[str, Any]:
    keys = ("name", "version", "entrypoint_sha256", "bundle_sha256", "source_file_count")
    return {key: value.get(key) for key in keys}


def regrade_receipt(
    source_path: Path,
    profile_name: str,
    profile: dict[str, Any],
    schema_bytes: bytes,
) -> dict[str, Any]:
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    current = evaluation_receipt(profile["prompt"], schema_bytes, profile)
    receipt_errors: list[str] = []

    def require_equal(label: str, actual: Any, expected: Any) -> None:
        if actual != expected:
            receipt_errors.append(f"{label}: expected {expected!r}, got {actual!r}")

    require_equal("source schema", source.get("schema"), "reverse-craft.host-eval.v2")
    require_equal("source evaluation mode", source.get("evaluation_mode"), EVALUATION_MODE)
    require_equal("source profile", source.get("profile"), profile_name)
    require_equal("source expectation exposure", source.get("expectation_exposed"), False)
    require_equal(
        "source evaluation prompt hash",
        source.get("evaluation_prompt_sha256"),
        current["evaluation_prompt_sha256"],
    )
    require_equal("source host prompt hashes", source.get("host_prompt_sha256"), current["host_prompt_sha256"])
    require_equal(
        "source response schema hash",
        source.get("response_schema_sha256"),
        current["response_schema_sha256"],
    )
    require_equal(
        "source Skill identity",
        stable_skill_identity(source.get("skill", {})),
        stable_skill_identity(current["skill"]),
    )

    requested = source.get("requested")
    if not isinstance(requested, list) or not requested or any(host not in {"codex", "pi"} for host in requested):
        receipt_errors.append(f"source requested hosts are invalid: {requested!r}")
        requested = []
    elif len(requested) != len(set(requested)):
        receipt_errors.append(f"source requested hosts contain duplicates: {requested!r}")
    source_results = source.get("results")
    if not isinstance(source_results, list):
        receipt_errors.append("source results are not an array")
        source_results = []
    by_host = {item.get("host"): item for item in source_results if isinstance(item, dict)}
    require_equal("source result count", len(source_results), len(by_host))
    require_equal("source result hosts", sorted(by_host), sorted(requested))

    results: list[dict[str, Any]] = []
    for host in requested:
        item = by_host.get(host, {})
        errors: list[str] = []
        if item.get("exit_code") != 0:
            errors.append(f"source host exit code is not zero: {item.get('exit_code')!r}")
        invocation = item.get("invocation") if isinstance(item.get("invocation"), dict) else {}
        if invocation.get("prompt_sha256") != current["host_prompt_sha256"][host]:
            errors.append("source host invocation prompt hash does not match")
        snapshot = item.get("skill_snapshot") if isinstance(item.get("skill_snapshot"), dict) else {}
        if stable_skill_identity(snapshot) != stable_skill_identity(current["skill"]):
            errors.append("source host Skill snapshot does not match")
        payload = item.get("payload")
        if not isinstance(payload, dict):
            errors.append("source host payload is not an object")
            payload_hash = None
            normalized_payload = None
            normalized_payload_hash = None
        else:
            normalized_payload = normalize_payload(payload, profile)
            errors.extend(validate_payload(payload, profile))
            payload_hash = canonical_json_sha256(payload)
            normalized_payload_hash = canonical_json_sha256(normalized_payload)
        results.append({
            "host": host,
            "version": item.get("version"),
            "source_status": item.get("status"),
            "source_errors": item.get("errors", []),
            "payload": payload,
            "payload_sha256": payload_hash,
            "normalized_payload": normalized_payload,
            "normalized_payload_sha256": normalized_payload_hash,
            "errors": errors,
            "valid": not errors,
        })

    valid = not receipt_errors and all(item["valid"] for item in results) and bool(results)
    return {
        "schema": "reverse-craft.host-eval-regrade.v1",
        "valid": valid,
        "profile": profile_name,
        "requested": requested,
        "results": results,
        "errors": receipt_errors,
        "source_receipt": {
            "path": str(source_path),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "schema": source.get("schema"),
            "valid": source.get("valid"),
            "expected_contract_sha256": source.get("expected_contract_sha256"),
        },
        **current,
    }


def render_result(payload: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).expanduser().resolve().write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def main() -> int:
    args = parse_args()
    profile = PROFILES[args.profile]
    requested = ["codex", "pi"] if args.host == "all" else [args.host]
    schema_bytes = response_schema_path(profile).read_bytes()
    response_schema = json.loads(schema_bytes)
    exposure_errors = []
    for host in requested:
        exposure_errors.extend(
            f"{host}: {error}"
            for error in expectation_exposure_errors(
                host_prompt(host, profile["prompt"]), private_contract(profile), response_schema,
            )
        )
    receipt = evaluation_receipt(profile["prompt"], schema_bytes, profile)
    if exposure_errors:
        payload = {
            "schema": "reverse-craft.host-eval.v2", "valid": False, "profile": args.profile,
            "requested": requested, "missing": [], "results": [], **receipt,
            "expectation_exposed": True, "errors": exposure_errors,
        }
        render_result(payload, args.output)
        return 2
    if args.regrade_receipt:
        payload = regrade_receipt(
            Path(args.regrade_receipt).expanduser().resolve(),
            args.profile,
            profile,
            schema_bytes,
        )
        render_result(payload, args.output)
        return 0 if payload["valid"] else 1
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="reverse-craft-host-eval-") as raw:
        root = Path(raw)
        for host in requested:
            workspace = root / host
            workspace.mkdir()
            try:
                result = (
                    run_codex(workspace, args.timeout, profile["prompt"], profile)
                    if host == "codex"
                    else run_pi(workspace, args.timeout, profile["prompt"], profile)
                )
            except subprocess.TimeoutExpired:
                result = {"host": host, "status": "timeout", "valid": False, "errors": [f"timeout after {args.timeout}s"]}
            results.append(result)
    missing = [item["host"] for item in results if item["status"] == "missing"]
    valid = all(item["valid"] or (args.allow_missing and item["status"] == "missing") for item in results)
    payload = {
        "schema": "reverse-craft.host-eval.v2", "valid": valid, "profile": args.profile, "requested": requested,
        "missing": missing, "results": results,
        "isolation": {"codex": "ephemeral, explicit workspace Skill snapshot, ignore rules, hooks/memories/plugins/apps disabled, read-only sandbox", "pi": "explicit Skill snapshot, no session/extensions/context/default skills, read-only file tool only; temporary session directory"},
        **receipt,
    }
    render_result(payload, args.output)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
