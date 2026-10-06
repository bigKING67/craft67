"""Offline, source-bound long-only portfolio arithmetic; no optimization or execution."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from itertools import combinations
from pathlib import Path
from urllib.parse import urlsplit

from financial_rigor import calculate, decimal_value

SCHEMA = "money-craft.portfolio-input.v1"
MAX_INPUT = 2 * 1024 * 1024
MAX_SOURCE = 32 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def obj(value, fields, label):
    require(isinstance(value, dict) and set(value) == set(fields.split()), f"invalid fields: {label}")
    return value


def text(value, label):
    require(isinstance(value, str) and 0 < len(value) <= 1024 and value.strip() == value, f"invalid text: {label}")
    return value


def day(value):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "date must be YYYY-MM-DD")
    return date.fromisoformat(value)


def number(value, label, low=None, high=None):
    require(isinstance(value, str) and len(value) <= 128 and re.fullmatch(r"-?\d+(?:\.\d+)?", value), f"decimal string required: {label}")
    require(len(value.replace("-", "").replace(".", "")) <= 34 and ("." not in value or len(value.split(".")[1]) <= 18), f"decimal precision exceeds contract: {label}")
    result = decimal_value(value)
    require(low is None or result >= low, f"below range: {label}")
    require(high is None or result <= high, f"above range: {label}")
    return result


def currency(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Z]{3}", value), "invalid currency")
    return value


def array(value, label, minimum=1, maximum=100):
    require(isinstance(value, list) and minimum <= len(value) <= maximum, f"invalid array: {label}")
    return value


def read_bounded(path, limit):
    require(path.is_file(), "input/evidence must be a regular file")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "input/evidence exceeds byte limit")
    return raw


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def review(payload, root):
    obj(payload, "schema as_of base_currency principal assumption_note max_loss max_issuer_weight sources funds scenarios", "portfolio")
    require(payload["schema"] == SCHEMA, "invalid schema")
    as_of = day(payload["as_of"])
    base_currency = currency(payload["base_currency"])
    principal = number(payload["principal"], "principal", 0)
    require(principal > 0, "principal must be positive")
    text(payload["assumption_note"], "assumption_note")
    max_loss = number(payload["max_loss"], "max_loss", 0, 1)
    max_issuer = number(payload["max_issuer_weight"], "max_issuer_weight", 0, 1)
    sources = {}
    for source in array(payload["sources"], "sources"):
        obj(source, "id fund_id path sha256 url as_of", "source")
        sid = text(source["id"], "source id")
        require(sid not in sources, "duplicate source id")
        text(source["fund_id"], "source fund_id")
        require(day(source["as_of"]) <= as_of, "future source")
        url = urlsplit(text(source["url"], "url"))
        require(url.scheme == "https" and url.hostname and not url.username and not url.password, "source URL must be credential-free HTTPS")
        require(isinstance(source["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", source["sha256"]), "invalid source digest")
        path = root / text(source["path"], "source path")
        raw = read_bounded(path, MAX_SOURCE)
        require(hashlib.sha256(raw).hexdigest() == source["sha256"], "source digest mismatch")
        sources[sid] = source

    def source_for(sid, fund_id):
        require(isinstance(sid, str) and sid in sources, "unknown source reference")
        source = sources[sid]
        require(source["fund_id"] == fund_id, "source fund identity mismatch")
        return source

    funds, identities, snapshot_dates = {}, {}, set()
    for fund in array(payload["funds"], "funds", maximum=50):
        obj(fund, "id quote_currency weight fee holdings", "fund")
        fid = text(fund["id"], "fund id")
        require(re.fullmatch(r"[A-Z0-9][A-Z0-9._:-]{0,127}", fid), "invalid fund identifier")
        require(fid not in funds, "duplicate fund id")
        currency(fund["quote_currency"])
        weight = number(fund["weight"], "fund weight", 0, 1)
        require(weight > 0, "zero weight fund must be omitted")
        fee = obj(fund["fee"], "rate source_id locator", "fee")
        number(fee["rate"], "fee rate", 0, 1)
        source_for(fee["source_id"], fid)
        text(fee["locator"], "fee locator")
        holdings = obj(fund["holdings"], "coverage as_of source_id locator positions", "holdings")
        require(holdings["coverage"] in ("partial", "complete"), "invalid coverage")
        source = source_for(holdings["source_id"], fid)
        require(holdings["as_of"] == source["as_of"], "holdings date differs from source date")
        snapshot_dates.add(holdings["as_of"])
        text(holdings["locator"], "holdings locator")
        positions = {}
        for position in array(holdings["positions"], "positions", minimum=0, maximum=20000):
            obj(position, "security_id issuer_id weight", "position")
            security = text(position["security_id"], "security id")
            issuer = text(position["issuer_id"], "issuer id")
            require(security not in positions, "duplicate security within fund")
            require(security not in identities or identities[security] == issuer, "conflicting security-to-issuer mapping")
            identities[security] = issuer
            number(position["weight"], "holding weight", 0, 1)
            positions[security] = position
        covered = calculate("add", [x["weight"] for x in positions.values()] or ["0"])
        require(covered <= 1, "holdings weights exceed one")
        require(holdings["coverage"] != "complete" or covered == 1, "complete holdings must sum exactly to one")
        funds[fid] = (fund, positions, covered)
    require(len(snapshot_dates) == 1, "mixed holdings dates are not comparable")
    require(calculate("add", [f[0]["weight"] for f in funds.values()]) == 1, "fund weights must sum exactly to one")

    calculations = []

    def calc(operation, inputs):
        inputs = list(map(str, inputs))
        value = calculate(operation, inputs)
        calculations.append({"id": f"C{len(calculations)+1:03d}", "operation": operation, "inputs": inputs, "expected": str(value), "tolerance": "0"})
        return value

    fee = calc("add", [calc("multiply", [f[0]["weight"], f[0]["fee"]["rate"]]) for f in funds.values()])
    annual_fee = calc("multiply", [principal, fee])
    coverage = calc("add", [calc("multiply", [f[0]["weight"], f[2]]) for f in funds.values()])
    complete = all(f[0]["holdings"]["coverage"] == "complete" for f in funds.values())
    contributions = {}
    for fund, positions, _ in funds.values():
        for position in positions.values():
            contributions.setdefault(position["issuer_id"], []).append(calc("multiply", [fund["weight"], position["weight"]]))
    issuers = []
    for issuer, parts in sorted(contributions.items()):
        exposure = calc("add", parts)
        issuers.append({"issuer_id": issuer, "known_weight": str(exposure), "constraint_status": "BREACHED" if exposure > max_issuer else "WITHIN_SNAPSHOT" if complete else "UNVERIFIED"})
    overlaps = []
    for left, right in combinations(funds, 2):
        lf, lp, _ = funds[left]
        rf, rp, _ = funds[right]
        overlap = calc("add", [min(decimal_value(lp[k]["weight"]), decimal_value(rp[k]["weight"])) for k in sorted(lp.keys() & rp.keys())] or ["0"])
        overlaps.append({"funds": [left, right], "security_weight_overlap": str(overlap), "scope": "EXACT_WITHIN_INPUT" if lf["holdings"]["coverage"] == rf["holdings"]["coverage"] == "complete" else "LOWER_BOUND"})
    scenarios, scenario_ids = [], set()
    fx_currencies = {f[0]["quote_currency"] for f in funds.values()} - {base_currency}
    for scenario in array(payload["scenarios"], "scenarios"):
        obj(scenario, "id assumption_note asset_returns fx_returns", "scenario")
        sid = text(scenario["id"], "scenario id")
        require(sid not in scenario_ids, "duplicate scenario id")
        scenario_ids.add(sid)
        text(scenario["assumption_note"], "scenario assumption")
        obj(scenario["asset_returns"], " ".join(funds), "asset_returns")
        obj(scenario["fx_returns"], " ".join(sorted(fx_currencies)), "fx_returns")
        fx = {c: number(v, "FX return", -1) for c, v in scenario["fx_returns"].items()}
        terms = []
        for fid, (fund, _, _) in funds.items():
            asset = number(scenario["asset_returns"][fid], "asset return", -1)
            gross = calc("multiply", [calc("add", [1, asset]), calc("add", [1, fx.get(fund["quote_currency"], 0)])])
            terms.append(calc("multiply", [fund["weight"], gross]))
        terminal = calc("add", terms)
        result = calc("subtract", [terminal, 1])
        scenarios.append({"id": sid, "base_currency_return": str(result), "ending_value": str(calc("multiply", [principal, terminal])), "loss_constraint": "BREACHED" if result < -max_loss else "WITHIN_SCENARIO", "assumption_note": scenario["assumption_note"]})
    return {"schema": "money-craft.portfolio-audit.v1", "valid": True, "as_of": payload["as_of"], "base_currency": base_currency, "holdings_as_of": next(iter(snapshot_dates)), "method": "DETERMINISTIC_INPUT_AUDIT", "weighted_expense_ratio": str(fee), "static_annual_fee": str(annual_fee), "holdings_coverage": str(coverage), "holdings_scope": "COMPLETE_AS_DECLARED" if complete else "PARTIAL", "issuers": issuers, "overlaps": overlaps, "scenarios": scenarios, "calculations": calculations, "input": payload, "source_integrity": "VERIFIED", "claim_support": "UNVERIFIED", "limits": ["Source hashes do not verify extracted figures, coverage or issuer mapping.", "Fees assume constant base-currency AUM; exclude trading, FX and taxes. NAV returns must not have fees deducted again.", "FX return means change in base currency per unit of quote currency; asset shocks are net-value inputs; no rebalancing.", "Scenario compliance is not a probability, maximum drawdown guarantee, optimal allocation or trade instruction."], "automatic_trading": False}


def review_file(path):
    try:
        path = Path(path).expanduser().resolve()
        raw = read_bounded(path, MAX_INPUT)
        payload = json.loads(raw, object_pairs_hook=unique_object)
        result = review(payload, path.parent)
        result["input_sha256"] = hashlib.sha256(raw).hexdigest()
        return result
    except (ValueError, OSError, TypeError, KeyError, RecursionError) as exc:
        return {"schema": "money-craft.portfolio-audit.v1", "valid": False, "error": str(exc), "automatic_trading": False}
