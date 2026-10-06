# Business Model and Profit

## Contents

- [Load when](#load-when)
- [Stage diagnosis](#stage-diagnosis)
- [Required model](#required-model)
- [Core formulas](#core-formulas)
- [Revenue, refunds and target profit](#revenue-refunds-and-target-profit)
- [Missing-data handling](#missing-data-handling)
- [Budget decision rules](#budget-decision-rules)
- [Executable experiment gates](#executable-experiment-gates)

## Load when

Use this reference for business diagnosis, profitability, ROI, budget, first-order loss, paid media scale, or review decisions.

## Stage diagnosis

| Stage | Primary job | Avoid |
| --- | --- | --- |
| Cold start | Test product, price, content, audience, creator, search terms, live conversion | Large paid-media or head-creator bets |
| Single-SKU lift | Find one stable converting SKU and build assets around it | Expanding SKU matrix too early |
| Hero-SKU scale | Scale proven content, creators, keywords, live rhythm, inventory | GMV growth without margin/refund control |
| Multi-SKU matrix | Add second hero, profit SKU, bundle, repurchase SKU, scene SKU | Same SKU/same price across all channels |
| Long-term brand operation | Grow brand words, category words, members, natural traffic, creator pool | Permanent low-price dependency |
| Profit/channel governance | Lower paid share, optimize commission, reduce refund, govern price | Treating all GMV as good GMV |

## Required model

For full plans, request or assume:

- AOV, product cost, gross margin, platform fee, fulfillment cost, gift cost.
- Refund rate and refund loss.
- Creator commission, pit fee, sample cost, service fee, content cost.
- Ad spend, ROI, gross-profit ROI, new-customer share.
- Repurchase cycle, repurchase rate, LTV, member/private-domain path.

## Core formulas

```text
GMV = exposure x CTR x CVR x AOV
ROI = transaction amount / ad spend
Gross-profit ROI = gross profit / ad spend
Break-even ROI = 1 / margin available for paid media

Available before ad =
GMV - product cost - platform fee - creator commission - pit fee
- gift cost - sample cost - fulfillment cost - refund loss
- service fee - content cost

Channel net profit = available before ad - ad spend
Comprehensive margin = available before ad / GMV
Break-even ROI = 1 / comprehensive margin
Allowable CAC = available before ad / orders - target unit profit
```

All terms in `available before ad` are totals for the same decision window, channel and SKU/order population. Align transaction versus settlement revenue and refund maturity explicitly. Brand-wide AOV or margin does not establish the economics of paid-attributed orders; matching dates or calling metrics comparable does not establish this equality. If unverified, request the cohort-specific figures or state the missing equality as a hypothetical assumption without asserting an observed per-order loss.

A missing cost is not zero: in strict mode, explicitly provide every required cost bucket, using `0` only when the cost is confirmed not to apply. Creator commission and pit fee are additionally mandatory for a talent scenario.

### Revenue, refunds and target profit

Choose a single revenue base `G`. Every rate and the numerator of `G / ad spend` must use this base. On gross transaction GMV, record refund principal and other refund losses once. On revenue already net of refunded principal, deduct only additional unrecovered costs not already reflected in revenue or another cost bucket; rebuild the contribution rate on that net base. A refund rate is not automatically a monetary loss rate. Do not switch from gross GMV to net GMV while retaining a rate that deducted the same refund principal.

Let `c` be the contribution rate after variable non-ad costs on `G`, `F` the fixed non-ad costs excluded from `c`, `A` ad spend, and `t` the target profit rate on `G`:

```text
Actual contribution profit = G*c - F - A
Cost break-even ad ceiling = G*c - F
Target-profit ad ceiling = G*(c-t) - F
At a fixed forecast G > 0:
Cost break-even G/A = 1 / (c-F/G)
Target-profit required G/A = 1 / (c-t-F/G)
```

ROI thresholds require a positive denominator. A negative ad ceiling means the objective is infeasible even at zero ad spend; zero permits no positive ad budget. A fixed-G ceiling is affordability at that forecast, not evidence that G stays constant when A changes. Include fixed costs once: `available before ad` in the earlier total-cost formula already includes them.

Target profit is an objective, not an incurred expense. For example, on G=300,000 with gross margin 55%, gifts/fulfillment 12%, refund loss 6% (all on the same gross base, no duplicated costs), A=150,000 and F=0, actual contribution is -39,000. Adding a 5% target leaves actual contribution unchanged and makes the target shortfall 54,000; adding 5% actual costs instead reduces actual contribution to -54,000. If an additional F=6,000 is incurred, actual contribution becomes -45,000, the cost break-even ad ceiling is 105,000 and the 5%-target ceiling is 90,000, requiring G/A of about 2.857 and 3.333 respectively. These are conditional arithmetic examples, not actual brand results or scaling authorization.

## Missing-data handling

If data is missing, use a labeled assumption block:

```text
Assumption model:
- AOV: ...
- Comprehensive gross margin: ...
- Fulfillment + gift: ...
- Refund loss: ...
- Target unit profit: ...
Therefore allowable CAC is approximately ...
If actual refund or gift cost is higher, reduce ad budget or raise bundle AOV first.
```

Never convert assumed economics into confirmed conclusions.

## Budget decision rules

### Executable experiment gates

Use the same explicitly named revenue numerator for observed ROI and its stop/scale threshold. If gross transaction GMV is used, account for mature refund losses once in its contribution rate. If net revenue is used, rebuild that rate and threshold on net revenue; do not compare net ROI against a gross-ROI threshold merely because both are called refund-adjusted.

Reconcile the calendar with the stage count: three sequential stages requiring at least 72 hours each need at least nine days, before any additional setup, washout or refund-maturity wait. A seven-day plan must use fewer such stages or explicitly defer the remainder. Stages may overlap only when independent allocations and interference controls justify it, not to make the dates fit. State which early signals permit bounded learning and which mature-refund evidence is required before scale.

When using an existing budget, identify the donor allocation, experimental spend and unaffected control; do not fund treatment by changing its own supposedly unchanged control. Evaluate the donor's displaced contribution for a portfolio-level conclusion. Keep the total approved spend and loss caps binding if timing changes; more observation time is not authorization for more spending.

A frozen expansion budget may fund a separately approved learning tranche only after its accountable owner releases that tranche within the approved total and loss caps; the remainder stays frozen. For a chosen revenue basis, set the scale hurdle to `max(approved target-profit ROI, cost break-even ROI * approved safety multiple)`. If the target is still a proposal, label it as such and require its approval before scale; never use the safety multiple to override an adopted profit target. For example, a 37% pre-ad contribution rate with zero fixed cost needs ROI 3.125 for a 5% target; ROI 3.0 yields only about 3.67% contribution on revenue, so a lower break-even safety hurdle is insufficient.

- Low CTR: test hook, cover, title, visual proof, and opening scene before changing the product.
- High click but low CVR: inspect price, review base, SKU structure, product page, live-room trust, and fulfillment promise.
- Fast spend with no orders: cap budget or pause; do not wait for "learning" without a conversion signal.
- Low ROI but high new-customer share: decide whether first-order loss is allowed and define payback cycle.
- High ROI but low volume: scale gradually; avoid abrupt budget jumps that break marginal ROI.
- Scale causes ROI drop: split audience, creative, bidding, SKU, and channel jobs.
- GMV up but net profit down: treat the action as brand/asset investment only if that budget owner is explicit.
