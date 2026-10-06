from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support import make_target, populate_valid_run, run_cli


class AssuranceTests(unittest.TestCase):
    def test_fast_budget_excludes_generated_vendored_and_binary_files(self) -> None:
        for kind in ("generated", "vendored", "binary"):
            with self.subTest(kind=kind):
                temporary, target = make_target()
                self.addCleanup(temporary.cleanup)
                assets = target / "assets"
                assets.mkdir()
                for index in range(201):
                    (assets / f"file{index}").write_bytes(
                        b"\0fixture" if kind == "binary" else b"VALUE = 1\n"
                    )
                with tempfile.TemporaryDirectory() as output:
                    config = None
                    if kind != "binary":
                        config = Path(output) / "config.json"
                        config.write_text(json.dumps({kind: ["assets/**"]}), encoding="utf-8")
                    run_dir = self._preflight(target, output, "fast", config)
                    coverage = json.loads((run_dir / "coverage.json").read_text())
                    self.assertEqual(len(coverage["files"]), 202)
                    self.assertEqual(
                        sum(row["disposition"] == kind.upper() for row in coverage["files"]),
                        201,
                    )
                    validated = run_cli("validate", "--run-dir", str(run_dir), "--allow-draft")
                    self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_fast_budget_keeps_the_ordinary_source_limit(self) -> None:
        for count in (200, 201):
            with self.subTest(count=count):
                temporary, target = make_target()
                self.addCleanup(temporary.cleanup)
                for index in range(count - 1):
                    (target / f"file{index}.py").write_text("VALUE = 1\n", encoding="utf-8")
                with tempfile.TemporaryDirectory() as output:
                    completed = run_cli(
                        "preflight",
                        "--target",
                        str(target),
                        "--output-root",
                        output,
                        "--assurance",
                        "fast",
                    )
                    if count == 200:
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                    else:
                        self.assertEqual(completed.returncode, 2, completed.stderr)
                        self.assertIn("201 > 200", completed.stderr)
                        self.assertEqual(list(Path(output).iterdir()), [])

    def test_fast_budget_mixed_coverage_uses_the_same_eligibility_count(self) -> None:
        from review_craft.assurance import eligible_file_count

        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        for index in range(199):
            (target / f"file{index}.py").write_text("VALUE = 1\n", encoding="utf-8")
        for name, payload in (
            ("generated.py", b"VALUE = 1\n"),
            ("vendor.py", b"VALUE = 1\n"),
            ("asset.bin", b"\0fixture"),
        ):
            (target / name).write_bytes(payload)
        with tempfile.TemporaryDirectory() as output:
            config = Path(output) / "config.json"
            config.write_text(
                json.dumps({"generated": ["generated.py"], "vendored": ["vendor.py"]})
            )
            run = self._preflight(target, output, "fast", config)
            coverage = json.loads((run / "coverage.json").read_text())
            self.assertEqual(len(coverage["files"]), 203)
            self.assertEqual(eligible_file_count(coverage), 200)
            checked = run_cli("validate", "--run-dir", str(run), "--allow-draft")
            self.assertEqual(checked.returncode, 0, checked.stderr)
            (target / "extra.py").write_text("VALUE = 1\n")
            rejected = run_cli(
                "preflight",
                "--target",
                str(target),
                "--output-root",
                output,
                "--assurance",
                "fast",
                "--config",
                str(config),
            )
            self.assertEqual(rejected.returncode, 2, rejected.stderr)
            self.assertIn("201 > 200", rejected.stderr)

    def _preflight(
        self,
        target: Path,
        output: str,
        level: str,
        config: Path | None = None,
    ) -> Path:
        args = [
            "preflight",
            "--target",
            str(target),
            "--output-root",
            output,
            "--assurance",
            level,
        ]
        if config is not None:
            args.extend(["--config", str(config)])
        completed = run_cli(*args)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return Path(json.loads(completed.stdout)["runDir"])

    def test_fast_assurance_is_budgeted_and_never_final_score(self) -> None:
        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        with tempfile.TemporaryDirectory() as output:
            run_dir = self._preflight(target, output, "fast")
            manifest = json.loads((run_dir / "review-manifest.json").read_text(encoding="utf-8"))
            scope = json.loads((run_dir / "review-scope.json").read_text(encoding="utf-8"))
            scorecard = json.loads((run_dir / "scorecard.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["configuration"]["assuranceLevel"], "fast")
            self.assertEqual(scope["assuranceLevel"], "fast")
            self.assertEqual(scorecard["assurance"]["level"], "fast")
            self.assertEqual(scorecard["assurance"]["budget"]["maxEvidenceCommands"], 3)

            populate_valid_run(run_dir)
            rejected = run_cli("finalize", "--run-dir", str(run_dir))
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("fast assurance must remain provisional", rejected.stderr)

            scorecard = json.loads((run_dir / "scorecard.json").read_text(encoding="utf-8"))
            scorecard["status"] = "provisional"
            (run_dir / "scorecard.json").write_text(
                json.dumps(scorecard, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            finalized = run_cli("finalize", "--run-dir", str(run_dir))
            self.assertEqual(finalized.returncode, 0, finalized.stderr)
            report = (run_dir / "report.md").read_text(encoding="utf-8")
            self.assertIn("Assurance: `FAST`", report)
            self.assertIn("FAST 保证等级不形成最终评分", report)
            sealed_scorecard = json.loads((run_dir / "scorecard.json").read_text(encoding="utf-8"))
            self.assertEqual(sealed_scorecard["assurance"]["completionStatus"], "PARTIAL")

    def test_assured_finalization_requires_bound_independent_verification(self) -> None:
        temporary, target = make_target()
        self.addCleanup(temporary.cleanup)
        with tempfile.TemporaryDirectory() as output:
            config = target / "assured.json"
            config.write_text(
                json.dumps(
                    {
                        "commands": {
                            "runtime-proof": {
                                "argv": [
                                    sys.executable,
                                    "-c",
                                    "import json; print(json.dumps({'ok': True}))",
                                ],
                                "evidenceClaims": [
                                    {
                                        "id": "runtime-proof",
                                        "kind": "runtime",
                                        "jsonPointer": "/ok",
                                        "equals": True,
                                    }
                                ],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            run_dir = self._preflight(target, output, "assured", config)
            evidence = run_cli(
                "run-evidence",
                "--run-dir",
                str(run_dir),
                "--command",
                "runtime-proof",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            populate_valid_run(run_dir)
            scorecard_path = run_dir / "scorecard.json"
            scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
            scorecard["evidenceLevel"] = "E3"
            scorecard_path.write_text(
                json.dumps(scorecard, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            missing = run_cli("finalize", "--run-dir", str(run_dir))
            self.assertEqual(missing.returncode, 2)
            self.assertIn("requires one registered verification artifact", missing.stderr)

            manifest = json.loads((run_dir / "review-manifest.json").read_text(encoding="utf-8"))
            before_input = {
                p.relative_to(run_dir): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()
            }
            # Windows redirected stdout may use a legacy code page. JSON must remain
            # portable without losing the original Unicode findings or digest.
            with patch.dict(os.environ, {"PYTHONIOENCODING": "cp1252"}):
                input_result = run_cli("verification-input", "--run-dir", str(run_dir))
            self.assertEqual(
                before_input,
                {p.relative_to(run_dir): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()},
            )
            self.assertEqual(input_result.returncode, 0, input_result.stderr)
            verifier_input = json.loads(input_result.stdout)
            self.assertEqual(verifier_input["reviewRunId"], manifest["runId"])
            self.assertEqual(
                verifier_input["findings"],
                json.loads((run_dir / "findings.json").read_text(encoding="utf-8")),
            )
            verifier = Path(output) / "verifier.json"
            verifier.write_text(
                json.dumps(
                    {
                        "schema": "review-craft.assurance-verification.v2",
                        "findingsSha256": verifier_input["findingsSha256"],
                        "reviewRunId": manifest["runId"],
                        "sourceFingerprint": manifest["target"]["sourceFingerprint"],
                        "createdAt": "2026-08-20T00:00:00Z",
                        "verifier": {
                            "kind": "HUMAN",
                            "identifier": "independent-fixture-reviewer",
                            "independent": True,
                        },
                        "assessments": [
                            {
                                "findingId": "RC-FINDING-001",
                                "disposition": "AGREED",
                                "rationale": "The independent fixture trace agrees.",
                                "evidenceRefs": ["source:app.py:1-2"],
                            }
                        ],
                        "unverifiedClaims": [],
                    }
                ),
                encoding="utf-8",
            )
            registered = run_cli(
                "register-evidence",
                "--run-dir",
                str(run_dir),
                "--id",
                "assured-verifier",
                "--source",
                str(verifier),
                "--kind",
                "verification",
                "--producer",
                "independent-fixture-reviewer",
                "--description",
                "Independent assured review fixture.",
                "--media-type",
                "application/json",
            )
            self.assertEqual(registered.returncode, 0, registered.stderr)
            findings_path = run_dir / "findings.json"
            original = json.loads(findings_path.read_text(encoding="utf-8"))
            for field, changed in (
                ("currentImpact", "A materially changed impact"),
                ("severity", "HIGH"),
                ("rootCause", "A different root cause"),
                ("locations", []),
                ("evidenceRefs", ["source:app.py:2-2"]),
                ("recommendation", "A different remediation"),
            ):
                with self.subTest(field=field):
                    value = json.loads(json.dumps(original))
                    value["findings"][0][field] = changed
                    findings_path.write_text(json.dumps(value), encoding="utf-8")
                    stale = run_cli("finalize", "--run-dir", str(run_dir))
                    self.assertEqual(stale.returncode, 2, stale.stderr)
                    self.assertIn("findingsSha256", stale.stderr)
            findings_path.write_text(json.dumps(original), encoding="utf-8")
            # A material content change requires a newly registered independent assessment.
            original["findings"][0]["currentImpact"] = "An independently reassessed impact"
            findings_path.write_text(json.dumps(original, sort_keys=True), encoding="utf-8")
            updated_input = run_cli("verification-input", "--run-dir", str(run_dir))
            self.assertEqual(updated_input.returncode, 0, updated_input.stderr)
            updated = json.loads(verifier.read_text(encoding="utf-8"))
            updated["findingsSha256"] = json.loads(updated_input.stdout)["findingsSha256"]
            verifier.write_text(json.dumps(updated), encoding="utf-8")
            reverified = run_cli(
                "register-evidence",
                "--run-dir",
                str(run_dir),
                "--id",
                "assured-verifier-current",
                "--source",
                str(verifier),
                "--kind",
                "verification",
                "--producer",
                "fixture",
                "--description",
                "New independent assessment after a material change",
                "--media-type",
                "application/json",
            )
            self.assertEqual(reverified.returncode, 0, reverified.stderr)
            finalized = run_cli("finalize", "--run-dir", str(run_dir))
            self.assertEqual(finalized.returncode, 0, finalized.stderr)
            sealed = json.loads(scorecard_path.read_text(encoding="utf-8"))
            self.assertEqual(sealed["assurance"]["completionStatus"], "COMPLETE")
            self.assertEqual(sealed["assurance"]["verifier"]["status"], "VERIFIED")
            self.assertEqual(
                sealed["assurance"]["verifier"]["evidenceRef"],
                "artifact:assured-verifier-current",
            )
            # Reconstruct a sealed historical v1 fixture with a matching registry hash.
            # Production registration remains immutable; only this test fixture is rewritten.
            registry_path = run_dir / "evidence-registry.json"
            registry = json.loads(registry_path.read_text())
            receipt = next(
                row for row in registry["artifacts"] if row["id"] == "assured-verifier-current"
            )
            receipt_path = run_dir / receipt["path"]
            historical = json.loads(receipt_path.read_text())
            historical["schema"] = "review-craft.assurance-verification.v1"
            del historical["findingsSha256"]
            content = json.dumps(historical).encode()
            receipt_path.write_bytes(content)
            receipt.update(sha256=hashlib.sha256(content).hexdigest(), sizeBytes=len(content))
            registry["artifacts"] = [
                row for row in registry["artifacts"] if row["id"] != "assured-verifier"
            ]
            (run_dir / "evidence/registered/assured-verifier/artifact").unlink()
            (run_dir / "evidence/registered/assured-verifier").rmdir()
            registry_path.write_text(json.dumps(registry))
            historical_read = run_cli("validate", "--run-dir", str(run_dir))
            self.assertEqual(historical_read.returncode, 0, historical_read.stderr)
            historical_write = run_cli("finalize", "--run-dir", str(run_dir))
            self.assertEqual(historical_write.returncode, 2)
            self.assertIn("findingsSha256", historical_write.stderr)


if __name__ == "__main__":
    unittest.main()
