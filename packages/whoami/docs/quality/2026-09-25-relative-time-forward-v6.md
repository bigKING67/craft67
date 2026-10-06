# v6 相对时间前向验收

日期：2026-09-25。结论：新增固定自然语言样例 `semantic-forward-008`，把 v6 相对时间结构门禁延伸到完整的任务、报告、交付答复、逐段 sidecar、维护者复核与 acceptance manifest。该样例能复算并拒绝把“明年、后年、下个大限”直接升级为升职、收入翻倍或婚变结论。

## 固定任务与产物

任务和量表在答复与报告之前固定。输入与 context 复用 007 的单候选合成命盘，避免为了新断言更换样本；这也意味着本项是同一资料上的新语言边界回归，不是独立样本或盲测。

[`report.json`](../../examples/acceptance/semantic-forward-008/report.json) 使用 `whoami.report.v6` 和 `2026-09-25 / Asia/Shanghai`。事业段保留“明年”并解析为 2027，财运段保留“后年”并解析为 2028；两段同时绑定主题论证与 `ziwei-timing`，由 unresolved 限运前提把正文状态降为 unresolved。用户的模糊周期词没有进入 report；关系段改写为当前 2022—2031 夫妻宫大限、后续 2032—2041 子女宫大限，并明确宫名与周期切换不能推出婚变。

[`response.md`](../../examples/acceptance/semantic-forward-008/response.md) 有 405 个非空白 Unicode 字符，直接回答两个相对年份和两段大限范围，再说明岗位、收入、现金流、关系行为与双方意愿均未提供。[`response-claims.json`](../../examples/acceptance/semantic-forward-008/response-claims.json) 逐段绑定事业/财运、关系及建议 claim，论证引用并集与最保守状态由当前验收器复核。

## 复核结果

- report-check：valid，chartId/evidenceId 与同一 context 一致。
- acceptance-check：status=partial、reviewStatus=PASS；responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- 五项问题计数均为 0；artifactCount=8。
- 固定回归已加入 `tests/acceptance.test.ts`；`npm run check` 为 141/141 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版成功重放；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- 缺可信 runtime receipt，runtimeBound/runtimeAttested/runtimeVerified 均为 false，不能升级为 verified。

关键指纹：Skill 快照 `84a39ac46479cc5581ed4e14ad86e7d93a449df5cb25feb1bae8f0d31dd6622e`；任务 `df1022d379da0319da182d85233ba6eba5403523f6344b11b89aa52ba46843e4`；量表 `58e32092234b5f18efffcaf02f5126b9f6716aaf879846412c79dfee64def302`；报告 `262e25b3cbbda38c93123064a258c75b74e6938d62b69d1e062d96fd3f9f95d2`；答复 `74ecb79d1b11d86b90580dd2c18544f5328d80f293fd34d11eb29c18dfb29cad`；sidecar `7016981525da1021540c8700e9b5fbcd97cd50ca10c096e8a599d88363a6eb90`；manifest `5c6e7129cb73b678c111917bf0ad2f342597b67d25a86b0eafe6712f3c783cb5`。

这项 PASS 只说明当前合成产物满足事实、前提和安全合同。它不是模型真实运行证明，不评价模型普遍表现，也不证明紫微理论或现实事件预测有效。
