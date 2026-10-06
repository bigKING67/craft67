#!/usr/bin/env python3
"""Deterministic commerce unit-economics calculator for commerce-growth-os."""

from __future__ import annotations

import argparse
import copy
import difflib
import json
import math
import sys
from pathlib import Path
from typing import Any


RATE_KEYS = {
    "gross_margin_rate",
    "product_cost_rate",
    "platform_fee_rate",
    "creator_commission_rate",
    "gift_cost_rate",
    "sample_cost_rate",
    "fulfillment_cost_rate",
    "refund_loss_rate",
    "service_fee_rate",
    "content_cost_rate",
    "refund_rate",
}

NONNEGATIVE_KEYS = {
    "gmv",
    "aov",
    "orders",
    "product_cost",
    "platform_fee",
    "ad_spend",
    "creator_commission",
    "pit_fee",
    "gift_cost",
    "sample_cost",
    "fulfillment_cost",
    "refund_loss",
    "service_fee",
    "content_cost",
    "target_profit",
    "target_unit_profit",
    "gift_cost_per_order",
    "sample_cost_per_order",
    "fulfillment_cost_per_order",
}

ALLOWED_INPUT_KEYS = RATE_KEYS | NONNEGATIVE_KEYS

STRICT_COMMON_REQUIRED_GROUPS = (
    ("platform fee", ("platform_fee", "platform_fee_rate")),
    ("fulfillment cost", ("fulfillment_cost", "fulfillment_cost_rate", "fulfillment_cost_per_order")),
    ("gift cost", ("gift_cost", "gift_cost_rate", "gift_cost_per_order")),
    ("sample cost", ("sample_cost", "sample_cost_rate", "sample_cost_per_order")),
    ("refund loss", ("refund_loss", "refund_loss_rate")),
    ("service fee", ("service_fee", "service_fee_rate")),
    ("content cost", ("content_cost", "content_cost_rate")),
    ("ad spend", ("ad_spend",)),
    ("target profit", ("target_profit", "target_unit_profit")),
)


def has_value(raw_data: dict[str, Any], *keys: str) -> bool:
    return any(key in raw_data and raw_data[key] not in (None, "") for key in keys)


def validate_input_keys(raw_data: dict[str, Any]) -> None:
    invalid_types = [key for key in raw_data if not isinstance(key, str)]
    if invalid_types:
        raise ValueError(f"input keys must be strings, got {invalid_types!r}")
    unknown = sorted(set(raw_data) - ALLOWED_INPUT_KEYS)
    if not unknown:
        return

    rendered: list[str] = []
    for key in unknown:
        suggestion = difflib.get_close_matches(key, ALLOWED_INPUT_KEYS, n=1, cutoff=0.65)
        rendered.append(f"{key} (did you mean {suggestion[0]}?)" if suggestion else key)
    raise ValueError("unknown input key(s): " + ", ".join(rendered))


def parse_number(raw: Any, key: str, warnings: list[str]) -> float:
    parsed_percent_string = False
    if raw is None or raw == "":
        return 0.0
    if isinstance(raw, bool):
        raise ValueError(f"{key} must be numeric, got boolean")
    if isinstance(raw, (int, float)):
        value = float(raw)
    elif isinstance(raw, str):
        text = raw.strip().replace(",", "")
        if text.endswith("%"):
            if key not in RATE_KEYS:
                raise ValueError(f"{key} does not accept percent values")
            value = float(text[:-1]) / 100.0
            parsed_percent_string = True
            warnings.append(f"{key} parsed as percent string")
        else:
            value = float(text)
    else:
        raise ValueError(f"{key} must be numeric, got {type(raw).__name__}")

    if not math.isfinite(value):
        raise ValueError(f"{key} must be finite")
    if key in RATE_KEYS and not parsed_percent_string and abs(value) > 1 and abs(value) <= 100:
        warnings.append(f"{key} normalized from percent-like value {value} to {value / 100.0}")
        value = value / 100.0
    if key in RATE_KEYS and not 0.0 <= value <= 1.0:
        raise ValueError(f"{key} must be a rate between 0 and 1, or a percent value between 0 and 100")
    if key in NONNEGATIVE_KEYS and value < 0:
        raise ValueError(f"{key} must be non-negative")
    return value


def safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def clean_number(value: float | None) -> float | None:
    if value is None:
        return None
    if math.isclose(value, 0.0, abs_tol=1e-9):
        return 0.0
    return round(value, 6)


def load_input(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_pairs(pairs: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Expected key=value argument, got {pair!r}")
        key, value = pair.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def validate_strict_inputs(raw_data: dict[str, Any], scenario: str) -> None:
    missing: list[str] = []
    if not has_value(raw_data, "gmv") and not (has_value(raw_data, "orders") and has_value(raw_data, "aov")):
        missing.append("gmv, or both orders and aov")
    if not has_value(raw_data, "product_cost", "product_cost_rate", "gross_margin_rate"):
        missing.append("product_cost, product_cost_rate, or gross_margin_rate")
    for label, keys in STRICT_COMMON_REQUIRED_GROUPS:
        if not has_value(raw_data, *keys):
            missing.append(f"{label} ({', '.join(keys)})")

    if scenario == "talent":
        if not has_value(raw_data, "creator_commission", "creator_commission_rate"):
            missing.append("creator_commission or creator_commission_rate for talent scenario")
        if not has_value(raw_data, "pit_fee"):
            missing.append("pit_fee for talent scenario; use pit_fee=0 for pure commission")

    if missing:
        raise ValueError("strict mode missing required inputs: " + "; ".join(missing))


def check_consistency(
    label: str,
    candidates: list[tuple[str, float]],
    warnings: list[str],
    *,
    strict: bool,
) -> None:
    if len(candidates) < 2:
        return
    baseline_name, baseline_value = candidates[0]
    for name, value in candidates[1:]:
        if math.isclose(value, baseline_value, rel_tol=0.01, abs_tol=0.01):
            continue
        message = (
            f"inconsistent {label} representations: "
            f"{baseline_name}={baseline_value:.6g}, {name}={value:.6g}"
        )
        if strict:
            raise ValueError(message)
        warnings.append(message + f"; using {baseline_name}")


def amount(
    data: dict[str, float],
    warnings: list[str],
    *,
    name: str,
    rate_name: str | None = None,
    per_order_name: str | None = None,
    gmv: float,
    orders: float | None,
    warn_if_missing: bool = False,
    strict: bool = False,
) -> float:
    candidates: list[tuple[str, float]] = []
    if name in data:
        candidates.append((name, data[name]))
    if rate_name and rate_name in data:
        candidates.append((rate_name, data[rate_name] * gmv))
    if per_order_name and per_order_name in data:
        if orders:
            candidates.append((per_order_name, data[per_order_name] * orders))
        else:
            message = f"{per_order_name} requires positive orders or enough data to derive orders"
            if strict:
                raise ValueError(message)
            warnings.append(message + "; ignored")
    if candidates:
        check_consistency(name, candidates, warnings, strict=strict)
        return candidates[0][1]
    if warn_if_missing:
        warnings.append(f"{name} missing; assumed 0")
    return 0.0


def calculate(
    raw_data: dict[str, Any],
    *,
    strict: bool = False,
    scenario: str = "general",
    sensitivity: bool = False,
) -> dict[str, Any]:
    if scenario not in {"general", "paid", "talent"}:
        raise ValueError(f"unknown scenario: {scenario}")
    validate_input_keys(raw_data)
    if strict:
        validate_strict_inputs(raw_data, scenario)
    warnings: list[str] = []
    data = {key: parse_number(value, key, warnings) for key, value in raw_data.items()}

    gmv = data.get("gmv", 0.0)
    aov = data.get("aov", 0.0)
    orders = data.get("orders")

    if all(has_value(raw_data, key) for key in ("gmv", "orders", "aov")):
        check_consistency(
            "gmv",
            [("gmv", gmv), ("orders_x_aov", orders * aov)],
            warnings,
            strict=strict,
        )

    if not gmv and orders and aov:
        gmv = orders * aov
        warnings.append("gmv derived from orders x aov")
    if not orders and gmv and aov:
        orders = gmv / aov
        warnings.append("orders derived from gmv / aov")
    if strict and gmv <= 0:
        raise ValueError("strict mode requires positive gmv, or positive orders and aov")
    if not gmv:
        warnings.append("gmv missing or zero; ratio outputs may be null")

    product_cost_candidates: list[tuple[str, float]] = []
    if "product_cost" in data:
        product_cost_candidates.append(("product_cost", data["product_cost"]))
    if "product_cost_rate" in data:
        product_cost_candidates.append(("product_cost_rate", data["product_cost_rate"] * gmv))
    if "gross_margin_rate" in data:
        product_cost_candidates.append(("gross_margin_rate", gmv * (1.0 - data["gross_margin_rate"])))
    if product_cost_candidates:
        check_consistency("product_cost", product_cost_candidates, warnings, strict=strict)
        product_cost = product_cost_candidates[0][1]
        if product_cost_candidates[0][0] == "gross_margin_rate":
            warnings.append("product_cost derived from gross_margin_rate")
    else:
        product_cost = 0.0
        warnings.append("product_cost or gross_margin_rate missing; product_cost assumed 0")

    platform_fee = amount(
        data,
        warnings,
        name="platform_fee",
        rate_name="platform_fee_rate",
        gmv=gmv,
        orders=orders,
        warn_if_missing=True,
        strict=strict,
    )
    ad_spend = data.get("ad_spend", 0.0)
    if "ad_spend" not in data:
        warnings.append("ad_spend missing; assumed 0")

    creator_commission = amount(
        data,
        warnings,
        name="creator_commission",
        rate_name="creator_commission_rate",
        gmv=gmv,
        orders=orders,
        warn_if_missing=False,
        strict=strict,
    )
    pit_fee = data.get("pit_fee", 0.0)
    gift_cost = amount(
        data,
        warnings,
        name="gift_cost",
        rate_name="gift_cost_rate",
        per_order_name="gift_cost_per_order",
        gmv=gmv,
        orders=orders,
        warn_if_missing=True,
        strict=strict,
    )
    sample_cost = amount(
        data,
        warnings,
        name="sample_cost",
        rate_name="sample_cost_rate",
        per_order_name="sample_cost_per_order",
        gmv=gmv,
        orders=orders,
        warn_if_missing=True,
        strict=strict,
    )
    fulfillment_cost = amount(
        data,
        warnings,
        name="fulfillment_cost",
        rate_name="fulfillment_cost_rate",
        per_order_name="fulfillment_cost_per_order",
        gmv=gmv,
        orders=orders,
        warn_if_missing=True,
        strict=strict,
    )
    refund_loss = amount(
        data,
        warnings,
        name="refund_loss",
        rate_name="refund_loss_rate",
        gmv=gmv,
        orders=orders,
        warn_if_missing=True,
        strict=strict,
    )
    if "refund_rate" in data and "refund_loss" not in data and "refund_loss_rate" not in data:
        warnings.append("refund_rate provided without refund_loss/refund_loss_rate; not converted to monetary loss")

    service_fee = amount(
        data,
        warnings,
        name="service_fee",
        rate_name="service_fee_rate",
        gmv=gmv,
        orders=orders,
        warn_if_missing=True,
        strict=strict,
    )
    content_cost = amount(
        data,
        warnings,
        name="content_cost",
        rate_name="content_cost_rate",
        gmv=gmv,
        orders=orders,
        warn_if_missing=True,
        strict=strict,
    )

    target_profit_total = amount(
        data,
        warnings,
        name="target_profit",
        per_order_name="target_unit_profit",
        gmv=gmv,
        orders=orders,
        warn_if_missing=True,
        strict=strict,
    )

    gross_profit = gmv - product_cost
    available_before_ad = (
        gross_profit
        - platform_fee
        - creator_commission
        - pit_fee
        - gift_cost
        - sample_cost
        - fulfillment_cost
        - refund_loss
        - service_fee
        - content_cost
    )
    channel_net_profit = available_before_ad - ad_spend
    comprehensive_margin = safe_div(available_before_ad, gmv)
    break_even_roi = safe_div(1.0, comprehensive_margin) if comprehensive_margin and comprehensive_margin > 0 else None

    allowable_cac = None
    if orders:
        target_unit_profit = safe_div(target_profit_total, orders) or 0.0
        allowable_cac = (available_before_ad / orders) - target_unit_profit
    else:
        warnings.append("orders unavailable; allowable_cac is null")

    max_commission_pool = (
        gmv
        - product_cost
        - platform_fee
        - ad_spend
        - pit_fee
        - gift_cost
        - sample_cost
        - fulfillment_cost
        - refund_loss
        - service_fee
        - content_cost
        - target_profit_total
    )
    max_creator_commission_rate = safe_div(max_commission_pool, gmv)
    first_order_loss = max(0.0, -channel_net_profit)

    result = {
        "inputs": {key: clean_number(value) for key, value in sorted(data.items())},
        "derived": {
            "gmv": clean_number(gmv),
            "orders": clean_number(orders),
            "product_cost": clean_number(product_cost),
            "platform_fee": clean_number(platform_fee),
            "ad_spend": clean_number(ad_spend),
            "creator_commission": clean_number(creator_commission),
            "pit_fee": clean_number(pit_fee),
            "gift_cost": clean_number(gift_cost),
            "sample_cost": clean_number(sample_cost),
            "fulfillment_cost": clean_number(fulfillment_cost),
            "refund_loss": clean_number(refund_loss),
            "service_fee": clean_number(service_fee),
            "content_cost": clean_number(content_cost),
            "target_profit_total": clean_number(target_profit_total),
        },
        "metrics": {
            "gross_profit": clean_number(gross_profit),
            "contribution_profit": clean_number(channel_net_profit),
            "comprehensive_margin": clean_number(comprehensive_margin),
            "allowable_cac": clean_number(allowable_cac),
            "break_even_roi": clean_number(break_even_roi),
            "roi": clean_number(safe_div(gmv, ad_spend)),
            "gross_profit_roi": clean_number(safe_div(gross_profit, ad_spend)),
            "channel_net_profit": clean_number(channel_net_profit),
            "max_creator_commission_rate": clean_number(max_creator_commission_rate),
            "first_order_loss": clean_number(first_order_loss),
            "repurchase_payback_required": {
                "total": clean_number(first_order_loss),
                "per_order": clean_number(safe_div(first_order_loss, orders or 0.0)),
            },
        },
        "warnings": warnings,
    }
    if sensitivity:
        result["sensitivity"] = build_sensitivity(raw_data, strict=strict, scenario=scenario)
    return result


def metric_snapshot(result: dict[str, Any]) -> dict[str, Any]:
    metrics = result["metrics"]
    return {
        "valid": True,
        "warnings": list(result["warnings"]),
        "channel_net_profit": metrics["channel_net_profit"],
        "roi": metrics["roi"],
        "gross_profit_roi": metrics["gross_profit_roi"],
        "break_even_roi": metrics["break_even_roi"],
        "first_order_loss": metrics["first_order_loss"],
        "max_creator_commission_rate": metrics["max_creator_commission_rate"],
    }


def run_variant(
    raw_data: dict[str, Any],
    updates: dict[str, Any],
    *,
    drop: tuple[str, ...] = (),
    strict: bool = False,
    scenario: str = "general",
) -> dict[str, Any]:
    variant = copy.deepcopy(raw_data)
    for key in drop:
        variant.pop(key, None)
    variant.update(updates)
    try:
        return metric_snapshot(calculate(variant, strict=strict, scenario=scenario))
    except ValueError as exc:
        return {"valid": False, "warnings": [], "error": str(exc)}


def build_sensitivity(
    raw_data: dict[str, Any],
    *,
    strict: bool = False,
    scenario: str = "general",
) -> dict[str, Any]:
    warnings: list[str] = []
    parsed = {key: parse_number(value, key, warnings) for key, value in raw_data.items()}
    gmv = parsed.get("gmv", 0.0)
    aov = parsed.get("aov", 0.0)
    orders = parsed.get("orders")
    if not gmv and orders and aov:
        gmv = orders * aov

    scenarios: dict[str, Any] = {}
    if "ad_spend" in parsed:
        ad_spend = parsed["ad_spend"]
        scenarios["ad_spend_plus_50pct"] = run_variant(
            raw_data,
            {"ad_spend": ad_spend * 1.5},
            strict=strict,
            scenario=scenario,
        )
        scenarios["ad_spend_plus_100pct"] = run_variant(
            raw_data,
            {"ad_spend": ad_spend * 2.0},
            strict=strict,
            scenario=scenario,
        )
    if gmv:
        current_refund_rate = parsed.get("refund_loss_rate")
        if current_refund_rate is None:
            current_refund_rate = parsed.get("refund_loss", 0.0) / gmv
        scenarios["refund_loss_rate_plus_3pt"] = run_variant(
            raw_data,
            {"refund_loss_rate": min(current_refund_rate + 0.03, 1.0)},
            drop=("refund_loss",),
            strict=strict,
            scenario=scenario,
        )
        scenarios["refund_loss_rate_plus_5pt"] = run_variant(
            raw_data,
            {"refund_loss_rate": min(current_refund_rate + 0.05, 1.0)},
            drop=("refund_loss",),
            strict=strict,
            scenario=scenario,
        )
        current_commission_rate = parsed.get("creator_commission_rate")
        if current_commission_rate is None:
            current_commission_rate = parsed.get("creator_commission", 0.0) / gmv
        scenarios["creator_commission_rate_plus_5pt"] = run_variant(
            raw_data,
            {"creator_commission_rate": min(current_commission_rate + 0.05, 1.0)},
            drop=("creator_commission",),
            strict=strict,
            scenario=scenario,
        )
        scenarios["gmv_minus_10pct_same_spend"] = run_variant(
            raw_data,
            {"gmv": gmv * 0.9},
            strict=strict,
            scenario=scenario,
        )
        scenarios["gmv_minus_20pct_same_spend"] = run_variant(
            raw_data,
            {"gmv": gmv * 0.8},
            strict=strict,
            scenario=scenario,
        )
    return scenarios


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate commerce unit economics.")
    parser.add_argument("pairs", nargs="*", help="Input values as key=value, e.g. gmv=100000 gross_margin_rate=55")
    parser.add_argument("--input", "-i", help="JSON input file, or '-' for stdin")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--strict", action="store_true", help="Fail when core cost/profit inputs are missing")
    parser.add_argument(
        "--scenario",
        choices=["general", "paid", "talent"],
        default="general",
        help="Tighten strict validation for the decision scenario",
    )
    parser.add_argument("--sensitivity", action="store_true", help="Add common downside sensitivity scenarios")
    args = parser.parse_args()

    try:
        data = load_input(args.input)
        data.update(parse_pairs(args.pairs))
        result = calculate(data, strict=args.strict, scenario=args.scenario, sensitivity=args.sensitivity)
    except Exception as exc:  # noqa: BLE001 - CLI should report clean errors.
        print(f"unit_economics error: {exc}", file=sys.stderr)
        return 2

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
