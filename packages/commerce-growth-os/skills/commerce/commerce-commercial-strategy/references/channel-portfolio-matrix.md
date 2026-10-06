# Channel Portfolio Matrix

## Load when

Use this reference when the user asks for full-channel strategy, which channels to enter, budget allocation, channel conflict, cross-channel portfolio design, or "Douyin/Tmall/Xiaohongshu/JD/Pinduoduo/WeChat should each do what".

## Principle

Do not choose channels by popularity. Assign a channel job by business model, SKU role, price ladder, content proof, search demand, conversion trust, fulfillment/service capacity, and repeat-purchase path.

Use this decision order:

1. Unit economics and price floor.
2. SKU role and whether the SKU can tolerate public comparison.
3. User decision mode: impulse, search, trust, replenishment, service-heavy, gift, or clearance.
4. Required proof: content demo, review/Q&A, parameter table, certification, creator trust, or service promise.
5. Channel conflict and price-memory risk.
6. Stop/scale metric and owner.

## Channel job matrix

| Channel | Primary job | Best-fit SKU | Use when | Do not use when | Key metric | Main risk |
| --- | --- | --- | --- | --- | --- | --- |
| Xiaohongshu | Trust, search mindshare, scenario education | Hero, proof SKU, premium scenario SKU | Users research before buying; proof and word-of-mouth matter | Landing page cannot absorb search intent or claims are unsafe | Search lift, save/comment quality, store/detail visits | Fake-looking seeding, weak landing conversion |
| Douyin short video | Interest creation, fast test, content asset discovery | Traffic SKU, hero SKU, demo SKU | The product can be shown in 3-15 seconds and tested by creative angle | Product needs long rational comparison before first click | Hook CTR, product click rate, paid reuse ROI | Chasing views without conversion or asset value |
| Douyin self-live | Stable conversion, SKU education, repeatable room model | Hero, bundle, repurchase SKU | Team can explain product, hold price, and review room metrics daily | Supply/CS/refund cannot support volume | Room payment CVR, gross-profit ROI, refund loss | GMV growth with margin/refund deterioration |
| Douyin talent livestream | Trust conversion, burst scale, creator audience match | Talent-exclusive pack, bundle, event SKU | Creator fit, economics, inventory, and review base are ready | Pit fee/commission breaks profit or price line | Channel net profit, new-customer quality | Paying for volume that damages price memory |
| Douyin shelf/search/product card | Active demand capture after content seeding | Standard hero, keyword SKU | Users search product/category/brand words | Product page cannot convert or reviews are weak | Search payment CVR, product-card ROI | Treating shelf as paid-traffic substitute |
| Tmall | Official trust, search/review landing, member repurchase | Hero, flagship, routine/repurchase SKU | Brand search and review proof matter | Price line conflicts with live or Pinduoduo | Brand-word CVR, review quality, member repurchase | Weak detail page wastes seeding demand |
| JD | Trust, authenticity, delivery/service, parameter comparison | Standard model, service-heavy, gift/fast-delivery SKU | Warranty, invoice, logistics, parameters, or after-sale matter | SKU is impulse-only or price comparison cannot be controlled | Search CVR, Q&A/review growth, service score | Direct price/spec comparison and after-sale cost |
| WeChat/private domain | Repurchase, member lifecycle, old-customer recall | Refill, subscription, member pack, service SKU | Repeat cycle and customer relationship are valuable | No content/member reason to re-contact users | Repurchase rate, LTV, recall conversion | Over-messaging without value |
| Pinduoduo | Clearance, value pack, defensive low-price reach | Channel-exclusive spec, old model, value pack | Objective is explicit and price separation is enforceable | Same hero SKU would be visibly cheaper | Channel net profit, subsidy cost, price complaints | Brand price memory and cross-channel complaints |
| Kuaishou | Relationship commerce, value bundle, trust live conversion | Bundle, practical household, creator-fit SKU | Category benefits from relationship trust and value explanation | Brand cannot accept value perception or service pressure | Live conversion, repeat order, complaint rate | Low-price framing and fulfillment pressure |
| Offline/distributor | Regional reach, service, trial, inventory clearing | Service SKU, sample/trial, local bundle | Physical trial, local service, or distributor coverage matters | Channel price/stock cannot be audited | Sell-through, price compliance, local repeat | Gray-market leakage |

## Portfolio construction

### Core split

- **Mindshare channels**: Xiaohongshu, creators, short video. They create trust/search demand and reusable assets.
- **Conversion channels**: Douyin live/shelf, Tmall, JD, Kuaishou. They convert demand and produce review/after-sale data.
- **Retention channels**: WeChat/private domain, members, subscription, replenishment reminders.
- **Value/clearance channels**: Pinduoduo, old-season/old-model distributor, controlled clearance events.

Do not let one channel perform every job. A channel that creates demand may not be the best final conversion point; a channel that clears inventory may damage the hero price line if not isolated.

### Budget buckets

Use percentages only as planning placeholders when the user has no history. Replace them with channel net profit, marginal ROI, conversion, and repurchase data as soon as data exists.

| Budget bucket | Job | Typical owner | Stop rule | Scale rule |
| --- | --- | --- | --- | --- |
| Proof/asset budget | Produce seeding, demos, reviews, detail-page material | Brand/content | Content saves/search/store visits stay weak | Reuse drives search, CTR, or CVR lift |
| Test budget | Validate channel/SKU/content fit | Growth | No decisive metric improves after a defined test window | One metric improves without hurting profit/refund |
| Scale budget | Buy proven traffic or talent capacity | Paid/live | Marginal ROI below break-even or refund rises | Marginal profit and service metrics remain stable |
| Search/shelf budget | Capture active demand | Platform ops | Clicks rise but payment CVR/review trust does not | Brand/category-word conversion improves |
| Clearance budget | Move old/isolated inventory | Finance/channel | Price complaints or negative price memory appear | Inventory reduces without price-line damage |
| Retention budget | Increase repeat/LTV | CRM/private domain | Recall conversion low or complaints rise | Repurchase and payback improve by cohort |

## Conflict rules

Resolve these before scaling:

1. **Same SKU/same spec/same gift/same public price conflict**: do not visibly undercut the hero SKU on a lower-trust or clearance channel.
2. **Benefit-stack conflict**: a lower headline price plus better gifts can still be a price breach.
3. **Search landing conflict**: if seeding creates search but Tmall/JD detail pages are weak, fix the landing before buying more traffic.
4. **Creator fairness conflict**: creators carrying similar packs need clear price/benefit windows or they will complain and stop cooperating.
5. **Clearance conflict**: old inventory should use isolated SKU names, pack sizes, gifts, or channels; do not reset the remembered price of the current hero.
6. **Unauthorized seller conflict**: define monitoring cadence, evidence owner, and enforcement path before a low-price channel expands.
7. **Service conflict**: channels that create high service expectations need CS scripts, warranty/refund rules, and review response ownership.

## Portfolio output template

When the user asks for a channel portfolio, output:

1. Channel role table: channel, SKU, price boundary, content asset, metric, owner.
2. Budget split by bucket, not only by platform.
3. First 14/30/90-day test sequence.
4. Stop/scale rules per channel.
5. Price and SKU conflict map.
6. Review cadence: daily operating dashboard, weekly decision review, monthly portfolio reset.
