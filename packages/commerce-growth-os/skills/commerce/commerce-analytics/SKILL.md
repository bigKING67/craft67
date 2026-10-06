---
name: commerce-analytics
description: 消费品牌电商经营分析 Skill。用于指标口径、数据质量、GMV/利润/ROI/退款/转化/搜索/复购漏斗、渠道贡献、Cohort/LTV、归因、实验、异常诊断以及日报周报月报。解决“事实发生了什么、为什么、证据有多强”；不负责退款执行 SOP、付费搜索投放、基于 LTV 的预算决策，也不参与已知成本输入下的单次渠道净利润/达人合作测算，后者属于 commerce-commercial-strategy。
---

# Commerce Analytics

## Role

Own the facts layer for commerce decisions. Define comparable metrics, diagnose changes, distinguish evidence from hypotheses, and make uncertainty visible.

## Workflow

1. Confirm data source, grain, time window, timezone, attribution window, and denominator.
2. Validate completeness, freshness, duplicates, refunds, and comparability.
3. Decompose GMV into traffic, CTR, CVR, and AOV; decompose profit into all material costs. Before reconstructing a quantity from a ratio, verify the same metric population and numerator/denominator scope. Total channel GMV is not automatically the attributed GMV numerator of paid ROI; if that numerator growth is unknown, spend growth is unknown. State any additional equality assumption explicitly as hypothetical, not observed or likely.
4. Compare channel, SKU, audience, creative, cohort, and lifecycle segments.
5. Separate observed fact, likely cause, alternative explanation, and required verification.
6. Output decision implications without taking ownership from the action domain. Naming an action owner does not authorize Analytics to prescribe that owner's budget or operational action. When approval or guardrails are missing, request that owner's decision and supply the evidence needed; for example, "Growth assesses whether to defer expansion" rather than "Growth pauses budget increases." Do not issue pause, cut, resume or scale instructions before the accountable owner has decided.

## Owned capabilities

- Metric dictionary and data contracts.
- Funnel, channel profit, refund, search, repurchase, cohort, and LTV analysis.
- Attribution assumptions, incrementality evidence, holdout and experiment readouts.
- Daily, weekly, and monthly review structures.
- Anomaly detection, root-cause trees, confidence, and next evidence request.

## References

- `references/data-review-metrics.md`
- `references/contracts/answer-quality-rubric.md`
- `references/contracts/category-overlay-contract.md` before applying a category overlay.
- `references/currentness/` for current report fields, attribution options, and platform metric definitions.
- `references/platform-overlays/` for platform-specific metric differences.
- `references/category-overlays/` for category-specific cycles and risks.

## Boundary

This skill defines facts and implications. Commercial Strategy decides economics, Marketing decides audience/media/content actions, and Operations decides execution actions.

## Output contract

Output metric change, data quality, decomposition, likely causes, alternatives, decision implication, owner/action, guardrail, and next review window.
