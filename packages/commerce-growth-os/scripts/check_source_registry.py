#!/usr/bin/env python3
"""Compatibility entrypoint for the currentness source checker."""

from __future__ import annotations

import runpy
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "tooling/evaluation/check_source_registry.py"
runpy.run_path(str(TARGET), run_name="__main__")
