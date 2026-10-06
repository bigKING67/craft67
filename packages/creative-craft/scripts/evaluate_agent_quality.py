#!/usr/bin/env python3
"""Run isolated, blind A/B/C Agent quality evaluations for Creative Craft."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVAL_CONFIG = ROOT / "evals" / "agent-quality"
OUTPUT_ROOT = ROOT / "dist" / "evals" / "agent-quality"
SKILL_ROOT = ROOT / "skills" / "creative-craft"
VARIANTS = ("baseline", "current", "candidate")
SCORE_FIELDS = (
    "strategic_fit",
    "distinctiveness",
    "execution_readiness",
    "evidence_honesty",
    "reference_change_preserve",
    "scope_proportionality",
    "clarity_usefulness",
)
SCORE_LIMITS = {
    "strategic_fit": 20,
    "distinctiveness": 15,
    "execution_readiness": 20,
    "evidence_honesty": 10,
    "reference_change_preserve": 10,
    "scope_proportionality": 15,
    "clarity_usefulness": 10,
}
SKILL_ENTRYPOINT_PATTERN = re.compile(
    r"(?:[A-Za-z]:[\\/]|/)[^\"'\s]*?creative-craft[\\/]SKILL\.md"
)
SKILL_SOURCE_CONTRACT_VERSION = 1


class EvalError(RuntimeError):
    """Raised for a deterministic evaluation contract failure."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def captured_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def load_cases(path: Path = EVAL_CONFIG / "cases.json") -> list[dict[str, Any]]:
    payload = read_json(path)
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list) or not cases:
        raise EvalError(f"invalid or empty cases file: {path}")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise EvalError("every quality case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise EvalError(f"invalid or duplicate quality case id: {case_id!r}")
        ids.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise EvalError(f"quality case {case_id} has no prompt")
        if case.get("expected_mode") not in {"quick", "traceable"}:
            raise EvalError(f"quality case {case_id} has invalid expected_mode")
    return cases


def load_routing_cases(
    path: Path = EVAL_CONFIG / "routing.json",
) -> list[dict[str, Any]]:
    payload = read_json(path)
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list) or not cases:
        raise EvalError(f"invalid or empty routing file: {path}")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise EvalError("every routing case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise EvalError(f"invalid or duplicate routing case id: {case_id!r}")
        ids.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise EvalError(f"routing case {case_id} has no prompt")
        if not isinstance(case.get("expect_creative_craft"), bool):
            raise EvalError(f"routing case {case_id} has no boolean expectation")
    return cases


def selected_cases(
    cases: list[dict[str, Any]], requested_ids: list[str] | None
) -> list[dict[str, Any]]:
    if not requested_ids:
        return cases
    by_id = {case["id"]: case for case in cases}
    unknown = sorted(set(requested_ids) - set(by_id))
    if unknown:
        raise EvalError(f"unknown case ids: {', '.join(unknown)}")
    return [by_id[case_id] for case_id in requested_ids]


def skill_files(root: Path) -> list[Path]:
    if not root.is_dir() or root.is_symlink():
        raise EvalError(f"skill root is missing or unsafe: {root}")
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise EvalError(f"skill tree contains a symlink: {path}")
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(path)
    if not files:
        raise EvalError(f"skill tree contains no files: {root}")
    return files


def skill_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in skill_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def copy_skill(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for path in skill_files(source):
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def export_git_skill(revision: str, destination: Path) -> None:
    raw = subprocess.check_output(
        ["git", "ls-tree", "-r", "-z", revision, "--", "skills/creative-craft"],
        cwd=ROOT,
    )
    records = [record for record in raw.split(b"\0") if record]
    if not records:
        raise EvalError(f"revision {revision} has no creative-craft skill")
    destination.mkdir(parents=True, exist_ok=False)
    prefix = PurePosixPath("skills/creative-craft")
    for record in records:
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, _object_id = metadata.decode("ascii").split()
        source_path = PurePosixPath(raw_path.decode("utf-8"))
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise EvalError(f"unsafe git entry in skill snapshot: {source_path}")
        try:
            relative = source_path.relative_to(prefix)
        except ValueError as error:
            raise EvalError(f"git entry escaped skill prefix: {source_path}") from error
        target = destination.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = subprocess.check_output(
            ["git", "show", f"{revision}:{source_path.as_posix()}"], cwd=ROOT
        )
        target.write_bytes(payload)


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def codex_version(codex_bin: str) -> str:
    result = subprocess.run(
        [codex_bin, "--version"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def load_provider_transport(config_file: Path) -> dict[str, Any] | None:
    """Extract only non-secret transport fields from the user's Codex config."""
    if not config_file.is_file():
        return None
    lines = config_file.read_text(encoding="utf-8").splitlines()
    provider_id: str | None = None
    section: str | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
            continue
        if section is None and "=" in stripped:
            key, raw_value = (part.strip() for part in stripped.split("=", 1))
            if key == "model_provider":
                value = parse_simple_toml_value(raw_value)
                if not isinstance(value, str):
                    raise EvalError("model_provider must be a string")
                provider_id = value
                break
    if provider_id is None:
        return None
    if (
        not isinstance(provider_id, str)
        or not provider_id.replace("-", "").replace("_", "").isalnum()
    ):
        raise EvalError("user config contains an unsafe model_provider id")
    allowed_types = {
        "name": str,
        "base_url": str,
        "wire_api": str,
        "requires_openai_auth": bool,
        "supports_websockets": bool,
    }
    transport: dict[str, Any] = {"id": provider_id}
    target_section = f"model_providers.{provider_id}"
    section = None
    found_section = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
            found_section = found_section or section == target_section
            continue
        if section != target_section or "=" not in stripped:
            continue
        key, raw_value = (part.strip() for part in stripped.split("=", 1))
        if key not in allowed_types:
            continue
        value = parse_simple_toml_value(raw_value)
        expected_type = allowed_types[key]
        if not isinstance(value, expected_type):
            raise EvalError(f"model provider field {key} has an invalid type")
        if isinstance(value, str) and ("\n" in value or "\r" in value):
            raise EvalError(f"model provider field {key} contains a newline")
        transport[key] = value
    if not found_section:
        raise EvalError(f"user config has no definition for model_provider {provider_id}")
    return transport


def parse_simple_toml_value(raw: str) -> str | bool:
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw.startswith('"') and raw.endswith('"'):
        value = json.loads(raw)
        if isinstance(value, str):
            return value
    if raw.startswith("'") and raw.endswith("'") and "'" not in raw[1:-1]:
        return raw[1:-1]
    raise EvalError("unsupported value in allowlisted model provider config")


def toml_literal(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return json.dumps(value)
    raise EvalError(f"unsupported provider transport value: {type(value).__name__}")


def validate_auth_path(auth_file: Path) -> None:
    # Existence is sufficient. The harness never opens or copies auth contents.
    if not auth_file.exists():
        raise EvalError(f"Codex auth file does not exist: {auth_file}")
    if auth_file.is_dir():
        raise EvalError(f"Codex auth path is a directory: {auth_file}")


def validate_config_files() -> None:
    load_cases()
    load_routing_cases()
    for name in ("judge.schema.json", "route.schema.json"):
        payload = read_json(EVAL_CONFIG / name)
        if not isinstance(payload, dict) or payload.get("type") != "object":
            raise EvalError(f"invalid output schema: {name}")


def build_isolated_environment(
    *, codex_home: Path, user_home: Path
) -> dict[str, str]:
    """Keep Codex auth/transport access while isolating user-level discovery."""
    isolated_roots = {
        "HOME": user_home,
        "USERPROFILE": user_home,
        "ZDOTDIR": user_home,
        "XDG_CONFIG_HOME": user_home / ".config",
        "XDG_DATA_HOME": user_home / ".local" / "share",
        "XDG_CACHE_HOME": user_home / ".cache",
        "APPDATA": user_home / "AppData" / "Roaming",
        "LOCALAPPDATA": user_home / "AppData" / "Local",
    }
    for path in set(isolated_roots.values()):
        path.mkdir(parents=True, exist_ok=True)
    (user_home / ".agents" / "skills").mkdir(parents=True, exist_ok=True)

    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(codex_home)
    environment.update({name: str(path) for name, path in isolated_roots.items()})
    environment.pop("HOMEDRIVE", None)
    environment.pop("HOMEPATH", None)
    return environment


def _nested_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in _nested_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in _nested_strings(child)]
    return []


def observed_skill_entrypoints(events_file: Path) -> set[str]:
    """Extract absolute Creative Craft entrypoint paths from Codex NDJSON events."""
    observed: set[str] = set()
    for line_number, line in enumerate(
        events_file.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise EvalError(
                f"invalid Codex event JSON at {events_file.name}:{line_number}"
            ) from error
        for value in _nested_strings(event):
            for match in SKILL_ENTRYPOINT_PATTERN.findall(value):
                observed.add(str(Path(match).resolve()).replace("\\", "/"))
    return observed


def verify_skill_source_events(
    events_file: Path,
    *,
    expected_entrypoint: Path | None,
    requirement: str,
) -> dict[str, Any]:
    if requirement not in {"forbidden", "required", "optional"}:
        raise EvalError(f"invalid Skill source requirement: {requirement}")
    if (requirement == "forbidden") != (expected_entrypoint is None):
        raise EvalError("Skill source requirement does not match the installed fixture")

    observed = observed_skill_entrypoints(events_file)
    expected = (
        None
        if expected_entrypoint is None
        else str(expected_entrypoint.resolve()).replace("\\", "/")
    )
    if requirement == "forbidden" and observed:
        raise EvalError(
            "Skill source contract failed: Creative Craft was read when forbidden"
        )
    if expected is not None:
        unexpected = observed - {expected}
        if unexpected:
            raise EvalError(
                "Skill source contract failed: Creative Craft was read outside the "
                "isolated fixture"
            )
        if requirement == "required" and expected not in observed:
            raise EvalError(
                "Skill source contract failed: isolated Creative Craft was not read"
            )
    return {
        "version": SKILL_SOURCE_CONTRACT_VERSION,
        "status": "passed",
        "requirement": requirement,
        "expected_location": "none" if expected is None else "isolated_fixture",
        "observed_entrypoint_count": len(observed),
    }


def build_codex_command(
    codex_bin: str,
    *,
    model: str,
    reasoning: str,
    output_file: Path,
    output_schema: Path | None = None,
    provider_transport: dict[str, Any] | None = None,
) -> list[str]:
    command = [
        codex_bin,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning}"',
    ]
    if provider_transport is not None:
        provider_id = provider_transport["id"]
        command.extend(["--config", f"model_provider={toml_literal(provider_id)}"])
        for key in (
            "name",
            "base_url",
            "wire_api",
            "requires_openai_auth",
            "supports_websockets",
        ):
            if key in provider_transport:
                override = (
                    f"model_providers.{provider_id}.{key}="
                    f"{toml_literal(provider_transport[key])}"
                )
                command.extend(
                    ["--config", override]
                )
    command.extend(["--json", "--output-last-message", str(output_file)])
    if output_schema is not None:
        command.extend(["--output-schema", str(output_schema)])
    command.append("-")
    return command


def public_command_receipt(
    *, kind: str, model: str, reasoning: str, has_schema: bool, has_skill: bool
) -> list[str]:
    command = [
        "codex",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning}"',
        "--json",
        "--output-last-message",
        "<isolated-output>",
    ]
    if has_schema:
        command.extend(["--output-schema", "<repo-schema>"])
    command.append("-")
    command.append(f"# kind={kind}; isolated_skill={str(has_skill).lower()}")
    return command


def run_codex(
    *,
    prompt: str,
    skill_source: Path | None,
    output_file: Path,
    events_file: Path,
    stderr_file: Path,
    output_schema: Path | None,
    auth_file: Path,
    codex_bin: str,
    model: str,
    reasoning: str,
    timeout_seconds: int,
    provider_transport: dict[str, Any] | None,
    expected_skill_digest: str | None = None,
    skill_read_requirement: str | None = None,
) -> dict[str, Any]:
    validate_auth_path(auth_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    events_file.parent.mkdir(parents=True, exist_ok=True)
    stderr_file.parent.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="creative-craft-agent-eval-") as directory:
        isolated = Path(directory)
        codex_home = isolated / "codex-home"
        user_home = isolated / "user-home"
        workspace = isolated / "workspace"
        codex_home.mkdir(mode=0o700)
        user_home.mkdir(mode=0o700)
        workspace.mkdir()
        (codex_home / "skills").mkdir()
        os.symlink(auth_file, codex_home / "auth.json")
        installed_skill: Path | None = None
        installed_digest: str | None = None
        if skill_source is not None:
            installed_skill = codex_home / "skills" / "creative-craft"
            copy_skill(skill_source, installed_skill)
            installed_digest = skill_digest(installed_skill)
            if (
                expected_skill_digest is not None
                and installed_digest != expected_skill_digest
            ):
                raise EvalError("isolated Skill digest does not match the bound source")
        elif expected_skill_digest is not None:
            raise EvalError("a Skill digest was supplied without a Skill fixture")

        requirement = skill_read_requirement
        if requirement is None:
            requirement = "required" if installed_skill is not None else "forbidden"

        isolated_output = isolated / "last-message.txt"
        command = build_codex_command(
            codex_bin,
            model=model,
            reasoning=reasoning,
            output_file=isolated_output,
            output_schema=output_schema,
            provider_transport=provider_transport,
        )
        environment = build_isolated_environment(
            codex_home=codex_home, user_home=user_home
        )
        try:
            result = subprocess.run(
                command,
                cwd=workspace,
                env=environment,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            events_file.write_text(captured_text(error.stdout), encoding="utf-8")
            stderr_file.write_text(captured_text(error.stderr), encoding="utf-8")
            raise EvalError(f"Codex call timed out after {timeout_seconds}s") from error

        events_file.write_text(result.stdout, encoding="utf-8")
        stderr_file.write_text(result.stderr, encoding="utf-8")
        if result.returncode != 0:
            raise EvalError(
                f"Codex call failed with exit code {result.returncode}; "
                f"see {stderr_file.relative_to(ROOT)}"
            )
        if not isolated_output.is_file():
            raise EvalError("Codex call succeeded without a final response file")
        source_contract = verify_skill_source_events(
            events_file,
            expected_entrypoint=(
                None if installed_skill is None else installed_skill / "SKILL.md"
            ),
            requirement=requirement,
        )
        source_contract["expected_sha256"] = expected_skill_digest
        source_contract["installed_sha256"] = installed_digest
        output_file.write_text(isolated_output.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "returncode": 0,
        "skill_source_contract": source_contract,
    }


def quality_prompt(user_prompt: str) -> str:
    return f"""Complete the user request directly and professionally.
Use an available skill only when it materially helps. Do not mention this
evaluation, the skill system, or hidden process. Do not inspect the workspace.
Produce the actual requested creative deliverable, not a plan for producing it.

USER REQUEST
{user_prompt}
"""


def judge_prompt(
    case: dict[str, Any], labeled_outputs: dict[str, str]
) -> str:
    outputs = "\n\n".join(
        f"## RESPONSE {label}\n{labeled_outputs[label]}" for label in ("A", "B", "C")
    )
    return f"""Act as a blind senior creative director and production reviewer.
Score all three responses to the same request. The labels are randomized; do
not infer their source. Judge the delivered work, not writing length or process
theater. Use integer scores and the exact JSON schema supplied by the caller.

Rubric (100 total):
- strategic_fit 0-20: understands objective, audience, tension, proposition,
  and whether the direction is selected or reopened. Reward returning to
  exploration when high-impact feedback changes direction; also reward bounded
  action without needless re-approval when the direction is explicit;
- distinctiveness 0-15: non-generic mechanism and real route separation;
- execution_readiness 0-20: concrete, coherent, makeable production detail;
- evidence_honesty 0-10: no invented facts, output claims, or performance claims;
- reference_change_preserve 0-10: handles references and edit invariants when
  relevant; award full credit when correctly unnecessary;
- scope_proportionality 0-15: gives the requested artifact without needless
  schemas, files, gates, or methodology. For the traceable-project case, reward
  only the governance actually required by that request;
- clarity_usefulness 0-10: direct, legible, decision-ready.

Set traceability_integrity=true unless the response fabricates an artifact,
provider execution, inspection, approval, delivery, or other claimed event. For
the traceable-project case it also requires preserving the necessary causal
gates without turning them into fake completed evidence.

CASE ID: {case['id']}
EXPECTED DEPTH: {case['expected_mode']}

USER REQUEST
{case['prompt']}

{outputs}
"""


def route_prompt(case: dict[str, Any]) -> str:
    return f"""Decide whether the available skill named creative-craft should be
loaded to complete the user request. Base the decision on the installed skill
description and the request's primary deliverable. Do not complete the request.
Do not select the skill merely because the request mentions marketing or visual
work; honor explicit exclusions and prefer the better neighboring domain. Return
only the JSON object required by the supplied schema.

CASE ID: {case['id']}
USER REQUEST: {case['prompt']}
"""


def ensure_output_run_dir(path: Path) -> Path:
    resolved_root = OUTPUT_ROOT.resolve()
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise EvalError(f"run directory must stay under {OUTPUT_ROOT}") from error
    if resolved.is_symlink():
        raise EvalError(f"run directory cannot be a symlink: {path}")
    return resolved


def create_run_dir(explicit: Path | None, candidate_digest: str) -> Path:
    if explicit is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = OUTPUT_ROOT / f"{stamp}-{candidate_digest[:12]}"
    else:
        run_dir = explicit
    run_dir = ensure_output_run_dir(run_dir)
    if run_dir.exists() and any(run_dir.iterdir()):
        raise EvalError(f"run directory is not empty: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def open_run_dir(path: Path) -> Path:
    run_dir = ensure_output_run_dir(path)
    if not (run_dir / "manifest.json").is_file():
        raise EvalError(f"run manifest not found: {run_dir}")
    return run_dir


def load_manifest(run_dir: Path) -> dict[str, Any]:
    manifest = read_json(run_dir / "manifest.json")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise EvalError("unsupported or invalid run manifest")
    return manifest


def save_manifest(run_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now()
    write_json(run_dir / "manifest.json", manifest)


def check_call_budget(manifest: dict[str, Any], planned: int, maximum: int) -> None:
    used = len(manifest.get("calls", []))
    if used + planned > maximum:
        raise EvalError(
            f"model-call budget exceeded: used={used}, planned={planned}, max={maximum}"
        )


def verify_recorded_runtime(
    manifest: dict[str, Any], *, model: str, reasoning: str
) -> None:
    if model != manifest.get("model") or reasoning != manifest.get("reasoning"):
        raise EvalError(
            "model and reasoning must match the output run: "
            f"{manifest.get('model')} / {manifest.get('reasoning')}"
        )


def verify_candidate_unchanged(manifest: dict[str, Any]) -> None:
    actual = skill_digest(SKILL_ROOT)
    if actual != manifest.get("candidate_skill_sha256"):
        raise EvalError(
            "candidate Skill changed after output generation; start a new bound run"
        )


def record_call(
    run_dir: Path,
    manifest: dict[str, Any],
    *,
    kind: str,
    case_id: str,
    variant: str | None,
    model: str,
    reasoning: str,
    has_schema: bool,
    has_skill: bool,
    result: dict[str, Any] | None,
    status: str,
) -> None:
    call = {
        "number": len(manifest.get("calls", [])) + 1,
        "kind": kind,
        "case_id": case_id,
        "variant": variant,
        "status": status,
        "elapsed_seconds": None if result is None else result["elapsed_seconds"],
        "command": public_command_receipt(
            kind=kind,
            model=model,
            reasoning=reasoning,
            has_schema=has_schema,
            has_skill=has_skill,
        ),
    }
    if result is not None and "skill_source_contract" in result:
        call["skill_source_contract"] = result["skill_source_contract"]
    manifest.setdefault("calls", []).append(call)
    save_manifest(run_dir, manifest)


def verify_quality_source_contracts(manifest: dict[str, Any]) -> None:
    """Fail closed before spending more calls on contaminated quality evidence."""
    if manifest.get("skill_source_contract_version") != SKILL_SOURCE_CONTRACT_VERSION:
        raise EvalError("quality evidence has no supported Skill source contract")
    expected_digests = {
        "baseline": None,
        "current": manifest.get("current_skill_sha256"),
        "candidate": manifest.get("candidate_skill_sha256"),
    }
    if not all(
        isinstance(expected_digests[variant], str)
        for variant in ("current", "candidate")
    ):
        raise EvalError("quality evidence is missing a bound Skill digest")

    indexed: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for call in manifest.get("calls", []):
        if call.get("kind") != "quality" or call.get("status") != "passed":
            continue
        key = (call.get("case_id"), call.get("variant"))
        indexed.setdefault(key, []).append(call)

    for case_id in manifest.get("quality_case_ids", []):
        for variant in VARIANTS:
            matches = indexed.get((case_id, variant), [])
            if len(matches) != 1:
                raise EvalError(
                    f"quality evidence has no unique passed call for {case_id}/{variant}"
                )
            contract = matches[0].get("skill_source_contract")
            if not isinstance(contract, dict) or contract.get("status") != "passed":
                raise EvalError(
                    f"quality evidence has no passed Skill source contract for "
                    f"{case_id}/{variant}"
                )
            if contract.get("version") != SKILL_SOURCE_CONTRACT_VERSION:
                raise EvalError(
                    f"quality evidence has an unsupported Skill source contract for "
                    f"{case_id}/{variant}"
                )
            expected_requirement = "forbidden" if variant == "baseline" else "required"
            if contract.get("requirement") != expected_requirement:
                raise EvalError(
                    f"quality evidence has the wrong Skill source requirement for "
                    f"{case_id}/{variant}"
                )
            expected_digest = expected_digests[variant]
            if contract.get("expected_sha256") != expected_digest:
                raise EvalError(
                    f"quality evidence has the wrong Skill digest for {case_id}/{variant}"
                )
            if contract.get("installed_sha256") != expected_digest:
                raise EvalError(
                    f"quality evidence did not install the bound Skill for "
                    f"{case_id}/{variant}"
                )
            observed = contract.get("observed_entrypoint_count")
            if variant == "baseline" and observed != 0:
                raise EvalError(f"baseline Skill source contract failed for {case_id}")
            if variant != "baseline" and not isinstance(observed, int):
                raise EvalError(
                    f"quality evidence has no Skill read count for {case_id}/{variant}"
                )
            if variant != "baseline" and observed < 1:
                raise EvalError(
                    f"isolated Skill was not read for {case_id}/{variant}"
                )


def run_quality(args: argparse.Namespace) -> int:
    validate_config_files()
    auth_file = args.auth_file.expanduser()
    validate_auth_path(auth_file)
    provider_transport = load_provider_transport(args.provider_config.expanduser())
    cases = selected_cases(load_cases(), args.case)
    planned_calls = len(cases) * len(VARIANTS)
    if planned_calls > args.max_total_calls:
        raise EvalError(
            f"requested run needs {planned_calls} calls, above max {args.max_total_calls}"
        )

    candidate_digest = skill_digest(SKILL_ROOT)
    run_dir = create_run_dir(args.run_dir, candidate_digest)
    revision = git_value("rev-parse", args.revision)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "model": args.model,
        "reasoning": args.reasoning,
        "timeout_seconds": args.timeout,
        "codex_version": codex_version(args.codex_bin),
        "provider_id": (
            "default" if provider_transport is None else provider_transport["id"]
        ),
        "provider_transport": (
            "codex_default"
            if provider_transport is None
            else "allowlisted_from_user_config"
        ),
        "git_head": git_value("rev-parse", "HEAD"),
        "current_revision": revision,
        "candidate_skill_sha256": candidate_digest,
        "skill_source_contract_version": SKILL_SOURCE_CONTRACT_VERSION,
        "variants": list(VARIANTS),
        "quality_case_ids": [case["id"] for case in cases],
        "routing_case_ids": [],
        "calls": [],
    }
    save_manifest(run_dir, manifest)

    try:
        with tempfile.TemporaryDirectory(prefix="creative-craft-head-snapshot-") as directory:
            current_skill = Path(directory) / "creative-craft"
            export_git_skill(revision, current_skill)
            current_digest = skill_digest(current_skill)
            manifest["current_skill_sha256"] = current_digest
            save_manifest(run_dir, manifest)
            skill_sources = {
                "baseline": None,
                "current": current_skill,
                "candidate": SKILL_ROOT,
            }
            skill_digests = {
                "baseline": None,
                "current": current_digest,
                "candidate": candidate_digest,
            }
            for case in cases:
                for variant in VARIANTS:
                    result: dict[str, Any] | None = None
                    try:
                        result = run_codex(
                            prompt=quality_prompt(case["prompt"]),
                            skill_source=skill_sources[variant],
                            output_file=run_dir / "outputs" / case["id"] / f"{variant}.md",
                            events_file=run_dir / "events" / f"quality-{case['id']}-{variant}.jsonl",
                            stderr_file=run_dir / "events" / f"quality-{case['id']}-{variant}.stderr",
                            output_schema=None,
                            auth_file=auth_file,
                            codex_bin=args.codex_bin,
                            model=args.model,
                            reasoning=args.reasoning,
                            timeout_seconds=args.timeout,
                            provider_transport=provider_transport,
                            expected_skill_digest=skill_digests[variant],
                        )
                    except Exception:
                        record_call(
                            run_dir,
                            manifest,
                            kind="quality",
                            case_id=case["id"],
                            variant=variant,
                            model=args.model,
                            reasoning=args.reasoning,
                            has_schema=False,
                            has_skill=variant != "baseline",
                            result=result,
                            status="failed",
                        )
                        raise
                    record_call(
                        run_dir,
                        manifest,
                        kind="quality",
                        case_id=case["id"],
                        variant=variant,
                        model=args.model,
                        reasoning=args.reasoning,
                        has_schema=False,
                        has_skill=variant != "baseline",
                        result=result,
                        status="passed",
                    )
    except Exception:
        manifest["status"] = "run_failed"
        save_manifest(run_dir, manifest)
        raise

    try:
        verify_quality_source_contracts(manifest)
    except Exception:
        manifest["status"] = "run_failed"
        save_manifest(run_dir, manifest)
        raise
    manifest["status"] = "outputs_complete"
    save_manifest(run_dir, manifest)
    print(run_dir.relative_to(ROOT))
    return 0


def validate_judgment(payload: Any, case_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("case_id") != case_id:
        raise EvalError(f"judge returned wrong case id for {case_id}")
    scores = payload.get("scores")
    if not isinstance(scores, list) or len(scores) != 3:
        raise EvalError(f"judge returned invalid scores for {case_id}")
    labels: set[str] = set()
    for score in scores:
        if not isinstance(score, dict) or score.get("label") not in {"A", "B", "C"}:
            raise EvalError(f"judge returned invalid label for {case_id}")
        labels.add(score["label"])
        total = 0
        for field, limit in SCORE_LIMITS.items():
            value = score.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= limit:
                raise EvalError(f"judge returned invalid {field} for {case_id}")
            total += value
        if not isinstance(score.get("traceability_integrity"), bool):
            raise EvalError(f"judge omitted traceability_integrity for {case_id}")
        score["total"] = total
    if labels != {"A", "B", "C"}:
        raise EvalError(f"judge returned duplicate labels for {case_id}")
    return payload


def blind_label_map(case_id: str, candidate_digest: str) -> dict[str, str]:
    variants = list(VARIANTS)
    seed = int.from_bytes(
        hashlib.sha256(f"{case_id}:{candidate_digest}".encode()).digest()[:8],
        "big",
    )
    random.Random(seed).shuffle(variants)
    return dict(zip(("A", "B", "C"), variants, strict=True))


def run_judges(args: argparse.Namespace) -> int:
    run_dir = open_run_dir(args.run_dir)
    manifest = load_manifest(run_dir)
    verify_recorded_runtime(manifest, model=args.model, reasoning=args.reasoning)
    verify_quality_source_contracts(manifest)
    provider_transport = load_provider_transport(args.provider_config.expanduser())
    provider_id = "default" if provider_transport is None else provider_transport["id"]
    if provider_id != manifest.get("provider_id"):
        raise EvalError("model provider changed after output generation")
    requested_ids = args.case or manifest.get("quality_case_ids")
    cases = selected_cases(load_cases(), requested_ids)
    check_call_budget(manifest, len(cases), args.max_total_calls)
    auth_file = args.auth_file.expanduser()
    judge_index: dict[str, Any] = {"schema_version": 1, "cases": {}}

    for case in cases:
        label_map = blind_label_map(case["id"], manifest["candidate_skill_sha256"])
        labeled_outputs: dict[str, str] = {}
        for label, variant in label_map.items():
            output = run_dir / "outputs" / case["id"] / f"{variant}.md"
            if not output.is_file():
                raise EvalError(f"quality output is missing: {output.relative_to(ROOT)}")
            labeled_outputs[label] = output.read_text(encoding="utf-8")
        output_file = run_dir / "judgments" / f"{case['id']}.json"
        result: dict[str, Any] | None = None
        try:
            result = run_codex(
                prompt=judge_prompt(case, labeled_outputs),
                skill_source=None,
                output_file=output_file,
                events_file=run_dir / "events" / f"judge-{case['id']}.jsonl",
                stderr_file=run_dir / "events" / f"judge-{case['id']}.stderr",
                output_schema=EVAL_CONFIG / "judge.schema.json",
                auth_file=auth_file,
                codex_bin=args.codex_bin,
                model=args.model,
                reasoning=args.reasoning,
                timeout_seconds=args.timeout,
                provider_transport=provider_transport,
            )
            judgment = validate_judgment(read_json(output_file), case["id"])
        except Exception:
            record_call(
                run_dir,
                manifest,
                kind="judge",
                case_id=case["id"],
                variant=None,
                model=args.model,
                reasoning=args.reasoning,
                has_schema=True,
                has_skill=False,
                result=result,
                status="failed",
            )
            raise
        record_call(
            run_dir,
            manifest,
            kind="judge",
            case_id=case["id"],
            variant=None,
            model=args.model,
            reasoning=args.reasoning,
            has_schema=True,
            has_skill=False,
            result=result,
            status="passed",
        )
        judge_index["cases"][case["id"]] = {
            "label_map": label_map,
            "scores": judgment["scores"],
            "summary": judgment["summary"],
        }
        write_json(run_dir / "judgments" / "index.json", judge_index)

    manifest["status"] = "judgments_complete"
    save_manifest(run_dir, manifest)
    print((run_dir / "judgments" / "index.json").relative_to(ROOT))
    return 0


def validate_route_result(payload: Any, case_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("case_id") != case_id:
        raise EvalError(f"route judge returned wrong case id for {case_id}")
    if not isinstance(payload.get("should_use_creative_craft"), bool):
        raise EvalError(f"route judge returned no boolean for {case_id}")
    if not isinstance(payload.get("reason"), str):
        raise EvalError(f"route judge returned no reason for {case_id}")
    return payload


def run_routes(args: argparse.Namespace) -> int:
    run_dir = open_run_dir(args.run_dir)
    manifest = load_manifest(run_dir)
    verify_recorded_runtime(manifest, model=args.model, reasoning=args.reasoning)
    verify_quality_source_contracts(manifest)
    verify_candidate_unchanged(manifest)
    provider_transport = load_provider_transport(args.provider_config.expanduser())
    provider_id = "default" if provider_transport is None else provider_transport["id"]
    if provider_id != manifest.get("provider_id"):
        raise EvalError("model provider changed after output generation")
    cases = selected_cases(load_routing_cases(), args.case)
    check_call_budget(manifest, len(cases), args.max_total_calls)
    auth_file = args.auth_file.expanduser()
    route_index: dict[str, Any] = {"schema_version": 1, "cases": {}}

    for case in cases:
        output_file = run_dir / "routing" / f"{case['id']}.json"
        result: dict[str, Any] | None = None
        try:
            result = run_codex(
                prompt=route_prompt(case),
                skill_source=SKILL_ROOT,
                output_file=output_file,
                events_file=run_dir / "events" / f"route-{case['id']}.jsonl",
                stderr_file=run_dir / "events" / f"route-{case['id']}.stderr",
                output_schema=EVAL_CONFIG / "route.schema.json",
                auth_file=auth_file,
                codex_bin=args.codex_bin,
                model=args.model,
                reasoning=args.reasoning,
                timeout_seconds=args.timeout,
                provider_transport=provider_transport,
                expected_skill_digest=manifest["candidate_skill_sha256"],
                skill_read_requirement="optional",
            )
            route_result = validate_route_result(read_json(output_file), case["id"])
        except Exception:
            record_call(
                run_dir,
                manifest,
                kind="route",
                case_id=case["id"],
                variant="candidate",
                model=args.model,
                reasoning=args.reasoning,
                has_schema=True,
                has_skill=True,
                result=result,
                status="failed",
            )
            raise
        record_call(
            run_dir,
            manifest,
            kind="route",
            case_id=case["id"],
            variant="candidate",
            model=args.model,
            reasoning=args.reasoning,
            has_schema=True,
            has_skill=True,
            result=result,
            status="passed",
        )
        actual = route_result["should_use_creative_craft"]
        route_index["cases"][case["id"]] = {
            "expected": case["expect_creative_craft"],
            "actual": actual,
            "passed": actual == case["expect_creative_craft"],
            "reason": route_result["reason"],
        }
        write_json(run_dir / "routing" / "index.json", route_index)

    manifest["routing_case_ids"] = [case["id"] for case in cases]
    manifest["status"] = "routing_complete"
    save_manifest(run_dir, manifest)
    print((run_dir / "routing" / "index.json").relative_to(ROOT))
    return 0


def scores_by_variant(case_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    label_map = case_result["label_map"]
    return {label_map[score["label"]]: score for score in case_result["scores"]}


def load_route_index(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "routing" / "index.json"
    if not path.is_file():
        return {"schema_version": 1, "cases": {}}
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise EvalError("unsupported or invalid routing index")
    return payload


def compute_report(
    quality_cases: list[dict[str, Any]],
    judge_index: dict[str, Any],
    route_index: dict[str, Any],
) -> dict[str, Any]:
    per_case: dict[str, Any] = {}
    aggregates = {
        variant: {field: 0 for field in (*SCORE_FIELDS, "total")}
        for variant in VARIANTS
    }
    candidate_beats_baseline = 0
    candidate_clear_losses = 0
    candidate_not_lower_current = 0
    evidence_honesty_no_regression = True
    quick_candidate_scope = 0
    quick_current_scope = 0
    quick_count = 0
    traceable_integrity = True
    traceable_count = 0

    indexed = judge_index.get("cases", {})
    for case in quality_cases:
        case_id = case["id"]
        if case_id not in indexed:
            raise EvalError(f"missing judgment for {case_id}")
        variant_scores = scores_by_variant(indexed[case_id])
        for variant in VARIANTS:
            score = variant_scores[variant]
            for field in SCORE_FIELDS:
                aggregates[variant][field] += score[field]
            aggregates[variant]["total"] += score["total"]
        candidate = variant_scores["candidate"]
        baseline = variant_scores["baseline"]
        current = variant_scores["current"]
        if candidate["total"] > baseline["total"]:
            candidate_beats_baseline += 1
        if candidate["total"] <= baseline["total"] - 5:
            candidate_clear_losses += 1
        if candidate["total"] >= current["total"]:
            candidate_not_lower_current += 1
        if candidate["evidence_honesty"] < current["evidence_honesty"]:
            evidence_honesty_no_regression = False
        if case["expected_mode"] == "quick":
            quick_count += 1
            quick_candidate_scope += candidate["scope_proportionality"]
            quick_current_scope += current["scope_proportionality"]
        else:
            traceable_count += 1
            traceable_integrity = traceable_integrity and candidate[
                "traceability_integrity"
            ]
        per_case[case_id] = {
            "expected_mode": case["expected_mode"],
            "scores": variant_scores,
            "summary": indexed[case_id]["summary"],
        }

    quality_ids = {case["id"] for case in quality_cases}
    full_quality_ids = {case["id"] for case in load_cases()}
    quality_suite_complete = quality_ids == full_quality_ids
    routing_cases = route_index.get("cases", {})
    full_routing_ids = {case["id"] for case in load_routing_cases()}
    routing_suite_complete = set(routing_cases) == full_routing_ids
    routing_all_correct = routing_suite_complete and all(
        result.get("passed") is True for result in routing_cases.values()
    )
    beats_baseline_minimum = math.ceil(len(quality_cases) * 5 / 7)
    not_lower_current_minimum = math.ceil(len(quality_cases) * 4 / 7)
    checks = {
        "quality_suite_complete": quality_suite_complete,
        "candidate_beats_baseline_threshold": (
            candidate_beats_baseline >= beats_baseline_minimum
        ),
        "candidate_clear_losses_at_most_1": candidate_clear_losses <= 1,
        "candidate_aggregate_not_below_current": (
            aggregates["candidate"]["total"] >= aggregates["current"]["total"]
        ),
        "candidate_not_lower_current_threshold": (
            candidate_not_lower_current >= not_lower_current_minimum
        ),
        "quick_scope_proportionality_improves": (
            quick_count > 0 and quick_candidate_scope > quick_current_scope
        ),
        "no_evidence_honesty_regression": evidence_honesty_no_regression,
        "traceable_case_retains_gates": (
            traceable_count > 0 and traceable_integrity
        ),
        "routing_suite_complete": routing_suite_complete,
        "routing_all_correct": routing_all_correct,
    }
    return {
        "schema_version": 1,
        "status": "PASS" if all(checks.values()) else "PARTIAL",
        "acceptance_checks": checks,
        "counts": {
            "quality_cases": len(quality_cases),
            "candidate_beats_baseline": candidate_beats_baseline,
            "candidate_clear_losses": candidate_clear_losses,
            "candidate_not_lower_current": candidate_not_lower_current,
            "candidate_beats_baseline_minimum": beats_baseline_minimum,
            "candidate_not_lower_current_minimum": not_lower_current_minimum,
            "routing_cases": len(routing_cases),
            "routing_passed": sum(
                result.get("passed") is True for result in routing_cases.values()
            ),
        },
        "aggregates": aggregates,
        "per_case": per_case,
        "routing": routing_cases,
        "limitations": [
            "Text-only Codex evaluation; no image or video provider was called.",
            "A blind model judge is comparative evidence, not human creative approval.",
            "Each variant has one generated sample and one blind judgment per case; repeated runs may vary.",
            "Codex calls isolate CODEX_HOME and user-level discovery roots, then verify Skill reads from event evidence.",
            "A subset run or a run without the complete routing suite is reported as PARTIAL.",
            "Results apply only to the recorded model, reasoning level, prompts, and source hashes.",
        ],
    }


def render_report(report: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        "# Creative Craft Agent Quality Evaluation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"- Model: `{manifest['model']}`",
        f"- Reasoning: `{manifest['reasoning']}`",
        f"- Codex: `{manifest['codex_version']}`",
        f"- Comparison revision: `{manifest['current_revision']}`",
        f"- Candidate skill SHA-256: `{manifest['candidate_skill_sha256']}`",
        f"- Model calls: `{len(manifest.get('calls', []))}`",
        "",
        "## Aggregate scores",
        "",
        "| Variant | Total | Strategic | Distinct | Execution | Evidence | Ref/change | Scope | Clarity |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    display_variants = {
        "baseline": "no Skill",
        "current": "comparison",
        "candidate": "candidate",
    }
    for variant in VARIANTS:
        score = report["aggregates"][variant]
        lines.append(
            f"| {display_variants[variant]} | {score['total']} | "
            f"{score['strategic_fit']} | "
            f"{score['distinctiveness']} | {score['execution_readiness']} | "
            f"{score['evidence_honesty']} | {score['reference_change_preserve']} | "
            f"{score['scope_proportionality']} | {score['clarity_usefulness']} |"
        )
    lines.extend(["", "## Acceptance", ""])
    for name, passed in report["acceptance_checks"].items():
        lines.append(f"- [{'x' if passed else ' '}] `{name}`")
    lines.extend(
        [
            "",
            "## Per-case totals",
            "",
            "| Case | No Skill | Comparison | Candidate |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for case_id, case in report["per_case"].items():
        scores = case["scores"]
        lines.append(
            f"| {case_id} | {scores['baseline']['total']} | "
            f"{scores['current']['total']} | {scores['candidate']['total']} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
    return "\n".join(lines) + "\n"


def write_report(args: argparse.Namespace) -> int:
    run_dir = open_run_dir(args.run_dir)
    manifest = load_manifest(run_dir)
    verify_quality_source_contracts(manifest)
    quality_cases = [
        case for case in load_cases() if case["id"] in manifest["quality_case_ids"]
    ]
    judge_index = read_json(run_dir / "judgments" / "index.json")
    route_index = load_route_index(run_dir)
    report = compute_report(quality_cases, judge_index, route_index)
    report["generated_at"] = utc_now()
    write_json(run_dir / "report.json", report)
    (run_dir / "report.md").write_text(
        render_report(report, manifest), encoding="utf-8"
    )
    manifest["status"] = "complete"
    manifest["result"] = report["status"]
    save_manifest(run_dir, manifest)
    print(json.dumps({"run_dir": str(run_dir.relative_to(ROOT)), "status": report["status"]}))
    return 0


def run_check(args: argparse.Namespace) -> int:
    validate_config_files()
    validate_auth_path(args.auth_file.expanduser())
    provider_transport = load_provider_transport(args.provider_config.expanduser())
    details = {
        "valid": True,
        "codex_version": codex_version(args.codex_bin),
        "provider_id": (
            "default" if provider_transport is None else provider_transport["id"]
        ),
        "provider_transport": (
            "codex_default"
            if provider_transport is None
            else "allowlisted_from_user_config"
        ),
        "quality_cases": len(load_cases()),
        "routing_cases": len(load_routing_cases()),
        "candidate_skill_sha256": skill_digest(SKILL_ROOT),
        "auth": "exists_not_read",
        "output_root": str(OUTPUT_ROOT.relative_to(ROOT)),
    }
    if args.json:
        print(json.dumps(details, indent=2))
    else:
        print(
            "Agent quality eval ready: "
            f"{details['quality_cases']} quality cases, "
            f"{details['routing_cases']} routing cases, {details['codex_version']}"
        )
    return 0


def add_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning", default="high")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument(
        "--auth-file", type=Path, default=Path.home() / ".codex" / "auth.json"
    )
    parser.add_argument(
        "--provider-config",
        type=Path,
        default=Path.home() / ".codex" / "config.toml",
        help="Read only allowlisted non-secret provider transport fields.",
    )
    parser.add_argument("--max-total-calls", type=int, default=40)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate Creative Craft's effect on isolated Codex outputs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Validate prerequisites without model calls.")
    add_runtime_arguments(check_parser)
    check_parser.add_argument("--json", action="store_true")
    check_parser.set_defaults(func=run_check)

    run_parser = subparsers.add_parser(
        "run", help="Generate no-Skill/comparison/candidate outputs."
    )
    add_runtime_arguments(run_parser)
    run_parser.add_argument("--run-dir", type=Path)
    run_parser.add_argument("--revision", default="HEAD")
    run_parser.add_argument("--case", action="append")
    run_parser.set_defaults(func=run_quality)

    judge_parser = subparsers.add_parser("judge", help="Blind-score generated outputs.")
    add_runtime_arguments(judge_parser)
    judge_parser.add_argument("--run-dir", type=Path, required=True)
    judge_parser.add_argument("--case", action="append")
    judge_parser.set_defaults(func=run_judges)

    route_parser = subparsers.add_parser("route", help="Evaluate description-level skill routing.")
    add_runtime_arguments(route_parser)
    route_parser.add_argument("--run-dir", type=Path, required=True)
    route_parser.add_argument("--case", action="append")
    route_parser.set_defaults(func=run_routes)

    report_parser = subparsers.add_parser("report", help="Compute acceptance from saved evidence.")
    report_parser.add_argument("--run-dir", type=Path, required=True)
    report_parser.set_defaults(func=write_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "timeout") and args.timeout <= 0:
        parser.error("--timeout must be positive")
    if hasattr(args, "max_total_calls") and args.max_total_calls <= 0:
        parser.error("--max-total-calls must be positive")
    try:
        return args.func(args)
    except (EvalError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
