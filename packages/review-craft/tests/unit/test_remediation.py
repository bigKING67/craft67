from __future__ import annotations

# tests.support adds the canonical runtime library to sys.path before product imports.
# ruff: noqa: I001

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tests.support import ROOT, RUNTIME_SCRIPT, make_target, populate_valid_run, run_cli

from review_craft.evidence import run_configured_command
from review_craft.jsonio import read_json, read_jsonl, sha256_json, write_json, write_jsonl
from review_craft.repository import inventory
from review_craft.repository_analysis import build_dependency_map
from review_craft.semantic_evidence import receipt_identity_payload


class RemediationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target_tmp, self.target = make_target(commit=True)
        self.output_tmp = tempfile.TemporaryDirectory(prefix="review-craft-runs-")
        self.fix_tmp = tempfile.TemporaryDirectory(prefix="review-craft-fixes-")
        self.flake_marker = Path(self.fix_tmp.name) / "flake-marker"
        (self.target / "auth.json").write_text(
            '{"token":"private-v1"}\n', encoding="utf-8"
        )
        config = self.target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "exclude": ["auth.json"],
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
                        "mutate": {
                            "argv": [
                                sys.executable,
                                "-c",
                                (
                                    "from pathlib import Path; "
                                    "Path('app.py').write_text('def answer():\\n    return 99\\n')"
                                ),
                            ]
                        },
                        "semantic-fail": {
                            "argv": [
                                sys.executable,
                                "-c",
                                (
                                    "import json; from pathlib import Path; "
                                    "assert 'return 42' in Path('app.py').read_text(); "
                                    "print(json.dumps({'checks': {'fixed': False}}))"
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
                        "after": {
                            "argv": [sys.executable, "-c", "print('must be skipped')"]
                        },
                        "slow-check": {
                            "argv": [
                                sys.executable,
                                "-c",
                                (
                                    "import time; from pathlib import Path; "
                                    "time.sleep(0.5); "
                                    "assert 'return 42' in Path('app.py').read_text()"
                                ),
                            ]
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
                        "measure-check": {
                            "argv": [
                                sys.executable,
                                "-c",
                                (
                                    "import json; from pathlib import Path; "
                                    "assert 'return 42' in Path('app.py').read_text(); "
                                    "print(json.dumps({'checks': {'fixed': True}, "
                                    "'metrics': {'startupMs': 123.5}}))"
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
                        }
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
            self.output_tmp.name,
        )
        if created.returncode != 0:
            raise AssertionError(created.stderr)
        self.run_dir = Path(json.loads(created.stdout)["runDir"])
        populate_valid_run(self.run_dir)
        finalized = run_cli("finalize", "--run-dir", str(self.run_dir))
        if finalized.returncode != 0:
            raise AssertionError(finalized.stderr)

    def tearDown(self) -> None:
        self.fix_tmp.cleanup()
        self.output_tmp.cleanup()
        self.target_tmp.cleanup()

    def _prepare(self, command: str = "check") -> Path:
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

    def _assessment(
        self, *, status: str, evidence: list[str], kind: str = "AGENT_ASSISTED"
    ) -> Path:
        path = Path(self.fix_tmp.name) / f"assessment-{status.lower()}.json"
        path.write_text(
            json.dumps(
                {
                    "documentType": "review-craft.fix-assessment",
                    "schemaVersion": "review-craft.fix.v1",
                    "kind": kind,
                    "assessor": "Review Craft test",
                    "assessedAt": "2026-07-30T03:00:00Z",
                    "findings": [
                        {
                            "findingId": "RC-FINDING-001",
                            "status": status,
                            "rationale": "The focused source correction matches the contract.",
                            "evidenceRefs": evidence,
                        }
                    ],
                    "remainingRisks": [],
                }
            ),
            encoding="utf-8",
        )
        return path

    def _attempt_assessment(
        self,
        attempt_dir: Path,
        *,
        command: str,
        status: str = "RESOLVED",
        evidence_refs: list[str] | None = None,
        measurements: list[dict[str, object]] | None = None,
        assessed_at: str | None = None,
    ) -> Path:
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
                    "assessor": "Review Craft attempt test",
                    "assessedAt": assessed_at or evidence["completedAt"],
                    "findings": [
                        {
                            "findingId": "RC-FINDING-001",
                            "status": status,
                            "rationale": "Assessment was written from captured receipts.",
                            "evidenceRefs": evidence_refs
                            or [
                                "change:app.py",
                                f"claim:{command}:fixed-behavior-check",
                            ],
                        }
                    ],
                    "measurements": measurements or [],
                    "remainingRisks": [],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_prepare_is_read_only_and_binds_selected_finding(self) -> None:
        before = (self.target / "app.py").read_bytes()
        fix_dir = self._prepare()
        self.assertEqual((self.target / "app.py").read_bytes(), before)
        plan = json.loads((fix_dir / "fix-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["authorization"]["sourceMutation"], "EXPLICIT_USER_REQUIRED")
        self.assertFalse(plan["authorization"]["runtimeMutatesSource"])
        self.assertEqual(
            [row["findingId"] for row in plan["selections"]], ["RC-FINDING-001"]
        )
        state = read_json(fix_dir / "fix-state.json")
        self.assertEqual(state["sourceConfiguration"]["exclude"], ["auth.json"])
        self.assertNotIn("auth.json", {row["path"] for row in state["baselineFiles"]})
        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir), "--allow-prepared")
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(json.loads(validated.stdout)["status"], "PREPARED")

    def test_legacy_fix_state_derives_source_scope_from_sealed_review(self) -> None:
        fix_dir = self._prepare()
        state = read_json(fix_dir / "fix-state.json")
        state.pop("sourceConfiguration")
        state.pop("sourceConfigurationSha256")
        write_json(fix_dir / "fix-state.json", state)

        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir), "--allow-prepared")
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(json.loads(validated.stdout)["status"], "PREPARED")

    def test_fix_source_scope_is_bound_to_review_provenance(self) -> None:
        fix_dir = self._prepare()
        state = read_json(fix_dir / "fix-state.json")
        state["sourceConfiguration"]["exclude"] = []
        state["sourceConfigurationSha256"] = sha256_json(
            state["sourceConfiguration"]
        )
        write_json(fix_dir / "fix-state.json", state)

        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir), "--allow-prepared")
        self.assertEqual(validated.returncode, 2)
        self.assertIn("does not match review provenance", validated.stderr)

    def test_verify_binds_changes_commands_and_assessment(self) -> None:
        fix_dir = self._prepare()
        (self.target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        (self.target / "auth.json").write_text(
            '{"token":"private-v2"}\n', encoding="utf-8"
        )
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:app.py", "command:check"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)
        result = json.loads(verified.stdout)
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual([row["path"] for row in result["changes"]], ["app.py"])
        self.assertEqual(result["commands"][0]["exitCode"], 0)
        self.assertTrue(result["commands"][0]["semanticEvidenceValid"])
        self.assertEqual(result["findingResults"][0]["locationPathsChanged"], ["app.py"])
        schema_root = ROOT / "skills/review-craft/schemas"
        for artifact, schema_name in (
            ("fix-plan.json", "fix-plan.schema.json"),
            ("fix-assessment.json", "fix-assessment.schema.json"),
            ("fix-verification.json", "fix-verification.schema.json"),
        ):
            schema = json.loads((schema_root / schema_name).read_text(encoding="utf-8"))
            instance = json.loads((fix_dir / artifact).read_text(encoding="utf-8"))
            errors = list(
                Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
                    instance
                )
            )
            self.assertEqual(errors, [], f"{artifact}: {errors}")
        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir))
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(json.loads(validated.stdout)["status"], "VERIFIED")

    def test_verify_without_source_change_is_not_success(self) -> None:
        fix_dir = self._prepare()
        assessment = self._assessment(
            status="UNRESOLVED",
            evidence=["manual:no source modification was applied"],
            kind="HUMAN",
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 5, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["status"], "NO_CHANGES")

    def test_tampered_command_output_breaks_fix_validation(self) -> None:
        fix_dir = self._prepare()
        (self.target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:app.py", "command:check"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)
        result = json.loads(verified.stdout)
        receipt_id = result["commands"][0]["receiptId"]
        (fix_dir / f"evidence/commands/{receipt_id}.stdout").write_text(
            "tampered\n", encoding="utf-8"
        )
        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir))
        self.assertEqual(validated.returncode, 2)
        self.assertIn("stdoutSha256 mismatch", validated.stderr)

    def test_tampered_command_argv_breaks_fix_validation(self) -> None:
        fix_dir = self._prepare()
        (self.target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:app.py", "command:check"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)

        receipts = read_jsonl(fix_dir / "evidence/commands.jsonl")
        receipt = receipts[0]
        old_id = receipt["id"]
        receipt["argv"] = [sys.executable, "-c", "print('never executed')"]
        new_id = sha256_json(receipt_identity_payload(receipt))[:16]
        receipt["id"] = new_id
        for suffix, field in (("stdout", "stdoutArtifact"), ("stderr", "stderrArtifact")):
            old_path = fix_dir / f"evidence/commands/{old_id}.{suffix}"
            new_path = fix_dir / f"evidence/commands/{new_id}.{suffix}"
            old_path.rename(new_path)
            receipt[field] = f"evidence/commands/{new_id}.{suffix}"
        write_jsonl(fix_dir / "evidence/commands.jsonl", receipts)

        result_path = fix_dir / "fix-verification.json"
        result = read_json(result_path)
        result["commands"][0]["receiptId"] = new_id
        result["commands"][0]["receiptSha256"] = sha256_json(receipt)
        write_json(result_path, result)

        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir))
        self.assertEqual(validated.returncode, 2)
        self.assertIn("argv does not match configured command", validated.stderr)

    def test_failed_verification_command_cannot_produce_verified_status(self) -> None:
        fix_dir = self._prepare()
        (self.target / "app.py").write_text("def answer():\n    return 43\n", encoding="utf-8")
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:app.py", "command:check"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 4, verified.stderr)
        result = json.loads(verified.stdout)
        self.assertEqual(result["status"], "FAILED")
        self.assertNotEqual(result["commands"][0]["exitCode"], 0)
        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir))
        self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_failed_semantic_assertion_cannot_produce_verified_status(self) -> None:
        fix_dir = self._prepare("semantic-fail")
        (self.target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:app.py", "command:semantic-fail"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 4, verified.stderr)
        result = json.loads(verified.stdout)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["commands"][0]["exitCode"], 0)
        self.assertFalse(result["commands"][0]["semanticEvidenceValid"])
        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir))
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(json.loads(validated.stdout)["status"], "FAILED")

    def test_source_drift_after_verification_breaks_validation(self) -> None:
        fix_dir = self._prepare()
        (self.target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:app.py", "command:check"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)
        (self.target / "app.py").write_text("def answer():\n    return 44\n", encoding="utf-8")
        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir))
        self.assertEqual(validated.returncode, 2)
        self.assertIn("target source changed after verification", validated.stderr)

    def test_assessment_must_bind_real_post_fix_evidence(self) -> None:
        fix_dir = self._prepare()
        (self.target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:not-changed.py", "command:check"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 2)
        self.assertIn("change evidence is not present", verified.stderr)

    def test_mutating_verification_command_stops_later_commands(self) -> None:
        prepared = run_cli(
            "prepare-fix",
            "--run-dir",
            str(self.run_dir),
            "--finding",
            "RC-FINDING-001",
            "--command",
            "mutate",
            "--command",
            "after",
            "--output-root",
            self.fix_tmp.name,
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        fix_dir = Path(json.loads(prepared.stdout)["fixDir"])
        (self.target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        assessment = self._assessment(
            status="REGRESSED",
            evidence=["change:app.py", "command:mutate"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 4, verified.stderr)
        result = json.loads(verified.stdout)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual([row["name"] for row in result["commands"]], ["mutate"])
        self.assertEqual(result["skippedCommands"], ["after"])
        self.assertTrue(result["commands"][0]["repositoryMutationDetected"])
        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir))
        self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_concurrent_verify_allows_one_terminal_result(self) -> None:
        prepared = run_cli(
            "prepare-fix",
            "--run-dir",
            str(self.run_dir),
            "--finding",
            "RC-FINDING-001",
            "--command",
            "slow-check",
            "--output-root",
            self.fix_tmp.name,
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        fix_dir = Path(json.loads(prepared.stdout)["fixDir"])
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:app.py", "command:slow-check"],
        )
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        argv = [
            sys.executable,
            str(RUNTIME_SCRIPT),
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        ]
        processes = [
            subprocess.Popen(
                argv,
                cwd=ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for _ in range(2)
        ]
        results = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=15)
            results.append((process.returncode, stdout, stderr))

        self.assertEqual(sorted(row[0] for row in results), [0, 2], results)
        success = next(row for row in results if row[0] == 0)
        rejected = next(row for row in results if row[0] == 2)
        self.assertEqual(json.loads(success[1])["status"], "VERIFIED")
        self.assertIn("fix session is already completed", rejected[2])
        receipts = read_jsonl(fix_dir / "evidence/commands.jsonl")
        verification = read_json(fix_dir / "fix-verification.json")
        self.assertEqual(len(receipts), 1)
        self.assertEqual(
            [row["receiptId"] for row in verification["commands"]],
            [receipts[0]["id"]],
        )
        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir))
        self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_incomplete_attempt_receipt_requires_new_fix_session(self) -> None:
        fix_dir = self._prepare()
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        state = read_json(fix_dir / "fix-state.json")
        run_configured_command(
            session_dir=fix_dir,
            target=self.target,
            commands=state["commands"],
            command_name="check",
            allow_repository_mutation=False,
        )
        invalid_prepared = run_cli(
            "validate-fix", "--fix-dir", str(fix_dir), "--allow-prepared"
        )
        self.assertEqual(invalid_prepared.returncode, 2)
        self.assertIn(
            "prepared/incomplete fix session must not contain command receipts",
            invalid_prepared.stderr,
        )
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:app.py", "command:check"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 2)
        self.assertIn("contains prior command receipts", verified.stderr)
        self.assertEqual(len(read_jsonl(fix_dir / "evidence/commands.jsonl")), 1)

    def test_orphan_receipt_breaks_completed_fix_validation(self) -> None:
        fix_dir = self._prepare()
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        assessment = self._assessment(
            status="RESOLVED",
            evidence=["change:app.py", "command:check"],
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)
        state = read_json(fix_dir / "fix-state.json")
        run_configured_command(
            session_dir=fix_dir,
            target=self.target,
            commands=state["commands"],
            command_name="check",
            allow_repository_mutation=False,
        )

        validated = run_cli("validate-fix", "--fix-dir", str(fix_dir))
        self.assertEqual(validated.returncode, 2)
        self.assertIn("receipt ledger must exactly match", validated.stderr)

    def test_attempt_lineage_preserves_failure_and_records_flaky_recovery(self) -> None:
        fix_dir = self._prepare("flaky-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )

        first_capture = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        self.assertEqual(first_capture.returncode, 4, first_capture.stderr)
        first_dir = Path(json.loads(first_capture.stdout)["attemptDir"])
        first_assessment = self._attempt_assessment(
            first_dir, command="flaky-check"
        )
        first_finalize = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(first_dir),
            "--assessment",
            str(first_assessment),
        )
        self.assertEqual(first_finalize.returncode, 4, first_finalize.stderr)
        self.assertEqual(json.loads(first_finalize.stdout)["status"], "FAILED")

        second_capture = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        self.assertEqual(second_capture.returncode, 0, second_capture.stderr)
        second_dir = Path(json.loads(second_capture.stdout)["attemptDir"])
        second_assessment = self._attempt_assessment(
            second_dir, command="flaky-check"
        )
        second_finalize = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(second_dir),
            "--assessment",
            str(second_assessment),
        )
        self.assertEqual(second_finalize.returncode, 0, second_finalize.stderr)
        second_result = json.loads(second_finalize.stdout)
        self.assertEqual(second_result["status"], "VERIFIED")
        self.assertEqual(
            second_result["recoveryClassification"], "FLAKY_COMMAND_RECOVERED"
        )

        listed = run_cli("list-fix-attempts", "--fix-dir", str(fix_dir))
        self.assertEqual(listed.returncode, 0, listed.stderr)
        lineage = json.loads(listed.stdout)
        self.assertEqual(lineage["aggregateStatus"], "VERIFIED_WITH_RETRY")
        self.assertEqual(
            [row["status"] for row in lineage["attempts"]],
            ["FAILED", "VERIFIED"],
        )
        self.assertTrue((first_dir / "attempt-verification.json").is_file())
        self.assertTrue((second_dir / "attempt-verification.json").is_file())
        for attempt_dir in (first_dir, second_dir):
            validated = run_cli(
                "validate-fix-attempt",
                "--attempt-dir",
                str(attempt_dir),
                "--snapshot-only",
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_attempt_assessment_is_post_command_and_measurement_bound(self) -> None:
        fix_dir = self._prepare("measure-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        captured = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        self.assertEqual(captured.returncode, 0, captured.stderr)
        attempt_dir = Path(json.loads(captured.stdout)["attemptDir"])
        assessment = self._attempt_assessment(
            attempt_dir,
            command="measure-check",
            evidence_refs=[
                "change:app.py",
                "claim:measure-check:fixed-behavior-check",
                "measurement:startup-ms",
            ],
            measurements=[
                {
                    "id": "startup-ms",
                    "command": "measure-check",
                    "jsonPointer": "/metrics/startupMs",
                    "value": 123.5,
                    "unit": "ms",
                }
            ],
        )
        finalized = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        result = json.loads(finalized.stdout)
        self.assertEqual(result["measurements"][0]["value"], 123.5)
        self.assertEqual(result["status"], "VERIFIED")

    def test_attempt_rejects_measurement_conflicting_with_receipt(self) -> None:
        fix_dir = self._prepare("measure-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        captured = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        attempt_dir = Path(json.loads(captured.stdout)["attemptDir"])
        assessment = self._attempt_assessment(
            attempt_dir,
            command="measure-check",
            evidence_refs=["change:app.py", "measurement:startup-ms"],
            measurements=[
                {
                    "id": "startup-ms",
                    "command": "measure-check",
                    "jsonPointer": "/metrics/startupMs",
                    "value": 120,
                }
            ],
        )
        finalized = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(finalized.returncode, 2)
        self.assertIn("value conflicts with captured command evidence", finalized.stderr)
        self.assertFalse((attempt_dir / "fix-assessment.json").exists())
        self.assertFalse((attempt_dir / "attempt-verification.json").exists())

    def test_attempt_rejects_assessment_before_evidence_completion(self) -> None:
        fix_dir = self._prepare("measure-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        captured = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        attempt_dir = Path(json.loads(captured.stdout)["attemptDir"])
        assessment = self._attempt_assessment(
            attempt_dir,
            command="measure-check",
            assessed_at="2020-01-01T00:00:00Z",
        )
        finalized = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(finalized.returncode, 2)
        self.assertIn("must not precede evidence completion", finalized.stderr)

    def test_attempt_rejects_future_assessment_before_terminal_write(self) -> None:
        fix_dir = self._prepare("measure-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        captured = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        attempt_dir = Path(json.loads(captured.stdout)["attemptDir"])
        assessment = self._attempt_assessment(
            attempt_dir,
            command="measure-check",
            assessed_at="2099-01-01T00:00:00Z",
        )
        finalized = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(finalized.returncode, 2)
        self.assertIn("precedes evidence or assessment", finalized.stderr)
        self.assertFalse((attempt_dir / "fix-assessment.json").exists())
        self.assertFalse((attempt_dir / "attempt-verification.json").exists())

    def test_attempt_retry_rejects_source_or_git_status_drift(self) -> None:
        fix_dir = self._prepare("flaky-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        first_capture = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        first_dir = Path(json.loads(first_capture.stdout)["attemptDir"])
        assessment = self._attempt_assessment(first_dir, command="flaky-check")
        finalized = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(first_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(finalized.returncode, 4, finalized.stderr)
        (self.target / "extra.py").write_text("value = 1\n", encoding="utf-8")
        retry = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        self.assertEqual(retry.returncode, 2)
        self.assertIn("Git status changed", retry.stderr)
        self.assertEqual(len(list((fix_dir / "attempts").iterdir())), 1)

    def test_concurrent_attempt_capture_leaves_one_awaiting_assessment(self) -> None:
        fix_dir = self._prepare("slow-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        argv = [
            sys.executable,
            str(RUNTIME_SCRIPT),
            "capture-fix-attempt",
            "--fix-dir",
            str(fix_dir),
        ]
        processes = [
            subprocess.Popen(
                argv,
                cwd=ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for _ in range(2)
        ]
        results = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=15)
            results.append((process.returncode, stdout, stderr))
        self.assertEqual(sorted(row[0] for row in results), [0, 2], results)
        rejected = next(row for row in results if row[0] == 2)
        self.assertIn("must be finalized", rejected[2])
        attempts = [path for path in (fix_dir / "attempts").iterdir() if path.is_dir()]
        self.assertEqual(len(attempts), 1)

    def test_attempt_tamper_and_deleted_predecessor_break_lineage(self) -> None:
        fix_dir = self._prepare("flaky-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        first_capture = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        first_dir = Path(json.loads(first_capture.stdout)["attemptDir"])
        first_assessment = self._attempt_assessment(first_dir, command="flaky-check")
        run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(first_dir),
            "--assessment",
            str(first_assessment),
        )
        second_capture = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        second_dir = Path(json.loads(second_capture.stdout)["attemptDir"])
        second_assessment = self._attempt_assessment(second_dir, command="flaky-check")
        run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(second_dir),
            "--assessment",
            str(second_assessment),
        )

        first_assessment_path = first_dir / "fix-assessment.json"
        first_payload = read_json(first_assessment_path)
        first_payload["remainingRisks"] = ["tampered"]
        write_json(first_assessment_path, first_payload)
        tampered = run_cli("list-fix-attempts", "--fix-dir", str(fix_dir))
        self.assertEqual(tampered.returncode, 2)
        self.assertIn("assessmentSha256", tampered.stderr)

        write_json(first_assessment_path, read_json(first_assessment))
        restored = run_cli("list-fix-attempts", "--fix-dir", str(fix_dir))
        self.assertEqual(restored.returncode, 0, restored.stderr)
        shutil.rmtree(first_dir)
        deleted = run_cli("list-fix-attempts", "--fix-dir", str(fix_dir))
        self.assertEqual(deleted.returncode, 2)
        self.assertIn("previous verification is unavailable", deleted.stderr)

    def test_orphan_attempt_receipt_blocks_finalization(self) -> None:
        fix_dir = self._prepare("measure-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        captured = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        attempt_dir = Path(json.loads(captured.stdout)["attemptDir"])
        state = read_json(fix_dir / "fix-state.json")
        run_configured_command(
            session_dir=attempt_dir,
            target=self.target,
            commands=state["commands"],
            command_name="measure-check",
            allow_repository_mutation=False,
            source_configuration=state["sourceConfiguration"],
        )
        assessment = self._attempt_assessment(
            attempt_dir, command="measure-check"
        )
        finalized = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(finalized.returncode, 2)
        self.assertIn("receipt ledger must exactly match", finalized.stderr)

    def test_attempt_finalize_is_single_terminal_write(self) -> None:
        fix_dir = self._prepare("measure-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        captured = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        attempt_dir = Path(json.loads(captured.stdout)["attemptDir"])
        assessment = self._attempt_assessment(
            attempt_dir, command="measure-check"
        )
        first = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        second = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(second.returncode, 2)
        self.assertIn("already finalized", second.stderr)

    def test_tampered_attempt_stdout_breaks_snapshot_validation(self) -> None:
        fix_dir = self._prepare("measure-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        captured = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        attempt_dir = Path(json.loads(captured.stdout)["attemptDir"])
        assessment = self._attempt_assessment(
            attempt_dir, command="measure-check"
        )
        finalized = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        receipt = read_jsonl(attempt_dir / "evidence/commands.jsonl")[0]
        (attempt_dir / receipt["stdoutArtifact"]).write_text(
            '{"checks":{"fixed":false}}\n', encoding="utf-8"
        )
        validated = run_cli(
            "validate-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--snapshot-only",
        )
        self.assertEqual(validated.returncode, 2)
        self.assertIn("stdoutSha256 mismatch", validated.stderr)

    def test_attempt_rejects_unknown_command_reference(self) -> None:
        fix_dir = self._prepare("measure-check")
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n", encoding="utf-8"
        )
        captured = run_cli("capture-fix-attempt", "--fix-dir", str(fix_dir))
        attempt_dir = Path(json.loads(captured.stdout)["attemptDir"])
        assessment = self._attempt_assessment(
            attempt_dir,
            command="measure-check",
            evidence_refs=["change:app.py", "command:not-run"],
        )
        finalized = run_cli(
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(finalized.returncode, 2)
        self.assertIn("command evidence was not run", finalized.stderr)

    def test_remediation_contract_dependencies_are_one_way(self) -> None:
        records, _ = inventory(ROOT)
        dependency_map = build_dependency_map(ROOT, records)
        edges = {(row["from"], row["to"]) for row in dependency_map["edges"]}
        runtime = "skills/review-craft/lib/review_craft"
        remediation = f"{runtime}/remediation.py"
        validation = f"{runtime}/remediation_validation.py"
        contract = f"{runtime}/remediation_contract.py"
        self.assertNotIn((validation, remediation), edges)
        self.assertIn((remediation, contract), edges)
        self.assertIn((validation, contract), edges)


if __name__ == "__main__":
    unittest.main()
