#!/usr/bin/env python3
"""Run isolated same-host skill-ablation variants without partial repo evidence."""

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
    RUN_SCHEMA,
    VARIANTS_SCHEMA,
    contract_sha256,
    sha256_bytes,
    sha256_file,
    variant_ids,
)
from design_craft_evidence_common import (
    command_version,
    git_dirty,
    git_head,
    publish_files,
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
    project_skill_domain,
    projected_skill_tree_sha256,
)

READ_ONLY_TOOLS = "read,grep,find,ls"


def load_variants(case_dir: Path) -> dict:
    payload = json.loads((case_dir / "variants.json").read_text(encoding="utf-8"))
    if payload.get("schema") != VARIANTS_SCHEMA:
        raise ValueError("variants.json has an unsupported schema")
    if payload.get("host") != "pi":
        raise ValueError("the comparative runner requires host=pi")
    items = payload.get("variants")
    if not isinstance(items, list):
        raise ValueError("variants.json variants must be an array")
    required = variant_ids(payload)
    observed_ids = [item.get("id") for item in items if isinstance(item, dict)]
    if sorted(observed_ids) != sorted(required) or len(observed_ids) != len(required):
        raise ValueError(f"variants must be {list(required)} exactly once")
    return payload


def install_variant_skills(
    variant: dict, workspace: Path, *, behavior_domain: str
) -> tuple[
    list[Path],
    dict[str, str],
    dict[str, str],
    dict[str, dict[str, object]],
    dict[str, str],
]:
    installed: list[Path] = []
    installed_trees: dict[str, str] = {}
    source_trees: dict[str, str] = {}
    source_fingerprints: dict[str, dict[str, object]] = {}
    public_paths: dict[str, str] = {}
    for index, raw_relative in enumerate(variant.get("skill_paths", []), start=1):
        relative = str(raw_relative)
        source = (ROOT / relative).resolve()
        if not source.joinpath("SKILL.md").is_file():
            raise FileNotFoundError(f"variant {variant.get('id')} skill is missing: {source}")
        destination = workspace / ".pi/skills" / f"{index:02d}-{source.name}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_tree = tree_sha256(source)
        source_trees[relative] = source_tree
        if relative == "skills/design-craft":
            project_skill_domain(ROOT, source, behavior_domain, destination)
            installed_tree = projected_skill_tree_sha256(
                ROOT, source, behavior_domain
            )
            source_fingerprints[relative] = {
                "kind": "evidence_domain",
                "domain": behavior_domain,
                "sha256": domain_fingerprint(ROOT, behavior_domain),
                "source_dirty": domain_dirty(ROOT, behavior_domain),
                "projected_tree_sha256": installed_tree,
            }
        else:
            shutil.copytree(source, destination, symlinks=False)
            installed_tree = source_tree
            source_fingerprints[relative] = {
                "kind": "tree",
                "sha256": source_tree,
                "source_dirty": git_dirty(ROOT, source),
                "projected_tree_sha256": installed_tree,
            }
        if tree_sha256(destination) != installed_tree:
            raise RuntimeError(
                f"isolated comparative skill projection does not match {relative}"
            )
        installed.append(destination)
        installed_trees[relative] = installed_tree
        public_paths[relative] = f"$VARIANT_WORKSPACE/{destination.relative_to(workspace).as_posix()}"
    return installed, installed_trees, source_trees, source_fingerprints, public_paths


def public_command(command: list[str], workspace: Path, installed: list[Path]) -> str:
    replacements = [(str(path), f"$VARIANT_SKILL_{index}") for index, path in enumerate(installed, 1)]
    replacements.extend(
        (
            (str(workspace), "$VARIANT_WORKSPACE"),
            (str(ROOT), "$DESIGN_CRAFT_HOME"),
            (str(Path.home().resolve()), "~"),
        )
    )
    values: list[str] = []
    for raw_value in command:
        value = raw_value
        for source, replacement in replacements:
            value = value.replace(source, replacement)
        values.append(value)
    return shlex.join(values)


def command_for(
    *, model: str, thinking: str, installed_skills: list[Path]
) -> list[str]:
    command = [
        "pi",
        "--print",
        "--no-session",
        "--no-context-files",
        "--no-skills",
        "--tools",
        READ_ONLY_TOOLS,
        "--model",
        model,
        "--thinking",
        thinking,
    ]
    for skill_path in installed_skills:
        command.extend(("--skill", str(skill_path)))
    return command


def run_self_check() -> None:
    case_dir = ROOT / "evals/comparative/emil-motion-ablation"
    variants = load_variants(case_dir)
    behavior_domain = binding_domain("comparative", case_dir.name, root=ROOT)
    with tempfile.TemporaryDirectory(prefix="design-craft-comparative-run-check-") as raw:
        root = Path(raw)
        for item in variants["variants"]:
            workspace = root / str(item["id"])
            workspace.mkdir()
            installed, trees, source_trees, fingerprints, public_paths = (
                install_variant_skills(
                    item,
                    workspace,
                    behavior_domain=behavior_domain,
                )
            )
            command = command_for(model="fixture", thinking="low", installed_skills=installed)
            if "--tools" not in command or READ_ONLY_TOOLS not in command:
                raise RuntimeError("comparative runner must expose only the read-only skill tools")
            if any(tool in command for tool in ("bash", "edit", "write")):
                raise RuntimeError("comparative runner exposed a mutating tool")
            redacted = public_command(command, workspace, installed)
            if str(root) in redacted or str(Path.home()) in redacted:
                raise RuntimeError("comparative command leaked a local path")
            if not (
                set(trees)
                == set(source_trees)
                == set(fingerprints)
                == set(public_paths)
            ):
                raise RuntimeError("comparative isolated skill metadata is incomplete")
        output = root / "output.md"
        manifest = root / "run.json"
        publish_files({output: b"fixture output\n", manifest: b"{}\n"})
        if not output.is_file() or not manifest.is_file():
            raise RuntimeError("comparative evidence transaction did not publish every file")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir")
    parser.add_argument("--model")
    parser.add_argument("--thinking", default="high")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        run_self_check()
        print("comparative_runner_self_check=ok")
        return 0
    if not args.case_dir or not args.model:
        parser.error("--case-dir and --model are required unless --check is used")
    if args.timeout < 10:
        parser.error("--timeout must be at least 10 seconds")
    if not args.dry_run and not shutil.which("pi"):
        parser.error("pi is required")

    case_dir = Path(args.case_dir).expanduser().resolve()
    prompt_path = case_dir / "prompt.md"
    if not prompt_path.is_file():
        parser.error(f"missing prompt: {prompt_path}")
    try:
        variants = load_variants(case_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    destinations = {
        item["id"]: (
            case_dir / f"output.{item['id']}.md",
            case_dir / f"run.{item['id']}.json",
        )
        for item in variants["variants"]
    }
    if not args.dry_run and not args.force:
        existing = [str(path) for pair in destinations.values() for path in pair if path.exists()]
        if existing:
            parser.error("refusing to overwrite comparative evidence: " + ", ".join(existing))

    prompt = prompt_path.read_text(encoding="utf-8")
    behavior_domain = binding_domain("comparative", case_dir.name, root=ROOT)
    source_commit = git_head(ROOT)
    before = worktree_fingerprint(ROOT)
    generated: dict[Path, bytes] = {}
    results: list[dict] = []
    version = "dry-run" if args.dry_run else command_version("pi")
    with tempfile.TemporaryDirectory(prefix="design-craft-comparative-run-") as raw:
        temp_root = Path(raw)
        variant_items = variants["variants"]
        for variant_index, variant in enumerate(variant_items, start=1):
            variant_id = str(variant["id"])
            workspace = temp_root / variant_id / "workspace"
            workspace.mkdir(parents=True)
            try:
                (
                    installed,
                    skill_trees,
                    source_trees,
                    source_fingerprints,
                    installed_paths,
                ) = install_variant_skills(
                    variant,
                    workspace,
                    behavior_domain=behavior_domain,
                )
            except (OSError, RuntimeError, FileNotFoundError) as exc:
                parser.error(str(exc))
            command = command_for(
                model=args.model,
                thinking=args.thinking,
                installed_skills=installed,
            )
            redacted_command = public_command(command, workspace, installed)
            if args.dry_run:
                results.append(
                    {
                        "schema": RUN_SCHEMA,
                        "variant": variant_id,
                        "command": redacted_command,
                        "cwd": "$VARIANT_WORKSPACE",
                        "source_commit": source_commit,
                        "skill_trees": skill_trees,
                        "source_trees": source_trees,
                        "source_fingerprints": source_fingerprints,
                        "installed_skill_paths": installed_paths,
                    }
                )
                continue

            print(
                f"[comparative] {case_dir.name} "
                f"variant {variant_index}/{len(variant_items)} {variant_id}: started",
                file=sys.stderr,
                flush=True,
            )
            started_at = datetime.now(timezone.utc)
            dirty_sources = [
                relative
                for relative, item in source_fingerprints.items()
                if item.get("source_dirty") is not False
            ]
            if dirty_sources:
                parser.error(
                    "refusing to run current comparative evidence from dirty sources: "
                    + ", ".join(dirty_sources)
                )
            started = time.monotonic()
            try:
                run = subprocess.run(
                    [*command, prompt],
                    cwd=workspace,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=args.timeout,
                    check=False,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )
            except subprocess.TimeoutExpired as exc:
                parser.error(f"variant {variant_id} timed out: {exc}")
            if run.returncode != 0:
                parser.error(run.stderr.strip() or f"variant {variant_id} failed")
            output_bytes = run.stdout.encode("utf-8")
            if len(output_bytes) < 40:
                parser.error(f"variant {variant_id} produced no substantive output")
            after_variant = worktree_fingerprint(ROOT)
            if after_variant != before:
                parser.error(f"variant {variant_id} changed the source worktree")
            for source_relative, installed_path in zip(skill_trees, installed, strict=True):
                if tree_sha256(installed_path) != skill_trees[source_relative]:
                    parser.error(f"variant {variant_id} changed its isolated skill copy")

            output_path, manifest_path = destinations[variant_id]
            payload = {
                "schema": RUN_SCHEMA,
                "variant": variant_id,
                "host": "pi",
                "host_version": version,
                "model": args.model,
                "model_observation": "requested_by_cli",
                "thinking": args.thinking,
                "thinking_observation": "requested_by_cli",
                "runner_os": platform.platform(),
                "source_commit": source_commit,
                "started_at": started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "duration_seconds": round(time.monotonic() - started, 3),
                "timeout_seconds": args.timeout,
                "prompt_sha256": sha256_file(prompt_path),
                "output_path": output_path.name,
                "output_sha256": sha256_bytes(output_bytes),
                "skill_trees": skill_trees,
                "source_trees": source_trees,
                "source_fingerprints": source_fingerprints,
                "installed_skill_paths": installed_paths,
                "skill_install_mode": "isolated_case_projection",
                "workspace_kind": "repo_external_isolated_project",
                "cwd": "$VARIANT_WORKSPACE",
                "command": redacted_command,
                "contract_sha256": contract_sha256(),
                "returncode": run.returncode,
                "stderr_bytes": len(run.stderr.encode("utf-8")),
                "stderr_sha256": sha256_bytes(run.stderr.encode("utf-8")),
                "worktree_before_sha256": before,
                "worktree_after_sha256": after_variant,
                "worktree_unchanged": True,
            }
            manifest_bytes = (
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            generated[output_path] = output_bytes
            generated[manifest_path] = manifest_bytes
            results.append(payload)
            print(
                f"[comparative] {case_dir.name} "
                f"variant {variant_index}/{len(variant_items)} {variant_id}: "
                f"passed in {payload['duration_seconds']:.3f}s",
                file=sys.stderr,
                flush=True,
            )
        if args.dry_run:
            print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        if worktree_fingerprint(ROOT) != before:
            parser.error("source worktree changed before comparative evidence publication")
        publish_files(generated)
    print(
        f"[comparative] {case_dir.name}: evidence transaction published",
        file=sys.stderr,
        flush=True,
    )
    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
