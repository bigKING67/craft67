"""Evidence-bound revenue/profit scenarios with one-at-a-time sensitivity."""
from __future__ import annotations
import copy
from decimal import Decimal, localcontext
from pathlib import Path
import earnings_baseline as baseline
import earnings_update as eu

RATES = ('gross_margin', 'expense_rate', 'tax_rate')
PROFIT = (*RATES, 'other_pretax', 'minority_profit')


class AttributionUnavailable(Exception):
    pass


def compute(drivers, segments, *, intermediate=False):
    revenues = {sid: eu.number(segment['revenue']) * (1 + drivers['growth:' + sid]) for sid, segment in segments.items()}
    eu.require(all(v >= 0 for v in revenues.values()), 'negative segment revenue')
    eu.require(all(0 <= drivers[k] <= 1 for k in RATES), 'rates must be between zero and one')
    revenue = sum(revenues.values(), Decimal(0))
    gross = revenue * drivers['gross_margin']
    expenses = revenue * drivers['expense_rate']
    pretax = gross - expenses + drivers['other_pretax']
    if intermediate and pretax < 0:
        raise AttributionUnavailable('fixed attribution order crosses an unsupported loss-making intermediate state')
    eu.require(pretax >= 0, 'loss-making cases need a separately specified tax model')
    tax = pretax * drivers['tax_rate']
    return {'segment_revenue': {k: str(v) for k, v in revenues.items()}, 'revenue': str(revenue),
            'gross_profit': str(gross), 'expenses': str(expenses), 'other_pretax': str(drivers['other_pretax']),
            'pretax_profit': str(pretax), 'income_tax': str(tax), 'minority_profit': str(drivers['minority_profit']),
            'net_income': str(pretax - tax - drivers['minority_profit'])}


def review_file(path: Path):
    try:
        with localcontext(eu.finance.CONTEXT):
            return build(baseline.read(path), path.parent)
    except (KeyError, TypeError, AttributeError, ValueError, OSError, ArithmeticError) as exc:
        raise eu.EarningsError('invalid_driver_model', str(exc)) from exc


def build(payload, base):
    eu.require(payload['schema'] == 'money-craft.earnings-drivers-input.v1', 'unsupported driver schema')
    eu.require(eu.workflow.SECURITY_ID_RE.fullmatch(payload['security_id']) is not None, 'security required')
    eu.require(eu.re.fullmatch(r'[A-Z]{3}', payload['currency']) is not None, 'currency required')
    sources = eu.validate_sources(payload, base)
    eu.require(eu.date(payload['as_of'], 'as_of') <= baseline.calendar_today(), 'future research date')
    old, new = payload['historical_period'], payload['forecast_period']
    eu.validate_period_window(old)
    eu.validate_period_window(new)
    eu.comparable_periods(old, new)
    eu.require(eu.date(old['end'], 'historical end') <= eu.date(payload['as_of'], 'as_of'), 'historical period not completed')
    eu.require(payload['dimension'] in {'product', 'channel', 'consolidated'}, 'choose a single primary revenue dimension')
    segments = payload['segments']
    eu.require(isinstance(segments, dict) and bool(segments), 'revenue segments required')
    for sid, segment in segments.items():
        eu.require(isinstance(sid, str) and sid.strip() and ':' not in sid, 'invalid segment ID')
        eu.require(segment['dimension'] == payload['dimension'], 'cannot add different revenue dimensions')
        eu.require(eu.number(segment['revenue']) >= 0, 'historical revenue must be nonnegative')
        eu.refs(segment['source_refs'], sources)
        eu.require(all(sources[r['source_id']]['published_on'] >= old['end'] for r in segment['source_refs']), 'historical segment source predates period')
    historical = payload['historical']
    eu.refs(historical['source_refs'], sources)
    eu.require(all(sources[r['source_id']]['published_on'] >= old['end'] for r in historical['source_refs']), 'historical profit source predates period')
    keys = ['growth:' + sid for sid in sorted(segments)] + list(PROFIT)
    historic_drivers = {'growth:' + sid: Decimal(0) for sid in segments}
    historic_drivers.update({k: eu.number(historical[k]) for k in PROFIT})
    historical_result = compute(historic_drivers, segments)
    for metric in ('revenue', 'net_income'):
        eu.require(abs(eu.number(historical_result[metric]) - eu.number(historical[metric])) <= Decimal('0.01'), 'historical ' + metric + ' does not reconcile within 0.01 currency units')
    eu.require(set(payload['scenarios']) == set(eu.SCENARIOS), 'bear/base/bull required')
    scenarios, parsed = {}, {}
    for name, scenario in payload['scenarios'].items():
        eu.require(set(scenario) == set(keys), 'scenario must cover exactly all drivers')
        values = {}
        for key, item in scenario.items():
            values[key] = eu.number(item['value'])
            for text in ('rationale', 'confirmation_condition', 'invalidation_condition', 'next_evidence'):
                eu.require(isinstance(item[text], str) and item[text].strip(), key + ': ' + text + ' required')
            eu.refs(item['source_refs'], sources)
        parsed[name] = values
        scenarios[name] = compute(values, segments)
    for metric in ('revenue', 'net_income'):
        ordered = [eu.number(scenarios[s][metric]) for s in eu.SCENARIOS]
        eu.require(ordered == sorted(ordered), 'bear/base/bull ' + metric + ' is not ordered')
    sensitivity = []
    seen = set()
    for shock in payload['sensitivity']:
        key, change = shock['driver'], eu.number(shock['delta'])
        eu.require(key in keys and key not in seen and change != 0, 'unique nonzero sensitivity shock required')
        seen.add(key)
        values = dict(parsed['base']); values[key] += change
        shocked = compute(values, segments)
        sensitivity.append({'driver': key, 'delta': str(change), 'delta_semantics': 'additive ratio points for growth/rates; currency units otherwise',
                            'revenue_change': str(eu.number(shocked['revenue']) - eu.number(scenarios['base']['revenue'])),
                            'net_income_change': str(eu.number(shocked['net_income']) - eu.number(scenarios['base']['net_income']))})
    result = {'schema': 'money-craft.earnings-drivers.v1', 'valid': True, 'security_id': payload['security_id'], 'as_of': payload['as_of'],
        'input_sha256': eu.hashlib.sha256(baseline.encoded(payload)).hexdigest(), 'dimension': payload['dimension'], 'currency': payload['currency'],
        'historical_period': old, 'forecast_period': new, 'historical_reconciliation': historical_result, 'scenarios': scenarios,
        'assumptions': payload['scenarios'], 'sensitivity': sensitivity, 'sensitivity_method': 'one_driver_at_a_time_from_base',
        'source_hashes': {sid: s['sha256'] for sid, s in sources.items()}, 'claim_support': 'UNVERIFIED', 'assumption_status': 'HYPOTHESIZED',
        'actual_review': None, 'automatic_thesis_update': False, 'network_used': False}
    if payload.get('actual') is not None:
        actual = payload['actual']
        eu.require(actual['period'] == new, 'actual fiscal period differs')
        eu.refs(actual['source_refs'], sources)
        eu.require(all(sources[r['source_id']]['published_on'] >= new['end'] for r in actual['source_refs']), 'actual source predates completed period')
        eu.require(set(actual['drivers']) == set(keys), 'actual driver set differs')
        actual_values = {k: eu.number(v) for k, v in actual['drivers'].items()}
        actual_model = compute(actual_values, segments)
        eu.require(abs(eu.number(actual['revenue']) - eu.number(actual_model['revenue'])) <= Decimal('0.01'), 'actual segment revenue does not reconcile')
        cursor = eu.number(scenarios['base']['net_income']); running = dict(parsed['base']); bridge = []
        bridge_status, bridge_reason = 'AVAILABLE', None
        try:
            for key in keys:
                running[key] = actual_values[key]
                value = eu.number(compute(running, segments, intermediate=True)['net_income'])
                bridge.append({'driver': key, 'contribution': str(value - cursor)}); cursor = value
        except AttributionUnavailable as exc:
            bridge, bridge_status, bridge_reason = [], 'UNAVAILABLE', str(exc)
        residual = eu.number(actual['net_income']) - eu.number(actual_model['net_income'])
        result['actual_review'] = {'bridge': bridge, 'bridge_status': bridge_status, 'bridge_reason': bridge_reason, 'actual_model': actual_model, 'driver_order': keys, 'order_dependent': True,
            'unexplained_residual': str(residual), 'residual_status': 'RECONCILED' if abs(residual) <= Decimal('0.01') else 'REQUIRES_RESEARCH',
            'actual_vs_base_net_income': str(eu.number(actual['net_income']) - eu.number(scenarios['base']['net_income'])),
            'limitation': 'Arithmetic attribution conditional on supplied drivers; not causal proof. Restatements require a new explicitly reconciled model version.'}
    return result
