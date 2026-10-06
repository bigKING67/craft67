# 紫微论证前提绑定 v4

> 历史快照：本页记录 v4 五主题绑定首次完成时的状态。当前模板已升级为 v5，并增加结构化限运作用链；现行合同与验证见[紫微限运作用链 v5](2026-09-25-ziwei-timing-chain-v5.md)。

日期：2026-09-25。结论：结构化报告已从“紫微事实可以不绑定解释前提”收紧为逐候选、逐主题绑定。`whoami.report.v4` 要求紫微/综合报告分别说明本命结构、事业联宫、财运联宫、关系联宫、限运与四化五类论证；正文与跨体系判断必须引用实际依赖的主题，`premiseStatus` 取所有八字与紫微前提中更保守的状态。

## 修正的问题

v3 已能约束八字的旺衰、格局、调候、扶抑和用神取舍，但纯紫微 claim 仍可使用空 `reasoningRefs` 和 `not-applicable`。这会造成不对称：紫微事实与规则虽然可追踪，宿主仍可绕过“支持、反证、条件、替代解释”的结构，跨体系结论也只绑定八字前提。

v4 在 [`src/report.ts`](../../src/report.ts) 增加五类 `ziweiReasoning`，并执行以下失败封闭规则：

- ziwei/combined 的每个候选都必须各有五个唯一主题；bazi 模式不得混入紫微论证。
- 每项必须有同一候选、同一体系的支持事实和关联规则，并完整填写结论、反证复核、成立条件与替代解释。
- 引用紫微事实的正文必须按章节绑定对应主题；advice 绑定其实际依赖的主题。
- 综合判断对同一候选同时绑定八字和紫微前提，不能跨候选拼盘。
- 任一所引前提 unresolved，正文就必须 unresolved；只有全部 conditional 才能写 conditional。
- `ziwei-timing` 只有年份、换限标签或四化星名时继续 unresolved，不能据此生成事件结论或逐年行动日程。

高风险措辞检查同步覆盖紫微论证四个自由文本字段；答复—报告一致性和 responseClaims 聚合改为同时处理两体系论证。程序验证结构、引用和一组窄范围越级措辞，仍不理解全部自然语言语义。

## 兼容与样例迁移

当前模板统一输出 v4。v3 仅兼容八字单体系历史报告，便于固定的 `semantic-forward-006` 和对照样例继续复算；v3 紫微或综合报告返回 `INVALID_REPORT`，不能只替换 schema 名称。

六份当前报告已迁移并重渲染：[`主样例`](../../examples/report.json)、[`边界双候选`](../../examples/acceptance/boundary/report.json)、[`1991 八字`](../../examples/acceptance/full-1991/report.json)、[`1996 综合`](../../examples/acceptance/full-1996/report.json)、[`普通综合`](../../examples/acceptance/ordinary/report.json)和[`扶抑八字`](../../examples/acceptance/strength-balance/report.json)。四份综合报告中，每个候选的本命结构、事业、财运与关系暂为 conditional，限运与四化保持 unresolved；两份八字单体系报告使用空 ziweiReasoning。

主报告的五项紫微前提为 4 conditional + 1 unresolved，八条正文 claim 为 1 conditional + 7 unresolved；原有逐年行动日程没有恢复。chartId / evidenceId 仍为 `a3fee7834bc85e84bff82e9ad80e72c9678383d5948ea7ae4d76e2094cb97789` / `3d0b34bd617494d53f269cc99fa79edf01647a9ebb72b0fc6a806970d096ea9e`。当前 [`report.json`](../../examples/report.json) 为 35,266 字节、SHA-256 `975eab95a62eb1a6669d2c6552f992601e88630ca5f32e7c978e0712e0bfe617`；[`report.md`](../../examples/report.md) 为 72,272 字节、SHA-256 `f66b68fae2e24d9b6b14703145c2df6c7d88adc4cdf192132f1f82d4c1af0686`。

## 验证

- `npm run check`：135/135 PASS，TypeScript strict 与 build PASS。
- 当前六份 v4 报告及 `semantic-forward-006` 历史 v3 八字报告均由构建版 `report-check` 按原输入和年份重算为 valid；六份 v4 Markdown 重渲染后逐字节一致。
- v3 综合 baseline 以 `INVALID_REPORT` 失败，v3 八字 baseline 继续 valid，兼容边界与设计一致。
- `semantic-forward-006` 的 acceptance-check 为 partial；四项 caseChecks 均 pass、人工 review 为 PASS，但没有可信 runtime receipt，不能升级为 verified。
- [`full-1991/receipt.json`](../../examples/acceptance/full-1991/receipt.json) 中 birth、report JSON、report Markdown、premise review 四项 SHA-256 均与当前文件一致。
- Skill quick_validate PASS；现行范围 59 个 Markdown 的 205 个本地链接无缺失；`openspec/` 不存在。

这些结果证明当前结构合同、样例和构建产物一致，不证明紫微传统规则正确、宿主自由文本已经完成专家审校，也不证明现实预测有效。conditional 表示在写明条件下可讨论的传统解释，不是现实事件概率；结构门禁之外的隐喻、弱化条件和跨段语义冲突仍须人工审查。

后续先增加 v4 紫微单体系固定前向样例，现已随报告合同迁移到[紫微限运作用链 v5](2026-09-25-ziwei-timing-chain-v5.md)。
