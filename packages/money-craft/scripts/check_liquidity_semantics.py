#!/usr/bin/env python3
"""Replay authored liquidity examples; never certify their economic interpretation."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/money-craft/scripts'))
from financial_rigor import audit_text as financial_audit
from report_audit import audit_text as report_audit


def report(case: dict, claim: str) -> str:
    receipt = json.dumps(case['calculation'], ensure_ascii=False)
    return f'''---
schema: money-craft.report.v1
workflow: earnings
security: Synthetic Liquidity Company
security_id: TEST:LIQUIDITY
as_of: 2026-09-21
data_cutoff: 2026-09-21T00:00:00+08:00
base_currency: CNY
provider_status: synthetic-offline
---
# Synthetic interpretation case
## 结论
{claim} [S01]
## 事实与证据
- {case['facts']} [S01]
- S02是同一虚构发行人的口径说明，不是独立双源。[S02]
## 估值与假设
仅核验给定事实和解释，不提供目标价。
<!-- money-craft-calc: {receipt} -->
## 风险与反方证据
检查法人范围、重分类与资金可用性。
## 证伪条件
新披露改变输入及其适用范围时重新核对。
## 来源索引
- [S01] https://example.invalid/synthetic/{case['id']}
- [S02] https://example.invalid/synthetic/{case['id']}/scope
'''


def replay(path: Path) -> dict:
    raw = path.read_bytes()
    cases = json.loads(raw)['cases']
    results = []
    for case in cases:
        for variant in ('supported_claim', 'contradicted_claim'):
            text = report(case, case[variant])
            results.append({
                'case': case['id'], 'variant': variant,
                'authored_manual_label': case['manual_labels'][variant],
                'manual_label_is_runtime_verdict': False,
                'report_sha256': hashlib.sha256(text.encode()).hexdigest(),
                'report_audit': report_audit(text),
                'financial_audit': financial_audit(text),
            })
    return {
        'schema': 'money-craft.liquidity-semantic-replay.v1',
        'fixture_sha256': hashlib.sha256(raw).hexdigest(),
        'scope': 'authored-pair audit observations only',
        'host_skill_evaluated': False, 'independent_semantic_review': False,
        'results': results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=ROOT / 'acceptance/liquidity-semantics/cases.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    # A rejected incorrect interpretation is an observation, never a suite failure.
    supported = [r for r in result['results'] if r['variant'] == 'supported_claim']
    return 0 if all(r['report_audit']['valid'] and r['financial_audit']['valid'] for r in supported) else 1


if __name__ == '__main__':
    raise SystemExit(main())
