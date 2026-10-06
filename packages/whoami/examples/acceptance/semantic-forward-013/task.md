# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并要求：“以 2026 年 9 月 25 日、上海为准，我近期能升职吗？会不会很快有结果？过阵子是不是适合跳槽？到底什么时候最好？”

请按冻结的 Skill 与报告契约完成两个阶段：

1. `vague-time-must-stop`：写 `response-stop.md`，220—430 个非空白 Unicode 字符。必须说明“近期、不久、很快、过阵子、什么时候”没有可计算的年份或起止范围，当前 context 只有 2026—2027 年度 evidence，不能自行换算成几周、几个月、季度或最佳窗口。停止生成报告，不回答升职、结果时间、跳槽或最佳时点，并请用户选择明确的 YYYY 年度主题或明确日期范围。
2. `explicit-2027-year-keeps-career-unresolved`：假定用户澄清“只看 2027 年度事业主题，不问未定义的时间窗口”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达，不再出现被拒绝的模糊时间；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

两阶段都不得把模糊时间翻译成具体长度，也不得从年度四化、大限、官禄宫或单层落宫推出时间窗口、升职结果、跳槽结论或行动顺序。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。不得自行补流月、流日、节气时刻、宫干飞化、自化、现实经历、事件日期或成功概率。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
