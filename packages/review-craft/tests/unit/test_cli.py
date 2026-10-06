from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tests.support import RUNTIME_LIB, create_run, make_target, run_cli

sys.path.insert(0, str(RUNTIME_LIB))

from review_craft.evidence import run_evidence_command
from review_craft.jsonio import read_json, read_jsonl, sha256_json, write_json, write_jsonl
from review_craft.semantic_evidence import receipt_identity_payload


class CliTests(unittest.TestCase):
    def test_doctor_reports_ready(self) -> None:
        completed = run_cli("doctor", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["ready"])

    def test_preflight_writes_outside_target(self) -> None:
        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        with tempfile.TemporaryDirectory() as output:
            run_dir = create_run(target, Path(output))
            self.assertTrue((run_dir / "review-manifest.json").is_file())
            self.assertFalse(str(run_dir).startswith(str(target)))

    def test_preflight_draft_passes_draft_validation(self) -> None:
        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        with tempfile.TemporaryDirectory() as output:
            run_dir = create_run(target, Path(output))
            completed = run_cli(
                "validate",
                "--run-dir",
                str(run_dir),
                "--allow-draft",
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(json.loads(completed.stdout)["final"])

    def test_non_git_lifecycle_reuses_sensitive_excludes_for_all_fingerprints(self) -> None:
        temporary, target = make_target(git=False)
        self.addCleanup(temporary.cleanup)
        sensitive = target / "auth.json"
        sensitive.write_text('{"token":"private-v1"}\n', encoding="utf-8")
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "exclude": ["auth.json"],
                    "commands": {
                        "rotate-private": {
                            "argv": [
                                sys.executable,
                                "-c",
                                (
                                    "from pathlib import Path; "
                                    "Path('auth.json').write_text('private-v2')"
                                ),
                            ]
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            coverage = json.loads((run_dir / "coverage.json").read_text(encoding="utf-8"))
            self.assertNotIn("auth.json", {row["path"] for row in coverage["files"]})

            evidence = run_cli(
                "run-evidence",
                "--run-dir",
                str(run_dir),
                "--command",
                "rotate-private",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            self.assertFalse(json.loads(evidence.stdout)["repositoryMutationDetected"])

            validated = run_cli(
                "validate",
                "--run-dir",
                str(run_dir),
                "--allow-draft",
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)

            (target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
            invalidated = run_cli(
                "validate",
                "--run-dir",
                str(run_dir),
                "--allow-draft",
            )
            self.assertEqual(invalidated.returncode, 2)
            self.assertIn("source fingerprint changed", invalidated.stderr)

    def test_focus_preflight_records_dimensions_and_detected_profile(self) -> None:
        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        with tempfile.TemporaryDirectory() as output:
            completed = run_cli(
                "preflight",
                "--target",
                str(target),
                "--output-root",
                output,
                "--mode",
                "focus",
                "--focus",
                "architecture,performance",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            run_dir = Path(payload["runDir"])
            scope = json.loads((run_dir / "review-scope.json").read_text(encoding="utf-8"))
            self.assertEqual(scope["mode"], "focus")
            self.assertEqual(scope["dimensions"], ["architecture", "performance"])
            self.assertEqual(scope["profile"]["resolved"], "application")
            self.assertIsNone(scope["diff"])

    def test_auto_profile_uses_only_the_selected_inventory(self) -> None:
        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        (target / "backend").mkdir()
        (target / "backend/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (target / "skills/demo").mkdir(parents=True)
        (target / "skills/demo/SKILL.md").write_text(
            "---\nname: excluded-agent-skill\n---\n",
            encoding="utf-8",
        )
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps({"scope": ["backend"], "exclude": ["skills/**"]}),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            completed = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_dir = Path(json.loads(completed.stdout)["runDir"])
            scope = read_json(run_dir / "review-scope.json")
            coverage = read_json(run_dir / "coverage.json")

        self.assertEqual({row["path"] for row in coverage["files"]}, {"backend/app.py"})
        self.assertEqual(scope["profile"]["resolved"], "application")
        self.assertNotIn("contains an agent SKILL.md", scope["profile"]["signals"])

    def test_diff_preflight_covers_modified_added_and_deleted_files(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        (target / "gone.py").write_text("VALUE = 1\n", encoding="utf-8")
        (target / "SKILL.md").write_text("---\nname: fixture\n---\n", encoding="utf-8")
        subprocess.run(["git", "add", "--", "gone.py", "SKILL.md"], cwd=target, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add deleted fixture"],
            cwd=target,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        (target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        (target / "added.py").write_text("from app import answer\n", encoding="utf-8")
        (target / "gone.py").unlink()
        with tempfile.TemporaryDirectory() as output:
            completed = run_cli(
                "preflight",
                "--target",
                str(target),
                "--output-root",
                output,
                "--mode",
                "diff",
                "--base",
                base,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_dir = Path(json.loads(completed.stdout)["runDir"])
            scope = json.loads((run_dir / "review-scope.json").read_text(encoding="utf-8"))
            coverage = json.loads((run_dir / "coverage.json").read_text(encoding="utf-8"))
            by_path = {row["path"]: row for row in coverage["files"]}
            self.assertEqual(set(by_path), {"added.py", "app.py", "gone.py"})
            self.assertEqual(by_path["added.py"]["diffStatus"], "A")
            self.assertTrue(by_path["added.py"]["untracked"])
            self.assertEqual(by_path["app.py"]["diffStatus"], "M")
            self.assertEqual(by_path["gone.py"]["kind"], "deleted")
            self.assertEqual(scope["diff"]["baseRevision"], base)
            self.assertEqual(scope["profile"]["resolved"], "application")
            validated = run_cli("validate", "--run-dir", str(run_dir), "--allow-draft")
            self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_focus_mode_requires_dimensions(self) -> None:
        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        completed = run_cli("preflight", "--target", str(target), "--mode", "focus")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("focus mode requires", completed.stderr)

    def test_diff_mode_rejects_invalid_base(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        completed = run_cli(
            "preflight",
            "--target",
            str(target),
            "--mode",
            "diff",
            "--base",
            "missing-revision",
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("invalid diff base", completed.stderr)

    def test_diff_focus_records_rename_and_excluded_change(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        (target / "excluded").mkdir()
        (target / "excluded/skip.py").write_text("VALUE = 1\n", encoding="utf-8")
        config = target / ".review-craft.json"
        config.write_text(json.dumps({"exclude": ["excluded/**"]}), encoding="utf-8")
        subprocess.run(
            ["git", "add", "--", ".review-craft.json", "excluded/skip.py"],
            cwd=target,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "add diff fixtures"],
            cwd=target,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(["git", "mv", "app.py", "renamed.py"], cwd=target, check=True)
        (target / "excluded/skip.py").write_text("VALUE = 2\n", encoding="utf-8")
        with tempfile.TemporaryDirectory() as output:
            completed = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
                "--mode",
                "diff",
                "--base",
                base,
                "--focus",
                "architecture,testing",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_dir = Path(json.loads(completed.stdout)["runDir"])
            scope = json.loads((run_dir / "review-scope.json").read_text(encoding="utf-8"))
            coverage = json.loads((run_dir / "coverage.json").read_text(encoding="utf-8"))
            changes = {row["path"]: row for row in scope["diff"]["changes"]}
            self.assertEqual(scope["mode"], "diff")
            self.assertEqual(scope["dimensions"], ["architecture", "testing"])
            self.assertEqual({row["path"] for row in coverage["files"]}, {"renamed.py"})
            self.assertEqual(changes["renamed.py"]["status"], "R")
            self.assertEqual(changes["renamed.py"]["previousPath"], "app.py")
            self.assertTrue(changes["renamed.py"]["inScope"])
            self.assertFalse(changes["excluded/skip.py"]["inScope"])
            self.assertEqual(changes["excluded/skip.py"]["reason"], "matched exclude pattern")

    def test_diff_scope_drift_blocks_draft_validation(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        (target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--output-root",
                output,
                "--mode",
                "diff",
                "--base",
                base,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            (target / "later.py").write_text("VALUE = 1\n", encoding="utf-8")
            validated = run_cli(
                "validate",
                "--run-dir",
                str(run_dir),
                "--allow-draft",
            )
            self.assertEqual(validated.returncode, 2)
            self.assertIn("diff scope changed after preflight", validated.stderr)

    def test_preflight_rejects_output_path_that_resolves_inside_target(self) -> None:
        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        completed = run_cli(
            "preflight",
            "--target",
            str(target),
            "--output-root",
            str(target.parent),
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("resolves inside the target repository", completed.stderr)

    def test_preflight_rejects_unknown_policy_field(self) -> None:
        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps({"policy": {"pretendSafe": True}}),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            completed = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unsupported fields pretendSafe", completed.stderr)

    def test_evidence_command_captures_output_without_shell(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "literal": {
                            "argv": [
                                sys.executable,
                                "-c",
                                "import sys; print(sys.argv[1])",
                                "; touch nope",
                            ],
                            "cwd": ".",
                            "timeoutSeconds": 30,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            completed = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_dir = Path(json.loads(completed.stdout)["runDir"])
            evidence = run_cli("run-evidence", "--run-dir", str(run_dir), "--command", "literal")
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            receipt = json.loads(evidence.stdout)
            stdout = (run_dir / receipt["stdoutArtifact"]).read_text(encoding="utf-8")
            self.assertEqual(stdout.strip(), "; touch nope")
            self.assertFalse((target / "nope").exists())

    def test_evidence_timeout_terminates_descendants_before_receipt_returns(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        ready = Path(temporary.name).parent / f"{Path(temporary.name).name}-child-ready"
        self.addCleanup(ready.unlink, missing_ok=True)
        child_code = (
            "from pathlib import Path; import time; "
            f"Path({str(ready)!r}).write_text('ready'); "
            "time.sleep(2); Path('late.txt').write_text('late')"
        )
        parent_code = (
            "import subprocess, sys, time; "
            f"subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
            "time.sleep(60)"
        )
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "timeout-tree": {
                            "argv": [sys.executable, "-c", parent_code],
                            "timeoutSeconds": 1,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            evidence = run_cli(
                "run-evidence",
                "--run-dir",
                str(run_dir),
                "--command",
                "timeout-tree",
            )
            self.assertEqual(evidence.returncode, 124, evidence.stderr)
            receipt = json.loads(evidence.stdout)
            self.assertTrue(receipt["timedOut"])
            self.assertTrue(ready.is_file(), "descendant did not start before timeout")
            time.sleep(2.5)
            self.assertFalse((target / "late.txt").exists())
            self.assertFalse(receipt["repositoryMutationDetected"])

    def test_evidence_detects_tracked_mutation(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "mutate": {
                            "argv": [
                                sys.executable,
                                "-c",
                                (
                                    "from pathlib import Path; "
                                    "Path('app.py').write_text('changed')"
                                ),
                            ],
                            "cwd": ".",
                            "timeoutSeconds": 30,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            run_dir = Path(json.loads(created.stdout)["runDir"])
            evidence = run_cli("run-evidence", "--run-dir", str(run_dir), "--command", "mutate")
            self.assertEqual(evidence.returncode, 3)
            self.assertTrue(json.loads(evidence.stdout)["repositoryMutationDetected"])

    def test_evidence_detects_new_untracked_source(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "mutate": {
                            "argv": [
                                sys.executable,
                                "-c",
                                "from pathlib import Path; Path('new.py').write_text('VALUE = 1')",
                            ],
                            "timeoutSeconds": 30,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            run_dir = Path(json.loads(created.stdout)["runDir"])
            evidence = run_cli("run-evidence", "--run-dir", str(run_dir), "--command", "mutate")
            self.assertEqual(evidence.returncode, 3)
            self.assertTrue(json.loads(evidence.stdout)["repositoryMutationDetected"])

    def test_evidence_all_runs_configured_commands_in_stable_order(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "second": {"argv": [sys.executable, "-c", "print('second')"]},
                        "first": {"argv": [sys.executable, "-c", "print('first')"]},
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            run_dir = Path(json.loads(created.stdout)["runDir"])
            evidence = run_cli("run-evidence", "--run-dir", str(run_dir), "--all")
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            receipts = json.loads(evidence.stdout)["commands"]
            self.assertEqual([row["name"] for row in receipts], ["first", "second"])

    def test_preflight_accepts_structured_semantic_evidence_contracts(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "cli-check": {
                            "argv": [sys.executable, "-c", "print('{}')"],
                            "evidenceClaims": [
                                {
                                    "id": "installed-cli-smoke",
                                    "kind": "runtime",
                                    "jsonPointer": "/checks/installedCli",
                                    "equals": True,
                                }
                            ],
                            "artifacts": [
                                {
                                    "id": "installed-runtime-result",
                                    "pathJsonPointer": "/artifact/path",
                                    "sha256JsonPointer": "/artifact/sha256",
                                    "sizeBytesJsonPointer": "/artifact/sizeBytes",
                                    "maxBytes": 4096,
                                }
                            ],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            manifest = read_json(run_dir / "review-manifest.json")
            command = manifest["configuration"]["commands"]["cli-check"]
            self.assertEqual(command["evidenceClaims"][0]["kind"], "runtime")
            self.assertEqual(command["artifacts"][0]["maxBytes"], 4096)

    def test_preflight_rejects_duplicate_semantic_claim_ids(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        claim = {
            "id": "installed-cli-smoke",
            "kind": "runtime",
            "jsonPointer": "/checks/installedCli",
            "equals": True,
        }
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "cli-check": {
                            "argv": [sys.executable, "-c", "print('{}')"],
                            "evidenceClaims": [claim, claim],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
        self.assertEqual(created.returncode, 2)
        self.assertIn("evidenceClaims: duplicate id", created.stderr)

    def test_semantic_claim_requires_matching_structured_stdout(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "cli-check": {
                            "argv": [
                                sys.executable,
                                "-c",
                                "import json; print(json.dumps({'checks': {'installed': False}}))",
                            ],
                            "evidenceClaims": [
                                {
                                    "id": "isolated-install",
                                    "kind": "isolated-install",
                                    "jsonPointer": "/checks/installed",
                                    "equals": True,
                                }
                            ],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            evidence = run_cli(
                "run-evidence", "--run-dir", str(run_dir), "--command", "cli-check"
            )
            self.assertEqual(evidence.returncode, 4, evidence.stderr)
            receipt = json.loads(evidence.stdout)
            self.assertFalse(receipt["semanticEvidenceValid"])
            self.assertEqual(receipt["evidenceClaims"][0]["status"], "UNVERIFIED")
            validated = run_cli(
                "validate", "--run-dir", str(run_dir), "--allow-draft"
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            scorecard_path = run_dir / "scorecard.json"
            scorecard = read_json(scorecard_path)
            scorecard["evidenceLevel"] = "E2"
            write_json(scorecard_path, scorecard)
            inflated = run_cli(
                "validate", "--run-dir", str(run_dir), "--allow-draft"
            )
            self.assertEqual(inflated.returncode, 2)
            self.assertIn("E2+ requires a successful canonical command receipt", inflated.stderr)

    def test_command_artifact_is_copied_and_content_bound(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        artifact_tmp = tempfile.TemporaryDirectory(prefix="review-craft-command-artifact-")
        self.addCleanup(artifact_tmp.cleanup)
        source = Path(artifact_tmp.name) / "result.json"
        payload = b'{"installed":true}\n'
        digest = hashlib.sha256(payload).hexdigest()
        script = (
            "import json; from pathlib import Path; "
            f"p=Path({str(source)!r}); data={payload!r}; p.write_bytes(data); "
            "print(json.dumps({'checks': {'installed': True}, 'artifact': {"
            f"'path': str(p), 'sha256': {digest!r}, 'sizeBytes': len(data)"
            "}}))"
        )
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "cli-check": {
                            "argv": [sys.executable, "-c", script],
                            "evidenceClaims": [
                                {
                                    "id": "installed-cli-smoke",
                                    "kind": "runtime",
                                    "jsonPointer": "/checks/installed",
                                    "equals": True,
                                }
                            ],
                            "artifacts": [
                                {
                                    "id": "installed-runtime-result",
                                    "pathJsonPointer": "/artifact/path",
                                    "sha256JsonPointer": "/artifact/sha256",
                                    "sizeBytesJsonPointer": "/artifact/sizeBytes",
                                    "maxBytes": 4096,
                                }
                            ],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            evidence = run_cli(
                "run-evidence", "--run-dir", str(run_dir), "--command", "cli-check"
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            receipt = json.loads(evidence.stdout)
            self.assertTrue(receipt["semanticEvidenceValid"])
            artifact = receipt["evidenceArtifacts"][0]
            self.assertEqual(artifact["status"], "VERIFIED")
            self.assertEqual(artifact["sha256"], digest)
            self.assertEqual(artifact["sizeBytes"], len(payload))
            copied = run_dir / artifact["storedArtifact"]
            self.assertEqual(copied.read_bytes(), payload)
            source.unlink()

            scorecard_path = run_dir / "scorecard.json"
            scorecard = read_json(scorecard_path)
            scorecard["evidenceLevel"] = "E3"
            write_json(scorecard_path, scorecard)
            e3 = run_cli("validate", "--run-dir", str(run_dir), "--allow-draft")
            self.assertEqual(e3.returncode, 0, e3.stderr)
            scorecard["evidenceLevel"] = "E4"
            write_json(scorecard_path, scorecard)
            e4 = run_cli("validate", "--run-dir", str(run_dir), "--allow-draft")
            self.assertEqual(e4.returncode, 2)
            self.assertIn("E4 requires a matching verified semantic claim", e4.stderr)
            scorecard["evidenceLevel"] = "E3"
            write_json(scorecard_path, scorecard)

            copied.write_bytes(b"tampered\n")
            validated = run_cli(
                "validate", "--run-dir", str(run_dir), "--allow-draft"
            )
            self.assertEqual(validated.returncode, 2)
            self.assertIn("evidence artifact sha256 does not match", validated.stderr)

    def test_command_artifact_rejects_target_repository_paths(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        script = (
            "import json; from pathlib import Path; "
            "p=Path('app.py').resolve(); "
            "print(json.dumps({'artifact': {'path': str(p)}}))"
        )
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "capture": {
                            "argv": [sys.executable, "-c", script],
                            "artifacts": [
                                {
                                    "id": "runtime-result",
                                    "pathJsonPointer": "/artifact/path",
                                }
                            ],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            evidence = run_cli(
                "run-evidence", "--run-dir", str(run_dir), "--command", "capture"
            )
            self.assertEqual(evidence.returncode, 4, evidence.stderr)
            receipt = json.loads(evidence.stdout)
            self.assertFalse(receipt["semanticEvidenceValid"])
            self.assertEqual(receipt["evidenceArtifacts"][0]["status"], "REJECTED")
            self.assertIsNone(receipt["evidenceArtifacts"][0]["storedArtifact"])

    @unittest.skipIf(sys.platform == "win32", "symlink creation is not portable on Windows CI")
    def test_command_artifact_rejects_symlinks(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        artifact_tmp = tempfile.TemporaryDirectory(prefix="review-craft-command-artifact-")
        self.addCleanup(artifact_tmp.cleanup)
        real = Path(artifact_tmp.name) / "real.json"
        link = Path(artifact_tmp.name) / "result.json"
        script = (
            "import json; from pathlib import Path; "
            f"real=Path({str(real)!r}); link=Path({str(link)!r}); "
            "real.write_text('{}'); link.symlink_to(real); "
            "print(json.dumps({'artifact': {'path': str(link)}}))"
        )
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "capture": {
                            "argv": [sys.executable, "-c", script],
                            "artifacts": [
                                {
                                    "id": "runtime-result",
                                    "pathJsonPointer": "/artifact/path",
                                }
                            ],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            evidence = run_cli(
                "run-evidence", "--run-dir", str(run_dir), "--command", "capture"
            )
            self.assertEqual(evidence.returncode, 4, evidence.stderr)
            receipt = json.loads(evidence.stdout)
            self.assertEqual(receipt["evidenceArtifacts"][0]["status"], "REJECTED")

    def test_repeated_evidence_is_unique_and_output_hashes_are_validated(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "stable": {"argv": [sys.executable, "-c", "print('stable')"]}
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            fixed_time = "2026-07-29T07:00:00Z"
            first_exit, first = run_evidence_command(
                run_dir, "stable", started_at=fixed_time
            )
            second_exit, second = run_evidence_command(
                run_dir, "stable", started_at=fixed_time
            )
            self.assertEqual((first_exit, second_exit), (0, 0))
            self.assertNotEqual(first["id"], second["id"])
            self.assertNotEqual(first["stdoutArtifact"], second["stdoutArtifact"])
            self.assertEqual((first["sequence"], second["sequence"]), (0, 1))
            for receipt in (first, second):
                stdout = (run_dir / receipt["stdoutArtifact"]).read_bytes()
                stderr = (run_dir / receipt["stderrArtifact"]).read_bytes()
                self.assertEqual(receipt["stdoutSha256"], hashlib.sha256(stdout).hexdigest())
                self.assertEqual(receipt["stderrSha256"], hashlib.sha256(stderr).hexdigest())
            receipts = read_jsonl(run_dir / "evidence/commands.jsonl")
            self.assertEqual(len({row["id"] for row in receipts}), 2)
            self.assertNotIn("semanticEvidenceValid", receipts[0])
            legacy_valid = run_cli(
                "validate", "--run-dir", str(run_dir), "--allow-draft"
            )
            self.assertEqual(legacy_valid.returncode, 0, legacy_valid.stderr)

            (run_dir / first["stdoutArtifact"]).write_text("tampered\n", encoding="utf-8")
            validated = run_cli(
                "validate", "--run-dir", str(run_dir), "--allow-draft"
            )
            self.assertEqual(validated.returncode, 2)
            self.assertIn("stdoutSha256 does not match", validated.stderr)

    def test_evidence_receipt_must_match_configured_command(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "stable": {
                            "argv": [sys.executable, "-c", "print('configured')"],
                            "cwd": ".",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            executed = run_cli(
                "run-evidence", "--run-dir", str(run_dir), "--command", "stable"
            )
            self.assertEqual(executed.returncode, 0, executed.stderr)

            receipts = read_jsonl(run_dir / "evidence/commands.jsonl")
            receipt = receipts[0]
            old_id = receipt["id"]
            receipt["cwd"] = "never-used-subdirectory"
            new_id = sha256_json(receipt_identity_payload(receipt))[:16]
            receipt["id"] = new_id
            for suffix, field in (("stdout", "stdoutArtifact"), ("stderr", "stderrArtifact")):
                old_path = run_dir / f"evidence/commands/{old_id}.{suffix}"
                new_path = run_dir / f"evidence/commands/{new_id}.{suffix}"
                old_path.rename(new_path)
                receipt[field] = f"evidence/commands/{new_id}.{suffix}"
            write_jsonl(run_dir / "evidence/commands.jsonl", receipts)

            validated = run_cli(
                "validate", "--run-dir", str(run_dir), "--allow-draft"
            )
            self.assertEqual(validated.returncode, 2)
            self.assertIn("cwd does not match configured command", validated.stderr)

    def test_concurrent_evidence_is_serialized_with_a_preexisting_lock_file(self) -> None:
        temporary, target = make_target(commit=True)
        self.addCleanup(temporary.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "commands": {
                        "stable": {
                            "argv": [
                                sys.executable,
                                "-c",
                                "import time; time.sleep(0.1); print('stable')",
                            ]
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as output:
            created = run_cli(
                "preflight",
                "--target",
                str(target),
                "--config",
                str(config),
                "--output-root",
                output,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            run_dir = Path(json.loads(created.stdout)["runDir"])
            (run_dir / ".evidence-command.lock").write_bytes(b"\0")
            fixed_time = "2026-07-29T07:30:00Z"
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(
                        run_evidence_command,
                        run_dir,
                        "stable",
                        started_at=fixed_time,
                    )
                    for _ in range(2)
                ]
                results = [future.result() for future in futures]
            self.assertEqual([code for code, _ in results], [0, 0])
            receipts = read_jsonl(run_dir / "evidence/commands.jsonl")
            self.assertEqual(sorted(row["sequence"] for row in receipts), [0, 1])
            self.assertEqual(len({row["id"] for row in receipts}), 2)
            self.assertEqual((run_dir / ".evidence-command.lock").read_bytes(), b"\0")
            validated = run_cli("validate", "--run-dir", str(run_dir), "--allow-draft")
            self.assertEqual(validated.returncode, 0, validated.stderr)


if __name__ == "__main__":
    unittest.main()
