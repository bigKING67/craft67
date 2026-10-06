"""Offline, evidence-bound earnings/model updates shared by the Skill and CLI.

Source files and page locators bind an extraction; they do not prove that the
extraction or an analyst's hypothesis interpretation is correct.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fsutil import sha256_file as digest

import financial_rigor as finance
import research_workflow as workflow

INPUT_SCHEMA = "money-craft.earnings-update-input.v1"
OUTPUT_SCHEMA = "money-craft.earnings-update.v1"
METRICS = ("revenue", "net_income", "operating_cash_flow", "shares")
SCENARIOS = ("bear", "base", "bull")
DRIVERS = ("net_income", "earnings_factor", "pe", "shares", "fx")


class EarningsError(workflow.WorkflowError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EarningsError("invalid_earnings_update", message)


def date(value: Any, label: str) -> dt.date:
    require(isinstance(value, str), f"{label} must be an ISO date")
    result = workflow.parse_date(value, label)
    require(result.isoformat() == value, f"{label} must be YYYY-MM-DD")
    return result


def number(value: Any) -> Decimal:
    # Decimal strings avoid binary-float input loss in persisted model assumptions.
    require(isinstance(value, str), "financial values must be decimal strings")
    return finance.decimal_value(value)


def text_number(value: Decimal) -> str:
    return str(value)  # Preserve Decimal precision; large exponents stay bounded.


def validate_sources(payload: dict[str, Any], base: Path) -> dict[str, dict[str, Any]]:
    sources = payload["sources"]
    require(isinstance(sources, dict) and bool(sources), "sources are required")
    for sid, source in sources.items():
        require(re.fullmatch(r"S\d{2,4}", sid) is not None, "invalid source ID")
        require(source["security_id"] == payload["security_id"], f"{sid}: issuer/security binding differs")
        require(bool(source["title"].strip()), f"{sid}: title required")
        url = urlsplit(source["url"])
        require(url.scheme == "https" and bool(url.hostname) and not url.username and not url.password,
                f"{sid}: public HTTPS source URL required")
        published = date(source["published_on"], f"{sid} publication date")
        require(published <= date(payload["as_of"], "as_of"), f"{sid}: source was published after as_of")
        require(re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) is not None, f"{sid}: invalid source hash")
        path = Path(source["local_path"])
        path = path if path.is_absolute() else base / path
        require(path.is_file() and not path.is_symlink(), f"{sid}: source must be a regular local file")
        require(digest(path) == source["sha256"], f"{sid}: source hash mismatch")
    return sources


def refs(value: Any, sources: dict[str, Any]) -> None:
    require(isinstance(value, list) and bool(value), "source_refs must contain source IDs and locators")
    for ref in value:
        require(ref["source_id"] in sources, "reference is not in verified source files")
        require(isinstance(ref["locator"], str) and bool(ref["locator"].strip()), "page/table locator required")


def validate_period_window(snapshot: dict[str, Any]) -> None:
    start, end = date(snapshot["start"], "period start"), date(snapshot["end"], "period end")
    require(start <= end, "period start follows end")
    require(snapshot["kind"] in {"annual", "quarter", "ytd"}, "invalid period kind")
    days = (end - start).days + 1
    low, high = {"annual": (330, 380), "quarter": (60, 110), "ytd": (1, 380)}[snapshot["kind"]]
    require(low <= days <= high, "period length does not match its declared kind")
    require(bool(snapshot["accounting_basis"].strip()), "accounting basis required")


def period(snapshot: dict[str, Any], currency: str, sources: dict[str, Any]) -> dict[str, Decimal]:
    validate_period_window(snapshot)
    end = date(snapshot["end"], "period end")
    require(snapshot["basis"] in {"reported", "restated"}, "use reported or documented restated values; estimates are not actuals")
    require(set(snapshot["metrics"]) == set(METRICS), "four core metrics are required")
    values = {}
    for metric, item in snapshot["metrics"].items():
        require(item["unit"] == ("shares" if metric == "shares" else currency), f"{metric}: unit/currency mismatch; normalize explicitly")
        refs(item["source_refs"], sources)
        for ref in item["source_refs"]:
            source = sources[ref["source_id"]]
            require(date(source["published_on"], "publication") >= end, "actuals cannot use a source published before period end")
        values[metric] = number(item["value"])
    require(values["shares"] > 0, "shares must be positive")
    return values


def comparable_periods(old: dict[str, Any], new: dict[str, Any]) -> None:
    require(old["kind"] == new["kind"], "annual, quarterly and cumulative periods cannot be mixed")
    require(old["accounting_basis"] == new["accounting_basis"], "accounting bases must be reconciled first")
    a, b = date(old["start"], "previous start"), date(old["end"], "previous end")
    c, d = date(new["start"], "current start"), date(new["end"], "current end")
    require(b < c and (a.month, a.day) == (c.month, c.day) and (b.month, b.day) == (d.month, d.day)
            and c.year == a.year + 1 and d.year == b.year + 1,
            "this update compares adjacent same-fiscal-window years; other calendars need a separately reconciled comparison")


def delta(before: Decimal, after: Decimal) -> dict[str, Any]:
    change = finance.calculate("subtract", [after, before])
    growth = finance.calculate("multiply", [finance.calculate("divide", [change, before]), "100"]) if before > 0 else None
    return {"previous": text_number(before), "current": text_number(after), "change": text_number(change),
            "change_pct": text_number(growth) if growth is not None else None,
            "percentage_basis": "positive_prior_value" if growth is not None else "not_meaningful_for_nonpositive_prior"}


def value_per_share(inputs: dict[str, Decimal]) -> Decimal:
    return finance.calculate("divide", [finance.calculate("multiply", [inputs[k] for k in ("net_income", "earnings_factor", "pe", "fx")]), inputs["shares"]])


def valuation_bridge(model: dict[str, Any], before: dict[str, Decimal], after: dict[str, Decimal], currency: str) -> dict[str, Any]:
    require(re.fullmatch(r"[A-Z]{3}", model["currency"]) is not None, "valuation currency required")
    require(model["method"] == "earnings_multiple", "only an explicit earnings-multiple model is supported")
    require(before["net_income"] > 0 and after["net_income"] > 0, "earnings-multiple model is not valid for losses")
    results = {}
    for side in ("previous", "current"):
        require(set(model[side]) == set(SCENARIOS), "bear/base/bull scenarios are required")
    for scenario in SCENARIOS:
        endpoints = []
        for side, actuals in (("previous", before), ("current", after)):
            assumption = model[side][scenario]
            require(bool(assumption["rationale"].strip()), "each scenario needs an assumption rationale")
            values = {key: number(assumption[key]) for key in ("earnings_factor", "pe", "fx")}
            require(all(v > 0 for v in values.values()), "valuation factors must be positive")
            require(model["currency"] != currency or values["fx"] == 1, "same-currency model must use fx=1")
            values.update(net_income=actuals["net_income"], shares=actuals["shares"])
            endpoints.append(values)
        old, new = endpoints
        previous_value, current_value = value_per_share(old), value_per_share(new)
        staged, cursor, bridge = dict(old), previous_value, []
        for driver in DRIVERS:
            staged[driver] = new[driver]
            next_value = value_per_share(staged)
            bridge.append({"driver": driver, "contribution": text_number(finance.calculate("subtract", [next_value, cursor]))})
            cursor = next_value
        total = finance.calculate("subtract", [current_value, previous_value])
        summed = finance.calculate("add", [entry["contribution"] for entry in bridge])
        residual = finance.calculate("subtract", [total, summed])
        require(abs(residual) <= Decimal("1e-20") * max(Decimal(1), abs(total)), "valuation bridge failed to reconcile")
        results[scenario] = {"previous_value_per_share": text_number(previous_value), "current_value_per_share": text_number(current_value),
                             "previous_inputs": {k: text_number(v) for k, v in old.items()},
                             "current_inputs": {k: text_number(v) for k, v in new.items()},
                             "previous_rationale": model["previous"][scenario]["rationale"],
                             "current_rationale": model["current"][scenario]["rationale"],
                             "change": text_number(total), "bridge": bridge, "rounding_residual": text_number(residual)}
    for side in ("previous", "current"):
        values = [Decimal(results[s][side + "_value_per_share"]) for s in SCENARIOS]
        require(values == sorted(values), "bear/base/bull values must be ordered")
    return {"method": "earnings_multiple", "currency": model["currency"], "assumption_status": "HYPOTHESIZED",
            "driver_order": list(DRIVERS), "order_dependent": True, "scenarios": results,
            "limitations": "Illustrative earnings-multiple bridge, not a full DCF or a price target; no net-cash addition to equity earnings."}


def build_update(payload: dict[str, Any], *, base: Path, previous_thesis: Path) -> dict[str, Any]:
    try:
        with localcontext(finance.CONTEXT):
            return _build_update(payload, base=base, previous_thesis=previous_thesis)
    except (KeyError, TypeError, AttributeError, ValueError, ArithmeticError) as exc:
        raise EarningsError("invalid_earnings_update", f"invalid earnings update: {exc}") from exc


def _build_update(payload: dict[str, Any], *, base: Path, previous_thesis: Path) -> dict[str, Any]:
    require(payload["schema"] == INPUT_SCHEMA, "unsupported input schema")
    require(date(payload["as_of"], "as_of") <= dt.datetime.now().astimezone().date(), "future research date")
    require(workflow.SECURITY_ID_RE.fullmatch(payload["security_id"]) is not None, "security_id required")
    require(re.fullmatch(r"[A-Z]{3}", payload["currency"]) is not None, "reporting currency required")
    thesis = workflow.load_thesis(previous_thesis)
    require(thesis["metadata"]["security_id"] == payload["security_id"], "previous thesis security differs")
    require(thesis["metadata"]["base_currency"] == payload["valuation"]["currency"], "valuation/thesis currency differs")
    plan = workflow.prepare_thesis_update(previous_thesis, as_of=payload["as_of"])
    sources = validate_sources(payload, base)
    old, new = payload["previous"], payload["current"]
    before = period(old, payload["currency"], sources)
    after = period(new, payload["currency"], sources)
    for item in old["metrics"].values():
        require(all(date(sources[r["source_id"]]["published_on"], "prior source publication") <= date(thesis["metadata"]["as_of"], "prior thesis date")
                    for r in item["source_refs"]), "prior model cannot use actuals published after the prior thesis")
    comparable_periods(old, new)
    require(date(new["end"], "period end") <= date(payload["as_of"], "as_of"), "period is later than research date")
    comparison = payload["comparison_basis"]
    require(comparison in {"unchanged", "restated", "unverified"}, "comparison basis must be explicit")
    result: dict[str, Any] = {"schema": OUTPUT_SCHEMA, "valid": False, "security_id": payload["security_id"],
        "as_of": payload["as_of"], "currency": payload["currency"], "previous_thesis_sha256": thesis["sha256"],
        "input_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest(),
        "sources": {sid: {k: v for k, v in source.items() if k != "local_path"} for sid, source in sources.items()},
        "evidence_assessment": {"file_integrity": "VERIFIED", "extraction_accuracy": "UNVERIFIED", "claim_support": "UNVERIFIED"},
        "comparison_basis": comparison, "metrics": {}, "expectations": [], "valuation": None, "tracking_handoff": None,
        "automatic_trading": False, "network_used": False, "errors": []}
    if comparison == "unverified":
        result["errors"].append("comparison basis is UNVERIFIED; reconcile before calculating changes or updating thesis")
        return result
    if comparison == "restated":
        comparable = payload["comparable_previous"]
        require(comparable["basis"] == "restated" and all(comparable[k] == old[k] for k in ("start", "end", "kind", "accounting_basis")),
                "restated comparison must describe the same previous period")
        require(bool(payload["restatement_reason"].strip()), "restatement reason required")
        before = period(comparable, payload["currency"], sources)
        result["restatement"] = {"reason": payload["restatement_reason"], "adjustments": {m: delta(number(old["metrics"][m]["value"]), before[m]) for m in METRICS}}
    else:
        require(old["basis"] == new["basis"] == "reported" and "comparable_previous" not in payload,
                "restated data must use the explicit restatement path")
    result["metrics"] = {m: {**delta(before[m], after[m]), "unit": "shares" if m == "shares" else payload["currency"],
                             "previous_source_refs": (payload["comparable_previous"] if comparison == "restated" else old)["metrics"][m]["source_refs"],
                             "current_source_refs": new["metrics"][m]["source_refs"]} for m in METRICS}
    publication = min(date(sources[r["source_id"]]["published_on"], "publication") for item in new["metrics"].values() for r in item["source_refs"])
    if payload.get("expectations"):
        event = payload["first_actual_disclosure"]
        disclosed = date(event["date"], "first actual-result disclosure")
        refs(event["source_refs"], sources)
        require(date(new["end"], "period end") <= disclosed <= publication,
                "first actual disclosure must fall between period end and the cited filing publication")
        require(all(date(sources[r["source_id"]]["published_on"], "disclosure source") <= disclosed for r in event["source_refs"])
                and any(date(sources[r["source_id"]]["published_on"], "disclosure source") == disclosed for r in event["source_refs"]),
                "first disclosure event requires a dated contemporaneous source")
        publication = disclosed
        result["first_actual_disclosure"] = event
    seen = set()
    for expectation in payload.get("expectations", []):
        metric = expectation["metric"]
        require(metric in METRICS and metric not in seen, "expectation metric must be unique and supported")
        seen.add(metric)
        require(expectation["period_start"] == new["start"] and expectation["period_end"] == new["end"]
                and expectation["kind"] == new["kind"] and expectation["accounting_basis"] == new["accounting_basis"],
                "expectation fiscal window, period kind or accounting basis differs")
        require(expectation["unit"] == new["metrics"][metric]["unit"], "expectation unit differs")
        observed_on = date(expectation["as_of"], "expectation as_of")
        require(observed_on < publication, "expectation must predate the actual-result disclosure")
        refs(expectation["source_refs"], sources)
        require(all(date(sources[r["source_id"]]["published_on"], "expectation source") <= observed_on for r in expectation["source_refs"]),
                "expectation source was unavailable on expectation date")
        expected = number(expectation["value"])
        result["expectations"].append({"metric": metric, "dated_baseline": expectation, "actual_vs_expected": delta(expected, after[metric]),
                                       "relation": "above" if after[metric] > expected else "below" if after[metric] < expected else "in_line"})
    result["expectation_status"] = "DATED_SOURCE_BOUND" if seen else "UNAVAILABLE_NO_BEAT_OR_MISS_CLAIM"
    # Restatement adjusts the comparison table, not the frozen prior valuation model.
    result["valuation"] = valuation_bridge(payload["valuation"], period(old, payload["currency"], sources), after, payload["currency"])
    updates = payload["thesis_updates"]
    mapped = {}
    for group, records, status_key, allowed in (("hypotheses", thesis["hypotheses"], "状态", workflow.HYPOTHESIS_STATES),
                                               ("red_lines", thesis["red_lines"], "当前状态", workflow.RED_LINE_STATES)):
        expected_ids = {record["ID"] for record in records}
        proposed = updates[group]
        require(isinstance(proposed, dict) and set(proposed) == expected_ids, "thesis proposal must cover every existing ID without adding or dropping claims")
        mapped[group] = {}
        for record in records:
            item = proposed[record["ID"]]
            require(set(item) == {"status", "rationale", "source_refs"}, "proposal contains unsupported or reserved fields")
            require(item["status"] in allowed and bool(item["rationale"].strip()), "proposal status and rationale required")
            refs(item["source_refs"], sources)
            mapped[group][record["ID"]] = {**item, "previous": record[status_key]}
    result["tracking_handoff"] = {"status": "PROPOSED_REQUIRES_REVIEW", "previous_sha256": thesis["sha256"], "as_of": payload["as_of"],
                                  "updates": mapped, "update_plan": plan,
                                  "next_step": "Review proposal; track init with the same previous thesis/as_of, complete thesis/card/state and run track check. Do not overwrite or auto-promote the old thesis."}
    result["valid"] = True
    return result


def review_file(input_path: Path, previous_thesis: Path) -> dict[str, Any]:
    require(input_path.is_file() and not input_path.is_symlink() and input_path.stat().st_size <= 2 * 1024 * 1024,
            "input must be a regular JSON file no larger than 2 MiB")
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise EarningsError("invalid_earnings_update", "cannot parse earnings input") from exc
    return build_update(payload, base=input_path.parent, previous_thesis=previous_thesis)
