#!/usr/bin/env python3
"""Compatibility facade for the modular Creative Craft portable runtime."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import creative_craft_contracts as contracts
import creative_craft_entrypoint as entrypoint
import creative_craft_evaluation as evaluation
import creative_craft_packs as packs
import creative_craft_project as project
import creative_craft_project_ops as project_ops
import creative_craft_runtime as runtime
import creative_craft_video as video

_MODULES = (contracts, project, evaluation, runtime, packs, project_ops, video, entrypoint)
for _module in _MODULES:
    for _name, _value in vars(_module).items():
        if not _name.startswith("__"):
            globals()[_name] = _value

main = entrypoint.main

if __name__ == "__main__":
    raise SystemExit(main())
