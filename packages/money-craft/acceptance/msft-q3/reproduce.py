#!/usr/bin/env python3
"""Reproduce the selected Microsoft cash-capex case; not a general research API."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

CASE = Path(__file__).resolve().parent
ROOT = CASE.parents[1]
sys.path.insert(0, str(ROOT / 'skills/money-craft/scripts'))
from financial_rigor import calculate, audit_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((CASE / 'evidence-manifest.json').read_text())
    payload = json.loads((CASE / 'input.json').read_text())
    for source in manifest['sources']:
        if hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('source hash mismatch')
        if source['published_on'] > payload['as_of']:
            raise ValueError('source exceeds cutoff')
    values = payload['values'].copy()
    receipts = []

    def calc(name, operation, *keys):
        inputs = [values.get(key, key) for key in keys]
        values[name] = str(calculate(operation, inputs))
        receipts.append(dict(id=f'C{len(receipts)+1:02}', operation=operation,
                             inputs=inputs, expected=values[name], tolerance='0.000001'))

    for window in ('q', 'qp', 'y', 'yp'):
        calc(window+'_fcf', 'subtract', window+'_ocf', window+'_capex')
    for metric in ('ocf', 'capex', 'fcf'):
        for now, old in (('q', 'qp'), ('y', 'yp')):
            name = now+'_'+metric
            calc(name+'_delta', 'subtract', name, old+'_'+metric)
            calc(name+'_ratio', 'divide', name+'_delta', old+'_'+metric)
            calc(name+'_pct', 'multiply', name+'_ratio', '100')
    for metric in ('op', 'net', 'gross'):
        for window in ('q', 'qp'):
            calc(window+'_'+metric+'_ratio', 'divide', window+'_'+metric, window+'_rev')
            calc(window+'_'+metric+'_margin', 'multiply', window+'_'+metric+'_ratio', '100')
        calc(metric+'_margin_pp', 'subtract', 'q_'+metric+'_margin', 'qp_'+metric+'_margin')
    for window in ('q', 'y'):
        calc(window+'_cash_end', 'add', window+'_cash_start', window+'_ocf',
             window+'_financing', window+'_investing', window+'_fx')
        if values[window+'_cash_end'] != values['cash_end']:
            raise ValueError('cash bridge mismatch')
    report = (CASE / 'report.template.md').read_text()
    for key, value in values.items():
        report = report.replace('{{'+key+'}}', format(calculate('add', [value]), '.2f'))
    if '{{' in report:
        raise ValueError('unresolved placeholder')
    report += '\n\n' + '\n'.join('<!-- money-craft-calc: '+json.dumps(r)+' -->' for r in receipts)+'\n'
    audit = audit_text(report)
    if not audit['valid']:
        raise ValueError('financial audit failed')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'report.md').write_text(report)
    for name, data in [('financial-audit.json', audit), ('result.json', dict(values=values, calculations=receipts))]:
        (args.output_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(valid=True, calculations=len(receipts))))


if __name__ == '__main__':
    main()
