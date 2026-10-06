# v6 模糊时间范围前向验收

日期：2026-09-25。结论：新增核心失败封闭规则与双 case 固定样例 `semantic-forward-013`。报告不再把“近期、不久、很快、过阵子、什么时候”等没有确定年份或起止范围的表达自行换算成几周、几个月、季度、日期或最佳窗口。

## 门禁范围

所有最终可见报告自由文本继续经过同一个时间检查入口。新增窄模式覆盖“近期”“不久前/后”“很快”“过阵子/过一段时间”“什么时候/何时/几时”“短期内”“未来/接下来一段时间”。命中时返回 `AMBIGUOUS_TIME_HORIZON`，要求先改写为明确 YYYY 年度主题或明确日期范围，并确保相应粒度 evidence 已经计算。

错误类型保持分层：春节、农历新年和立春相关年界仍优先返回 `AMBIGUOUS_RELATIVE_TIME`；“三个月内、下个月、第一季度”等已有具体粒度但超出年度 evidence 的表达仍返回 `UNSUPPORTED_TIME_GRANULARITY`；只有范围本身未定义时才返回 `AMBIGUOUS_TIME_HORIZON`。明确的“2027 年度事业主题”“当前资料不支持具体时点判断”继续允许。

## 两阶段产物

第一 case 使用[同一 input](../../examples/acceptance/semantic-forward-013/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-013/context.json)。[停机答复](../../examples/acceptance/semantic-forward-013/response-stop.md) 为 230 个非空白 Unicode 字符，解释用户的五类时间词没有确定范围，当前只有年度 evidence；它不绑定 report，不判断升职、跳槽、结果时间或最佳时点。

第二 case 假定用户明确选择 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-013/report.json) 绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，正文只使用明确年度范围；事业段绑定 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。[年度答复](../../examples/acceptance/semantic-forward-013/response-annual.md) 为 365 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-013/response-claims.json)逐段绑定 timing、career 与 advice claim。明确年度只解决时间口径，现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 第一 case：responseSafety=pass，未提供 report 的三项检查为 not-applicable。
- 第二 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=11；最终 status=partial。
- 核心边界测试与固定前向回归各新增 1 项；`npm run check` 为 149/149 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `bdb0a59d74d74945a439bb284ce679b460e3b599e8e447b936ca284cb4ddb4f5`；任务 `8b45c6334e02517edad5f35387162d90357942017e0a0ef4cc5635fe37d3de5d`；量表 `1223ea2cd66efa1af78365ef72839fd227a71a912147b29c7c349f25e63370ba`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；停机答复 `ea7bdd6aee3ca3384152039612285421383a6e7bf6cb2e9f59fd4a03e2e43ed5`；年度答复 `06b4f0fb2a2be86a44f123aea717257168519941ad0f173b23e0f5c243d5545c`；sidecar `986d79392d283507bd3b30ca2af86bffc2839f34e1aaa8a452c38a1c3fa61e7f`；manifest `f7368c5618e87fca321a3f8d067860b12b1987229e3b4c63fd492bf48fe0a9ff`。

这项 PASS 只说明固定样例遵守模糊时间停机、明确年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
