from __future__ import annotations

import copy
import hashlib
import json
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

from review_craft.constants import (
    ARTIFACT_PATHS,
    LEGACY_SCHEMA_VERSION,
    PREVIOUS_SCHEMA_VERSION,
)
from review_craft.contracts import ContractError, load_run, validate_run
from review_craft.jsonio import canonical_json, read_json, read_jsonl, write_json, write_jsonl
from review_craft.report import _eligible_inspection, render_report


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target_tmp, self.target = make_target()
        self.output_tmp = tempfile.TemporaryDirectory(prefix="review-craft-runs-")
        self.run_dir = create_run(self.target, Path(self.output_tmp.name))
        populate_valid_run(self.run_dir)

    def tearDown(self) -> None:
        self.output_tmp.cleanup()
        self.target_tmp.cleanup()

    def test_valid_run_finalizes_deterministically(self) -> None:
        first = run_cli("finalize", "--run-dir", str(self.run_dir))
        self.assertEqual(first.returncode, 0, first.stderr)
        report = self.run_dir / "report.md"
        first_hash = hashlib.sha256(report.read_bytes()).hexdigest()
        second = run_cli("finalize", "--run-dir", str(self.run_dir))
        self.assertEqual(second.returncode, 0, second.stderr)
        second_hash = hashlib.sha256(report.read_bytes()).hexdigest()
        self.assertEqual(first_hash, second_hash)
        text = report.read_text(encoding="utf-8")
        for heading in (
            "第一部分：执行摘要",
            "第二部分：评分",
            "第三部分：问题清单",
            "第四部分：代码与模块处置建议",
            "第五部分：目标方案",
            "第六部分：实施计划",
            "最终结论",
        ):
            self.assertIn(heading, text)
        self.assertIn("- Mode: `review`", text)
        self.assertIn("- Profile: `application`", text)

    def test_report_score_wording_is_bound_to_review_mode(self) -> None:
        base = load_run(self.run_dir)
        expectations = {
            "review": (
                "当前项目综合评分为 **85/100**",
                "当前项目综合评分：** 85/100",
                None,
            ),
            "focus": (
                "当前 focused review 评分为 **85/100**",
                "当前 focused scope 评分：** 85/100",
                "该分数只适用于本次 focused scope，不代表完整仓库综合评分。",
            ),
            "diff": (
                "当前 diff review 评分为 **85/100**",
                "当前 diff scope 评分：** 85/100",
                "该分数只覆盖本次指定 diff，不代表完整仓库综合评分。",
            ),
        }
        for mode, (summary, conclusion, limitation) in expectations.items():
            with self.subTest(mode=mode):
                data = copy.deepcopy(base)
                data["reviewScope"]["mode"] = mode
                text = render_report(data)
                self.assertIn(summary, text)
                self.assertIn(conclusion, text)
                if limitation is not None:
                    self.assertIn(limitation, text)

    def test_focus_finalization_emits_scope_limited_score(self) -> None:
        target_tmp, target = make_target()
        self.addCleanup(target_tmp.cleanup)
        config = target / ".review-craft.json"
        config.write_text(
            json.dumps(
                {
                    "mode": "focus",
                    "focusDimensions": ["correctness"],
                }
            ),
            encoding="utf-8",
        )
        with tempfile.TemporaryDirectory(prefix="review-craft-focus-run-") as output:
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
            populate_valid_run(run_dir)
            finalized = run_cli("finalize", "--run-dir", str(run_dir))
            self.assertEqual(finalized.returncode, 0, finalized.stderr)
            text = (run_dir / "report.md").read_text(encoding="utf-8")
            self.assertIn("当前 focused review 评分为 **85/100**", text)
            self.assertIn(
                "该分数只适用于本次 focused scope，不代表完整仓库综合评分。",
                text,
            )

    def test_report_separates_findings_evidence_gaps_and_remaining_risks(self) -> None:
        data = load_run(self.run_dir)
        data["findings"]["findings"] = []
        data["qualityModel"]["unknowns"] = [
            "尚未在 Windows 主机验证安装路径。",
            "尚未执行长期并发稳定性测试。",
        ]
        data["scorecard"]["dimensions"][0]["deductions"] = [
            {
                "points": 2,
                "reason": "缺少隔离安装后的真实启动证据。",
                "evidenceRefs": ["evidence-gap:isolated-install"],
            }
        ]
        text = render_report(data)
        self.assertIn("已确认问题（Confirmed Findings）：`0`", text)
        self.assertIn("证据缺口（Evidence Gaps）：`1`", text)
        self.assertIn("剩余风险（Remaining Risks）：`2`", text)
        self.assertIn("`evidence-gap:isolated-install`：缺少隔离安装后的真实启动证据。", text)
        self.assertIn("尚未在 Windows 主机验证安装路径。", text)

    def test_report_separates_confirmed_and_likely_findings(self) -> None:
        data = load_run(self.run_dir)
        data["candidates"][0]["validation"]["status"] = "LIKELY"
        data["findings"]["findings"][0]["validationStatus"] = "LIKELY"
        text = render_report(data)

        self.assertIn("已确认问题（Confirmed Findings）：`0`", text)
        self.assertIn("高概率问题（Likely Findings）：`1`", text)
        confirmed = text.split("## 已确认问题（Confirmed Findings）", 1)[1].split(
            "## 高概率问题（Likely Findings）", 1
        )[0]
        likely = text.split("## 高概率问题（Likely Findings）", 1)[1]
        self.assertNotIn("RC-FINDING-001", confirmed)
        self.assertIn("RC-FINDING-001", likely)

    def test_report_projects_verified_command_semantics(self) -> None:
        data = load_run(self.run_dir)
        data["commands"] = [
            {
                "name": "cli-check",
                "evidenceClaims": [
                    {
                        "id": "installed-cli-smoke",
                        "kind": "runtime",
                        "status": "VERIFIED",
                    }
                ],
                "evidenceArtifacts": [
                    {
                        "id": "installed-runtime-result",
                        "status": "VERIFIED",
                        "sha256": "a" * 64,
                        "sizeBytes": 1983,
                    }
                ],
            }
        ]
        text = render_report(data)
        self.assertIn("`command:cli-check#installed-cli-smoke`（runtime）", text)
        self.assertIn("`command:cli-check#installed-runtime-result`", text)
        self.assertIn("已验证语义声明：1", text)
        self.assertIn("已捕获证据产物：1", text)

    def test_zh_cn_report_projects_canonical_fixture_text_without_english_paragraphs(self) -> None:
        finalized = run_cli("finalize", "--run-dir", str(self.run_dir))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        text = (self.run_dir / "report.md").read_text(encoding="utf-8")
        for legacy_text in (
            "A local correction is sufficient",
            "Keep the fixture as a minimal single-module library",
            "The fixture module and its focused test",
        ):
            self.assertNotIn(legacy_text, text)

    def test_pending_candidate_blocks_finalization(self) -> None:
        candidates = read_jsonl(self.run_dir / ARTIFACT_PATHS["candidateLedger"])
        candidates[0]["validation"]["status"] = "PENDING"
        candidates[0]["validation"]["method"] = ""
        write_jsonl(self.run_dir / ARTIFACT_PATHS["candidateLedger"], candidates)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("unresolved candidate", str(captured.exception))

    def test_delete_requires_migration_and_rollback(self) -> None:
        decisions = read_json(self.run_dir / ARTIFACT_PATHS["decisions"])
        decisions["decisions"][0]["decision"] = "DELETE"
        decisions["decisions"][0]["alternatives"] = []
        write_json(self.run_dir / ARTIFACT_PATHS["decisions"], decisions)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("required for DELETE", str(captured.exception))

    def test_unmeasured_performance_suspicion_is_not_a_finding(self) -> None:
        findings = read_json(self.run_dir / ARTIFACT_PATHS["findings"])
        findings["findings"][0]["performanceClass"] = "LIKELY_HOT_PATH"
        write_json(self.run_dir / ARTIFACT_PATHS["findings"], findings)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("unmeasured suspicion", str(captured.exception))

    def test_score_95_requires_e3(self) -> None:
        scorecard = read_json(self.run_dir / ARTIFACT_PATHS["scorecard"])
        for row in scorecard["dimensions"]:
            row["awarded"] = row["maximum"]
            row["deductions"] = []
        scorecard["dimensions"][0]["awarded"] -= 5
        scorecard["dimensions"][0]["deductions"] = [
            {"points": 5, "reason": "fixture", "evidenceRefs": ["RC-FINDING-001"]}
        ]
        scorecard["total"] = 95
        scorecard["evidenceLevel"] = "E2"
        write_json(self.run_dir / ARTIFACT_PATHS["scorecard"], scorecard)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("scores >=95 require evidence level E3", str(captured.exception))

    def test_current_score_deductions_require_closed_references(self) -> None:
        scorecard = read_json(self.run_dir / ARTIFACT_PATHS["scorecard"])
        scorecard["dimensions"][0]["deductions"][0]["evidenceRefs"] = [
            "bogus:not-a-finding-or-evidence-gap"
        ]
        write_json(self.run_dir / ARTIFACT_PATHS["scorecard"], scorecard)

        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("unknown score evidence reference", str(captured.exception))

    def test_current_run_accepts_canonical_evidence_gap_reference(self) -> None:
        scorecard = read_json(self.run_dir / ARTIFACT_PATHS["scorecard"])
        scorecard["dimensions"][0]["deductions"][0]["evidenceRefs"] = [
            "evidence-gap:isolated-install"
        ]
        write_json(self.run_dir / ARTIFACT_PATHS["scorecard"], scorecard)

        validate_run(self.run_dir)

    def test_run_v3_keeps_historical_score_reference_semantics(self) -> None:
        rewrite_fixture_run_schema(self.run_dir, LEGACY_SCHEMA_VERSION)
        scorecard = read_json(self.run_dir / ARTIFACT_PATHS["scorecard"])
        scorecard["dimensions"][0]["deductions"][0]["evidenceRefs"] = [
            "legacy:free-form-reference"
        ]
        write_json(self.run_dir / ARTIFACT_PATHS["scorecard"], scorecard)

        validate_run(self.run_dir)

    def test_run_v4_keeps_content_bound_score_reference_semantics(self) -> None:
        rewrite_fixture_run_schema(self.run_dir, PREVIOUS_SCHEMA_VERSION)
        scorecard_path = self.run_dir / ARTIFACT_PATHS["scorecard"]
        scorecard = read_json(scorecard_path)
        scorecard["dimensions"][0]["deductions"][0]["evidenceRefs"] = [
            "legacy:free-form-reference"
        ]
        write_json(scorecard_path, scorecard)

        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("unknown score evidence reference", str(captured.exception))

    def test_e2_requires_successful_canonical_command_evidence(self) -> None:
        scorecard = read_json(self.run_dir / ARTIFACT_PATHS["scorecard"])
        scorecard["evidenceLevel"] = "E2"
        write_json(self.run_dir / ARTIFACT_PATHS["scorecard"], scorecard)
        self.assertEqual(read_jsonl(self.run_dir / ARTIFACT_PATHS["commands"]), [])

        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn(
            "E2+ requires a successful canonical command receipt", str(captured.exception)
        )

    def test_final_score_rejects_deferred_review_gaps(self) -> None:
        coverage = read_json(self.run_dir / ARTIFACT_PATHS["coverage"])
        for row in coverage["files"]:
            row["disposition"] = "DEFERRED"
            row["reason"] = "Deliberately deferred by the regression fixture."
        coverage["summary"]["reviewed"] = 0
        coverage["summary"]["deferred"] = len(coverage["files"])
        write_json(self.run_dir / ARTIFACT_PATHS["coverage"], coverage)

        scorecard = read_json(self.run_dir / ARTIFACT_PATHS["scorecard"])
        scorecard["coveragePercent"] = 0.0
        scorecard["accountedPercent"] = 100.0
        scorecard["reviewedPercent"] = 0.0
        write_json(self.run_dir / ARTIFACT_PATHS["scorecard"], scorecard)

        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn(
            "final requires no pending, deferred, unreadable, or out-of-scope review gaps",
            str(captured.exception),
        )

    def test_report_distinguishes_accounted_and_reviewed_coverage(self) -> None:
        coverage = read_json(self.run_dir / ARTIFACT_PATHS["coverage"])
        for row in coverage["files"]:
            row["disposition"] = "DEFERRED"
            row["reason"] = "Deliberately deferred by the report fixture."
        coverage["summary"]["reviewed"] = 0
        coverage["summary"]["deferred"] = len(coverage["files"])
        write_json(self.run_dir / ARTIFACT_PATHS["coverage"], coverage)

        scorecard = read_json(self.run_dir / ARTIFACT_PATHS["scorecard"])
        scorecard["status"] = "provisional"
        write_json(self.run_dir / ARTIFACT_PATHS["scorecard"], scorecard)

        finalized = run_cli("finalize", "--run-dir", str(self.run_dir))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        report = (self.run_dir / "report.md").read_text(encoding="utf-8")
        self.assertIn("Inventory classified: `100.0%`", report)
        self.assertIn("Eligible files inspected: `0.0%` (`0/1`)", report)
        self.assertIn("Reviewed inventory: `0.0%`", report)
        self.assertIn("Score status: `provisional`", report)
        self.assertIn("DEFERRED: `1`", report)

    def test_eligible_inspection_excludes_non_semantic_inventory_classes(self) -> None:
        rows = [
            {"disposition": "REVIEWED"},
            {"disposition": "COVERED_BY_PARENT"},
            {"disposition": "PENDING"},
            {"disposition": "UNREADABLE"},
            {"disposition": "GENERATED"},
            {"disposition": "VENDORED"},
            {"disposition": "BINARY"},
        ]

        self.assertEqual(_eligible_inspection(rows), (2, 4, 50.0))
        self.assertEqual(
            _eligible_inspection(
                [
                    {"disposition": "GENERATED"},
                    {"disposition": "VENDORED"},
                    {"disposition": "BINARY"},
                ]
            ),
            (0, 0, None),
        )

    def test_coverage_total_must_match_rows(self) -> None:
        coverage = read_json(self.run_dir / ARTIFACT_PATHS["coverage"])
        coverage["summary"]["total"] += 1
        write_json(self.run_dir / ARTIFACT_PATHS["coverage"], coverage)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("coverage.summary.total", str(captured.exception))

    def test_coverage_summary_must_match_dispositions(self) -> None:
        coverage = read_json(self.run_dir / ARTIFACT_PATHS["coverage"])
        coverage["summary"]["reviewed"] = 0
        write_json(self.run_dir / ARTIFACT_PATHS["coverage"], coverage)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("coverage.summary.reviewed", str(captured.exception))

    def test_run_v5_binds_coverage_rows_to_the_canonical_inventory(self) -> None:
        coverage = read_json(self.run_dir / ARTIFACT_PATHS["coverage"])
        cases = {
            "sha256": "f" * 64,
            "untracked": True,
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                tampered = copy.deepcopy(coverage)
                tampered["files"][0][field] = value
                write_json(self.run_dir / ARTIFACT_PATHS["coverage"], tampered)

                with self.assertRaises(ContractError) as captured:
                    validate_run(self.run_dir)
                self.assertIn(
                    f"coverage.files[0].{field}: does not match the canonical inventory",
                    str(captured.exception),
                )

    def test_run_v5_coverage_paths_match_the_canonical_inventory(self) -> None:
        coverage = read_json(self.run_dir / ARTIFACT_PATHS["coverage"])
        coverage["files"][0]["path"] = "replacement.py"
        write_json(self.run_dir / ARTIFACT_PATHS["coverage"], coverage)

        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        message = str(captured.exception)
        self.assertIn("coverage.files: missing canonical inventory path 'app.py'", message)
        self.assertIn(
            "coverage.files: unexpected canonical inventory path 'replacement.py'",
            message,
        )

    def test_run_v4_keeps_frozen_coverage_row_validation_semantics(self) -> None:
        rewrite_fixture_run_schema(self.run_dir, PREVIOUS_SCHEMA_VERSION)
        coverage = read_json(self.run_dir / ARTIFACT_PATHS["coverage"])
        coverage["files"][0]["sha256"] = "f" * 64
        write_json(self.run_dir / ARTIFACT_PATHS["coverage"], coverage)

        validate_run(self.run_dir)

    def test_review_scope_dimensions_must_match_configuration(self) -> None:
        review_scope = read_json(self.run_dir / ARTIFACT_PATHS["reviewScope"])
        review_scope["dimensions"] = ["architecture"]
        write_json(self.run_dir / ARTIFACT_PATHS["reviewScope"], review_scope)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("must match configuration focusDimensions", str(captured.exception))

    def test_module_map_file_counts_must_close_against_coverage(self) -> None:
        module_map = read_json(self.run_dir / ARTIFACT_PATHS["moduleMap"])
        module_map["modules"][0]["fileCount"] += 1
        write_json(self.run_dir / ARTIFACT_PATHS["moduleMap"], module_map)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("file counts total", str(captured.exception))

    def test_repository_maps_must_match_deterministic_source_projection(self) -> None:
        module_map = read_json(self.run_dir / ARTIFACT_PATHS["moduleMap"])
        module_map["modules"][0]["totalBytes"] += 1
        write_json(self.run_dir / ARTIFACT_PATHS["moduleMap"], module_map)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("does not match the current inventory", str(captured.exception))

    def test_source_change_after_preflight_blocks_finalization(self) -> None:
        (self.target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("source fingerprint changed after preflight", str(captured.exception))

    def test_finding_validation_must_match_candidate(self) -> None:
        findings = read_json(self.run_dir / ARTIFACT_PATHS["findings"])
        findings["findings"][0]["validationStatus"] = "LIKELY"
        write_json(self.run_dir / ARTIFACT_PATHS["findings"], findings)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("must match the candidate", str(captured.exception))

    def test_schema_rejects_unknown_candidate_property(self) -> None:
        candidates = read_jsonl(self.run_dir / ARTIFACT_PATHS["candidateLedger"])
        candidates[0]["agentOpinion"] = "trust me"
        write_jsonl(self.run_dir / ARTIFACT_PATHS["candidateLedger"], candidates)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("additional property is not allowed", str(captured.exception))

    def test_schema_rejects_invalid_command_receipt(self) -> None:
        write_jsonl(
            self.run_dir / ARTIFACT_PATHS["commands"],
            [{"id": "not-a-command-receipt"}],
        )
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir)
        self.assertIn("command-receipt.schema.json", str(captured.exception))

    def test_schema_invalid_top_level_artifact_returns_contract_error(self) -> None:
        write_json(self.run_dir / ARTIFACT_PATHS["reviewScope"], [])
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir, final=False)
        self.assertIn("review-scope.schema.json", str(captured.exception))
        self.assertIn("expected a JSON object", str(captured.exception))

    @unittest.skipIf(sys.platform == "win32", "symlink creation is not portable on Windows CI")
    def test_canonical_artifact_symlink_is_rejected(self) -> None:
        artifact = self.run_dir / ARTIFACT_PATHS["reviewScope"]
        outside = Path(self.output_tmp.name) / "outside-review-scope.json"
        outside.write_bytes(artifact.read_bytes())
        artifact.unlink()
        artifact.symlink_to(outside)
        with self.assertRaises(ContractError) as captured:
            validate_run(self.run_dir, final=False)
        self.assertIn("must not be a symlink", str(captured.exception))

    def test_canonical_json_rejects_non_finite_numbers(self) -> None:
        with self.assertRaises(ValueError):
            canonical_json({"score": float("nan")})


if __name__ == "__main__":
    unittest.main()
