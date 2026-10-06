#!/usr/bin/env python3
"""Reproduce the bounded Target historical case using the shared Decimal core.

This is a case runner, not an automatic extractor or a general valuation API.
Source hashes bind manually reviewed inputs; arithmetic cannot certify economics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/money-craft/scripts'))
from financial_rigor import audit_text, calculate


def build(case: dict) -> tuple[dict, list[dict]]:
    values = {key: row['value'] for key, row in case['values'].items()}
    receipts = []

    def calc(key, operation, *inputs):
        args = [values.get(item, item) for item in inputs]
        result = str(calculate(operation, args))
        receipts.append(dict(id=f'C{len(receipts)+1:02}', operation=operation,
                             inputs=args, expected=result, tolerance='0.000001'))
        values[key] = result
        return result

    calc('market_cap', 'multiply', 'price', 'shares')
    calc('debt', 'add', 'debt_current', 'debt_noncurrent')
    calc('book_net_debt', 'subtract', 'debt', 'cash')
    calc('issuer_net_debt_check', 'subtract', 'debt', 'short_investments')
    if values['issuer_net_debt_check'] != values['issuer_net_debt']:
        raise ValueError('issuer net debt reconciliation failed')
    calc('operating_cash_remainder', 'subtract', 'cash', 'short_investments')
    calc('ev_book', 'add', 'market_cap', 'book_net_debt')
    calc('ev_short_investments_only', 'add', 'market_cap', 'issuer_net_debt')
    calc('ev_operating_lease_included', 'add', 'ev_book', 'operating_lease')
    calc('pe_reported', 'divide', 'price', 'eps')
    calc('pe_forward_low', 'divide', 'price', 'guidance_high')
    calc('pe_forward_high', 'divide', 'price', 'guidance_low')
    calc('wmt_reported_pe', 'divide', 'wmt_price', 'wmt_eps')
    calc('fcf_proxy', 'subtract', 'ocf', 'capex')
    calc('capex_sum', 'add', 'capex_low', 'capex_high')
    calc('capex_mid', 'divide', 'capex_sum', '2')
    for name in ('low', 'mid', 'high'):
        calc('fcf_capex_'+name, 'subtract', 'ocf', 'capex_'+name)
    calc('five_year_eps_sum', 'add', 'eps', 'eps_2023', 'eps_2022', 'eps_2021', 'eps_2020')
    calc('five_year_eps_mean', 'divide', 'five_year_eps_sum', '5')
    calc('eps_reconstructed', 'divide', 'net_income', 'weighted_diluted')
    for scenario in case['scenarios']:
        key = scenario['name']
        calc(key, 'multiply', scenario['eps_key'], scenario['pe_key'])
        calc(key+'_price_difference', 'subtract', key, 'price')
        calc(key+'_relative_price_difference', 'divide', key+'_price_difference', 'price')
    # A two-variable grid exposes that both earnings and multiple drive the range.
    grid = []
    for eps in ('eps_2022', 'eps', 'guidance_high'):
        for pe in ('pe_reported', 'analyst_spot_pe', 'analyst_pe'):
            key = f'grid_{eps}_{pe}'
            grid.append(dict(eps=values[eps], pe=values[pe], value=calc(key, 'multiply', eps, pe)))
    # Demonstrate, do not misrepresent, the limits of arithmetic validation.
    variants = [
        ('double_finance_lease', 'add', ['ev_book', 'finance_lease'], 'REJECT: finance lease already in debt'),
        ('double_short_investment', 'subtract', ['ev_book', 'short_investments'], 'REJECT: cash already includes short investments'),
        ('weighted_shares_market_cap', 'multiply', ['price', 'weighted_diluted'], 'REJECT: period average is not outstanding shares'),
        ('debt_subtracted_from_pe', 'divide', ['book_net_debt', 'shares'], 'REJECT: subtracting this from EPS x PE double-counts capital structure'),
    ]
    semantic = []
    for key, op, args, verdict in variants:
        result = str(calculate(op, [values[a] for a in args]))
        receipt = dict(id='C01', operation=op, inputs=[values[a] for a in args], expected=result, tolerance='0.000001')
        check = audit_text('<!-- money-craft-calc: '+json.dumps(receipt)+' -->')
        semantic.append(dict(variant=key, value=result, arithmetic_pass=check['valid'], manual_verdict=verdict))
    return dict(values=values, sensitivity_grid=grid, negative_semantic_cases=semantic), receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', type=Path, default=ROOT/'acceptance/target-valuation')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    case_dir = args.case_dir.resolve()
    case = json.loads((case_dir/'input.json').read_text())
    manifest = json.loads((case_dir/'evidence-manifest.json').read_text())
    hashes = {}
    for source in manifest['sources']:
        digest = hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()
        if digest != source['sha256']:
            raise ValueError('source hash mismatch: '+source['source_id'])
        hashes[source['source_id']] = digest
    result, receipts = build(case)
    report = (case_dir/'report.template.md').read_text()
    for key, value in result['values'].items():
        report = report.replace('{{'+key+'}}', format(calculate('add', [value]), '.4f'))
    if '{{' in report:
        raise ValueError('unresolved report placeholder')
    report += '\n\n## 计算回执\n\n'+'\n'.join('<!-- money-craft-calc: '+json.dumps(r)+' -->' for r in receipts)+'\n'
    financial = audit_text(report)
    if not financial['valid']:
        raise ValueError('final report financial audit failed')
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out/'report.md').write_text(report)
    result.update(schema='money-craft.target-valuation-result.v1', as_of=case['as_of'],
                  status='PASS_BOUNDED_RECONSTRUCTION', valuation_status='CONDITIONAL_NOT_FAIR_VALUE',
                  source_hashes=hashes, calculations=receipts,
                  input_sha256=hashlib.sha256((case_dir/'input.json').read_bytes()).hexdigest(),
                  template_sha256=hashlib.sha256((case_dir/'report.template.md').read_bytes()).hexdigest())
    (out/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    (out/'financial-audit.json').write_text(json.dumps(financial, indent=2)+'\n')
    print(json.dumps(dict(valid=True, calculations=len(receipts), source_files=len(hashes), output=str(out))))


if __name__ == '__main__':
    main()
