#!/usr/bin/env python3
"""Compatibility entrypoint for the repository evaluation scorer."""

from __future__ import annotations

import runpy
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "tooling/evaluation/score_eval.py"
runpy.run_path(str(TARGET), run_name="__main__")
