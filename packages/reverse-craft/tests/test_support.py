from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "skills" / "reverse-craft" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from reverse_craft.routing import route  # noqa: E402,F401

