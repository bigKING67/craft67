from __future__ import annotations

import statistics
import time
from collections.abc import Callable, Sequence


# Summaries are calculated before samples are serialized to three decimals.
SUMMARY_TOLERANCE_MS = 0.001001


def percentile(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * quantile)))
    return ordered[index]


def summarize_samples(values: Sequence[float]) -> dict[str, float]:
    if not values:
        raise ValueError("benchmark samples must not be empty")
    return {
        "p50": round(statistics.median(values), 3),
        "p95": round(percentile(values, 0.95), 3),
        "max": round(max(values), 3),
    }


def measure(function: Callable[[], object], iterations: int) -> dict[str, object]:
    if iterations <= 0:
        raise ValueError("benchmark iterations must be positive")
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        function()
        samples.append((time.perf_counter() - started) * 1_000)
    return {
        "unit": "ms",
        "iterations": iterations,
        **summarize_samples(samples),
        "samples": [round(value, 3) for value in samples],
    }
