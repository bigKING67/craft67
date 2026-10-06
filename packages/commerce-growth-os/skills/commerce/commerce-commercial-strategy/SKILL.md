---
name: commerce-commercial-strategy
description: 消费品牌商业策略与商品经营 Skill。用于利润模型、ROI/CAC/LTV、货盘、SKU 角色、价盘、渠道专供、最低利润价、达人佣金与坑位、投放预算边界、渠道进入和渠道冲突决策。遇到“值不值得、最多花多少、能否放量、是否降价或进渠道”时使用；“千川 ROI 下降后是否还能加预算、盈亏平衡和预算上限”必须使用本 Skill，并与 growth-performance-lifecycle-marketing 组合完成投放实验。
---

# Commerce Commercial Strategy

## Role

Own commercial viability. Decide whether a SKU, price, channel, creator, promotion, or media plan can create acceptable profit and strategic value.

## Workflow

1. Separate confirmed facts and assumptions.
2. Classify the decision: assortment, price, budget, creator, channel, or scale.
3. Build the smallest sufficient economics model.
4. Define price floors, budget ceilings, and channel constraints.
5. Run downside sensitivity when refund, commission, traffic cost, or volume can change the conclusion.
6. Output decision, conditions, stop rule, scale rule, owner, and review window.

## Required economics

Use `scripts/unit_economics.py` for concrete ROI, CAC, creator, or profitability decisions. Use `--strict` when missing costs can reverse the recommendation, `--scenario paid|talent|general` for decision-specific gates, and `--sensitivity` for scale decisions. Strict mode requires every material cost bucket explicitly, including a literal `0` when a cost is confirmed not to apply; it rejects unknown fields and inconsistent amount/rate representations.

Never recommend scale from platform ROI alone. Include product cost, platform fee, media, commission, pit fee, gifts, fulfillment, refunds, service, and content when material; show target profit separately from incurred costs.

Before calculating, explicitly align the channel, SKU/order population, revenue basis and refund state of AOV, margin and ROI. A matching time window or generic "comparable scopes" caveat is insufficient. Unknown equality permits only a labeled hypothetical model, not an observed profit claim. Use one revenue basis throughout: if revenue is already net of refunds, do not deduct the same refund principal again or reuse an unreconciled gross-GMV contribution rate. Distinguish actual contribution, cost break-even and target-profit requirements; fixed costs must enter the budget and corresponding ROI threshold. For these calculations, load `references/business-model-and-profit.md`.

Carry that revenue basis into every stop/scale comparison: "refund-adjusted ROI" is not a definition. Name its numerator and compare it only with a threshold built on the same gross/net basis. State the positive-denominator condition for ROI thresholds; a zero ad ceiling allows no positive ad spend, and a negative ceiling means the objective is infeasible even without ads.

For staged budget tests, state the funding source, non-overlapping control and treatment allocation, and a feasible calendar. Sequential stages must fit the sum of their observation windows; distinguish early media signals from mature-refund acceptance. If they do not fit the proposed horizon, reduce stages or explicitly extend the calendar without automatically increasing the approved spend cap. Budget transferred from another campaign is not costless incremental spend: account for displaced contribution or limit the inference to the tested allocation.

Frozen or unreleased budget is not an approved learning allocation: require the accountable owner's approval of the specific test tranche before spending, and include it in the approved total cap. A scale gate must meet both the approved target-profit ROI and any cost-break-even safety buffer; use the greater threshold on the same revenue basis. Do not introduce a target margin in the budget section and then silently relax it to a lower break-even multiple in the scale section.

## Owned decisions

- Business model and unit economics.
- SKU roles, assortment, bundles, and channel exclusives.
- Daily price, campaign price, member price, minimum profit price, and forbidden floor price.
- Allowable CAC, break-even ROI, maximum commission, pit-fee tolerance, and paid-media budget bounds.
- Channel jobs, entry gates, price conflicts, and unauthorized low-price risks.
- First-order loss tolerance and repurchase payback conditions.

## References

- `references/business-model-and-profit.md`
- `references/assortment-pricing-channel-control.md`
- `references/channel-portfolio-matrix.md`
- `references/contracts/answer-quality-rubric.md`
- `references/contracts/category-overlay-contract.md` before applying a category overlay.
- `references/currentness/` when a fee, eligibility rule, platform product, or report field can drift.
- `references/category-overlays/` when category risk changes economics.

## Boundary

Marketing owns audience and communication. Operations owns execution. Analytics owns metric definitions. Sourcing, capacity, upstream inventory, quality, or legal readiness must be confirmed by the user-designated Supply, Product, Quality, Legal, or external specialist owner; without one, keep the dependency as a blocker. This Skill owns the commercial constraints they must respect.

## Output contract

State the decision first, then confirmed facts, assumptions, economics, strategic value, price/channel risk, downside cases, stop rule, scale rule, owner, and next review.
