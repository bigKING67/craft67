# 紫微限运作用链 v5

> 历史快照：本页记录 timingChain 首次落地时的状态与指纹。随后 v5 继续收紧了[紫微年度正文与作用链绑定](2026-09-25-ziwei-year-claim-binding-v5.md)；下列主报告哈希和 138 项测试数不代表当前文件。

日期：2026-09-25。结论：报告合同已从“声明引用了 `ziwei-timing`”收紧为可结构检查的限运作用链。`whoami.report.v5` 要求每个紫微候选的限运论证同时绑定目标主题、证据包内年份、四化事实、大限/流年事实、主题宫事实、跨层复核、现实依据、未闭合环节和撤回条件。现实触发资料未绑定时，状态必须失败封闭为 `unresolved`。

## 修正的问题

v4 已能要求五类紫微论证并把正文绑定到对应主题，但 `ziwei-timing` 的“作用链”仍藏在自由文本里。程序只能确认该主题存在，无法区分以下情况：

- 年份不在当前 evidence 中；
- 把本命基础、另一候选或其他类型事实冒充四化、大限或主题宫；
- 作用链引用没有进入该项支持/反证依据；
- 没有现实经历、目标与约束，却把限运状态升级为 conditional；
- 把仍列有缺口的链条写成已经收窄的结论。

v5 在 [`src/report.ts`](../../src/report.ts) 为 `ziwei-timing` 增加 `timingChain`。三组事实引用必须非空、唯一、同候选、类型正确，并已出现在本项 `supportRefs/counterRefs`。years 必须是当前 evidence 的非空唯一子集。career/wealth/relationships 目标还须分别引用官禄/财帛/夫妻宫，不能用另一主题宫冒充；general 按实际问题列出所用主题宫。非限运主题携带 timingChain 会拒绝。所有新增自由文本继续经过报告安全措辞门禁。

现实依据分为 `not-provided` 与 `provided`。前者要求 `source=null`、至少一个 `missingLinks`，并强制论证状态为 unresolved；后者要求非空来源说明，若要使用 conditional 还必须清空 missingLinks。`provided` 只说明宿主声明的资料来源可追踪，不验证资料真实性，也不会自动证明作用链或现实预测有效。

## 迁移与显示

当前模板统一输出 v5。v3/v4 只兼容八字单体系历史报告；旧 schema 的紫微或综合报告返回 `INVALID_REPORT`，不能靠改版本号绕过 timingChain。六份活跃报告已迁移到 v5，四份综合报告的限运作用链均明确现实资料未提供并保持 unresolved；两份八字报告保持空 `ziweiReasoning`。渲染结果在“限运与四化”下直接显示作用链目标、年份、三组依据、跨层复核、现实资料状态、未闭合环节和撤回条件。

固定前向样例 [`semantic-forward-007`](../../examples/acceptance/semantic-forward-007/) 同步迁移到 v5。它绑定 2024—2028、同候选四化/运限/主题宫事实，明确现实资料未提供和两个缺口，仍拒绝从四化清单生成升职、收入或关系事件日程。交付答复未改写，responseClaims 只更新 report 哈希绑定。

## 验证

- `npm run check`：138/138 PASS，TypeScript strict 与 build PASS。
- 新增回归覆盖：timingChain 缺失、证据包外年份、错误宫位类型、目标与主题宫错配、非限运主题夹带作用链、现实资料未提供却标 conditional、资料来源已声明但缺口未清空；目标与宫位匹配、显式来源且缺口清空的结构路径也有正例。
- 六份活跃报告按各自原输入和年份由构建版 `report-check` 重算为 valid，并重新渲染；主报告 chartId/evidenceId 保持不变。
- `semantic-forward-007` 的 `acceptance-check` 四项 caseChecks 均 pass、五项问题计数为 0、reviewStatus=PASS、artifactCount=8；无可信 runtime receipt，最终 status 仍为 partial。
- 九份 semantic-forward manifest 均由当前构建版重放成功；原始 PARTIAL 内容评审保持 PARTIAL，没有因 schema 升级被改写成 PASS。
- Skill quick_validate PASS；现行范围 61 个 Markdown 的 216 个本地链接无缺失；`openspec/` 仍不存在。

主 [`report.json`](../../examples/report.json) 为 36,706 字节、SHA-256 `d2bcd21e1c473c7845b26c65343f925715852a5fd99f31ed78da4a2309914061`；[`report.md`](../../examples/report.md) 为 73,260 字节、SHA-256 `6a4dfc60fe90b6391f23a7ceff91721fd4316fd562b1339383f7c1d4f034dd51`。007 的 report SHA-256 为 `57e78420c963839e8754a6658ad4e362122e667dd348237573525bebe92f6c2e`，responseClaims 为 `3e9408c2de9b854b496eafaec3d961fbda13eb758b5beadee3eb6c1f05f36ea8`，manifest 为 `151b7e1fd2a9b731339e11d8a13fe7cc911e8fe746a9ab35ddb5ddc2ea1d7cab`。

这些结果证明结构合同、引用、迁移样例和本地回归一致。程序仍不会自动判断三方四正、飞化、自化或跨层取舍的传统学理是否正确；来源声明也不是现实事实认证。conditional 仍只表示限定范围内的传统解释，不表示现实发生概率。
