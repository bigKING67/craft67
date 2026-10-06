from __future__ import annotations

import json
from copy import deepcopy
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate as source_validator


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_source_validator_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_local_upstream_status_is_current(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/upstream_status.py", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["local_valid"])
        self.assertFalse(payload["remote_checked"])
        self.assertEqual(len(payload["upstreams"]), 4)

    def test_behavior_contract_covers_core_failure_modes(self) -> None:
        payload = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
        cases = payload["cases"]
        case_ids = {case["id"] for case in cases}
        tags = {tag for case in cases for tag in case["tags"]}
        tracks = {case["track"] for case in cases}
        self.assertTrue({"rewrite", "diagnose", "evidence", "routing", "reader-test"} <= tags)
        self.assertEqual(tracks, {"regression", "exploration"})
        self.assertIn("decision-entry-preserves-engineering-source", case_ids)
        self.assertIn("formatted-document-uses-semantic-emphasis", case_ids)
        self.assertIn("approved-plan-preserves-editing-authority", case_ids)
        self.assertIn("proposal-mode-separates-new-suggestions", case_ids)
        self.assertIn("clean-delivery-without-process-commentary", case_ids)
        self.assertIn("same-source-different-readers", case_ids)
        self.assertIn(
            "human-reader-test-records-understanding-not-agreement", case_ids
        )
        self.assertIn("multi-source-conflict-preserves-authority", case_ids)
        source_conflict = next(
            case
            for case in cases
            if case["id"] == "multi-source-conflict-preserves-authority"
        )
        self.assertEqual(source_conflict["track"], "exploration")
        self.assertEqual(
            {source["source_id"] for source in source_conflict["sources"]},
            {"approval-record", "later-working-draft"},
        )
        reader_case = next(
            case for case in cases if case["id"] == "sufficient-source-no-repeat-questions"
        )
        self.assertEqual(len(reader_case["reader_test"]["questions"]), 6)
        self.assertIn(
            "causality",
            {question["id"] for question in reader_case["reader_test"]["questions"]},
        )
        rewrite_case = next(
            case for case in cases if case["id"] == "ai-video-proposal-rewrite"
        )
        targeted_ids = {
            "ai-video-proposal-rewrite",
            "sufficient-source-no-repeat-questions",
            "diagnosis-does-not-overwrite",
            "routing-boundaries",
        }
        for case in cases:
            if case["id"] in targeted_ids:
                semantic = case.get("semantic_contract")
                self.assertIsInstance(semantic, dict)
                self.assertTrue(semantic["facts"])
                self.assertTrue(semantic["forbidden_inferences"])
                self.assertEqual(
                    set(semantic),
                    {
                        "facts",
                        "allowed_inferences",
                        "forbidden_inferences",
                        "unknowns",
                        "reader_truths",
                        "reader_misreadings",
                    },
                )
        self.assertEqual(rewrite_case["max_revisions"], 1)
        self.assertEqual(reader_case["max_revisions"], 1)
        approved_case = next(
            case
            for case in cases
            if case["id"] == "approved-plan-preserves-editing-authority"
        )
        audience_case = next(
            case for case in cases if case["id"] == "same-source-different-readers"
        )
        decision_entry_case = next(
            case
            for case in cases
            if case["id"] == "decision-entry-preserves-engineering-source"
        )
        self.assertEqual(approved_case["max_revisions"], 1)
        self.assertEqual(audience_case["max_revisions"], 1)
        self.assertEqual(decision_entry_case["max_revisions"], 1)
        self.assertIn(
            "基线、负责人",
            " ".join(approved_case["expected"]["must_not"]),
        )
        self.assertIn(
            "验收用途",
            " ".join(audience_case["expected"]["must_not"]),
        )
        audience_prohibited = " ".join(audience_case["expected"]["must_not"])
        self.assertIn("费用构成", audience_prohibited)
        self.assertIn("不可绕过", audience_prohibited)
        gaps_case = next(
            case for case in cases if case["id"] == "critical-gaps-with-draft"
        )
        constraint_case = next(
            case
            for case in cases
            if case["id"] == "decision-changing-technical-constraint"
        )
        self.assertEqual(gaps_case["max_revisions"], 1)
        self.assertEqual(constraint_case["max_revisions"], 1)
        self.assertIn(
            "使用范围、交付方式",
            " ".join(gaps_case["expected"]["must_not"]),
        )
        self.assertIn(
            "不虚构附录内容",
            " ".join(constraint_case["expected"]["must"]),
        )
        constraint_prohibited = " ".join(constraint_case["expected"]["must_not"])
        self.assertIn("当前版本不具备该能力", constraint_prohibited)
        self.assertIn("GPU 型号", constraint_prohibited)
        self.assertIn("组件、接口、部署方式", constraint_prohibited)
        self.assertIn("任务模式", constraint_prohibited)
        self.assertIn("未授权素材不可用", constraint_prohibited)
        self.assertIn("尚未实现自动化", constraint_prohibited)
        self.assertIn("推进前明确预期", constraint_prohibited)
        self.assertIn("辅助剪辑方案", rewrite_case["source"])
        self.assertIn("不申请立项、拨款或审批", rewrite_case["source"])
        self.assertTrue(
            any("擅自把原方案改成试点" in item for item in rewrite_case["expected"]["must_not"])
        )
        self.assertFalse(
            any("首期建议" in item for item in rewrite_case["expected"]["must"])
        )
        self.assertTrue(
            any("后续服务话术" in item for item in rewrite_case["expected"]["must_not"])
        )
        reader_must = " ".join(reader_case["expected"]["must"])
        reader_must_not = " ".join(reader_case["expected"]["must_not"])
        self.assertIn("三项试点前后比较指标", reader_must)
        self.assertIn("新增审批事项", reader_must_not)
        self.assertIn("数据记录流程", reader_must_not)
        self.assertIn("不具备自动发送能力", reader_must_not)
        self.assertIn("已证实因果", reader_must_not)
        self.assertIn("持续成本", " ".join(rewrite_case["expected"]["must_not"]))
        diagnosis_case = next(
            case for case in cases if case["id"] == "diagnosis-does-not-overwrite"
        )
        self.assertIn("原稿全文只有以下五段", diagnosis_case["source"])
        self.assertNotIn("max_revisions", diagnosis_case)
        self.assertTrue(
            any(
                "无来源的确定性判断" in item
                for item in diagnosis_case["expected"]["must_not"]
            )
        )
        diagnosis_prohibited = " ".join(diagnosis_case["expected"]["must_not"])
        self.assertIn("看完不知道如何回应", diagnosis_prohibited)
        self.assertIn("推导业务贡献", diagnosis_prohibited)
        routing_case = next(
            case for case in cases if case["id"] == "routing-boundaries"
        )
        self.assertIn("明确不主导广告创意", routing_case["source"])
        status_case = next(
            case
            for case in cases
            if case["id"] == "status-update-without-fake-approval"
        )
        status_prohibited = " ".join(status_case["expected"]["must_not"])
        self.assertIn("完成本地测试", status_prohibited)
        self.assertIn("测试通过", status_prohibited)
        self.assertIn("进展正常", status_prohibited)
        self.assertNotIn("风险", " ".join(status_case["expected"]["must"]))
        skill_text = (ROOT / "skills" / "write-craft" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        normalized_skill_text = " ".join(skill_text.split())
        # These mandatory clauses moved with their routing to progressive references.
        reference_root = ROOT / "skills" / "write-craft" / "references"
        integrity = (reference_root / "source-integrity.md").read_text(encoding="utf-8")
        decisions = (reference_root / "decision-documents.md").read_text(encoding="utf-8")
        normalized_integrity = " ".join(integrity.split())
        self.assertIn("before responding; its diagnosis rules and source distinctions are required", skill_text)
        self.assertIn("before every", skill_text)
        self.assertIn("moving them to a reference does not make them optional", skill_text)
        self.assertIn("source-integrity.md", skill_text)
        self.assertIn("decision-documents.md", skill_text)
        self.assertIn("completing a test is not the same as passing it", normalized_integrity)
        self.assertIn("Silence is not an explicitly named unknown", integrity)
        self.assertIn("材料未提供当前基线", integrity)
        self.assertIn("proceeding as planned", normalized_integrity)
        self.assertIn("团队按计划推进", integrity)
        self.assertIn("exactly those three facts", normalized_integrity)
        self.assertIn("尚未给出测试结论", integrity)
        self.assertIn("components, interfaces, or deployment methods", decisions)
        self.assertIn("没有可放入附录的内容", decisions)
        self.assertIn("mode classification", skill_text)
        self.assertIn("separate application is required", normalized_integrity)
        self.assertIn("Treat an unstated reader task as an observed gap", integrity)
        self.assertIn("A Diagnose response is incomplete", integrity)
        self.assertIn("读者看完不知道如何回应", integrity)
        self.assertIn("infer each component's business contribution", integrity)
        self.assertIn("完整工程方案见文件二", decisions)
        self.assertIn("document-presentation.md", skill_text)
        presentation_case = next(
            case
            for case in cases
            if case["id"] == "formatted-document-uses-semantic-emphasis"
        )
        self.assertIn("presentation", presentation_case["tags"])
        self.assertIn(
            "颜色作为区分",
            " ".join(presentation_case["expected"]["must_not"]),
        )
        length_case = next(
            case for case in cases if case["id"] == "strict-total-length-budget"
        )
        self.assertEqual(length_case["limits"], {"max_han_characters": 500})
        self.assertTrue(
            any("附注" in item for item in length_case["expected"]["must_not"])
        )
        self.assertTrue(
            any("责任人" in item for item in length_case["expected"]["must_not"])
        )
        prohibited = " ".join(
            item for case in cases for item in case["expected"]["must_not"]
        )
        for invariant in ("编造", "生产上线", "独立通过", "飞书写入", "嵌入电子表格"):
            self.assertIn(invariant, prohibited)

    def test_source_integrity_rejects_permanent_modal_strengthening(self) -> None:
        source_integrity = (
            ROOT / "skills" / "write-craft" / "references" / "source-integrity.md"
        ).read_text(encoding="utf-8")
        self.assertIn("current, phase-specific, or approved boundary", source_integrity)
        self.assertIn("不是过渡做法", source_integrity)
        self.assertIn("以后也不会自动化", source_integrity)

    def test_release_policy_requires_layered_evidence(self) -> None:
        policy = json.loads(
            (ROOT / "evals" / "release-policy.json").read_text(encoding="utf-8")
        )
        self.assertEqual(policy["required_tracks"], ["regression"])
        self.assertTrue(policy["exploration"]["require_disclosure"])
        self.assertTrue(policy["judge_calibration"]["required"])
        self.assertEqual(
            policy["judge_calibration"]["fixtures"], "evals/judge-fixtures.json"
        )
        self.assertGreaterEqual(policy["human_acceptance"]["minimum_documents"], 3)
        self.assertTrue(policy["human_acceptance"]["require_independence_record"])
        self.assertTrue(policy["package"]["require_boundary_check"])

    def test_release_validator_rejects_stale_behavior_baseline(self) -> None:
        original_read_json = source_validator.read_json

        def read_with_drift(path: Path) -> dict[str, object]:
            payload = original_read_json(path)
            if path == ROOT / "evals" / "cases.json":
                payload = deepcopy(payload)
                cases = payload["cases"]
                self.assertIsInstance(cases, list)
                cases[0]["expected"]["must"][0] += "（已变更）"
            return payload

        with patch.object(source_validator, "read_json", side_effect=read_with_drift):
            errors = source_validator.validate_release_evidence()
        self.assertTrue(
            any("case_digest does not match current case" in error for error in errors),
            errors,
        )

    def test_source_validator_rejects_corrupted_historical_baseline(self) -> None:
        original_read_json = source_validator.read_json
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        baseline_path = ROOT / "evals" / "baselines" / f"pi-v{version}.json"

        def read_without_one_result(path: Path) -> dict[str, object]:
            payload = original_read_json(path)
            if path == baseline_path:
                payload = deepcopy(payload)
                results = payload["results"]
                self.assertIsInstance(results, list)
                results.pop()
            return payload

        with patch.object(source_validator, "read_json", side_effect=read_without_one_result):
            errors = source_validator.validate()
        self.assertTrue(
            any("acceptance must match its result count" in error for error in errors),
            errors,
        )

    def test_release_validator_rejects_overlength_behavior_candidate(self) -> None:
        original_read_json = source_validator.read_json
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        baseline_path = ROOT / "evals" / "baselines" / f"pi-v{version}.json"

        def read_with_overlength_candidate(path: Path) -> dict[str, object]:
            payload = original_read_json(path)
            if path == baseline_path:
                payload = deepcopy(payload)
                results = payload["results"]
                self.assertIsInstance(results, list)
                result = next(
                    item
                    for item in results
                    if item["case_id"] == "strict-total-length-budget"
                )
                result["candidate"] += "超" * 500
                result["candidate_sha256"] = source_validator.sha256_text(
                    result["candidate"]
                )
                result["candidate_metrics"] = {
                    "han_characters": source_validator.han_character_count(
                        result["candidate"]
                    )
                }
            return payload

        with patch.object(
            source_validator,
            "read_json",
            side_effect=read_with_overlength_candidate,
        ):
            errors = source_validator.validate_release_evidence()
        self.assertTrue(
            any("exceeds max_han_characters" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
