#!/usr/bin/env python3
"""Verify exact per-level GitHub workflow and Release state for HEAD."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.design_craft.release.assets import validate_assets
from tools.design_craft.release.github_runs import validate_run
from tools.design_craft.release.native_bundle import validate_native_bundle
from tools.design_craft.release.policy import LEVELS, load_policy


SCHEMA = "design-craft.github-checks.v2"
WORKFLOWS = ("validate.yml", "native-runtime.yml")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def latest_matching_run(
    runs: list[dict],
    *,
    head: str,
    required_event: str | None = None,
    required_branch: str | None = None,
) -> tuple[list[dict], dict | None]:
    matching = [
        item
        for item in runs
        if item.get("headSha") == head
        and (required_event is None or item.get("event") == required_event)
        and (required_branch is None or item.get("headBranch") == required_branch)
    ]
    matching.sort(key=lambda item: str(item.get("createdAt", "")), reverse=True)
    return matching, matching[0] if matching else None


def validate_latest_run(
    workflow: str,
    runs: list[dict],
    *,
    head: str,
    required_event: str | None = None,
    required_branch: str | None = None,
) -> tuple[list[dict], dict | None, list[str]]:
    matching, latest = latest_matching_run(
        runs,
        head=head,
        required_event=required_event,
        required_branch=required_branch,
    )
    qualifiers = []
    if required_event:
        qualifiers.append(f"event={required_event}")
    if required_branch:
        qualifiers.append(f"headBranch={required_branch}")
    suffix = f" ({', '.join(qualifiers)})" if qualifiers else ""
    if latest is None:
        return matching, latest, [f"{workflow} has no run for {head}{suffix}"]
    if latest.get("status") != "completed":
        return matching, latest, [
            f"latest {workflow} run for {head}{suffix} is not completed: "
            f"{latest.get('url', 'unknown run')}"
        ]
    if latest.get("conclusion") != "success":
        return matching, latest, [
            f"latest {workflow} run for {head}{suffix} did not succeed: "
            f"{latest.get('conclusion', 'unknown')} {latest.get('url', '')}".strip()
        ]
    return matching, latest, []


def validate_release_native_bindings(
    manifest: dict[str, object],
    *,
    required_native: tuple[str, ...],
    expected_run: dict[str, object] | None,
    expected_repository: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(expected_run, dict):
        return ["release native evidence cannot be bound to the selected tag run"]
    bindings = manifest.get("native_evidence")
    if not isinstance(bindings, dict):
        return ["release manifest native_evidence is missing"]
    for native in required_native:
        if native == "physical_device":
            continue
        binding = bindings.get(native)
        workflow = binding.get("workflow") if isinstance(binding, dict) else None
        if not isinstance(workflow, dict):
            errors.append(f"release native evidence {native} has no workflow binding")
            continue
        expected = {
            "repository": expected_repository,
            "run_id": expected_run.get("databaseId"),
            "run_attempt": expected_run.get("attempt"),
            "head_sha": expected_run.get("headSha"),
            "event": expected_run.get("event"),
            "url": expected_run.get("url"),
        }
        for field, value in expected.items():
            if workflow.get(field) != value:
                errors.append(
                    f"release native evidence {native} workflow {field} does not match the selected tag run"
                )
        head_branch = expected_run.get("headBranch")
        if isinstance(head_branch, str) and workflow.get("ref") != f"refs/tags/{head_branch}":
            errors.append(
                f"release native evidence {native} workflow ref does not match the selected tag run"
            )
    return errors


def run_self_check() -> None:
    head = "a" * 40
    manual_success = {
        "databaseId": 1,
        "attempt": 1,
        "status": "completed",
        "conclusion": "success",
        "headSha": head,
        "headBranch": "main",
        "event": "workflow_dispatch",
        "createdAt": "2026-01-01T00:00:00Z",
        "url": "https://example.invalid/manual",
    }
    tag_failure = {
        **manual_success,
        "databaseId": 2,
        "conclusion": "failure",
        "headBranch": "v0.5.0",
        "event": "push",
        "createdAt": "2026-01-02T00:00:00Z",
        "url": "https://example.invalid/tag-failure",
    }
    _, latest, errors = validate_latest_run(
        "native-runtime.yml",
        [manual_success, tag_failure],
        head=head,
        required_event="push",
        required_branch="v0.5.0",
    )
    if latest != tag_failure or not errors:
        raise RuntimeError("tag-run validation accepted an older manual success")
    tag_success = {
        **tag_failure,
        "databaseId": 3,
        "conclusion": "success",
        "createdAt": "2026-01-03T00:00:00Z",
        "url": "https://example.invalid/tag-success",
    }
    _, latest, errors = validate_latest_run(
        "native-runtime.yml",
        [manual_success, tag_failure, tag_success],
        head=head,
        required_event="push",
        required_branch="v0.5.0",
    )
    if latest != tag_success or errors:
        raise RuntimeError("latest successful tag run did not validate")
    policy = load_policy()
    if len(policy["operational_95"].assets("0.5.0")) != 4:
        raise RuntimeError("operational_95 must require exactly four assets")
    if len(policy["certified_100"].assets("0.5.0")) != 7:
        raise RuntimeError("certified_100 must require exactly seven assets")
    fixture_manifest = {
        "native_evidence": {
            native: {
                "workflow": {
                    "repository": "example/design-craft",
                    "run_id": tag_success["databaseId"],
                    "run_attempt": 1,
                    "head_sha": head,
                    "event": "push",
                    "url": tag_success["url"],
                    "ref": "refs/tags/v0.5.0",
                }
            }
            for native in ("ios_simulator", "android_emulator")
        }
    }
    if validate_release_native_bindings(
        fixture_manifest,
        required_native=("ios_simulator", "android_emulator"),
        expected_run=tag_success,
        expected_repository="example/design-craft",
    ):
        raise RuntimeError("valid operational native workflow bindings were rejected")
    fixture_manifest["native_evidence"]["ios_simulator"]["workflow"]["run_id"] = 999
    if not validate_release_native_bindings(
        fixture_manifest,
        required_native=("ios_simulator", "android_emulator"),
        expected_run=tag_success,
        expected_repository="example/design-craft",
    ):
        raise RuntimeError("tampered operational native workflow binding was accepted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", choices=LEVELS)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--require-tag-run",
        action="store_true",
        help="Require the latest v<VERSION> tag-push run for Validate and Native runtime.",
    )
    parser.add_argument(
        "--require-release-assets",
        action="store_true",
        help="Require a published GitHub Release with the exact per-level asset set.",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        run_self_check()
        print("github_checks_self_check=ok")
        return 0
    if not args.level:
        parser.error("--level is required unless --check is used")
    level = load_policy()[args.level]

    errors: list[str] = []
    results: dict[str, object] = {}
    selected_runs: dict[str, object] = {}
    if not shutil.which("gh"):
        errors.append("gh CLI is required to verify remote workflow runs")
        repo = ""
        head = ""
    else:
        head_result = run(["git", "rev-parse", "HEAD"])
        head = head_result.stdout.strip()
        repo_result = run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
        )
        repo = repo_result.stdout.strip()
        if head_result.returncode != 0 or not head:
            errors.append("cannot resolve current HEAD")
        if repo_result.returncode != 0 or not repo:
            errors.append(repo_result.stderr.strip() or "cannot resolve GitHub repository")

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    tag = f"v{version}"
    required_event = "push" if args.require_tag_run else None
    required_branch = tag if args.require_tag_run else None
    if args.require_tag_run:
        tag_result = run(["git", "rev-list", "-n", "1", tag])
        if tag_result.returncode != 0 or tag_result.stdout.strip() != head:
            errors.append(f"tag {tag} must exist and point to current HEAD")

    if repo and head:
        for workflow in WORKFLOWS:
            result = run(
                [
                    "gh",
                    "run",
                    "list",
                    "--repo",
                    repo,
                    "--workflow",
                    workflow,
                    "--commit",
                    head,
                    "--limit",
                    "20",
                    "--json",
                    "attempt,databaseId,status,conclusion,headSha,headBranch,url,event,createdAt,workflowName",
                ]
            )
            if result.returncode != 0:
                errors.append(result.stderr.strip() or f"cannot query {workflow}")
                results[workflow] = []
                continue
            try:
                runs = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid gh output for {workflow}: {exc}")
                results[workflow] = []
                continue
            matching, latest, run_errors = validate_latest_run(
                workflow,
                runs,
                head=head,
                required_event=required_event,
                required_branch=required_branch,
            )
            results[workflow] = matching
            selected_runs[workflow] = latest
            errors.extend(run_errors)

    release_payload: dict[str, object] | None = None
    release_assets_validation: dict[str, object] | None = None
    release_manifest: dict[str, object] | None = None
    native_validation: dict[str, object] | None = None
    if args.require_release_assets:
        if not repo:
            errors.append("cannot verify GitHub Release without a repository")
        else:
            release_result = run(["gh", "api", f"repos/{repo}/releases/tags/{tag}"])
            if release_result.returncode != 0:
                errors.append(release_result.stderr.strip() or f"GitHub Release {tag} does not exist")
            else:
                try:
                    release_payload = json.loads(release_result.stdout)
                except json.JSONDecodeError as exc:
                    errors.append(f"invalid GitHub Release payload: {exc}")
                else:
                    if release_payload.get("draft") is True or release_payload.get("prerelease") is True:
                        errors.append(f"GitHub Release {tag} must be final and published")
                    if release_payload.get("tag_name") != tag:
                        errors.append(f"GitHub Release tag must be {tag}")
                    expected_assets = set(level.assets(version))
                    observed_assets = {
                        item.get("name")
                        for item in release_payload.get("assets", [])
                        if isinstance(item, dict)
                    }
                    if observed_assets != expected_assets:
                        errors.append(
                            "GitHub Release asset set mismatch: "
                            f"expected={sorted(expected_assets)} observed={sorted(observed_assets)}"
                        )
                    else:
                        with tempfile.TemporaryDirectory(
                            prefix="design-craft-release-download-"
                        ) as raw:
                            download = run(
                                [
                                    "gh",
                                    "release",
                                    "download",
                                    tag,
                                    "--repo",
                                    repo,
                                    "--dir",
                                    raw,
                                    *[
                                        argument
                                        for name in level.assets(version)
                                        for argument in ("--pattern", name)
                                    ],
                                ]
                            )
                            if download.returncode != 0:
                                errors.append(download.stderr.strip() or "cannot download release assets")
                            else:
                                release_assets_validation = validate_assets(
                                    Path(raw), level=level
                                )
                                errors.extend(release_assets_validation.get("errors", []))
                                manifest_path = Path(raw) / level.assets(version)[2]
                                try:
                                    release_manifest = json.loads(
                                        manifest_path.read_text(encoding="utf-8")
                                    )
                                except (OSError, json.JSONDecodeError) as exc:
                                    errors.append(f"cannot read downloaded release manifest: {exc}")
                                if level.name == "certified_100":
                                    native_validation = validate_native_bundle(
                                        Path(raw),
                                        verify_remote_run=True,
                                        require_current_source=True,
                                    )
                                    errors.extend(native_validation.get("errors", []))

    if args.require_release_assets and isinstance(release_manifest, dict):
        errors.extend(
            validate_release_native_bindings(
                release_manifest,
                required_native=level.required_native,
                expected_run=(
                    selected_runs.get("native-runtime.yml")
                    if isinstance(selected_runs.get("native-runtime.yml"), dict)
                    else None
                ),
                expected_repository=repo,
            )
        )

    if level.name == "certified_100" and args.require_release_assets:
        selected_native = selected_runs.get("native-runtime.yml")
        manifest_runs = (
            native_validation.get("github_runs")
            if isinstance(native_validation, dict)
            else None
        )
        manifest_run = (
            manifest_runs.get("native") if isinstance(manifest_runs, dict) else None
        )
        if not isinstance(manifest_run, dict) or not isinstance(selected_native, dict):
            errors.append("certified native bundle cannot be bound to the selected tag run")
        else:
            errors.extend(
                validate_run(
                    manifest_run,
                    kind="native",
                    expected_run=selected_native,
                )
            )

    payload = {
        "schema": SCHEMA,
        "root": str(ROOT),
        "release_level": level.name,
        "repository": repo,
        "head": head,
        "required_event": required_event,
        "required_branch": required_branch,
        "workflows": results,
        "selected_runs": selected_runs,
        "release": release_payload,
        "release_assets_validation": release_assets_validation,
        "release_manifest": release_manifest,
        "native_bundle_validation": native_validation,
        "ok": not errors,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif payload["ok"]:
        print(f"GitHub release checks verified: {level.name}")
    else:
        print("\n".join(errors), file=sys.stderr)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
