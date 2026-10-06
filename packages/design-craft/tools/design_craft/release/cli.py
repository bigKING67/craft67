from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from .evidence import evaluate_release
from .github_runs import (
    ARTIFACT_OBSERVATION_SCHEMA,
    OBSERVATION_SCHEMA,
    artifact_observation_document,
    load_observation,
    observation_document,
    observe_artifact,
    observe_run,
)
from .integrity import repository_head, repository_version
from .native_bundle import build_native_bundle, validate_native_bundle
from .policy import load_policy
from .assets import build_assets, validate_assets
from .certification import (
    SCHEMA as CERTIFICATION_SCHEMA,
    build_certification_bundle,
    validate_certification_bundle,
)
from .run_bindings import validate_release_run_bindings
from .sbom import write_spdx


def run_release(args: Namespace) -> int:
    levels = load_policy()
    if args.release_command == "run-observation":
        output = Path(args.output).expanduser().absolute()
        try:
            run = observe_run(
                args.kind,
                args.run_id,
                repository=args.repository,
                require_latest=args.kind == "native",
            )
            payload = observation_document(args.kind, run)
            if output.exists() or output.is_symlink():
                raise ValueError(
                    f"run observation output already exists or is unsafe: {output}"
                )
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            payload = {
                "schema": OBSERVATION_SCHEMA,
                "kind": args.kind,
                "ok": False,
                "errors": [str(exc)],
            }
        else:
            payload = {**payload, "output": str(output), "ok": True, "errors": []}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif payload["ok"]:
            print(f"GitHub {args.kind} run observation written: {output}")
        else:
            print("\n".join(payload["errors"]), file=sys.stderr)
        return 0 if payload["ok"] else 1
    if args.release_command == "artifact-observation":
        output = Path(args.output).expanduser().absolute()
        try:
            certification_run = load_observation(
                Path(args.certification_observation).expanduser().absolute(),
                expected_kind="certification",
            )
            artifact = observe_artifact(
                args.artifact_id,
                run=certification_run,
                expected_name=args.expected_name,
            )
            payload = artifact_observation_document(
                artifact,
                repository=str(certification_run["repository"]),
            )
            if output.exists() or output.is_symlink():
                raise ValueError(
                    f"artifact observation output already exists or is unsafe: {output}"
                )
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            payload = {
                "schema": ARTIFACT_OBSERVATION_SCHEMA,
                "ok": False,
                "errors": [str(exc)],
            }
        else:
            payload = {**payload, "output": str(output), "ok": True, "errors": []}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif payload["ok"]:
            print(f"GitHub artifact observation written: {output}")
        else:
            print("\n".join(payload["errors"]), file=sys.stderr)
        return 0 if payload["ok"] else 1
    if args.release_command == "evidence-bindings":
        level = levels[args.level]
        evidence = Path(args.evidence).expanduser().absolute()
        try:
            native_run = load_observation(
                Path(args.native_observation).expanduser().absolute(),
                expected_kind="native",
            )
            benchmark_run = load_observation(
                Path(args.benchmark_observation).expanduser().absolute(),
                expected_kind="benchmark",
            )
            physical_run = (
                load_observation(
                    Path(args.physical_observation).expanduser().absolute(),
                    expected_kind="physical",
                )
                if args.physical_observation
                else None
            )
            if level.name == "certified_100" and physical_run is None:
                raise ValueError(
                    "--physical-observation is required for certified_100 evidence"
                )
            if level.name == "operational_95" and physical_run is not None:
                raise ValueError(
                    "--physical-observation is not allowed for operational_95 evidence"
                )
            payload = validate_release_run_bindings(
                evidence,
                level=level,
                native_run=native_run,
                benchmark_run=benchmark_run,
                benchmark_result_path=Path(args.benchmark_result).expanduser().resolve(),
                physical_run=physical_run,
                evidence_root=Path(args.evidence_root).expanduser().resolve(),
            )
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            payload = {
                "schema": "design-craft.release-run-bindings.v1",
                "release_level": level.name,
                "ok": False,
                "errors": [str(exc)],
            }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif payload["ok"]:
            print(f"release evidence run bindings verified: {level.name}")
        else:
            print("\n".join(payload["errors"]), file=sys.stderr)
        return 0 if payload["ok"] else 1
    if args.release_command == "certification":
        level = levels[args.level]
        try:
            if args.certification_command == "build":
                if level.name == "certified_100" and not args.physical_observation:
                    raise ValueError(
                        "--physical-observation is required for certified_100 certification"
                    )
                if level.name == "operational_95" and args.physical_observation:
                    raise ValueError(
                        "--physical-observation is not allowed for operational_95 certification"
                    )
                payload = build_certification_bundle(
                    Path(args.output_dir).expanduser().resolve(),
                    level=level,
                    tag=args.tag,
                    evidence_path=Path(args.evidence).expanduser().resolve(),
                    evidence_root=Path(args.evidence_root).expanduser().resolve(),
                    native_observation=Path(args.native_observation).expanduser().resolve(),
                    benchmark_observation=Path(
                        args.benchmark_observation
                    ).expanduser().resolve(),
                    benchmark_result=Path(args.benchmark_result).expanduser().resolve(),
                    physical_observation=(
                        Path(args.physical_observation).expanduser().resolve()
                        if args.physical_observation
                        else None
                    ),
                    assets_dir=Path(args.assets_dir).expanduser().resolve(),
                    repository=args.repository,
                    workflow_run_id=args.workflow_run_id,
                    workflow_run_attempt=args.workflow_run_attempt,
                )
            else:
                payload = validate_certification_bundle(
                    Path(args.input_dir).expanduser().resolve(),
                    level=level,
                    certification_observation=(
                        Path(args.certification_observation).expanduser().resolve()
                        if args.certification_observation
                        else None
                    ),
                    artifact_observation=(
                        Path(args.artifact_observation).expanduser().resolve()
                        if args.artifact_observation
                        else None
                    ),
                    expected_artifact_id=args.artifact_id,
                    expected_artifact_digest=args.artifact_digest,
                )
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            payload = {
                "schema": CERTIFICATION_SCHEMA,
                "release_level": level.name,
                "ok": False,
                "errors": [str(exc)],
            }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif payload["ok"]:
            print(f"release certification bundle verified: {level.name}")
        else:
            print("\n".join(payload["errors"]), file=sys.stderr)
        return 0 if payload["ok"] else 1
    if args.release_command == "native-bundle":
        output_dir = Path(args.output_dir).expanduser().absolute()
        try:
            if args.native_bundle_command == "build":
                native_run = load_observation(
                    Path(args.native_observation).expanduser().absolute(),
                    expected_kind="native",
                )
                physical_run = load_observation(
                    Path(args.physical_observation).expanduser().absolute(),
                    expected_kind="physical",
                )
                payload = build_native_bundle(
                    output_dir,
                    native_run,
                    physical_run,
                    ios_source=Path(args.ios_source).expanduser().absolute(),
                    android_source=Path(args.android_source).expanduser().absolute(),
                    physical_device_source=Path(
                        args.physical_device_source
                    ).expanduser().absolute(),
                    force=args.force,
                    require_current_source=True,
                )
            else:
                payload = validate_native_bundle(
                    output_dir,
                    verify_remote_run=args.verify_run,
                    require_current_source=True,
                )
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            payload = {
                "schema": "design-craft.native-release-bundle.v2",
                "root": str(output_dir),
                "version": repository_version(),
                "ok": False,
                "errors": [str(exc)],
            }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif payload["ok"]:
            print("native release bundle verified: " + ", ".join(payload["assets"]))
        else:
            print("\n".join(payload["errors"]), file=sys.stderr)
        return 0 if payload["ok"] else 1
    if args.release_command == "assets":
        level = levels[args.level]
        output_dir = Path(args.output_dir).expanduser().resolve()
        try:
            if args.build:
                if not args.evidence:
                    raise ValueError("--evidence is required when building release assets")
                payload = build_assets(
                    output_dir,
                    level=level,
                    evidence_path=Path(args.evidence).expanduser().resolve(),
                    evidence_root=(
                        Path(args.evidence_root).expanduser().resolve()
                        if args.evidence_root
                        else None
                    ),
                    force=args.force,
                )
            else:
                payload = validate_assets(output_dir, level=level)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            payload = {
                "schema": "design-craft.release-assets.v2",
                "release_level": level.name,
                "ok": False,
                "errors": [str(exc)],
            }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif payload["ok"]:
            print(f"release assets verified: {level.name}")
        else:
            print("\n".join(payload["errors"]))
        return 0 if payload["ok"] else 1
    if args.release_command == "sbom":
        version = repository_version()
        source_commit = repository_head()
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = write_spdx(
            Path(args.package).expanduser().resolve(),
            output,
            version=version,
            source_commit=source_commit,
        )
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"SPDX SBOM written: {output}")
        return 0
    payload = evaluate_release(
        levels[args.level],
        baseline_path=Path(args.baseline).expanduser().resolve() if args.baseline else None,
        benchmark_result_path=(
            Path(args.benchmark_result).expanduser().resolve()
            if args.benchmark_result
            else None
        ),
        benchmark_observation_path=(
            Path(args.benchmark_observation).expanduser().resolve()
            if args.benchmark_observation
            else None
        ),
        phase=args.phase,
    )
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"release {args.level} {args.phase}: {'ready' if payload['ok'] else 'not ready'}")
        for check in payload["checks"]:
            print(f"{'+' if check['status'] == 'passed' else '-'} {check['id']}: {check['status']}")
    return 0 if payload["ok"] else 1
