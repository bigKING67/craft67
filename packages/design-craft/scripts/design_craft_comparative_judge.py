#!/usr/bin/env python3
"""Run an independent blind comparative judge in an empty read-only workspace."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from design_craft_comparative_common import (
    BLIND_LABELS,
    JUDGE_RUN_SCHEMA,
    load_scorecard,
    parse_json_output,
    sha256_bytes,
    sha256_file,
    validate_judgment,
    validate_judgment_schema,
)
from design_craft_evidence_common import command_version, publish_files, worktree_fingerprint


ROOT = Path(__file__).resolve().parents[1]
HOSTS = ("codex", "cursor", "claude")
EXECUTABLES = {"codex": "codex", "cursor": "cursor-agent", "claude": "claude"}


def command_for(
    host: str,
    *,
    model: str,
    reasoning: str,
    workspace: Path,
    schema_path: Path,
    schema_json: str,
    output_path: Path,
) -> tuple[list[str], bool]:
    if host == "codex":
        return (
            [
                "codex",
                "exec",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--skip-git-repo-check",
                "--ignore-rules",
                "-C",
                str(workspace),
                "--model",
                model,
                "-c",
                f'model_reasoning_effort="{reasoning}"',
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
                "-",
            ],
            True,
        )
    if host == "cursor":
        return (
            [
                "cursor-agent",
                "--print",
                "--mode",
                "ask",
                "--workspace",
                str(workspace),
                "--trust",
                "--model",
                model,
            ],
            False,
        )
    return (
        [
            "claude",
            "--print",
            "--permission-mode",
            "plan",
            "--tools",
            "",
            "--no-session-persistence",
            "--no-chrome",
            "--setting-sources",
            "project",
            "--json-schema",
            schema_json,
            "--model",
            model,
            "--effort",
            reasoning,
        ],
        False,
    )


def public_command(
    command: list[str], workspace: Path, schema_path: Path, schema_json: str
) -> str:
    replacements = (
        (schema_json, "$JUDGMENT_SCHEMA_JSON"),
        (str(schema_path), "$JUDGMENT_SCHEMA"),
        (str(workspace), "$JUDGE_WORKSPACE"),
        (str(ROOT), "$DESIGN_CRAFT_HOME"),
        (str(Path.home().resolve()), "~"),
    )
    values: list[str] = []
    for raw_value in command:
        value = raw_value
        for source, replacement in replacements:
            value = value.replace(source, replacement)
        values.append(value)
    return shlex.join(values)


def run_self_check() -> None:
    case_dir = ROOT / "evals/comparative/emil-motion-ablation"
    weights, errors = load_scorecard(case_dir)
    errors.extend(validate_judgment_schema(case_dir, weights))
    if errors:
        raise RuntimeError("; ".join(errors))
    criteria = {criterion: maximum for criterion, maximum in weights.items()}
    payload = {
        "results": [
            {
                "label": label,
                "criteria": criteria,
                "total": 100,
                "summary": "A sufficiently detailed self-check judgment summary.",
            }
            for label in BLIND_LABELS
        ],
        "winner": "A",
        "rationale": "A sufficiently detailed self-check rationale for the blind judgment contract.",
    }
    raw = "```json\n" + json.dumps(payload) + "\n```"
    parsed = parse_json_output(raw)
    if validate_judgment(parsed, weights):
        raise RuntimeError("judge self-check rejected a valid judgment")
    invalid = json.loads(json.dumps(payload))
    invalid["results"][0]["total"] = 99
    if not validate_judgment(invalid, weights):
        raise RuntimeError("judge self-check accepted a mismatched total")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir")
    parser.add_argument("--host", choices=HOSTS)
    parser.add_argument("--model")
    parser.add_argument("--reasoning-profile")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        run_self_check()
        print("comparative_judge_self_check=ok")
        return 0
    for value, label in (
        (args.case_dir, "--case-dir"),
        (args.host, "--host"),
        (args.model, "--model"),
        (args.reasoning_profile, "--reasoning-profile"),
    ):
        if not value:
            parser.error(f"{label} is required unless --check is used")
    if args.timeout < 10:
        parser.error("--timeout must be at least 10 seconds")
    if not args.dry_run and not shutil.which(EXECUTABLES[args.host]):
        parser.error(f"host executable is unavailable: {EXECUTABLES[args.host]}")

    case_dir = Path(args.case_dir).expanduser().resolve()
    packet_path = case_dir / "blind-packet.md"
    schema_source = case_dir / "judgment.schema.json"
    destinations = {
        "raw": case_dir / "judge-output.raw.txt",
        "judgment": case_dir / "blind-judgment.json",
        "manifest": case_dir / "run.judge.json",
    }
    if not packet_path.is_file() or not schema_source.is_file():
        parser.error("blind-packet.md and judgment.schema.json are required")
    if not args.dry_run and not args.force:
        existing = [str(path) for path in destinations.values() if path.exists()]
        if existing:
            parser.error("refusing to overwrite judge evidence: " + ", ".join(existing))
    weights, errors = load_scorecard(case_dir)
    errors.extend(validate_judgment_schema(case_dir, weights))
    if errors:
        parser.error("; ".join(errors))

    packet = packet_path.read_text(encoding="utf-8")
    schema_json = json.dumps(
        json.loads(schema_source.read_text(encoding="utf-8")),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    with tempfile.TemporaryDirectory(prefix=f"design-craft-judge-{args.host}-") as raw:
        temp_root = Path(raw)
        workspace = temp_root / "workspace"
        workspace.mkdir()
        schema_path = workspace / "judgment.schema.json"
        schema_path.write_text(schema_source.read_text(encoding="utf-8"), encoding="utf-8")
        temporary_output = workspace / ".judge-output.raw.txt"
        command, prompt_via_stdin = command_for(
            args.host,
            model=args.model,
            reasoning=args.reasoning_profile,
            workspace=workspace,
            schema_path=schema_path,
            schema_json=schema_json,
            output_path=temporary_output,
        )
        redacted_command = public_command(command, workspace, schema_path, schema_json)
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "schema": JUDGE_RUN_SCHEMA,
                        "host": args.host,
                        "command": redacted_command,
                        "cwd": "$JUDGE_WORKSPACE",
                        "packet_sha256": sha256_file(packet_path),
                        "judgment_schema_sha256": sha256_file(schema_source),
                        "outputs": {
                            key: f"$CASE_DIR/{path.name}"
                            for key, path in destinations.items()
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        before = worktree_fingerprint(ROOT)
        print(
            f"[comparative-judge] {case_dir.name} {args.host}: started",
            file=sys.stderr,
            flush=True,
        )
        started_at = datetime.now(timezone.utc)
        started = time.monotonic()
        run_command = command if prompt_via_stdin else [*command, packet]
        try:
            result = subprocess.run(
                run_command,
                input=packet if prompt_via_stdin else None,
                cwd=workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=args.timeout,
                check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        except subprocess.TimeoutExpired as exc:
            parser.error(f"{args.host} judge timed out after {args.timeout}s: {exc}")
        if args.host != "codex":
            temporary_output.write_text(result.stdout, encoding="utf-8")
        if result.returncode != 0:
            parser.error(result.stderr.strip() or f"{args.host} judge exited {result.returncode}")
        if not temporary_output.is_file() or temporary_output.stat().st_size < 40:
            parser.error(f"{args.host} judge did not produce substantive output")
        after = worktree_fingerprint(ROOT)
        if after != before:
            parser.error(f"{args.host} judge changed the source worktree")
        raw_output = temporary_output.read_text(encoding="utf-8")
        try:
            judgment = parse_json_output(raw_output)
        except (json.JSONDecodeError, ValueError) as exc:
            parser.error(f"judge output is not one canonical JSON object: {exc}")
        judgment_errors = validate_judgment(judgment, weights)
        if judgment_errors:
            parser.error("; ".join(judgment_errors))
        judgment_bytes = (
            json.dumps(judgment, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        raw_bytes = raw_output.encode("utf-8")
        manifest = {
            "schema": JUDGE_RUN_SCHEMA,
            "host": args.host,
            "host_version": command_version(EXECUTABLES[args.host]),
            "model": args.model,
            "model_observation": "requested_by_cli",
            "reasoning_profile": args.reasoning_profile,
            "reasoning_observation": "requested_by_cli",
            "runner_os": platform.platform(),
            "started_at": started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_seconds": round(time.monotonic() - started, 3),
            "timeout_seconds": args.timeout,
            "packet_path": packet_path.name,
            "packet_sha256": sha256_file(packet_path),
            "judgment_schema_sha256": sha256_file(schema_source),
            "raw_output_path": destinations["raw"].name,
            "raw_output_sha256": sha256_bytes(raw_bytes),
            "judgment_path": destinations["judgment"].name,
            "judgment_sha256": sha256_bytes(judgment_bytes),
            "workspace_kind": "repo_external_empty_project",
            "cwd": "$JUDGE_WORKSPACE",
            "command": redacted_command,
            "returncode": result.returncode,
            "stderr_bytes": len(result.stderr.encode("utf-8")),
            "stderr_sha256": sha256_bytes(result.stderr.encode("utf-8")),
            "worktree_before_sha256": before,
            "worktree_after_sha256": after,
            "worktree_unchanged": True,
        }
        manifest_bytes = (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        publish_files(
            {
                destinations["raw"]: raw_bytes,
                destinations["judgment"]: judgment_bytes,
                destinations["manifest"]: manifest_bytes,
            }
        )
    print(
        f"[comparative-judge] {case_dir.name} {args.host}: "
        f"passed in {manifest['duration_seconds']:.3f}s",
        file=sys.stderr,
        flush=True,
    )
    print(destinations["manifest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
