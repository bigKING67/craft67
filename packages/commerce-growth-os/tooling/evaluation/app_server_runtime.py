"""Opt-in, isolated App Server execution with explicit Skill input evidence.

An accepted input is not a host attestation of the bytes injected into context.
No authentication files or mutable user configuration are copied into this runtime.
"""
from __future__ import annotations

import json
import hashlib
import os
import queue
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from live_runtime import (
    cleanup_on_sigterm, load_manifest, reap_process_tree, sha256_text,
    tree_evidence, validate_codex_config_overrides, validate_real_directory,
)


class ProtocolError(ValueError):
    pass


def run_app_server(
    instruction: str, *, skill_name: str, model: str, timeout: float,
    reasoning_effort: str = "medium", config_overrides: list[str] | None = None,
    command: list[str] | None = None,
) -> dict[str, Any]:
    if os.name != "posix":
        raise ValueError("App Server backend currently requires POSIX process-group cleanup")
    if not model or timeout <= 0:
        raise ValueError("App Server requires an explicit model and positive timeout")
    manifest = load_manifest()
    if skill_name not in {skill["name"] for skill in manifest["skills"]}:
        raise ValueError("unknown explicit Skill")
    root = validate_real_directory(Path(manifest["default_install_root"]).expanduser())
    skill_root = root / skill_name
    before = tree_evidence(skill_root)
    skill_path = skill_root / "SKILL.md"
    skill_digest = hashlib.sha256(skill_path.read_bytes()).hexdigest()
    overrides = validate_codex_config_overrides(config_overrides)
    argv = list(command) if command is not None else ["codex", "app-server", "--stdio"]
    for override in overrides:
        argv.extend(["-c", override])
    started = time.monotonic()
    deadline = started + timeout
    receipt: dict[str, Any] = {
        "schema_version": 1, "backend": "app-server",
        "skill_name": skill_name, "skill_path": str(skill_path),
        "skill_sha256": skill_digest, "bundle_tree_sha256": before["tree_sha256"],
        "instruction_sha256": sha256_text(instruction),
        "input_accepted": False, "turn_completed": False,
        "requested_reasoning_effort": reasoning_effort,
        "runtime_skill_loading_verified": False,
        "loading_evidence_status": "INPUT_CONTRACT_ONLY",
    }
    result: dict[str, Any] = {"ok": False, "model": None, "skill_input_receipt": receipt}
    with tempfile.TemporaryDirectory(prefix="commerce-app-server-") as temp:
        base = Path(temp).resolve()
        workspace, home = base / "workspace", base / "codex-home"
        workspace.mkdir(mode=0o700)
        home.mkdir(mode=0o700)
        api_key = os.environ.get("CODEX_API_KEY") or os.environ.get("OPENAI_API_KEY")
        env = os.environ.copy()
        env.pop("CODEX_API_KEY", None)
        env.pop("OPENAI_API_KEY", None)
        env["CODEX_HOME"] = str(home)
        options = {"start_new_session": True} if os.name == "posix" else {
            "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP,
        }
        with cleanup_on_sigterm(), subprocess.Popen(
            argv, cwd=workspace, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            encoding="utf-8", **options,
        ) as process:
            incoming: queue.Queue = queue.Queue(maxsize=128)
            stopping = threading.Event()

            def reader() -> None:
                try:
                    while not stopping.is_set():
                        line = process.stdout.readline(1024 * 1024 + 1)
                        if not line:
                            message = None
                        elif len(line) > 1024 * 1024:
                            message = ProtocolError("App Server event exceeds size limit")
                        else:
                            try:
                                message = json.loads(line)
                            except ValueError:
                                message = ProtocolError("invalid App Server JSON")
                        while not stopping.is_set():
                            try:
                                incoming.put(message, timeout=0.05)
                                break
                            except queue.Full:
                                pass
                        if message is None or isinstance(message, Exception):
                            return
                except (OSError, ValueError):
                    return

            thread = threading.Thread(target=reader, daemon=True)
            thread.start()

            def send(message: dict) -> None:
                payload = json.dumps(message, ensure_ascii=False) + "\n"
                if len(payload.encode("utf-8")) > 4096:
                    raise ProtocolError("App Server request exceeds bounded write size")
                process.stdin.write(payload)
                process.stdin.flush()

            pending: list[dict] = []

            def receive() -> dict:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("App Server total timeout")
                try:
                    message = incoming.get(timeout=remaining)
                except queue.Empty:
                    raise TimeoutError("App Server total timeout") from None
                if message is None:
                    raise ProtocolError("App Server closed before completion")
                if isinstance(message, Exception):
                    raise message
                if not isinstance(message, dict):
                    raise ProtocolError("App Server event must be an object")
                if "method" in message and "id" in message:
                    # Never approve tools, filesystem access, auth, or user input.
                    send({"id": message["id"], "error": {"code": -32601, "message": "interactive requests disabled"}})
                    raise ProtocolError("App Server requested interactive approval")
                return message

            def request(ident: int, method: str, params: dict) -> dict:
                send({"id": ident, "method": method, "params": params})
                while True:
                    message = receive()
                    if message.get("id") == ident:
                        if "error" in message or not isinstance(message.get("result"), dict):
                            raise ProtocolError(f"App Server rejected {method}")
                        return message["result"]
                    if "id" in message:
                        raise ProtocolError("unexpected App Server response id")
                    pending.append(message)
                    if len(pending) > 128:
                        raise ProtocolError("too many notifications before response")

            try:
                request(1, "initialize", {"clientInfo": {"name": "commerce-eval", "version": "1"}})
                send({"method": "initialized", "params": {}})
                if api_key:
                    request(2, "account/login/start", {"type": "apiKey", "apiKey": api_key})
                    receipt["authentication"] = "api-key-login-accepted"
                created = request(3, "thread/start", {
                    "model": model, "cwd": str(workspace), "ephemeral": True,
                    "sandbox": "read-only", "approvalPolicy": "never",
                    "config": {"model_reasoning_effort": reasoning_effort},
                })
                thread_id = created.get("thread", {}).get("id")
                if not isinstance(thread_id, str) or not thread_id:
                    raise ProtocolError("missing thread id")
                if (created.get("approvalPolicy") != "never"
                    or created.get("sandbox", {}).get("type") != "readOnly"
                    or Path(created.get("cwd", "")) != workspace):
                    raise ProtocolError("App Server did not confirm requested isolation")
                if created.get("model") != model:
                    raise ProtocolError("App Server changed the requested model")
                receipt["observed_reasoning_effort"] = created.get("reasoningEffort")
                if created.get("reasoningEffort") not in (None, reasoning_effort):
                    raise ProtocolError("App Server changed requested reasoning effort")
                result["model"] = created.get("model")
                receipt["thread_id"] = thread_id
                accepted = request(4, "turn/start", {
                    "threadId": thread_id, "effort": reasoning_effort,
                    "input": [{"type": "text", "text": instruction},
                              {"type": "skill", "name": skill_name, "path": str(skill_path)}],
                })
                turn_id = accepted.get("turn", {}).get("id")
                if not isinstance(turn_id, str) or not turn_id:
                    raise ProtocolError("missing turn id")
                receipt.update(input_accepted=True, turn_id=turn_id)
                answers: dict[str, str] = {}
                while True:
                    message = pending.pop(0) if pending else receive()
                    method, params = message.get("method"), message.get("params", {})
                    if not isinstance(params, dict) or params.get("threadId") != thread_id:
                        continue
                    if method == "item/completed" and params.get("turnId") == turn_id:
                        item = params.get("item", {})
                        if item.get("type") == "agentMessage" and isinstance(item.get("text"), str):
                            if item.get("phase") in (None, "final_answer"):
                                answers[str(item.get("id"))] = item["text"]
                    if method == "turn/completed" and params.get("turn", {}).get("id") == turn_id:
                        turn = params["turn"]
                        if turn.get("status") != "completed" or turn.get("error") is not None:
                            raise ProtocolError("App Server turn did not complete successfully")
                        receipt["turn_completed"] = True
                        break
                if tree_evidence(skill_root) != before:
                    raise ProtocolError("Skill bundle changed during execution")
                receipt["bundle_unchanged"] = True
                answer = "\n\n".join(answers.values()).strip()
                if not answer:
                    raise ProtocolError("App Server returned no final answer")
                result.update(ok=True, answer=answer, answer_sha256=sha256_text(answer))
            except (OSError, ValueError, TimeoutError, TypeError, AttributeError) as exc:
                # Protocol errors are authored here; never persist host payloads.
                result["error"] = str(exc) if isinstance(exc, (ProtocolError, TimeoutError)) else "App Server transport failed"
            finally:
                stopping.set()
                reap_process_tree(process, drain=False)
                thread.join(timeout=2)
                if thread.is_alive():
                    raise RuntimeError("App Server event reader did not stop")
    result["duration_seconds"] = round(time.monotonic() - started, 3)
    return result
