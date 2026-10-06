# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并要求：“以 2026 年 9 月 25 日、上海为准，明年上半年能升职吗？三个月内哪个月最好？年底前能有结果吗？春节前几天适合谈加薪？”

请按冻结的 Skill 与报告契约完成两个阶段：

1. `subannual-time-must-stop`：写 `response-stop.md`，220—430 个非空白 Unicode 字符。必须说明普通明年可按冻结公历日期解析为 2027，但当前 context 只有年度层，没有半年、季度、月、周、日或精确节气证据；“春节前几天”还叠加了未明确的历法边界。停止生成报告，不回答哪个月、哪几天或能否升职，并请用户改为明确的 2027 年度主题。
2. `explicit-2027-year-keeps-career-unresolved`：假定用户澄清“只看 2027 年度事业主题，不问半年、季度、月份或具体日期”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用“2027 年度”等明确年度表达，不再使用当前年度 evidence 不支持的细分时间；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

两阶段都不得从年度四化、大限、官禄宫或单层落宫推出半年、季度、月份、日期、最佳窗口或升职结果。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。不得自行补流月、流日、春节日期、立春时刻、宫干飞化、自化、现实经历、事件日期或成功概率。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
