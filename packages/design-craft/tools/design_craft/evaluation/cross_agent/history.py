from __future__ import annotations

import re
from pathlib import Path

from .contract import OBSERVED_REQUIRED_CRITERIA, read_text


HISTORICAL_REQUIRED_FILES = ("prompt.md", "expected-findings.md", "scorecard.md")
REQUIRED_CRITERIA = {
    "style_authority": ("style authority", "product context"),
    "reference_selection": ("reference",),
    "anti_generic_redesign": ("generic", "redesign"),
    "evidence_level": ("evidence level",),
    "verified_boundary": ("verified", "unverified"),
    "design_moves": ("design moves",),
    "scope_control": ("unrelated", "scope"),
}


def _markdown_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        rows.append(cells)
    return rows


def historical_scorecard_weights(path: Path) -> dict[str, int]:
    rows = _markdown_rows(read_text(path))
    if len(rows) < 2:
        return {}
    header = [cell.lower() for cell in rows[0]]
    if "criterion" not in header or "weight" not in header:
        return {}
    criterion_index = header.index("criterion")
    weight_index = header.index("weight")
    values: dict[str, int] = {}
    for row in rows[1:]:
        if len(row) <= max(criterion_index, weight_index):
            return {}
        match = re.fullmatch(r"([0-9]+)(?:\s*%)?", row[weight_index])
        if not match:
            return {}
        criterion_text = row[criterion_index].lower()
        matches = [
            criterion
            for criterion, terms in REQUIRED_CRITERIA.items()
            if all(term in criterion_text for term in terms)
        ]
        if len(matches) != 1 or matches[0] in values:
            return {}
        values[matches[0]] = int(match.group(1))
    if set(values) != set(OBSERVED_REQUIRED_CRITERIA):
        return {}
    return values


def validate_historical_task_definition(path: Path) -> list[str]:
    errors: list[str] = []
    for name in HISTORICAL_REQUIRED_FILES:
        file_path = path / name
        if not file_path.is_file():
            errors.append(f"{path}: missing historical file {name}")
            continue
        if len(read_text(file_path).strip()) < 80:
            errors.append(f"{file_path}: historical file is unexpectedly sparse")
    return errors
