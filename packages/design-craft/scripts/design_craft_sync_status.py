#!/usr/bin/env python3
"""Report canonical, installed, route-pack, and upstream sync status."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


SCHEMA = "design-craft.sync-status.v2"
ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def parse_json_result(result: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "errors": [result.stderr.strip() or result.stdout.strip() or "invalid JSON output"],
        }


def git_value(*args: str) -> str:
    result = run(["git", *args])
    return result.stdout.strip() if result.returncode == 0 else ""


def parse_divergence(value: str) -> tuple[int | None, int | None]:
    try:
        behind, ahead = (int(part) for part in value.split())
    except (TypeError, ValueError):
        return None, None
    return behind, ahead


def parse_ls_remote(value: str, ref: str) -> str:
    for line in value.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1] == ref:
            return fields[0]
    return ""


def canonical_status(*, remote: bool) -> dict[str, object]:
    head = git_value("rev-parse", "HEAD")
    branch = git_value("symbolic-ref", "--quiet", "--short", "HEAD")
    upstream = git_value("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    cached_upstream_head = git_value("rev-parse", "@{upstream}") if upstream else ""
    divergence = git_value("rev-list", "--left-right", "--count", "@{upstream}...HEAD") if upstream else ""
    behind, ahead = parse_divergence(divergence)
    dirty = bool(git_value("status", "--porcelain=v1", "--untracked-files=all"))

    remote_name = git_value("config", "--get", f"branch.{branch}.remote") if branch else ""
    merge_ref = git_value("config", "--get", f"branch.{branch}.merge") if branch else ""
    remote_payload: dict[str, object] = {
        "checked": remote,
        "name": remote_name,
        "ref": merge_ref,
        "head": None,
        "matches_head": None,
        "ok": None,
        "error": None,
    }
    if remote:
        if not remote_name or not merge_ref:
            remote_payload.update(
                {
                    "ok": False,
                    "error": "current branch must have a configured remote and merge ref",
                }
            )
        else:
            remote_result = run(["git", "ls-remote", remote_name, merge_ref])
            remote_head = parse_ls_remote(remote_result.stdout, merge_ref)
            matches_head = bool(head and remote_head == head)
            remote_payload.update(
                {
                    "head": remote_head or None,
                    "matches_head": matches_head,
                    "ok": remote_result.returncode == 0 and bool(remote_head) and matches_head,
                    "error": None
                    if remote_result.returncode == 0 and remote_head
                    else remote_result.stderr.strip() or f"cannot resolve {remote_name} {merge_ref}",
                }
            )

    cached_ok = bool(
        head
        and branch
        and upstream
        and cached_upstream_head == head
        and behind == 0
        and ahead == 0
    )
    remote_ok = remote_payload["ok"] is not False
    return {
        "root": str(ROOT),
        "branch": branch or None,
        "head": head or None,
        "dirty": dirty,
        "upstream": upstream or None,
        "cached_upstream_head": cached_upstream_head or None,
        "behind": behind,
        "ahead": ahead,
        "cached_ok": cached_ok,
        "remote": remote_payload,
        "ok": cached_ok and remote_ok,
    }


def install_status(skill_root: Path, version: str, name: str) -> dict[str, object]:
    installed = skill_root / name
    result = run(
        [
            sys.executable,
            "scripts/design_craft_install_verify.py",
            "--source",
            f"skills/{name}",
            "--installed",
            str(installed),
            "--expected-name",
            name,
            "--expected-version",
            version,
            "--require-metadata",
            "--json",
        ]
    )
    payload = parse_json_result(result)
    payload["present"] = installed.exists()
    return payload


def run_self_check() -> None:
    behind, ahead = parse_divergence("2\t3")
    if (behind, ahead) != (2, 3):
        raise RuntimeError("sync-status divergence parser failed")
    if parse_divergence("invalid") != (None, None):
        raise RuntimeError("sync-status accepted invalid divergence")
    sample = "a" * 40 + "\trefs/heads/main\n" + "b" * 40 + "\tHEAD\n"
    if parse_ls_remote(sample, "refs/heads/main") != "a" * 40:
        raise RuntimeError("sync-status ls-remote parser failed")
    if parse_ls_remote(sample, "refs/heads/missing"):
        raise RuntimeError("sync-status invented a missing remote ref")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Also compare live origin and mutable upstream heads.",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        run_self_check()
        print("sync_status_self_check=ok")
        return 0

    skill_root = Path(
        os.environ.get("DESIGN_CRAFT_SKILL_ROOT", Path.home() / ".agents/skills")
    ).expanduser()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    canonical = canonical_status(remote=args.remote)
    install = install_status(skill_root, version, "design-craft")
    route_result = run(
        [sys.executable, "scripts/design_craft_codex_route_pack.py", "--strict", "--json"]
    )
    route_pack = parse_json_result(route_result)

    upstream: dict[str, object] = {"checked": False, "ok": None}
    if args.remote:
        upstream_result = run(
            [
                sys.executable,
                "scripts/upstream_absorption_report.py",
                "--remote-details",
                "--fail-on-unreviewed",
                "--json",
            ]
        )
        upstream = {
            "checked": True,
            "ok": upstream_result.returncode == 0,
            "report": parse_json_result(upstream_result),
            "stderr": upstream_result.stderr.strip(),
        }

    ok = bool(
        canonical.get("ok")
        and install.get("ok")
        and route_pack.get("status") == "ok"
        and upstream.get("ok") is not False
    )
    payload = {
        "schema": SCHEMA,
        "root": str(ROOT),
        "version": version,
        "ok": ok,
        "canonical": canonical,
        "install": install,
        "route_pack": {
            "status": route_pack.get("status"),
            "source_root": route_pack.get("source_root"),
            "summary": route_pack.get("summary"),
            "semantic_validation": route_pack.get("semantic_validation"),
        },
        "upstream": upstream,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"design-craft sync status: {'ok' if ok else 'drift'}")
        print(f"canonical: {'ok' if canonical.get('ok') else 'drift'}")
        print(f"install: {'ok' if install.get('ok') else 'drift'}")
        print(f"route_pack: {route_pack.get('status', 'invalid')}")
        print(
            f"upstream: {'not checked' if not args.remote else 'ok' if upstream.get('ok') else 'drift'}"
        )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
