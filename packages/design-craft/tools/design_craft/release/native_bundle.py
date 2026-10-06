from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from .github_runs import (
    RUN_KEYS,
    observe_run,
    validate_run,
    validate_workflow_binding,
)
from .integrity import publish_asset_set, repository_head, repository_version, sha256_file
from .native_archive import write_deterministic_tar
from .native_evidence import (
    EVIDENCE_LAYOUT,
    EVIDENCE_SCHEMA,
    ArchiveInspection,
    archive_files,
    copy_evidence,
    evidence_summary,
    inspect_evidence_archive,
    validate_bundle_evidence,
)
from .policy import load_policy


SCHEMA = "design-craft.native-release-bundle.v2"
NATIVE_KEYS = {
    "ios": "ios_simulator",
    "android": "android_emulator",
    "real_device": "physical_device",
}
MANIFEST_KEYS = {
    "schema",
    "version",
    "tag",
    "source_commit",
    "github_runs",
    "bundle",
    "checksum",
    "evidence",
}
RUN_GROUP_KEYS = {"native", "physical_device"}
SUMMARY_KEYS = {
    "path",
    "sha256",
    "schema",
    "platform",
    "runtime_kind",
    "source_commit",
    "contract_sha256",
    "artifact_count",
}


def native_asset_names(version: str | None = None) -> tuple[str, str, str]:
    selected = version or repository_version()
    assets = load_policy()["certified_100"].assets(selected)[4:]
    if len(assets) != 3:
        raise ValueError("certified release policy must define three native assets")
    return assets


def _exact_keys(payload: object, expected: set[str], label: str) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be an object"]
    actual = set(payload)
    return (
        []
        if actual == expected
        else [
            f"{label} fields mismatch expected={sorted(expected)} actual={sorted(actual)}"
        ]
    )


def _evidence_run_binding_errors(
    payloads: dict[str, dict[str, object]],
    *,
    native_run: dict[str, object],
    physical_run: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    for key, payload in payloads.items():
        kind = "physical" if key == "real_device" else "native"
        run = physical_run if kind == "physical" else native_run
        errors.extend(
            validate_workflow_binding(
                payload.get("workflow"),
                run,
                kind=kind,
                label=f"native bundle {key}",
            )
        )
    return errors


def build_native_bundle(
    output_dir: Path,
    native_run: dict[str, object],
    physical_run: dict[str, object],
    *,
    ios_source: Path,
    android_source: Path,
    physical_device_source: Path,
    force: bool,
    require_current_source: bool = True,
) -> dict[str, object]:
    run_errors = validate_run(native_run, kind="native")
    run_errors.extend(validate_run(physical_run, kind="physical"))
    if run_errors:
        raise RuntimeError("; ".join(run_errors))
    version = repository_version()
    bundle_name, checksum_name, manifest_name = native_asset_names(version)
    names = (bundle_name, checksum_name, manifest_name)
    if output_dir.is_symlink():
        raise ValueError(f"native release output directory is unsafe: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".design-craft-native-release-", dir=output_dir.parent
    ) as raw:
        staging = Path(raw)
        evidence_root = staging / "evidence"
        source_payloads = {
            "ios": copy_evidence(
                ios_source,
                evidence_root / EVIDENCE_LAYOUT["ios"][0],
                EVIDENCE_LAYOUT["ios"][1],
            ),
            "android": copy_evidence(
                android_source,
                evidence_root / EVIDENCE_LAYOUT["android"][0],
                EVIDENCE_LAYOUT["android"][1],
            ),
            "real_device": copy_evidence(
                physical_device_source,
                evidence_root / EVIDENCE_LAYOUT["real_device"][0],
                EVIDENCE_LAYOUT["real_device"][1],
            ),
        }
        bundle_path = staging / bundle_name
        write_deterministic_tar(archive_files(evidence_root, source_payloads), bundle_path)
        inspection = inspect_evidence_archive(bundle_path)
        errors = validate_bundle_evidence(
            inspection, require_current_source=require_current_source
        )
        errors.extend(
            _evidence_run_binding_errors(
                inspection.payloads,
                native_run=native_run,
                physical_run=physical_run,
            )
        )
        if errors:
            raise RuntimeError("; ".join(errors))
        if require_current_source:
            for key, payload in inspection.payloads.items():
                selected_run = physical_run if key == "real_device" else native_run
                if payload.get("source_commit") != selected_run.get("head_sha"):
                    raise RuntimeError(
                        f"{key} evidence source_commit must match its selected workflow run"
                    )
                if payload.get("schema") != EVIDENCE_SCHEMA:
                    raise RuntimeError(
                        f"{key} native evidence must use the current evidence schema"
                    )
        digest = inspection.bundle_sha256
        if digest is None:
            raise RuntimeError("native bundle digest is unavailable")
        checksum_path = staging / checksum_name
        checksum_path.write_text(f"{digest}  {bundle_name}\n", encoding="utf-8")
        manifest = {
            "schema": SCHEMA,
            "version": version,
            "tag": f"v{version}",
            "source_commit": repository_head(),
            "github_runs": {
                "native": native_run,
                "physical_device": physical_run,
            },
            "bundle": {
                "path": bundle_name,
                "bytes": bundle_path.stat().st_size,
                "sha256": digest,
            },
            "checksum": {
                "path": checksum_name,
                "sha256": sha256_file(checksum_path),
            },
            "evidence": {
                key: evidence_summary(
                    EVIDENCE_LAYOUT[key][0],
                    EVIDENCE_LAYOUT[key][1],
                    payload,
                    inspection.entries[
                        f"{EVIDENCE_LAYOUT[key][0]}/{EVIDENCE_LAYOUT[key][1]}"
                    ],
                )
                for key, payload in inspection.payloads.items()
            },
        }
        manifest_path = staging / manifest_name
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        staged_validation = validate_native_bundle(
            staging,
            expected_runs={
                "native": native_run,
                "physical_device": physical_run,
            },
            require_current_source=require_current_source,
        )
        if not staged_validation["ok"]:
            raise RuntimeError("; ".join(staged_validation["errors"]))
        published_validation: dict[str, object] = {}

        def validate_published(root: Path) -> None:
            result = validate_native_bundle(
                root,
                expected_runs={
                    "native": native_run,
                    "physical_device": physical_run,
                },
                require_current_source=require_current_source,
            )
            if not result["ok"]:
                raise RuntimeError("; ".join(result["errors"]))
            published_validation.update(result)

        publish_asset_set(
            staging,
            output_dir,
            names,
            force=force,
            validate_published=validate_published,
        )
    return published_validation


def load_native_manifest(output_dir: Path) -> dict[str, object]:
    manifest_path = output_dir / native_asset_names()[2]
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise FileNotFoundError(
            f"native release manifest is missing or unsafe: {manifest_path}"
        )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("native release manifest must contain a JSON object")
    return payload


def _validate_manifest_runs(
    raw_runs: object,
    *,
    expected_runs: dict[str, dict[str, object]] | None,
    verify_remote_run: bool,
) -> tuple[dict[str, dict[str, object]], list[str]]:
    errors = _exact_keys(raw_runs, RUN_GROUP_KEYS, "native release github_runs")
    runs: dict[str, dict[str, object]] = {}
    if not isinstance(raw_runs, dict):
        return runs, errors
    for manifest_key, kind in (("native", "native"), ("physical_device", "physical")):
        run = raw_runs.get(manifest_key)
        label = f"native release github_runs.{manifest_key}"
        errors.extend(_exact_keys(run, RUN_KEYS, label))
        if not isinstance(run, dict):
            continue
        runs[manifest_key] = run
        expected = expected_runs.get(manifest_key) if expected_runs else None
        errors.extend(validate_run(run, kind=kind, expected_run=expected))
        if verify_remote_run:
            try:
                live = observe_run(
                    kind,
                    run.get("id", ""),
                    repository=(
                        run.get("repository")
                        if isinstance(run.get("repository"), str)
                        else None
                    ),
                    require_latest=kind == "native",
                )
            except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
                errors.append(f"cannot verify {kind} GitHub run: {exc}")
            else:
                errors.extend(validate_run(run, kind=kind, expected_run=live))
    return runs, errors


def validate_native_bundle(
    output_dir: Path,
    *,
    expected_runs: dict[str, dict[str, object]] | None = None,
    verify_remote_run: bool = False,
    require_current_source: bool = True,
    outer_manifest: dict[str, object] | None = None,
) -> dict[str, object]:
    version = repository_version()
    bundle_name, checksum_name, manifest_name = native_asset_names(version)
    bundle_path = output_dir / bundle_name
    checksum_path = output_dir / checksum_name
    manifest_path = output_dir / manifest_name
    errors: list[str] = []

    try:
        manifest = load_native_manifest(output_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        manifest = {}
        errors.append(f"invalid native release manifest: {exc}")
    errors.extend(_exact_keys(manifest, MANIFEST_KEYS, "native release manifest"))
    if manifest.get("schema") != SCHEMA:
        errors.append(f"native release manifest schema must be {SCHEMA}")
    if manifest.get("version") != version or manifest.get("tag") != f"v{version}":
        errors.append("native release manifest version/tag must match VERSION")
    if manifest.get("source_commit") != repository_head():
        errors.append("native release manifest source_commit must match current HEAD")
    runs, run_errors = _validate_manifest_runs(
        manifest.get("github_runs"),
        expected_runs=expected_runs,
        verify_remote_run=verify_remote_run,
    )
    errors.extend(run_errors)

    bundle_payload = manifest.get("bundle")
    checksum_payload = manifest.get("checksum")
    errors.extend(_exact_keys(bundle_payload, {"path", "bytes", "sha256"}, "native bundle"))
    errors.extend(_exact_keys(checksum_payload, {"path", "sha256"}, "native checksum"))
    if not isinstance(bundle_payload, dict):
        bundle_payload = {}
    if not isinstance(checksum_payload, dict):
        checksum_payload = {}

    inspection: ArchiveInspection | None = None
    if bundle_path.is_symlink() or not bundle_path.is_file():
        errors.append(f"missing or unsafe native release bundle: {bundle_path}")
    else:
        inspection = inspect_evidence_archive(bundle_path)
        digest = inspection.bundle_sha256
        if bundle_payload.get("path") != bundle_name:
            errors.append("native release bundle path is invalid")
        if bundle_payload.get("bytes") != bundle_path.stat().st_size:
            errors.append("native release bundle byte count is invalid")
        if digest is None or bundle_payload.get("sha256") != digest:
            errors.append("native release bundle hash is invalid")
        errors.extend(
            validate_bundle_evidence(
                inspection, require_current_source=require_current_source
            )
        )
        manifest_evidence = manifest.get("evidence")
        errors.extend(
            _exact_keys(manifest_evidence, set(EVIDENCE_LAYOUT), "native release evidence")
        )
        if isinstance(manifest_evidence, dict) and not inspection.errors:
            for key, payload in inspection.payloads.items():
                summary = manifest_evidence.get(key)
                errors.extend(
                    _exact_keys(summary, SUMMARY_KEYS, f"native release evidence.{key}")
                )
                member_name = f"{EVIDENCE_LAYOUT[key][0]}/{EVIDENCE_LAYOUT[key][1]}"
                expected = evidence_summary(
                    EVIDENCE_LAYOUT[key][0],
                    EVIDENCE_LAYOUT[key][1],
                    payload,
                    inspection.entries[member_name],
                )
                if summary != expected:
                    errors.append(f"native release manifest evidence.{key} is invalid")
            if set(runs) == RUN_GROUP_KEYS:
                errors.extend(
                    _evidence_run_binding_errors(
                        inspection.payloads,
                        native_run=runs["native"],
                        physical_run=runs["physical_device"],
                    )
                )
            if outer_manifest is not None:
                errors.extend(
                    validate_outer_native_bindings(
                        outer_manifest,
                        manifest,
                        inspection.payloads,
                    )
                )

    if checksum_path.is_symlink() or not checksum_path.is_file():
        errors.append(f"missing or unsafe native release checksum: {checksum_path}")
    elif inspection is not None and inspection.bundle_sha256 is not None:
        digest = inspection.bundle_sha256
        if checksum_path.read_text(encoding="utf-8") != f"{digest}  {bundle_name}\n":
            errors.append("native release checksum does not match the bundle")
        if checksum_payload.get("path") != checksum_name:
            errors.append("native release checksum path is invalid")
        if checksum_payload.get("sha256") != sha256_file(checksum_path):
            errors.append("native release checksum metadata is invalid")
    return {
        "schema": SCHEMA,
        "root": str(output_dir),
        "version": version,
        "github_runs": runs,
        "assets": [str(bundle_path), str(checksum_path), str(manifest_path)],
        "ok": not errors,
        "errors": errors,
    }


def validate_outer_native_bindings(
    outer_manifest: dict[str, object],
    inner_manifest: dict[str, object],
    evidence_payloads: dict[str, dict[str, object]],
) -> list[str]:
    errors: list[str] = []
    outer_evidence = outer_manifest.get("native_evidence")
    inner_evidence = inner_manifest.get("evidence")
    if not isinstance(outer_evidence, dict) or not isinstance(inner_evidence, dict):
        return ["release manifests must contain native evidence bindings"]
    for inner_key, outer_key in NATIVE_KEYS.items():
        outer = outer_evidence.get(outer_key)
        inner = inner_evidence.get(inner_key)
        evidence = evidence_payloads.get(inner_key)
        if not isinstance(outer, dict) or not isinstance(inner, dict):
            errors.append(f"release native evidence binding is missing: {outer_key}")
            continue
        if not isinstance(evidence, dict):
            errors.append(f"inner native evidence payload is missing: {inner_key}")
            continue
        comparisons = {
            "evidence_sha256": "sha256",
            "schema": "schema",
            "platform": "platform",
            "runtime_kind": "runtime_kind",
            "source_commit": "source_commit",
            "contract_sha256": "contract_sha256",
        }
        for outer_field, inner_field in comparisons.items():
            if outer.get(outer_field) != inner.get(inner_field):
                errors.append(
                    f"outer native_evidence.{outer_key}.{outer_field} does not match "
                    f"inner evidence.{inner_key}.{inner_field}"
                )
        if outer.get("native") != outer_key:
            errors.append(f"outer native_evidence.{outer_key}.native is invalid")
        for field in ("schema", "platform", "runtime_kind", "source_commit", "contract_sha256", "observed_at", "workflow", "artifacts"):
            if outer.get(field) != evidence.get(field):
                errors.append(
                    f"outer native_evidence.{outer_key}.{field} does not match "
                    f"archived evidence.{inner_key}.{field}"
                )
        artifacts = evidence.get("artifacts")
        if not isinstance(artifacts, list) or len(artifacts) != inner.get("artifact_count"):
            errors.append(
                f"archived evidence.{inner_key}.artifacts does not match "
                f"inner evidence.{inner_key}.artifact_count"
            )
    if outer_manifest.get("source_commit") != inner_manifest.get("source_commit"):
        errors.append("outer and inner native release source_commit values do not match")
    return errors


__all__ = [
    "SCHEMA",
    "build_native_bundle",
    "load_native_manifest",
    "native_asset_names",
    "validate_native_bundle",
    "validate_outer_native_bindings",
]
