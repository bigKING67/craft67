from __future__ import annotations

import json
import datetime as dt
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
TEMPLATE_ROOT = ROOT / "skills" / "money-craft" / "templates"
sys.path.insert(0, str(SCRIPT_DIR))

import tracking_workflow as tracking  # noqa: E402


INITIAL_UPDATE = "| 2026-08-23 | 初始建立 H01 | 初始估值 | 初始结论 | [S01] |"
NEXT_UPDATE = "| 2026-11-01 | H01 转为 WEAKENED | 下调 | 需要复核 | [S02] |"


def thesis_text(
    *,
    as_of: str,
    cutoff: str,
    hypothesis_state: str,
    update_rows: list[str],
) -> str:
    rows = "\n".join(update_rows)
    return f"""---
schema: money-craft.thesis.v1
workflow: thesis
security: Test Company
thscode: 600519.SH
as_of: {as_of}
data_cutoff: {cutoff}
base_currency: CNY
provider_status: unavailable
---
# Test Company 投资论文
## 结论
当前结论以正式证据为准。[S01][S02]
## 事实与证据
- 收入由正式报告核验 [S01]
- 现金流由独立来源复核 [S02]
## 核心假设
| ID | 假设 | 指标与阈值 | 验证来源 | 频率 | 状态 |
|---|---|---|---|---|---|
| H01 | 收入质量可持续 | 收入与现金流匹配 | [S01][S02] | 季度 | {hypothesis_state} |
## 估值与假设
情景估值仍需持续验证。[S01]
<!-- money-craft-calc: {{"id":"C01","operation":"multiply","inputs":["2","3"],"expected":"6","tolerance":"0.000001"}} -->
## 风险与反方证据
核心风险是现金流与利润背离。[S02]
## 证伪条件
| ID | 条件 | 严重度 | 当前状态 | 证据 |
|---|---|---|---|---|
| R01 | 现金流连续恶化 | fatal | CLEAR | [S02] |
## 更新记录
| 日期 | 假设变化 | 估值变化 | 结论变化 | 来源 |
|---|---|---|---|---|
{rows}
## 来源索引
- [S01] https://example.invalid/annual.pdf
- [S02] https://example.invalid/quarter.pdf
"""


class TrackingWorkflowTests(unittest.TestCase):
    def test_cli_rejects_invalid_run_state_without_publishing(self):
        for key, value in (("run_id", None), ("run_id", True), ("created_at", None),
                           ("created_at", "2026-09-19T24:00:00Z"), ("execution_boundary", {}),
                           ("source_research", True), ("previous", {})):
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as directory:
                root, workspace = self.candidate_with_states(Path(directory))
                path = workspace / "run-state.json"
                payload = json.loads(path.read_text())
                if value is None:
                    payload.pop(key)
                else:
                    payload[key] = value
                path.chmod(0o600)
                path.write_text(json.dumps(payload))
                before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
                result = subprocess.run([sys.executable, str(SCRIPT_DIR / "money_craft.py"), "track", "check",
                                         "--workspace", str(workspace), "--json"], capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid_workspace", result.stdout)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def create_two_revisions(self, base: Path) -> Path:
        root, workspace = self.candidate_with_states(base)
        tracking.finalize_tracking(workspace)
        initialized = tracking.initialize_tracking(root, as_of="2026-12-01", template_root=TEMPLATE_ROOT)
        workspace = Path(initialized["workspace"])
        path = workspace / "thesis.md"
        text = path.read_text().replace("as_of: 2026-11-01", "as_of: 2026-12-01").replace(
            "2026-11-01T12:00:00+08:00", "2026-12-01T12:00:00+08:00")
        text = text.replace("## 来源索引", "| 2026-12-01 | H01 复核 | 维持 | 继续跟踪 | [S02] |\n## 来源索引")
        path.write_text(text)
        thesis = tracking.research_workflow.load_thesis(path)
        state = tracking.initial_state(thesis, as_of="2026-12-01", source_research=None)
        state["next_mandatory_review"] = {"event": "quarterly disclosure", "required_workflow": "earnings-review"}
        (workspace / "state.json").write_bytes(tracking.json_bytes(state))
        path = workspace / "card.md"
        path.write_text(re.sub(r"\{\{[^{}]+\}\}", "reviewed", path.read_text()))
        tracking.finalize_tracking(workspace)
        return root

    def test_verify_rejects_missing_history_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = self.create_two_revisions(base)
            self.assertTrue(tracking.verify_tracking(root)["valid"])
            first = root / "revisions/t0001"
            os.chmod(first, 0o755)
            first.rename(base / "preserved-t0001")
            result = tracking.verify_tracking(root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("contiguous" in error for error in result["errors"]))
            status = tracking.tracking_status(root)
            self.assertEqual(status["assessment"]["integrity"], "INVALID")

    def test_verify_rejects_self_consistent_revision_with_wrong_predecessor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.create_two_revisions(Path(directory))
            revision = root / "revisions/t0002"
            for path in [revision, *revision.iterdir()]:
                os.chmod(path, 0o755 if path.is_dir() else 0o644)
            for name in ("thesis-diff.json", "update-plan.json"):
                path = revision / name
                data = json.loads(path.read_text())
                data["previous"]["sha256"] = "0" * 64
                path.write_bytes(tracking.json_bytes(data))
            path = revision / "TRACKING.json"
            manifest = json.loads(path.read_text())
            manifest["files"] = {name: tracking.file_record(revision / name) for name in sorted(tracking.REVISION_FILES)}
            path.write_bytes(tracking.json_bytes(manifest))
            (revision / "SHA256SUMS").write_bytes(tracking.make_checksums(revision))
            tracking.set_tree_read_only(revision)
            path = root / "current.json"
            current = json.loads(path.read_text())
            current.update(tracking_manifest_sha256=tracking.sha256_file(revision / "TRACKING.json"),
                           checksums_sha256=tracking.sha256_file(revision / "SHA256SUMS"))
            path.write_bytes(tracking.json_bytes(current))
            self.assertTrue(tracking.verify_revision(revision, require_read_only=True)["valid"])
            before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            result = tracking.verify_tracking(root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("previous thesis does not match" in error for error in result["errors"]))
            self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_cli_publication_failure_preserves_pointer_and_retry(self) -> None:
        for phase in ("revision_chmod", "pointer_replace", "directory_fsync"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                root, workspace = self.candidate_with_states(Path(directory))
                before = {p.name: p.read_bytes() for p in workspace.iterdir() if p.is_file()}
                injected = """
import os, stat, sys
from pathlib import Path
sys.path.insert(0, sys.argv.pop(1))
phase = sys.argv.pop(1)
import tracking_workflow as tracking
import money_craft
original_chmod, original_replace, original_fsync = os.chmod, os.replace, os.fsync
fired = False
def chmod(path, mode, *args, **kwargs):
    global fired
    if phase == 'revision_chmod' and Path(path).name == 't0001' and mode == 0o555 and not fired:
        fired = True
        raise OSError('injected revision chmod failure')
    return original_chmod(path, mode, *args, **kwargs)
def replace(source, destination):
    if phase == 'pointer_replace' and Path(destination).name == 'current.json':
        raise OSError('injected pointer replacement failure')
    return original_replace(source, destination)
def fsync(fd):
    if phase == 'directory_fsync' and stat.S_ISDIR(os.fstat(fd).st_mode):
        raise OSError('injected directory sync failure')
    return original_fsync(fd)
os.chmod, os.replace, os.fsync = chmod, replace, fsync
raise SystemExit(money_craft.main())
"""
                result = subprocess.run([sys.executable, "-c", injected, str(SCRIPT_DIR), phase,
                                         "track", "check", "--workspace", str(workspace)],
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("injected", result.stdout + result.stderr)
                self.assertEqual(before, {p.name: p.read_bytes() for p in workspace.iterdir() if p.is_file()})
                self.assertFalse(list((root / "revisions").glob(".*.staging.*")))
                if phase == "directory_fsync":
                    self.assertTrue(tracking.verify_tracking(root)["valid"])
                    with self.assertRaises(tracking.TrackingError) as error:
                        tracking.finalize_tracking(workspace)
                    self.assertEqual(error.exception.kind, "stale_previous")
                    self.assertFalse((root / "revisions/t0002").exists())
                    fresh = tracking.initialize_tracking(root, as_of="2026-12-01", template_root=TEMPLATE_ROOT)
                    self.assertTrue(Path(fresh["workspace"]).is_dir())
                else:
                    self.assertFalse((root / "current.json").exists())
                    self.assertEqual(list((root / "revisions").iterdir()), [])
                    tracking.finalize_tracking(workspace)
                    self.assertTrue(tracking.verify_tracking(root)["valid"])

    def test_cli_readers_wait_for_publication_snapshot(self) -> None:
        for command in ("verify", "status"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                root, workspace = self.candidate_with_states(Path(directory))
                paused_writer = """
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv.pop(1))
import money_craft
original = os.replace
def replace(source, destination):
    if Path(destination).name == 'current.json':
        print('POINTER_PENDING', flush=True)
        if sys.stdin.readline().strip() != 'continue':
            raise RuntimeError('test barrier cancelled')
    return original(source, destination)
os.replace = replace
raise SystemExit(money_craft.main())
"""
                with subprocess.Popen([sys.executable, "-c", paused_writer, str(SCRIPT_DIR),
                                       "track", "check", "--workspace", str(workspace)],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True) as writer:
                    reader = None
                    try:
                        self.assertEqual(writer.stdout.readline().strip(), "POINTER_PENDING")
                        reader = subprocess.Popen([sys.executable, str(SCRIPT_DIR / "money_craft.py"),
                                                   "track", command, "--tracking-root", str(root), "--json"],
                                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        early = None
                        try:
                            early = reader.communicate(timeout=0.3)
                        except subprocess.TimeoutExpired:
                            pass
                    finally:
                        writer_output, writer_error = writer.communicate("continue\n", timeout=10)
                        if reader is not None:
                            output, error = reader.communicate(timeout=10)
                    self.assertEqual(writer.returncode, 0, writer_output + writer_error)
                    self.assertIsNone(early, "reader observed an in-flight publication: " + str(early))
                    self.assertEqual(reader.returncode, 0, output + error)
                    payload = json.loads(output)
                    self.assertTrue(payload["valid"], payload)
                    self.assertEqual(payload["revision_count"], 1)
                    self.assertEqual(payload["current"]["tracking_revision"], "t0001")
                    if command == "status":
                        self.assertEqual(payload["assessment"]["integrity"], "VERIFIED")
                    self.assertTrue(tracking.verify_tracking(root)["valid"])

    @unittest.skipUnless(os.name == "posix", "SIGKILL recovery probe requires POSIX")
    def test_killed_publication_cannot_extend_invalid_history(self) -> None:
        for phase in ("before_pointer", "after_pointer"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                root, workspace = self.candidate_with_states(Path(directory))
                injected = """
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv.pop(1))
phase = sys.argv.pop(1)
import money_craft
original = os.replace
def replace(source, destination):
    if Path(destination).name != 'current.json':
        return original(source, destination)
    if phase == 'after_pointer':
        original(source, destination)
    print('KILL_READY', flush=True)
    sys.stdin.readline()
    raise RuntimeError('kill barrier unexpectedly released')
os.replace = replace
raise SystemExit(money_craft.main())
"""
                with subprocess.Popen([sys.executable, "-c", injected, str(SCRIPT_DIR), phase,
                                       "track", "check", "--workspace", str(workspace)],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True) as writer:
                    try:
                        self.assertEqual(writer.stdout.readline().strip(), "KILL_READY")
                    finally:
                        writer.kill()
                        writer.communicate(timeout=10)
                    self.assertLess(writer.returncode, 0)
                before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
                verified = subprocess.run([sys.executable, str(SCRIPT_DIR / "money_craft.py"),
                                           "track", "verify", "--tracking-root", str(root), "--json"],
                                          capture_output=True, text=True, timeout=10)
                self.assertEqual(json.loads(verified.stdout)["valid"], phase == "after_pointer")
                retry = subprocess.run([sys.executable, str(SCRIPT_DIR / "money_craft.py"),
                                        "track", "check", "--workspace", str(workspace), "--json"],
                                       capture_output=True, text=True, timeout=10)
                self.assertNotEqual(retry.returncode, 0, retry.stdout)
                self.assertIn("invalid_history" if phase == "before_pointer" else "stale_previous", retry.stdout)
                self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()})
                self.assertFalse((root / "revisions/t0002").exists())

    def candidate_with_states(self, base: Path, *, hypothesis="SUPPORTED", red_line="CLEAR", due=None) -> tuple[Path, Path]:
        root = base / "tracking"
        initialized = tracking.initialize_tracking(root, as_of="2026-11-01", previous=self.create_previous(base), template_root=TEMPLATE_ROOT)
        workspace = Path(initialized["workspace"])
        self.prepare_candidate(workspace)
        thesis_path = workspace / "thesis.md"
        text = thesis_path.read_text().replace("| WEAKENED |", f"| {hypothesis} |").replace("| CLEAR |", f"| {red_line} |")
        thesis_path.write_text(text)
        thesis = tracking.research_workflow.load_thesis(thesis_path)
        state = tracking.initial_state(thesis, as_of="2026-11-01", source_research=None)
        state["next_mandatory_review"] = {"event": "quarterly disclosure", "required_workflow": "earnings-review"}
        if due is not None:
            state["next_mandatory_review"]["due_date"] = due
        (workspace / "state.json").write_bytes(tracking.json_bytes(state))
        return root, workspace

    def test_unknown_evidence_never_receives_supported_or_numeric_health(self) -> None:
        for hypothesis, red_line in (("UNVERIFIED", "CLEAR"), ("SUPPORTED", "UNVERIFIED"), ("BROKEN", "UNVERIFIED")):
            with self.subTest(hypothesis=hypothesis, red_line=red_line), tempfile.TemporaryDirectory() as directory:
                root, workspace = self.candidate_with_states(Path(directory), hypothesis=hypothesis, red_line=red_line, due="2026-12-01")
                sealed = tracking.finalize_tracking(workspace)
                self.assertIsNone(sealed["health_score"])
                self.assertEqual(sealed["health_status"], "BROKEN" if hypothesis == "BROKEN" else "UNVERIFIED")
                status = tracking.tracking_status(root, today=dt.date(2026, 11, 2))
                self.assertTrue(status["valid"], status["errors"])
                self.assertIsNone(status["assessment"]["score"])
                self.assertNotEqual(status["assessment"]["status"], "SUPPORTED")

    def test_watch_is_not_supported_and_known_damage_retains_priority(self) -> None:
        for hypothesis, red_line, expected, score in (("SUPPORTED", "WATCH", "WATCH", 10), ("WEAKENED", "WATCH", "WEAKENED", 9), ("UNVERIFIED", "TRIGGERED", "BROKEN", None)):
            health = tracking.health_contract({"hypotheses": [{"ID": "H01", "状态": hypothesis}], "red_lines": [{"ID": "R01", "当前状态": red_line}]})
            self.assertEqual((health["status"], health["score"]), (expected, score))

    def test_health_rejects_missing_or_unknown_state_instead_of_defaulting(self) -> None:
        for hypotheses, red_lines in (([], []), ([{"ID": "H01", "状态": "ERROR"}], [{"ID": "R01", "当前状态": "CLEAR"}])):
            with self.assertRaises(tracking.TrackingError):
                tracking.health_contract({"hypotheses": hypotheses, "red_lines": red_lines})

    def test_review_window_does_not_rewrite_archived_health(self) -> None:
        for due, today, expected in ((None, dt.date(2026, 11, 2), "UNKNOWN"), ("2026-12-01", dt.date(2026, 12, 2), "STALE"), ("2026-12-01", dt.date(2026, 10, 31), "NOT_YET_VALID"), ("2026-12-01", dt.date(2026, 12, 1), "WITHIN_REVIEW_WINDOW")):
            with self.subTest(freshness=expected), tempfile.TemporaryDirectory() as directory:
                root, workspace = self.candidate_with_states(Path(directory), due=due)
                tracking.finalize_tracking(workspace)
                before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
                status = tracking.tracking_status(root, today=today)
                self.assertTrue(status["valid"])
                self.assertEqual(status["assessment"]["freshness"], expected)
                self.assertEqual(status["assessment"]["status"], "SUPPORTED" if expected == "WITHIN_REVIEW_WINDOW" else "UNVERIFIED")
                self.assertEqual(status["assessment"]["score"], 10 if expected == "WITHIN_REVIEW_WINDOW" else None)
                self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_invalid_review_deadline_blocks_sealing(self) -> None:
        for due in ("2026-10-31", "20261130", "2026-11-31", 1):
            with self.subTest(due=due), tempfile.TemporaryDirectory() as directory:
                root, workspace = self.candidate_with_states(Path(directory), due=due)
                with self.assertRaises(tracking.TrackingError):
                    tracking.finalize_tracking(workspace)
                self.assertFalse((root / "current.json").exists())

    def test_failed_calculation_cannot_seal_a_supported_thesis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.candidate_with_states(Path(directory), due="2026-12-01")
            thesis = workspace / "thesis.md"
            thesis.write_text(thesis.read_text().replace('"tolerance":"0.000001"', '"tolerance":"NaN"'))
            with self.assertRaises(tracking.TrackingError) as error:
                tracking.finalize_tracking(workspace)
            self.assertEqual(error.exception.kind, "financial_audit_failed")
            self.assertFalse((root / "current.json").exists())
            self.assertTrue(workspace.is_dir())

    def test_status_does_not_trust_tampered_health_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.candidate_with_states(Path(directory), hypothesis="BROKEN", due="2026-12-01")
            tracking.finalize_tracking(workspace)
            p = root / "current.json"; current = json.loads(p.read_text())
            current.update(health_score=10, health_status="SUPPORTED")
            p.write_bytes(tracking.json_bytes(current))
            status = tracking.tracking_status(root, today=dt.date(2026, 11, 2))
            self.assertFalse(status["valid"])
            self.assertEqual(status["assessment"]["integrity"], "INVALID")
            self.assertIsNone(status["assessment"]["score"])
            self.assertEqual(status["assessment"]["status"], "UNVERIFIED")

    def test_legacy_sealed_unknown_is_verifiable_but_not_current_support(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.candidate_with_states(Path(directory), hypothesis="UNVERIFIED", due="2026-12-01")
            tracking.finalize_tracking(workspace)
            revision = root / "revisions" / "t0001"
            for p in revision.iterdir():
                p.chmod(0o600)
            state = json.loads((revision / "state.json").read_text())
            state["schema"] = "money-craft.tracking-state.v1"
            state["health"].update(score=10, status="SUPPORTED", formula="10")
            state["next_mandatory_review"]["due_date"] = "2026-10-31"  # v1 allowed this metadata.
            (revision / "state.json").write_bytes(tracking.json_bytes(state))
            manifest = json.loads((revision / "TRACKING.json").read_text())
            manifest["schema"] = "money-craft.tracking-revision.v1"
            manifest["result"].update(health_score=10, health_status="SUPPORTED")
            manifest["files"]["state.json"] = tracking.file_record(revision / "state.json")
            (revision / "TRACKING.json").write_bytes(tracking.json_bytes(manifest))
            (revision / "SHA256SUMS").write_bytes(tracking.make_checksums(revision))
            for p in revision.iterdir():
                p.chmod(0o444)
            p = root / "current.json"; current = json.loads(p.read_text())
            current.update(schema="money-craft.tracking-current.v1", health_score=10, tracking_manifest_sha256=tracking.sha256_file(revision / "TRACKING.json"), checksums_sha256=tracking.sha256_file(revision / "SHA256SUMS"))
            current.pop("health_status")
            p.write_bytes(tracking.json_bytes(current))
            verified = tracking.verify_tracking(root)
            self.assertTrue(verified["valid"], verified["errors"])
            self.assertTrue(any("legacy" in w for w in verified["warnings"]))
            status = tracking.tracking_status(root, today=dt.date(2026, 11, 2))
            self.assertIsNone(status["assessment"]["score"])
            self.assertEqual(status["assessment"]["status"], "UNVERIFIED")
            self.assertEqual(status["assessment"]["freshness"], "UNKNOWN")
            self.assertEqual(status["current"]["health_score"], 10)  # Archival value stays untouched.

    def test_global_thesis_initializes_tracking_with_security_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            previous = base / "previous-global.md"
            text = thesis_text(
                as_of="2026-08-23",
                cutoff="2026-08-23T12:00:00+08:00",
                hypothesis_state="UNVERIFIED",
                update_rows=[INITIAL_UPDATE],
            )
            text = text.replace("security: Test Company", "security: NVIDIA Corporation")
            text = text.replace("thscode: 600519.SH", "security_id: US-NASDAQ:NVDA")
            text = text.replace("base_currency: CNY", "base_currency: USD")
            previous.write_text(text, encoding="utf-8")
            initialized = tracking.initialize_tracking(
                base / "tracking",
                as_of="2026-11-01",
                previous=previous,
                template_root=TEMPLATE_ROOT,
            )
            workspace = Path(initialized["workspace"])
            state = json.loads((workspace / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["security_id"], "US-NASDAQ:NVDA")
            self.assertEqual(state["base_currency"], "USD")
            self.assertIn("US-NASDAQ:NVDA", (workspace / "card.md").read_text(encoding="utf-8"))

    def create_previous(self, root: Path) -> Path:
        previous = root / "previous.md"
        previous.write_text(
            thesis_text(
                as_of="2026-08-23",
                cutoff="2026-08-23T12:00:00+08:00",
                hypothesis_state="UNVERIFIED",
                update_rows=[INITIAL_UPDATE],
            ),
            encoding="utf-8",
        )
        return previous

    def prepare_candidate(self, workspace: Path, *, valid_health: bool = True) -> None:
        (workspace / "thesis.md").write_text(
            thesis_text(
                as_of="2026-11-01",
                cutoff="2026-11-01T12:00:00+08:00",
                hypothesis_state="WEAKENED",
                update_rows=[INITIAL_UPDATE, NEXT_UPDATE],
            ),
            encoding="utf-8",
        )
        card = (workspace / "card.md").read_text(encoding="utf-8")
        (workspace / "card.md").write_text(
            re.sub(r"\{\{[^{}]+\}\}", "已由正式证据复核", card),
            encoding="utf-8",
        )
        state = json.loads((workspace / "state.json").read_text(encoding="utf-8"))
        state["as_of"] = "2026-11-01"
        state["data_cutoff"] = "2026-11-01T12:00:00+08:00"
        state["hypotheses"] = {"H01": "WEAKENED"}
        state["health"] = {
            "score": 9 if valid_health else 10,
            "maximum": 10,
            "status": "WEAKENED",
            "formula": "10 - 1 weakened hypothesis",
        }
        state["next_mandatory_review"] = {
            "event": "下一份正式定期报告",
            "required_workflow": "earnings-review then track init/check",
        }
        (workspace / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_init_check_status_verify_and_current_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            previous = self.create_previous(base)
            root = base / "tracking"
            initialized = tracking.initialize_tracking(
                root,
                as_of="2026-11-01",
                previous=previous,
                template_root=TEMPLATE_ROOT,
            )
            workspace = Path(initialized["workspace"])
            self.assertEqual(initialized["schema"], "money-craft.tracking-init.v1")
            self.assertFalse(initialized["execution_boundary"]["network_used"])
            self.assertEqual(stat.S_IMODE((workspace / "run-state.json").stat().st_mode), 0o400)
            self.assertEqual(stat.S_IMODE((workspace / "previous-thesis.md").stat().st_mode), 0o400)

            self.prepare_candidate(workspace)
            sealed = tracking.finalize_tracking(workspace)
            self.assertEqual(sealed["tracking_revision"], "t0001")
            self.assertFalse(workspace.exists())
            revision = root / "revisions" / "t0001"
            self.assertTrue(revision.is_dir())
            self.assertEqual(stat.S_IMODE(revision.stat().st_mode) & 0o222, 0)
            self.assertEqual(stat.S_IMODE((revision / "thesis.md").stat().st_mode) & 0o222, 0)

            status = tracking.tracking_status(root)
            self.assertEqual(status["revisions"], ["t0001"])
            self.assertEqual(status["current"]["tracking_revision"], "t0001")
            verified = tracking.verify_tracking(root)
            self.assertTrue(verified["valid"], verified["errors"])

            next_run = tracking.initialize_tracking(
                root,
                as_of="2026-12-01",
                template_root=TEMPLATE_ROOT,
            )
            next_state = json.loads((Path(next_run["workspace"]) / "run-state.json").read_text(encoding="utf-8"))
            self.assertEqual(next_state["previous"]["path"], str((revision / "thesis.md").resolve()))

    def test_cli_rejects_stale_workspace_and_preserves_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            previous = self.create_previous(base)
            root = base / "tracking"
            workspaces = []
            for _ in range(2):
                init = tracking.initialize_tracking(root, as_of="2026-11-01", previous=previous, template_root=TEMPLATE_ROOT)
                workspace = Path(init["workspace"])
                self.prepare_candidate(workspace)
                workspaces.append(workspace)
            def check(workspace):
                result = subprocess.run([sys.executable, str(SCRIPT_DIR / "money_craft.py"), "track", "check",
                                         "--workspace", str(workspace), "--json"], capture_output=True, text=True, timeout=30)
                return result.returncode, json.loads(result.stdout)
            self.assertEqual(check(workspaces[0])[0], 0)
            before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            code, result = check(workspaces[1])
            self.assertEqual(code, 2)
            self.assertEqual(result["error"]["kind"], "stale_previous")
            self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()})
            self.assertTrue(workspaces[1].is_dir())
            self.assertFalse((root / "revisions/t0002").exists())
            self.assertTrue(tracking.verify_tracking(root)["valid"])
            fresh = tracking.initialize_tracking(root, as_of="2026-12-01", template_root=TEMPLATE_ROOT)
            fresh_workspace = Path(fresh["workspace"])
            self.prepare_candidate(fresh_workspace)
            thesis_path = fresh_workspace / "thesis.md"
            text = thesis_path.read_text().replace("as_of: 2026-11-01", "as_of: 2026-12-01").replace(
                "data_cutoff: 2026-11-01T12:00:00+08:00", "data_cutoff: 2026-12-01T12:00:00+08:00")
            text = text.replace(NEXT_UPDATE, NEXT_UPDATE + "\n| 2026-12-01 | H01 复核 | 维持 | 继续跟踪 | [S02] |")
            thesis_path.write_text(text)
            state_path = fresh_workspace / "state.json"
            state = json.loads(state_path.read_text())
            state.update(as_of="2026-12-01", data_cutoff="2026-12-01T12:00:00+08:00")
            state_path.write_text(json.dumps(state))
            code, result = check(fresh_workspace)
            self.assertEqual(code, 0, result)
            self.assertEqual(result["tracking_revision"], "t0002")
            self.assertTrue(tracking.verify_tracking(root)["valid"])

    def test_check_rejects_health_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            initialized = tracking.initialize_tracking(
                base / "tracking",
                as_of="2026-11-01",
                previous=self.create_previous(base),
                template_root=TEMPLATE_ROOT,
            )
            workspace = Path(initialized["workspace"])
            self.prepare_candidate(workspace, valid_health=False)
            with self.assertRaisesRegex(tracking.TrackingError, "health"):
                tracking.finalize_tracking(workspace)
            self.assertTrue(workspace.is_dir())

    def test_check_rejects_rewritten_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            initialized = tracking.initialize_tracking(
                base / "tracking",
                as_of="2026-11-01",
                previous=self.create_previous(base),
                template_root=TEMPLATE_ROOT,
            )
            workspace = Path(initialized["workspace"])
            self.prepare_candidate(workspace)
            thesis = (workspace / "thesis.md").read_text(encoding="utf-8")
            (workspace / "thesis.md").write_text(
                thesis.replace("初始建立 H01", "改写历史 H01"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(tracking.TrackingError, "preserved verbatim"):
                tracking.finalize_tracking(workspace)

    def test_verify_detects_writable_or_tampered_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "tracking"
            initialized = tracking.initialize_tracking(
                root,
                as_of="2026-11-01",
                previous=self.create_previous(base),
                template_root=TEMPLATE_ROOT,
            )
            workspace = Path(initialized["workspace"])
            self.prepare_candidate(workspace)
            tracking.finalize_tracking(workspace)
            thesis = root / "revisions" / "t0001" / "thesis.md"
            os.chmod(thesis, 0o644)
            verified = tracking.verify_tracking(root)
            self.assertFalse(verified["valid"])
            self.assertTrue(any("writable" in message for message in verified["errors"]))
            thesis.write_text(thesis.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            os.chmod(thesis, 0o444)
            tampered = tracking.verify_tracking(root)
            self.assertFalse(tampered["valid"])
            self.assertTrue(any("mismatch" in message for message in tampered["errors"]))

    def test_init_hash_binds_optional_formal_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            previous = self.create_previous(base)
            formal = base / "r0001"
            formal.mkdir()
            revision_manifest = formal / "REVISION.json"
            revision_manifest.write_text(
                json.dumps(
                    {
                        "schema": "codex.investment-archive-revision.v1",
                        "research_id": "600519-Test Company/2026-08-23",
                        "revision_id": "r0001",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            initialized = tracking.initialize_tracking(
                base / "tracking",
                as_of="2026-11-01",
                previous=previous,
                source_revision=formal,
                template_root=TEMPLATE_ROOT,
            )
            state = json.loads((Path(initialized["workspace"]) / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["source_research"]["revision_id"], "r0001")
            self.assertEqual(
                state["source_research"]["revision_manifest_sha256"],
                tracking.sha256_file(revision_manifest),
            )

    def test_cli_status_and_verify_are_model_free(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "tracking"
            previous = self.create_previous(base)
            initialized_command = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "money_craft.py"),
                    "track",
                    "init",
                    "--tracking-root",
                    str(root),
                    "--previous",
                    str(previous),
                    "--as-of",
                    "2026-11-01",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(initialized_command.returncode, 0, initialized_command.stdout)
            initialized = json.loads(initialized_command.stdout)
            workspace = Path(initialized["workspace"])
            self.prepare_candidate(workspace)
            checked = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "money_craft.py"),
                    "track",
                    "check",
                    "--workspace",
                    str(workspace),
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stdout)
            self.assertEqual(json.loads(checked.stdout)["tracking_revision"], "t0001")
            for command in ("status", "verify"):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT_DIR / "money_craft.py"),
                        "track",
                        command,
                        "--tracking-root",
                        str(root),
                        "--json",
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stdout)
                payload = json.loads(completed.stdout)
                self.assertTrue(payload["valid"])
                self.assertFalse(payload["network_used"])


if __name__ == "__main__":
    unittest.main()
