#!/usr/bin/env python3
"""Record one native runtime observation with hashed artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from design_craft_evidence_common import sha256_file, skill_provenance, tree_sha256
from design_craft_native_runtime_validate import (
    EVIDENCE_SCHEMA,
    REQUIRED_ARTIFACT_ROLES,
    REQUIRED_ASSERTIONS,
    native_contract_sha256,
    validate_evidence,
)


def parse_assertion(raw: str) -> tuple[str, bool]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("assertion must use name=true|false")
    name, value = raw.split("=", 1)
    normalized = value.strip().lower()
    if not name.strip() or normalized not in {"true", "false"}:
        raise argparse.ArgumentTypeError("assertion must use name=true|false")
    return name.strip(), normalized == "true"


def parse_artifact(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("artifact must use role=path")
    role, path = raw.split("=", 1)
    if not re.fullmatch(r"[a-z][a-z0-9_]*", role.strip()) or not path.strip():
        raise argparse.ArgumentTypeError("artifact must use role=path")
    return role.strip(), path.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=("ios", "android"))
    parser.add_argument(
        "--runtime-kind",
        required=True,
        choices=("ios_simulator", "ios_device", "android_emulator", "android_device"),
    )
    parser.add_argument("--runtime-id", required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--command", action="append", required=True)
    parser.add_argument("--assertion", action="append", type=parse_assertion, required=True)
    parser.add_argument("--artifact", action="append", type=parse_artifact, required=True)
    parser.add_argument("--skill-root", default="skills/design-craft")
    parser.add_argument("--fixture-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    expected_prefix = "ios_" if args.platform == "ios" else "android_"
    if not args.runtime_kind.startswith(expected_prefix):
        parser.error("runtime kind does not match platform")
    assertions = dict(args.assertion)
    if len(assertions) != len(args.assertion):
        parser.error("assertion names must be unique")
    missing_assertions = sorted(REQUIRED_ASSERTIONS[args.runtime_kind] - set(assertions))
    if missing_assertions:
        parser.error(f"missing required assertions: {missing_assertions}")
    if not all(assertions.values()):
        parser.error("refusing to record verified evidence with a failed assertion")

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    skill_root = Path(args.skill_root).expanduser().resolve()
    fixture_root = Path(args.fixture_root).expanduser().resolve()
    if not fixture_root.is_dir():
        parser.error(f"fixture root does not exist: {fixture_root}")
    try:
        provenance = skill_provenance(skill_root)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        parser.error(f"cannot resolve skill provenance: {exc}")
    source_commit = str(provenance.get("skill_source_commit", ""))
    if len(source_commit) != 40:
        parser.error("skill provenance must contain a full source commit")
    artifacts = []
    observed_roles: set[str] = set()
    for role, raw_path in args.artifact:
        if role in observed_roles:
            parser.error(f"artifact role must be unique: {role}")
        observed_roles.add(role)
        path = Path(raw_path).expanduser()
        if not path.is_file():
            parser.error(f"artifact does not exist: {path}")
        try:
            stored_path = str(path.resolve().relative_to(output.parent.resolve()))
        except ValueError:
            parser.error("artifacts must be stored inside the evidence output directory")
        artifacts.append(
            {
                "role": role,
                "path": stored_path,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    missing_roles = sorted(REQUIRED_ARTIFACT_ROLES[args.runtime_kind] - observed_roles)
    if missing_roles:
        parser.error(f"missing required artifact roles: {missing_roles}")

    raw_runtime_id = args.runtime_id.strip()
    if not raw_runtime_id:
        parser.error("runtime-id must be non-empty")
    redacted_runtime_id = "sha256:" + hashlib.sha256(
        raw_runtime_id.encode("utf-8")
    ).hexdigest()

    workflow = None
    if os.environ.get("GITHUB_ACTIONS") == "true":
        required_workflow_env = (
            "GITHUB_REPOSITORY",
            "GITHUB_RUN_ID",
            "GITHUB_RUN_ATTEMPT",
            "GITHUB_EVENT_NAME",
            "GITHUB_SHA",
            "GITHUB_REF",
            "GITHUB_SERVER_URL",
        )
        missing_workflow_env = [
            name for name in required_workflow_env if not os.environ.get(name)
        ]
        if missing_workflow_env:
            parser.error(
                "GitHub runtime evidence is missing workflow identity: "
                + ", ".join(missing_workflow_env)
            )
        workflow = {
            "repository": os.environ["GITHUB_REPOSITORY"],
            "run_id": int(os.environ["GITHUB_RUN_ID"]),
            "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
            "url": (
                f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}"
                f"/actions/runs/{os.environ['GITHUB_RUN_ID']}"
            ),
            "event": os.environ["GITHUB_EVENT_NAME"],
            "head_sha": os.environ["GITHUB_SHA"],
            "ref": os.environ["GITHUB_REF"],
        }

    payload = {
        "schema": EVIDENCE_SCHEMA,
        "platform": args.platform,
        "verified": True,
        "runtime_kind": args.runtime_kind,
        "evidence_level": "runtime_observed",
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_id_kind": "sha256",
        "runtime_id": redacted_runtime_id,
        "tool": args.tool,
        "source_commit": source_commit,
        "source_dirty": provenance.get("skill_source_dirty"),
        "skill_source_dirty": provenance.get("skill_source_dirty"),
        "repo_dirty": provenance.get("repo_dirty"),
        "skill_version": provenance.get("skill_version"),
        "skill_tree_sha256": provenance.get("skill_tree_sha256"),
        "fixture_tree_sha256": tree_sha256(
            fixture_root,
            ignored_dirs={"build", ".gradle"},
        ),
        "contract_sha256": native_contract_sha256(args.platform),
        "capture_context": (
            f"{os.environ.get('GITHUB_SERVER_URL')}/{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/{os.environ.get('GITHUB_RUN_ID')}"
            if os.environ.get("GITHUB_ACTIONS") == "true"
            else "local"
        ),
        "workflow": workflow,
        "commands": args.command,
        "assertions": assertions,
        "artifacts": artifacts,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, errors = validate_evidence(
        output,
        args.platform,
        args.runtime_kind,
        skill_root=skill_root,
        fixture_root=fixture_root.parent,
    )
    if errors:
        output.unlink(missing_ok=True)
        parser.error("generated evidence did not validate: " + "; ".join(errors))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
