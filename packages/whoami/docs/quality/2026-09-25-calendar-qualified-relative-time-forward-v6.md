# v6 历法限定相对时间前向验收

日期：2026-09-25。结论：新增核心失败封闭规则与双 case 固定样例 `semantic-forward-011`。报告不再把“农历明年、过完春节、立春后”等混合年界表达静默套入公历 `asOfDate`；宿主须先区分公历元旦、紫微农历新年和八字立春，再以明确年份与体系标签重写。

## 门禁范围

所有最终可见报告自由文本继续经过同一个时间检查入口。新增窄模式覆盖：

- 农历/阴历/夏历修饰今年、本年、明年、后年、去年或前年；
- 相对年份后接“按/以/的农历、阴历、夏历”；
- “过完/过了/过春节、农历新年、立春”；
- 春节、农历新年或立春直接接前、后、以前、以后、之前、之后。

命中时返回 `AMBIGUOUS_RELATIVE_TIME`，要求先改写为明确公历年份及对应体系年界。规则刻意不解析春节日期、精确立春时刻、所有口语时间或虚岁；“2027 紫微流年按农历年标签”“八字 2027 年界按立春口径”“未来年份/今后年份”等已明确或非指令表达继续允许。

## 两阶段产物

第一 case 使用[同一 input](../../examples/acceptance/semantic-forward-011/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-011/context.json)。[停机答复](../../examples/acceptance/semantic-forward-011/response-stop.md) 为 245 个非空白 Unicode 字符，说明普通明年=2027，但三个体系年界不能互换；它不绑定 report，并请用户选择公历 2027、紫微 2027 农历年标签或八字 2027 立春年标签。

第二 case 假定用户只选择紫微 2027 农历年标签。[v6 报告](../../examples/acceptance/semantic-forward-011/report.json) 绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，正文使用明确年度标签，不再含被拒绝表达；事业段绑定 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。[明确口径答复](../../examples/acceptance/semantic-forward-011/response-explicit.md) 为 411 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-011/response-claims.json)逐段绑定 timing、career 与 advice claim。明确年界只消除时间歧义，现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 第一 case：responseSafety=pass，未提供 report 的三项检查为 not-applicable。
- 第二 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=11；最终 status=partial。
- 核心边界测试与固定前向回归各新增 1 项；`npm run check` 为 145/145 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `234da3e7e1ae893bd609a092d9c14f095de6fc122bffe8148950c477192c63a4`；任务 `a1ba2903839c9422fc4f43d7bb312a9d52fb8822da15915b117f74448844ae04`；量表 `cc99881f2f75bde0911c5d5be108c7a8ce14d0215cde2026c3b1da45866fec81`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `4c0e9a8bf5d212b5faee92f979337a231eaf95d226e7f44055db1c5a92a456a6`；停机答复 `44ce3c56919640c265ecd303bf790807e8fbac9136e02b376c92d963f855e8e7`；明确口径答复 `02fabc2b8f538adb7b0ec9673caf79c3cef1ba23c80c3039fe69170d9a8cadc8`；sidecar `2b057cb2459e93b2b5ad805ddee21c7dff5971df054084528a4527d1c3732400`；manifest `f1f9f47b5ae91f8c3542b04bd06c3cffe4769fee4e9efc8b4291d0e5f6adad79`。

这项 PASS 只说明固定样例遵守历法分层、停机、明确改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、传统历法解释或现实事件预测有效。
