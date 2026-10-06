#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))

from reverse_craft.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())

