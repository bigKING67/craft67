#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
import time
import tracemalloc
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import resource
except ImportError:  # pragma: no cover - exercised by the Windows CI matrix.
    resource = None  # type: ignore[assignment]

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_LIB = ROOT / "skills/review-craft/lib"
RUNTIME_SCRIPT = ROOT / "skills/review-craft/scripts/review_craft.py"
SPEC_PATH = ROOT / "benchmarks/specs/runtime.json"
RESULT_SCHEMA = ROOT / "benchmarks/schemas/runtime-result.schema.json"
sys.path.insert(0, str(RUNTIME_LIB))

from review_craft import __version__  # noqa: E402
from review_craft.repository import (  # noqa: E402
    fingerprint_inventory,
    inventory,
    worktree_fingerprint,
)
from review_craft.repository_analysis import (  # noqa: E402
    build_dependency_map,
    build_module_map,
)


class BenchmarkError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _git(*args: str, cwd: Path = ROOT, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def _source() -> dict[str, Any]:
    revision = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    tree = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        check=True,
        capture_output=True,
    )
    tree_rows = []
    for item in tree.stdout.split(b"\0"):
        if not item:
            continue
        relative = item.decode("utf-8", errors="surrogateescape")
        path = ROOT / relative
        if path.is_file() or path.is_symlink():
            content = (
                os.readlink(path).encode("utf-8", errors="surrogateescape")
                if path.is_symlink()
                else path.read_bytes()
            )
            tree_rows.append(
                {
                    "path": relative,
                    "size": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    return {
        "revision": revision.stdout.strip() if revision.returncode == 0 else None,
        "dirty": bool(status.stdout) if status.returncode == 0 else True,
        "dirtyFingerprint": hashlib.sha256(status.stdout.encode("utf-8")).hexdigest(),
        "treeSha256": sha256_json(tree_rows),
        "runnerSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def _write_fixture(path: Path, index: int, target_bytes: int) -> None:
    content = f"VALUE = {index}\n"
    if len(content.encode("utf-8")) < target_bytes:
        remaining = target_bytes - len(content.encode("utf-8"))
        content += "#" + "x" * max(0, remaining - 2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_repository(
    root: Path,
    *,
    file_count: int,
    file_bytes: int,
    modules: int,
    use_git: bool,
) -> Path:
    target = root / "target"
    target.mkdir(parents=True)
    for index in range(file_count):
        module = index % min(modules, file_count)
        relative = Path(f"packages/pkg-{module:03d}/src/module-{index:06d}.py")
        _write_fixture(target / relative, index, file_bytes)
    if use_git:
        _git("init", "-b", "main", cwd=target, check=True)
        _git("config", "user.name", "Review Craft Benchmark", cwd=target, check=True)
        _git(
            "config",
            "user.email",
            "review-craft-benchmark@example.invalid",
            cwd=target,
            check=True,
        )
        _git("add", "--", ".", cwd=target, check=True)
        _git("commit", "-m", "benchmark fixture", cwd=target, check=True)
    return target


def _process_cpu_seconds() -> float:
    values = os.times()
    return values.user + values.system + values.children_user + values.children_system


def _io_blocks() -> tuple[int | None, int | None]:
    if resource is None:
        return None, None
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (
        self_usage.ru_inblock + child_usage.ru_inblock,
        self_usage.ru_oublock + child_usage.ru_oublock,
    )


def _peak_rss_bytes() -> int | None:
    if resource is None:
        return _windows_peak_rss_bytes() if os.name == "nt" else None
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _windows_peak_rss_bytes() -> int | None:
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("page_fault_count", wintypes.DWORD),
            ("peak_working_set_size", ctypes.c_size_t),
            ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t),
            ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
            ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t),
            ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(
            kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        ):
            return None
    except (AttributeError, OSError):
        return None
    return int(counters.peak_working_set_size)


def measure(operation: Callable[[], Any], *, capture_memory: bool) -> dict[str, Any]:
    gc.collect()
    if capture_memory:
        tracemalloc.start()
    before_cpu = _process_cpu_seconds()
    before_input, before_output = _io_blocks()
    started = time.perf_counter()
    operation()
    wall_ms = (time.perf_counter() - started) * 1000
    cpu_ms = (_process_cpu_seconds() - before_cpu) * 1000
    after_input, after_output = _io_blocks()
    peak: int | None = None
    if capture_memory:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return {
        "wallMs": round(wall_ms, 3),
        "cpuMs": round(max(cpu_ms, 0.0), 3),
        "processPeakRssBytes": _peak_rss_bytes(),
        "pythonAllocatedPeakBytes": peak,
        "inputBlocks": (
            max(after_input - before_input, 0)
            if before_input is not None and after_input is not None
            else None
        ),
        "outputBlocks": (
            max(after_output - before_output, 0)
            if before_output is not None and after_output is not None
            else None
        ),
    }


def _percentile(values: list[float | int | None], percentile: float) -> float | int | None:
    present = sorted(value for value in values if value is not None)
    if not present:
        return None
    index = max(0, math.ceil(percentile * len(present)) - 1)
    return present[index]


def summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "p50WallMs": _percentile([sample["wallMs"] for sample in samples], 0.5),
        "p95WallMs": _percentile([sample["wallMs"] for sample in samples], 0.95),
        "p50CpuMs": _percentile([sample["cpuMs"] for sample in samples], 0.5),
        "p95CpuMs": _percentile([sample["cpuMs"] for sample in samples], 0.95),
        "p95PythonAllocatedPeakBytes": _percentile(
            [sample["pythonAllocatedPeakBytes"] for sample in samples], 0.95
        ),
        "p95ProcessPeakRssBytes": _percentile(
            [sample["processPeakRssBytes"] for sample in samples], 0.95
        ),
        "p50InputBlocks": _percentile([sample["inputBlocks"] for sample in samples], 0.5),
        "p95InputBlocks": _percentile([sample["inputBlocks"] for sample in samples], 0.95),
        "p50OutputBlocks": _percentile([sample["outputBlocks"] for sample in samples], 0.5),
        "p95OutputBlocks": _percentile([sample["outputBlocks"] for sample in samples], 0.95),
    }


def _add_throughput(operation: dict[str, Any], file_count: int) -> None:
    values = [
        round(file_count * 1000 / sample["wallMs"], 3)
        for sample in operation["samples"]
        if sample["wallMs"] > 0
    ]
    operation["summary"]["p50FilesPerSecond"] = _percentile(values, 0.5)
    operation["summary"]["p95FilesPerSecond"] = _percentile(values, 0.95)


def benchmark_operation(
    operation: Callable[[], Any],
    *,
    warmups: int,
    repetitions: int,
    capture_memory: bool,
) -> dict[str, Any]:
    for _ in range(warmups):
        operation()
    samples = [measure(operation, capture_memory=capture_memory) for _ in range(repetitions)]
    result = {
        "samples": samples,
        "summary": summarize(samples),
        "memoryScope": ("PYTHON_PROCESS" if capture_memory else "NOT_CAPTURED_FOR_SUBPROCESS"),
    }
    return result


def _runtime_command(*args: str) -> dict[str, Any]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(RUNTIME_SCRIPT), *args],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise BenchmarkError(completed.stderr.strip() or completed.stdout.strip())
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise BenchmarkError(f"runtime returned invalid JSON: {error}") from error


def benchmark_size(
    *,
    file_count: int,
    file_bytes: int,
    modules: int,
    use_git: bool,
    repetitions: int,
    warmups: int,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"review-craft-benchmark-{file_count}-") as directory:
        temporary = Path(directory)
        target = create_repository(
            temporary,
            file_count=file_count,
            file_bytes=file_bytes,
            modules=modules,
            use_git=use_git,
        )
        output_root = temporary / "runs"
        baseline_records, _ = inventory(target)
        validation_run = Path(
            _runtime_command(
                "preflight",
                "--target",
                str(target),
                "--output-root",
                str(output_root),
            )["runDir"]
        )

        operations: dict[str, dict[str, Any]] = {}
        operations["inventory"] = benchmark_operation(
            lambda: inventory(target),
            warmups=warmups,
            repetitions=repetitions,
            capture_memory=True,
        )
        operations["inventoryFingerprint"] = benchmark_operation(
            lambda: fingerprint_inventory(baseline_records),
            warmups=warmups,
            repetitions=repetitions,
            capture_memory=True,
        )
        operations["moduleMap"] = benchmark_operation(
            lambda: build_module_map(baseline_records),
            warmups=warmups,
            repetitions=repetitions,
            capture_memory=True,
        )
        operations["dependencyMap"] = benchmark_operation(
            lambda: build_dependency_map(target, baseline_records),
            warmups=warmups,
            repetitions=repetitions,
            capture_memory=True,
        )
        operations["worktreeFingerprint"] = benchmark_operation(
            lambda: worktree_fingerprint(target),
            warmups=warmups,
            repetitions=repetitions,
            capture_memory=True,
        )
        operations["preflight"] = benchmark_operation(
            lambda: _runtime_command(
                "preflight",
                "--target",
                str(target),
                "--output-root",
                str(output_root),
            ),
            warmups=warmups,
            repetitions=repetitions,
            capture_memory=False,
        )
        operations["draftValidation"] = benchmark_operation(
            lambda: _runtime_command(
                "validate",
                "--run-dir",
                str(validation_run),
                "--allow-draft",
            ),
            warmups=warmups,
            repetitions=repetitions,
            capture_memory=False,
        )
        for operation in operations.values():
            _add_throughput(operation, len(baseline_records))
        return {
            "fileCount": len(baseline_records),
            "totalBytes": sum(record["sizeBytes"] for record in baseline_records),
            "operations": operations,
        }


def _schema_errors(payload: Any) -> list[str]:
    schema = read_json(RESULT_SCHEMA)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    return [
        f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
        for error in errors
    ]


def validate_result(path: Path) -> list[str]:
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        return [str(error)]
    errors = _schema_errors(payload)
    if not isinstance(payload, dict):
        return errors
    expected = sha256_json({key: value for key, value in payload.items() if key != "contentSha256"})
    if payload.get("contentSha256") != expected:
        errors.append("contentSha256 does not match benchmark metadata")
    operations = read_json(SPEC_PATH)["operations"]
    measurements = payload.get("measurements", [])
    if not isinstance(measurements, list):
        return errors
    for measurement in measurements:
        if not isinstance(measurement, dict):
            continue
        if sorted(measurement.get("operations", {})) != sorted(operations):
            errors.append(
                f"{measurement.get('fileCount', 'unknown')} files: operation set is incomplete"
            )
    return errors


def _parse_sizes(value: str) -> list[int]:
    try:
        sizes = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise argparse.ArgumentTypeError("sizes must be comma-separated integers") from error
    if not sizes or any(size < 1 for size in sizes) or len(set(sizes)) != len(sizes):
        raise argparse.ArgumentTypeError("sizes must be unique positive integers")
    return sizes


def command_run(args: argparse.Namespace) -> int:
    spec = read_json(SPEC_PATH)
    sizes = spec["scaleSizes"] if args.full else (args.sizes or spec["defaultSizes"])
    repetitions = args.repetitions or spec["repetitions"]
    warmups = spec["warmups"] if args.warmups is None else args.warmups
    started_at = utc_now()
    measurements = []
    for size in sizes:
        print(f"benchmarking {size} files", file=sys.stderr, flush=True)
        measurements.append(
            benchmark_size(
                file_count=size,
                file_bytes=spec["fileBytes"],
                modules=spec["modules"],
                use_git=not args.no_git,
                repetitions=repetitions,
                warmups=warmups,
            )
        )
    payload = {
        "schema": "review-craft.runtime-benchmark.v1",
        "runtimeVersion": __version__,
        "startedAt": started_at,
        "completedAt": utc_now(),
        "source": _source(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "parameters": {
            "sizes": sizes,
            "repetitions": repetitions,
            "warmups": warmups,
            "fileBytes": spec["fileBytes"],
            "modules": spec["modules"],
            "git": not args.no_git,
        },
        "measurements": measurements,
        "contentSha256": "0" * 64,
    }
    payload["contentSha256"] = sha256_json(
        {key: value for key, value in payload.items() if key != "contentSha256"}
    )
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else Path(tempfile.gettempdir())
        / "review-craft-benchmarks"
        / f"runtime-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    errors = validate_result(output)
    if errors:
        raise BenchmarkError("generated result is invalid: " + "; ".join(errors))
    print(json.dumps({"result": str(output), "measurements": measurements}, sort_keys=True))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.result).expanduser().resolve(strict=True)
    errors = validate_result(path)
    if errors:
        print("review-craft benchmark validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    payload = read_json(path)
    print(
        json.dumps(
            {
                "valid": True,
                "runtimeVersion": payload["runtimeVersion"],
                "sizes": payload["parameters"]["sizes"],
                "contentSha256": payload["contentSha256"],
            },
            sort_keys=True,
        )
    )
    return 0


COMPARISON_METRICS = (("p50WallMs", "LOWER_IS_BETTER"),)


def compare_payloads(
    baseline: dict[str, Any],
    current: dict[str, Any],
    *,
    maximum_regression_percent: float,
) -> dict[str, Any]:
    if baseline["environment"] != current["environment"]:
        raise BenchmarkError("baseline and current benchmark environments differ")
    if baseline["parameters"] != current["parameters"]:
        raise BenchmarkError("baseline and current benchmark parameters differ")
    baseline_sizes = {row["fileCount"]: row for row in baseline["measurements"]}
    current_sizes = {row["fileCount"]: row for row in current["measurements"]}
    if set(baseline_sizes) != set(current_sizes):
        raise BenchmarkError("baseline and current benchmark sizes differ")
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for file_count in sorted(baseline_sizes):
        baseline_operations = baseline_sizes[file_count]["operations"]
        current_operations = current_sizes[file_count]["operations"]
        if set(baseline_operations) != set(current_operations):
            raise BenchmarkError(f"{file_count} files: benchmark operation sets differ")
        for operation in sorted(baseline_operations):
            for metric, direction in COMPARISON_METRICS:
                before = baseline_operations[operation]["summary"].get(metric)
                after = current_operations[operation]["summary"].get(metric)
                if before is None or after is None or before <= 0:
                    continue
                regression = round((after - before) * 100 / before, 3)
                passed = regression <= maximum_regression_percent
                rows.append(
                    {
                        "fileCount": file_count,
                        "operation": operation,
                        "metric": metric,
                        "direction": direction,
                        "baseline": before,
                        "current": after,
                        "regressionPercent": regression,
                        "passed": passed,
                    }
                )
                if not passed:
                    failures.append(f"{file_count}/{operation}/{metric}: {regression}%")
    if not rows:
        raise BenchmarkError("benchmark comparison has no comparable measurements")
    return {
        "schema": "review-craft.runtime-benchmark-comparison.v1",
        "valid": not failures,
        "maximumRegressionPercent": maximum_regression_percent,
        "baselineSha256": baseline["contentSha256"],
        "currentSha256": current["contentSha256"],
        "comparisons": rows,
        "failures": failures,
    }


def command_compare(args: argparse.Namespace) -> int:
    baseline_path = Path(args.baseline).expanduser().resolve(strict=True)
    current_path = Path(args.result).expanduser().resolve(strict=True)
    for label, path in (("baseline", baseline_path), ("current", current_path)):
        errors = validate_result(path)
        if errors:
            raise BenchmarkError(f"{label} result is invalid: " + "; ".join(errors))
    comparison = compare_payloads(
        read_json(baseline_path),
        read_json(current_path),
        maximum_regression_percent=args.max_regression_percent,
    )
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(comparison, sort_keys=True))
    return 0 if comparison["valid"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark Review Craft repository hot paths")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    selection = run.add_mutually_exclusive_group()
    selection.add_argument("--sizes", type=_parse_sizes)
    selection.add_argument("--full", action="store_true")
    run.add_argument("--repetitions", type=int)
    run.add_argument("--warmups", type=int)
    run.add_argument("--no-git", action="store_true")
    run.add_argument("--output")
    run.set_defaults(handler=command_run)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--result", required=True)
    validate.set_defaults(handler=command_validate)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--result", required=True)
    compare.add_argument("--max-regression-percent", type=float, default=20.0)
    compare.add_argument("--output")
    compare.set_defaults(handler=command_compare)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repetitions = getattr(args, "repetitions", None)
        warmups = getattr(args, "warmups", None)
        if repetitions is not None and repetitions < 1:
            raise BenchmarkError("--repetitions must be positive")
        if warmups is not None and warmups < 0:
            raise BenchmarkError("--warmups must not be negative")
        maximum_regression = getattr(args, "max_regression_percent", None)
        if maximum_regression is not None and maximum_regression < 0:
            raise BenchmarkError("--max-regression-percent must not be negative")
        return args.handler(args)
    except (BenchmarkError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"review-craft benchmark: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
