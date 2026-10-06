#!/usr/bin/env python3
"""Measure the portable runtime's JSON Schema uniqueItems scaling."""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills" / "creative-craft" / "scripts" / "creative_craft.py"
SPEC = importlib.util.spec_from_file_location("creative_craft_benchmark", RUNTIME)
assert SPEC and SPEC.loader
cc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cc
SPEC.loader.exec_module(cc)


def measure(size: int, runs: int) -> list[float]:
    values = [f"unique-item-{index}" for index in range(size)]
    schema = {"type": "array", "uniqueItems": True}

    def once() -> float:
        result = cc.Result()
        started = time.perf_counter()
        cc._validate_schema_node(values, schema, schema, (), result)
        duration_ms = (time.perf_counter() - started) * 1000
        if not result.ok:
            raise RuntimeError("benchmark fixture unexpectedly failed validation")
        return duration_ms

    for _ in range(3):
        once()
    return [once() for _ in range(runs)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--small", type=int, default=1600)
    parser.add_argument("--large", type=int, default=3200)
    parser.add_argument("--runs", type=int, default=21)
    parser.add_argument("--max-ratio", type=float, default=2.5)
    args = parser.parse_args(argv)
    if args.small <= 0 or args.large <= args.small or args.runs < 3:
        parser.error("require 0 < small < large and runs >= 3")

    small_samples = measure(args.small, args.runs)
    large_samples = measure(args.large, args.runs)
    small_median = statistics.median(small_samples)
    large_median = statistics.median(large_samples)
    ratio = large_median / small_median
    passed = ratio <= args.max_ratio
    print(
        json.dumps(
            {
                "schema_version": "creative-craft.unique-items-benchmark.v1",
                "small": {"items": args.small, "median_ms": small_median},
                "large": {"items": args.large, "median_ms": large_median},
                "ratio": ratio,
                "max_ratio": args.max_ratio,
                "runs": args.runs,
                "passed": passed,
            },
            sort_keys=True,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
