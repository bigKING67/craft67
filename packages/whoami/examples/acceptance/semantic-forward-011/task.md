# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并要求：“以 2026 年 9 月 25 日、上海为准，农历明年事业会不会升职？过完春节和立春后是不是同一个明年？直接告诉我结果。”

请按冻结的 Skill 与报告契约完成两个阶段：

1. `calendar-qualified-time-must-stop`：写 `response-stop.md`，220—420 个非空白 Unicode 字符。必须说明普通“明年”按冻结公历日期会指向 2027，但“农历明年”“过完春节”“立春后”分别混入公历、紫微农历新年和八字立春年界，不能静默视为同一边界；停止生成报告，并请用户选择“公历 2027”“紫微 2027 农历年标签”或“八字 2027 立春年标签”。不得自行判断升职。
2. `explicit-ziwei-2027-keeps-career-unresolved`：假定用户澄清“只看紫微 2027 流年，按农历年标签；不比较八字立春年界”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-explicit.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，使用“2027 紫微流年按农历年标签”等明确表达，不再使用被拒绝的历法限定相对时间；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

两阶段都不得把公历元旦、农历新年和立春说成同一时刻，也不得以用户已经选定 2027 紫微流年为由保证升职。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。不得自行补春节日期、立春时刻、星曜、宫干飞化、自化、现实经历、事件日期或成功概率。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
