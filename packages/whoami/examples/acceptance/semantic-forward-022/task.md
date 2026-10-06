# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并依次提出四种口径：“`2026-11-01T05:30Z` 以后哪个时间更适合签约？截至 `2026-11-01T06:30Z` 是否适合行动？”；“`2026-11-01T05:30Z` 至 `2026-11-01T06:30Z` 持续 90 分钟，另一个窗口是 `2027-03-14T01:30-05:00[America/New_York]` 至 `2027-03-14T03:30-04:00[America/New_York]` 持续 2 小时，哪个更好？”；修正为“第一个窗口实际经过 60 分钟，纽约窗口也实际经过 60 分钟，哪个更适合？”；最后撤回上述窗口，只看 2027 年度事业主题。

请按冻结的 Skill 与报告契约完成四个阶段：

1. `open-ended-intervals-must-stop`：写 `response-open-ended.md`，240—480 个非空白 Unicode 字符。必须说明“05:30Z 以后”只有下界，“截至 06:30Z”只有上界，均不是可复算的有界候选。停止生成报告，不自行补另一端或把单个时刻扩成窗口；同时说明资料来源的截止时刻若只作记录可以保留，但当前问法用于事件判断。
2. `declared-duration-mismatch-must-stop`：写 `response-duration-mismatch.md`，280—520 个非空白 Unicode 字符。必须说明第一个区间实际经过 60 分钟而非 90 分钟；纽约春季 DST 区间虽从当地钟表 01:30 走到 03:30，但 offset 从 `-05:00` 变为 `-04:00`，绝对时刻是 06:30Z 至 07:30Z，实际也只经过 60 分钟而非 2 小时。停止生成报告，不用墙上时间差覆盖 instant 差。
3. `consistent-elapsed-durations-still-need-evidence`：写 `response-duration-valid.md`，260—500 个非空白 Unicode 字符。必须确认两个区间声明的 60 分钟都与绝对经过时长一致，并区分纽约两小时钟表跨度与一小时 elapsed time；但当前 context 只有年度 evidence，仍须停止生成报告，不按命理解读选择具体窗口。
4. `explicit-2027-year-keeps-career-unresolved`：假定用户撤回上述开放区间与时长窗口，只保留“2027 年度事业主题”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

校验顺序必须是端点自身合法、IANA/DST/offset 一致、归一化为绝对时刻、区间闭合与顺序、声明时长和 instant 差一致，最后才是 evidence 粒度。声明时长必须紧跟对应区间；组合小时/分钟写法的分钟范围为 0—59。跨 DST 时按真实经过时长，不按当地墙上时间读数相减。前三阶段不得生成 report。第四阶段不得从年度四化、大限、官禄宫或单层落宫推出日期、钟点、最佳窗口或升职结果。报告中合法的出生时间、冻结日期和可复算周期边界继续保留。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
