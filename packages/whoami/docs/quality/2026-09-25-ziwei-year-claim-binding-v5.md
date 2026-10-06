# 紫微年度正文与作用链绑定 v5

> 历史快照：本页记录显式四位年份绑定首次完成时的状态。当前模板已升级为 v6，并增加冻结日期下的相对年份解析；当前结果见[报告相对时间基准 v6](2026-09-25-relative-time-reference-v6.md)。下列哈希、测试数和“相对时间仍需人工核对”的限制不代表当前文件。

日期：2026-09-25。结论：含紫微事实的正文与跨体系判断，只要提到当前证据范围内的具体年份或年份区间，现在必须同时绑定同候选 `ziwei-timing`，且 `timingChain.years` 覆盖文字涉及的全部年份。这样年度结论不能只挂事业、财运或关系主题而绕开限运前提。

## 修正的问题

初版 v5 已能检查 timingChain 自身的字段、事实类型、目标宫位与现实缺口，但正文绑定仍有两处缝隙：

- career/wealth/relationships claim 可以写入具体流年，却只绑定对应主题，不绑定 ziwei-timing；
- timingChain.years 只要是 evidence 年份的非空子集即可，正文写 `2026—2028` 时仍可能只登记 2026 和 2028。

这会造成作用链结构存在，但真正的年度句子没有继承其 unresolved 状态。现在 [`validateReport`](../../src/report.ts) 从 claim.text、claim.conditions 与 crossSystem.text 中提取四位年份，并将区间展开到当前 evidence 已请求的每一年。只要该段同时引用紫微事实，就逐候选检查：

1. reasoningRefs 必须包含 `ziwei-timing`；
2. 段落涉及的每个 evidence 年份都必须包含在同候选 timingChain.years；
3. premiseStatus 继续由所有已绑定前提聚合，限运 unresolved 时年度段落也必须 unresolved。

只检查当前 evidence 范围，出生年份、文献出版年份等范围外数字不会被误当成限运年份。`2026—2028`、`2026-2028`、`2026 至 2028` 等常见区间会覆盖其中所有已请求年份。

## 样例迁移

五份含紫微的活跃报告完成扫描。主报告补了 2 条年度正文绑定，1996 综合样例补了 5 条，普通综合样例补了 1 条；边界双候选和 `semantic-forward-007` 原本已经绑定，无需改写。新增限运前提的段落同步保持 unresolved，没有通过删年份或弱化测试绕过门禁。

六份活跃报告仍按原输入和年份复算；八字单体系报告不受此门禁影响。`semantic-forward-007` 的冻结 Skill 快照、答复、报告和 manifest 均未改写，当前验收器重放仍为内容 PASS、最终 partial。

## 验证

- 新增回归先证明 `2026—2028` 只绑定 ziwei-career 会失败，再证明缺少中间 2027 的 timingChain 会失败；补齐 ziwei-timing 与三个年份后通过。
- `npm run check`：139/139 PASS，TypeScript strict 与 build PASS。
- 五份紫微/综合活跃报告的年度段落扫描为 0 个漏绑；四份综合报告与 007 由构建版 `report-check` 返回 valid。
- 007 的 acceptance 四项 caseChecks 继续全部 pass，五项问题计数为 0，reviewStatus=PASS；没有可信 runtime receipt，仍为 partial。
- 九份 semantic-forward manifest 由当前构建版重放成功；原有 PASS/PARTIAL 内容评审保持不变。
- Skill quick_validate PASS；现行范围 62 个 Markdown 的 221 个本地链接无缺失；99 个 JSON 可解析，`full-1991` 收据哈希无漂移；`openspec/` 不存在。

主 [`report.json`](../../examples/report.json) 为 36,924 字节、SHA-256 `515cdb2dd06558ce9f24ffb257cc871e3edc7f06bb48c65e0ec2123f0ee057ff`；[`report.md`](../../examples/report.md) 为 73,312 字节、SHA-256 `a7dfd18ffb9c3ba7eac05eca68fc37db46be721664dee484f91349e65b473b09`。chartId/evidenceId 保持不变。

当前门禁识别显式四位年份与常见区间，不自动理解“明年”“后年”“下个大限”或干支年简称；这些表达仍须宿主人工核对。年份绑定证明的是报告前提没有被绕过，不证明紫微传统作用链正确，也不证明现实事件会发生。
