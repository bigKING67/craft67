---
schema: money-craft.thesis.v1
workflow: thesis
security: 贵州茅台
thscode: 600519.SH
as_of: 2026-08-23
data_cutoff: 2026-08-23T19:40:16+08:00
base_currency: CNY
provider_status: configured_with_latest_indicator_gap
---

# 贵州茅台投资论文

## 结论

品牌、毛利率与资本回报仍属稀缺资产，但 2025 年负增长及 2026 H1 利润承压削弱了确定性。2026-08-21 收盘价对应约 19.54 倍 TTM PE，接近基准情景而非深度折价；当前结论为“高质量、需等待增长与渠道验证”，置信度中等。[S03][S04][S08][S11][S12]

## 事实与证据

- 2025 年营业收入 1,688.38 亿元、归母净利润 823.20 亿元，同比分别下降 1.21% 和 4.53%；经审计年报与 Fuyao 字段一致。[S05][S08][S12]
- 2026 H1 营业收入 907.03 亿元、归母净利润 445.17 亿元，同比分别增长 1.47% 和下降 1.95%；营业成本同比增长 21.81%。[S11][S14]
- 2026 H1 合同负债较年初下降 60.31%，公司归因为市场改革、销售模式和预收政策变化；这是待验证解释，而非已证明的无风险变化。[S11]
- 2026 H1 经营现金流同比增长 438.84%，但主要受财务子公司成员存款及同业存放波动影响，不代表主业现金创造同比同幅改善。[S11][S16]
- 2026-08-21 收盘价 1,272.83 元，复算 TTM 归母净利润 814.34 亿元、PE 19.539 倍，与 Fuyao PE TTM 一致。[S03][S04][S11][S12]
- Fuyao 最新 `2026-2` 指标返回 Provider `5003/result empty`；H1 毛利率使用利润表字段派生，未把 2025 年指标冒充最新指标。[S14][S17]

## 核心假设

| ID | 假设 | 指标与阈值 | 验证来源 | 频率 | 状态 |
|---|---|---|---|---|---|
| H01 | 品牌与渠道改革能稳定收入 | 后续两个报告期收入不再连续负增长 | [S11][S12] | 季度 | UNVERIFIED |
| H02 | 利润率压力可控 | 派生毛利率不连续跌破 88%，归母净利率不持续下行 | [S11][S14] | 季度 | UNVERIFIED |
| H03 | 可持续归母净利润处于基准区间 | TTM 归母净利润约 840 亿元，Bear 下限 780 亿元 | [S11][S12] | 季度 | UNVERIFIED |
| H04 | 主业现金创造与利润匹配 | 剔除财务子公司存款波动后的 CFO/归母净利润接近或高于 1 | [S11][S16] | 半年度 | UNVERIFIED |

## 估值与假设

当前市值由 1,272.83 元和 1,250,081,601 股复算为 1.591 万亿元；TTM 归母净利润为 814.34 亿元，对应 PE 19.539 倍。[S03][S04][S11][S12]

<!-- money-craft-calc: {"id":"C01","operation":"multiply","inputs":["1272.83","1250081601"],"expected":"1591141364200.83","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C02","operation":"subtract","inputs":["126836947523.54","45402962298.10"],"expected":"81433985225.44","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C03","operation":"divide","inputs":["1591141364200.83","81433985225.44"],"expected":"19.53903348578545297721249280404509","tolerance":"0.000001"} -->

| 情景 | 可持续归母净利润 | PE | 每股价值 | 状态 |
|---|---:|---:|---:|---|
| Bear | 780 亿元 | 16 倍 | 998.33 元 | HYPOTHESIZED |
| Base | 840 亿元 | 20 倍 | 1,343.91 元 | HYPOTHESIZED |
| Bull | 900 亿元 | 24 倍 | 1,727.89 元 | HYPOTHESIZED |

<!-- money-craft-calc: {"id":"C04","operation":"multiply","inputs":["78000000000","16"],"expected":"1248000000000","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C05","operation":"divide","inputs":["1248000000000","1250081601"],"expected":"998.3348279037665797946577409069474","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C06","operation":"multiply","inputs":["84000000000","20"],"expected":"1680000000000","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C07","operation":"divide","inputs":["1680000000000","1250081601"],"expected":"1343.912268331993472800500805067045","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C08","operation":"multiply","inputs":["90000000000","24"],"expected":"2160000000000","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C09","operation":"divide","inputs":["2160000000000","1250081601"],"expected":"1727.887202141134465029215320800486","tolerance":"0.000001"} -->

## 风险与反方证据

- 行业处于结构性与周期性调整期，需求或批发价格走弱可同时压低利润与估值倍数。[S11]
- 合同负债下降和经销商调整可能是改革节奏，也可能是渠道信心下降；当前证据不能排除后一解释。[S11]
- 2026 H1 成本增速显著快于收入，历史高利润率并非不可逆。[S11][S14]
- 财务子公司使合并 CFO 失真；在拿到拆分口径前，主业自由现金流质量仍为 UNVERIFIED。[S11][S16]
- 食品安全、环境、监管和舆情事件会对高曝光品牌造成非线性永久损失。[S11]

## 证伪条件

| ID | 条件 | 严重度 | 当前状态 | 证据 |
|---|---|---|---|---|
| R01 | TTM 归母净利润跌破 780 亿元且无一次性解释 | fatal | UNVERIFIED | [S11][S12] |
| R02 | 收入与归母净利润连续两个定期报告同时负增长 | material | UNVERIFIED | [S11][S12] |
| R03 | 派生毛利率连续两个报告期低于 88% | material | UNVERIFIED | [S11][S14] |
| R04 | 合同负债、经销商和渠道回款连续两个报告期同向恶化 | material | UNVERIFIED | [S11] |
| R05 | 剔除财务子公司影响后的主业 CFO 持续低于归母净利润 | fatal | UNVERIFIED | [S11][S16] |

## 更新记录

| 日期 | 假设变化 | 估值变化 | 结论变化 | 来源 |
|---|---|---|---|---|
| 2026-08-23 | 初始建立 H01-H04 | 建立 Bear/Base/Bull 三情景 | 初始结论：高质量但基准估值缺乏显著安全边际 | [S03][S04][S11][S12] |

## 来源索引

- [S03] Fuyao valuations：`evidence-manifest.json` S03；底层响应仅保存在本地私有 evidence。
- [S04] Fuyao daily history：`evidence-manifest.json` S04；底层响应仅保存在本地私有 evidence。
- [S05] Fuyao annual income statements：`evidence-manifest.json` S05；底层响应仅保存在本地私有 evidence。
- [S08] Fuyao 2025-4 indicators：`evidence-manifest.json` S08；底层响应仅保存在本地私有 evidence。
- [S11] 贵州茅台 2026 年半年度报告：https://www.moutaichina.com/mtgf/articleFileDir/2026-08/17/277c9b776bff4ae89dde75e987437760.pdf；下载文件 SHA-256 见 `evidence-manifest.json` S11。
- [S12] 贵州茅台 2025 年年度报告：https://big5.sse.com.cn/site/cht/www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026-04-17/600519_20260417_9QS4.pdf；下载文件 SHA-256 见 `evidence-manifest.json` S12。
- [S14] Fuyao quarterly income statements：`evidence-manifest.json` S14；底层响应仅保存在本地私有 evidence。
- [S16] Fuyao quarterly cash-flow statements：`evidence-manifest.json` S16；底层响应仅保存在本地私有 evidence。
- [S17] Fuyao 2026-2 indicator error envelope：`evidence-manifest.json` S17；底层响应仅保存在本地私有 evidence。
