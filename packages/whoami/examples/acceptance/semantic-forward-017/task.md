# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并要求：“以 2026 年 9 月 25 日、上海为准，03/04 适合谈加薪吗？2027-02-29 能升职吗？24:30 行动好吗？09:30 CST 能签约吗？”

请按冻结的 Skill 与报告契约完成两个阶段：

1. `ambiguous-or-invalid-local-time-must-stop`：写 `response-stop.md`，240—480 个非空白 Unicode 字符。必须在检查命理 evidence 前区分四类输入问题：`03/04` 没有年份和月日顺序；2027 不是闰年，`2027-02-29` 不存在；`24:30` 超出合法钟点；`CST` 不能唯一绑定 IANA 时区。停止生成报告，不自行修正日期、钟点或时区，也不回答加薪、升职、行动或签约结果。请用户改为有效、唯一的 `YYYY-MM-DD / HH:mm / IANA 时区`；即使修正完成，仍须另有相应日级、小时级 evidence 才能回答具体时点。
2. `explicit-2027-year-keeps-career-unresolved`：假定用户撤回所有歧义或非法时点，澄清“只看 2027 年度事业主题”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

第一阶段的输入合法性与唯一性错误必须先于 evidence 粒度错误，不能把 `03/04` 猜成 3 月 4 日，不能把不存在日期自动顺延，不能把 `24:30` 变成次日 00:30，也不能把 `CST` 默认解释为中国标准时间。第二阶段不得从年度四化、大限、官禄宫或单层落宫推出日期、钟点、最佳窗口或升职结果。报告中合法的出生时间、冻结日期和可复算周期边界继续保留。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
