from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "skills" / "money-craft" / "scripts"))

import acceptance_case as acceptance  # noqa: E402
import research_run  # noqa: E402
from research_workflow import company_research_plan  # noqa: E402


class AcceptanceCaseTests(unittest.TestCase):
    def temporary_evidence_directory(self) -> tempfile.TemporaryDirectory:
        evidence_root = ROOT / "local" / "evidence"
        evidence_root.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=evidence_root)

    def case(self, root: str) -> dict[str, object]:
        return {
            "schema": acceptance.CASE_SCHEMA,
            "case_id": "000333",
            "security": "美的集团",
            "expected_thscode": "000333.SZ",
            "as_of": "2026-08-23",
            "evidence_root": root,
            "public_root": "artifacts/acceptance/000333",
            "provider_documentation": "https://fuyao.aicubes.cn/docs/api-reference/overview/",
            "operations": [
                {
                    "id": "S01",
                    "title": "Ticker search",
                    "operation": "search",
                    "arguments": {"query": "000333", "limit": 3},
                    "output": "S01-search.normalized.json",
                },
                {
                    "id": "S17",
                    "title": "Latest indicators",
                    "operation": "indicators",
                    "arguments": {"thscode": "000333.SZ", "report": "2026-1"},
                    "output": "S17-indicators.normalized.json",
                    "allow_error_codes": [5003],
                },
            ],
            "official_sources": [
                {
                    "id": "S11",
                    "kind": "official-document",
                    "title": "Official report",
                    "url": "https://example.invalid/report.pdf",
                    "retrieved_on": "2026-08-23",
                    "local_path": "S11-report.pdf",
                }
            ],
        }

    def test_repository_case_is_valid_and_uses_complete_sz_thscode(self) -> None:
        case = acceptance.load_case(ROOT / "acceptance" / "cases" / "000333.json")
        self.assertEqual(case["expected_thscode"], "000333.SZ")
        self.assertEqual(case["operations"][0]["operation"], "search")
        command = acceptance.operation_command(
            acceptance.RUNTIME,
            case["operations"][3],
            ROOT / "local" / "evidence" / "000333" / "captures",
        )
        self.assertIn("000333.SZ", command)
        self.assertNotIn("X-api-key", command)
        self.assertTrue(all(not item.get("allow_error_codes") for item in case["operations"]))
        plan = company_research_plan(
            security="美的集团",
            thscode="000333.SZ",
            as_of="2026-08-23",
            latest_report="2026-1",
            provider={"mode": "auto", "configured": True, "network_checked": False},
            today=dt.date(2026, 8, 23),
        )
        derived = research_run.derived_case(plan, "0" * 64)
        self.assertEqual(
            [(item["id"], item["operation"], item["arguments"]) for item in case["operations"]],
            [(item["id"], item["operation"], item["arguments"]) for item in derived["operations"]],
        )
        self.assertEqual(
            [item["id"] for item in case["official_sources"]],
            [item["id"] for item in derived["official_sources"] if item.get("required", True)],
        )

    def test_case_rejects_public_or_parent_traversal_evidence_root(self) -> None:
        case = self.case("../evidence")
        with self.assertRaises(acceptance.AcceptanceError):
            acceptance.validate_case(case)

    def test_case_rejects_cross_security_operation(self) -> None:
        case = self.case("local/evidence/test-case")
        case["operations"][1]["arguments"]["thscode"] = "600519.SH"
        with self.assertRaisesRegex(acceptance.AcceptanceError, "expected_thscode"):
            acceptance.validate_case(case)

    def test_financial_response_must_match_requested_statement(self) -> None:
        item = {
            "id": "S05",
            "operation": "financials",
            "arguments": {"statement": "income"},
        }
        payload = {
            "schema": "money-craft.data-response.v1",
            "ok": True,
            "provider": "fuyao",
            "operation": "financials.balance",
        }
        with self.assertRaisesRegex(acceptance.AcceptanceError, "response operation"):
            acceptance.operation_status(item, payload, 0)

    def test_collect_accepts_declared_provider_gap_and_preserves_capture_boundary(self) -> None:
        with self.temporary_evidence_directory() as directory:
            evidence = Path(directory) / "case"
            relative = evidence.relative_to(ROOT).as_posix()
            case = self.case(relative)
            acceptance.validate_case(case)

            def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                source_id = command[command.index("--source-id") + 1]
                capture_root = Path(command[command.index("--capture-dir") + 1])
                if source_id == "S01":
                    destination = capture_root / source_id
                    destination.mkdir(parents=True)
                    raw = b'{"code":0,"message":"success","request_id":"r1","data":{"item":[]}}'
                    (destination / "response.json").write_bytes(raw)
                    payload = {
                        "schema": "money-craft.data-response.v1",
                        "ok": True,
                        "provider": "fuyao",
                        "operation": "search",
                        "request_id": "r1",
                        "fetched_at": "2026-08-23T00:00:00Z",
                        "data": {
                            "item": [
                                {
                                    "thscode": "000333.SZ",
                                    "ticker": "000333",
                                    "name": "美的集团",
                                }
                            ]
                        },
                    }
                    return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
                payload = {
                    "schema": "money-craft.data-response.v1",
                    "ok": False,
                    "provider": "fuyao",
                    "operation": "indicators",
                    "fetched_at": "2026-08-23T00:00:01Z",
                    "data": None,
                    "error": {"kind": "transient_provider_error", "code": 5003, "retryable": True},
                }
                return subprocess.CompletedProcess(command, 5, json.dumps(payload), "")

            summary = acceptance.collect(case, runner=runner)
            self.assertTrue(summary["complete"])
            self.assertEqual(summary["passed"], 1)
            self.assertEqual(summary["allowed_errors"], 1)
            self.assertFalse((evidence / "captures" / "S17").exists())

    def test_manifest_hashes_private_files_without_distributing_payloads(self) -> None:
        with self.temporary_evidence_directory() as directory:
            evidence = Path(directory)
            relative = evidence.relative_to(ROOT).as_posix()
            case = self.case(relative)
            acceptance.validate_case(case)
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "captures" / "S01").mkdir(parents=True)
            (evidence / "captures" / "S01" / "response.json").write_text("{}", encoding="utf-8")
            (evidence / "S01-search.normalized.json").write_text(
                json.dumps(
                    {
                        "schema": "money-craft.data-response.v1",
                        "ok": True,
                        "provider": "fuyao",
                        "operation": "search",
                        "fetched_at": "2026-08-23T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            (evidence / "S17-indicators.normalized.json").write_text(
                json.dumps(
                    {
                        "schema": "money-craft.data-response.v1",
                        "ok": False,
                        "provider": "fuyao",
                        "operation": "indicators",
                        "fetched_at": "2026-08-23T00:00:01Z",
                        "error": {"kind": "transient_provider_error", "code": 5003},
                    }
                ),
                encoding="utf-8",
            )
            (evidence / "S11-report.pdf").write_bytes(b"%PDF-1.7\nfixture")
            output = evidence / "manifest.json"
            manifest = acceptance.build_manifest(case, output=output)
            self.assertFalse(manifest["distribution"]["provider_payloads_distributed"])
            self.assertEqual(manifest["source_count"], 3)
            self.assertEqual(len(manifest["sources"][0]["files"]), 2)
            self.assertEqual(len(manifest["sources"][2]["files"]), 1)
            self.assertNotIn("%PDF-1.7", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
