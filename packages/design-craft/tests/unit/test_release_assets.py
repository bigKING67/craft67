from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.fixtures.benchmark import full_benchmark_result
from tools.design_craft.release.assets import (
    build_assets,
    load_release_evidence,
    validate_assets,
)
from tools.design_craft.release.integrity import publish_asset_set
from tools.design_craft.release.integrity import repository_version
from tools.design_craft.release.policy import ReleaseLevel, load_policy
from tools.design_craft.release.run_bindings import validate_release_run_bindings
from tools.design_craft.release.sbom import write_spdx
from tools.design_craft.repo import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from design_craft_github_checks import validate_release_native_bindings  # noqa: E402


VERSION = repository_version()
HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def workflow(*, physical: bool = False) -> dict[str, object]:
    run_id = 456 if physical else 123
    return {
        "repository": "bigKING67/design-craft",
        "run_id": run_id,
        "run_attempt": 1,
        "url": f"https://github.com/bigKING67/design-craft/actions/runs/{run_id}",
        "event": "workflow_dispatch" if physical else "push",
        "head_sha": HEAD,
        "ref": "refs/heads/main" if physical else f"refs/tags/v{VERSION}",
    }


def selected_workflow_run() -> dict[str, object]:
    return {
        "databaseId": 123,
        "attempt": 1,
        "status": "completed",
        "conclusion": "success",
        "headSha": HEAD,
        "headBranch": f"v{VERSION}",
        "event": "push",
        "createdAt": "2026-07-23T00:00:00Z",
        "url": "https://github.com/bigKING67/design-craft/actions/runs/123",
    }


def native_run_observation(run_id: int = 123) -> dict[str, object]:
    return {
        "id": run_id,
        "attempt": 1,
        "workflow": ".github/workflows/native-runtime.yml",
        "workflow_name": "Native runtime evidence",
        "event": "push",
        "head_branch": f"v{VERSION}",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/bigKING67/design-craft/actions/runs/{run_id}",
        "repository": "bigKING67/design-craft",
    }


def benchmark_run_observation(run_id: int = 456) -> dict[str, object]:
    return {
        "id": run_id,
        "attempt": 1,
        "workflow": ".github/workflows/benchmark.yml",
        "workflow_name": "Performance benchmark",
        "event": "workflow_dispatch",
        "head_branch": f"v{VERSION}",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/bigKING67/design-craft/actions/runs/{run_id}",
        "repository": "bigKING67/design-craft",
    }


def write_benchmark_result(path: Path) -> None:
    payload = full_benchmark_result(100.0)
    payload["source_commit"] = HEAD
    payload["source_dirty"] = False
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def attach_benchmark_binding(
    payload: dict[str, object],
    benchmark_result: Path,
    *,
    run_id: int = 456,
) -> None:
    checks = payload["checks"]
    for check in checks:
        if check["id"] == "performance_regression":
            check["evidence"] = {
                "source_commit": HEAD,
                "benchmark_result_sha256": sha256(benchmark_result),
                "workflow": {
                    "repository": "bigKING67/design-craft",
                    "run_id": run_id,
                    "run_attempt": 1,
                    "url": (
                        "https://github.com/bigKING67/design-craft/actions/runs/"
                        f"{run_id}"
                    ),
                    "event": "workflow_dispatch",
                    "head_sha": HEAD,
                    "ref": f"refs/tags/v{VERSION}",
                },
            }
            return
    raise AssertionError("release evidence is missing performance_regression")


def native_binding(native: str) -> dict[str, object]:
    return {
        "native": native,
        "schema": "design-craft.native-runtime-evidence.v3",
        "evidence_path": f"{native}-observed.json",
        "evidence_sha256": "b" * 64,
        "source_commit": HEAD,
        "platform": "ios" if native == "ios_simulator" else "android",
        "runtime_kind": (
            "android_device" if native == "physical_device" else native
        ),
        "contract_sha256": "d" * 64,
        "observed_at": "2026-07-23T00:00:00Z",
        "workflow": workflow(physical=native == "physical_device"),
        "artifacts": [
            {
                "role": "after_screenshot",
                "path": f"{native}.png",
                "bytes": 3,
                "sha256": "c" * 64,
            }
        ],
    }


def write_assets(root: Path, level: ReleaseLevel) -> Path:
    expected = level.assets(VERSION)
    package_name, checksum_name, manifest_name, sbom_name = expected[:4]
    package = root / package_name
    content = b"0.5.0\n"
    info = tarfile.TarInfo("package/VERSION")
    info.size = len(content)
    info.mtime = 0
    with tarfile.open(package, "w:gz") as archive:
        archive.addfile(info, io.BytesIO(content))
    digest = sha256(package)
    checksum = root / checksum_name
    checksum.write_text(f"{digest}  {package_name}\n", encoding="utf-8")
    sbom = root / sbom_name
    write_spdx(package, sbom, version=VERSION, source_commit=HEAD)
    native_assets = []
    for name in expected[4:]:
        path = root / name
        path.write_bytes(name.encode("utf-8"))
        native_assets.append(
            {"path": name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        )
    manifest = {
        "schema": "design-craft.release-assets.v2",
        "version": VERSION,
        "tag": f"v{VERSION}",
        "release_level": level.name,
        "source_commit": HEAD,
        "verified_hosts": list(level.required_hosts),
        "verified_native": list(level.required_native),
        "unverified": {name: "unverified" for name in level.allowed_unverified},
        "benchmark_status": "passed",
        "evidence_retention": (
            "self_contained_native_release_bundle"
            if level.permanent_native_bundle
            else "workflow_artifact_90_days"
        ),
        "native_evidence": {
            native: native_binding(native) for native in level.required_native
        },
        "package": {
            "path": package_name,
            "bytes": package.stat().st_size,
            "sha256": digest,
            "entry_count": 1,
            "unpacked_bytes": package.stat().st_size,
        },
        "checksum": {"path": checksum_name, "sha256": sha256(checksum)},
        "sbom": {"path": sbom_name, "sha256": sha256(sbom)},
        "native_assets": native_assets,
    }
    manifest_path = root / manifest_name
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest_path


def write_package(root: Path, name: str = "fixture.tgz") -> Path:
    package = root / name
    content = b"0.5.0\n"
    info = tarfile.TarInfo("package/VERSION")
    info.size = len(content)
    info.mtime = 0
    with tarfile.open(package, "w:gz") as archive:
        archive.addfile(info, io.BytesIO(content))
    return package


def write_external_native_evidence(
    root: Path, level: ReleaseLevel
) -> dict[str, dict[str, object]]:
    bindings: dict[str, dict[str, object]] = {}
    for native in level.required_native:
        artifact_path = root / f"{native}.png"
        artifact_path.write_bytes(b"png")
        record = native_binding(native)
        record["artifacts"] = [
            {
                "role": "after_screenshot",
                "path": artifact_path.name,
                "bytes": artifact_path.stat().st_size,
                "sha256": sha256(artifact_path),
            }
        ]
        record_path = root / f"{native}-observed.json"
        record_path.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
        bindings[native] = {
            **record,
            "evidence_sha256": sha256(record_path),
        }
    return bindings


def release_evidence(level: ReleaseLevel, *, phase: str = "final") -> dict[str, object]:
    check_ids = {
        *level.required_domains,
        *(f"host_{host}_current_source" for host in level.required_hosts),
        *(f"native_{native}_current_source" for native in level.required_native),
    }
    return {
        "schema": "design-craft.release-evidence.v1",
        "release_level": level.name,
        "release_level_score": level.score,
        "phase": phase,
        "source_commit": HEAD,
        "verified_hosts": list(level.required_hosts),
        "verified_native": list(level.required_native),
        "unverified": {name: "unverified" for name in level.allowed_unverified},
        "evidence_retention": (
            "self_contained_native_release_bundle"
            if level.permanent_native_bundle
            else "workflow_artifact_90_days"
        ),
        "checks": [
            {"id": check_id, "status": "passed", "evidence": {}, "error": ""}
            for check_id in sorted(check_ids)
        ],
        "ok": True,
    }


def attach_native_bindings(
    payload: dict[str, object],
    level: ReleaseLevel,
    bindings: dict[str, dict[str, object]],
) -> None:
    checks = payload["checks"]
    for check in checks:
        check_id = check["id"]
        if check_id.startswith("native_") and check_id.endswith("_current_source"):
            native = check_id.removeprefix("native_").removesuffix("_current_source")
            if native in level.required_native:
                check["evidence"] = bindings[native]


class ReleaseAssetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy()

    def validate(self, root: Path, level: ReleaseLevel) -> dict[str, object]:
        with patch("tools.design_craft.release.assets._head", return_value=HEAD), patch(
            "tools.design_craft.release.assets._version", return_value=VERSION
        ):
            return validate_assets(root, level=level)

    def test_operational_exact_asset_set_validates(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_assets(root, self.policy["operational_95"])
            self.assertTrue(self.validate(root, self.policy["operational_95"])["ok"])

    def test_operational_extra_native_asset_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            level = self.policy["operational_95"]
            write_assets(root, level)
            (root / "design-craft-v0.5.0-native-runtime.tgz").write_bytes(b"extra")
            result = self.validate(root, level)
            self.assertFalse(result["ok"])
            self.assertTrue(any("asset set mismatch" in error for error in result["errors"]))

    def test_extra_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            level = self.policy["operational_95"]
            write_assets(root, level)
            (root / "unexpected-directory").mkdir()
            result = self.validate(root, level)
            self.assertFalse(result["ok"])
            self.assertTrue(
                any("unexpected or unsafe" in error for error in result["errors"])
            )

    def test_expected_asset_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            root = base / "release"
            root.mkdir()
            level = self.policy["operational_95"]
            write_assets(root, level)
            package = root / level.assets(VERSION)[0]
            outside = base / "outside.tgz"
            outside.write_bytes(package.read_bytes())
            package.unlink()
            package.symlink_to(outside)
            result = self.validate(root, level)
            self.assertFalse(result["ok"])
            self.assertTrue(
                any("unexpected or unsafe" in error for error in result["errors"])
            )

    def test_non_hex_native_digest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            level = self.policy["operational_95"]
            manifest_path = write_assets(root, level)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["native_evidence"]["ios_simulator"]["evidence_sha256"] = "z" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = self.validate(root, level)
            self.assertFalse(result["ok"])
            self.assertTrue(any("evidence_sha256" in error for error in result["errors"]))

    def test_certified_native_asset_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            level = self.policy["certified_100"]
            write_assets(root, level)
            (root / level.assets(VERSION)[4]).write_bytes(b"tampered")
            result = self.validate(root, level)
            self.assertFalse(result["ok"])
            self.assertTrue(any("native asset metadata mismatch" in error for error in result["errors"]))

    def test_candidate_evidence_cannot_build_final_assets(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "evidence.json"
            path.write_text(json.dumps(release_evidence(level, phase="candidate")), encoding="utf-8")
            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                with self.assertRaisesRegex(ValueError, "final-phase"):
                    load_release_evidence(path, level)

    def test_release_level_tamper_is_rejected(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            payload = release_evidence(level)
            payload["release_level"] = "certified_100"
            path = Path(raw) / "evidence.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                with self.assertRaisesRegex(ValueError, "requested release level"):
                    load_release_evidence(path, level)

    def test_duplicate_release_check_ids_are_rejected(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            payload = release_evidence(level)
            payload["checks"].append(dict(payload["checks"][0]))
            path = Path(raw) / "evidence.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                with self.assertRaisesRegex(ValueError, "check ids must be unique"):
                    load_release_evidence(path, level)

    def test_missing_required_domain_check_is_rejected(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            payload = release_evidence(level)
            payload["checks"] = [
                check
                for check in payload["checks"]
                if check["id"] != "performance_regression"
            ]
            path = Path(raw) / "evidence.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                with self.assertRaisesRegex(ValueError, "performance_regression"):
                    load_release_evidence(path, level)

    def test_certified_missing_physical_evidence_check_is_rejected(self) -> None:
        level = self.policy["certified_100"]
        with tempfile.TemporaryDirectory() as raw:
            payload = release_evidence(level)
            payload["checks"] = [
                check
                for check in payload["checks"]
                if check["id"] != "native_physical_device_current_source"
            ]
            path = Path(raw) / "evidence.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                with self.assertRaisesRegex(ValueError, "native_physical_device_current_source"):
                    load_release_evidence(path, level)

    def test_workflow_binding_tamper_is_rejected_against_selected_run(self) -> None:
        expected_run = selected_workflow_run()
        valid_manifest = {
            "native_evidence": {
                native: {"workflow": workflow()}
                for native in ("ios_simulator", "android_emulator")
            }
        }
        self.assertEqual(
            validate_release_native_bindings(
                valid_manifest,
                required_native=("ios_simulator", "android_emulator"),
                expected_run=expected_run,
                expected_repository="bigKING67/design-craft",
            ),
            [],
        )
        tampered = {
            "run_attempt": 2,
            "ref": "refs/heads/v0.5.0",
            "event": "workflow_dispatch",
            "url": "https://github.com/bigKING67/design-craft/actions/runs/999",
        }
        for field, value in tampered.items():
            with self.subTest(field=field):
                manifest = json.loads(json.dumps(valid_manifest))
                manifest["native_evidence"]["ios_simulator"]["workflow"][field] = value
                errors = validate_release_native_bindings(
                    manifest,
                    required_native=("ios_simulator", "android_emulator"),
                    expected_run=expected_run,
                    expected_repository="bigKING67/design-craft",
                )
                self.assertTrue(any(field in error for error in errors), errors)

    def test_sbom_manifest_digest_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            level = self.policy["operational_95"]
            manifest_path = write_assets(root, level)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["sbom"]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = self.validate(root, level)
            self.assertFalse(result["ok"])
            self.assertIn("release manifest SBOM digest mismatch", result["errors"])

    def test_sbom_package_digest_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            level = self.policy["operational_95"]
            manifest_path = write_assets(root, level)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            sbom_path = root / level.assets(VERSION)[3]
            sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
            sbom["packages"][0]["checksums"][0]["checksumValue"] = "0" * 64
            sbom_path.write_text(json.dumps(sbom), encoding="utf-8")
            manifest["sbom"]["sha256"] = sha256(sbom_path)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = self.validate(root, level)
            self.assertFalse(result["ok"])
            self.assertIn("SBOM package digest mismatch", result["errors"])

    def test_external_native_evidence_binding_mismatch_is_rejected(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence_root = root / "evidence"
            evidence_root.mkdir()
            bindings = write_external_native_evidence(evidence_root, level)
            bindings["ios_simulator"]["workflow"] = {
                **bindings["ios_simulator"]["workflow"],
                "run_attempt": 2,
            }
            payload = release_evidence(level)
            attach_native_bindings(payload, level, bindings)
            evidence_path = root / "release-evidence.json"
            evidence_path.write_text(json.dumps(payload), encoding="utf-8")
            output_dir = root / "release"

            def fake_pack(destination: Path) -> tuple[Path, dict[str, object]]:
                package = write_package(destination)
                return package, {"entryCount": 1, "unpackedSize": 6}

            with patch("tools.design_craft.release.assets._head", return_value=HEAD), patch(
                "tools.design_craft.release.assets._version", return_value=VERSION
            ), patch("tools.design_craft.release.assets._npm_pack", side_effect=fake_pack):
                with self.assertRaisesRegex(ValueError, "workflow binding"):
                    build_assets(
                        output_dir,
                        level=level,
                        evidence_path=evidence_path,
                        evidence_root=evidence_root,
                    )

    def test_operational_evidence_is_bound_to_the_selected_native_run(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence_root = root / "evidence"
            evidence_root.mkdir()
            payload = release_evidence(level)
            benchmark_result = root / "benchmark-result-full.json"
            write_benchmark_result(benchmark_result)
            attach_benchmark_binding(payload, benchmark_result)
            attach_native_bindings(
                payload,
                level,
                write_external_native_evidence(evidence_root, level),
            )
            evidence_path = root / "release-evidence.json"
            evidence_path.write_text(json.dumps(payload), encoding="utf-8")
            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                result = validate_release_run_bindings(
                    evidence_path,
                    level=level,
                    native_run=native_run_observation(),
                    benchmark_run=benchmark_run_observation(),
                    benchmark_result_path=benchmark_result,
                    evidence_root=evidence_root,
                )
                self.assertTrue(result["ok"], result["errors"])
                tampered_run = native_run_observation(999)
                result = validate_release_run_bindings(
                    evidence_path,
                    level=level,
                    native_run=tampered_run,
                    benchmark_run=benchmark_run_observation(),
                    benchmark_result_path=benchmark_result,
                    evidence_root=evidence_root,
                )
            self.assertFalse(result["ok"])
            self.assertTrue(any("run_id" in error for error in result["errors"]))

    def test_operational_evidence_rejects_benchmark_run_or_digest_tamper(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence_root = root / "evidence"
            evidence_root.mkdir()
            benchmark_result = root / "benchmark-result-full.json"
            write_benchmark_result(benchmark_result)
            payload = release_evidence(level)
            attach_benchmark_binding(payload, benchmark_result)
            attach_native_bindings(
                payload,
                level,
                write_external_native_evidence(evidence_root, level),
            )
            evidence_path = root / "release-evidence.json"
            evidence_path.write_text(json.dumps(payload), encoding="utf-8")

            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                wrong_run = validate_release_run_bindings(
                    evidence_path,
                    level=level,
                    native_run=native_run_observation(),
                    benchmark_run=benchmark_run_observation(999),
                    benchmark_result_path=benchmark_result,
                    evidence_root=evidence_root,
                )
                self.assertFalse(wrong_run["ok"])
                self.assertTrue(
                    any("run_id" in error for error in wrong_run["errors"]),
                    wrong_run["errors"],
                )

                benchmark_result.write_bytes(benchmark_result.read_bytes() + b"\n")
                wrong_digest = validate_release_run_bindings(
                    evidence_path,
                    level=level,
                    native_run=native_run_observation(),
                    benchmark_run=benchmark_run_observation(),
                    benchmark_result_path=benchmark_result,
                    evidence_root=evidence_root,
                )
            self.assertFalse(wrong_digest["ok"])
            self.assertTrue(
                any("benchmark_result_sha256" in error for error in wrong_digest["errors"]),
                wrong_digest["errors"],
            )

    def test_artifact_relative_evidence_survives_root_relocation(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            original_root = root / "download-a"
            original_root.mkdir()
            payload = release_evidence(level)
            benchmark_result = root / "benchmark-result-full.json"
            write_benchmark_result(benchmark_result)
            attach_benchmark_binding(payload, benchmark_result)
            bindings = write_external_native_evidence(original_root, level)
            attach_native_bindings(payload, level, bindings)
            self.assertTrue(
                all("evidence_source_path" not in binding for binding in bindings.values())
            )
            evidence_path = root / "release-evidence.json"
            evidence_path.write_text(json.dumps(payload), encoding="utf-8")
            relocated_root = root / "download-b"
            original_root.rename(relocated_root)

            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                result = validate_release_run_bindings(
                    evidence_path,
                    level=level,
                    native_run=native_run_observation(),
                    benchmark_run=benchmark_run_observation(),
                    benchmark_result_path=benchmark_result,
                    evidence_root=relocated_root,
                )
            self.assertTrue(result["ok"], result["errors"])

    def test_legacy_absolute_evidence_source_path_remains_readable(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence_root = root / "legacy"
            evidence_root.mkdir()
            payload = release_evidence(level)
            benchmark_result = root / "benchmark-result-full.json"
            write_benchmark_result(benchmark_result)
            attach_benchmark_binding(payload, benchmark_result)
            bindings = write_external_native_evidence(evidence_root, level)
            for binding in bindings.values():
                binding["evidence_source_path"] = str(
                    evidence_root / str(binding["evidence_path"])
                )
            attach_native_bindings(payload, level, bindings)
            evidence_path = root / "release-evidence.json"
            evidence_path.write_text(json.dumps(payload), encoding="utf-8")

            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                result = validate_release_run_bindings(
                    evidence_path,
                    level=level,
                    native_run=native_run_observation(),
                    benchmark_run=benchmark_run_observation(),
                    benchmark_result_path=benchmark_result,
                )
            self.assertTrue(result["ok"], result["errors"])

    def test_artifact_relative_evidence_rejects_root_escape(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence_root = root / "evidence"
            evidence_root.mkdir()
            payload = release_evidence(level)
            benchmark_result = root / "benchmark-result-full.json"
            write_benchmark_result(benchmark_result)
            attach_benchmark_binding(payload, benchmark_result)
            bindings = write_external_native_evidence(evidence_root, level)
            bindings["ios_simulator"]["evidence_path"] = "../outside.json"
            attach_native_bindings(payload, level, bindings)
            evidence_path = root / "release-evidence.json"
            evidence_path.write_text(json.dumps(payload), encoding="utf-8")

            with patch("tools.design_craft.release.assets._head", return_value=HEAD):
                with self.assertRaisesRegex(ValueError, "must stay relative"):
                    validate_release_run_bindings(
                        evidence_path,
                        level=level,
                        native_run=native_run_observation(),
                        benchmark_run=benchmark_run_observation(),
                        benchmark_result_path=benchmark_result,
                        evidence_root=evidence_root,
                    )

    def test_force_build_failure_preserves_existing_assets(self) -> None:
        level = self.policy["operational_95"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence_root = root / "evidence"
            evidence_root.mkdir()
            payload = release_evidence(level)
            attach_native_bindings(
                payload,
                level,
                write_external_native_evidence(evidence_root, level),
            )
            evidence_path = root / "release-evidence.json"
            evidence_path.write_text(json.dumps(payload), encoding="utf-8")
            output_dir = root / "release"
            output_dir.mkdir()
            before = {}
            for name in level.assets(VERSION):
                path = output_dir / name
                path.write_bytes(f"existing:{name}".encode("utf-8"))
                before[name] = path.read_bytes()

            with patch("tools.design_craft.release.assets._head", return_value=HEAD), patch(
                "tools.design_craft.release.assets._version", return_value=VERSION
            ), patch(
                "tools.design_craft.release.assets._npm_pack",
                side_effect=RuntimeError("pack failed"),
            ):
                with self.assertRaisesRegex(RuntimeError, "pack failed"):
                    build_assets(
                        output_dir,
                        level=level,
                        evidence_path=evidence_path,
                        evidence_root=evidence_root,
                        force=True,
                    )
            self.assertEqual(
                {name: (output_dir / name).read_bytes() for name in before}, before
            )

    def test_published_validation_failure_rolls_back_the_asset_set(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "release"
            staging = root / "staging"
            output.mkdir()
            staging.mkdir()
            names = ("package.tgz", "manifest.json")
            for name in names:
                (output / name).write_bytes(f"old:{name}".encode("utf-8"))
                (staging / name).write_bytes(f"new:{name}".encode("utf-8"))
            before = {name: (output / name).read_bytes() for name in names}

            def reject_published(_: Path) -> None:
                raise RuntimeError("published validation failed")

            with self.assertRaisesRegex(RuntimeError, "published validation failed"):
                publish_asset_set(
                    staging,
                    output,
                    names,
                    force=True,
                    validate_published=reject_published,
                )
            self.assertEqual(
                {name: (output / name).read_bytes() for name in names}, before
            )


if __name__ == "__main__":
    unittest.main()
