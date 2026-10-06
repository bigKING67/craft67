from __future__ import annotations

import datetime as dt
import concurrent.futures
import threading
import time
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
# In-process hooks injected via runpy are lost if the CLI re-execs into a user data runtime.
HOOKED_CLI_ENV = {**os.environ, "MONEY_CRAFT_DATA_RUNTIME_ACTIVE": "1"}

import research_run  # noqa: E402
from research_workflow import company_research_plan  # noqa: E402


def example_plan(*, provider_mode: str = "auto") -> dict[str, object]:
    return company_research_plan(
        security="美的集团",
        thscode="000333.SZ",
        as_of="2026-08-23",
        latest_report="2026-1",
        provider={
            "mode": provider_mode,
            "configured": provider_mode != "disabled",
            "configuration_source": "secure-file" if provider_mode != "disabled" else None,
            "network_checked": False,
        },
        today=dt.date(2026, 8, 23),
    )


class FakeProviderRunner:
    def __init__(self, *, gap_source_id: str | None = None) -> None:
        self.gap_source_id = gap_source_id
        self.commands: list[list[str]] = []

    def __call__(self, command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        source_id = command[command.index("--source-id") + 1]
        capture_root = Path(command[command.index("--capture-dir") + 1])
        operation = command[command.index("data") + 1]
        actual_operation = operation
        if operation == "financials":
            statement = command[command.index("--statement") + 1]
            actual_operation = f"financials.{statement}"
        if source_id == self.gap_source_id:
            payload = {
                "schema": "money-craft.data-response.v1",
                "ok": False,
                "provider": "fuyao",
                "operation": actual_operation,
                "request_id": "fixture-gap",
                "fetched_at": "2026-08-23T12:00:00Z",
                "source_timestamp_ms": None,
                "parameters": {},
                "data": None,
                "warnings": [],
                "error": {"kind": "data_error", "code": 3001, "message": "fixture gap", "retryable": False},
            }
            return subprocess.CompletedProcess(command, 4, json.dumps(payload, ensure_ascii=False), "")
        data: dict[str, object] = {}
        if operation == "search":
            data = {"item": [{"name": "美的集团", "thscode": "000333.SZ"}]}
        if operation in {"snapshot", "valuations"}:
            data = {"item": [{"thscode": "000333.SZ", "ticker": "000333"}]}
        if operation == "calendar":
            data = {"item": []}
        capture = capture_root / source_id
        capture.mkdir(parents=True)
        (capture / "response.json").write_text(
            json.dumps({"code": 0, "message": "ok", "request_id": f"fixture-{source_id}", "data": data}),
            encoding="utf-8",
        )
        payload = {
            "schema": "money-craft.data-response.v1",
            "ok": True,
            "provider": "fuyao",
            "operation": actual_operation,
            "request_id": f"fixture-{source_id}",
            "fetched_at": f"2026-08-23T12:{int(source_id[1:]):02d}:00Z",
            "source_timestamp_ms": None,
            "parameters": {},
            "data": data,
            "warnings": [],
            "capture": {"source_id": source_id, "path": str(capture)},
        }
        import money_craft as mc
        parsed = mc.build_parser().parse_args(command[2:])
        _operation, request_path, _parameters, output_parameters = mc.prepare_operation(parsed)
        payload["parameters"] = output_parameters
        (capture / "request.json").write_text(json.dumps({"schema": "money-craft.sanitized-request.v1", "provider": "fuyao", "operation": actual_operation, "method": "GET", "path": request_path, "parameters": output_parameters, "authentication": "fixture"}))
        raw_path = capture / "response.json"
        (capture / "capture.json").write_text(json.dumps({
            "schema": "money-craft.source-capture.v1", "source_id": source_id,
            "provider": payload["provider"], "operation": actual_operation,
            "request_id": payload["request_id"], "fetched_at": payload["fetched_at"],
            "response_sha256": research_run.sha256_file(raw_path), "response_bytes": raw_path.stat().st_size,
            "files": ["request.json", "response.json", "capture.json"],
        }))
        return subprocess.CompletedProcess(command, 0, json.dumps(payload, ensure_ascii=False), "")


def valid_report(schema: str, workflow: str) -> str:
    extra = ""
    if schema == "money-craft.thesis.v1":
        extra = """
## 核心假设

| ID | 假设 | 指标与阈值 | 验证来源 | 频率 | 状态 |
|---|---|---|---|---|---|
| H01 | 收入质量可持续 | 收入与现金流匹配 | [S01][S11] | 季度 | UNVERIFIED |
"""
    red_line = "事实发生重大变化。"
    update = ""
    if schema == "money-craft.thesis.v1":
        red_line = """| ID | 条件 | 严重度 | 当前状态 | 证据 |
|---|---|---|---|---|
| R01 | 现金流连续恶化 | fatal | UNVERIFIED | [S01][S11] |"""
        update = """
## 更新记录

| 日期 | 假设变化 | 估值变化 | 结论变化 | 来源 |
|---|---|---|---|---|
| 2026-08-23 | 初始建立 | 初始建立 | 初始建立 | [S01][S11] |
"""
    return f"""---
schema: {schema}
workflow: {workflow}
security: 美的集团
thscode: 000333.SZ
as_of: 2026-08-23
data_cutoff: 2026-08-23T12:17:00+00:00
base_currency: CNY
provider_status: configured
---
# 美的集团
## 结论
证据边界明确。
## 事实与证据
- 公司身份已经核验 [S01]
- 正式报告已经导入 [S11]
{extra}
## 重大披露与期后事项
已按条件路由核对重大披露与期后事项 [S11]
## 重述口径与三表勾稽
口径和三表勾稽结果记录在结构化回执中 [S11]
## 估值与假设
情景输入仍需持续复核。
<!-- money-craft-calc: {{"id":"C01","operation":"add","inputs":["1","2"],"expected":"3"}} -->
## 风险与反方证据
结构化数据可能存在缺口。
## 证伪条件
{red_line}
{update}
## 来源索引
- [S01] `evidence/S01-search.normalized.json`
- [S11] `evidence/S11-official.pdf`
"""


def valid_reconciliation() -> dict[str, object]:
    return {
        "schema": "money-craft.financial-reconciliation.v1",
        "security": "美的集团",
        "thscode": "000333.SZ",
        "as_of": "2026-08-23",
        "base_currency": "CNY",
        "required_checks": ["balance-sheet-equation", "cash-balance-tie"],
        "period_basis": [
            {
                "role": "current",
                "period": "2026-1",
                "basis": "reported",
                "source_ids": ["S11"],
                "notes": "Current period formal filing.",
            },
            {
                "role": "comparison",
                "period": "2025-1",
                "basis": "reported",
                "source_ids": ["S11", "S12"],
                "notes": "Comparison period reported column.",
            },
        ],
        "restatement_assessment": {
            "status": "none-disclosed",
            "source_ids": ["S11", "S12"],
            "notes": "No retrospective restatement was disclosed in the inspected filings.",
        },
        "material_disclosure_assessment": [
            {
                "source_id": "S18",
                "status": "not-triggered",
                "notes": "No decision-critical transaction or capital-structure trigger was identified.",
            },
            {
                "source_id": "S19",
                "status": "not-triggered",
                "notes": "Management Q&A was not required for a decision-critical claim.",
            },
            {
                "source_id": "S20",
                "status": "not-triggered",
                "notes": "No decision-critical post-reporting-period event trigger was identified.",
            },
        ],
        "checks": [
            {
                "id": "FR01",
                "kind": "balance-sheet-equation",
                "period": "2026-1",
                "unit": "CNY million",
                "inputs": {"assets": "100", "liabilities": "40", "equity": "60"},
                "tolerance": "0.000001",
                "source_ids": ["S11"],
            },
            {
                "id": "FR02",
                "kind": "cash-balance-tie",
                "period": "2026-1",
                "unit": "CNY million",
                "inputs": {"balance_sheet_cash": "25", "cash_flow_ending_cash": "25"},
                "tolerance": "0.000001",
                "source_ids": ["S11"],
            },
        ],
        "presentation_to_economics": {
            "status": "no-material-distortion",
            "source_ids": ["S11"],
            "notes": "No decision-critical accounting presentation distortion was identified.",
            "items": [],
        },
        "subsequent_events": {
            "status": "none-disclosed",
            "source_ids": ["S11", "S13"],
            "notes": "No material post-reporting-period event was identified through the official index.",
            "items": [],
        },
    }


class ResearchRunTests(unittest.TestCase):
    def test_atomic_no_replace_competing_writers(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "receipt.json"
            barrier = threading.Barrier(2, timeout=5)
            real_replace, real_link = os.replace, os.link
            def synchronized(operation):
                def publish(source, destination, *args, **kwargs):
                    barrier.wait()
                    return operation(source, destination, *args, **kwargs)
                return publish
            def write(value):
                try:
                    research_run.atomic_bytes(target, value, replace=False)
                    return "success", value
                except research_run.ResearchRunError as exc:
                    return exc.kind, value
            with mock.patch.object(research_run.os, "replace", synchronized(real_replace)), mock.patch.object(research_run.os, "link", synchronized(real_link)):
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(write, (b"first", b"second")))
            self.assertEqual(sorted(status for status, _ in results), ["existing_artifact", "success"])
            winner = next(value for status, value in results if status == "success")
            self.assertEqual(target.read_bytes(), winner)
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["receipt.json"])

    def test_competing_finalize_cli_preserves_winning_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            self.write_finalization_artifacts(workspace)
            barrier_root = Path(directory) / "barrier"
            barrier_root.mkdir()
            script = r"""
import os, pathlib, runpy, sys, time
barrier = pathlib.Path(sys.argv[1])
cli = sys.argv[2]
args = sys.argv[3:]
original = os.link
def publish(source, destination, *args, **kwargs):
    if pathlib.Path(destination).name == 'completion-receipt.json':
        (barrier / 'ready').touch()
        deadline = time.monotonic() + 15
        while not (barrier / 'release').exists():
            if time.monotonic() > deadline: raise RuntimeError('barrier timeout')
            time.sleep(0.01)
    return original(source, destination, *args, **kwargs)
os.link = publish
sys.path.insert(0, str(pathlib.Path(cli).parent))
sys.argv = [cli, *args]
runpy.run_path(cli, run_name='__main__')
"""
            process = subprocess.Popen([sys.executable, "-c", script, str(barrier_root), str(SCRIPT_DIR / "money_craft.py"),
                "research", "finalize", "--workspace", str(workspace)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=HOOKED_CLI_ENV)
            try:
                deadline = time.monotonic() + 10
                while not (barrier_root / "ready").exists():
                    self.assertIsNone(process.poll(), "finalizer exited before publication barrier")
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.01)
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                commands = [("finalize", []), ("status", []), ("collect", ["--resume"]),
                    ("import-official", ["--source-id", "S18", "--file", str(workspace / "report.md"), "--url", "https://example.invalid/source"])]
                for command, extra in commands:
                    result = subprocess.run([sys.executable, str(SCRIPT_DIR / "money_craft.py"), "research", command,
                        "--workspace", str(workspace), *extra], capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stdout)["error"]["kind"], "workspace_busy")
                    self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})
                (barrier_root / "release").touch()
                output, error = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0, output + error)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
            self.assertFalse(list(workspace.rglob(".*.staging.*")))
            self.assertTrue(research_run.research_status(workspace)["complete"])
            before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
            self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})

    def test_workspace_lock_releases_on_exception_and_process_death(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            with self.assertRaisesRegex(RuntimeError, "injected"):
                with research_run.workspace_lock(workspace):
                    raise RuntimeError("injected")
            research_run.research_status(workspace)
            script = "import sys,time; from pathlib import Path; sys.path.insert(0,sys.argv[1]); import research_run; " \
                     "lock=research_run.workspace_lock(sys.argv[2]); lock.__enter__(); print('locked',flush=True); time.sleep(30)"
            process = subprocess.Popen([sys.executable, "-c", script, str(SCRIPT_DIR), str(workspace)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.assertEqual(process.stdout.readline().strip(), "locked")
                with self.assertRaises(research_run.ResearchRunError) as caught:
                    research_run.research_status(workspace)
                self.assertEqual(caught.exception.kind, "workspace_busy")
            finally:
                process.kill()
                process.communicate(timeout=10)
            self.assertTrue(research_run.research_status(workspace)["valid"])
            self.assertTrue(workspace.with_name(f".{workspace.name}.research.lock").is_file())
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory, provider_mode="disabled")
            command = [sys.executable, str(SCRIPT_DIR / "money_craft.py"), "research", "collect", "--workspace", str(workspace)]
            with research_run.workspace_lock(workspace):
                busy = subprocess.run(command, capture_output=True, text=True, timeout=10)
                self.assertEqual(busy.returncode, 4)
                self.assertEqual(json.loads(busy.stdout)["error"]["kind"], "workspace_busy")
            released = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(json.loads(released.stdout)["error"]["kind"], "provider_disabled")

    def test_workspace_lock_rejects_unsafe_targets_and_unsupported_platform(self):
        for kind in ("symlink", "hardlink", "unsupported"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                target = workspace.with_name(f".{workspace.name}.research.lock")
                # No operation is active; replace this fixture-owned lock for the unsafe-path probes.
                target.unlink()
                protected = Path(directory) / "protected"
                protected.write_bytes(b"preserve")
                if kind == "symlink": target.symlink_to(protected)
                elif kind == "hardlink": os.link(protected, target)
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                if kind == "unsupported":
                    with mock.patch.object(research_run, "fcntl", None), mock.patch.object(research_run, "msvcrt", None):
                        with self.assertRaises(research_run.ResearchRunError) as caught:
                            research_run.research_status(workspace)
                    self.assertEqual(caught.exception.kind, "unsupported_lock")
                    self.assertFalse(target.exists())
                else:
                    with self.assertRaises(research_run.ResearchRunError) as caught:
                        research_run.research_status(workspace)
                    self.assertEqual(caught.exception.kind, "unsafe_lock")
                self.assertEqual(protected.read_bytes(), b"preserve")
                self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})

    def test_atomic_no_replace_preserves_existing_targets_and_cleans_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for kind in ("file", "directory", "dangling-symlink"):
                target = root / kind
                if kind == "file": target.write_bytes(b"original")
                elif kind == "directory": target.mkdir()
                else: target.symlink_to(root / "missing")
                with self.assertRaises(research_run.ResearchRunError) as caught:
                    research_run.atomic_bytes(target, b"replacement", replace=False)
                self.assertEqual(caught.exception.kind, "existing_artifact")
            self.assertEqual((root / "file").read_bytes(), b"original")
            self.assertTrue((root / "directory").is_dir())
            self.assertTrue((root / "dangling-symlink").is_symlink())
            with mock.patch.object(research_run.os, "link", side_effect=OSError("unsupported filesystem")):
                with self.assertRaises(OSError):
                    research_run.atomic_bytes(root / "unpublished", b"data", replace=False)
            self.assertFalse((root / "unpublished").exists())
            self.assertFalse(list(root.glob(".*.staging.*")))
            research_run.atomic_bytes(root / "file", b"updated", replace=True)
            self.assertEqual((root / "file").read_bytes(), b"updated")

    def test_preseal_provider_capture_corruption_blocks_finalization(self):
        for failure in ("raw", "metadata", "missing_metadata"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                self.collect(workspace)
                self.import_official_sources(workspace, directory)
                self.write_finalization_artifacts(workspace)
                folder = workspace / "evidence/captures/S02"
                if failure == "raw": (folder / "response.json").write_text('{"changed":true}')
                elif failure == "missing_metadata": (folder / "capture.json").unlink()
                else:
                    path = folder / "capture.json"
                    data = json.loads(path.read_text()); data["source_id"] = "S99"; path.write_text(json.dumps(data))
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                with self.assertRaises(research_run.ResearchRunError):
                    research_run.finalize_workspace(workspace)
                self.assertFalse((workspace / "completion-receipt.json").exists())
                self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})


    def test_sealed_cli_rejects_collection_and_official_import_without_mutation(self):
        for command in ("collect", "import-official"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                self.collect(workspace)
                self.import_official_sources(workspace, directory)
                self.write_finalization_artifacts(workspace)
                self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
                source = Path(directory) / "extra.pdf"
                source.write_bytes(b"%PDF-1.7\noptional source")
                args = ["--resume"] if command == "collect" else ["--source-id", "S18", "--file", str(source),
                    "--url", "https://example.invalid/S18", "--retrieved-on", "2026-08-23"]
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                result = subprocess.run([sys.executable, str(SCRIPT_DIR / "money_craft.py"), "research", command,
                    "--workspace", str(workspace), *args, "--json"], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["error"]["kind"], "finalized_workspace")
                self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})
                self.assertTrue(research_run.research_status(workspace)["complete"])


    def test_citation_binding_checks_content_after_index(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            path.write_text("## 来源索引\n- [S01] https://example.invalid/one\n## 补充说明\n收入 [S99]\n")
            result = research_run.citation_binding_audit(path, {"S01": {"https://example.invalid/one"}})
            self.assertFalse(result["valid"])
            self.assertIn("S99", result["cited_source_ids"])

    def check_cli_lifecycle(self, runtime: Path) -> list[dict[str, object]]:
        """Exercise a chosen source/installed CLI without importing its implementation."""
        receipts = []
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "run"

            def call(stage: str, command: str, *args: str, target: Path = workspace, code: int = 0):
                process = subprocess.run(
                    [sys.executable, str(runtime), "research", command, "--workspace", str(target), *args, "--json"],
                    cwd=base, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(process.returncode, code, process.stdout + process.stderr)
                payload = json.loads(process.stdout)
                receipts.append({"stage": stage, "command": command, "exit_code": process.returncode})
                return payload

            def snapshot(root: Path):
                return {str(p.relative_to(root)): research_run.sha256_file(p) for p in root.rglob("*") if p.is_file()}

            call("initialize", "init", "--security", "美的集团", "--thscode", "000333.SZ",
                 "--as-of", "2026-08-23", "--latest-report", "2026-1", "--provider-mode", "disabled")
            status = call("initial-status", "status")
            self.assertFalse(status["complete"])
            self.assertEqual(status["missing_sources"], ["S11", "S12", "S13"])
            self.assertEqual(call("missing-evidence-block", "finalize", code=4)["error"]["kind"], "incomplete_evidence")
            for source_id, data in (("S11", b"%PDF-1.7\nquarter"), ("S12", b"%PDF-1.7\nannual"),
                                    ("S13", b"<!doctype html><html>index</html>")):
                path = base / source_id
                path.write_bytes(data)
                call("import-" + source_id, "import-official", "--source-id", source_id, "--file", str(path),
                     "--url", "https://example.invalid/" + source_id, "--retrieved-on", "2026-08-23")
            imported = snapshot(workspace)
            duplicate = call("duplicate-import-block", "import-official", "--source-id", "S11", "--file", str(base / "S11"),
                             "--url", "https://example.invalid/S11", code=4)
            self.assertEqual(duplicate["error"]["kind"], "existing_artifact")
            self.assertEqual(imported, snapshot(workspace))
            report = valid_report("money-craft.report.v1", "research").replace("[S01]", "[S12]").replace(
                "`evidence/S01-search.normalized.json`", "https://example.invalid/S12")
            thesis = valid_report("money-craft.thesis.v1", "thesis").replace("[S01]", "[S12]").replace(
                "`evidence/S01-search.normalized.json`", "https://example.invalid/S12")
            self.write_finalization_artifacts(workspace, report_text=report.replace(
                "https://example.invalid/S12", "https://example.invalid/unrelated"), thesis_text=thesis)
            self.assertFalse(call("wrong-url-block", "finalize", code=4)["valid"])
            self.assertFalse((workspace / "completion-receipt.json").exists())
            (workspace / "report.md").write_text(report)
            self.assertTrue(call("finalize", "finalize")["valid"])
            frozen = snapshot(workspace)
            status = call("completed-status", "status")
            self.assertTrue(status["complete"])
            self.assertEqual(status["assessment"]["evidence_coverage"], "PARTIAL")
            self.assertEqual(status["assessment"]["claim_support"], "UNVERIFIED")
            self.assertEqual(status["assessment"]["source_freshness"], "UNVERIFIED")
            self.assertFalse(status["network_used_by_status"])
            self.assertTrue(call("idempotent-finalize", "finalize")["valid"])
            self.assertEqual(frozen, snapshot(workspace))
            for variant in ("legacy", "receipt", "path", "url", "evidence"):
                clone = base / variant
                shutil.copytree(workspace, clone)
                if variant in {"legacy", "receipt"}:
                    p = clone / "completion-receipt.json"
                    data = json.loads(p.read_text())
                    if variant == "legacy":
                        del data["assessment"]
                    else:
                        data["valid"] = False
                    p.write_text(json.dumps(data))
                elif variant == "path":
                    p = clone / "case.json"
                    data = json.loads(p.read_text())
                    data["official_sources"][0]["local_path"] = str(base / "S11")
                    p.write_text(json.dumps(data))
                elif variant == "url":
                    (clone / "report.md").write_text(report.replace("https://example.invalid/S12", "https://example.invalid/unrelated"))
                else:
                    (clone / "evidence/S11-official.pdf").write_bytes(b"%PDF-1.7\nchanged")
                before = snapshot(clone)
                result = call(variant + "-status", "status", target=clone, code=4 if variant in {"path", "evidence"} else 0)
                if variant not in {"path", "evidence"}:
                    self.assertEqual(result["complete"], variant == "legacy")
                if variant == "receipt":
                    self.assertEqual(result["assessment"]["receipt_integrity"], "INVALID")
                elif variant == "url":
                    self.assertEqual(result["assessment"]["citation_binding"], "INVALID")
                elif variant in {"path", "evidence"}:
                    self.assertEqual(result["error"]["kind"], "invalid_case" if variant == "path" else "evidence_drift")
                finalized = call(variant + "-finalize", "finalize", target=clone, code=0 if variant == "legacy" else 4)
                if variant == "legacy":
                    self.assertTrue(finalized["valid"])
                else:
                    expected_error = {"path": "invalid_case", "evidence": "evidence_drift"}.get(variant, "finalized_workspace")
                    self.assertEqual(finalized["error"]["kind"], expected_error)
                self.assertEqual(before, snapshot(clone))
            self.assertEqual(frozen, snapshot(workspace))
        return receipts

    def test_cli_research_lifecycle_and_sealed_failure_boundaries(self) -> None:
        self.check_cli_lifecycle(SCRIPT_DIR / "money_craft.py")

    def test_global_workspace_declares_unconfigured_yfinance_and_keeps_official_evidence_primary(self) -> None:
        plan = company_research_plan(
            security="NVIDIA Corporation",
            security_id="US-NASDAQ:NVDA",
            base_currency="USD",
            as_of="2026-08-23",
            latest_report="2026-2",
            latest_report_end="2025-07-27",
            latest_annual_report="2025-4",
            provider={"mode": "auto", "configured": False, "network_checked": False},
            today=dt.date(2026, 8, 23),
        )
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "run"
            initialized = research_run.initialize_workspace(
                workspace,
                plan,
                template_root=ROOT / "skills" / "money-craft" / "templates",
            )
            self.assertEqual(initialized["provider_operation_count"], 0)
            case = json.loads((workspace / "case.json").read_text(encoding="utf-8"))
            self.assertEqual(case["operations"], [])
            report = (workspace / "report.md").read_text(encoding="utf-8")
            self.assertIn("security_id: US-NASDAQ:NVDA", report)
            self.assertIn("base_currency: USD", report)
            status = research_run.research_status(workspace)
            self.assertEqual(status["stages"]["provider_evidence"], "not_applicable")
            self.assertEqual(status["provider_gaps"], ["provider:yfinance:not-configured"])
            self.assertEqual(status["missing_sources"], ["S11", "S12", "S13"])

    def initialize(self, directory: str, *, provider_mode: str = "auto") -> Path:
        workspace = Path(directory) / "run"
        result = research_run.initialize_workspace(
            workspace,
            example_plan(provider_mode=provider_mode),
            template_root=ROOT / "skills" / "money-craft" / "templates",
        )
        self.assertTrue(result["valid"])
        self.assertFalse(result["network_used"])
        return workspace

    def collect(self, workspace: Path, *, gap_source_id: str | None = None) -> FakeProviderRunner:
        runner = FakeProviderRunner(gap_source_id=gap_source_id)
        research_run.collect_workspace(workspace, runtime=Path("fixture-runtime.py"), runner=runner)
        return runner

    def import_official_sources(
        self, workspace: Path, directory: str, *, retrieved_on: str = "2026-08-23"
    ) -> None:
        source_root = Path(directory) / "official"
        source_root.mkdir()
        sources = (
            ("S11", b"%PDF-1.7\nq1"),
            ("S12", b"%PDF-1.7\nannual"),
            ("S13", b"<!doctype html><html></html>"),
        )
        for source_id, payload in sources:
            source = source_root / source_id
            source.write_bytes(payload)
            result = research_run.import_official_source(
                workspace,
                source_id=source_id,
                source_file=source,
                url=f"https://example.invalid/{source_id}",
                retrieved_on=retrieved_on,
            )
            self.assertTrue(result["valid"])

    def write_finalization_artifacts(
        self,
        workspace: Path,
        *,
        report_text: str | None = None,
        thesis_text: str | None = None,
    ) -> None:
        (workspace / "report.md").write_text(
            report_text or valid_report("money-craft.report.v1", "research"), encoding="utf-8"
        )
        (workspace / "thesis.md").write_text(
            thesis_text or valid_report("money-craft.thesis.v1", "thesis"), encoding="utf-8"
        )
        (workspace / "financial-reconciliation.json").write_text(
            json.dumps(valid_reconciliation(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def test_init_derives_single_case_truth_and_rejects_plan_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            plan = json.loads((workspace / "plan.json").read_text(encoding="utf-8"))
            case = json.loads((workspace / "case.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [(item["id"], item["operation"], item["arguments"]) for item in case["operations"]],
                [(item["id"], item["operation"], item["arguments"]) for item in plan["provider_operations"]],
            )
            self.assertEqual(len(case["operations"]), 14)
            self.assertEqual(
                [item["id"] for item in case["official_sources"]],
                ["S11", "S12", "S13", "S21", "S22", "S18", "S19", "S20"],
            )
            self.assertTrue((workspace / "financial-reconciliation.json").is_file())
            self.assertEqual(
                [item["id"] for item in case["official_sources"] if item.get("required", True)],
                ["S11", "S12", "S13"],
            )
            with self.assertRaisesRegex(research_run.ResearchRunError, "already exists"):
                self.initialize(directory)
            plan["as_of"] = "2026-08-22"
            (workspace / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(research_run.ResearchRunError, "plan.json changed"):
                research_run.research_status(workspace)

    def test_default_workspace_uses_money_archive_research_layer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = example_plan()
            plan["identity"]["security"] = " 美的/集团 "
            workspace, run_id = research_run.allocate_default_workspace(
                plan,
                root=Path(directory) / "money",
            )
            self.assertEqual(
                workspace,
                (Path(directory) / "money").resolve()
                / "000333-美的-集团"
                / "2026-08-23"
                / ".research"
                / run_id,
            )
            result = research_run.initialize_workspace(
                workspace,
                plan,
                template_root=ROOT / "skills" / "money-craft" / "templates",
                run_id=run_id,
            )
            self.assertEqual(result["run_id"], run_id)
            state = json.loads((workspace / "run-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["run_id"], run_id)

    def test_output_root_precedence_is_explicit_environment_then_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            explicit, explicit_source = research_run.output_root(
                base / "explicit",
                environment={research_run.OUTPUT_ROOT_ENV: str(base / "environment")},
                home=base / "home",
            )
            configured, configured_source = research_run.output_root(
                environment={research_run.OUTPUT_ROOT_ENV: str(base / "environment")},
                home=base / "home",
            )
            default, default_source = research_run.output_root(environment={}, home=base / "home")
            self.assertEqual((explicit, explicit_source), ((base / "explicit").resolve(), "command-line"))
            self.assertEqual(
                (configured, configured_source),
                ((base / "environment").resolve(), f"environment:{research_run.OUTPUT_ROOT_ENV}"),
            )
            self.assertEqual(
                (default, default_source),
                ((base / "home" / "Documents" / "sixseven" / "money").resolve(), "default"),
            )

    def test_collect_is_non_overwriting_and_resume_is_model_free(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            runner = self.collect(workspace)
            self.assertEqual(len(runner.commands), 14)
            status = research_run.research_status(workspace)
            self.assertEqual(status["stages"]["provider_evidence"], "complete")
            self.assertEqual(status["missing_sources"], ["S11", "S12", "S13"])
            with self.assertRaisesRegex(research_run.ResearchRunError, "already exists"):
                research_run.collect_workspace(workspace, runtime=Path("fixture-runtime.py"), runner=runner)
            before = len(runner.commands)
            resumed = research_run.collect_workspace(
                workspace,
                runtime=Path("fixture-runtime.py"),
                resume=True,
                runner=runner,
            )
            self.assertTrue(resumed["valid"])
            self.assertEqual(resumed["network_requests_attempted"], 0)
            self.assertEqual(len(runner.commands), before)
            self.assertTrue(all(item["resumed"] for item in resumed["results"]))

    def test_provider_gap_is_visible_and_never_reported_as_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            result = research_run.collect_workspace(
                workspace,
                runtime=Path("fixture-runtime.py"),
                runner=FakeProviderRunner(gap_source_id="S03"),
            )
            self.assertFalse(result["valid"])
            self.assertTrue(result["complete"])
            self.assertEqual(result["provider_gaps"], 1)
            status = research_run.research_status(workspace)
            self.assertEqual(status["stages"]["provider_evidence"], "complete_with_gaps")
            self.assertEqual(status["provider_gaps"], ["S03"])
            self.assertFalse(status["complete"])

    def test_existing_plan_without_historical_slots_still_finalizes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "legacy-plan"
            plan = example_plan()
            plan["official_evidence_requirements"] = [
                item for item in plan["official_evidence_requirements"] if item["id"] not in {"S21", "S22"}
            ]
            research_run.initialize_workspace(
                workspace, plan, template_root=ROOT / "skills" / "money-craft" / "templates"
            )
            before = (workspace / "plan.json").read_bytes()
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            self.write_finalization_artifacts(workspace)
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
            self.assertTrue(research_run.research_status(workspace)["complete"])
            self.assertEqual((workspace / "plan.json").read_bytes(), before)

    def test_historical_annual_source_is_optional_bound_and_checked_after_seal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            self.assertEqual(research_run.research_status(workspace)["missing_sources"], [])
            source = Path(directory) / "historical.pdf"
            source.write_bytes(b"%PDF-1.7\nhistorical annual statement")
            result = research_run.import_official_source(
                workspace, source_id="S21", source_file=source,
                url="https://example.invalid/historical-annual", retrieved_on="2026-08-23",
            )
            self.assertTrue(result["valid"])
            self.write_finalization_artifacts(workspace)
            for name in ("report.md", "thesis.md"):
                target = workspace / name
                text = target.read_text().replace("## 事实与证据", "## 事实与证据\n\nHistorical comparison [S21].")
                text += "\n- [S21] https://example.invalid/historical-annual\n"
                target.write_text(text)
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
            self.assertTrue(research_run.research_status(workspace)["complete"])
            imported = list((workspace / "evidence").rglob("S21*"))
            historical = next(p for p in imported if p.is_file() and p.suffix == ".pdf")
            historical.write_bytes(b"%PDF-1.7\nchanged historical annual")
            with self.assertRaisesRegex(research_run.ResearchRunError, "official evidence changed after import: S21"):
                research_run.research_status(workspace)

    def test_gap_finalization_records_partial_evidence_without_claiming_claim_support(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace, gap_source_id="S03")
            self.import_official_sources(workspace, directory)
            self.write_finalization_artifacts(workspace)
            finalized = research_run.finalize_workspace(workspace)
            self.assertTrue(finalized["valid"])
            receipt = json.loads((workspace / "completion-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["assessment"],
                {
                    "artifact_integrity": "VERIFIED",
                    "receipt_integrity": "VERIFIED",
                    "evidence_coverage": "PARTIAL",
                    "citation_binding": "VERIFIED",
                    "claim_support": "UNVERIFIED",
                    "source_freshness": "UNVERIFIED",
                },
            )
            status = research_run.research_status(workspace)
            self.assertTrue(status["complete"])
            self.assertEqual(status["assessment"], receipt["assessment"])

    def test_completed_status_rechecks_manifest_evidence_contents(self) -> None:
        for role in ("raw-response", "normalized-response", "capture-metadata"):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                self.collect(workspace)
                self.import_official_sources(workspace, directory)
                self.write_finalization_artifacts(workspace)
                self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
                manifest = json.loads((workspace / "evidence-manifest.json").read_text())
                target = next(f for source in manifest["sources"] for f in source["files"] if f["role"] == role)
                path = workspace / target["path"]
                payload = json.loads(path.read_text()); payload["synthetic_tamper"] = True
                path.write_text(json.dumps(payload))
                if role == "raw-response":
                    with self.assertRaises(research_run.ResearchRunError) as caught:
                        research_run.research_status(workspace)
                    self.assertEqual(caught.exception.kind, "evidence_drift")
                else:
                    status = research_run.research_status(workspace)
                    self.assertFalse(status["complete"])
                    self.assertEqual(status["assessment"]["artifact_integrity"], "STALE")
                preserved = {name: (workspace / name).read_bytes() for name in ("evidence-manifest.json", "completion-receipt.json", "report-audit.json")}
                with self.assertRaises(research_run.ResearchRunError): research_run.finalize_workspace(workspace)
                self.assertEqual(preserved, {name: (workspace / name).read_bytes() for name in preserved})

    def test_url_suffix_does_not_bypass_local_citation_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            path.write_text("## 来源索引\n- [S01] `evidence/wrong.json` (https://example.invalid/provenance)\n")
            result = research_run.citation_binding_audit(path, {"S01": {"evidence/right.json"}})
            self.assertFalse(result["valid"])

    def test_public_citation_url_must_match_its_imported_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            template = valid_report("money-craft.report.v1", "research")
            for target in (
                "https://example.invalid/unrelated-company",
                "[annual report](https://example.invalid/S12)",
                "https://example.invalid/S11 other text",
            ):
                with self.subTest(target=target):
                    self.write_finalization_artifacts(workspace, report_text=template.replace("`evidence/S11-official.pdf`", target))
                    result = research_run.finalize_workspace(workspace)
                    self.assertFalse(result["valid"])
                    self.assertIsNone(result["receipt"])
                    self.assertFalse((workspace / "completion-receipt.json").exists())
                    self.assertEqual(research_run.research_status(workspace)["assessment"]["citation_binding"], "INVALID")
            for target in ("https://example.invalid/S11", "[official report](https://example.invalid/S11)"):
                with self.subTest(valid_target=target):
                    self.write_finalization_artifacts(workspace, report_text=template.replace("`evidence/S11-official.pdf`", target))
                    self.assertEqual(research_run.research_status(workspace)["assessment"]["citation_binding"], "VERIFIED")
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
            self.assertTrue(research_run.research_status(workspace)["complete"])

    def test_finalize_rejects_citations_to_unbound_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            report = valid_report("money-craft.report.v1", "research").replace("S01", "S98").replace("S11", "S99")
            thesis = valid_report("money-craft.thesis.v1", "thesis").replace("S01", "S98").replace("S11", "S99")
            self.write_finalization_artifacts(workspace, report_text=report, thesis_text=thesis)
            finalized = research_run.finalize_workspace(workspace)
            self.assertFalse(finalized["valid"])
            self.assertIsNone(finalized["receipt"])
            self.assertTrue(
                any("S98 is not a passed or imported" in error for error in finalized["audits"]["report"]["report"]["errors"])
            )
            status = research_run.research_status(workspace)
            self.assertEqual(status["assessment"]["citation_binding"], "INVALID")
            self.assertFalse(status["complete"])

    def test_finalize_rejects_citation_to_failed_provider_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace, gap_source_id="S03")
            self.import_official_sources(workspace, directory)
            report = valid_report("money-craft.report.v1", "research").replace(
                "S01-search.normalized.json", "S03-valuations.normalized.json"
            ).replace("[S01]", "[S03]")
            thesis = valid_report("money-craft.thesis.v1", "thesis").replace(
                "S01-search.normalized.json", "S03-valuations.normalized.json"
            ).replace("[S01]", "[S03]")
            self.write_finalization_artifacts(workspace, report_text=report, thesis_text=thesis)
            finalized = research_run.finalize_workspace(workspace)
            self.assertFalse(finalized["valid"])
            self.assertTrue(
                any("S03 is not a passed or imported" in error for error in finalized["audits"]["report"]["report"]["errors"])
            )

    def test_finalize_rejects_local_evidence_path_for_another_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            report = valid_report("money-craft.report.v1", "research").replace(
                "evidence/S01-search.normalized.json", "evidence/S02-snapshot.normalized.json"
            )
            self.write_finalization_artifacts(workspace, report_text=report)
            finalized = research_run.finalize_workspace(workspace)
            self.assertFalse(finalized["valid"])
            self.assertTrue(
                any("S01 local evidence path does not match" in error for error in finalized["audits"]["report"]["report"]["errors"])
            )

    def test_old_source_retrieval_does_not_claim_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory, retrieved_on="2020-01-01")
            self.write_finalization_artifacts(workspace)
            finalized = research_run.finalize_workspace(workspace)
            self.assertTrue(finalized["valid"])
            receipt = json.loads((workspace / "completion-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["assessment"]["source_freshness"], "UNVERIFIED")
            self.assertEqual(research_run.research_status(workspace)["assessment"]["source_freshness"], "UNVERIFIED")

    def test_completion_receipt_metadata_must_match_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace, gap_source_id="S03")
            self.import_official_sources(workspace, directory)
            self.write_finalization_artifacts(workspace)
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
            path = workspace / "completion-receipt.json"
            original = json.loads(path.read_text())
            mutations = [
                ("valid", False), ("valid", 1),
                ("automatic_trading", True), ("automatic_trading", 0),
                ("run_id", "0" * 32), ("provider_gaps", []),
                ("completed_at", "not-a-date"), ("completed_at", "2026-09-16T12:00:00"),
                ("assessment", {**original["assessment"], "claim_support": "VERIFIED"}),
                ("assessment", {**original["assessment"], "evidence_coverage": "COMPLETE"}),
                ("unexpected", True),
            ]
            for key, value in mutations:
                with self.subTest(key=key, value=value):
                    path.write_text(json.dumps({**original, key: value}))
                    preserved = {p.name: p.read_bytes() for p in workspace.iterdir() if p.is_file()}
                    status = research_run.research_status(workspace)
                    self.assertFalse(status["complete"])
                    self.assertEqual(status["assessment"]["receipt_integrity"], "INVALID")
                    with self.assertRaises(research_run.ResearchRunError):
                        research_run.finalize_workspace(workspace)
                    self.assertEqual(preserved, {p.name: p.read_bytes() for p in workspace.iterdir() if p.is_file()})
            missing = dict(original)
            del missing["completed_at"]
            path.write_text(json.dumps(missing))
            self.assertFalse(research_run.research_status(workspace)["complete"])
            path.write_text(json.dumps(original))
            self.assertTrue(research_run.research_status(workspace)["complete"])
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])

    def test_incomplete_legacy_manifest_is_rejected_and_preserves_sealed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            self.write_finalization_artifacts(workspace)
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
            manifest_path = workspace / "evidence-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            for source in manifest["sources"]:
                source["files"] = [item for item in source["files"] if item["role"] != "capture-metadata"]
            manifest_path.write_text(json.dumps(manifest))
            receipt_path = workspace / "completion-receipt.json"
            receipt = json.loads(receipt_path.read_text())
            receipt["bindings"]["evidence-manifest.json"] = research_run.sha256_file(manifest_path)
            receipt_path.write_text(json.dumps(receipt))
            self.assertFalse(research_run.research_status(workspace)["complete"])
            before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
            with self.assertRaises(research_run.ResearchRunError):
                research_run.finalize_workspace(workspace)
            self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})
            self.assertFalse(research_run.research_status(workspace)["complete"])

    def test_legacy_receipt_without_assessment_remains_verifiable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            self.write_finalization_artifacts(workspace)
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
            receipt_path = workspace / "completion-receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            del receipt["assessment"]
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            status = research_run.research_status(workspace)
            self.assertTrue(status["complete"])
            self.assertEqual(status["assessment"]["receipt_integrity"], "VERIFIED")
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])

    def test_official_evidence_path_is_bound_before_file_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            case_path = workspace / "case.json"
            original = json.loads(case_path.read_text())
            outside = Path(directory) / "outside.pdf"
            outside.write_bytes(b"%PDF-1.7\noutside fixture")
            for local_path in (str(outside), "../../outside.pdf", "S12-official.pdf", "subdir/S11-official.pdf"):
                with self.subTest(local_path=local_path):
                    case = json.loads(json.dumps(original))
                    source = case["official_sources"][0]
                    source.update(local_path=local_path, sha256=research_run.sha256_file(outside), bytes=outside.stat().st_size)
                    case_path.write_text(json.dumps(case))
                    preserved = case_path.read_bytes()
                    with mock.patch.object(research_run, "validate_official_file") as read_file:
                        with self.assertRaises(research_run.ResearchRunError) as raised:
                            research_run.research_status(workspace)
                        self.assertEqual(raised.exception.kind, "invalid_case")
                        read_file.assert_not_called()
                    self.assertEqual(case_path.read_bytes(), preserved)
            case_path.write_text(json.dumps(original))
            self.assertTrue(research_run.research_status(workspace)["ready_for_report"])
            source = original["official_sources"][0]
            evidence = workspace / "evidence" / source["local_path"]
            evidence.write_bytes(b"<!doctype html><html>changed format</html>")
            source.update(sha256=research_run.sha256_file(evidence), bytes=evidence.stat().st_size)
            case_path.write_text(json.dumps(original))
            with self.assertRaisesRegex(research_run.ResearchRunError, "format does not match"):
                research_run.research_status(workspace)

    def test_collection_event_limit_prevents_requests_and_writes(self):
        for resume in (False, True):
            with self.subTest(resume=resume), tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                if resume: self.collect(workspace)
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                limit = len(json.loads((workspace / "run-state.json").read_text())["events"])
                runner = FakeProviderRunner()
                with mock.patch.object(research_run, "MAX_STATE_EVENTS", limit):
                    with self.assertRaises(research_run.ResearchRunError) as caught:
                        research_run.collect_workspace(workspace, runtime=SCRIPT_DIR / "money_craft.py", resume=resume, runner=runner)
                self.assertEqual(caught.exception.kind, "state_limit")
                self.assertEqual(runner.commands, [])
                self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})

    def test_concurrent_init_cli_and_killed_initializer_retry(self):
        for terminate in (False, True):
            with self.subTest(terminate=terminate), tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory) / "run"
                marker, release = Path(directory) / "ready", Path(directory) / "release"
                cli = str(SCRIPT_DIR / "money_craft.py")
                args = ["research", "init", "--security", "美的集团", "--thscode", "000333.SZ", "--as-of", "2026-08-23",
                    "--latest-report", "2026-1", "--provider-mode", "disabled", "--workspace", str(workspace)]
                script = r"""
import os, pathlib, runpy, sys, time
marker, release, target = map(pathlib.Path, sys.argv[1:4])
cli, args = sys.argv[4], sys.argv[5:]
original = os.replace
def publish(source, destination, *args, **kwargs):
    if pathlib.Path(destination).resolve() == target.resolve():
        marker.touch()
        deadline = time.monotonic() + 15
        while not release.exists():
            if time.monotonic() > deadline: raise RuntimeError('init barrier timeout')
            time.sleep(0.01)
    return original(source, destination, *args, **kwargs)
os.replace = publish
sys.path.insert(0, str(pathlib.Path(cli).parent))
sys.argv = [cli, *args]
runpy.run_path(cli, run_name='__main__')
"""
                process = subprocess.Popen([sys.executable, "-c", script, str(marker), str(release), str(workspace), cli, *args],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=HOOKED_CLI_ENV)
                try:
                    deadline = time.monotonic() + 10
                    while not marker.exists():
                        self.assertIsNone(process.poll())
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(0.01)
                    self.assertFalse(workspace.exists())
                    other = subprocess.run([sys.executable, cli, *args], capture_output=True, text=True, timeout=10)
                    self.assertEqual(other.returncode, 4, other.stdout + other.stderr)
                    self.assertEqual(json.loads(other.stdout)["error"]["kind"], "workspace_busy")
                    self.assertFalse(workspace.exists())
                    if terminate: process.kill()
                    else: release.touch()
                    output, error = process.communicate(timeout=10)
                    if not terminate: self.assertEqual(process.returncode, 0, output + error)
                finally:
                    if process.poll() is None:
                        process.kill()
                    process.communicate(timeout=10)
                if terminate:
                    retry = subprocess.run([sys.executable, cli, *args], capture_output=True, text=True, timeout=10)
                    self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
                self.assertTrue(research_run.research_status(workspace)["valid"])
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                duplicate = subprocess.run([sys.executable, cli, *args], capture_output=True, text=True, timeout=10)
                self.assertEqual(duplicate.returncode, 4)
                self.assertEqual(json.loads(duplicate.stdout)["error"]["kind"], "existing_workspace")
                self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})

    def test_collection_process_kill_before_normalized_blocks_cli_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            marker = Path(directory) / "capture-published"
            script = r"""
import pathlib, sys, time
sys.path.insert(0, sys.argv[1])
from test_research_run import FakeProviderRunner, research_run, SCRIPT_DIR
root, marker = pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
original = research_run.atomic_json
def write(path, payload, **kwargs):
    if path.parent.name == 'evidence' and payload.get('ok') is True:
        marker.touch()
        time.sleep(30)
    return original(path, payload, **kwargs)
research_run.atomic_json = write
research_run.collect_workspace(root, runtime=SCRIPT_DIR / 'money_craft.py', runner=FakeProviderRunner())
"""
            process = subprocess.Popen([sys.executable, "-c", script, str(ROOT / "tests"), str(workspace), str(marker)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 10
                while not marker.exists():
                    self.assertIsNone(process.poll())
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.01)
            finally:
                if process.poll() is None: process.kill()
                process.communicate(timeout=10)
            before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
            for command in ("collect", "status", "finalize"):
                result = subprocess.run([sys.executable, str(SCRIPT_DIR / "money_craft.py"), "research", command,
                    "--workspace", str(workspace), *(["--resume"] if command == "collect" else [])],
                    capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["error"]["kind"], "incomplete_collection")
            self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})

    def test_registered_capture_staging_blocks_without_reading_content(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            captures = workspace / "evidence/captures"
            target = captures / (".S01.staging." + "a" * 32)
            target.mkdir()
            (target / "partial").write_bytes(b"preserve")
            with self.assertRaises(research_run.ResearchRunError) as caught: research_run.research_status(workspace)
            self.assertEqual(caught.exception.kind, "incomplete_collection")
            self.assertEqual((target / "partial").read_bytes(), b"preserve")

    def test_capture_without_normalized_result_rejects_retry_without_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            original = research_run.atomic_json
            def write(path, payload, **kwargs):
                if path.parent.name == "evidence" and payload.get("ok") is True:
                    raise OSError("normalized publication interrupted")
                return original(path, payload, **kwargs)
            runner = FakeProviderRunner()
            with mock.patch.object(research_run, "atomic_json", side_effect=write):
                with self.assertRaises(OSError):
                    research_run.collect_workspace(workspace, runtime=SCRIPT_DIR / "money_craft.py", runner=runner)
            self.assertEqual(len(runner.commands), 1)
            before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
            retry = mock.Mock(side_effect=AssertionError("must not request provider"))
            for operation in (research_run.research_status, research_run.finalize_workspace,
                lambda root: research_run.collect_workspace(root, runtime=SCRIPT_DIR / "money_craft.py", resume=True, runner=retry)):
                with self.assertRaises(research_run.ResearchRunError) as caught: operation(workspace)
                self.assertEqual(caught.exception.kind, "incomplete_collection")
            retry.assert_not_called()
            self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})

    def test_collection_event_failure_resumes_complete_results_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            with mock.patch.object(research_run, "record_event", side_effect=OSError("event failed")):
                with self.assertRaises(OSError): self.collect(workspace)
            evidence = {str(p.relative_to(workspace)): p.read_bytes() for p in (workspace / "evidence").rglob("*") if p.is_file() and p.name != "collection-summary.json"}
            runner = mock.Mock(side_effect=AssertionError("must not request provider"))
            result = research_run.collect_workspace(workspace, runtime=SCRIPT_DIR / "money_craft.py", resume=True, runner=runner)
            self.assertTrue(result["valid"])
            self.assertEqual(result["network_requests_attempted"], 0)
            runner.assert_not_called()
            self.assertEqual(evidence, {str(p.relative_to(workspace)): p.read_bytes() for p in (workspace / "evidence").rglob("*") if p.is_file() and p.name != "collection-summary.json"})
            events = json.loads((workspace / "run-state.json").read_text())["events"]
            self.assertEqual(sum(event["type"] == "provider-collection" for event in events), 1)

    def test_finalize_cli_kill_after_receipt_recovers_event_only(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            self.write_finalization_artifacts(workspace)
            marker = Path(directory) / "receipt-published"
            script = r"""
import os, pathlib, runpy, sys, time
marker, cli = pathlib.Path(sys.argv[1]), sys.argv[2]
args = sys.argv[3:]
original = os.link
def publish(source, destination, *args, **kwargs):
    result = original(source, destination, *args, **kwargs)
    if pathlib.Path(destination).name == 'completion-receipt.json':
        marker.touch()
        time.sleep(30)
    return result
os.link = publish
sys.path.insert(0, str(pathlib.Path(cli).parent))
sys.argv = [cli, *args]
runpy.run_path(cli, run_name='__main__')
"""
            cli = str(SCRIPT_DIR / "money_craft.py")
            process = subprocess.Popen([sys.executable, "-c", script, str(marker), cli, "research", "finalize",
                "--workspace", str(workspace)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=HOOKED_CLI_ENV)
            try:
                deadline = time.monotonic() + 10
                while not marker.exists():
                    self.assertIsNone(process.poll())
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.01)
            finally:
                if process.poll() is None: process.kill()
                process.communicate(timeout=10)
            before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
            status = subprocess.run([sys.executable, cli, "research", "status", "--workspace", str(workspace)], capture_output=True, text=True, timeout=10)
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertFalse(json.loads(status.stdout)["complete"])
            retry = subprocess.run([sys.executable, cli, "research", "finalize", "--workspace", str(workspace)], capture_output=True, text=True, timeout=10)
            self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
            after = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
            self.assertEqual(set(before), set(after))
            self.assertEqual([name for name in before if before[name] != after[name]], ["run-state.json"])
            self.assertTrue(research_run.research_status(workspace)["complete"])

    def test_finalize_event_limit_rejects_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            self.write_finalization_artifacts(workspace)
            before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
            limit = len(json.loads((workspace / "run-state.json").read_text())["events"])
            with mock.patch.object(research_run, "MAX_STATE_EVENTS", limit):
                with self.assertRaises(research_run.ResearchRunError) as caught: research_run.finalize_workspace(workspace)
            self.assertEqual(caught.exception.kind, "state_limit")
            self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})

    def test_finalize_recovers_missing_event_without_rewriting_sealed_artifacts(self):
        for tamper in (False, True):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                self.collect(workspace)
                self.import_official_sources(workspace, directory)
                self.write_finalization_artifacts(workspace)
                with mock.patch.object(research_run, "record_event", side_effect=OSError("event interrupted")):
                    with self.assertRaises(OSError): research_run.finalize_workspace(workspace)
                self.assertTrue((workspace / "completion-receipt.json").exists())
                status = research_run.research_status(workspace)
                self.assertFalse(status["complete"])
                self.assertEqual(status["stages"]["finalization_event"], "pending")
                if tamper:
                    with (workspace / "report.md").open("a") as handle: handle.write("\nchanged\n")
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                if tamper:
                    with self.assertRaises(research_run.ResearchRunError): research_run.finalize_workspace(workspace)
                    self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})
                else:
                    self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
                    after = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                    self.assertEqual([name for name in before if before[name] != after[name]], ["run-state.json"])
                    self.assertEqual(set(before), set(after))
                    events = json.loads(after["run-state.json"])["events"]
                    self.assertEqual(sum(event["type"] == "finalized" for event in events), 1)
                    self.assertTrue(research_run.research_status(workspace)["complete"])
                    self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
                    self.assertEqual(after, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})

    def test_import_cli_killed_before_or_after_case_preserves_evidence(self):
        for stop_name in ("S18-official.pdf", "case.json"):
            with tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                self.collect(workspace)
                self.import_official_sources(workspace, directory)
                self.write_finalization_artifacts(workspace)
                source = Path(directory) / "official.pdf"
                source.write_bytes(b"%PDF-1.7\nfixture")
                marker = Path(directory) / "case-published"
                script = r"""
import os, pathlib, runpy, sys, time
marker = pathlib.Path(sys.argv[1])
cli = sys.argv[2]
stop_name = sys.argv[3]
args = sys.argv[4:]
original = os.replace
def publish(source, destination, *args, **kwargs):
    result = original(source, destination, *args, **kwargs)
    if pathlib.Path(destination).name == stop_name:
            marker.touch()
            time.sleep(30)
    return result
os.replace = publish
sys.path.insert(0, str(pathlib.Path(cli).parent))
sys.argv = [cli, *args]
runpy.run_path(cli, run_name='__main__')
"""
                process = subprocess.Popen([sys.executable, "-c", script, str(marker), str(SCRIPT_DIR / "money_craft.py"), stop_name,
                    "research", "import-official", "--workspace", str(workspace), "--source-id", "S18", "--file", str(source),
                    "--url", "https://example.invalid/report.pdf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=HOOKED_CLI_ENV)
                try:
                    deadline = time.monotonic() + 10
                    while not marker.exists():
                        self.assertIsNone(process.poll(), "import exited before case publication")
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(0.01)
                finally:
                    if process.poll() is None: process.kill()
                    process.communicate(timeout=10)
                self.assertEqual((workspace / "evidence/S18-official.pdf").read_bytes(), source.read_bytes())
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                for command in ("status", "finalize"):
                    result = subprocess.run([sys.executable, str(SCRIPT_DIR / "money_craft.py"), "research", command,
                        "--workspace", str(workspace)], capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 4)
                    self.assertEqual(json.loads(result.stdout)["error"]["kind"], "incomplete_import")
                self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})
                self.assertFalse((workspace / "completion-receipt.json").exists())

    def test_pending_optional_orphan_files_block_sealing_without_cleanup(self):
        for name in ("S18-official.pdf", "S18-official.html", ".S18-official.pdf.staging." + "a" * 32):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                self.collect(workspace)
                self.import_official_sources(workspace, directory)
                self.write_finalization_artifacts(workspace)
                (workspace / "evidence" / name).write_bytes(b"%PDF-1.7\npartial import")
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                for operation in (research_run.research_status, research_run.finalize_workspace):
                    with self.assertRaises(research_run.ResearchRunError) as caught:
                        operation(workspace)
                    self.assertEqual(caught.exception.kind, "incomplete_import")
                self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})

    def test_import_failure_preserves_published_evidence_and_blocks_incomplete_state(self):
        for failure in ("before-case", "after-case", "event", "state-limit"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                source = Path(directory) / "official.pdf"
                source.write_bytes(b"%PDF-1.7\nfixture")
                before = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                original = research_run.atomic_json
                def write(path, payload, **kwargs):
                    if path.name == "case.json" and failure == "before-case": raise OSError("before case")
                    if path.name == "run-state.json" and failure == "event": raise OSError("event failed")
                    result = original(path, payload, **kwargs)
                    if path.name == "case.json" and failure == "after-case": raise OSError("after case")
                    return result
                with mock.patch.object(research_run, "atomic_json", side_effect=write), mock.patch.object(research_run, "MAX_STATE_EVENTS", len(json.loads((workspace / "run-state.json").read_text())["events"]) if failure == "state-limit" else research_run.MAX_STATE_EVENTS):
                    with self.assertRaises((OSError, research_run.ResearchRunError)):
                        research_run.import_official_source(workspace, source_id="S11", source_file=source,
                            url="https://example.invalid/report.pdf", retrieved_on="2026-08-23")
                if failure in {"before-case", "state-limit"}:
                    self.assertEqual(before, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})
                    self.assertTrue(research_run.research_status(workspace)["valid"])
                else:
                    self.assertEqual((workspace / "evidence/S11-official.pdf").read_bytes(), source.read_bytes())
                    preserved = {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()}
                    for operation in (research_run.research_status, research_run.finalize_workspace):
                        with self.assertRaises(research_run.ResearchRunError) as caught:
                            operation(workspace)
                        self.assertEqual(caught.exception.kind, "incomplete_import")
                    self.assertEqual(preserved, {str(p.relative_to(workspace)): p.read_bytes() for p in workspace.rglob("*") if p.is_file()})
                self.assertFalse(list(workspace.rglob(".*.staging.*")))

    def test_official_import_is_hash_bound_and_non_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            source = Path(directory) / "official.pdf"
            source.write_bytes(b"%PDF-1.7\nfixture")
            result = research_run.import_official_source(
                workspace,
                source_id="S11",
                source_file=source,
                url="https://example.invalid/report.pdf",
                retrieved_on="2026-08-23",
            )
            self.assertEqual(result["sha256"], research_run.sha256_file(workspace / "evidence" / "S11-official.pdf"))
            with self.assertRaisesRegex(research_run.ResearchRunError, "already imported"):
                research_run.import_official_source(
                    workspace,
                    source_id="S11",
                    source_file=source,
                    url="https://example.invalid/report.pdf",
                )
            (workspace / "evidence" / "S11-official.pdf").write_bytes(b"%PDF-1.7\ntampered")
            with self.assertRaisesRegex(research_run.ResearchRunError, "changed after import"):
                research_run.research_status(workspace)

    def test_finalize_binds_manifest_audits_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            (workspace / "report.md").write_text(
                valid_report("money-craft.report.v1", "research"), encoding="utf-8"
            )
            (workspace / "thesis.md").write_text(
                valid_report("money-craft.thesis.v1", "thesis"), encoding="utf-8"
            )
            (workspace / "financial-reconciliation.json").write_text(
                json.dumps(valid_reconciliation(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = research_run.finalize_workspace(workspace)
            self.assertTrue(result["valid"], result["audits"])
            self.assertEqual(result["evidence_manifest"]["source_count"], 17)
            self.assertTrue(result["audits"]["financial_reconciliation"]["valid"])
            self.assertIsNotNone(result["receipt"])
            receipt = json.loads((workspace / "completion-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(len(receipt["bindings"]), 11)
            self.assertIn("financial-reconciliation.json", receipt["bindings"])
            self.assertIn("financial-reconciliation-audit.json", receipt["bindings"])
            status = research_run.research_status(workspace)
            self.assertTrue(status["complete"])
            self.assertTrue(research_run.finalize_workspace(workspace)["valid"])
            (workspace / "report.md").write_text(
                valid_report("money-craft.report.v1", "research") + "\n",
                encoding="utf-8",
            )
            stale = research_run.research_status(workspace)
            self.assertFalse(stale["complete"])
            self.assertTrue(any("stale" in warning for warning in stale["warnings"]))

    def test_finalize_fails_closed_while_reconciliation_is_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            (workspace / "report.md").write_text(
                valid_report("money-craft.report.v1", "research"), encoding="utf-8"
            )
            (workspace / "thesis.md").write_text(
                valid_report("money-craft.thesis.v1", "thesis"), encoding="utf-8"
            )
            result = research_run.finalize_workspace(workspace)
            self.assertFalse(result["valid"])
            self.assertFalse(result["audits"]["financial_reconciliation"]["valid"])
            self.assertIsNone(result["receipt"])
            self.assertFalse((workspace / "completion-receipt.json").exists())

    def test_research_report_requires_source_bound_disclosure_and_reconciliation_sections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            text = valid_report("money-craft.report.v1", "research")
            text = text.replace(
                "## 重大披露与期后事项\n已按条件路由核对重大披露与期后事项 [S11]\n",
                "",
            )
            path.write_text(text, encoding="utf-8")
            checks = research_run.document_audits(path, example_plan(), "money-craft.report.v1")
            self.assertFalse(checks["valid"])
            self.assertTrue(
                any("重大披露与期后事项" in item for item in checks["report"]["errors"]),
                checks["report"]["errors"],
            )

    def test_document_identity_error_keeps_security_id_parse_reason(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            text = valid_report("money-craft.report.v1", "research").replace(
                "thscode: 000333.SZ\n", "security_id: CN-SZ:000333\nthscode: 600519.SH\n", 1
            )
            path.write_text(text, encoding="utf-8")
            checks = research_run.document_audits(path, example_plan(), "money-craft.report.v1")
            self.assertFalse(checks["valid"])
            self.assertEqual(checks["report"]["errors"].count("security_id and thscode identify different securities"), 1)

    def test_citation_binding_cannot_pass_without_evidence_map_or_with_wrong_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            self.assertFalse(research_run.citation_binding_audit(path, None)["valid"])
            for target, valid in (("[file](evidence/S11.pdf)", True),
                                  ("[file](evidence/S12.pdf)", False),
                                  ("`./evidence/S11.pdf`", False)):
                path.write_text(f"---\nschema: test\n---\n[S11]\n## 来源索引\n- [S11] {target}\n")
                audit = research_run.citation_binding_audit(path, {"S11": {"evidence/S11.pdf"}})
                self.assertEqual(audit["valid"], valid, audit)

    def test_optional_material_disclosure_can_be_imported_without_blocking_default_flow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            status = research_run.research_status(workspace)
            optional = {item["id"]: item for item in status["official_results"] if not item["required"]}
            self.assertEqual(set(optional), {"S18", "S19", "S20", "S21", "S22"})
            self.assertTrue(all(item["status"] == "optional-not-imported" for item in optional.values()))
            source = Path(directory) / "material.html"
            source.write_text("<!doctype html><html><body>fixture</body></html>", encoding="utf-8")
            imported = research_run.import_official_source(
                workspace,
                source_id="S18",
                source_file=source,
                url="https://example.invalid/material-event",
                retrieved_on="2026-08-23",
            )
            self.assertEqual(imported["kind"], "official-material")
            self.assertTrue(imported["local_path"].endswith(".html"))
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            (workspace / "report.md").write_text(
                valid_report("money-craft.report.v1", "research"), encoding="utf-8"
            )
            (workspace / "thesis.md").write_text(
                valid_report("money-craft.thesis.v1", "thesis"), encoding="utf-8"
            )
            optional_reconciliation = valid_reconciliation()
            optional_reconciliation["material_disclosure_assessment"][0]["status"] = "imported"
            optional_reconciliation["material_disclosure_assessment"][0]["notes"] = (
                "A decision-critical material transaction disclosure was imported."
            )
            (workspace / "financial-reconciliation.json").write_text(
                json.dumps(optional_reconciliation, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            finalized = research_run.finalize_workspace(workspace)
            self.assertTrue(finalized["valid"])
            self.assertEqual(finalized["evidence_manifest"]["source_count"], 18)
            manifest = json.loads((workspace / "evidence-manifest.json").read_text(encoding="utf-8"))
            optional_source = next(item for item in manifest["sources"] if item["id"] == "S18")
            self.assertEqual(optional_source["kind"], "official-material")

    def test_cli_disabled_provider_fails_before_collection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "cli-run"
            runtime = ROOT / "skills" / "money-craft" / "scripts" / "money_craft.py"
            init = subprocess.run(
                [
                    sys.executable,
                    str(runtime),
                    "research",
                    "init",
                    "--security",
                    "美的集团",
                    "--thscode",
                    "000333.SZ",
                    "--as-of",
                    "2026-08-23",
                    "--latest-report",
                    "2026-1",
                    "--provider-mode",
                    "disabled",
                    "--workspace",
                    str(workspace),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stdout)
            environment = dict(os.environ)
            environment.pop("FUYAO_API_KEY", None)
            collect = subprocess.run(
                [sys.executable, str(runtime), "research", "collect", "--workspace", str(workspace), "--json"],
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            payload = json.loads(collect.stdout)
            self.assertEqual(collect.returncode, 2)
            self.assertEqual(payload["error"]["kind"], "provider_disabled")
            self.assertEqual(list((workspace / "evidence").glob("*.normalized.json")), [])

    def test_cli_init_without_workspace_uses_configured_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory) / "money"
            runtime = ROOT / "skills" / "money-craft" / "scripts" / "money_craft.py"
            environment = dict(os.environ)
            environment[research_run.OUTPUT_ROOT_ENV] = str(output_root)
            initialized = subprocess.run(
                [
                    sys.executable,
                    str(runtime),
                    "research",
                    "init",
                    "--security",
                    "美的集团",
                    "--thscode",
                    "000333.SZ",
                    "--as-of",
                    "2026-08-23",
                    "--latest-report",
                    "2026-1",
                    "--provider-mode",
                    "disabled",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stdout)
            payload = json.loads(initialized.stdout)
            workspace = Path(payload["workspace"])
            self.assertEqual(workspace.parent.name, ".research")
            self.assertEqual(workspace.parent.parent.name, "2026-08-23")
            self.assertEqual(workspace.parent.parent.parent.name, "000333-美的集团")
            self.assertEqual(workspace.name, payload["run_id"])
            self.assertTrue((workspace / "plan.json").is_file())


if __name__ == "__main__":
    unittest.main()
