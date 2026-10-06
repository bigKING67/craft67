#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "reverse-craft" / "lib"))

from reverse_craft.routing import route  # noqa: E402


def main() -> int:
    bank = json.loads((ROOT / "tests" / "fixtures" / "route_seeds.json").read_text(encoding="utf-8"))
    failures: list[dict[str, str]] = []
    total = 0
    for expected, hints in bank["routes"].items():
        for hint in hints:
            total += 1
            actual = route(hint)["primary"]["id"]
            if actual != expected:
                failures.append({"hint": hint, "expected": expected, "actual": actual})
    result = {
        "schema": "reverse-craft.route-bank-result.v1",
        "routes": len(bank["routes"]),
        "cases": total,
        "passed": total - len(failures),
        "failed": len(failures),
        "failures": failures[:50],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

