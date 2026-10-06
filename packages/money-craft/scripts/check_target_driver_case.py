#!/usr/bin/env python3
"""Recompute Target's historical profit bridge and implied margin hurdles.

Bounded research-case runner. No forecast certification or new runtime API.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/money-craft/scripts'))
from financial_rigor import calculate, audit_text


def run(case, manifest):
    for event in case['events']:
        if date.fromisoformat(event['event_date']) > date.fromisoformat(case['as_of']):
            raise ValueError('future event cannot inform historical model: '+event['id'])
    bound = {}
    for source in manifest['sources']:
        digest = hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()
        if digest != source['sha256']:
            raise ValueError('source hash mismatch: '+source['source_id'])
        bound[source['source_id']] = digest
    if any(e['source_id'] not in bound for e in case['events']):
        raise ValueError('event source missing')
    receipts = []

    def calc(op, *args):
        args = list(map(str, args))
        value = calculate(op, args)
        receipts.append(dict(id=f'C{len(receipts)+1:02}', operation=op, inputs=args,
                             expected=str(value), tolerance='0.000001'))
        return value

    h = case['historical']; a = case['assumptions']
    nonop = calc('subtract', h['other_income'], h['net_interest'])
    pretax = calc('add', h['operating_income'], nonop)
    net = calc('subtract', pretax, h['income_tax'])
    if str(pretax) != h['pretax'] or str(net) != h['net_income']:
        raise ValueError('historical earnings fail reconciliation')
    old_margin = calc('divide', h['operating_income'], h['revenue'])
    old_margin_pct = calc('multiply', old_margin, '100')
    revenue = calc('multiply', h['revenue'], calc('add', '1', a['revenue_growth']))
    hurdles = []
    for eps in a['eps_hurdles']:
        for tax in a['tax_rates']:
            retain = calc('subtract', '1', tax)
            required_net = calc('multiply', eps, h['weighted_diluted_shares'])
            required_pretax = calc('divide', required_net, retain)
            required_op = calc('subtract', required_pretax, nonop)
            margin = calc('divide', required_op, revenue)
            margin_pct = calc('multiply', margin, '100')
            delta_bp = calc('multiply', calc('subtract', margin, old_margin), '10000')
            # Round trip checks the inverse against the forward profit equation.
            back = calc('divide', calc('multiply', calc('add', calc('multiply', revenue, margin), nonop), retain), h['weighted_diluted_shares'])
            if abs(back - calculate('add', [eps])) > calculate('add', ['1e-25']):
                raise ValueError('inverse/forward EPS mismatch')
            hurdles.append(dict(eps=eps, tax=tax, revenue=str(revenue), operating_income=str(required_op),
                                margin_pct=str(margin_pct), change_bp=str(delta_bp), recovered_eps=str(back)))
    # Unit sensitivities, not predicted shocks or probabilities.
    retain_mid = calc('subtract', '1', '0.235')
    op_100bp = calc('multiply', revenue, '0.01')
    eps_100bp = calc('divide', calc('multiply', op_100bp, retain_mid), h['weighted_diluted_shares'])
    historical_tax = calc('divide', h['income_tax'], h['pretax'])
    no_improvement_op = calc('multiply', revenue, old_margin)
    no_improvement_eps = calc('divide', calc('multiply', calc('add', no_improvement_op, nonop), retain_mid), h['weighted_diluted_shares'])
    return dict(schema='money-craft.target-driver-hurdle-result.v1', valid=True,
                status='CONDITIONAL_HURDLES_NOT_NORMALIZED_FORECAST', source_hashes=bound,
                historical=dict(nonoperating=str(nonop), pretax=str(pretax), net_income=str(net), margin_pct=str(old_margin_pct), tax_rate=str(historical_tax)),
                forecast_revenue=str(revenue), hurdles=hurdles,
                eps_change_per_100bp_margin=str(eps_100bp), operating_change_per_100bp=str(op_100bp),
                eps_at_unchanged_margin=str(no_improvement_eps), calculations=receipts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', type=Path, default=ROOT/'acceptance/target-drivers')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads((args.case_dir/'input.json').read_text())
    manifest = json.loads((args.case_dir/'evidence-manifest.json').read_text())
    result = run(payload, manifest)
    rows = ['| EPS 条件 | 税率 | 所需营业利润率 | 较 FY2024 变化（bp） |', '|---:|---:|---:|---:|']
    for row in result['hurdles']:
        rows.append(f"| {row['eps']} | {float(row['tax'])*100:.1f}% | {float(row['margin_pct']):.4f}% | {float(row['change_bp']):.2f} |")
    text = (args.case_dir/'report.template.md').read_text().replace('{{hurdles}}', '\n'.join(rows))
    for key in ('forecast_revenue','eps_change_per_100bp_margin','operating_change_per_100bp','eps_at_unchanged_margin'):
        text = text.replace('{{'+key+'}}', format(calculate('add', [result[key]]), '.4f'))
    text += '\n\n## 计算回执\n\n'+'\n'.join('<!-- money-craft-calc: '+json.dumps(r)+' -->' for r in result['calculations'])+'\n'
    if '{{' in text:
        raise ValueError('unresolved template placeholder')
    audit = audit_text(text)
    if not audit['valid']:
        raise ValueError('final report arithmetic audit failed')
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=False)
    result['input_sha256'] = hashlib.sha256((args.case_dir/'input.json').read_bytes()).hexdigest()
    (out/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    (out/'report.md').write_text(text)
    (out/'financial-audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps(dict(valid=True, sources=len(result['source_hashes']), calculations=len(result['calculations']), reverse_forward_checks=len(result['hurdles']))))


if __name__ == '__main__':
    main()
