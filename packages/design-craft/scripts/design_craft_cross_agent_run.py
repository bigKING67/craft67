#!/usr/bin/env python3
"""Run one exact cross-agent benchmark in an isolated project skill workspace."""

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

from design_craft_evidence_common import (
    command_version,
    git_head,
    publish_files,
    sha256_bytes,
    tree_sha256,
    worktree_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.design_craft.evaluation.evidence_graph import (
    binding_domain,
    domain_dirty,
    domain_fingerprint,
    git_domain_fingerprint,
    git_projected_skill_tree_sha256,
    project_skill_domain,
    projected_skill_tree_sha256,
)


SCHEMA = "design-craft.cross-agent-run.v3"
HOSTS = ("codex", "pi", "cursor", "claude")
EXECUTABLES = {
    "codex": "codex",
    "pi": "pi",
    "cursor": "cursor-agent",
    "claude": "claude",
}
PROJECT_SKILL_PATHS = {
    "codex": Path(".agents/skills/design-craft"),
    "pi": Path(".pi/skills/design-craft"),
    "cursor": Path(".cursor/skills/design-craft"),
    "claude": Path(".claude/skills/design-craft"),
}


def install_project_skill(
    host: str, source: Path, workspace: Path, *, behavior_domain: str
) -> Path:
    destination = workspace / PROJECT_SKILL_PATHS[host]
    destination.parent.mkdir(parents=True, exist_ok=True)
    project_skill_domain(ROOT, source, behavior_domain, destination)
    expected = projected_skill_tree_sha256(ROOT, source, behavior_domain)
    if tree_sha256(destination) != expected:
        raise RuntimeError(
            f"isolated {host} skill projection does not match {behavior_domain}"
        )
    return destination


def command_for(
    host: str,
    *,
    model: str,
    reasoning: str,
    workspace: Path,
    installed_skill: Path,
    output: Path,
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
                "--output-last-message",
                str(output),
                "-",
            ],
            True,
        )
    if host == "pi":
        return (
            [
                "pi",
                "--print",
                "--no-session",
                "--no-skills",
                "--skill",
                str(installed_skill),
                "--no-context-files",
                "--tools",
                "read,grep,find,ls",
                "--model",
                model,
                "--thinking",
                reasoning,
            ],
            False,
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
            "Read,Grep,Glob",
            "--no-session-persistence",
            "--no-chrome",
            "--strict-mcp-config",
            "--setting-sources",
            "user,project",
            "--model",
            model,
            "--effort",
            reasoning,
        ],
        False,
    )


def public_command(command: list[str], workspace: Path, installed_skill: Path) -> str:
    replacements = (
        (str(installed_skill), "$BENCHMARK_SKILL"),
        (str(workspace), "$BENCHMARK_WORKSPACE"),
        (str(ROOT), "$DESIGN_CRAFT_HOME"),
        (str(Path.home().resolve()), "~"),
    )
    redacted = []
    for raw_value in command:
        value = raw_value
        for source, replacement in replacements:
            value = value.replace(source, replacement)
        redacted.append(value)
    return shlex.join(redacted)


def run_self_check() -> None:
    with tempfile.TemporaryDirectory(prefix="design-craft-cross-agent-check-") as raw:
        root = Path(raw)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        untracked = root / "dirty.txt"
        untracked.write_text("one\n", encoding="utf-8")
        before = worktree_fingerprint(root)
        untracked.write_text("two\n", encoding="utf-8")
        if worktree_fingerprint(root) == before:
            raise RuntimeError("worktree fingerprint ignored an already-untracked edit")

        workspace = root / "workspace"
        workspace.mkdir()
        behavior_domain = "skill-motion-review"
        installed = install_project_skill(
            "codex",
            ROOT / "skills/design-craft",
            workspace,
            behavior_domain=behavior_domain,
        )
        output = workspace / ".design-craft-output.md"
        for host in HOSTS:
            host_skill = (
                installed
                if host == "codex"
                else install_project_skill(
                    host,
                    ROOT / "skills/design-craft",
                    workspace / host,
                    behavior_domain=behavior_domain,
                )
            )
            host_workspace = workspace if host == "codex" else workspace / host
            command, stdin_prompt = command_for(
                host,
                model="fixture",
                reasoning="low",
                workspace=host_workspace,
                installed_skill=host_skill,
                output=output,
            )
            public = public_command(command, host_workspace, host_skill)
            if "$BENCHMARK_WORKSPACE" not in public and host in {"codex", "cursor"}:
                raise RuntimeError(f"{host} command is not bound to the isolated workspace")
            if str(root) in public or str(Path.home()) in public:
                raise RuntimeError(f"{host} public command leaked a local path")
            if host == "codex" and (not stdin_prompt or command[-1] != "-"):
                raise RuntimeError("Codex command is not stdin-bound")
            if host == "pi" and str(host_skill) not in command:
                raise RuntimeError("Pi command is not bound to the isolated skill")
            if host == "claude":
                if "user,project" not in command or "Read,Grep,Glob" not in command:
                    raise RuntimeError("Claude command must preserve auth and expose read-only tools")
                if any(tool in command for tool in ("Bash", "Edit", "Write")):
                    raise RuntimeError("Claude command exposed a mutating tool")

        destination = root / "published.md"
        publish_files({destination: b"first\n"})
        publish_files({destination: b"second\n"})
        if destination.read_bytes() != b"second\n":
            raise RuntimeError("evidence publisher did not replace the staged output")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir")
    parser.add_argument("--host", choices=HOSTS)
    parser.add_argument("--model")
    parser.add_argument("--reasoning-profile")
    parser.add_argument("--skill-root", default="skills/design-craft")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        run_self_check()
        print("cross_agent_runner_self_check=ok")
        return 0
    for value, label in (
        (args.task_dir, "--task-dir"),
        (args.host, "--host"),
        (args.model, "--model"),
        (args.reasoning_profile, "--reasoning-profile"),
    ):
        if not value:
            parser.error(f"{label} is required unless --check is used")
    if args.timeout < 10:
        parser.error("--timeout must be at least 10 seconds")

    task_dir = Path(args.task_dir).expanduser().resolve()
    skill_root = Path(args.skill_root).expanduser().resolve()
    prompt_path = task_dir / "prompt.md"
    output_path = task_dir / f"{args.host}-output.md"
    manifest_path = task_dir / f"run.{args.host}.json"
    if not prompt_path.is_file():
        parser.error(f"benchmark prompt does not exist: {prompt_path}")
    if not skill_root.joinpath("SKILL.md").is_file():
        parser.error(f"skill root does not exist: {skill_root}")
    if not args.dry_run and not args.force and (output_path.exists() or manifest_path.exists()):
        parser.error("refusing to overwrite existing host output/run manifest without --force")
    executable = EXECUTABLES[args.host]
    if not args.dry_run and not shutil.which(executable):
        parser.error(f"host executable is unavailable: {executable}")

    prompt = prompt_path.read_text(encoding="utf-8")
    source_skill_tree = tree_sha256(skill_root)
    behavior_domain = binding_domain("cross_agent", task_dir.name, root=ROOT)
    behavior_sha256 = domain_fingerprint(ROOT, behavior_domain)
    behavior_source_dirty = domain_dirty(ROOT, behavior_domain)
    projected_tree = projected_skill_tree_sha256(
        ROOT, skill_root, behavior_domain
    )
    if not args.dry_run and behavior_source_dirty:
        parser.error(
            f"refusing to run current evidence from dirty behavior domain {behavior_domain}"
        )
    if not args.dry_run:
        source_commit = git_head(ROOT)
        if (
            git_domain_fingerprint(ROOT, behavior_domain, source_commit)
            != behavior_sha256
            or git_projected_skill_tree_sha256(
                ROOT, skill_root, behavior_domain, source_commit
            )
            != projected_tree
        ):
            parser.error(
                f"behavior domain {behavior_domain} is not committed at current HEAD"
            )
    with tempfile.TemporaryDirectory(prefix=f"design-craft-{args.host}-run-") as raw:
        temp_root = Path(raw)
        workspace = temp_root / "workspace"
        workspace.mkdir()
        installed_skill = install_project_skill(
            args.host,
            skill_root,
            workspace,
            behavior_domain=behavior_domain,
        )
        temporary_output = workspace / ".design-craft-host-output.md"
        command, prompt_via_stdin = command_for(
            args.host,
            model=args.model,
            reasoning=args.reasoning_profile,
            workspace=workspace,
            installed_skill=installed_skill,
            output=temporary_output,
        )
        public = public_command(command, workspace, installed_skill)
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "schema": SCHEMA,
                        "host": args.host,
                        "command": public,
                        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
                        "prompt_transport": "stdin" if prompt_via_stdin else "argument",
                        "skill_path": f"$BENCHMARK_WORKSPACE/{PROJECT_SKILL_PATHS[args.host].as_posix()}",
                        "source_skill_tree_sha256": source_skill_tree,
                        "behavior_domain": behavior_domain,
                        "behavior_sha256": behavior_sha256,
                        "behavior_source_dirty": behavior_source_dirty,
                        "projected_skill_tree_sha256": projected_tree,
                        "output": f"$TASK_DIR/{output_path.name}",
                        "manifest": f"$TASK_DIR/{manifest_path.name}",
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        before = worktree_fingerprint(ROOT)
        started_at = datetime.now(timezone.utc)
        started = time.monotonic()
        run_command = command if prompt_via_stdin else [*command, prompt]
        try:
            result = subprocess.run(
                run_command,
                input=prompt if prompt_via_stdin else None,
                cwd=workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=args.timeout,
                check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        except subprocess.TimeoutExpired as exc:
            parser.error(f"{args.host} inference timed out after {args.timeout}s: {exc}")
        duration = round(time.monotonic() - started, 3)
        if args.host != "codex":
            temporary_output.write_text(result.stdout, encoding="utf-8")
        if result.returncode != 0:
            parser.error(
                result.stderr.strip()
                or result.stdout.strip()
                or f"{args.host} exited {result.returncode}"
            )
        if not temporary_output.is_file() or temporary_output.stat().st_size < 40:
            parser.error(f"{args.host} did not produce a substantive output")
        after = worktree_fingerprint(ROOT)
        if after != before:
            parser.error(f"{args.host} changed the source worktree despite isolated read-only mode")
        if tree_sha256(installed_skill) != projected_tree:
            parser.error(f"{args.host} isolated skill projection changed during inference")

        output_bytes = temporary_output.read_bytes()
        version = command_version(EXECUTABLES[args.host])
        manifest = {
            "schema": SCHEMA,
            "host": args.host,
            "host_version": version,
            "model": args.model,
            "model_observation": "requested_by_cli",
            "reasoning_profile": args.reasoning_profile,
            "reasoning_observation": "requested_by_cli",
            "runner_os": platform.platform(),
            "started_at": started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_seconds": duration,
            "timeout_seconds": args.timeout,
            "prompt_path": "prompt.md",
            "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
            "prompt_transport": "stdin" if prompt_via_stdin else "argument",
            "output_path": output_path.name,
            "output_sha256": sha256_bytes(output_bytes),
            "skill_path": f"$BENCHMARK_WORKSPACE/{PROJECT_SKILL_PATHS[args.host].as_posix()}",
            "source_skill_tree_sha256": source_skill_tree,
            "behavior_domain": behavior_domain,
            "behavior_sha256": behavior_sha256,
            "behavior_source_dirty": behavior_source_dirty,
            "projected_skill_tree_sha256": projected_tree,
            "skill_install_mode": "isolated_domain_projection",
            "workspace_kind": "repo_external_isolated_project",
            "cwd": "$BENCHMARK_WORKSPACE",
            "command": public,
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
        publish_files({output_path: output_bytes, manifest_path: manifest_bytes})
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
