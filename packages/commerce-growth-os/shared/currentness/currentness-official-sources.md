# Currentness Official Sources

## Load when

Use this reference with `platform-currentness.md` when an answer needs current platform verification, source selection, or evidence labeling.

## Rule

This file lists verification entry points and what to verify. It does not cache current feature availability, backend capability, policy wording, fee rates, or eligibility thresholds.

Only label an answer `Officially verified` after checking the relevant official page, help center, policy page, or authenticated user backend in the current task. If a page is inaccessible, login-gated, stale-looking, or ambiguous, label the claim `Needs current verification`.

Prefer the user's authenticated backend for operational capability details; public official pages can lag backend rollouts.

## Verification order

1. User-provided current backend screenshots, exports, campaign settings, rejection notices, or platform notices.
2. Current official help centers, product documentation, announcements, and policy pages.
3. Official account-manager or platform service material supplied by the user.
4. Recent authoritative industry notes only as secondary context.

If evidence conflicts, prefer live backend behavior, then current official documentation, then recent official notices, then third-party commentary. For legal, safety, health, efficacy, or regulated-category claims, use the user's review notice, official platform policy, applicable regulator material, or qualified legal review rather than a marketing playbook.

## Source registry

| Platform area | Official / authority entry | Use to verify | Drift risk | Evidence label after checking |
| --- | --- | --- | --- | --- |
| Ocean Engine / 巨量引擎 / 千川 | `https://www.oceanengine.com/`, `https://school.oceanengine.com/product_help`, `https://support.oceanengine.com/support/?pageId=221&spaceId=122` | Product names, campaign types, account navigation, bidding/optimization modes, attribution/report fields | High | `Officially verified` only after current page/backend check |
| Douyin e-commerce / 抖音电商 / 抖店 | `https://school.jinritemai.com/`, user's Douyin shop backend | Shop rules, shelf/search/product-card entry, merchant rules, fees, fulfillment, after-sale, category policy | High | `Officially verified` or `Confirmed from user backend` |
| Xingtu / 星图 | `https://www.xingtu.cn/`, `https://www.xingtu.cn/help-center` | Creator cooperation formats, authorization, task workflow, quotation/settlement, disclosure, report visibility | High | `Officially verified` only after current help/backend check |
| Tmall / Taobao / Alimama / 万相台 | `https://www.alimama.com/`, user's Tmall/Taobao/Alimama merchant backend | Wanxiangtai product names, campaign objectives, keyword/audience modes, member tools, fee/report fields | High | `Officially verified` or `Confirmed from user backend` |
| Xiaohongshu / 聚光 | `https://ad.xiaohongshu.com/`, `https://ad.xiaohongshu.com/help/home` | Juguang product entrances, Feed/Search split, campaign objective, landing restrictions, report fields, industry access | High | `Officially verified` only after current page/backend check |
| Xiaohongshu / 蒲公英 | `https://pgy.xiaohongshu.com/`, `https://pgy.xiaohongshu.com/help/home` | Creator cooperation workflow, brand/agency authorization, review rules, disclosure, content audit, data visibility | High | `Officially verified` only after current page/backend check |
| JD / 京准通 / 京东商家 | `https://jzt.jd.com/`, `https://jzt.jd.com/school/problem`, user's JD/Jingzhuntong backend | Search/recommendation/display ads, learning docs, product names, reporting, merchant requirements, service rules | Medium-high | `Officially verified` or `Confirmed from user backend` |
| Pinduoduo / 拼多多商家 / 多多进宝 | `https://mms.pinduoduo.com/`, `https://jinbao.pinduoduo.com/`, `https://open.yangkeduo.com/` | Merchant backend rules, promotion/CPS tools, subsidy/commission mechanics, product/API docs, order/report fields | High | `Officially verified` or `Confirmed from user backend` |
| Kuaishou / 磁力引擎 / 快手电商 | `https://e.kuaishou.com/`, `https://knowledge.e.kuaishou.com/`, `https://www.kwaixiaodian.com/index.html`, `https://login.kwaixiaodian.com/`, `https://edu.kwaixiaodian.com/rule/web/category` | Magnetic Engine products, Kuaishou merchant entry, rules, creator/live commerce docs, category access, ads reporting | High | `Officially verified` or `Confirmed from user backend` |
| WeChat Channels / 视频号小店 / 微信小店 | `https://channels.weixin.qq.com/shop`, `https://developers.weixin.qq.com/doc/channels/Operational_Guidelines/Shop_opening_guidelines.html`, user's WeChat shop/backend | Shop entry, merchant rules, live/shop connection, product display, private-domain handoff, category and after-sale rules | High | `Officially verified` or `Confirmed from user backend` |
| Platform compliance / claims | Official platform policy centers, user's review rejection notice, applicable regulator or legal counsel source | Claim wording, category access, qualification, ad review, prohibited content, disclosure requirements | High | `Officially verified`, `Confirmed from user backend`, or `Needs current verification` (then name the required platform, regulator, or legal review) |

## Verification checklist

Before making a platform-current recommendation, verify:

1. Exact product/feature name and whether it is still active.
2. Eligibility: account type, store type, category, region, qualification, deposit, or whitelist if relevant.
3. Entry path in current backend or official documentation.
4. Allowed use case and prohibited use case.
5. Fee, commission, settlement, attribution, or report field definitions if they affect economics.
6. Data visibility and export fields needed for review.
7. Policy/compliance boundaries and review risk.
8. Date, page URL, backend screenshot/export, or user-supplied notice used as evidence.

## Response snippet

Use this pattern in answers:

```text
Currentness:
- Stable principle: ...
- Needs current verification: exact backend entrance / product name / rule wording.
- Official/source to check: ...
- Decision impact: if the entrance or rule changed, we keep the operating principle but change the channel execution path and budget gate.
```

## Do not do

- Do not say "currently supports" because a URL exists in this registry.
- Do not interpret a successful reachability audit as proof that the page content is fresh or the capability still exists.
- Do not cite a third-party article as official platform evidence unless the user explicitly allows non-official research.
- Do not preserve fee rates, campaign options, or policy wording in memory or in this skill as permanent facts.
- Do not turn login-gated backend observations into public facts without the user's confirmation.

## Maintainer check

After editing this registry, run:

```bash
python3 tooling/evaluation/check_source_registry.py shared/currentness/currentness-official-sources.md --json
```
