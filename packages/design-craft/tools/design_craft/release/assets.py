from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

from ..repo import REPO_ROOT
from .evidence import REPORT_SCHEMA
from .integrity import publish_asset_set
from .integrity import repository_head as _head
from .integrity import repository_version as _version
from .integrity import sha256_file as _sha256
from .native_bundle import (
    validate_native_bundle,
)
from .policy import ReleaseLevel
from .sbom import write_spdx


MANIFEST_SCHEMA = "design-craft.release-assets.v2"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _is_commit(value: object) -> bool:
    return isinstance(value, str) and COMMIT_RE.fullmatch(value) is not None


def _safe_file(path: Path) -> bool:
    return not path.is_symlink() and path.is_file()


def load_release_evidence(path: Path, level: ReleaseLevel) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != REPORT_SCHEMA:
        raise ValueError(f"release evidence must use {REPORT_SCHEMA}")
    if payload.get("release_level") != level.name or payload.get("ok") is not True:
        raise ValueError("release evidence must pass for the requested release level")
    if payload.get("phase") != "final":
        raise ValueError("release assets require final-phase release evidence")
    if not _is_commit(payload.get("source_commit")) or payload.get("source_commit") != _head():
        raise ValueError("release evidence source_commit must match current HEAD")
    if set(payload.get("verified_hosts", [])) != set(level.required_hosts):
        raise ValueError("release evidence verified_hosts must match the release policy")
    if set(payload.get("verified_native", [])) != set(level.required_native):
        raise ValueError("release evidence verified_native must match the release policy")
    unverified = payload.get("unverified")
    if not isinstance(unverified, dict) or set(unverified) != set(level.allowed_unverified):
        raise ValueError("release evidence unverified targets must match the release policy")
    expected_retention = (
        "self_contained_native_release_bundle"
        if level.permanent_native_bundle
        else "workflow_artifact_90_days"
    )
    if payload.get("evidence_retention") != expected_retention:
        raise ValueError("release evidence retention must match the release policy")
    checks = payload.get("checks")
    if not isinstance(checks, list) or not all(isinstance(item, dict) for item in checks):
        raise ValueError("release evidence checks must be an array of objects")
    check_by_id = {
        item.get("id"): item
        for item in checks
        if isinstance(item.get("id"), str)
    }
    if len(check_by_id) != len(checks):
        raise ValueError("release evidence check ids must be unique non-empty strings")
    required_checks = {
        *level.required_domains,
        *(f"host_{host}_current_source" for host in level.required_hosts),
        *(f"native_{native}_current_source" for native in level.required_native),
    }
    failed = sorted(
        check_id
        for check_id in required_checks
        if check_by_id.get(check_id, {}).get("status") != "passed"
    )
    if failed:
        raise ValueError("release evidence is missing passing checks: " + ", ".join(failed))
    return payload


def _resolve_evidence_path(
    binding: dict[str, object],
    *,
    evidence_root: Path | None,
    check_id: str,
) -> Path:
    raw_path = binding.get("evidence_path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError(f"passing release evidence is missing {check_id}.evidence_path")
    relative_path = Path(raw_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"{check_id}.evidence_path must stay relative to its evidence root")

    if evidence_root is not None:
        root = evidence_root.expanduser().resolve()
        resolved = (root / relative_path).resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError(f"{check_id}.evidence_path escapes its evidence root")
        return resolved

    legacy_source = binding.get("evidence_source_path")
    if isinstance(legacy_source, str) and legacy_source:
        resolved = Path(legacy_source).expanduser()
        if not resolved.is_absolute():
            resolved = REPO_ROOT / resolved
        return resolved.resolve()

    resolved = (REPO_ROOT / relative_path).resolve()
    if resolved != REPO_ROOT and REPO_ROOT not in resolved.parents:
        raise ValueError(f"{check_id}.evidence_path escapes the repository root")
    return resolved


def collect_native_evidence(
    evidence: dict[str, object],
    level: ReleaseLevel,
    *,
    evidence_root: Path | None = None,
) -> dict[str, dict[str, object]]:
    checks = evidence.get("checks")
    if not isinstance(checks, list):
        raise ValueError("release evidence checks must be an array")
    native_evidence: dict[str, dict[str, object]] = {}
    for native in level.required_native:
        check_id = f"native_{native}_current_source"
        check = next(
            (item for item in checks if isinstance(item, dict) and item.get("id") == check_id),
            None,
        )
        if not isinstance(check, dict) or check.get("status") != "passed":
            raise ValueError(f"passing release evidence is missing {check_id}")
        binding = check.get("evidence")
        if not isinstance(binding, dict):
            raise ValueError(f"passing release evidence has invalid {check_id} binding")
        resolved = _resolve_evidence_path(
            binding,
            evidence_root=evidence_root,
            check_id=check_id,
        )
        if not resolved.is_file() or _sha256(resolved) != binding.get("evidence_sha256"):
            raise ValueError(
                f"{check_id} evidence file digest does not match the release report"
            )
        try:
            record = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"{check_id} evidence file is invalid: {exc}") from exc
        for field in (
            "schema",
            "source_commit",
            "platform",
            "runtime_kind",
            "contract_sha256",
            "observed_at",
            "workflow",
            "artifacts",
        ):
            if record.get(field) != binding.get(field):
                raise ValueError(
                    f"{check_id} evidence file does not match its {field} binding"
                )
        native_evidence[native] = {
            key: value for key, value in binding.items() if key != "evidence_source_path"
        }
    return native_evidence


def _npm_pack(destination: Path) -> tuple[Path, dict[str, object]]:
    validation = subprocess.run(
        [
            "python3",
            "scripts/design_craft_package_validate.py",
            "--validate",
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if validation.returncode != 0:
        raise RuntimeError(validation.stderr.strip() or validation.stdout.strip())
    result = subprocess.run(
        [
            "npm",
            "pack",
            "--json",
            "--ignore-scripts",
            "--pack-destination",
            str(destination),
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "npm pack failed")
    payload = json.loads(result.stdout)
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        raise ValueError("npm pack must return one package record")
    package = destination / str(payload[0].get("filename", ""))
    if not package.is_file():
        raise FileNotFoundError("npm pack output is missing")
    return package, payload[0]


def build_assets(
    output_dir: Path,
    *,
    level: ReleaseLevel,
    evidence_path: Path,
    evidence_root: Path | None = None,
    force: bool = False,
) -> dict[str, object]:
    version = _version()
    expected = level.assets(version)
    generated_names = expected[:4]
    evidence = load_release_evidence(evidence_path, level)
    native_evidence = collect_native_evidence(
        evidence,
        level,
        evidence_root=evidence_root,
    )
    if output_dir.is_symlink():
        raise ValueError(f"release output directory is unsafe: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    unexpected = sorted(
        path.name
        for path in output_dir.iterdir()
        if path.name not in expected
    )
    if unexpected:
        raise ValueError("release output contains unexpected entries: " + ", ".join(unexpected))
    existing = [
        output_dir / name
        for name in generated_names
        if (output_dir / name).exists() or (output_dir / name).is_symlink()
    ]
    if existing and not force:
        raise FileExistsError("release assets already exist: " + ", ".join(map(str, existing)))
    package_name, checksum_name, manifest_name, sbom_name = expected[:4]
    with tempfile.TemporaryDirectory(
        prefix=".design-craft-assets-", dir=output_dir.parent
    ) as raw:
        staging = Path(raw)
        packed, pack_record = _npm_pack(staging)
        package_path = staging / package_name
        packed.replace(package_path)
        package_digest = _sha256(package_path)
        checksum_path = staging / checksum_name
        checksum_path.write_text(f"{package_digest}  {package_name}\n", encoding="utf-8")
        sbom_path = staging / sbom_name
        write_spdx(
            package_path,
            sbom_path,
            version=version,
            source_commit=str(evidence["source_commit"]),
        )

        native_assets: list[dict[str, object]] = []
        for name in expected[4:]:
            source = output_dir / name
            if source.is_symlink() or not source.is_file():
                raise FileNotFoundError(f"certified native asset is missing or unsafe: {source}")
            target = staging / name
            target.write_bytes(source.read_bytes())
            native_assets.append(
                {"path": name, "bytes": target.stat().st_size, "sha256": _sha256(target)}
            )

        performance_check = next(
            check
            for check in evidence["checks"]
            if check.get("id") == "performance_regression"
        )
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "version": version,
            "tag": f"v{version}",
            "release_level": level.name,
            "source_commit": evidence["source_commit"],
            "verified_hosts": evidence["verified_hosts"],
            "verified_native": evidence["verified_native"],
            "unverified": evidence["unverified"],
            "benchmark_status": performance_check["status"],
            "evidence_retention": evidence["evidence_retention"],
            "native_evidence": native_evidence,
            "package": {
                "path": package_name,
                "bytes": package_path.stat().st_size,
                "sha256": package_digest,
                "entry_count": pack_record.get("entryCount"),
                "unpacked_bytes": pack_record.get("unpackedSize"),
            },
            "checksum": {"path": checksum_name, "sha256": _sha256(checksum_path)},
            "sbom": {"path": sbom_name, "sha256": _sha256(sbom_path)},
            "native_assets": native_assets,
        }
        (staging / manifest_name).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        staged_validation = validate_assets(staging, level=level)
        if not staged_validation["ok"]:
            raise RuntimeError("; ".join(staged_validation["errors"]))
        published_validation: dict[str, object] = {}

        def validate_published(root: Path) -> None:
            result = validate_assets(root, level=level)
            if not result["ok"]:
                raise RuntimeError("; ".join(result["errors"]))
            published_validation.update(result)

        publish_asset_set(
            staging,
            output_dir,
            expected,
            force=True,
            validate_published=validate_published,
        )
    return published_validation


def validate_assets(output_dir: Path, *, level: ReleaseLevel) -> dict[str, object]:
    version = _version()
    expected = level.assets(version)
    errors: list[str] = []
    if output_dir.is_symlink() or not output_dir.is_dir():
        entries: tuple[Path, ...] = ()
        errors.append(f"release asset directory is missing or unsafe: {output_dir}")
    else:
        entries = tuple(output_dir.iterdir())
    actual = tuple(sorted(path.name for path in entries))
    if set(actual) != set(expected):
        errors.append(f"asset set mismatch expected={sorted(expected)} actual={sorted(actual)}")
    unsafe = sorted(
        path.name
        for path in entries
        if path.name not in expected or not _safe_file(path)
    )
    if unsafe:
        errors.append("release asset entries are unexpected or unsafe: " + ", ".join(unsafe))
    package_name, checksum_name, manifest_name, sbom_name = expected[:4]
    package_path = output_dir / package_name
    checksum_path = output_dir / checksum_name
    manifest_path = output_dir / manifest_name
    sbom_path = output_dir / sbom_name
    try:
        if not _safe_file(manifest_path):
            raise OSError("manifest is missing or unsafe")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        manifest = {}
        errors.append(f"invalid release manifest: {exc}")
    if manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("release_level") != level.name:
        errors.append("release manifest schema or release_level is invalid")
    if manifest.get("version") != version or manifest.get("tag") != f"v{version}":
        errors.append("release manifest version or tag is invalid")
    if not _is_commit(manifest.get("source_commit")) or manifest.get("source_commit") != _head():
        errors.append("release manifest source_commit must match HEAD")
    if set(manifest.get("verified_hosts", [])) != set(level.required_hosts):
        errors.append("release manifest verified_hosts must match the release policy")
    if set(manifest.get("verified_native", [])) != set(level.required_native):
        errors.append("release manifest verified_native must match the release policy")
    unverified = manifest.get("unverified")
    if not isinstance(unverified, dict) or set(unverified) != set(level.allowed_unverified):
        errors.append("release manifest unverified targets must match the release policy")
    if manifest.get("benchmark_status") != "passed":
        errors.append("release manifest benchmark_status must be passed")
    expected_retention = (
        "self_contained_native_release_bundle"
        if level.permanent_native_bundle
        else "workflow_artifact_90_days"
    )
    if manifest.get("evidence_retention") != expected_retention:
        errors.append("release manifest evidence_retention is invalid")
    native_evidence = manifest.get("native_evidence")
    if not isinstance(native_evidence, dict) or set(native_evidence) != set(level.required_native):
        errors.append("release manifest native_evidence must cover every required target")
    else:
        for native, binding in native_evidence.items():
            if not isinstance(binding, dict):
                errors.append(f"release manifest native_evidence.{native} must be an object")
                continue
            if not isinstance(binding.get("evidence_path"), str):
                errors.append(f"release manifest native_evidence.{native}.evidence_path is required")
            if not _is_sha256(binding.get("evidence_sha256")):
                errors.append(f"release manifest native_evidence.{native}.evidence_sha256 is invalid")
            if binding.get("source_commit") != manifest.get("source_commit"):
                errors.append(f"release manifest native_evidence.{native}.source_commit mismatch")
            artifacts = binding.get("artifacts")
            if not isinstance(artifacts, list) or not artifacts:
                errors.append(f"release manifest native_evidence.{native}.artifacts are required")
            else:
                for index, artifact in enumerate(artifacts):
                    label = f"release manifest native_evidence.{native}.artifacts[{index}]"
                    if not isinstance(artifact, dict):
                        errors.append(f"{label} must be an object")
                        continue
                    if not isinstance(artifact.get("role"), str) or not artifact["role"]:
                        errors.append(f"{label}.role is invalid")
                    if not isinstance(artifact.get("path"), str) or not artifact["path"]:
                        errors.append(f"{label}.path is invalid")
                    if not isinstance(artifact.get("bytes"), int) or artifact["bytes"] < 0:
                        errors.append(f"{label}.bytes is invalid")
                    if not _is_sha256(artifact.get("sha256")):
                        errors.append(f"{label}.sha256 is invalid")
            workflow = binding.get("workflow")
            if not isinstance(workflow, dict):
                errors.append(f"release manifest native_evidence.{native}.workflow is required")
            else:
                prefix = f"release manifest native_evidence.{native}.workflow"
                if workflow.get("head_sha") != manifest.get("source_commit"):
                    errors.append(f"{prefix} head mismatch")
                if not isinstance(workflow.get("repository"), str) or not workflow["repository"]:
                    errors.append(f"{prefix}.repository is invalid")
                if not isinstance(workflow.get("run_id"), int) or workflow["run_id"] <= 0:
                    errors.append(f"{prefix}.run_id is invalid")
                if not isinstance(workflow.get("run_attempt"), int) or workflow["run_attempt"] <= 0:
                    errors.append(f"{prefix}.run_attempt is invalid")
                if workflow.get("event") not in {"workflow_dispatch", "push"}:
                    errors.append(f"{prefix}.event is invalid")
                if not isinstance(workflow.get("ref"), str) or not workflow["ref"].startswith("refs/"):
                    errors.append(f"{prefix}.ref is invalid")
                url = workflow.get("url")
                if not isinstance(url, str) or f"/actions/runs/{workflow.get('run_id')}" not in url:
                    errors.append(f"{prefix}.url is invalid")
    if _safe_file(package_path):
        digest = _sha256(package_path)
        package_payload = manifest.get("package")
        if not isinstance(package_payload, dict) or package_payload.get("sha256") != digest:
            errors.append("release package digest mismatch")
        elif (
            package_payload.get("path") != package_name
            or package_payload.get("bytes") != package_path.stat().st_size
        ):
            errors.append("release package path or size mismatch")
        if _safe_file(checksum_path) and checksum_path.read_text(encoding="utf-8") != f"{digest}  {package_name}\n":
            errors.append("release checksum content mismatch")
        checksum_payload = manifest.get("checksum")
        if _safe_file(checksum_path) and (
            not isinstance(checksum_payload, dict)
            or checksum_payload.get("path") != checksum_name
            or checksum_payload.get("sha256") != _sha256(checksum_path)
        ):
            errors.append("release manifest checksum metadata mismatch")
    if _safe_file(sbom_path):
        try:
            sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid SPDX JSON: {exc}")
        else:
            packages = sbom.get("packages") if isinstance(sbom, dict) else None
            package = packages[0] if isinstance(packages, list) and packages and isinstance(packages[0], dict) else {}
            checksums = package.get("checksums", [])
            sbom_digest = next(
                (item.get("checksumValue") for item in checksums if item.get("algorithm") == "SHA256"),
                None,
            )
            if _safe_file(package_path) and sbom_digest != _sha256(package_path):
                errors.append("SBOM package digest mismatch")
            sbom_payload = manifest.get("sbom")
            if (
                not isinstance(sbom_payload, dict)
                or sbom_payload.get("path") != sbom_name
                or sbom_payload.get("sha256") != _sha256(sbom_path)
            ):
                errors.append("release manifest SBOM digest mismatch")
    native_assets = manifest.get("native_assets")
    expected_native_names = expected[4:]
    if not isinstance(native_assets, list) or len(native_assets) != len(expected_native_names):
        errors.append("release manifest native_assets must match the release policy")
    else:
        indexed = {
            item.get("path"): item
            for item in native_assets
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
        if set(indexed) != set(expected_native_names):
            errors.append("release manifest native asset paths must match the release policy")
        for name in expected_native_names:
            path = output_dir / name
            item = indexed.get(name)
            if not _safe_file(path) or not isinstance(item, dict):
                continue
            if item.get("bytes") != path.stat().st_size or item.get("sha256") != _sha256(path):
                errors.append(f"release native asset metadata mismatch: {name}")
    if level.permanent_native_bundle:
        native_validation = validate_native_bundle(
            output_dir,
            require_current_source=True,
            outer_manifest=manifest,
        )
        errors.extend(native_validation["errors"])
    return {
        "schema": MANIFEST_SCHEMA,
        "release_level": level.name,
        "assets": list(expected),
        "ok": not errors,
        "errors": errors,
    }


__all__ = [
    "build_assets",
    "collect_native_evidence",
    "load_release_evidence",
    "validate_assets",
]
