---
schema: money-craft.thesis.v1
workflow: thesis
security: 美的集团
thscode: 000333.SZ
as_of: 2026-08-23
data_cutoff: 2026-08-23T12:42:37.772301Z
base_currency: CNY
provider_status: configured_full_matrix_passed
---

# 美的集团（000333.SZ）投资论文

## 结论

美的集团以多品类规模、全球制造与渠道、研发和成本效率构成较强经营底盘，2025 年收入与归母净利润实现双位数增长；但 2026 Q1 扣非归母净利润下降、毛利率回落和应收账款上升，使“增长质量持续改善”仍未得到验证。[S08][S11][S12][S14][S15][S17]

2026-08-21 A 股收盘价 84.30 元，对应 Fuyao PE TTM 14.5507 倍；按正式报告近似复算为 14.5020 倍。价格接近本文 90.75 元基准情景，低于 Bull、明显高于 Bear；当前论文是“优质经营平台，但等待扣非增长和现金转换确认”，置信度中等。[S03][S04][S11][S12]

## 事实与证据

- 2025 年营业收入 4,564.52 亿元、归母净利润 439.45 亿元，同比分别增长 12.11% 和 14.03%；Fuyao 与经审计年报字段一致。[S05][S08][S12]
- 2026 Q1 营业收入 1,310.99 亿元、归母净利润 126.75 亿元，同比分别增长 2.55% 和 2.03%；扣非归母净利润同比下降 14.02%。[S11][S14][S17]
- 2025 年智能家居、商业及工业解决方案、海外业务收入占比分别为 65.71%、26.89% 和 42.93%，业务与地域组合已不是单一中国白电公司。[S12]
- 2025 年经营活动现金流净额 533.46 亿元，同比下降 11.84%；经营现金流减购建长期资产现金的简化代理值为 422.04 亿元。[S07][S12]
- 2026 Q1 应收账款从年末 404.50 亿元升至 525.37 亿元，存货从 646.29 亿元降至 578.24 亿元；季度季节性尚不能解释全部变化。[S11][S15]
- 2026 Q1 派生毛利率 25.5711%，低于 2025 年 26.3910%；最新 `2026-1` Provider 指标成功返回，未复用 2025 年指标冒充最新数据。[S08][S11][S14][S17]
- 2025 年每股 3.80 元分配额相对 84.30 元为 4.51%，但未来分红仍取决于利润、资本开支、并购和回购安排。[S04][S09][S12]

## 核心假设

| ID | 假设 | 指标与阈值 | 验证来源 | 频率 | 状态 |
|---|---|---|---|---|---|
| H01 | 核心家电与全球 OBM 能维持温和增长 | 收入和扣非利润不连续两个报告期同时负增长 | [S11][S12][S14] | 季度 | UNVERIFIED |
| H02 | 毛利率压力可逆 | 派生毛利率恢复至 26% 附近且不连续下滑 | [S08][S11][S14][S17] | 季度 | UNVERIFIED |
| H03 | 应收增长主要是季节性而非回款恶化 | 应收增速回落至不高于收入增速，CFO/利润保持匹配 | [S07][S11][S15][S16] | 季度 | UNVERIFIED |
| H04 | ToB 和跨境并购提高而非稀释资本回报 | 商业及工业解决方案利润率、现金回报和商誉风险改善 | [S11][S12] | 半年度 | UNVERIFIED |
| H05 | 可持续归母净利润达到基准区间 | TTM 归母净利润约 460 亿元，Bear 下限 400 亿元 | [S11][S12][S14] | 季度 | UNVERIFIED |

## 估值与假设

TTM 归母净利润按“2025 全年 + 2026 Q1 - 2025 Q1”近似为 441.98 亿元；当前总股本 7,603,276,186 股，对应 TTM EPS 约 5.8130 元、A 股 PE 约 14.5020 倍。[S03][S04][S11][S12][S14]

<!-- money-craft-calc: {"id":"C01","operation":"add","inputs":["43945411000","12674556000"],"expected":"56619967000","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C02","operation":"subtract","inputs":["56619967000","12422233000"],"expected":"44197734000","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C03","operation":"divide","inputs":["44197734000","7603276186"],"expected":"5.812985470839767282392916615800546","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C04","operation":"divide","inputs":["84.3","5.812985470839767282392916615800546"],"expected":"14.50201457114973360398974300356665","tolerance":"0.000001"} -->

| 情景 | 可持续归母净利润 | PE | A 股每股价值 | 状态 |
|---|---:|---:|---:|---|
| Bear | 400 亿元 | 11 倍 | 57.87 元 | HYPOTHESIZED |
| Base | 460 亿元 | 15 倍 | 90.75 元 | HYPOTHESIZED |
| Bull | 520 亿元 | 18 倍 | 123.10 元 | HYPOTHESIZED |

<!-- money-craft-calc: {"id":"C05","operation":"multiply","inputs":["40000000000","11"],"expected":"440000000000","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C06","operation":"divide","inputs":["440000000000","7603276186"],"expected":"57.86979050033419369990514244355242","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C07","operation":"multiply","inputs":["46000000000","15"],"expected":"690000000000","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C08","operation":"divide","inputs":["690000000000","7603276186"],"expected":"90.75035328461498557485124610466176","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C09","operation":"multiply","inputs":["52000000000","18"],"expected":"936000000000","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C10","operation":"divide","inputs":["936000000000","7603276186"],"expected":"123.1048270643472847797982121071933","tolerance":"0.000001"} -->

美的同时有 A/H 股。以上每股估值针对 `000333.SZ` 的 A 股价格比较；不能把 A 股价格乘全部 A/H 股后称为按两个市场分别计价的真实合并市值。[S11][S12]

## 风险与反方证据

- 2026 Q1 扣非归母净利润下降 14.02%，说明表面归母利润增长可能受非经常性项目支持。[S11][S14]
- Q1 毛利率低于 2025 全年，原材料、关税、价格竞争和业务组合均可能继续压缩利润率。[S08][S11][S12][S17]
- 应收账款季末较年末增加约 29.88%；若后续不能随季节回落，收入质量与现金转换将受损。[S11][S15]
- 海外收入占比超过四成，汇率、关税、本地合规和全球供应链变化可能抵消收入增长。[S12]
- Q1 商誉约 332.15 亿元，多业务并购可能产生整合成本或减值。[S11]
- 多元化可能分散周期风险，也可能降低管理聚焦并掩盖低回报业务；ToB 增长必须用利润和现金回报证明。[S12]

## 证伪条件

| ID | 条件 | 严重度 | 当前状态 | 证据 |
|---|---|---|---|---|
| R01 | TTM 归母净利润跌破 400 亿元且无一次性解释 | fatal | UNVERIFIED | [S11][S12][S14] |
| R02 | 收入和扣非归母净利润连续两个报告期同时负增长 | material | UNVERIFIED | [S11][S12][S14] |
| R03 | 派生毛利率连续两个报告期低于 25% | material | UNVERIFIED | [S08][S11][S14][S17] |
| R04 | 应收增速持续高于收入且 CFO/归母净利润明显低于 1 | fatal | UNVERIFIED | [S07][S11][S15][S16] |
| R05 | 商誉减值或并购整合成本持续侵蚀 ToB 增量利润 | material | UNVERIFIED | [S11][S12] |

## 更新记录

| 日期 | 假设变化 | 估值变化 | 结论变化 | 来源 |
|---|---|---|---|---|
| 2026-08-23 | 初始建立 H01-H05 | 建立 Bear/Base/Bull 三情景 | 初始结论：经营质量较强，但当前价格需等待扣非增长和现金转换确认 | [S03][S04][S11][S12] |

## 来源索引

- [S03] Fuyao valuations：`evidence-manifest.json` S03；底层响应仅保存在本地私有 evidence。
- [S04] Fuyao daily history：`evidence-manifest.json` S04；底层响应仅保存在本地私有 evidence。
- [S05] Fuyao annual income statements：`evidence-manifest.json` S05；底层响应仅保存在本地私有 evidence。
- [S07] Fuyao annual cash-flow statements：`evidence-manifest.json` S07；底层响应仅保存在本地私有 evidence。
- [S08] Fuyao 2025-4 indicators：`evidence-manifest.json` S08；底层响应仅保存在本地私有 evidence。
- [S09] Fuyao corporate actions：`evidence-manifest.json` S09；底层响应仅保存在本地私有 evidence。
- [S11] 美的集团 2026 年第一季度报告：https://static.cninfo.com.cn/finalpage/2026-04-30/1225259066.PDF；下载文件 SHA-256 见 `evidence-manifest.json` S11。
- [S12] 美的集团 2025 年年度报告：https://static.cninfo.com.cn/finalpage/2026-03-31/1225058110.PDF；下载文件 SHA-256 见 `evidence-manifest.json` S12。
- [S14] Fuyao quarterly income statements：`evidence-manifest.json` S14；底层响应仅保存在本地私有 evidence。
- [S15] Fuyao quarterly balance sheets：`evidence-manifest.json` S15；底层响应仅保存在本地私有 evidence。
- [S16] Fuyao quarterly cash-flow statements：`evidence-manifest.json` S16；底层响应仅保存在本地私有 evidence。
- [S17] Fuyao 2026-1 indicators：`evidence-manifest.json` S17；底层响应仅保存在本地私有 evidence。
