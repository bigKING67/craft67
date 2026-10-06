# v6 八字运年与边界论证门禁

日期：2026-09-25。结论：`whoami.report.v6` 的八字论证由五类本命取法扩为六类，新增 `bazi-timing`（运年与边界）。引用八字大运/流年事实或当前 evidence 年份的正文，必须显式绑定同候选的时间论证和完整年份范围；不再借挂旺衰、扶抑或用神取舍来承担时间推理。

## 缺口与合同

核心早已有 `.bazi.cycles` 事实和 `R-bazi-timing` 规则，但报告层只有 strength、pattern、climate、balance、selection。年度段落因此可以引用周期事实，却没有对应的结构化前提；从引用图看似“有论证”，实际时间推理只能挂在本命取法上。

[报告实现](../../src/report.ts)要求 v6 每个八字候选各有六类论证。`bazi-timing` 必须引用同候选 `.bazi.cycles` 与 `R-bazi-timing`，并填写来自当前 evidence、去重且升序的 `years`；其自身叙述涉及的 evidence 年份也必须全部纳入该数组。其他八字主题不得填写 years。v3/v4/v5 继续只读原五类；向旧 schema 追加 `bazi-timing` 会拒绝，避免只改字段冒充迁移。该入口后来继续补齐[结构化作用链门禁](2026-09-25-bazi-timing-chain-v6.md)，本页保留第一阶段“独立主题与年份绑定”的来由。

claim 或 crossSystem 在 v6 中引用 `.bazi.cycles` 时，必须绑定该候选 `bazi-timing`；含八字事实并提到 evidence 年份时，`bazi-timing.years` 必须覆盖全文涉及的年份。带年份的跨体系强关系还须同时绑定 `bazi-timing` 与 `ziwei-timing`。这些门禁只确认时间范围、事实和论证入口相连，不证明传统作用、现实触发或事件预测成立。

## 迁移

六份当前主报告共七个八字候选已新增独立时间论证并重新渲染：根目录综合例、boundary 双候选、full-1991、full-1996、ordinary、strength-balance。结构化作用链补齐后，七项均保持 unresolved；strength-balance 原先仅凭普通格与暂偏弱前提保留的 conditional 已撤回，因为逐年制化与现实触发仍未闭合。

boundary 原先在所有章节批量引用两候选 cycles 与 `R-bazi-timing`。迁移时只在 timing 章节保留这些时间依据并绑定两候选 `bazi-timing`，其余章节移除误挂引用。full-1991 的开发收据同步更新 report JSON/Markdown 哈希；出生输入与逐段复核哈希未变。

## 验证与限制

- `npm run check`：184/184 PASS，TypeScript strict 与 build PASS。
- 六份当前报告均由当前 CLI 按各自输入与年份通过 `report-check`，并由同一实现重新 `render`。
- 三项构建版故障注入分别删除 `bazi-timing`、删除 cycle claim 的时间论证引用、缩短 years，均退出 1，并分别返回 `MISSING_REASONING`、`MISSING_REASONING_LINK`、`MISSING_TIMING_YEAR`。
- 23 份冻结 semantic-forward manifest 由当前构建版重放成功，全部仍因缺可信 runtime receipt 保持 partial；没有复制第 24 份自然语言样例来代替确定性报告合同测试。
- Skill quick_validate 在隔离 PyYAML 环境中 PASS。`openspec/` 与 `.git/` 均不存在。

本轮证明报告可以拒绝八字时间论证的缺主题、漏绑和错年；不证明运年传统规则正确、文本语义完整或现实预测有效。完整运行约束见[报告契约](../../references/report.md)与[分析契约](../../references/analysis.md)。
