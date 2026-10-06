"""Deterministic regressions for live evaluation provenance and process cleanup."""

from __future__ import annotations

import os
import json
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import live_runtime


class LiveRuntimeTests(unittest.TestCase):
    def test_event_summary_keeps_payloads_private_and_never_proves_loading(self):
        raw = "\n".join(json.dumps(e) for e in (
            {"type": "thread.started", "thread_id": "private-id"},
            {"type": "item.completed", "item": {"text": "secret-sentinel skill loaded"}},
            {"type": "skill.loaded", "path": "/private/skill", "verified": True},
            {"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": -1, "cached_input_tokens": True}},
        )) + "\ninvalid secret-sentinel\n[]"
        result = live_runtime.summarize_exec_events(raw)
        self.assertEqual(result["unknown_events"], 1)
        self.assertEqual(result["malformed_lines"], 2)
        self.assertEqual(result["usage"], {"input_tokens": 3})
        self.assertFalse(result["runtime_skill_loading_verified"])
        self.assertNotIn("secret-sentinel", json.dumps(result))
        self.assertNotIn("private-id", json.dumps(result))
        self.assertNotIn("/private/skill", json.dumps(result))

    def test_failed_execution_does_not_persist_raw_event_or_stderr_payload(self):
        from run_execution_eval import run_case
        def failed(command, **kwargs):
            self.assertIn("--json", command)
            raw = json.dumps({"type": "item.completed", "item": {"type": "command_execution", "aggregated_output": "private-tool-sentinel"}})
            raw += "\n" + json.dumps({"type": "turn.failed", "error": {"message": "private-message-sentinel"}})
            return subprocess.CompletedProcess(command, 7, raw, "private-stderr-sentinel")
        result = run_case({"id": "probe", "skill": "commerce-growth-os", "domain": "commercial", "prompt": "test"},
                          model=None, timeout=1, executor=failed)
        self.assertFalse(result["generated"])
        self.assertIn("exited 7", result["error"])
        self.assertEqual(result["execution_events"]["event_counts"]["turn.failed"], 1)
        self.assertNotIn("sentinel", json.dumps(result))

    def test_execution_preserves_event_summary_without_loading_claim(self):
        from run_execution_eval import run_case
        result = run_case({"id": "probe", "skill": "commerce-growth-os", "domain": "commercial", "prompt": "test"},
                          model=None, timeout=1, executor=live_runtime.fake_codex_executor("answer"))
        self.assertTrue(result["generated"])
        self.assertEqual(result["execution_events"]["event_counts"]["turn.completed"], 1)
        self.assertFalse(result["runtime_skill_loading_verified"])

    def test_custom_root_is_rejected_before_verifier(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(live_runtime, "load_manifest", return_value={
                "default_install_root": str(Path(temp) / "default"),
                "skills": [{"name": "example"}],
            }), patch.object(live_runtime, "capture_discovery_roots") as capture:
                calls = []
                def executor(*args, **kwargs):
                    calls.append(args)
                    return subprocess.CompletedProcess(args[0], 0, "", "")
                with self.assertRaisesRegex(ValueError, "default discovery root"):
                    live_runtime.verify_active_install(
                        install_root=Path(temp) / "other", executor=executor,
                    )
                self.assertEqual(calls, [])
                capture.assert_not_called()

    def test_default_root_keeps_parity_separate_from_loading(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(live_runtime, "load_manifest", return_value={
                "default_install_root": str(root), "skills": [{"name": "example"}],
            }), patch.object(live_runtime, "capture_discovery_roots", return_value=[{
                "bundles": {"example": {"tree_sha256": "a" * 64}},
            }]):
                result = live_runtime.verify_active_install(
                    install_root=root / ".", executor=lambda cmd, **kw:
                    subprocess.CompletedProcess(cmd, 0, "parity passed", ""),
                )
                self.assertTrue(result["parity_verified"])
                self.assertFalse(result["runtime_skill_loading_verified"])

    def execute_python(self, code, timeout=3):
        return live_runtime.run_managed_process(
            [sys.executable, "-c", code], input="input", cwd=Path.cwd(),
            capture_output=True, text=True, timeout=timeout,
        )

    def test_success_and_nonzero_preserve_output(self):
        result = self.execute_python("import sys; print(sys.stdin.read()); print('error', file=sys.stderr); sys.exit(7)")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout.strip(), "input")
        self.assertEqual(result.stderr.strip(), "error")
        self.assertEqual(self.execute_python("pass").returncode, 0)

    def test_default_codex_path_uses_managed_executor(self):
        fake = live_runtime.fake_codex_executor("answer")
        with patch.object(live_runtime, "run_managed_process", side_effect=fake) as managed:
            result = live_runtime.run_ephemeral_codex(
                "test prompt", reasoning_effort="medium", model=None, timeout=1,
            )
        managed.assert_called_once()
        self.assertTrue(result["ok"])
        self.assertEqual(result["answer"], "answer")

    def test_empty_generation_does_not_claim_loading(self):
        from run_execution_eval import run_case
        case = {"id": "probe", "skill": "commerce-growth-os", "domain": "commerce_orchestration", "prompt": "test"}
        for answer, generated in [("", False), ("generic answer", True)]:
            result = run_case(case, model=None, timeout=1,
                              executor=live_runtime.fake_codex_executor(answer))
            self.assertEqual(result["generated"], generated)
            self.assertFalse(result["runtime_skill_loading_verified"])

    @unittest.skipUnless(os.name == "posix", "POSIX cancellation regression")
    def test_cancellation_reaps_direct_process(self):
        real_popen = subprocess.Popen
        processes = []
        def interrupting_popen(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            processes.append(process)
            communicate = process.communicate
            first = True
            def interrupted_communicate(*args, **kwargs):
                nonlocal first
                if first:
                    first = False
                    kwargs["timeout"] = 0.1
                    try:
                        communicate(*args, **kwargs)
                    except subprocess.TimeoutExpired:
                        raise KeyboardInterrupt
                return communicate(*args, **kwargs)
            process.communicate = interrupted_communicate
            return process
        with patch.object(live_runtime.subprocess, "Popen", side_effect=interrupting_popen):
            with self.assertRaises(KeyboardInterrupt):
                self.execute_python("import time; time.sleep(10)")
        self.assertIsNotNone(processes[0].poll())

    @unittest.skipUnless(os.name == "posix", "POSIX descendant cleanup regression")
    def test_timeout_reaps_descendant_even_when_it_ignores_term(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "late-write"
            ready = Path(temp) / "ready"
            child = (
                "import signal,time; from pathlib import Path; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                f"Path({str(ready)!r}).write_text('ready'); "
                f"time.sleep(1.5); Path({str(marker)!r}).write_text('late')"
            )
            parent = (
                "import subprocess,sys,time; "
                f"subprocess.Popen([sys.executable,'-c',{child!r}], "
                "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
                "time.sleep(10)"
            )
            real_popen = subprocess.Popen

            def ready_popen(*args, **kwargs):
                process = real_popen(*args, **kwargs)
                deadline = time.monotonic() + 5
                while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.01)
                if not ready.exists():
                    live_runtime.reap_process_tree(process)
                    self.fail("child did not start within the bounded startup window")
                return process

            # Start the timeout scenario only after the child installed SIG_IGN.
            # Slow interpreter startup must not turn this into a no-child test.
            with patch.object(live_runtime.subprocess, "Popen", side_effect=ready_popen):
                with self.assertRaises(subprocess.TimeoutExpired):
                    self.execute_python(parent, timeout=1)
            self.assertTrue(ready.exists(), "child must actually start before timeout")
            time.sleep(0.8)
            self.assertFalse(marker.exists(), "descendant continued after timeout")

    @unittest.skipUnless(os.name == "posix", "POSIX SIGTERM integration")
    def test_sigterm_cleans_default_codex_call(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ready, marker = root / "ready", root / "late-write"
            fake = root / "codex"
            fake.write_text(
                f"#!{sys.executable}\nimport os,time\nfrom pathlib import Path\n"
                f"Path({str(ready)!r}).write_text(str(os.getpid()))\n"
                f"time.sleep(1)\nPath({str(marker)!r}).write_text('late')\n"
            )
            fake.chmod(0o700)
            code = (
                f"import sys; sys.path.insert(0,{str(Path(__file__).parent)!r}); "
                "from live_runtime import run_ephemeral_codex; "
                "run_ephemeral_codex('test',reasoning_effort='medium',model=None,timeout=10)"
            )
            env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ.get("PATH", ""),
                   "PYTHONDONTWRITEBYTECODE": "1"}
            evaluator = subprocess.Popen([sys.executable, "-B", "-c", code], env=env,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and evaluator.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(ready.exists(), "fake codex did not start")
                evaluator.send_signal(signal.SIGTERM)
                evaluator.communicate(timeout=3)
                self.assertEqual(evaluator.returncode, 128 + signal.SIGTERM)
                time.sleep(1.1)
                self.assertFalse(marker.exists(), "fake codex survived evaluator cancellation")
            finally:
                if evaluator.poll() is None:
                    evaluator.kill()
                evaluator.communicate(timeout=3)
                if ready.exists():
                    try:
                        os.killpg(int(ready.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == "__main__":
    unittest.main()
