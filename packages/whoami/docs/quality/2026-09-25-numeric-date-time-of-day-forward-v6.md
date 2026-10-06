# v6 数字日期与日内时点前向验收

日期：2026-09-25。结论：新增两类窄失败封闭规则与双 case 固定样例 `semantic-forward-016`。数字日期格式本身可以合法出现在出生资料、报告冻结日期和周期边界中；只有它被用于事业、结果、行动或窗口等事件判断时才会停机。今晚、明早、上午九点等日内时点还必须具备当地日期、IANA 时区以及日级、小时级证据。

## 两类门禁

数字日期模式覆盖 `2027-03-15`、`2027/03/15`、`2027.3.15`、`3.15`、`03/15` 与 `3-15`。校验器在日期附近出现升职、加薪、结果、行动、面试、签约、机会、最佳、必然等判断语境时返回 `UNSUPPORTED_TIME_GRANULARITY`。现有合规报告中的 `1991-10-12 11:40` 出生资料、`2026-09-25` 冻结日期与 `2024-07-03至2034-07-03` 周期边界继续允许；这三类事实不因数字格式本身被删除，也不因此获得现实事件证明。

日内模式覆盖今晚、今早、明早、明晚、明天上午等相对日内表达，以及上午九点、下午 3:30、09:30 等钟点。它们用于事件判断时返回 `UNSUPPORTED_TIME_OF_DAY`。冻结的 `asOfDate` 只有当地公历日期，没有当前钟表时间，也没有日级或小时级作用链；年度四化、大限与主题宫不能补出行动钟点。出生记录、真太阳时和边界采样里的钟点在没有事件判断语境时继续允许。

## 两阶段产物

第一 case 使用[同一 input](../../examples/acceptance/semantic-forward-016/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-016/context.json)。[停机答复](../../examples/acceptance/semantic-forward-016/response-stop.md) 为 258 个非空白 Unicode 字符，先说明数字日期缺日级作用链，再说明今晚、明早与上午九点还缺当地日期、时区及小时级证据；它不绑定 report，也不判断升职、加薪、结果或行动时刻。

第二 case 假定用户明确退回 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-016/report.json) 绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，并保留资料性时间事实；事业段绑定 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。[年度答复](../../examples/acceptance/semantic-forward-016/response-annual.md) 为 376 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-016/response-claims.json)逐段绑定 timing、career 与 advice claim。退回年度层只关闭时点越界，现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 第一 case：responseSafety=pass，未提供 report 的三项检查为 not-applicable。
- 第二 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=11；最终 status=partial。
- 核心边界测试与固定前向回归各新增 1 项；`npm run check` 为 155/155 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `9ad3aef5cec93abad96cb6322230b0c36ddf513ef264f23b0ac2152ec63537aa`；任务 `ce3331a4288d178ce0e8ccc7c63f52d3f374ece097f0fa8c5b7abddcd0cfaea2`；量表 `88da03513489c5b6c7ee8c292db143beb09834a78af85b3ddc0029021e31bd84`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；停机答复 `1a628427aeeb0ce9af737e2f6e963b5ca4bfd3a4b7af393227c779344df10b70`；年度答复 `902197f873e27519d5d43b7eeebaa97b7e233f947ea8f317db3d5d6182bc4e64`；sidecar `b91ea47fc4267133d16a7fb8831381fcecc10c259bbd02e44a9f304aeced8bd5`；manifest `ab2071e97a46c4a4171b08072739d11f29ada58db55307db862dff323d8d9bc3`。

这项 PASS 只说明固定样例遵守数字日期与日内时点停机、非事件时间事实保留、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
