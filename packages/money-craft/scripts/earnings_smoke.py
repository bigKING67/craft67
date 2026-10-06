#!/usr/bin/env python3
"""Offline synthetic CLI pipeline; accepts a source or installed runtime path."""
import hashlib
import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_smoke(cli):
    with tempfile.TemporaryDirectory(prefix='money-earnings-e2e-') as directory:
        root = Path(directory)
        def write(name, data):
            path = root / name; path.write_text(json.dumps(data)); return path
        def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
        def run(*args, valid=True):
            process = subprocess.run([sys.executable, str(cli), 'earnings', *map(str,args), '--json'], cwd=root,
                                     capture_output=True, text=True, timeout=30)
            result = json.loads(process.stdout)
            if (process.returncode == 0) != valid or (valid and result.get('valid') is not True):
                raise ValueError(f'earnings smoke failed at {args[0]}: {process.stdout} {process.stderr}')
            return result
        evidence = root / 'source.txt'; evidence.write_text('Synthetic historical inputs only; not an issuer filing.')
        refs = [dict(source_id='S01',locator='synthetic table')]
        source = dict(security_id='CN-SH:600519',title='Synthetic fixture',url='https://example.invalid/fixture',published_on='2025-02-01',sha256=digest(evidence),local_path=str(evidence))
        historic = dict(start='2024-01-01',end='2024-06-30',kind='ytd',accounting_basis='synthetic consolidated')
        future = dict(start='2025-01-01',end='2025-06-30',kind='ytd',accounting_basis='synthetic consolidated')
        params = dict(gross_margin='0.6',expense_rate='0.2',tax_rate='0.25',other_pretax='0',minority_profit='0')
        scenarios = {}
        for name,growth in [('bear','-0.1'),('base','0'),('bull','0.1')]:
            scenarios[name] = {k:dict(value=v,rationale='synthetic assumption',confirmation_condition='compare actual',invalidation_condition='actual diverges',next_evidence='synthetic outcome',source_refs=refs) for k,v in {**params,'growth:A':growth}.items()}
        model = dict(schema='money-craft.earnings-drivers-input.v1',security_id=source['security_id'],currency='CNY',as_of='2025-03-01',sources={'S01':source},dimension='product',historical_period=historic,forecast_period=future,
                     segments={'A':dict(revenue='100',dimension='product',source_refs=refs)},historical=dict(revenue='100',net_income='30',source_refs=refs,**params),scenarios=scenarios,sensitivity=[dict(driver='gross_margin',delta='0.01')])
        model_path=write('model-input.json',model); result=run('drivers','--input',model_path)
        if result['scenarios']['base']['net_income'] != '30.000':
            from decimal import Decimal
            if Decimal(result['scenarios']['base']['net_income']) != 30: raise ValueError('wrong driver result')
        model_result=write('model-result.json',result)
        expectations=[dict(metric=m,origin='analyst',rationale='synthetic driver output',value=result['scenarios']['base'][m],unit='CNY',as_of='2025-03-01',period_start=future['start'],period_end=future['end'],kind='ytd',accounting_basis=future['accounting_basis'],source_refs=refs) for m in ('revenue','net_income')]
        preview=dict(schema='money-craft.earnings-preview.v1',security_id=source['security_id'],currency='CNY',as_of='2025-03-01',sources={'S01':source},expectations=expectations,catalysts=[],linked_model_hashes={'model-input.json':digest(model_path),'model-result.json':digest(model_result)})
        preview_path=write('preview.json',preview); sealed=root/'baseline.json'
        run('seal-preview','--input',preview_path,'--output',sealed)
        original=sealed.read_bytes()
        run('inspect-preview','--baseline',sealed)
        actual_file=root/'actual.txt';actual_file.write_text('Synthetic actuals; no market data.')
        actual_source={**source,'published_on':'2025-08-20','local_path':str(actual_file),'sha256':digest(actual_file)}
        actual=dict(**future,basis='reported',metrics={m:dict(value=v,unit='shares' if m=='shares' else 'CNY',source_refs=refs) for m,v in [('revenue','110'),('net_income','33'),('operating_cash_flow','20'),('shares','10')]})
        outcome=write('outcome.json',dict(schema='money-craft.earnings-outcome.v1',security_id=source['security_id'],currency='CNY',as_of='2025-08-31',sources={'S01':actual_source},actual=actual,first_actual_disclosure=dict(date='2025-08-20',source_refs=refs),catalyst_observations={}))
        replay=run('replay-preview','--baseline',sealed,'--input',outcome)
        if replay['timing']!='RECONSTRUCTED_AFTER_DISCLOSURE':raise ValueError('historical exercise falsely labelled a live prediction')
        from decimal import Decimal
        if Decimal(replay['comparisons'][1]['actual_vs_expected']['change'])!=3:raise ValueError('wrong earnings comparison')
        capture = root / 'capture'; capture.mkdir()
        def millis(date): return int(dt.datetime.fromisoformat(date + 'T00:00:00+08:00').timestamp() * 1000)
        raw = dict(code=0,request_id='synthetic-e2e',data=dict(item=[dict(thscode='600519.SH',fiscal_year=2024,fiscal_period='Q2',period='quarterly',currency='CNY',period_end_ms=millis('2024-06-30'),report_date_ms=millis('2024-08-20'),operating_income='100',parent_holder_net_profit='30')]))
        response = capture / 'response.json'; response.write_text(json.dumps(raw))
        (capture / 'capture.json').write_text(json.dumps(dict(schema='money-craft.source-capture.v1',provider='fuyao',operation='financials.income',request_id='synthetic-e2e',fetched_at='2025-08-31T00:00:00Z',response_sha256=digest(response))))
        spec = dict(schema='money-craft.earnings-crosscheck-input.v1',security_id=source['security_id'],as_of='2025-08-31',provider_capture=str(capture),provider_basis='ytd_confirmed_against_filing',checks=[dict(metric=m,year=2024,quarter=2,kind='ytd',unit='CNY',value=v,source_refs=refs) for m,v in [('revenue','100'),('net_income','30')]])
        cross_path = write('crosscheck.json',spec)
        cross = run('crosscheck-preview','--baseline',sealed,'--input',cross_path)
        if cross['numeric_status'] != 'MATCHED': raise ValueError('crosscheck pipeline did not match synthetic inputs')
        spec.pop('provider_capture'); write('crosscheck.json',spec)
        missing = run('crosscheck-preview','--baseline',sealed,'--input',cross_path,valid=False)
        if missing.get('numeric_status') != 'MISSING': raise ValueError('missing capture was not preserved')
        run('seal-preview','--input',preview_path,'--output',sealed,valid=False)
        if original!=sealed.read_bytes():raise ValueError('baseline overwritten')
        model_result.write_text('{}')
        run('inspect-preview','--baseline',sealed,valid=False)
        return {'valid':True,'checks':['driver-cli','linked-preview-seal','baseline-inspect','outcome-replay','numeric-crosscheck','missing-evidence-gate','historical-timing','no-overwrite','linked-tamper-rejection'],'network_used':False}

if __name__=='__main__':
    print(json.dumps(run_smoke(Path(sys.argv[1]).resolve()),indent=2))
