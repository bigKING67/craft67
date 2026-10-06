# v6 八字运年结构化作用链

日期：2026-09-25。结论：`bazi-timing` 已从“周期事实 + 年份清单”收紧为可复算的结构化作用链。报告必须逐年匹配 `.bazi.cycles.yearly` 的年份、干支和立春边界，同时绑定本候选四柱或干支关系、跨层复核、现实资料、未闭合环节与撤回条件。该合同防止报告只抄年序后直接生成事件判断；它不自动完成传统制化推理，也不证明现实预测有效。

## 原缺口

第一阶段的 v6 门禁能确认六类八字论证齐全、周期事实与规则已引用、正文年份进入 `bazi-timing.years`。但年份数组不能回答三个关键问题：报告写出的年度干支是否与引擎事实一致；年度解释究竟回连了哪些本命事实；现实经历未提供时，是否仍可能把运年状态抬成 conditional。紫微限运已有相应的现实缺口门禁，八字年度链仍弱一层。

## 当前合同

[报告实现](../../src/report.ts)为 v6 `bazi-timing` 增加 `timingChain`：

- `target` 固定事业、财富、关系或综合范围；`cycleRefs` 只能引用同候选且已纳入本项依据的 `.bazi.cycles`。
- `annualReviews` 与顶层 `years` 数量和顺序完全一致。每项 `year/pillar/boundary` 必须精确匹配周期事实，`natalRefs` 只能回连同候选四柱或 `.bazi.relations`，复核文字必须明确写出该年和干支。
- `crossLayerReview` 说明本命、大运与流年如何分层；`missingLinks`、`realityBasis`、`withdrawalConditions` 显式保存没有闭合的传统与现实前提。
- 现实资料未提供时，`source=null`、缺口不得为空且状态强制 unresolved。声明已提供来源不等于验证真实；conditional 还要求缺口为空。任何 unresolved 运年项都必须保留至少一个缺口。
- 其他八字主题不得填写 timingChain；旧 v3/v4/v5 继续按原五类只读兼容，不能追加新字段冒充迁移。

模板从 cycles 预填年份、干支与立春边界，引用和解释保持为空，避免模板伪装成完成的报告。渲染结果在八字论证下展示目标、周期事实、逐年干支、本命依据、跨层复核、现实资料、缺口和撤回条件。

## 报告迁移

根目录综合例及 boundary、full-1991、full-1996、ordinary、strength-balance 六份当前报告，共七个八字候选，均补入作用链并重新渲染。逐年干支直接读取各自 context 的 cycles；本命入口绑定各候选自身的 `.bazi.relations`，不跨候选借用。full-1996 与 ordinary 将目标限定为事业，其余保持综合。

strength-balance 原先的 `bazi-timing.status=conditional` 已改为 unresolved，并同步降低引用它的正文前提状态。普通格与暂偏弱只能作为本命假设，不能替代逐年制化和现实触发；因此这次状态收紧是合同修正，不是文风降级。其余六项本来就是 unresolved。

## 验证边界

直接回归覆盖缺失 timingChain、错误年度干支、错误本命引用和没有现实资料却升级 conditional；原有缺主题、错规则、缺周期事实、漏年与正文绑定回归继续保留。构建版 CLI 另做缺链、错干支和现实状态升级故障注入。六份当前报告以各自输入和年份重算，结构化链、渲染文本与开发收据同步更新。

- `npm run check`：184/184 PASS，TypeScript strict 与 build PASS；模板回归同时确认 2026 丙午与立春边界由 cycles 预填。
- 六份当前报告均由构建版 CLI 按各自输入与年份通过 `report-check` 并重新 `render`；full-1991 收据中的四项 artifact 哈希已重算并逐项复核一致。
- 缺失 timingChain、把 2026 干支改成甲子、在现实资料未提供时把状态改成 conditional 三项故障注入均退出 1，依次返回 `INVALID_REPORT`、`FACT_MISMATCH`、`PREMISE_STATUS_MISMATCH`。
- 23 份 semantic-forward manifest 全部由当前构建版重放成功，并继续因缺可信 runtime receipt 保持 partial；没有创建第 24 份自然语言样例来替代确定性结构回归。
- Skill quick_validate 在隔离 PyYAML 环境中 PASS；当前文档范围 85 个 Markdown、417 个本地链接无缺失，175 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。

这些检查只证明：确定性周期事实没有被报告改写，引用范围与状态门禁闭合。逐年制化是否符合具体传统流派、现实资料是否真实、文本推论是否充分以及未来事件是否发生，仍需分别核验，不能由 `report-check` 或测试通过推出。
