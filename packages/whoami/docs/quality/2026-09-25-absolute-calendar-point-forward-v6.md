# v6 绝对时点与命名历法点前向验收

日期：2026-09-25。结论：新增两类失败封闭规则与双 case 固定样例 `semantic-forward-015`。年度 context/evidence 不能直接回答指定月份、日期或星期，也不能把春节、立春、清明等命名历法点未经换算和日级证据就当成可判断的现实事件窗口。

## 两类门禁与允许项

第一类是绝对月日星期。evidence 年份内的“2027 年 3 月”，以及没有年份的“3 月 15 日、三月十五日、周一、星期五”，返回 `UNSUPPORTED_TIME_GRANULARITY`。宿主须退回明确年度主题，或先接入与报告合同一致的月、日、星期粒度 evidence。早于冻结报告年份、未落入 `evidence.years` 的历史年月只在报告标题与 `timingChain.realityBasis.source` 中允许，用于出生资料和来源说明；放在 claim、论证或建议中仍会拒绝，允许项也不等于现实事件获得证明。

第二类是命名历法点。“明年春节、2027 年立春、立春当天、清明那天”等返回 `UNSUPPORTED_CALENDAR_POINT`。宿主须先明确对应公历日期、所用历法、IANA 时区和体系年界，再接入日级作用链。裸的“八字年度边界按立春、紫微年度边界按农历新年”只说明报告口径，不包含事件时间，因此继续允许。

这两类规则位于最终可见报告自由文本的共同时间检查入口。它们只拒绝缺证据的时点结论，不自行补春节日期、节气时刻、流月、流日或现实经历，也不把出生日期误判成未来预测。

## 两阶段产物

第一 case 使用[同一 input](../../examples/acceptance/semantic-forward-015/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-015/context.json)。[停机答复](../../examples/acceptance/semantic-forward-015/response-stop.md) 为 244 个非空白 Unicode 字符，先说明 2027 年 3 月、3 月 15 日和周一超出年度 evidence，再说明春节与立春当天需要公历日期、历法及时区口径；它不绑定 report，也不判断升职、加薪、跳槽或行动日。

第二 case 假定用户明确退回 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-015/report.json) 绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，并允许历史出生日期及裸年界说明；事业段绑定 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。[年度答复](../../examples/acceptance/semantic-forward-015/response-annual.md) 为 370 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-015/response-claims.json)逐段绑定 timing、career 与 advice claim。退回年度层只关闭绝对时点越界，现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 第一 case：responseSafety=pass，未提供 report 的三项检查为 not-applicable。
- 第二 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=11；最终 status=partial。
- 核心边界测试与固定前向回归各新增 1 项；`npm run check` 为 153/153 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `b8f8426076354d0c0b895296c7b319668291da65f2dc2c2640facc43d5821850`；任务 `5585764b3e44961297562b0885814ebad84274e617f261d03dfbc207450dabfd`；量表 `183c14d7a188a00e08949b03be746675cfe035fe363814dbe6046293abd59c45`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；停机答复 `8298bec4c68bc70dfd84d99644085d74091bc66fc6caf4a6907c4cbe6db40df4`；年度答复 `4d5cc9c30da15168f88d2a7bb83de5272884e6099ec09d266bbe073e9a079201`；sidecar `aa3731109ed75eed98376cc67c14d71f661bf5bd173dc2d80c77b935727d5e26`；manifest `ed3393eba50ae9cedfc8ff4028e081df9545ffe4d029f03a9148bfe106e55de3`。

这项 PASS 只说明固定样例遵守绝对时点停机、命名历法点规范化要求、历史资料允许项、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
