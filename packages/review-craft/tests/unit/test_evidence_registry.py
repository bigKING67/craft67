from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from tests.support import (
    RUNTIME_LIB,
    create_run,
    make_target,
    populate_valid_run,
    rewrite_fixture_run_schema,
    run_cli,
)

sys.path.insert(0, str(RUNTIME_LIB))

from review_craft.constants import (  # noqa: E402
    ARTIFACT_PATHS,
    LEGACY_SCHEMA_VERSION,
    PREVIOUS_SCHEMA_VERSION,
    SCHEMA_VERSION,
)
from review_craft.contracts import ContractError, validate_run  # noqa: E402
from review_craft.jsonio import (  # noqa: E402
    read_json,
    read_jsonl,
    sha256_bytes,
    write_json,
    write_jsonl,
)


class EvidenceRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target_temporary, self.target = make_target()
        self.addCleanup(self.target_temporary.cleanup)
        self.output_temporary = tempfile.TemporaryDirectory(prefix="review-craft-output-")
        self.addCleanup(self.output_temporary.cleanup)
        self.output_root = Path(self.output_temporary.name)
        self.run_dir = create_run(self.target, self.output_root)

    def _source(self, name: str, payload: bytes) -> Path:
        source = self.output_root / name
        source.write_bytes(payload)
        return source

    def _register(
        self,
        identifier: str = "runtime-probe",
        *,
        source: Path | None = None,
        max_bytes: int | None = None,
    ) -> tuple[dict[str, object], object]:
        source = source or self._source(f"{identifier}.json", b'{"ok":true}\n')
        arguments = [
            "register-evidence",
            "--run-dir",
            str(self.run_dir),
            "--id",
            identifier,
            "--source",
            str(source),
            "--kind",
            "runtime",
            "--producer",
            "Codex",
            "--description",
            "Controlled runtime probe",
            "--media-type",
            "application/json",
        ]
        if max_bytes is not None:
            arguments.extend(["--max-bytes", str(max_bytes)])
        completed = run_cli(*arguments)
        payload = json.loads(completed.stdout) if completed.returncode == 0 else {}
        return payload, completed

    def _bind_reference_everywhere(self, reference: str) -> None:
        coverage = read_json(self.run_dir / ARTIFACT_PATHS["coverage"])
        coverage["files"][0]["evidenceRefs"] = [reference]
        write_json(self.run_dir / ARTIFACT_PATHS["coverage"], coverage)

        candidates = read_jsonl(self.run_dir / ARTIFACT_PATHS["candidateLedger"])
        candidates[0]["evidence"][0]["ref"] = reference
        candidates[0]["validation"]["evidenceRefs"] = [reference]
        write_jsonl(self.run_dir / ARTIFACT_PATHS["candidateLedger"], candidates)

        findings = read_json(self.run_dir / ARTIFACT_PATHS["findings"])
        findings["findings"][0]["evidenceRefs"] = [reference]
        write_json(self.run_dir / ARTIFACT_PATHS["findings"], findings)


    def _sealed_run(self) -> dict[str, object]:
        entry, completed = self._register()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        populate_valid_run(self.run_dir)
        self._bind_reference_everywhere(str(entry["ref"]))
        finalized = run_cli("finalize", "--run-dir", str(self.run_dir))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        return entry

    def test_preflight_creates_v4_empty_registry(self) -> None:
        manifest = read_json(self.run_dir / "review-manifest.json")
        registry = read_json(self.run_dir / ARTIFACT_PATHS["evidenceRegistry"])
        self.assertEqual(manifest["schemaVersion"], SCHEMA_VERSION)
        self.assertEqual(manifest["artifacts"], ARTIFACT_PATHS)
        self.assertEqual(
            registry,
            {
                "documentType": "review-craft.evidence-registry",
                "schemaVersion": SCHEMA_VERSION,
                "artifacts": [],
            },
        )
        validated = run_cli("validate", "--run-dir", str(self.run_dir), "--allow-draft")
        self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_register_evidence_copies_hashes_and_sorts_artifacts(self) -> None:
        z_source = self._source("z.json", b'{"id":"z"}\n')
        a_source = self._source("a.json", b'{"id":"a"}\n')
        z_entry, z_completed = self._register("z-probe", source=z_source)
        a_entry, a_completed = self._register("a-probe", source=a_source)
        self.assertEqual(z_completed.returncode, 0, z_completed.stderr)
        self.assertEqual(a_completed.returncode, 0, a_completed.stderr)
        registry = read_json(self.run_dir / ARTIFACT_PATHS["evidenceRegistry"])
        self.assertEqual([row["id"] for row in registry["artifacts"]], ["a-probe", "z-probe"])
        for entry, expected in ((a_entry, a_source.read_bytes()), (z_entry, z_source.read_bytes())):
            artifact = self.run_dir / str(entry["path"])
            self.assertEqual(artifact.read_bytes(), expected)
            self.assertEqual(entry["sha256"], sha256_bytes(expected))
            self.assertEqual(entry["sizeBytes"], len(expected))
            self.assertEqual(entry["ref"], f"artifact:{entry['id']}")
        validate_run(self.run_dir, final=False)

    def test_register_evidence_rejects_duplicate_invalid_large_and_symlink_sources(self) -> None:
        _, first = self._register()
        self.assertEqual(first.returncode, 0, first.stderr)
        _, duplicate = self._register()
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("already exists", duplicate.stderr)

        invalid_source = self._source("invalid-id.json", b"{}\n")
        _, invalid = self._register("Bad/Path", source=invalid_source)
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("--id must start", invalid.stderr)

        large_source = self._source("large.bin", b"1234")
        _, large = self._register("large", source=large_source, max_bytes=3)
        self.assertNotEqual(large.returncode, 0)
        self.assertIn("exceeds --max-bytes", large.stderr)

        if hasattr(os, "symlink"):
            link = self.output_root / "probe-link.json"
            try:
                link.symlink_to(large_source)
            except OSError:
                pass
            else:
                _, symlink = self._register("symlink", source=link)
                self.assertNotEqual(symlink.returncode, 0)
                self.assertIn("non-symlink", symlink.stderr)

            self.run_dir = create_run(self.target, self.output_root)
            outside_parent = self.output_root / "outside-registered"
            outside_parent.mkdir()
            registered_parent = self.run_dir / "evidence/registered"
            try:
                registered_parent.symlink_to(outside_parent, target_is_directory=True)
            except OSError:
                pass
            else:
                _, parent_symlink = self._register("parent-symlink")
                self.assertNotEqual(parent_symlink.returncode, 0)
                self.assertIn("parent must not be a symlink", parent_symlink.stderr)

    def test_registered_reference_finalizes_and_is_projected_into_report(self) -> None:
        entry = self._sealed_run()
        report = (self.run_dir / ARTIFACT_PATHS["report"]).read_text(encoding="utf-8")
        self.assertIn(f"`{entry['ref']}`（runtime，Codex）", report)
        self.assertIn(str(entry["sha256"]), report)
        self.assertIn(f"{entry['sizeBytes']} bytes", report)

    def test_sealed_run_rejects_missing_modified_and_rebound_registered_artifacts(self) -> None:
        entry = self._sealed_run()
        artifact = self.run_dir / str(entry["path"])
        artifact.unlink()
        with self.assertRaises(ContractError) as missing:
            validate_run(self.run_dir)
        self.assertIn("invalid run artifact", str(missing.exception))

        self.run_dir = create_run(self.target, self.output_root)
        entry = self._sealed_run()
        artifact = self.run_dir / str(entry["path"])
        artifact.write_bytes(b"tampered\n")
        with self.assertRaises(ContractError) as modified:
            validate_run(self.run_dir)
        self.assertIn("sha256: does not match", str(modified.exception))

        self.run_dir = create_run(self.target, self.output_root)
        self._sealed_run()
        registry_path = self.run_dir / ARTIFACT_PATHS["evidenceRegistry"]
        registry = read_json(registry_path)
        registry["artifacts"][0]["sizeBytes"] += 1
        write_json(registry_path, registry)
        with self.assertRaises(ContractError) as rebound:
            validate_run(self.run_dir)
        self.assertIn("sizeBytes: does not match", str(rebound.exception))

        if hasattr(os, "symlink"):
            self.run_dir = create_run(self.target, self.output_root)
            entry = self._sealed_run()
            artifact = self.run_dir / str(entry["path"])
            replacement = self._source("replacement.json", b'{"replacement":true}\n')
            artifact.unlink()
            try:
                artifact.symlink_to(replacement)
            except OSError:
                pass
            else:
                with self.assertRaises(ContractError) as symlink:
                    validate_run(self.run_dir)
                self.assertIn("must not be a symlink", str(symlink.exception))

    def test_unknown_and_path_style_artifact_references_fail_closed(self) -> None:
        populate_valid_run(self.run_dir)
        self._bind_reference_everywhere("artifact:unknown-probe")
        with self.assertRaises(ContractError) as unknown:
            validate_run(self.run_dir)
        message = str(unknown.exception)
        for prefix in (
            "coverage.files[0].evidenceRefs",
            "candidate-ledger[0].evidence[0].ref",
            "candidate-ledger[0].validation.evidenceRefs",
            "findings.findings[0].evidenceRefs",
        ):
            self.assertIn(prefix, message)

        findings_path = self.run_dir / ARTIFACT_PATHS["findings"]
        for reference in (
            "artifact:/tmp/probe.json",
            "artifact:../probe.json",
            "artifact:evidence/manual/probe.json",
        ):
            with self.subTest(reference=reference):
                entry, completed = self._register("runtime-probe")
                if completed.returncode != 0:
                    self.assertIn("already exists", completed.stderr)
                findings = read_json(findings_path)
                findings["findings"][0]["evidenceRefs"] = [reference]
                write_json(findings_path, findings)
                with self.assertRaises(ContractError) as invalid:
                    validate_run(self.run_dir)
                self.assertIn("expected artifact:<registered-id>", str(invalid.exception))
                valid_reference = str(entry.get("ref", "artifact:runtime-probe"))
                findings["findings"][0]["evidenceRefs"] = [valid_reference]
                write_json(findings_path, findings)

    def test_registry_rejects_path_tampering_or_unregistered_artifacts(self) -> None:
        self._register()
        registry_path = self.run_dir / ARTIFACT_PATHS["evidenceRegistry"]
        registry = read_json(registry_path)
        registry["artifacts"][0]["path"] = "../outside"
        write_json(registry_path, registry)
        with self.assertRaises(ContractError) as traversal:
            validate_run(self.run_dir, final=False)
        self.assertIn("safe run-relative path", str(traversal.exception))

        registry["artifacts"][0]["path"] = "evidence/registered/other/artifact"
        write_json(registry_path, registry)
        with self.assertRaises(ContractError) as rebound_path:
            validate_run(self.run_dir, final=False)
        self.assertIn(
            "expected evidence/registered/runtime-probe/artifact",
            str(rebound_path.exception),
        )

        self.run_dir = create_run(self.target, self.output_root)
        self._register("a-probe")
        self._register("b-probe")
        registry_path = self.run_dir / ARTIFACT_PATHS["evidenceRegistry"]
        registry = read_json(registry_path)
        registry["artifacts"][1]["id"] = "a-probe"
        registry["artifacts"][1]["path"] = registry["artifacts"][0]["path"]
        write_json(registry_path, registry)
        with self.assertRaises(ContractError) as duplicates:
            validate_run(self.run_dir, final=False)
        self.assertIn("duplicate 'a-probe'", str(duplicates.exception))
        self.assertIn("duplicate 'evidence/registered/a-probe/artifact'", str(duplicates.exception))

        self.run_dir = create_run(self.target, self.output_root)
        orphan = self.run_dir / "evidence/registered/orphan/artifact"
        orphan.parent.mkdir(parents=True)
        orphan.write_bytes(b"orphan\n")
        with self.assertRaises(ContractError) as unregistered:
            validate_run(self.run_dir, final=False)
        self.assertIn("unregistered artifact path", str(unregistered.exception))

        if hasattr(os, "symlink"):
            self.run_dir = create_run(self.target, self.output_root)
            outside = self.output_root / "validator-outside-registered"
            outside.mkdir()
            registered_root = self.run_dir / "evidence/registered"
            try:
                registered_root.symlink_to(outside, target_is_directory=True)
            except OSError:
                pass
            else:
                with self.assertRaises(ContractError) as root_symlink:
                    validate_run(self.run_dir, final=False)
                self.assertIn("registered root must not be a symlink", str(root_symlink.exception))

    def test_sealed_and_historical_runs_have_explicit_registration_boundaries(self) -> None:
        self._sealed_run()
        _, sealed = self._register("after-seal")
        self.assertNotEqual(sealed.returncode, 0)
        self.assertIn("unsealed draft", sealed.stderr)
        sealed_evidence = run_cli(
            "run-evidence",
            "--run-dir",
            str(self.run_dir),
            "--command",
            "test",
        )
        self.assertNotEqual(sealed_evidence.returncode, 0)
        self.assertIn("unsealed draft", sealed_evidence.stderr)

        rewrite_fixture_run_schema(self.run_dir, PREVIOUS_SCHEMA_VERSION)
        validate_run(self.run_dir)
        historical_v4_evidence = run_cli(
            "run-evidence",
            "--run-dir",
            str(self.run_dir),
            "--command",
            "test",
        )
        self.assertNotEqual(historical_v4_evidence.returncode, 0)
        self.assertIn("current run.v5", historical_v4_evidence.stderr)
        historical_v4_finalize = run_cli("finalize", "--run-dir", str(self.run_dir))
        self.assertNotEqual(historical_v4_finalize.returncode, 0)
        self.assertIn("run.v4 remain validation-only", historical_v4_finalize.stderr)

        rewrite_fixture_run_schema(self.run_dir, LEGACY_SCHEMA_VERSION)
        validated = run_cli("validate", "--run-dir", str(self.run_dir))
        self.assertEqual(validated.returncode, 0, validated.stderr)
        historical_evidence = run_cli(
            "run-evidence",
            "--run-dir",
            str(self.run_dir),
            "--command",
            "test",
        )
        self.assertNotEqual(historical_evidence.returncode, 0)
        self.assertIn("current run.v5", historical_evidence.stderr)
        finalized = run_cli("finalize", "--run-dir", str(self.run_dir))
        self.assertNotEqual(finalized.returncode, 0)
        self.assertIn("validation-only historical data", finalized.stderr)


if __name__ == "__main__":
    unittest.main()
