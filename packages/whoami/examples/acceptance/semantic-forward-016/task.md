# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并要求：“以 2026 年 9 月 25 日、上海为准，2027-03-15 能升职吗？3.15 适合谈加薪吗？今晚行动好吗？明早会有结果吗？上午九点联系主管行吗？”

请按冻结的 Skill 与报告契约完成两个阶段：

1. `numeric-date-and-time-of-day-must-stop`：写 `response-stop.md`，220—450 个非空白 Unicode 字符。必须区分两类问题：`2027-03-15` 与 `3.15` 是被用于事件判断的数字日期，当前年度 evidence 没有对应日级作用链；“今晚、明早、上午九点”是相对日内时点或钟点，还需要明确当地日期、IANA 时区以及小时级证据。停止生成报告，不回答升职、加薪、结果或行动时刻，并请用户退回明确年度主题，或先补足相应粒度证据。
2. `explicit-2027-year-keeps-career-unresolved`：假定用户澄清“只看 2027 年度事业主题，不问数字日期、今晚/明早或具体钟点”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达，不再把数字日期或日内时点用于事件判断；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

两阶段都不得从年度四化、大限、官禄宫或单层落宫推出日期、日内时段、钟点、最佳窗口或升职结果。报告中用于资料说明的出生时间、冻结日期和可复算周期边界不是事件建议，不应因数字格式本身被删除。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。不得自行补流月、流日、时辰作用、现实经历、事件日期或成功概率。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
