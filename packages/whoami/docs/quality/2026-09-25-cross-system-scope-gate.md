# 跨体系主题与年份范围门禁

日期：2026-09-25。结论：v6 `crossSystem` 现在把比较主题、年份范围和关系强度写成可复算合同。此前校验只确认同一候选同时引用八字与紫微事实；主题不一致、年份没有双侧时间链或未决前提被手工改成 supports/complements/conflicts，仍可能通过结构检查。

## 合同

- 每项 v6 `crossSystem` 必须声明 `target`，只允许 general、career、wealth、relationships、timing；必须声明升序去重的 `years`，并与正文实际涉及的 evidence 年份完全一致。未涉及具体流年时使用空数组，timing 不允许空年份。
- insufficient 用于记录未核验、不可比或未闭合的比较，仍保留打算比较的主题和年份，不要求伪造完整主题依据。
- supports、complements、conflicts 每项只能比较一个候选；所引八字与紫微论证必须全部为 conditional，且两边各至少一条直接事实引用须落在所绑定论证的 supportRefs/counterRefs 中，不能用同候选无关事实挂名。任一前提 unresolved 时返回 `UNRESOLVED_CROSS_SYSTEM_RELATIONSHIP`。
- 强关系必须绑定 target 对应的紫微论证，并在该项 `factRefs` 直接引用对应主题事实：general 为 base 与命宫，career、wealth、relationships 分别为官禄、财帛、夫妻宫，timing 为运限与四化。主题或年份范围不一致返回 `CROSS_SYSTEM_SCOPE_MISMATCH`。
- 强关系只要带年份，还必须同时引用八字 cycles、紫微 cycles、紫微 transformations，并绑定 ziwei-timing；缺项返回 `MISSING_CROSS_SYSTEM_TIMING`。
- v5 继续兼容既有无 target/years 的 crossSystem。新合同只要求 v6，避免把历史报告静默当成已迁移。

八字的 strength、pattern、climate、balance、selection 是分析方法，不等同事业、财运或关系主题。本轮没有强造一套八字主题映射；target 负责声明比较问题，直接事实、两边论证内容及人工语义复核仍共同决定关系是否成立。自动门禁不能证明文字真的支持、互补或冲突，更不能证明传统学理或现实预测有效。

## 当前产物迁移

四份含跨体系对照的当前报告补齐字段并由构建版重新渲染：[主样例](../../examples/report.json) 两项分别标为 career/general，[边界双候选](../../examples/acceptance/boundary/report.json) 两项标为 general，[1996 综合样例](../../examples/acceptance/full-1996/report.json) 标为 timing 且 years 为 2026—2028，[普通综合样例](../../examples/acceptance/ordinary/report.json) 标为 career。六项关系原本均为 insufficient，本轮没有借结构迁移把它们升级成强关系。渲染后的“八字与紫微对照”直接显示主题和年份范围。

## 验证与限制

- 新增四项直接回归，覆盖字段缺失/年份错配、未决升级、强关系主题正反例和双体系年份链；连同既有用例，`npm test` 为 182/182 PASS。
- 构建版 CLI 对缺 target、正文与 years 错配、unresolved 强关系的故障注入均退出 1，分别返回 `CROSS_SYSTEM_SCOPE_MISMATCH`、`CROSS_SYSTEM_SCOPE_MISMATCH`、`UNRESOLVED_CROSS_SYSTEM_RELATIONSHIP`。
- 主样例、boundary、full-1991、full-1996、ordinary、strength-balance 六份当前报告按各自原输入和年份复算，全部返回 valid；四份综合 Markdown 已重渲染。
- 23 份 semantic-forward manifest 由当前构建版逐份重放成功，仍因缺可信 runtime receipt 保持原有 partial。没有新增第 24 份，因为本轮是确定性报告结构合同，直接正反测试比复制自然语言回答更能固定边界。
- Skill quick_validate PASS。工程检查只证明结构、引用、兼容和失败封闭；关系文字是否符合具体流派、两边论证是否真正同题，以及现实材料是否可信，仍须人工复核。
