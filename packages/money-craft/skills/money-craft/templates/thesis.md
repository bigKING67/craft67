---
schema: money-craft.thesis.v1
workflow: thesis
security: {{security_name}}
security_id: {{market_symbol}}
as_of: {{YYYY-MM-DD}}
data_cutoff: {{ISO-8601}}
base_currency: {{base_currency}}
provider_status: {{provider_availability}}
---

# {{security_name}} 投资论文

## 结论

{{core_thesis_within_200_chinese_characters}}

## 事实与证据

- {{observable_fact}} [S01]
- {{observable_fact}} [S02]

## 核心假设

| ID | 假设 | 指标与阈值 | 验证来源 | 频率 | 状态 |
|---|---|---|---|---|---|
| H01 | {{testable_hypothesis}} | {{metric}} | [S01] | {{frequency}} | UNVERIFIED |

## 估值与假设

{{bear_base_bull_scenarios_with_formula_inputs_and_units}}

<!-- money-craft-calc: {"id":"C01","operation":"multiply","inputs":["1","1"],"expected":"1","tolerance":"0.000001"} -->

## 风险与反方证据

{{strongest_counterarguments}}

## 证伪条件

| ID | 条件 | 严重度 | 当前状态 | 证据 |
|---|---|---|---|---|
| R01 | {{observable_red_line}} | {{fatal_or_material}} | UNVERIFIED | [S02] |

## 更新记录

| 日期 | 假设变化 | 估值变化 | 结论变化 | 来源 |
|---|---|---|---|---|
| {{YYYY-MM-DD}} | {{initial_or_updated}} | {{change}} | {{change}} | [S01] |

## 来源索引

- [S01] {{official_source_url_or_local_capture_path}}
- [S02] {{independent_source_url_or_local_capture_path}}
