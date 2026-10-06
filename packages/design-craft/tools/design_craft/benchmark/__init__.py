"""Reproducible performance benchmarks and regression policy."""

from .contract import compare_results
from .runner import run_suite

__all__ = ["compare_results", "run_suite"]
