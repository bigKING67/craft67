from __future__ import annotations

# tests.support adds the canonical runtime library to sys.path before product imports.
# ruff: noqa: I001

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

from tests.support import ROOT, make_target, populate_valid_run, run_cli

from review_craft.attempt_delivery import verify_attempt_delivery
from review_craft.delivery_contract import attestation_base_id
from review_craft.delivery_validation import validate_delivery
from review_craft.jsonio import read_json, sha256_bytes, sha256_json, write_json


class AttemptDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target_tmp, self.target = make_target(commit=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://example.invalid/review.git"],
            cwd=self.target,
            check=True,
        )
        self.run_tmp = tempfile.TemporaryDirectory(prefix="review-craft-runs-")
        self.fix_tmp = tempfile.TemporaryDirectory(prefix="review-craft-fixes-")
        self.delivery_tmp = tempfile.TemporaryDirectory(
            prefix="review-craft-deliveries-"
        )
        self.flake_marker = Path(self.fix_tmp.name) / "flake-marker"
        config = self.target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "check": {
                            "argv": [
                                sys.executable,
                                "-c",
                                (
                                    "import json; from pathlib import Path; "
                                    "assert 'return 42' in Path('app.py').read_text(); "
                                    "print(json.dumps({'checks': {'fixed': True}}))"
                                ),
                            ],
                            "evidenceClaims": [
                                {
                                    "id": "fixed-behavior-check",
                                    "kind": "test",
                                    "jsonPointer": "/checks/fixed",
                                    "equals": True,
                                }
                            ],
                        },
                        "flaky-check": {
                            "argv": [
                                sys.executable,
                                "-c",
                                (
                                    "import json; import sys; from pathlib import Path; "
                                    "assert 'return 42' in Path('app.py').read_text(); "
                                    f"marker = Path({str(self.flake_marker)!r}); "
                                    "seen = marker.exists(); marker.write_text('seen'); "
                                    "print(json.dumps({'checks': {'fixed': True}})); "
                                    "sys.exit(0 if seen else 1)"
                                ),
                            ],
                            "evidenceClaims": [
                                {
                                    "id": "fixed-behavior-check",
                                    "kind": "test",
                                    "jsonPointer": "/checks/fixed",
                                    "equals": True,
                                }
                            ],
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        created = run_cli(
            "preflight",
            "--target",
            str(self.target),
            "--config",
            str(config),
            "--output-root",
            self.run_tmp.name,
        )
        self.assertEqual(created.returncode, 0, created.stderr)
        self.run_dir = Path(json.loads(created.stdout)["runDir"])
        populate_valid_run(self.run_dir)
        finalized = run_cli("finalize", "--run-dir", str(self.run_dir))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)

    def tearDown(self) -> None:
        self.delivery_tmp.cleanup()
        self.fix_tmp.cleanup()
        self.run_tmp.cleanup()
        self.target_tmp.cleanup()

    def _prepare(self, command: str) -> Path:
        prepared = run_cli(
            "prepare-fix",
            "--run-dir",
            str(self.run_dir),
            "--finding",
            "RC-FINDING-001",
            "--command",
            command,
            "--output-root",
            self.fix_tmp.name,
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        return Path(json.loads(prepared.stdout)["fixDir"])

    def _assessment(self, attempt_dir: Path, command: str) -> Path:
        manifest = read_json(attempt_dir / "attempt-manifest.json")
        evidence = read_json(attempt_dir / "attempt-evidence.json")
        path = Path(self.fix_tmp.name) / f"assessment-{manifest['attemptId']}.json"
        path.write_text(
            json.dumps(
                {
                    "documentType": "review-craft.fix-attempt-assessment",
                    "schemaVersion": "review-craft.fix-attempt.v1",
                    "fixId": manifest["fixId"],
                    "attemptId": manifest["attemptId"],
                    "evidenceSha256": sha256_json(evidence),
                    "kind": "AGENT_ASSISTED",
                    "assessor": "Review Craft attempt delivery test",
                    "assessedAt": evidence["completedAt"],
                    "findings": [
                        {
                            "findingId": "RC-FINDING-001",
                            "status": "RESOLVED",
                            "rationale": "The captured attempt matches the fixture contract.",
                            "evidenceRefs": [
                                "change:app.py",
                                f"claim:{command}:fixed-behavior-check",
                            ],
                        }
                    ],
                    "measurements": [],
                    "remainingRisks": [],
                }
            ),
            encoding="utf-8",
        )
        return path

    def _capture_and_finalize(
        self,
        fix_dir: Path,
        command: str,
        *,
        capture_code: int,
        finalize_code: int,
    ) -> Path:
        captured = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        self.assertEqual(captured.returncode, capture_code, captured.stderr)
        attempt_dir = Path(json.loads(captured.stdout)["attemptDir"])
        finalized = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(self._assessment(attempt_dir, command)),
        )
        self.assertEqual(finalized.returncode, finalize_code, finalized.stderr)
        return attempt_dir

    def _commit_source(self) -> str:
        subprocess.run(
            ["git", "add", "--", "app.py", ".review-craft.json"],
            cwd=self.target,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "apply verified attempt fixture"],
            cwd=self.target,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def _verified_attempt(self, *, retry: bool = False) -> tuple[Path, str]:
        command = "flaky-check" if retry else "check"
        fix_dir = self._prepare(command)
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        if retry:
            self._capture_and_finalize(
                fix_dir,
                command,
                capture_code=4,
                finalize_code=4,
            )
        attempt_dir = self._capture_and_finalize(
            fix_dir,
            command,
            capture_code=0,
            finalize_code=0,
        )
        return attempt_dir, self._commit_source()

    @staticmethod
    def _capture(
        argv: list[str], stdout: bytes, *, exit_code: int = 0
    ) -> tuple[dict, bytes]:
        return (
            {
                "argv": argv,
                "cwd": ".",
                "startedAt": "2026-08-02T04:00:00Z",
                "durationMs": 10,
                "exitCode": exit_code,
                "timedOut": False,
                "errorKind": None,
                "stdoutSha256": sha256_bytes(stdout),
                "stderrSha256": sha256_bytes(b""),
                "stdoutBytes": len(stdout),
                "stderrBytes": 0,
            },
            stdout,
        )

    def _successful_ci(self, revision: str) -> dict:
        return {
            "workflowName": "Validate",
            "status": "completed",
            "conclusion": "success",
            "url": "https://example.invalid/actions/runs/123",
            "jobs": [
                {
                    "name": "test",
                    "status": "completed",
                    "conclusion": "success",
                    "startedAt": "2026-08-02T04:00:00Z",
                    "completedAt": "2026-08-02T04:01:00Z",
                    "url": "https://example.invalid/actions/jobs/1",
                }
            ],
            "headSha": revision,
            "createdAt": "2026-08-02T04:00:00Z",
            "updatedAt": "2026-08-02T04:01:00Z",
        }

    def _fake_commands(self, revision: str):
        ci = self._successful_ci(revision)

        def run(argv: list[str], *, cwd: Path, captured_at: str | None = None):
            del cwd, captured_at
            if argv[:2] == ["git", "ls-remote"]:
                ref = argv[-1]
                return self._capture(argv, f"{revision}\t{ref}\n".encode())
            if argv[:3] == ["gh", "run", "view"]:
                return self._capture(argv, json.dumps(ci).encode())
            raise AssertionError(f"unexpected command: {argv}")

        return run

    def _rebind_delivery(self, delivery_dir: Path) -> Path:
        attestation_path = delivery_dir / "delivery-attestation.json"
        state_path = delivery_dir / "delivery-state.json"
        attestation = read_json(attestation_path)
        attestation["deliveryId"] = attestation_base_id(attestation)
        new_dir = delivery_dir.parent / attestation["deliveryId"]
        write_json(attestation_path, attestation, mode=0o600)
        state = read_json(state_path)
        state["deliveryId"] = attestation["deliveryId"]
        state["attestationSha256"] = sha256_json(attestation)
        write_json(state_path, state, mode=0o600)
        delivery_dir.rename(new_dir)
        return new_dir

    def test_local_delivery_v2_is_partial_schema_valid_and_portable(self) -> None:
        attempt_dir, revision = self._verified_attempt()
        completed = run_cli(
            "verify-attempt-delivery",
            "--attempt-dir",
            str(attempt_dir),
            "--output-root",
            self.delivery_tmp.name,
        )
        self.assertEqual(completed.returncode, 3, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "PARTIAL")
        self.assertEqual(payload["lineageStatus"], "VERIFIED")
        self.assertEqual(payload["commit"], revision)
        delivery_dir = Path(payload["deliveryDir"])
        attestation = read_json(delivery_dir / "delivery-attestation.json")
        schema = read_json(
            ROOT / "skills/review-craft/schemas/delivery-attestation-v2.schema.json"
        )
        errors = list(
            Draft202012Validator(
                schema,
                format_checker=FormatChecker(),
            ).iter_errors(attestation)
        )
        self.assertEqual(errors, [])
        self.fix_tmp.cleanup()
        self.run_tmp.cleanup()
        self.target_tmp.cleanup()
        validated = run_cli(
            "validate-delivery", "--delivery-dir", str(delivery_dir)
        )
        self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_retry_delivery_copies_failed_predecessor_and_rejects_deletion(self) -> None:
        attempt_dir, _ = self._verified_attempt(retry=True)
        delivery_dir, attestation = verify_attempt_delivery(
            attempt_dir,
            output_root=self.delivery_tmp.name,
        )
        self.assertEqual(attestation["fix"]["lineageStatus"], "VERIFIED_WITH_RETRY")
        self.assertEqual(
            attestation["fix"]["recoveryClassification"],
            "FLAKY_COMMAND_RECOVERED",
        )
        attempts = attestation["sourceArtifacts"]["attempts"]
        self.assertEqual(len(attempts), 2)
        first_verification = delivery_dir / attempts[0]["verification"]["path"]
        first_verification.unlink()
        with self.assertRaisesRegex(Exception, "invalid delivery artifact"):
            validate_delivery(delivery_dir)

    def test_portable_validation_rejects_rebound_predecessor_assessment_tamper(self) -> None:
        attempt_dir, _ = self._verified_attempt(retry=True)
        delivery_dir, attestation = verify_attempt_delivery(
            attempt_dir,
            output_root=self.delivery_tmp.name,
        )
        first = attestation["sourceArtifacts"]["attempts"][0]
        assessment_path = delivery_dir / first["assessment"]["path"]
        assessment = read_json(assessment_path)
        assessment["remainingRisks"] = ["tampered"]
        write_json(assessment_path, assessment, mode=0o600)
        content = assessment_path.read_bytes()
        first["assessment"]["sha256"] = sha256_bytes(content)
        first["assessment"]["sizeBytes"] = len(content)
        write_json(delivery_dir / "delivery-attestation.json", attestation, mode=0o600)
        delivery_dir = self._rebind_delivery(delivery_dir)
        with self.assertRaisesRegex(Exception, "assessmentSha256"):
            validate_delivery(delivery_dir)

    def test_portable_validation_rejects_rebound_lineage_tamper(self) -> None:
        attempt_dir, _ = self._verified_attempt(retry=True)
        delivery_dir, attestation = verify_attempt_delivery(
            attempt_dir,
            output_root=self.delivery_tmp.name,
        )
        lineage_ref = attestation["sourceArtifacts"]["fixLineage"]
        lineage_path = delivery_dir / lineage_ref["path"]
        lineage = read_json(lineage_path)
        lineage["aggregateStatus"] = "VERIFIED"
        write_json(lineage_path, lineage, mode=0o600)
        content = lineage_path.read_bytes()
        lineage_ref["sha256"] = sha256_bytes(content)
        lineage_ref["sizeBytes"] = len(content)
        attestation["fix"]["lineageStatus"] = "VERIFIED"
        attestation["fix"]["lineageSha256"] = sha256_json(lineage)
        write_json(delivery_dir / "delivery-attestation.json", attestation, mode=0o600)
        delivery_dir = self._rebind_delivery(delivery_dir)
        with self.assertRaisesRegex(Exception, "does not match copied attempt artifacts"):
            validate_delivery(delivery_dir)

    def test_failed_latest_attempt_cannot_be_exported(self) -> None:
        fix_dir = self._prepare("flaky-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        attempt_dir = self._capture_and_finalize(
            fix_dir,
            "flaky-check",
            capture_code=4,
            finalize_code=4,
        )
        completed = run_cli(
            "verify-attempt-delivery",
            "--attempt-dir",
            str(attempt_dir),
            "--output-root",
            self.delivery_tmp.name,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("requires a VERIFIED fix attempt", completed.stderr)

    def test_non_latest_attempt_cannot_be_exported(self) -> None:
        latest_dir, _ = self._verified_attempt(retry=True)
        first_dir = sorted(latest_dir.parent.iterdir(), key=lambda path: path.name)[0]
        completed = run_cli(
            "verify-attempt-delivery",
            "--attempt-dir",
            str(first_dir),
            "--output-root",
            self.delivery_tmp.name,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("requires the latest finalized fix attempt", completed.stderr)

    def test_dirty_or_mismatched_source_produces_failed_delivery(self) -> None:
        attempt_dir, _ = self._verified_attempt()
        (self.target / "app.py").write_text(
            "def answer():\n    return 43\n", encoding="utf-8"
        )
        delivery_dir, attestation = verify_attempt_delivery(
            attempt_dir,
            output_root=self.delivery_tmp.name,
        )
        self.assertEqual(attestation["status"], "FAILED")
        self.assertFalse(attestation["localSource"]["clean"])
        self.assertFalse(attestation["localSource"]["sourceMatchesVerification"])
        self.assertEqual(validate_delivery(delivery_dir)["attestation"]["status"], "FAILED")

    def test_push_and_ci_evidence_use_delivery_v2(self) -> None:
        attempt_dir, revision = self._verified_attempt()
        with patch(
            "review_craft.delivery._run_read_only_command",
            side_effect=self._fake_commands(revision),
        ):
            delivery_dir, attestation = verify_attempt_delivery(
                attempt_dir,
                verify_push=True,
                github_run=123,
                output_root=self.delivery_tmp.name,
            )
        self.assertEqual(attestation["status"], "VERIFIED")
        for relative in (
            "evidence/git-remote.json",
            "evidence/github-actions-run.json",
        ):
            self.assertEqual(
                read_json(delivery_dir / relative)["schemaVersion"],
                "review-craft.delivery.v2",
            )
        validate_delivery(delivery_dir)

    def test_output_inside_target_is_rejected(self) -> None:
        attempt_dir, _ = self._verified_attempt()
        completed = run_cli(
            "verify-attempt-delivery",
            "--attempt-dir",
            str(attempt_dir),
            "--output-root",
            str(self.target / "deliveries"),
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("inside the target repository", completed.stderr)


if __name__ == "__main__":
    unittest.main()
