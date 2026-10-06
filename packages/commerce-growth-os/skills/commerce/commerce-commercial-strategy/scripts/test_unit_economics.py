#!/usr/bin/env python3
"""Regression tests for the commerce unit-economics calculator."""

from __future__ import annotations

from pathlib import Path

from unit_economics import calculate, parse_number


def assert_close(actual: float | None, expected: float, *, tolerance: float = 0.00001) -> None:
    if actual is None or abs(actual - expected) > tolerance:
        raise AssertionError(f"expected {expected}, got {actual}")


def assert_raises(message: str, func) -> None:
    try:
        func()
    except Exception as exc:  # noqa: BLE001 - small CLI-style regression runner.
        if message not in str(exc):
            raise AssertionError(f"expected error containing {message!r}, got {exc!r}") from exc
        return
    raise AssertionError(f"expected error containing {message!r}")


def strict_inputs(**updates: float) -> dict[str, float]:
    data = {
        "gmv": 100000,
        "orders": 100,
        "product_cost_rate": 40,
        "platform_fee": 0,
        "fulfillment_cost": 0,
        "gift_cost": 0,
        "sample_cost": 0,
        "refund_loss": 0,
        "service_fee": 0,
        "content_cost": 0,
        "ad_spend": 0,
        "target_profit": 0,
    }
    data.update(updates)
    return data


def test_qianchuan_budget_case() -> None:
    result = calculate(
        {
            "gmv": 300000,
            "ad_spend": 150000,
            "gross_margin_rate": 55,
            "gift_cost_rate": 6,
            "fulfillment_cost_rate": 6,
            "refund_loss_rate": 6,
        }
    )
    metrics = result["metrics"]
    assert_close(metrics["roi"], 2.0)
    assert_close(metrics["break_even_roi"], 2.702703)
    assert_close(metrics["channel_net_profit"], -39000.0)


def test_talent_booking_case() -> None:
    result = calculate(
        {
            "gmv": 400000,
            "product_cost_rate": 32,
            "platform_fee_rate": 5,
            "creator_commission_rate": 25,
            "pit_fee": 50000,
            "gift_cost_rate": 8,
            "fulfillment_cost_rate": 4,
            "refund_loss_rate": 7,
            "ad_spend": 0,
            "orders": 2000,
        }
    )
    metrics = result["metrics"]
    assert_close(metrics["channel_net_profit"], 26000.0)
    assert_close(metrics["allowable_cac"], 13.0)
    assert_close(metrics["max_creator_commission_rate"], 0.315)


def test_paid_and_creator_costs_share_one_acquisition_ceiling() -> None:
    result = calculate(
        {
            "gmv": 100000,
            "product_cost_rate": 40,
            "creator_commission_rate": 10,
            "pit_fee": 5000,
            "ad_spend": 10000,
            "orders": 100,
        }
    )
    metrics = result["metrics"]
    assert_close(metrics["break_even_roi"], 2.222222)
    assert_close(metrics["allowable_cac"], 450.0)
    assert_close(metrics["channel_net_profit"], 35000.0)


def test_strict_mode_rejects_missing_inputs() -> None:
    assert_raises(
        "strict mode missing required inputs",
        lambda: calculate({"gmv": 100000, "gross_margin_rate": 50}, strict=True),
    )


def test_strict_mode_requires_explicit_cost_buckets() -> None:
    for key, label in (
        ("sample_cost", "sample cost"),
        ("service_fee", "service fee"),
        ("content_cost", "content cost"),
    ):
        inputs = strict_inputs()
        inputs.pop(key)
        assert_raises(label, lambda inputs=inputs: calculate(inputs, strict=True))

    result = calculate(strict_inputs(), strict=True)
    assert_close(result["metrics"]["channel_net_profit"], 60000.0)


def test_talent_strict_mode_requires_scenario_costs() -> None:
    base = strict_inputs()
    assert_raises(
        "creator_commission",
        lambda: calculate(base, strict=True, scenario="talent"),
    )
    base["creator_commission"] = 0
    assert_raises(
        "pit_fee",
        lambda: calculate(base, strict=True, scenario="talent"),
    )
    base["pit_fee"] = 0
    calculate(base, strict=True, scenario="talent")


def test_unknown_input_key_is_rejected_with_suggestion() -> None:
    assert_raises(
        "did you mean fulfillment_cost",
        lambda: calculate({"gmv": 100000, "fulfilment_cost": 10000}),
    )


def test_conflicting_amount_and_rate_fail_closed_in_strict_mode() -> None:
    inputs = strict_inputs(platform_fee=5000)
    inputs["platform_fee_rate"] = 10
    assert_raises(
        "inconsistent platform_fee representations",
        lambda: calculate(inputs, strict=True),
    )

    result = calculate(inputs)
    if not any("inconsistent platform_fee representations" in warning for warning in result["warnings"]):
        raise AssertionError("non-strict conflict should be observable")
    assert_close(result["derived"]["platform_fee"], 5000.0)


def test_conflicting_gmv_orders_and_aov_fail_closed_in_strict_mode() -> None:
    inputs = strict_inputs(aov=900)
    assert_raises(
        "inconsistent gmv representations",
        lambda: calculate(inputs, strict=True),
    )

    result = calculate(inputs)
    if not any("inconsistent gmv representations" in warning for warning in result["warnings"]):
        raise AssertionError("non-strict GMV conflict should be observable")
    assert_close(result["derived"]["gmv"], 100000.0)

    consistent = calculate(strict_inputs(aov=1000), strict=True)
    assert_close(consistent["metrics"]["allowable_cac"], 600.0)


def test_per_order_cost_requires_order_basis_in_strict_mode() -> None:
    inputs = strict_inputs()
    inputs.pop("orders")
    inputs.pop("fulfillment_cost")
    inputs["fulfillment_cost_per_order"] = 10
    assert_raises(
        "fulfillment_cost_per_order requires positive orders",
        lambda: calculate(inputs, strict=True),
    )


def test_reference_formula_matches_calculator_cost_buckets() -> None:
    reference = (
        Path(__file__).resolve().parents[1] / "references/business-model-and-profit.md"
    ).read_text(encoding="utf-8")
    required_formula_terms = (
        "Available before ad =",
        "creator commission",
        "pit fee",
        "sample cost",
        "refund loss",
        "service fee",
        "content cost",
        "Allowable CAC = available before ad / orders - target unit profit",
    )
    missing = [term for term in required_formula_terms if term not in reference]
    if missing:
        raise AssertionError(f"reference formula is missing calculator terms: {missing}")


def test_invalid_rate_rejected() -> None:
    assert_raises(
        "must be a rate between 0 and 1",
        lambda: calculate({"gmv": 100000, "gross_margin_rate": 150}),
    )


def test_percent_string_validation() -> None:
    result = calculate({"gmv": "100,000", "gross_margin_rate": "55%"})
    assert_close(result["inputs"]["gmv"], 100000.0)
    assert_close(result["inputs"]["gross_margin_rate"], 0.55)
    if "gross_margin_rate parsed as percent string" not in result["warnings"]:
        raise AssertionError("expected percent-string normalization warning")

    for value in ("150%", "-5%", "nan%", "inf%"):
        assert_raises(
            "gross_margin_rate must be",
            lambda value=value: calculate({"gmv": 100000, "gross_margin_rate": value}),
        )


def test_non_rate_percent_and_boolean_rejected() -> None:
    assert_raises(
        "gmv does not accept percent values",
        lambda: calculate({"gmv": "100%", "gross_margin_rate": 55}),
    )
    assert_raises(
        "gmv must be numeric, got boolean",
        lambda: calculate({"gmv": True, "gross_margin_rate": 55}),
    )


def test_numeric_percent_like_rate_is_preserved() -> None:
    warnings: list[str] = []
    assert_close(parse_number(55, "gross_margin_rate", warnings), 0.55)
    if not any("normalized from percent-like value" in warning for warning in warnings):
        raise AssertionError("expected numeric percent-like normalization warning")


def test_sensitivity_output() -> None:
    result = calculate(
        {
            "gmv": 400000,
            "product_cost_rate": 32,
            "platform_fee_rate": 5,
            "creator_commission_rate": 25,
            "pit_fee": 50000,
            "gift_cost_rate": 8,
            "fulfillment_cost_rate": 4,
            "refund_loss_rate": 7,
            "ad_spend": 0,
            "orders": 2000,
        },
        sensitivity=True,
    )
    sensitivity = result["sensitivity"]
    for key in [
        "refund_loss_rate_plus_3pt",
        "refund_loss_rate_plus_5pt",
        "creator_commission_rate_plus_5pt",
        "gmv_minus_10pct_same_spend",
        "gmv_minus_20pct_same_spend",
    ]:
        if key not in sensitivity:
            raise AssertionError(f"missing sensitivity scenario: {key}")
        if sensitivity[key].get("valid") is not True:
            raise AssertionError(f"expected valid non-strict sensitivity scenario: {key}")
        if not isinstance(sensitivity[key].get("warnings"), list):
            raise AssertionError(f"sensitivity scenario must retain warnings: {key}")


def test_sensitivity_propagates_strict_mode_and_scenario() -> None:
    inputs = strict_inputs(
        aov=1000,
        creator_commission=0,
        pit_fee=0,
        product_cost=40000,
    )
    result = calculate(inputs, strict=True, scenario="talent", sensitivity=True)

    ad_variant = result["sensitivity"]["ad_spend_plus_50pct"]
    if ad_variant.get("valid") is not True:
        raise AssertionError(f"well-formed strict talent variant should remain valid: {ad_variant}")

    gmv_variant = result["sensitivity"]["gmv_minus_10pct_same_spend"]
    if gmv_variant.get("valid") is not False:
        raise AssertionError(f"strict conflicting variant should be marked invalid: {gmv_variant}")
    if "inconsistent gmv representations" not in gmv_variant.get("error", ""):
        raise AssertionError(f"strict variant must surface its consistency failure: {gmv_variant}")


def test_target_profit_is_not_an_incurred_cost() -> None:
    base = strict_inputs(gmv=300000, orders=1000, product_cost_rate=45,
                         gift_cost=18000, fulfillment_cost=18000,
                         refund_loss=18000, ad_spend=150000, content_cost=6000)
    actual = calculate(base, strict=True)
    target = calculate({**base, "target_profit": 15000}, strict=True)
    assert_close(actual["metrics"]["contribution_profit"], -45000)
    assert_close(target["metrics"]["contribution_profit"], -45000)
    assert_close(target["metrics"]["break_even_roi"], 300000 / 105000)
    assert_close(target["metrics"]["allowable_cac"] * 1000, 90000)
    extra_cost = calculate({**base, "service_fee": 15000}, strict=True)
    assert_close(extra_cost["metrics"]["contribution_profit"], -60000)


def test_refund_principal_is_counted_once_across_revenue_bases() -> None:
    gross = strict_inputs(gmv=300000, orders=1000, product_cost_rate=45,
                          gift_cost=18000, fulfillment_cost=18000,
                          refund_loss=18000, ad_spend=150000)
    gross.pop("product_cost_rate")
    gross["product_cost"] = 135000
    net = {**gross, "gmv": 282000, "refund_loss": 0}
    gross_result = calculate(gross, strict=True)
    net_result = calculate(net, strict=True)
    assert_close(gross_result["metrics"]["contribution_profit"], -39000)
    assert_close(net_result["metrics"]["contribution_profit"], -39000)
    assert_close(net_result["metrics"]["comprehensive_margin"], 111000 / 282000)
    # A net-revenue ROI has a different numerator; retain that distinction.
    assert_close(net_result["metrics"]["break_even_roi"], 282000 / 111000)


def main() -> int:
    tests = [
        test_qianchuan_budget_case,
        test_target_profit_is_not_an_incurred_cost,
        test_refund_principal_is_counted_once_across_revenue_bases,
        test_talent_booking_case,
        test_paid_and_creator_costs_share_one_acquisition_ceiling,
        test_strict_mode_rejects_missing_inputs,
        test_strict_mode_requires_explicit_cost_buckets,
        test_talent_strict_mode_requires_scenario_costs,
        test_unknown_input_key_is_rejected_with_suggestion,
        test_conflicting_amount_and_rate_fail_closed_in_strict_mode,
        test_conflicting_gmv_orders_and_aov_fail_closed_in_strict_mode,
        test_per_order_cost_requires_order_basis_in_strict_mode,
        test_reference_formula_matches_calculator_cost_buckets,
        test_invalid_rate_rejected,
        test_percent_string_validation,
        test_non_rate_percent_and_boolean_rejected,
        test_numeric_percent_like_rate_is_preserved,
        test_sensitivity_output,
        test_sensitivity_propagates_strict_mode_and_scenario,
    ]
    for test in tests:
        test()
    print("unit_economics regression tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
