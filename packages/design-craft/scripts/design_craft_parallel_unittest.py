#!/usr/bin/env python3
"""Run isolated unittest cases concurrently with deterministic reporting."""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import io
import os
import subprocess
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class TestResult:
    test_id: str
    returncode: int
    stdout: str
    stderr: str


def iter_test_ids(suite: unittest.TestSuite) -> list[str]:
    test_ids: list[str] = []
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            test_ids.extend(iter_test_ids(test))
        else:
            test_ids.append(test.id())
    return test_ids


def collect_test_ids(targets: list[str]) -> list[str]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    loader = unittest.defaultTestLoader
    test_ids: list[str] = []
    for target in targets:
        test_ids.extend(iter_test_ids(loader.loadTestsFromName(target)))
    return sorted(set(test_ids))


def discover_modules(start_dir: str, pattern: str) -> list[str]:
    directory = (ROOT / start_dir).resolve()
    try:
        directory.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError("discovery directory must be inside the repository") from exc
    if not directory.is_dir():
        raise ValueError(f"discovery directory does not exist: {start_dir}")

    modules: list[str] = []
    for path in sorted(directory.rglob(pattern)):
        relative = path.relative_to(ROOT).with_suffix("")
        if path.is_file() and all(part.isidentifier() for part in relative.parts):
            modules.append(".".join(relative.parts))
    return modules


def collect_isolated_tasks(
    discovery_dirs: list[str], targets: list[str], pattern: str
) -> list[str]:
    tasks: set[str] = set()
    for start_dir in discovery_dirs:
        tasks.update(discover_modules(start_dir, pattern))
    if targets:
        tasks.update(collect_test_ids(targets))
    return sorted(tasks)


def run_test(test_id: str) -> TestResult:
    return run_test_group([test_id])


def run_test_group(test_ids: list[str]) -> TestResult:
    label = ", ".join(test_ids)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", *test_ids],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return TestResult(label, result.returncode, result.stdout, result.stderr)


def run_tests(test_ids: list[str], jobs: int) -> list[TestResult]:
    workers = min(max(1, jobs), len(test_ids))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(run_test, test_ids))


def run_module_test(module: str) -> TestResult:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        suite = unittest.defaultTestLoader.loadTestsFromName(module)
        runner = unittest.TextTestRunner(stream=stderr, verbosity=1)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = runner.run(suite)
    except Exception as exc:  # pragma: no cover - defensive worker boundary
        return TestResult(module, 1, stdout.getvalue(), f"{type(exc).__name__}: {exc}")
    return TestResult(
        module,
        0 if result.wasSuccessful() else 1,
        stdout.getvalue(),
        stderr.getvalue(),
    )


def run_modules(modules: list[str], jobs: int) -> list[TestResult]:
    workers = module_worker_count(modules, jobs)
    environment_value = os.environ.get("PYTHONDONTWRITEBYTECODE")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            return list(executor.map(run_module_test, modules, chunksize=1))
    finally:
        if environment_value is None:
            os.environ.pop("PYTHONDONTWRITEBYTECODE", None)
        else:
            os.environ["PYTHONDONTWRITEBYTECODE"] = environment_value


def module_worker_count(modules: list[str], jobs: int) -> int:
    return min(max(1, jobs), len(modules), os.cpu_count() or 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", help="unittest module, class, or method")
    parser.add_argument("--discover-dir", help="run matching test modules in isolation")
    parser.add_argument(
        "--include-discover-dir",
        action="append",
        default=[],
        help="add a discovery directory to one shared isolated process pool",
    )
    parser.add_argument(
        "--include-target",
        action="append",
        default=[],
        help="add individual tests from a target to the shared isolated process pool",
    )
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")
    composite = bool(args.include_discover_dir or args.include_target)
    if args.discover_dir and args.targets:
        parser.error("targets and --discover-dir are mutually exclusive")
    if composite and (args.discover_dir or args.targets):
        parser.error("include options cannot be combined with positional discovery modes")
    if not composite and not args.discover_dir and not args.targets:
        parser.error("provide targets or --discover-dir")

    try:
        test_ids = collect_isolated_tasks(
            args.include_discover_dir,
            args.include_target,
            args.pattern,
        ) if composite else (
            discover_modules(args.discover_dir, args.pattern)
            if args.discover_dir
            else collect_test_ids(args.targets)
        )
    except ValueError as exc:
        parser.error(str(exc))
    if not test_ids:
        print("no tests found", file=sys.stderr)
        return 2

    if composite or args.discover_dir:
        results = run_modules(test_ids, args.jobs)
        subprocess_count = module_worker_count(test_ids, args.jobs)
    else:
        results = run_tests(test_ids, args.jobs)
        subprocess_count = len(results)
    failures = [result for result in results if result.returncode != 0]
    if failures:
        for result in failures:
            print(f"FAILED: {result.test_id}", file=sys.stderr)
            detail = result.stderr.strip() or result.stdout.strip() or "test failed"
            print(detail, file=sys.stderr)
        return 1

    print(
        f"parallel unittest verified: targets={len(test_ids)}, "
        f"jobs={min(args.jobs, len(test_ids))}, subprocesses={subprocess_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
