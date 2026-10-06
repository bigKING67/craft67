# 报告相对时间基准 v6

日期：2026-09-25。结论：新报告升级为 `whoami.report.v6`，以顶层 `timeReference.asOfDate` 和 IANA `timeZone` 冻结相对时间语义。“今年/本年/明年/后年/去年/前年”不再随报告被阅读或重放的日期漂移；它们先解析成公历年份，再进入既有 evidence 年份范围与紫微 `timingChain` 绑定门禁。

自然语言产物层的固定回归见[相对时间前向验收 v6](2026-09-25-relative-time-forward-v6.md)。

## 修正的问题

v5 已能约束显式四位年份与年份区间，但“明年只讨论事业主题”没有四位数字，可以绕开年度绑定；同一份报告隔年阅读时，“明年”还会改变含义。“下个大限”也不能只靠当前日期唯一定位到 evidence 中哪个传统运限范围。

v6 现在执行以下合同：

1. 新报告必须填写有效 `YYYY-MM-DD` 日期与有效 IANA 时区；旧 schema 不能靠追加该字段冒充迁移。
2. 所有会展示给用户的报告自由文本都经过相对时间检查，包括标题、边界、正文、八字/紫微论证、`timingChain` 和跨体系判断。
3. 六个明确相对年份按 `asOfDate` 的年份解析；结果不在 `evidence.years` 时返回 `RELATIVE_TIME_OUT_OF_SCOPE`，要求先重算对应年份。
4. 含紫微事实的 claim 或 crossSystem 使用相对年份时，解析结果与显式年份取并集，继续要求同候选 `ziwei-timing` 及完整 `timingChain.years`。
5. “下个大限/下一大限/下一个大限”返回 `AMBIGUOUS_RELATIVE_TIME`，宿主须改写为 evidence 内明确年份范围。
6. v5 仅兼容不含相对年份的既有报告；v3/v4 仍仅兼容八字单体系历史报告。

识别使用窄词法边界。“未来年份”和“今后年份”不会误判成相对年份；未支持的干支简称、流月、流日或其他上下文时间表达仍须宿主改写成明确年份。`timeZone` 用于记录日期语境，解析值由已经冻结的 `asOfDate` 年份决定；校验器不从系统当前时间推导报告日期。

## 样例迁移

六份活跃报告迁移到 v6，并固定 `2026-09-25 / Asia/Shanghai`：[主样例](../../examples/report.json)、[边界双候选](../../examples/acceptance/boundary/report.json)、[1991 八字](../../examples/acceptance/full-1991/report.json)、[1996 综合](../../examples/acceptance/full-1996/report.json)、[普通综合](../../examples/acceptance/ordinary/report.json)和[扶抑八字](../../examples/acceptance/strength-balance/report.json)。它们按原输入与年份复算后均为 valid，并重新渲染；报告“资料与口径”区会直接显示冻结基准。

`semantic-forward-007` 刻意保留为冻结的 v5 验收产物。它不含受支持的相对年份，不需要改写 report、responseClaims、Skill 快照或 manifest，当前校验器仍可重放；这也验证了 v5 的窄兼容路径，而不是把固定验收产物静默迁移。

## 验证与边界

- 回归覆盖冻结日期解析、紫微限运前提绑定、evidence 越界、模糊大限、无效日期、无效时区、v5 相对年份拒绝，以及“未来年份/今后年份”不被误判。
- `npm run check`：140/140 PASS，TypeScript strict 与 build PASS。
- 六份活跃报告由当前构建版 `report-check` 返回 valid，并重新渲染；主 Markdown 可见 `2026-09-25（Asia/Shanghai）` 时间基准。
- `full-1991` 收据已按当前 report JSON 与 Markdown 更新，四项 artifact 哈希与文件一致。
- 二十三份 semantic-forward manifest 均由当前构建版重放成功；原有 PASS/PARTIAL 内容评审不变，全部仍因没有可信 runtime receipt 保持 partial。`semantic-forward-007` 至 `semantic-forward-023` 的适用 caseChecks 均为 pass、reviewStatus=PASS。
- Skill quick_validate 在隔离的 PyYAML 运行环境中 PASS；AGENTS/README/SKILL/references/docs 共 80 个现行 Markdown、401 个本地链接无缺失；private 与 node_modules 之外 175 个 JSON 均可解析；`openspec/` 不存在。完整记录见[验证日志](../validation.md)。

当前主 [`report.json`](../../examples/report.json) 为 37,012 字节、SHA-256 `2c036c7bdaf8698d80d9e314aa2d31c4d97b6bfc562a76738ec7f31db5b455bc`；[`report.md`](../../examples/report.md) 为 73,432 字节、SHA-256 `20b350481a0465002d9ae742271e93b31f859d0a540ec3fcba092f9b26108575`。chartId/evidenceId 保持不变。

这项变更只固定报告文字的时间指代并封闭结构绕过，不证明传统运限作用链正确，不新增现实事件预测，也不把结构校验升级成自然语言完整语义认证。
