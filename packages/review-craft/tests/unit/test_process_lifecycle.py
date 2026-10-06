from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_LIB = ROOT / "skills/review-craft/lib"
sys.path.insert(0, str(RUNTIME_LIB))

from review_craft import process_lifecycle  # noqa: E402
from review_craft.process_lifecycle import run_process  # noqa: E402


class ProcessLifecycleTests(unittest.TestCase):
    def test_job_assignment_rejection_uses_process_group_fallback(self) -> None:
        process = MagicMock()
        with (
            patch.object(process_lifecycle.subprocess, "Popen", return_value=process),
            patch.object(
                process_lifecycle,
                "_assign_windows_kill_job",
                side_effect=PermissionError(5, "Access is denied"),
            ),
        ):
            opened = process_lifecycle.open_process_tree(["fixture"])

        self.assertIs(opened, process)
        process.kill.assert_not_called()

    def test_taskkill_failure_does_not_claim_confirmed_cleanup(self) -> None:
        process = MagicMock()
        process.pid = 1234
        process.poll.return_value = None
        setattr(process, process_lifecycle._WINDOWS_JOB_ATTRIBUTE, None)
        completed = MagicMock(returncode=1)
        with (
            patch.object(
                process_lifecycle,
                "_terminate_windows_snapshot_tree",
                return_value=False,
            ),
            patch.object(process_lifecycle.subprocess, "run", return_value=completed),
        ):
            cleanup = process_lifecycle._terminate_windows_tree(process)

        self.assertEqual(cleanup, "FAILED")
        process.kill.assert_called_once_with()

    def test_taskkill_success_confirms_fallback_cleanup(self) -> None:
        process = MagicMock()
        process.pid = 1234
        process.poll.return_value = 1
        setattr(process, process_lifecycle._WINDOWS_JOB_ATTRIBUTE, None)
        completed = MagicMock(returncode=0)
        with (
            patch.object(
                process_lifecycle,
                "_terminate_windows_snapshot_tree",
                return_value=False,
            ),
            patch.object(process_lifecycle.subprocess, "run", return_value=completed),
        ):
            cleanup = process_lifecycle._terminate_windows_tree(process)

        self.assertEqual(cleanup, "CONFIRMED")
        process.kill.assert_not_called()

    def test_native_snapshot_cleanup_avoids_taskkill_fallback(self) -> None:
        process = MagicMock()
        process.pid = 1234
        process.poll.return_value = 1
        setattr(process, process_lifecycle._WINDOWS_JOB_ATTRIBUTE, None)
        with (
            patch.object(
                process_lifecycle,
                "_terminate_windows_snapshot_tree",
                return_value=True,
            ),
            patch.object(process_lifecycle.subprocess, "run") as taskkill,
        ):
            cleanup = process_lifecycle._terminate_windows_tree(process)

        self.assertEqual(cleanup, "CONFIRMED")
        taskkill.assert_not_called()

    def test_job_cleanup_also_terminates_the_snapshotted_tree(self) -> None:
        process = MagicMock()
        process.pid = 1234
        process.poll.return_value = 1
        setattr(process, process_lifecycle._WINDOWS_JOB_ATTRIBUTE, 99)
        with (
            patch.object(
                process_lifecycle,
                "_terminate_windows_snapshot_tree",
                return_value=True,
            ) as snapshot_cleanup,
            patch.object(
                process_lifecycle,
                "_close_windows_job",
                return_value=True,
            ) as close_job,
            patch.object(process_lifecycle.subprocess, "run") as taskkill,
        ):
            cleanup = process_lifecycle._terminate_windows_tree(process)

        self.assertEqual(cleanup, "CONFIRMED")
        snapshot_cleanup.assert_called_once_with(process)
        close_job.assert_called_once_with(process)
        taskkill.assert_not_called()

    def test_native_descendant_failure_preserves_root_for_taskkill(self) -> None:
        process = MagicMock()
        process.pid = 1234
        with (
            patch.object(
                process_lifecycle,
                "_windows_process_tree",
                return_value=[5678, 1234],
            ),
            patch.object(
                process_lifecycle,
                "_terminate_windows_pid",
                side_effect=[False],
            ) as terminate_pid,
        ):
            confirmed = process_lifecycle._terminate_windows_snapshot_tree(process)

        self.assertFalse(confirmed)
        terminate_pid.assert_called_once_with(5678)

    def test_timeout_preserves_partial_output_and_explicit_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_process(
                [
                    sys.executable,
                    "-c",
                    (
                        "import os, time; "
                        "print(os.environ['REVIEW_CRAFT_PROCESS_TEST'], flush=True); "
                        "time.sleep(30)"
                    ),
                ],
                cwd=Path(directory),
                timeout=1,
                env={**os.environ, "REVIEW_CRAFT_PROCESS_TEST": "streamed"},
            )

        self.assertTrue(result.timed_out)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.replace(b"\r\n", b"\n"), b"streamed\n")
        self.assertEqual(result.process_tree_cleanup, "CONFIRMED")

    @unittest.skipIf(os.name == "nt", "POSIX process-group assertion")
    def test_timeout_terminates_spawned_child_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child_pid_path = root / "child.pid"
            result = run_process(
                [
                    sys.executable,
                    "-c",
                    (
                        "import pathlib, subprocess, sys, time; "
                        "child=subprocess.Popen([sys.executable, '-c', "
                        "'import time; time.sleep(30)']); "
                        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
                        "print('ready', flush=True); time.sleep(30)"
                    ),
                ],
                cwd=root,
                timeout=1,
            )
            child_pid = int(child_pid_path.read_text(encoding="utf-8"))

            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                try:
                    os.kill(child_pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.02)
            else:
                self.fail("spawned child survived process-tree cleanup")

        self.assertTrue(result.timed_out)
        self.assertEqual(result.process_tree_cleanup, "CONFIRMED")

    def test_keyboard_interrupt_cleans_process_tree_and_reraises(self) -> None:
        class InterruptedProcess:
            def communicate(self, timeout: int | None = None) -> tuple[bytes, bytes]:
                raise KeyboardInterrupt

        process = InterruptedProcess()
        with (
            patch.object(
                process_lifecycle,
                "open_process_tree",
                return_value=process,
            ),
            patch.object(
                process_lifecycle,
                "terminate_process_tree",
                return_value="CONFIRMED",
            ) as terminate,
            self.assertRaises(KeyboardInterrupt),
        ):
            run_process(["fixture"], cwd=Path.cwd(), timeout=1)

        terminate.assert_called_once_with(process)


if __name__ == "__main__":
    unittest.main()
