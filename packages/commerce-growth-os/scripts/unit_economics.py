#!/usr/bin/env python3
"""Compatibility entrypoint for commerce-commercial-strategy economics."""

from __future__ import annotations

import runpy
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "skills/commerce/commerce-commercial-strategy/scripts/unit_economics.py"
runpy.run_path(str(TARGET), run_name="__main__")
