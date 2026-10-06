#!/usr/bin/env python3
"""Compatibility entrypoint for unit-economics regression tests."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "skills/commerce/commerce-commercial-strategy/scripts/test_unit_economics.py"
sys.path.insert(0, str(TARGET.parent))
runpy.run_path(str(TARGET), run_name="__main__")
