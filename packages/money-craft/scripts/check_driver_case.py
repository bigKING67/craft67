#!/usr/bin/env python3
"""Build and separately seal a hypothetical 2027 H1 product-driver case."""
import argparse
import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/money-craft/scripts'))
import earnings_drivers as drivers
import earnings_update as eu
import earnings_baseline as baseline


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--half-year',required=True,type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    expected='0e10aa26be46b1cf3cd03f06e834c7fb98d5dd0d661b96f8fddd4af7e846a4f6'
    eu.require(args.half_year.is_file() and not args.half_year.is_symlink() and eu.digest(args.half_year)==expected,'source hash mismatch')
    refs=[dict(source_id='S01',locator='2026 H1 PDF p.30-31 consolidated income statement; p.74 product disaggregation')]
    source=dict(security_id='CN-SH:600519',title='2026 H1 report',url='https://static.cninfo.com.cn/finalpage/2026-08-15/1225475868.PDF',published_on='2026-08-15',sha256=expected,local_path=str(args.half_year.resolve()))
    with localcontext(eu.finance.CONTEXT):
        revenue=Decimal('90703260964.48');cost=Decimal('9473762565.88')
        expenses=sum(map(Decimal,['3206308341.53','3635355263.82','114926219.60']))
        pretax=Decimal('61438419177.29');tax=Decimal('15405088610.51');minority=Decimal('1516450144.92')
        hist=dict(revenue=str(revenue),net_income='44516880421.86',gross_margin=str((revenue-cost)/revenue),expense_rate=str(expenses/revenue),tax_rate=str(tax/pretax),
                  other_pretax=str(pretax-(revenue-cost-expenses)),minority_profit=str(minority),source_refs=refs)
        segments={sid:dict(dimension='product',revenue=value,source_refs=refs) for sid,value in [('moutai','77724437925.48'),('series','12934186511.82'),('other','44636527.18')]}
        payload=dict(schema='money-craft.earnings-drivers-input.v1',security_id='CN-SH:600519',currency='CNY',as_of='2026-09-15',sources={'S01':source},dimension='product',
            historical_period=dict(start='2026-01-01',end='2026-06-30',kind='ytd',accounting_basis='PRC-GAAP consolidated'),
            forecast_period=dict(start='2027-01-01',end='2027-06-30',kind='ytd',accounting_basis='PRC-GAAP consolidated'),
            segments=segments,historical=hist,scenarios={},sensitivity=[dict(driver='growth:moutai',delta='0.01'),dict(driver='growth:series',delta='0.01'),dict(driver='gross_margin',delta='0.01'),dict(driver='expense_rate',delta='0.01'),dict(driver='tax_rate',delta='0.01')])
        for name,growth,margin_shift in [('bear','-0.05','-0.01'),('base','0','0'),('bull','0.05','0.01')]:
            values={'growth:'+sid:growth for sid in segments};values.update({k:hist[k] for k in drivers.PROFIT});values['gross_margin']=str(Decimal(hist['gross_margin'])+Decimal(margin_shift))
            payload['scenarios'][name]={k:dict(value=v,rationale='HYPOTHESIZED sensitivity envelope, not a validated forecast: product revenue +/-5%, gross margin +/-1pp; other rates and absolute adjustments held at H1. Other pretax is an explicit balancing aggregate of taxes/surcharges, finance subsidiary income/costs, finance expense and other gains/losses; it is not assumed absent.',
                confirmation_condition='Reconcile same-window product revenue and consolidated profit lines with the next official report',
                invalidation_condition='Any product trend, margin, tax or adjustment movement contradicting the held-constant assumption requires model revision',
                next_evidence='Official product revenues, cost mix, tax/surcharge and finance-subsidiary disclosures; independent corroboration',source_refs=refs) for k,v in values.items()}
        output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=False)
        (output/'model-input.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
        result=drivers.review_file(output/'model-input.json')
        (output/'model-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        assumptions=next(iter(payload['scenarios']['base'].values()))
        expectations=[dict(metric=m,origin='analyst',rationale='Hypothetical product-driver base case; see sealed linked model hashes. Not management guidance or consensus.',value=result['scenarios']['base'][m],unit='CNY',as_of=payload['as_of'],period_start='2027-01-01',period_end='2027-06-30',kind='ytd',accounting_basis='PRC-GAAP consolidated',source_refs=refs) for m in ('revenue','net_income')]
        preview=dict(schema='money-craft.earnings-preview.v1',security_id=payload['security_id'],currency='CNY',as_of=payload['as_of'],sources=payload['sources'],expectations=expectations,
            linked_model_hashes={name:eu.digest(output/name) for name in ('model-input.json','model-result.json')},
            catalysts=[dict(id='C01',window_start='2027-07-01',window_end='2027-08-31',impact_path='Product mix and margin affect parent earnings; analyst watch window only',confirmation_condition=assumptions['confirmation_condition'],invalidation_condition=assumptions['invalidation_condition'],next_evidence=assumptions['next_evidence'],decision_condition='Reconcile changed drivers before any thesis update',source_refs=refs)])
        (output/'preview.json').write_text(json.dumps(preview,ensure_ascii=False,indent=2)+'\n')
        receipt=baseline.seal(output/'preview.json',output/'baseline.json')
        receipt.update(model_hashes=preview['linked_model_hashes'],research_readiness='PARTIAL',assumptions='ILLUSTRATIVE_NOT_VALIDATED_FORECAST')
        (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,eu.EarningsError) as exc:
        print(json.dumps(dict(valid=False,error=str(exc))));raise SystemExit(1)
