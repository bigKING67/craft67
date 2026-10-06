# Data Review Metrics

## Load when

Use this reference for dashboards, daily/weekly/monthly reviews, channel contribution analysis, campaign review, or when the user provides performance data.

## Review principle

Separate four layers before deciding an action:

1. `Traffic quality`: exposure, CTR, CPC, source mix, search intent, creator/content fit.
2. `Conversion quality`: CVR, product click, payment CVR, AOV, review trust, page/live-room persuasion.
3. `Profit quality`: gross-profit ROI, channel net profit, refund loss, fulfillment/gift cost, commission, pit fee.
4. `Asset quality`: brand/category search lift, review growth, member growth, repeat purchase, reusable content, creator pool.

Do not call a channel healthy only because GMV or ROI rose. Check whether profit and assets improved.

## Metric dictionary

| Metric | Use for | Watchout |
| --- | --- | --- |
| GMV | Size of transaction result | Not profit; can rise while net profit falls |
| Ad spend | Paid scale and risk exposure | Must connect to marginal ROI and cash flow |
| ROI | Explicitly scoped attributed GMV / matching ad spend for paid reporting | Total channel GMV cannot replace paid attributed GMV; also check gross margin and refund loss |
| Gross-profit ROI | Gross profit / ad spend | Still misses platform fee, gift, fulfillment, refund, commission, pit fee |
| Channel net profit | Channel GMV minus all direct channel costs | Best decision metric for scale/cut decisions |
| New-customer share | Acquisition value | Needs repurchase payback if first order loses money |
| Repurchase rate | LTV quality | Track by SKU role and cohort, not only aggregate |
| Refund loss | Profit leakage | Refund rate is not the same as monetary refund loss |
| Inventory days | Fulfillment and scale readiness | Low stock can break paid learning and reviews |
| CTR | Hook/cover/title match | High CTR with low CVR usually means landing or price/trust issue |
| CPC | Traffic cost | Low CPC can still be bad if intent is weak |
| CVR | Conversion efficiency | Diagnose by price, proof, reviews, SKU structure, service promise |
| AOV | Basket quality | AOV growth may hide discount or gift-cost damage |
| Live GPM / UV value | Live-room commercial efficiency | Needs refund and product-click context |
| Product click rate | Product interest after content/live explanation | Low rate means SKU, card, price, benefit, or sequence issue |
| Payment CVR | Final purchase trust | Low rate points to price, reviews, page, coupon, shipping, or customer-service concerns |
| Brand-word search | Mindshare and seeding effect | Must connect to landing conversion |
| Category-word search | New demand capture | Requires title/detail/search ad alignment |
| Review count and quality | Trust asset | Watch negative reasons and buyer-show quality |

## Ratio reconstruction and scope

Before calculating a missing quantity, identify the metric population, numerator, denominator, period, attribution window, refund treatment and maturity. Same dates or attribution windows alone do not establish the same population. Do not substitute total channel revenue, all-shop GMV or organic/creator GMV for the attributed GMV numerator of a paid-channel ROI.

For two periods, spend growth = (attributed GMV_new / attributed GMV_old) × (ROI_old / ROI_new) - 1. If only total-channel GMV growth is known, actual spend growth remains unknown: obtain both periods of comparable spend or attributed GMV. A calculation using an additional same-growth assumption is allowed only when that assumption is explicitly hypothetical and the result is not presented as confirmed or likely. This also applies to deriving orders from AOV, profit from margins, or refunds from rates: match populations and avoid double counting.

## Daily review output

For daily reviews, output:

1. What changed: metric movement and affected channel/SKU.
2. Likely cause: traffic, conversion, profit, fulfillment, or asset layer.
3. Decision implications: explain which Commercial, Growth, or Operations owner should assess the finding; do not take over that owner's decision. Assigning the owner's name to an instruction does not turn it into analysis: request a decision ("Growth evaluates whether to defer expansion"), rather than prescribe an unapproved action ("Growth pauses expansion"). This distinction applies to cautious pauses as well as cuts, increases and operational fixes.
4. Evidence: confidence, alternative explanations, missing evidence, and the next verification window. Cite an existing stop/scale threshold only when its commercial guardrail and owner are confirmed; otherwise request that owner's decision instead of inventing a threshold.
5. Risk: inventory, refund, price conflict, claim/compliance, or review damage.

## Weekly review output

For weekly reviews, output:

| Area | Ask | Decision |
| --- | --- | --- |
| SKU role | Did each SKU do its job? | Keep, replace, bundle, split by channel |
| Channel profit | Which channel made contribution profit? | Scale, cap, or treat as asset budget |
| Content | Which hooks/creators/search terms created reusable assets? | Reuse, boost, brief more, or retire |
| Search/shelf | Did seeding convert into search and product-detail visits? | Fix title/detail/reviews or buy search harvest |
| Price control | Did any channel break the price ladder? | Separate SKU/spec/gift or forbid floor price |
| Fulfillment/reviews | Did scale create complaints or refund reasons? | Cap sales, change promise, fix CS/script |

## Monthly review output

For monthly reviews, output:

- Paid share vs natural share.
- Gross-profit ROI and channel net profit by channel.
- Brand/category-word search trend.
- New-customer cohort quality and first-order loss payback.
- Repurchase by SKU role.
- Creator/content reusable asset pool.
- Assortment and price-ladder change for the next month.
