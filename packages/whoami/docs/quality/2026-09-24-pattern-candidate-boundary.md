# 财格候选入口与成格未决的分层验收

日期：2026-09-24。结论：`wealthReview.status=candidate-only` 可以支持 pattern 的窄范围 `conditional`——只确认财格候选入口满足；`wealthReview.judgment=unresolved` 继续表示成格、破格、救应与格局用神未裁定。两种状态描述不同层级，不互相冲突。

## 可收窄的最低结论

- 月支必须藏有正财或偏财。
- 该月藏财干必须精确出现在年、月或时干；同五行异干、同为财类但不同干，以及日干同字，都不能代替。
- 满足后只写“正财格/偏财格候选入口已满足”或等价表述，并在同一段写明尚未确认成格。
- 八组 `observed` 只确认对应显干前提；财印位置、财官分支及其他反例继续保留，不能按多数表决。
- `outside-scope` 只表示当前模块入口未满足。pattern 继续 unresolved，不能写成无财格、财格不成或命盘不好。

## 当前核心重算

三例均使用仓库内合成出生资料和当前构建版 `context`。本轮判断的是候选入口，不评价传统理论或现实结果。

| 对照 | 输入与年份 | 可复算事实 | 模块状态 | pattern 最低边界 |
|---|---|---|---|---|
| 正例 | [`examples/birth.json`](../../examples/birth.json)，2024—2028 | 庚辰、甲申、丙午、庚寅；申藏庚偏财，年、时干均见庚；candidate 为庚偏财 | `candidate-only` | 可条件性确认“偏财格候选入口已满足”，成格继续未决 |
| 近失配 A | [`strength-balance/birth.json`](../../examples/acceptance/strength-balance/birth.json)，2026—2028 | 庚午、戊子、丁巳、甲辰；年干庚为正财，但月支子只藏癸七杀，不藏财 | `outside-scope` | 其他柱显财不能代替月令财；不得写无财格或财格失败 |
| 近失配 B | [`case-02-birth.json`](../../examples/acceptance/strength-ablation/case-02-birth.json)，2026—2028 | 己巳、壬申、甲寅、壬申；申藏戊偏财，年干己为正财；己与戊同属土和财类，但不是同一干，戊的 `exposedAt=[]` | `outside-scope` | 同五行或同财类异干不能冒充月藏同干透出；不得写无财格或财格失败 |

正例重算得到 `chartId=a3fee7834bc85e84bff82e9ad80e72c9678383d5948ea7ae4d76e2094cb97789`、`evidenceId=3d0b34bd617494d53f269cc99fa79edf01647a9ebb72b0fc6a806970d096ea9e`。`wealthReview` 返回 `candidate-only`、庚偏财及 `exposedAt=[year,hour]`，同时保留 `judgment=unresolved`、财印相邻风险和其余待核条件。

近失配 A 重算得到 `chartId=4b6a66ef698209a07964e294019e8ad54923b3fc74eccaa1786dc7aeaa20f62a`、`evidenceId=8412f9eadc80551ea35b44533fafb97fe6dad691f990827416b521d2e1aeb410`。近失配 B 重算得到 `chartId=ddbbd8bb361b916e2c328aea10f14e779e308bb87762beaee42e5e6ad3cc61dd`、`evidenceId=9b5af8ebc18f73fbf97b16ff6d17b13387b4f5f77953f9a0ff16ca74b7069d0d`。两例均返回空 candidates 和 `outside-scope`，但 `judgment` 仍为 unresolved，未形成否定格局的证据。

## 主报告更新边界

主报告的 pattern 改为 `conditional`，结论只新增“偏财格候选入口已满足”的层级说明；成格、财印实际作用、寅申冲、旺衰、救应和格局用神全部保留未决。正文中只引用 strength 与 pattern 的性格段，因两个前提现在均为 conditional，其 `premiseStatus` 同步改为 conditional；其他仍引用 climate 或 selection 的段落继续 unresolved。

本轮没有修改核心 `wealthReview` 输出、报告 schema、自动成格逻辑或依赖。结构校验通过只能证明引用和前提状态一致，不能证明自然语言格局分析正确，更不能证明现实预测有效。

主报告 `report-check` 返回 valid，重新 `render` 与 [`examples/report.md`](../../examples/report.md) 字节一致。更新后的结构化报告为 27,568 字节、SHA-256 `91afde918b76a4244d52a353ea7f2054bc3e349cf3d951b2a3747c0ac291b75d`；Markdown 为 66,006 字节、SHA-256 `1c3dd97375cce2365661e082d5163a9fe810b9c55ca197142ab1155470ac4146`。`npm run check` 132/132 PASS，TypeScript strict 与 build PASS，Skill quick_validate PASS；49 个现行 Markdown 的 167 个本地链接无缺失，`openspec/` 仍不存在。
