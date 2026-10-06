#!/usr/bin/env python3
"""Reproduce this retrospective case, preserving the prior research receipts."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'skills/money-craft/scripts'))
from financial_rigor import calculate, audit_text


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(payload, manifest):
    prior = ROOT/payload['prior_review']
    old = json.loads(prior.read_text())
    if payload['previous_as_of'] != old['as_of'] or date.fromisoformat(payload['as_of']) <= date.fromisoformat(old['as_of']):
        raise ValueError('follow-up must advance the bound historical cutoff')
    for name, expected in old['artifacts'].items():
        if digest(ROOT/name) != expected:
            raise ValueError('prior artifact changed: '+name)
    for source in manifest['sources']:
        if digest(ROOT/source['path']) != source['sha256']:
            raise ValueError('source hash mismatch')
        if source.get('published_on', payload['previous_as_of']) > payload['as_of']:
            raise ValueError('source disclosure exceeds research cutoff')
    values = dict(payload['values']); receipts = []

    def calc(name, operation, *keys):
        args = [values.get(k,k) for k in keys]
        values[name] = str(calculate(operation,args))
        receipts.append(dict(id=f'C{len(receipts)+1:02}',operation=operation,inputs=args,expected=values[name],tolerance='0.000001'))

    calc('adjusted_op','subtract','op_income','gain_pretax')
    calc('adjusted_net','subtract','net_income','gain_aftertax')
    calc('gain_tax','subtract','gain_pretax','gain_aftertax')
    calc('adjusted_eps_check','subtract','eps','eps_adjustment')
    if calculate('add',[values['adjusted_eps_check']]) != calculate('add',[values['eps_adjusted']]):
        raise ValueError('EPS adjustment bridge does not reconcile')
    for key, prior_key in [('revenue','revenue_prior'),('op_income','op_prior'),('adjusted_op','op_prior'),('net_income','net_prior'),('adjusted_net','net_prior'),('inventory','inventory_prior'),('ocf','ocf_prior')]:
        calc(key+'_delta','subtract',key,prior_key)
        calc(key+'_change','divide',key+'_delta',prior_key)
        calc(key+'_pct','multiply',key+'_change','100')
    for key in ('op_income','adjusted_op'):
        calc(key+'_margin','divide',key,'revenue')
        calc(key+'_margin_pct','multiply',key+'_margin','100')
    calc('prior_margin','divide','op_prior','revenue_prior')
    calc('prior_margin_pct','multiply','prior_margin','100')
    calc('adjusted_margin_change','subtract','adjusted_op_margin','prior_margin')
    calc('adjusted_margin_change_pp','multiply','adjusted_margin_change','100')
    calc('fcf','subtract','ocf','capex')
    calc('fcf_prior','subtract','ocf_prior','capex_prior')
    calc('cash_change','add','ocf','investing','financing')
    calc('cash_end_check','add','cash_start','cash_change')
    if values['cash_end_check'] != values['cash_end']:
        raise ValueError('cash bridge does not reconcile')
    for kind in ('old','new_adjusted','new_gaap'):
        calc(kind+'_sum','add',kind+'_low',kind+'_high')
        calc(kind+'_mid','divide',kind+'_sum','2')
    calc('adjusted_mid_change','subtract','new_adjusted_mid','old_mid')
    calc('low_change','subtract','new_adjusted_low','old_low')
    calc('high_change','subtract','new_adjusted_high','old_high')
    return dict(schema='money-craft.target-q1-replay-result.v1',valid=True,as_of=payload['as_of'],
                prior_review_sha256=digest(prior),values=values,calculations=receipts,
                status='PASS_BOUNDED_RETROSPECTIVE_REVIEW',prediction_score='NOT_APPLICABLE')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    payload=json.loads((CASE/'input.json').read_text())
    result=build(payload,json.loads((CASE/'evidence-manifest.json').read_text()))
    text=(CASE/'report.template.md').read_text()
    for key,value in result['values'].items():
        text=text.replace('{{'+key+'}}',format(calculate('add',[value]),'.4f'))
    if '{{' in text:raise ValueError('unresolved template placeholders')
    text+='\n\n## 计算回执\n\n'+'\n'.join('<!-- money-craft-calc: '+json.dumps(r)+' -->' for r in result['calculations'])+'\n'
    audit=audit_text(text)
    if not audit['valid']:raise ValueError('final text financial audit failed')
    args.output_dir.mkdir(parents=True,exist_ok=False)
    result['input_sha256']=digest(CASE/'input.json')
    result['source_hashes']={s['source_id']:s['sha256'] for s in json.loads((CASE/'evidence-manifest.json').read_text())['sources']}
    for name,data in [('result.json',result),('financial-audit.json',audit)]:
        (args.output_dir/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (args.output_dir/'report.md').write_text(text)
    print(json.dumps(dict(valid=True,calculations=len(result['calculations']),prior_artifacts_unchanged=True)))


if __name__=='__main__':main()
