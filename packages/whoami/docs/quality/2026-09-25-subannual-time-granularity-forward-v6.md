# v6 年度以下时间粒度前向验收

日期：2026-09-25。结论：新增核心失败封闭规则与双 case 固定样例 `semantic-forward-012`。当前 context/evidence 只有年度层，报告不再从年度四化、大限或主题宫生成半年、季度、月份、星期、日期、最佳窗口或几天内的事件判断。

## 门禁范围

所有最终可见报告自由文本继续经过同一个时间检查入口。新增窄模式覆盖：

- 上半年、下半年、年初、年中、年底和年末；
- 本季度、下季度、上季度、第一至第四季度及 Q1—Q4；
- 这个月、本月、下个月、上个月、月初、月中、月底和月末；
- 本周、下周、上周及相应星期表达；
- “三个月内”“未来十天”“接下来两周”等天、周、星期或月持续时间。

命中时返回 `UNSUPPORTED_TIME_GRANULARITY`，要求退回明确年度主题，或先接入流月、流日、精确节气及对应作用链证据。“2027 年度事业主题”“月份资料尚未提供”“流月与流日未计算”等范围说明继续允许。春节、农历新年或立春前后的表达仍由历法限定门禁先返回 `AMBIGUOUS_RELATIVE_TIME`，避免把年界歧义误报成单纯粒度不足。

## 两阶段产物

第一 case 使用[同一 input](../../examples/acceptance/semantic-forward-012/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-012/context.json)。[停机答复](../../examples/acceptance/semantic-forward-012/response-stop.md) 为 265 个非空白 Unicode 字符，解释普通明年=2027，但现有 evidence 不支持用户要求的细分时点；它不绑定 report，也不选择月份、日期或推断升职。

第二 case 假定用户退回 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-012/report.json) 绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，正文只使用年度范围并明确细粒度证据缺失；事业段绑定 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。[年度答复](../../examples/acceptance/semantic-forward-012/response-annual.md) 为 395 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-012/response-claims.json)逐段绑定 timing、career 与 advice claim。退回年度层只解决证据粒度越界，现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 第一 case：responseSafety=pass，未提供 report 的三项检查为 not-applicable。
- 第二 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=11；最终 status=partial。
- 核心边界测试与固定前向回归各新增 1 项；`npm run check` 为 147/147 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `091e64f71273f12fd7381e2c56179626d70fb335bfe7dad0df994d2135af738f`；任务 `fa8fd86620043e4386c05611aee3cc34fdf13346f00ae7667cb2f4313e6e87af`；量表 `b421b627942a855053e5ca711a7659044c84662398504907a1f31d68e6376040`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；停机答复 `711ef81abef52c9bbc35deb49d2611c82affcf8d7b89569fa351bc6f59b307bb`；年度答复 `cb6298689c1280260e005d9a760dde89835ef181840733affaf606a0dbbdb24b`；sidecar `fa475e98397948ece53b866f3cd74cd8d81ff57e4353b5fd04fa058063767ea6`；manifest `8696c66ba896f3631ef9d530e98e1edbd26f5a13688ba870d36696714628197f`。

这项 PASS 只说明固定样例遵守粒度停机、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
