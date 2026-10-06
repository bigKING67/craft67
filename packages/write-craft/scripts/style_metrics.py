#!/usr/bin/env python3
"""Describe defensive phrasing and repeated passages in drafts. Development only.

The numbers locate candidates for editorial reading; they are not a pass/fail
gate. A contrast can be necessary and a repeated phrase can be a precise term.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

CONTRAST_PATTERN = re.compile(
    "不是|不代表|不能证明|不等于|并非|不作为|不要求|不阻塞|不影响|仅用于"
)
HAN = re.compile(r"[一-鿿]")
DEFAULT_WINDOW = 12


def repeated_passages(text: str, window: int = DEFAULT_WINDOW) -> list[str]:
    """Return distinct maximal Han passages (>= `window` chars) that occur twice or more."""
    han = "".join(HAN.findall(text))
    starts = range(len(han) - window + 1)
    counts = Counter(han[i : i + window] for i in starts)
    found: list[str] = []
    i = 0
    while i < len(starts):
        if counts[han[i : i + window]] < 2:
            i += 1
            continue
        end = i
        while end + 1 < len(starts) and counts[han[end + 1 : end + 1 + window]] >= 2:
            end += 1
        passage = han[i : end + window]
        if not any(passage in seen for seen in found):
            found.append(passage)
        i = end + 1
    return found


def style_metrics(text: str, window: int = DEFAULT_WINDOW) -> dict[str, object]:
    han_count = len(HAN.findall(text))
    contrasts = CONTRAST_PATTERN.findall(text)
    repeats = repeated_passages(text, window)
    return {
        "han_characters": han_count,
        "contrast_phrases": len(contrasts),
        "contrast_per_1000_han": round(len(contrasts) * 1000 / han_count, 1) if han_count else 0.0,
        "contrast_breakdown": dict(Counter(contrasts).most_common()),
        "repeated_passages": len(repeats),
        "repeated_examples": repeats[:10],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    args = parser.parse_args()
    if args.window < 4:
        parser.error("--window must be at least 4")
    report = {
        str(path): style_metrics(path.read_text(encoding="utf-8"), args.window)
        for path in args.files
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
