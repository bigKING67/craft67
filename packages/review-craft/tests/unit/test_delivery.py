from __future__ import annotations

# tests.support adds the canonical runtime library to sys.path before product imports.
# ruff: noqa: I001

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

from tests.support import ROOT, make_target, populate_valid_run, run_cli

from review_craft.delivery import verify_delivery
from review_craft.delivery_validation import validate_delivery
from review_craft.jsonio import read_json, sha256_bytes, write_json
from review_craft.repository import inventory
from review_craft.repository_analysis import build_dependency_map


class DeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target_tmp, self.target = make_target(commit=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://example.invalid/review.git"],
            cwd=self.target,
            check=True,
        )
        self.run_tmp = tempfile.TemporaryDirectory(prefix="review-craft-runs-")
        self.fix_tmp = tempfile.TemporaryDirectory(prefix="review-craft-fixes-")
        self.delivery_tmp = tempfile.TemporaryDirectory(prefix="review-craft-deliveries-")
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
                                    "from pathlib import Path; "
                                    "assert 'return 42' in Path('app.py').read_text()"
                                ),
                            ]
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
            self.run_tmp.name,
        )
        self.assertEqual(created.returncode, 0, created.stderr)
        run_dir = Path(json.loads(created.stdout)["runDir"])
        populate_valid_run(run_dir)
        finalized = run_cli("finalize", "--run-dir", str(run_dir))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        prepared = run_cli(
            "prepare-fix",
            "--run-dir",
            str(run_dir),
            "--finding",
            "RC-FINDING-001",
            "--command",
            "check",
            "--output-root",
            self.fix_tmp.name,
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        self.fix_dir = Path(json.loads(prepared.stdout)["fixDir"])
        (self.target / "app.py").write_text(
            "def answer():\n    return 42\n",
            encoding="utf-8",
        )
        assessment = Path(self.fix_tmp.name) / "assessment.json"
        assessment.write_text(
            json.dumps(
                {
                    "documentType": "review-craft.fix-assessment",
                    "schemaVersion": "review-craft.fix.v1",
                    "kind": "AGENT_ASSISTED",
                    "assessor": "Review Craft delivery test",
                    "assessedAt": "2026-07-31T03:00:00Z",
                    "findings": [
                        {
                            "findingId": "RC-FINDING-001",
                            "status": "RESOLVED",
                            "rationale": "The focused fixture now returns the contracted value.",
                            "evidenceRefs": ["change:app.py", "command:check"],
                        }
                    ],
                    "remainingRisks": ["Remote delivery had not yet been checked."],
                }
            ),
            encoding="utf-8",
        )
        verified = run_cli(
            "verify-fix",
            "--fix-dir",
            str(self.fix_dir),
            "--assessment",
            str(assessment),
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)
        subprocess.run(
            ["git", "add", "--", "app.py", ".review-craft.json"],
            cwd=self.target,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "apply verified fixture fix"],
            cwd=self.target,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        self.revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def tearDown(self) -> None:
        self.delivery_tmp.cleanup()
        self.fix_tmp.cleanup()
        self.run_tmp.cleanup()
        self.target_tmp.cleanup()

    @staticmethod
    def _capture(argv: list[str], stdout: bytes, *, exit_code: int = 0) -> tuple[dict, bytes]:
        return (
            {
                "argv": argv,
                "cwd": ".",
                "startedAt": "2026-07-31T04:00:00Z",
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

    def _fake_commands(
        self,
        *,
        remote_sha: str | None = None,
        ci: dict | None = None,
        missing_gh: bool = False,
    ):
        remote_sha = remote_sha or self.revision

        def run(argv: list[str], *, cwd: Path, captured_at: str | None = None):
            del cwd, captured_at
            if argv[:2] == ["git", "ls-remote"]:
                ref = argv[-1]
                return self._capture(argv, f"{remote_sha}\t{ref}\n".encode())
            if argv[:3] == ["gh", "run", "view"]:
                if missing_gh:
                    command, stdout = self._capture(argv, b"")
                    command["exitCode"] = None
                    command["errorKind"] = "COMMAND_NOT_FOUND"
                    return command, stdout
                return self._capture(argv, json.dumps(ci or {}).encode())
            raise AssertionError(f"unexpected command: {argv}")

        return run

    def _successful_ci(self) -> dict:
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
                    "startedAt": "2026-07-31T04:00:00Z",
                    "completedAt": "2026-07-31T04:01:00Z",
                    "url": "https://example.invalid/actions/jobs/1",
                }
            ],
            "headSha": self.revision,
            "createdAt": "2026-07-31T04:00:00Z",
            "updatedAt": "2026-07-31T04:01:00Z",
        }

    def test_local_only_delivery_is_partial_and_portable(self) -> None:
        completed = run_cli(
            "verify-delivery",
            "--fix-dir",
            str(self.fix_dir),
            "--output-root",
            self.delivery_tmp.name,
        )
        self.assertEqual(completed.returncode, 3, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "PARTIAL")
        delivery_dir = Path(payload["deliveryDir"])
        self.fix_tmp.cleanup()
        self.run_tmp.cleanup()
        self.target_tmp.cleanup()
        validated = run_cli(
            "validate-delivery", "--delivery-dir", str(delivery_dir)
        )
        self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_git_status_failure_does_not_create_delivery_attestation(self) -> None:
        subprocess.run(
            ["git", "config", "status.showUntrackedFiles", "invalid"],
            cwd=self.target,
            check=True,
        )
        completed = run_cli(
            "verify-delivery",
            "--fix-dir",
            str(self.fix_dir),
            "--output-root",
            self.delivery_tmp.name,
        )
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("git status failed", completed.stderr)
        self.assertEqual(list(Path(self.delivery_tmp.name).iterdir()), [])

    def test_hidden_untracked_verified_source_fails_delivery(self) -> None:
        for args in (
            ["rm", "--cached", "--", "app.py"],
            ["commit", "-m", "leave verified source untracked"],
            ["config", "status.showUntrackedFiles", "no"],
        ):
            subprocess.run(["git", *args], cwd=self.target, check=True, capture_output=True)
        completed = run_cli(
            "verify-delivery", "--fix-dir", str(self.fix_dir),
            "--output-root", self.delivery_tmp.name,
        )
        self.assertEqual(completed.returncode, 4, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAILED")
        attestation = read_json(Path(payload["deliveryDir"]) / "delivery-attestation.json")
        self.assertTrue(attestation["localSource"]["sourceMatchesVerification"])
        self.assertFalse(attestation["localSource"]["clean"])
        validated = run_cli("validate-delivery", "--delivery-dir", payload["deliveryDir"])
        self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_public_delivery_schema_accepts_generated_attestation(self) -> None:
        _, attestation = verify_delivery(
            self.fix_dir,
            output_root=self.delivery_tmp.name,
        )
        schema = read_json(
            ROOT / "skills/review-craft/schemas/delivery-attestation.schema.json"
        )
        errors = list(
            Draft202012Validator(
                schema,
                format_checker=FormatChecker(),
            ).iter_errors(attestation)
        )
        self.assertEqual(errors, [])

    def test_source_fingerprint_mismatch_and_dirty_worktree_fail(self) -> None:
        (self.target / "app.py").write_text("def answer():\n    return 43\n", encoding="utf-8")
        delivery_dir, attestation = verify_delivery(
            self.fix_dir,
            output_root=self.delivery_tmp.name,
        )
        self.assertEqual(attestation["status"], "FAILED")
        self.assertFalse(attestation["localSource"]["clean"])
        self.assertFalse(attestation["localSource"]["sourceMatchesVerification"])
        self.assertEqual(validate_delivery(delivery_dir)["attestation"]["status"], "FAILED")

    def test_push_match_is_verified(self) -> None:
        with patch(
            "review_craft.delivery._run_read_only_command",
            side_effect=self._fake_commands(),
        ):
            delivery_dir, attestation = verify_delivery(
                self.fix_dir,
                verify_push=True,
                output_root=self.delivery_tmp.name,
            )
        self.assertEqual(attestation["status"], "VERIFIED")
        self.assertEqual(attestation["push"]["remoteSha"], self.revision)
        validate_delivery(delivery_dir)

    def test_push_mismatch_fails(self) -> None:
        with patch(
            "review_craft.delivery._run_read_only_command",
            side_effect=self._fake_commands(remote_sha="0" * 40),
        ):
            _, attestation = verify_delivery(
                self.fix_dir,
                verify_push=True,
                output_root=self.delivery_tmp.name,
            )
        self.assertEqual(attestation["status"], "FAILED")
        self.assertEqual(attestation["push"]["status"], "FAILED")

    def test_successful_github_run_binds_jobs_and_head(self) -> None:
        with patch(
            "review_craft.delivery._run_read_only_command",
            side_effect=self._fake_commands(ci=self._successful_ci()),
        ):
            delivery_dir, attestation = verify_delivery(
                self.fix_dir,
                verify_push=True,
                github_run=123,
                output_root=self.delivery_tmp.name,
            )
        self.assertEqual(attestation["status"], "VERIFIED")
        self.assertEqual(attestation["githubActions"]["status"], "VERIFIED")
        self.assertEqual(len(attestation["githubActions"]["jobs"]), 1)
        validate_delivery(delivery_dir)

    def test_github_run_head_mismatch_fails(self) -> None:
        ci = self._successful_ci()
        ci["headSha"] = "0" * 40
        with patch(
            "review_craft.delivery._run_read_only_command",
            side_effect=self._fake_commands(ci=ci),
        ):
            _, attestation = verify_delivery(
                self.fix_dir,
                github_run=123,
                output_root=self.delivery_tmp.name,
            )
        self.assertEqual(attestation["githubActions"]["status"], "FAILED")

    def test_failed_and_incomplete_github_runs_fail(self) -> None:
        for status, conclusion in (("completed", "failure"), ("in_progress", None)):
            with self.subTest(status=status, conclusion=conclusion):
                ci = self._successful_ci()
                ci["status"] = status
                ci["conclusion"] = conclusion
                with patch(
                    "review_craft.delivery._run_read_only_command",
                    side_effect=self._fake_commands(ci=ci),
                ):
                    _, attestation = verify_delivery(
                        self.fix_dir,
                        github_run=123,
                        output_root=self.delivery_tmp.name,
                    )
                self.assertEqual(attestation["githubActions"]["status"], "FAILED")

    def test_missing_gh_is_recorded_as_failed_proof(self) -> None:
        with patch(
            "review_craft.delivery._run_read_only_command",
            side_effect=self._fake_commands(missing_gh=True),
        ):
            delivery_dir, attestation = verify_delivery(
                self.fix_dir,
                github_run=123,
                output_root=self.delivery_tmp.name,
            )
        self.assertEqual(attestation["githubActions"]["status"], "FAILED")
        self.assertIn("COMMAND_NOT_FOUND", attestation["githubActions"]["failureReasons"][0])
        validate_delivery(delivery_dir)

    def test_repeated_attestations_create_independent_directories(self) -> None:
        kwargs = {
            "output_root": self.delivery_tmp.name,
            "attested_at": "2026-07-31T05:00:00Z",
        }
        first, first_attestation = verify_delivery(self.fix_dir, **kwargs)
        second, second_attestation = verify_delivery(self.fix_dir, **kwargs)
        self.assertNotEqual(first, second)
        self.assertEqual(first_attestation["deliveryId"] + "-2", second_attestation["deliveryId"])
        validate_delivery(first)
        validate_delivery(second)

    def test_copied_fix_artifact_tampering_is_detected(self) -> None:
        delivery_dir, _ = verify_delivery(
            self.fix_dir,
            output_root=self.delivery_tmp.name,
        )
        plan_path = delivery_dir / "source/fix-plan.json"
        plan = read_json(plan_path)
        plan["review"]["repositoryName"] = "tampered"
        write_json(plan_path, plan)
        with self.assertRaisesRegex(Exception, "sha256 mismatch"):
            validate_delivery(delivery_dir)

    def test_attestation_tampering_is_detected_by_content_bound_id(self) -> None:
        delivery_dir, _ = verify_delivery(
            self.fix_dir,
            output_root=self.delivery_tmp.name,
        )
        path = delivery_dir / "delivery-attestation.json"
        attestation = read_json(path)
        attestation["remainingRisks"].append("tampered")
        write_json(path, attestation)
        with self.assertRaisesRegex(Exception, "content-bound"):
            validate_delivery(delivery_dir)

    @unittest.skipIf(os.name == "nt", "symlink creation is not portable on Windows CI")
    def test_symlinked_delivery_artifact_is_rejected(self) -> None:
        delivery_dir, _ = verify_delivery(
            self.fix_dir,
            output_root=self.delivery_tmp.name,
        )
        path = delivery_dir / "source/fix-plan.json"
        real = delivery_dir / "source/real-plan.json"
        path.rename(real)
        path.symlink_to(real.name)
        with self.assertRaisesRegex(Exception, "must not be a symlink"):
            validate_delivery(delivery_dir)

    def test_raw_command_output_is_not_stored(self) -> None:
        secret = "secret-token-must-not-leak"

        def command(argv: list[str], *, cwd: Path, captured_at: str | None = None):
            del cwd, captured_at
            ref = argv[-1]
            stdout = f"{self.revision}\t{ref}\n{secret}\n".encode()
            return self._capture(argv, stdout)

        with patch("review_craft.delivery._run_read_only_command", side_effect=command):
            delivery_dir, _ = verify_delivery(
                self.fix_dir,
                verify_push=True,
                output_root=self.delivery_tmp.name,
            )
        rendered = "\n".join(
            path.read_text(encoding="utf-8")
            for path in delivery_dir.rglob("*.json")
        )
        self.assertNotIn(secret, rendered)

    def test_cli_rejects_non_positive_github_run_id(self) -> None:
        completed = run_cli(
            "verify-delivery",
            "--fix-dir",
            str(self.fix_dir),
            "--github-run",
            "0",
            "--output-root",
            self.delivery_tmp.name,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("positive GitHub Actions run id", completed.stderr)

    def test_delivery_output_inside_target_is_rejected_without_mutation(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=self.target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        with self.assertRaisesRegex(ValueError, "resolves inside the target repository"):
            verify_delivery(
                self.fix_dir,
                output_root=self.target / "delivery-output",
            )
        after = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=self.target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(after, before)

    def test_delivery_contract_dependencies_are_one_way(self) -> None:
        records, _ = inventory(ROOT)
        dependency_map = build_dependency_map(ROOT, records)
        edges = {(row["from"], row["to"]) for row in dependency_map["edges"]}
        runtime = "skills/review-craft/lib/review_craft"
        delivery = f"{runtime}/delivery.py"
        validation = f"{runtime}/delivery_validation.py"
        contract = f"{runtime}/delivery_contract.py"
        self.assertNotIn((validation, delivery), edges)
        self.assertIn((delivery, contract), edges)
        self.assertIn((validation, contract), edges)


if __name__ == "__main__":
    unittest.main()
