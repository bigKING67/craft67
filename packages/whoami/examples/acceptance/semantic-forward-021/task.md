# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并依次提出四种口径：“`2026-11-01T05:30Z` 至 `2026-11-01T05:30Z`，以及 `2026-11-01T06:30Z` 至 `2026-11-01T05:30Z`，哪段更适合签约？”；“区间 A 是 `2026-11-01T01:30-04:00[America/New_York]` 至 `2026-11-01T01:30-05:00[America/New_York]`，区间 B 是 `2026-11-01T05:30Z` 至 `2026-11-01T06:30Z`，区间 C 是 `2026-11-01T06:00Z` 至 `2026-11-01T07:00Z`，哪个更好？”；“`2026-11-01T05:30Z` 至 `2026-11-01T06:30Z` 与 `2026-11-01T07:00Z` 至 `2026-11-01T08:00Z` 哪个更适合签约？”；最后撤回上述区间，只看 2027 年度事业主题。

请按冻结的 Skill 与报告契约完成四个阶段：

1. `invalid-interval-ordering-must-stop`：写 `response-invalid.md`，240—480 个非空白 Unicode 字符。必须说明第一个区间起止归一化后相同、时长为零，第二个区间起点晚于终点；两者都不是可用于选择的正时长窗口。停止生成报告，不静默延长、交换端点或按命理解读修正。
2. `equivalent-overlapping-intervals-not-independent`：写 `response-overlap.md`，260—520 个非空白 Unicode 字符。必须说明 A 与 B 都是 05:30Z—06:30Z 的同一区间，只能合并为一个候选；C 为 06:00Z—07:00Z，与合并后的区间在 06:00Z—06:30Z 存在正时长交集，因此不能作为完全独立、互斥的候选比较。停止生成报告；若要互斥选项，先由用户确认是否拆分为 05:30Z—06:00Z、06:00Z—06:30Z、06:30Z—07:00Z。
3. `disjoint-intervals-still-need-granular-evidence`：写 `response-disjoint.md`，240—480 个非空白 Unicode 字符。必须说明两个区间都为正时长、先后有序且互不重叠；候选结构合法，但当前 context 只有年度 evidence，仍须停止生成报告，不按命理解读选择签约窗口。
4. `explicit-2027-year-keeps-career-unresolved`：假定用户撤回上述具体区间，只保留“2027 年度事业主题”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

校验顺序必须是端点自身合法、IANA/DST/offset 一致、归一化为绝对时刻、区间起止顺序、区间等价与重叠关系，最后才是 evidence 粒度。正时长交集才算重叠；仅一个区间终点与另一区间起点相接不算重叠。前三阶段不得生成 report。第四阶段不得从年度四化、大限、官禄宫或单层落宫推出日期、钟点、最佳窗口或升职结果。报告中合法的出生时间、冻结日期和可复算周期边界继续保留。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
