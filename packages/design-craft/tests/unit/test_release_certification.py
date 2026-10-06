from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.release.certification import (
    artifact_name,
    build_certification_bundle,
    validate_certification_bundle,
)
from tools.design_craft.release.github_runs import (
    ARTIFACT_OBSERVATION_SCHEMA,
    CERTIFICATION_WORKFLOW_NAME,
    CERTIFICATION_WORKFLOW_PATH,
    OBSERVATION_SCHEMA,
)
from tools.design_craft.release.policy import load_policy

from tests.unit.test_release_assets import (
    HEAD,
    VERSION,
    attach_benchmark_binding,
    attach_native_bindings,
    benchmark_run_observation,
    native_run_observation,
    release_evidence,
    write_assets,
    write_benchmark_result,
    write_external_native_evidence,
)


REPOSITORY = "bigKING67/design-craft"


def write_observation(path: Path, kind: str, run: dict[str, object]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": OBSERVATION_SCHEMA,
                "kind": kind,
                "source_commit": HEAD,
                "run": run,
            }
        ),
        encoding="utf-8",
    )


def certification_run(run_id: int) -> dict[str, object]:
    return {
        "id": run_id,
        "attempt": 1,
        "workflow": CERTIFICATION_WORKFLOW_PATH,
        "workflow_name": CERTIFICATION_WORKFLOW_NAME,
        "event": "workflow_dispatch",
        "head_branch": "main",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/{REPOSITORY}/actions/runs/{run_id}",
        "repository": REPOSITORY,
    }


def write_artifact_observation(
    path: Path,
    *,
    repository: str = REPOSITORY,
    run_id: int = 789,
    artifact_id: int = 900,
    digest: str | None = None,
) -> str:
    selected_digest = digest or f"sha256:{'a' * 64}"
    path.write_text(
        json.dumps(
            {
                "schema": ARTIFACT_OBSERVATION_SCHEMA,
                "source_commit": HEAD,
                "repository": repository,
                "artifact": {
                    "id": artifact_id,
                    "name": artifact_name(f"v{VERSION}", run_id),
                    "size_in_bytes": 1024,
                    "digest": selected_digest,
                    "expired": False,
                    "created_at": "2026-07-23T00:00:00Z",
                    "updated_at": "2026-07-23T00:00:01Z",
                    "workflow_run": {
                        "id": run_id,
                        "head_branch": "main",
                        "head_sha": HEAD,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return selected_digest


class ReleaseCertificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.level = load_policy()["operational_95"]

    def build_fixture(self, root: Path, *, run_id: int = 789) -> Path:
        evidence_root = root / "native-evidence-source"
        evidence_root.mkdir()
        payload = release_evidence(self.level)
        benchmark_result = root / "benchmark-result-full.json"
        write_benchmark_result(benchmark_result)
        attach_benchmark_binding(payload, benchmark_result)
        attach_native_bindings(
            payload,
            self.level,
            write_external_native_evidence(evidence_root, self.level),
        )
        evidence_path = root / "release-evidence.json"
        evidence_path.write_text(json.dumps(payload), encoding="utf-8")
        native_observation = root / "native-run.json"
        write_observation(
            native_observation,
            "native",
            native_run_observation(),
        )
        benchmark_observation = root / "benchmark-run.json"
        write_observation(
            benchmark_observation,
            "benchmark",
            benchmark_run_observation(),
        )
        assets_dir = root / "release-assets"
        assets_dir.mkdir()
        write_assets(assets_dir, self.level)
        output = root / "certification"
        result = build_certification_bundle(
            output,
            level=self.level,
            tag=f"v{VERSION}",
            evidence_path=evidence_path,
            evidence_root=evidence_root,
            native_observation=native_observation,
            benchmark_observation=benchmark_observation,
            benchmark_result=benchmark_result,
            physical_observation=None,
            assets_dir=assets_dir,
            repository=REPOSITORY,
            workflow_run_id=run_id,
            workflow_run_attempt=1,
        )
        self.assertTrue(result["ok"], result["errors"])
        return output

    def test_bundle_is_self_contained_and_relocatable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            bundle = self.build_fixture(root)
            relocated = root / "downloaded-certification"
            bundle.rename(relocated)
            result = validate_certification_bundle(relocated, level=self.level)
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(result["artifact_name"], artifact_name(f"v{VERSION}", 789))
            self.assertTrue(
                (relocated / "observations/benchmark-run.json").is_file()
            )
            self.assertTrue(
                (relocated / "benchmark/benchmark-result-full.json").is_file()
            )

    def test_benchmark_result_tamper_is_rejected_after_relocation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            bundle = self.build_fixture(root)
            benchmark_result = bundle / "benchmark/benchmark-result-full.json"
            benchmark_result.write_bytes(benchmark_result.read_bytes() + b"\n")
            result = validate_certification_bundle(bundle, level=self.level)
            self.assertFalse(result["ok"])
            self.assertTrue(
                any(
                    "digest mismatch" in error
                    or "benchmark_result_sha256" in error
                    for error in result["errors"]
                ),
                result["errors"],
            )

    def test_publication_validation_binds_run_artifact_id_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            bundle = self.build_fixture(root)
            run_path = root / "certification-run.json"
            write_observation(run_path, "certification", certification_run(789))
            artifact_path = root / "artifact.json"
            digest = write_artifact_observation(artifact_path)
            result = validate_certification_bundle(
                bundle,
                level=self.level,
                certification_observation=run_path,
                artifact_observation=artifact_path,
                expected_artifact_id=900,
                expected_artifact_digest=digest,
            )
            self.assertTrue(result["ok"], result["errors"])

            rejected = validate_certification_bundle(
                bundle,
                level=self.level,
                certification_observation=run_path,
                artifact_observation=artifact_path,
                expected_artifact_id=900,
                expected_artifact_digest=f"sha256:{'b' * 64}",
            )
            self.assertFalse(rejected["ok"])
            self.assertTrue(any("digest" in error for error in rejected["errors"]))

    def test_publication_validation_requires_complete_external_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            bundle = self.build_fixture(root)
            run_path = root / "certification-run.json"
            write_observation(run_path, "certification", certification_run(789))
            result = validate_certification_bundle(
                bundle,
                level=self.level,
                certification_observation=run_path,
            )
            self.assertFalse(result["ok"])
            self.assertTrue(
                any("requires certification observation" in error for error in result["errors"])
            )

    def test_publication_validation_rejects_artifact_repository_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            bundle = self.build_fixture(root)
            run_path = root / "certification-run.json"
            write_observation(run_path, "certification", certification_run(789))
            artifact_path = root / "artifact.json"
            digest = write_artifact_observation(
                artifact_path,
                repository="other/design-craft",
            )
            result = validate_certification_bundle(
                bundle,
                level=self.level,
                certification_observation=run_path,
                artifact_observation=artifact_path,
                expected_artifact_id=900,
                expected_artifact_digest=digest,
            )
            self.assertFalse(result["ok"])
            self.assertTrue(any("repository" in error for error in result["errors"]))

    def test_unmanifested_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            bundle = self.build_fixture(root)
            (bundle / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
            result = validate_certification_bundle(bundle, level=self.level)
            self.assertFalse(result["ok"])
            self.assertTrue(any("file set mismatch" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
