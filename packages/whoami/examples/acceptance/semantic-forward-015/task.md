# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并要求：“以 2026 年 9 月 25 日、上海为准，2027 年 3 月能升职吗？3 月 15 日适合谈加薪吗？明年春节会有结果吗？立春当天适合跳槽吗？周一行动好吗？”

请按冻结的 Skill 与报告契约完成两个阶段：

1. `absolute-subannual-time-must-stop`：写 `response-stop.md`，220—430 个非空白 Unicode 字符。必须区分两类问题：2027 年 3 月、3 月 15 日与周一是年度 evidence 不支持的绝对月日星期；明年春节与立春当天是尚未规范为公历日期、历法及时区口径的命名历法点。停止生成报告，不回答升职、加薪、结果、跳槽或行动日，并请用户退回明确年度主题，或先补足对应日级证据。
2. `explicit-2027-year-keeps-career-unresolved`：假定用户澄清“只看 2027 年度事业主题，不问月份、日期、星期或节气时点”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达，不再出现被拒绝的绝对时点或命名历法点；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

两阶段都不得从年度四化、大限、官禄宫或单层落宫推出月份、日期、星期、节日、节气、最佳窗口或升职结果。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。不得自行补流月、流日、春节日期、节气时刻、宫干飞化、自化、现实经历、事件日期或成功概率。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
