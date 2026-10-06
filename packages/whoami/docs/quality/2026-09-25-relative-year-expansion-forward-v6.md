# v6 缺年补算前向验收

日期：2026-09-25。结论：新增双 case 固定样例 `semantic-forward-009`，验证相对年份落在当前 evidence 之外时，宿主必须先停下，再以同一 input 补算目标年份；补算只修复年份事实缺失，不能自动升级事业结论。

## 两阶段证据

任务和量表在两阶段答复与报告之前固定。baseline [`context-2026.json`](../../examples/acceptance/semantic-forward-009/context-2026.json) 的 years 只有 2026；以 `2026-09-25 / Asia/Shanghai` 为基准，“明年”解析为 2027，因此 [`response-stop.md`](../../examples/acceptance/semantic-forward-009/response-stop.md) 在 178 个非空白字符内说明缺年并停止，没有绑定 report。

expanded [`context-2026-2027.json`](../../examples/acceptance/semantic-forward-009/context-2026-2027.json) 由同一 input 重算。两份 context 的 chartId 相同，证明出生盘绑定未变；evidenceId 不同，证明年份范围已进入证据版本。expanded [`report.json`](../../examples/acceptance/semantic-forward-009/report.json) 只绑定新 evidenceId，timingChain.years 精确为 `[2026, 2027]`；事业段保留明年=2027，并同时绑定事业与限运主题，状态 unresolved。

[`response-expanded.md`](../../examples/acceptance/semantic-forward-009/response-expanded.md) 有 434 个非空白字符，说明补算后才可读取 2027 流年、四化与宫职事实，同时保留岗位、考核、权限、组织机会、跨层作用与撤回条件缺口。[`response-claims.json`](../../examples/acceptance/semantic-forward-009/response-claims.json) 逐段绑定 timing、career 和 advice claim。

## 复核结果

- baseline case：responseSafety=pass，未提供 report 的三项检查为 not-applicable。
- expanded case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=11；最终 status=partial。
- 固定回归已加入 `tests/acceptance.test.ts`；`npm run check` 为 142/142 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `84a39ac46479cc5581ed4e14ad86e7d93a449df5cb25feb1bae8f0d31dd6622e`；任务 `68492e29a37f314fd1b384aee808ae180a0182f495c521ffef697c654b3d066b`；量表 `371cb992052862cac31db2cbf5a3340a3d927d61bfc0275abda5a106bde6cade`；baseline context `79f98489cde8792aa6ae1131b768acf7ef48c460f96c7781407dd03b0e879347`；expanded context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `3c0c1876114350d3bce69b47ea2944522a4e27942f18acc1be65991cebc8e2e5`；baseline 答复 `53f3a1d6f9206fe5e16b61e4dd56ab069d992c3b140107c14ce375b07d0b13e6`；expanded 答复 `d0f25f0cad3ee6caf783ef2a80c7bc2622518c5fdd4d919c28d6d4c33baa17e8`；sidecar `ecd3aab7eeea068bc8e593f5dd4c6fa357f14438d2cd5f75a10181bd54af92d9`；manifest `818d05479433bc6566458c295a6c5f74cc7c6dc42730e9a7aa5ca6f0e799fcdd`。

这项 PASS 只说明当前合成产物遵守缺年停机、补算与前提边界。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
