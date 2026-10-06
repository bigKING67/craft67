"""Shared fail-closed runtime and installation evidence for live evaluations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "skill-pack.json"
VERIFY_INSTALL = ROOT / "tooling/installation/verify_install.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.manifest import load_manifest as load_manifest_file
from tooling.installation.tree_integrity import (
    TreeIntegrityError,
    is_runtime_cache,
    lexical_absolute,
    validate_real_directory,
    validate_tree,
)

CommandExecutor = Callable[..., subprocess.CompletedProcess[str]]
CASE_ID_PATTERN = re.compile(r"\A[a-z0-9]+(?:_[a-z0-9]+)*\Z")
PROVIDER_ID_PATTERN = re.compile(r"\A[a-zA-Z0-9_-]+\Z")
PROVIDER_OVERRIDE_PATTERN = re.compile(
    r"\Amodel_providers\.([a-zA-Z0-9_-]+)\."
    r"(name|base_url|wire_api|requires_openai_auth|supports_websockets)\Z"
)


def load_manifest() -> dict[str, Any]:
    return load_manifest_file(MANIFEST)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_case_id(value: object, *, label: str = "case id") -> str:
    if not isinstance(value, str) or not CASE_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must use lowercase snake_case: {value!r}")
    return value


def _quoted_config_string(value: str, *, field: str) -> str:
    if len(value) < 2 or value[0] not in {'"', "'"} or value[-1] != value[0]:
        raise ValueError(f"Codex config override {field} must use a quoted string value")
    decoded = value[1:-1]
    if not decoded or "\\" in decoded or value[0] in decoded:
        raise ValueError(f"Codex config override {field} has an unsafe string value")
    return decoded


def validate_codex_config_overrides(values: list[str] | None) -> list[str]:
    """Allow only non-secret model-provider transport settings for isolated live runs."""
    validated: list[str] = []
    seen_keys: set[str] = set()
    for override in values or []:
        if not isinstance(override, str) or "=" not in override:
            raise ValueError(f"invalid Codex config override: {override!r}")
        key, raw_value = (part.strip() for part in override.split("=", 1))
        if key in seen_keys:
            raise ValueError(f"Codex config override key is duplicated: {key}")
        seen_keys.add(key)
        if key == "model_provider":
            provider = _quoted_config_string(raw_value, field=key)
            if not PROVIDER_ID_PATTERN.fullmatch(provider):
                raise ValueError(f"invalid Codex model_provider id: {provider!r}")
        else:
            match = PROVIDER_OVERRIDE_PATTERN.fullmatch(key)
            if not match:
                raise ValueError(f"Codex config override is not allowlisted: {key}")
            field = match.group(2)
            if field in {"requires_openai_auth", "supports_websockets"}:
                if raw_value not in {"true", "false"}:
                    raise ValueError(f"Codex config override {key} must be true or false")
            else:
                value = _quoted_config_string(raw_value, field=key)
                if field == "base_url":
                    parsed = urlparse(value)
                    if (
                        parsed.scheme not in {"http", "https"}
                        or not parsed.hostname
                        or parsed.username
                        or parsed.password
                        or parsed.query
                        or parsed.fragment
                    ):
                        raise ValueError(f"Codex config override {key} has an unsafe base URL")
                elif field == "wire_api" and value != "responses":
                    raise ValueError("isolated live evaluation currently requires wire_api=responses")
                elif not PROVIDER_ID_PATTERN.fullmatch(value):
                    raise ValueError(f"Codex config override {key} has an unsafe value")
        validated.append(f"{key}={raw_value}")
    return validated


def ensure_private_directory(path: Path, *, require_empty: bool = False) -> Path:
    candidate = lexical_absolute(path)
    missing: list[Path] = []
    existing = candidate
    while not os.path.lexists(existing):
        missing.append(existing)
        parent = existing.parent
        if parent == existing:
            raise ValueError(f"evaluation directory has no existing ancestor: {candidate}")
        existing = parent
    try:
        normalized = validate_real_directory(existing)
    except TreeIntegrityError as exc:
        raise ValueError(f"evaluation directory must have a real ancestor: {candidate}: {exc}") from exc
    for component in reversed(missing):
        normalized /= component.name
        try:
            normalized.mkdir(mode=0o700)
        except FileExistsError:
            pass
        try:
            normalized = validate_real_directory(normalized)
        except TreeIntegrityError as exc:
            raise ValueError(f"evaluation directory must be a real directory: {candidate}: {exc}") from exc
    if require_empty and any(normalized.iterdir()):
        raise ValueError(f"evaluation directory must be empty: {normalized}")
    if os.name != "nt":
        normalized.chmod(0o700)
    return normalized


def create_private_run_directory(base: Path) -> tuple[str, Path]:
    root = ensure_private_directory(base)
    for _ in range(10):
        run_id = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ-") + secrets.token_hex(4)
        run = root / run_id
        try:
            run.mkdir(mode=0o700)
        except FileExistsError:
            continue
        return run_id, run
    raise ValueError(f"could not allocate a unique evaluation run under {root}")


def write_private_text(path: Path, content: str, *, overwrite: bool = True) -> None:
    target = lexical_absolute(path)
    try:
        parent = validate_real_directory(target.parent)
    except TreeIntegrityError as exc:
        raise ValueError(f"evaluation artifact parent must be a real directory: {target.parent}: {exc}") from exc
    target = parent / target.name
    if not overwrite and os.path.lexists(target):
        raise ValueError(f"evaluation artifact already exists: {target}")
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ValueError(f"evaluation artifact target is not a regular file: {target}")

    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=parent)
    temporary = Path(temporary_name)
    try:
        if os.name != "nt":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if not overwrite and os.path.lexists(target):
            raise ValueError(f"evaluation artifact appeared concurrently: {target}")
        os.replace(temporary, target)
        if os.name != "nt":
            target.chmod(0o600)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def tree_evidence(root: Path) -> dict[str, Any]:
    """Hash a regular-file tree without following symlinks."""
    try:
        files = validate_tree(root, require_directory=True)
    except TreeIntegrityError as exc:
        raise ValueError(f"bundle tree is invalid: {root}: {exc}") from exc
    entries: list[dict[str, str]] = []
    for path in files:
        relative = path.relative_to(root)
        if is_runtime_cache(relative):
            continue
        entries.append(
            {
                "path": relative.as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    encoded = json.dumps(entries, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return {
        "tree_sha256": sha256_text(encoded),
        "files": len(entries),
        "bytes": sum((root / item["path"]).stat().st_size for item in entries),
    }


def capture_discovery_roots(
    manifest: dict[str, Any],
    canonical_root: Path,
    skill_names: list[str],
) -> list[dict[str, Any]]:
    configured = [("canonical", canonical_root)]
    configured.extend(
        ("duplicate", lexical_absolute(Path(value).expanduser()))
        for value in manifest.get("duplicate_discovery_roots", [])
    )
    roots: list[dict[str, Any]] = []
    canonical_hashes: dict[str, str] = {}
    for kind, path in configured:
        if path.exists() or path.is_symlink():
            try:
                validate_real_directory(path)
            except TreeIntegrityError as exc:
                raise ValueError(f"discovery root must be a real directory: {path}: {exc}") from exc
        elif kind == "canonical":
            raise ValueError(f"canonical discovery root is not a directory: {path}")
        bundles: dict[str, dict[str, Any]] = {}
        for name in skill_names:
            bundle = path / name
            if bundle.exists() or bundle.is_symlink():
                bundles[name] = tree_evidence(bundle)
        if kind == "canonical":
            missing = sorted(set(skill_names) - set(bundles))
            if missing:
                raise ValueError(f"canonical discovery root is missing skills: {', '.join(missing)}")
            canonical_hashes = {name: item["tree_sha256"] for name, item in bundles.items()}
        else:
            conflicts = [
                name
                for name, item in bundles.items()
                if canonical_hashes.get(name) != item["tree_sha256"]
            ]
            if conflicts:
                raise ValueError(
                    f"duplicate discovery root has conflicting skills at {path}: {', '.join(conflicts)}"
                )
        roots.append(
            {
                "kind": kind,
                "path": str(path),
                "exists": path.is_dir(),
                "bundles": bundles,
            }
        )
    return roots


def verify_active_install(
    *,
    install_root: Path | None = None,
    skill_names: list[str] | None = None,
    run_verifier: bool = True,
    executor: CommandExecutor = subprocess.run,
) -> dict[str, Any]:
    """Verify current source parity, then capture the exact active discovery trees."""
    manifest = load_manifest()
    selected = skill_names or [skill["name"] for skill in manifest["skills"]]
    default_root = lexical_absolute(Path(manifest["default_install_root"]).expanduser())
    canonical_root = lexical_absolute(
        (install_root or Path(manifest["default_install_root"])).expanduser()
    )
    if canonical_root != default_root:
        raise ValueError(
            "live evaluation only supports the default discovery root "
            f"{default_root}; --install-root cannot override Codex runtime discovery"
        )
    verifier_output = "not run"
    if run_verifier:
        command = [sys.executable, str(VERIFY_INSTALL), "--install-root", str(canonical_root)]
        for name in selected:
            command.extend(["--skill", name])
        result = executor(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
        )
        verifier_output = "\n".join(
            part for part in (result.stdout.strip(), result.stderr.strip()) if part
        )
        if result.returncode != 0:
            raise ValueError(f"active installation parity failed: {verifier_output[-2000:]}")
    roots = capture_discovery_roots(manifest, canonical_root, selected)
    return {
        "parity_verified": run_verifier,
        "discovery_mode": "canonical-active-root-parity",
        "runtime_discovery_override": False,
        "runtime_skill_loading_verified": False,
        "verifier_output": verifier_output,
        "canonical_root": str(canonical_root),
        "selected_skills": selected,
        "discovery_roots": roots,
        "active_bundle_tree_sha256": {
            name: roots[0]["bundles"][name]["tree_sha256"] for name in selected
        },
    }


@contextmanager
def cleanup_on_sigterm():
    """Let the CLI's default SIGTERM unwind managed calls before exiting.

    Embedded callers retain their own handlers; Python only permits installing
    signal handlers from the main thread.
    """
    install = (
        threading.current_thread() is threading.main_thread()
        and signal.getsignal(signal.SIGTERM) == signal.SIG_DFL
    )
    if install:
        def terminate(signum, _frame):
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            raise SystemExit(128 + signum)
        previous = signal.signal(signal.SIGTERM, terminate)
    try:
        yield
    finally:
        if install:
            signal.signal(signal.SIGTERM, previous)


def reap_process_tree(process: subprocess.Popen, *, drain: bool = True) -> None:
    """Terminate this invocation and reap pipes, including surviving descendants."""
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=0.25) if drain else process.wait(timeout=0.25)
        except subprocess.TimeoutExpired:
            pass
        finally:
            # A child can ignore TERM after its parent closes the pipes.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    else:
        try:
            cleanup = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True, text=True, timeout=5,
            )
            if cleanup.returncode != 0:
                raise RuntimeError("live process-tree cleanup failed")
        finally:
            # Even if taskkill fails, do not leave __exit__ waiting for
            # the direct process indefinitely. Tree failure still raises.
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)
    try:
        process.communicate(timeout=2) if drain else process.wait(timeout=2)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("live process pipes remained open after cleanup") from exc


def run_managed_process(
    command: list[str],
    *,
    input: str,
    cwd: Path,
    capture_output: bool,
    text: bool,
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    """Run a live call and reap its process group on timeout or cancellation.

    Detached processes are outside this boundary. Windows uses taskkill for the
    captured process tree; POSIX uses a new session owned by this invocation.
    """
    if not capture_output or not text:
        raise ValueError("live calls require captured text output")
    options = {"start_new_session": True} if os.name == "posix" else {
        "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP,
    }
    with cleanup_on_sigterm(), subprocess.Popen(
        command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, **options,
    ) as process:
        try:
            stdout, stderr = process.communicate(input=input, timeout=timeout)
        except BaseException:
            reap_process_tree(process)
            raise
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def summarize_exec_events(stdout: str) -> dict[str, Any]:
    """Retain bounded protocol metadata, never message/tool payloads or loading claims."""
    counts = {name: 0 for name in (
        "thread.started", "turn.started", "turn.completed", "turn.failed",
        "item.started", "item.updated", "item.completed", "error",
    )}
    malformed = unknown = 0
    usage: dict[str, int] = {}
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            malformed += 1
            continue
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            malformed += 1
            continue
        event_type = event["type"]
        if event_type not in counts:
            unknown += 1
            continue
        counts[event_type] += 1
        if event_type == "turn.completed" and isinstance(event.get("usage"), dict):
            for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"):
                value = event["usage"].get(key)
                if type(value) is int and value >= 0:
                    usage[key] = usage.get(key, 0) + value
    return {
        "schema_version": 1,
        "source": "codex-exec-jsonl",
        "stdout_sha256": sha256_text(stdout),
        "event_counts": counts,
        "malformed_lines": malformed,
        "unknown_events": unknown,
        "usage": usage,
        "runtime_skill_loading_verified": False,
        "loading_evidence_status": "UNSUPPORTED_BY_CURRENT_ADAPTER",
    }


def run_ephemeral_codex(
    instruction: str,
    *,
    reasoning_effort: str,
    model: str | None,
    timeout: int,
    schema: Path | None = None,
    config_overrides: list[str] | None = None,
    executor: CommandExecutor = subprocess.run,
) -> dict[str, Any]:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    with tempfile.TemporaryDirectory(prefix="commerce-skill-live-eval-") as temp:
        workspace = Path(temp) / "workspace"
        workspace.mkdir()
        output = Path(temp) / "last-message.txt"
        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--json",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "-s",
            "read-only",
            "--color",
            "never",
            "-C",
            str(workspace),
        ]
        for override in validate_codex_config_overrides(config_overrides):
            command.extend(["-c", override])
        command.extend(["-c", f'model_reasoning_effort="{reasoning_effort}"'])
        if schema is not None:
            command.extend(["--output-schema", str(schema)])
        command.extend(["-o", str(output)])
        if model:
            command.extend(["-m", model])
        command.append("-")
        started = time.monotonic()
        try:
            result = (run_managed_process if executor is subprocess.run else executor)(
                command,
                cwd=workspace,
                input=instruction,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "duration_seconds": round(time.monotonic() - started, 3),
                "model": None,
                "error": f"codex timed out after {timeout} seconds",
            }
        duration = round(time.monotonic() - started, 3)
        event_summary = summarize_exec_events(result.stdout)
        event_summary["instruction_sha256"] = sha256_text(instruction)
        runtime_log = result.stderr  # stdout is JSONL; model-authored payloads are not host headers.
        model_match = re.search(r"^model:\s*(.+)$", runtime_log, re.MULTILINE)
        if result.returncode != 0:
            return {
                "ok": False,
                "duration_seconds": duration,
                "execution_events": event_summary,
                "model": model_match.group(1).strip() if model_match else None,
                "error": f"codex exited {result.returncode}; see execution_events for protocol diagnostics",
            }
        try:
            answer = output.read_text(encoding="utf-8")
        except OSError as exc:
            return {
                "ok": False,
                "duration_seconds": duration,
                "execution_events": event_summary,
                "model": model_match.group(1).strip() if model_match else None,
                "error": f"missing last message: {exc}",
            }
    return {
        "ok": True,
        "duration_seconds": duration,
        "execution_events": event_summary,
        "model": model_match.group(1).strip() if model_match else None,
        "answer": answer,
        "answer_sha256": sha256_text(answer),
    }


def fake_codex_executor(answer: str, *, model: str = "fake-model") -> CommandExecutor:
    """Return a subprocess-compatible fake used only by deterministic self-tests."""
    def execute(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if command[:2] != ["codex", "exec"] or "--ephemeral" not in command:
            raise AssertionError(f"live eval lost ephemeral Codex isolation: {command}")
        if "--ignore-user-config" not in command or "--ignore-rules" not in command:
            raise AssertionError(f"live eval loaded mutable user configuration: {command}")
        if "--skip-git-repo-check" not in command:
            raise AssertionError("live eval neutral workspace must not depend on an enclosing Git repository")
        if "-s" not in command or command[command.index("-s") + 1] != "read-only":
            raise AssertionError(f"live eval lost read-only sandboxing: {command}")
        if command[-1] != "-":
            raise AssertionError("live-eval prompt must be supplied on stdin, not the process command line")
        prompt = kwargs.get("input")
        if not isinstance(prompt, str) or not prompt:
            raise AssertionError("live-eval prompt is missing from stdin")
        if any(prompt in argument for argument in command):
            raise AssertionError("live-eval prompt leaked into the process command line")
        workspace = Path(command[command.index("-C") + 1])
        if Path(kwargs.get("cwd", "")) != workspace or workspace == ROOT:
            raise AssertionError("live eval must run from an isolated neutral workspace")
        output = Path(command[command.index("-o") + 1])
        output.write_text(answer, encoding="utf-8")
        events = [
            {"type": "thread.started", "thread_id": "fake-thread"},
            {"type": "turn.started"},
            {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}},
        ]
        return subprocess.CompletedProcess(command, 0, "\n".join(json.dumps(e) for e in events), f"model: {model}\n")

    return execute
