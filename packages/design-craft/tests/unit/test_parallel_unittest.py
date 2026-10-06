from __future__ import annotations

import unittest
from unittest import mock

from scripts import design_craft_parallel_unittest as parallel_unittest


class ParallelUnittestTests(unittest.TestCase):
    def test_collect_test_ids_is_complete_and_sorted(self) -> None:
        test_ids = parallel_unittest.collect_test_ids(
            ["tests.contract.test_installer.InstallerContractTests"]
        )

        self.assertEqual(len(test_ids), 5)
        self.assertEqual(test_ids, sorted(test_ids))
        self.assertTrue(
            all(test_id.startswith("tests.contract.test_installer.") for test_id in test_ids)
        )

    def test_discover_modules_is_complete_and_sorted(self) -> None:
        modules = parallel_unittest.discover_modules("tests/unit", "test_*.py")

        self.assertEqual(modules, sorted(modules))
        self.assertIn("tests.unit.test_parallel_unittest", modules)
        self.assertEqual(len(modules), len(set(modules)))

    def test_collect_isolated_tasks_combines_lanes_without_duplicates(self) -> None:
        tasks = parallel_unittest.collect_isolated_tasks(
            ["tests/integration", "tests/adversarial"],
            ["tests.contract.test_installer"],
            "test_*.py",
        )

        self.assertEqual(tasks, sorted(set(tasks)))
        self.assertIn("tests.integration.test_visual_reference_cli", tasks)
        self.assertIn("tests.adversarial.test_shadow_lab_boundaries", tasks)
        self.assertTrue(
            any(task.endswith("test_dry_run_does_not_write") for task in tasks)
        )

    def test_run_tests_preserves_input_order(self) -> None:
        def fake_run(test_id: str) -> parallel_unittest.TestResult:
            return parallel_unittest.TestResult(test_id, 0, "", "")

        with mock.patch.object(parallel_unittest, "run_test", side_effect=fake_run):
            results = parallel_unittest.run_tests(["test.z", "test.a"], jobs=2)

        self.assertEqual([result.test_id for result in results], ["test.z", "test.a"])

    def test_failure_result_remains_observable(self) -> None:
        expected = parallel_unittest.TestResult("test.failure", 1, "", "trace")
        with mock.patch.object(parallel_unittest, "run_test", return_value=expected):
            results = parallel_unittest.run_tests(["test.failure"], jobs=4)

        self.assertEqual(results, [expected])

    def test_module_worker_reports_success(self) -> None:
        result = parallel_unittest.run_module_test(
            "tests.unit.test_parallel_unittest.ParallelUnittestTests."
            "test_discover_modules_is_complete_and_sorted"
        )

        self.assertEqual(result.returncode, 0)

    def test_run_modules_preserves_input_order(self) -> None:
        observed: list[tuple[int, int]] = []

        class FakeExecutor:
            def __init__(self, *, max_workers: int) -> None:
                observed.append((max_workers, 0))

            def __enter__(self) -> "FakeExecutor":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def map(
                self,
                function: object,
                modules: list[str],
                *,
                chunksize: int,
            ) -> list[parallel_unittest.TestResult]:
                observed[-1] = (observed[-1][0], chunksize)
                return [parallel_unittest.TestResult(module, 0, "", "") for module in modules]

        with (
            mock.patch.object(
                parallel_unittest.concurrent.futures,
                "ProcessPoolExecutor",
                FakeExecutor,
            ),
            mock.patch.object(parallel_unittest.os, "cpu_count", return_value=8),
        ):
            results = parallel_unittest.run_modules(["test.z", "test.a"], jobs=4)

        self.assertEqual([result.test_id for result in results], ["test.z", "test.a"])
        self.assertEqual(observed, [(2, 1)])

    def test_module_workers_do_not_exceed_available_cpus(self) -> None:
        with mock.patch.object(parallel_unittest.os, "cpu_count", return_value=4):
            workers = parallel_unittest.module_worker_count(
                [f"tests.unit.test_{index}" for index in range(10)], jobs=8
            )

        self.assertEqual(workers, 4)

    @mock.patch.object(parallel_unittest.subprocess, "run")
    def test_subprocess_disables_bytecode_writes(self, run: mock.Mock) -> None:
        run.return_value.returncode = 0
        run.return_value.stdout = ""
        run.return_value.stderr = ""

        parallel_unittest.run_test("tests.unit.test_parallel_unittest")

        self.assertEqual(run.call_args.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1")

    @mock.patch.object(parallel_unittest.subprocess, "run")
    def test_group_uses_one_subprocess_for_all_modules(self, run: mock.Mock) -> None:
        run.return_value.returncode = 0
        run.return_value.stdout = ""
        run.return_value.stderr = ""

        parallel_unittest.run_test_group(["tests.unit.test_a", "tests.unit.test_b"])

        self.assertEqual(
            run.call_args.args[0],
            [
                parallel_unittest.sys.executable,
                "-m",
                "unittest",
                "tests.unit.test_a",
                "tests.unit.test_b",
            ],
        )
