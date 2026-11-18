#!/usr/bin/env python3
"""Compute per-prototype evidence levels from the ledger and reject level drift.

Levels follow references/story-patterns.md:

  A  own ad data: at least three single-variable rounds, each with >=3 samples
  B  at least five same-structure samples recorded, but no own ad data
  C  sampled classification only, sample counts not recorded per prototype

`--check` recomputes the levels, compares them with evals/levels.json, and keeps
README from claiming a level the ledger cannot support.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'evals' / 'ledger.json'
LEVELS = ROOT / 'evals' / 'levels.json'
README = ROOT / 'README.md'

PROTOTYPES = [f'P{number}' for number in range(1, 12)]
ORDER = {'C': 0, 'B': 1, 'A': 2}
MIN_ROUNDS = 3
MIN_SAMPLES_PER_ROUND = 3
MIN_LIBRARY_SAMPLES = 5
REVIEW_DAYS = 90
ACCEPTED_ATTRIBUTION = {'hypothesis_rejected', 'hypothesis_supported', 'execution_failed'}
CONCLUSIONS = {'keep', 'drop', 'more'}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def compute(ledger: dict, as_of: dt.date) -> dict[str, str]:
    rounds: dict[str, list[dict]] = {}
    for entry in ledger.get('rounds', []):
        rounds.setdefault(entry.get('prototype', ''), []).append(entry)
    library = {entry.get('prototype'): entry for entry in ledger.get('library', [])}

    levels: dict[str, str] = {}
    for prototype in PROTOTYPES:
        own = rounds.get(prototype, [])
        strong = [
            entry for entry in own
            if int(entry.get('samples', 0)) >= MIN_SAMPLES_PER_ROUND
            and entry.get('attribution') in ACCEPTED_ATTRIBUTION
            and entry.get('conclusion') in CONCLUSIONS
            and isinstance(entry.get('metrics'), dict) and entry['metrics']
        ]
        if len(strong) >= MIN_ROUNDS:
            levels[prototype] = 'A'
            continue
        record = library.get(prototype)
        if record:
            reviewed = record.get('reviewed')
            fresh = True
            if reviewed:
                fresh = (as_of - dt.date.fromisoformat(reviewed)).days <= REVIEW_DAYS
            if int(record.get('samples', 0)) >= MIN_LIBRARY_SAMPLES and fresh:
                levels[prototype] = 'B'
                continue
        levels[prototype] = 'C'
    return levels


def check(ledger: dict, declared: dict, readme: str, as_of: dt.date) -> list[str]:
    errors: list[str] = []
    computed = compute(ledger, as_of)
    declared_levels = declared.get('levels', {})

    missing = [prototype for prototype in PROTOTYPES if prototype not in declared_levels]
    extra = [prototype for prototype in declared_levels if prototype not in PROTOTYPES]
    if missing:
        errors.append(f'evals/levels.json is missing prototypes: {missing}')
    if extra:
        errors.append(f'evals/levels.json declares unknown prototypes: {extra}')

    for prototype, level in computed.items():
        stated = declared_levels.get(prototype)
        if stated not in ORDER:
            continue
        if ORDER[level] > ORDER[stated]:
            errors.append(f'{prototype}: ledger supports {level} but levels.json declares {stated}; upgrade levels.json and README')
        elif ORDER[level] < ORDER[stated]:
            errors.append(f'{prototype}: levels.json declares {stated} but the ledger only supports {level}')

    all_c = all(level == 'C' for level in declared_levels.values()) if declared_levels else False
    if all_c and '均为 C 级' not in readme:
        errors.append('README.md must state that every prototype is 均为 C 级 while levels.json is all C')
    if not all_c and '均为 C 级' in readme:
        errors.append('README.md still claims 均为 C 级 while levels.json declares a stronger level')

    for entry in ledger.get('rounds', []):
        prototype = entry.get('prototype')
        if prototype not in PROTOTYPES:
            errors.append(f'ledger round {entry.get("round")!r} uses unknown prototype {prototype!r}')
        if entry.get('attribution') and entry['attribution'] not in ACCEPTED_ATTRIBUTION:
            errors.append(f'ledger round {entry.get("round")!r} has unknown attribution {entry["attribution"]!r}')
        if entry.get('conclusion') and entry['conclusion'] not in CONCLUSIONS:
            errors.append(f'ledger round {entry.get("round")!r} has unknown conclusion {entry["conclusion"]!r}')
        if int(entry.get('samples', 0)) < 1:
            errors.append(f'ledger round {entry.get("round")!r} records no samples')
        if not entry.get('variable'):
            errors.append(f'ledger round {entry.get("round")!r} does not name the single variable under test')
    for entry in ledger.get('library', []):
        if entry.get('prototype') not in PROTOTYPES:
            errors.append(f'library entry uses unknown prototype {entry.get("prototype")!r}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='reject drift between the ledger, levels and README')
    parser.add_argument('--as-of', help='date used for the review window, default today')
    args = parser.parse_args()

    as_of = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
    ledger = load(LEDGER)
    declared = load(LEVELS)
    computed = compute(ledger, as_of)
    errors = check(ledger, declared, README.read_text(encoding='utf-8'), as_of) if args.check else []
    report = {
        'ok': not errors,
        'as_of': as_of.isoformat(),
        'rounds': len(ledger.get('rounds', [])),
        'library_entries': len(ledger.get('library', [])),
        'declared': declared.get('levels', {}),
        'computed': computed,
        'errors': errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
